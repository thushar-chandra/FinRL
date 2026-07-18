# INTERFACE_CONTRACTS.md

> The concrete implementation contract for every module: public interfaces, method signatures, data structures, expected behavior, error handling, and integration requirements. This is the document OpenCode should implement directly against. Research rationale lives in [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md); engineering narrative lives in [AGENTS.md](./AGENTS.md). Where those documents describe *what* and *why*, this document describes *exactly how the code must be callable*. Every design decision here that resolves a prior ambiguity is recorded in [DECISIONS.md](./DECISIONS.md) ADR-019 through ADR-026 — this document is the implementation of those ADRs, not an independent source.

---

## Class → File → Purpose → Dependencies Map

*(Design Review M4 — this table is the single place that binds every class to its file. No class below is defined anywhere else in this document set without appearing here first.)*

| Class | File | Purpose | Depends On | Related Interfaces |
|---|---|---|---|---|
| `MarketAnalysisAgent` | `finrl/agents/ca_marl/market_agent.py` | Market-direction RL agent | Feature Engineering output | `AgentOutput` |
| `RiskAssessmentAgent` | `finrl/agents/ca_marl/risk_agent.py` | Risk/volatility RL agent | Feature Engineering output | `AgentOutput` |
| `PortfolioAllocationAgent` | `finrl/agents/ca_marl/allocation_agent.py` | Allocation-weight RL agent | Feature Engineering output only (ADR-025 — no cross-agent inputs) | `AgentOutput` |
| `ConfidenceEngine` | `finrl/agents/ca_marl/confidence_engine.py` | Confidence Estimation & Calibration (one combined module, ADR-022) | `AgentOutput` from all three agents; `OutcomeLabelGenerator` | `CalibratedConfidence` |
| `OutcomeLabelGenerator` | `finrl/agents/ca_marl/confidence_engine.py` (same file — owned by `ConfidenceEngine`, ADR-024) | Generates per-recommendation outcome labels, reused by training and Evaluation | Realized market data (Data Pipeline) | consumed by `ConfidenceEngine`, `EvaluationEngine` |
| `ConfidenceAwareFusion` | `finrl/agents/ca_marl/confidence_fusion.py` | Deterministic, PPO-independent fusion (ADR-014, ADR-020) | `AgentOutput` × 3, `CalibratedConfidence` | `FusedDecision` |
| `RiskManagementLayer` | `finrl/agents/ca_marl/risk_management.py` | Authoritative constraint enforcement | `FusedDecision` | `FinalRecommendation` |
| `EvaluationEngine` | `finrl/agents/ca_marl/evaluation.py` | Financial + calibration evaluation, ablations, baselines (ADR-021) | `FinalRecommendation` history, realized returns, `OutcomeLabelGenerator` | `EvaluationReport` |

---

## Shared Data Structures

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class AgentOutput:
    agent_name: str
    recommendation: Any            # type varies per agent — see per-agent contract below;
                                    # NOT combined directly across agents (see AssetWeightProposal below)
    raw_confidence: float          # scalar per agent (ADR-020 — not a per-asset dict)
    reasoning: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None  # populated by Confidence Calibration, not the agent itself

@dataclass
class CalibratedConfidence:
    agent_name: str
    calibrated_confidence: float    # scalar per agent (ADR-020)
    diagnostics: dict[str, Any]     # ece, brier_score, reliability_curve_ref
    timestamp: datetime

# --- Fusion intermediate representation (ADR-020) ---
# AssetWeightProposal: dict[str, float] — per-asset weight, all values >= 0,
# sums to 1.0 within floating-point tolerance. This is the common shape every
# agent's heterogeneous `recommendation` is transformed into, INSIDE the
# fusion module, before the confidence-weighted average is applied.
AssetWeightProposal = dict[str, float]

@dataclass
class FusedDecision:
    final_allocation: dict[str, float]     # AssetWeightProposal-shaped: non-negative, sums to 1.0 (ADR-020 — no more Any/TBD)
    reasoning: str                          # composed by ConfidenceAwareFusion (ADR-019) — see §5
    confidence_summary: dict[str, float]    # {agent_name: calibrated_confidence}, passed through from Confidence Calibration (ADR-019)
    fusion_metadata: dict[str, Any]         # e.g. {"fallback_used": bool, "per_agent_proposals": {...}} for auditability
    timestamp: datetime

@dataclass
class FinalRecommendation:
    # Prose/pipeline-stage name: "Final Portfolio Recommendation" (canonical, ADR-026).
    # `FinalRecommendation` is the accepted class-name shorthand for that stage's output.
    allocation: dict[str, float]    # long-only, sums to 1.0, post-Risk-Management-Layer
    reasoning: str                  # passed through unchanged from FusedDecision.reasoning (ADR-019)
    confidence_summary: dict[str, float]  # passed through unchanged from FusedDecision.confidence_summary (ADR-019)
    timestamp: datetime

# --- Evaluation data structures (ADR-021) ---
@dataclass
class FinancialMetrics:
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    cumulative_return: float

@dataclass
class CalibrationMetrics:
    ece: float
    brier_score: float
    reliability_curve_ref: str      # path to the generated diagnostic artifact

@dataclass
class EvaluationReport:
    financial_metrics: FinancialMetrics
    calibration_metrics: dict[str, CalibrationMetrics]   # keyed by agent_name
    ablation_results: dict[str, Any] | None
    baseline_comparison: dict[str, FinancialMetrics] | None
    fold_id: str
    timestamp: datetime
```

**Note on typing:** `pydantic` models are preferred over plain `dataclasses` if runtime validation is desired (recommended given multiple contributors/agents touching this codebase) — see `CODING_STANDARDS.md`. The shapes above are the contract; the exact class mechanism (dataclass vs. pydantic) is an implementation choice. **No field above is typed `Any` except `AgentOutput.metadata`/`recommendation` and `fusion_metadata`, which are intentionally open-ended auxiliary/diagnostic fields, not load-bearing data the pipeline depends on structurally.**

---

## 1. Market Analysis RL Agent

```python
class MarketAnalysisAgent:
    def predict(self, features: "pd.DataFrame") -> AgentOutput:
        """
        Args:
            features: engineered feature DataFrame for the current timestep(s),
                      including regime features (bull/bear, volatility regime,
                      trend regime, market-state — see ADR-016).
        Returns:
            AgentOutput with recommendation as a BUY/SELL/HOLD-style value
            per asset, e.g. {"RELIANCE.NS": "BUY", "TCS.NS": "HOLD"}.
        Raises:
            InsufficientHistoryError: if indicator warm-up period not satisfied.
        """

    def prediction_consistency(self, features: "pd.DataFrame", k: int) -> float:
        """
        Implements ADR-023. Samples this agent's policy on k nearby historical
        states within the same regime bucket as `features`. Returns the
        fraction of the k samples agreeing with the modal (most common)
        recommendation. Feeds ConfidenceEngine.estimate_raw_confidence().
        """
```

**Integration requirement:** must expose the reward-stability signal ConfidenceEngine needs, via `metadata["reward_stability"]` (a scalar, computed as the inverse of the variance of this agent's realized training/inference-time reward over its recent history — exact window size in `configs/agents.yaml`).

**Error handling:** raise a dedicated `InsufficientHistoryError` rather than returning a silent default; tie-break behavior on ambiguous signals must be deterministic and recorded in `metadata["tie_break_reason"]`.

---

## 2. Risk Assessment RL Agent

```python
class RiskAssessmentAgent:
    def predict(self, features: "pd.DataFrame") -> AgentOutput:
        """
        Returns:
            AgentOutput with recommendation as
            {asset: {"expected_volatility": float, "risk_score": float}}.
        """

    def prediction_consistency(self, features: "pd.DataFrame", k: int) -> float:
        """
        Implements ADR-023. Same k-sample procedure as MarketAnalysisAgent,
        but consistency = 1 - coefficient_of_variation across the k
        continuous risk_score samples (not modal-agreement, since output
        is continuous, not categorical).
        """
```

**Integration requirement:** same `metadata["reward_stability"]` exposure requirement as the Market Analysis Agent.

**Error handling:** `InsufficientHistoryError` for volatility warm-up; regime-boundary discontinuities must be smoothed at the feature level (`MODULE_SPECIFICATIONS.md` §2), not patched inside this agent.

---

## 3. Portfolio Allocation RL Agent

```python
class PortfolioAllocationAgent:
    def predict(self, features: "pd.DataFrame") -> AgentOutput:
        """
        Args:
            features: engineered feature DataFrame incl. regime features.
                      Per ADR-025, this agent takes NO other agents' outputs
                      as input — its observation space is Feature Engineering
                      output only, symmetric with the other two agents.
        Returns:
            AgentOutput with recommendation as {asset: weight, ...}.
            Raw output is NOT guaranteed long-only/sum-to-one at this layer —
            that is authoritatively enforced downstream by the Risk Management
            Layer, never assumed satisfied here.
        """

    def prediction_consistency(self, features: "pd.DataFrame", k: int) -> float:
        """Implements ADR-023, continuous-output variant (as RiskAssessmentAgent)."""
```

**Error handling:** degenerate/infeasible raw output must still be returned (not raised as an error) — enforcement is the Risk Management Layer's job. Do not add ad hoc clipping here.

---

## 4. Confidence Estimation & Calibration (one combined module — ADR-022)

```python
class OutcomeLabelGenerator:
    """Owned by ConfidenceEngine (ADR-024). Reused, not reimplemented, by EvaluationEngine."""

    def generate_label(self, agent_name: str, recommendation: AgentOutput,
                        realized_data: "pd.DataFrame") -> float:
        """
        Computes the outcome label for a past recommendation, once
        realized_data covers that recommendation's label horizon
        (recommendation.timestamp + label_horizon, horizon configured in
        agents.yaml per agent type). Per-agent label definition:
          - Market Analysis: sign agreement between recommendation direction
            and forward return over the horizon.
          - Risk Assessment: 1.0 if realized volatility fell within the
            predicted band, else 0.0.
          - Portfolio Allocation: realized risk-adjusted return of the
            proposed weights vs. an equal-weight reference over the horizon.
        Raises:
            LabelNotYetResolvableError: if realized_data does not yet cover
            the full label horizon for this recommendation.
        """

    def is_eligible_for_fold(self, recommendation: AgentOutput, label_horizon: "timedelta",
                              fold_training_window_end: datetime) -> bool:
        """
        Implements the ADR-024 leakage rule exactly:
        returns True iff recommendation.timestamp + label_horizon <=
        fold_training_window_end. ConfidenceEngine.fit_calibration() MUST
        filter its training pairs through this method before fitting.
        """


class ConfidenceEngine:
    def estimate_raw_confidence(self, agent_outputs: list[AgentOutput]) -> dict[str, float]:
        """
        Computes raw confidence (scalar per agent, ADR-020) as a combination
        of: historical accuracy (rolling mean of OutcomeLabelGenerator labels,
        filtered per is_eligible_for_fold), reward stability (from
        AgentOutput.metadata["reward_stability"]), and prediction consistency
        (from each agent's prediction_consistency() method). Exact combination
        function (e.g. weighted average, its weights) is an implementation
        detail — record the final choice in DECISIONS.md when made.
        """

    def fit_calibration(self, training_window_data: Any) -> None:
        """Fits the calibration mapping (Platt/temperature scaling) STRICTLY
        on (confidence, label) pairs that pass OutcomeLabelGenerator's
        is_eligible_for_fold() check for the current fold. Must never be
        called with ineligible pairs — see TESTING_STRATEGY.md's mandatory
        calibration-leakage test."""

    def calibrate(self, raw_confidence: dict[str, float]) -> CalibratedConfidence:
        """Applies the fitted calibration mapping; also computes ECE, Brier
        score, and reliability-diagram diagnostics."""
```

**Error handling:** cold-start (insufficient track record in a regime bucket) → documented uninformative-prior fallback (0.5), logged at `WARNING`.

**Integration requirement:** `fit_calibration` must be called exactly once per walk-forward fold, on that fold's eligible training pairs only (per `is_eligible_for_fold`). Any code path that calls `calibrate()` before `fit_calibration()` has run for the current fold is a bug.

---

## 5. Confidence-Aware Decision Fusion (ADR-020)

```python
class ConfidenceAwareFusion:
    # --- Per-agent transform functions (ADR-020) — internal to this class ---
    def _market_to_proposal(self, recommendation: dict[str, str],
                             universe: list[str]) -> AssetWeightProposal:
        """BUY->+1, HOLD->0, SELL->-1 per asset; negatives clipped to 0;
        renormalized to sum to 1. If all assets are non-positive, falls back
        to equal-weight across `universe` (logged: metadata["market_fallback"]
        = "no_buy_signal_equal_weight")."""

    def _risk_to_proposal(self, recommendation: dict[str, dict],
                           universe: list[str], epsilon: float = 1e-6) -> AssetWeightProposal:
        """inv_i = 1 / (epsilon + risk_score_i); renormalized to sum to 1
        (lower risk -> higher weight)."""

    def _allocation_to_proposal(self, recommendation: dict[str, float],
                                 universe: list[str]) -> AssetWeightProposal:
        """Defensive re-clip (negatives -> 0) and renormalize. Falls back to
        equal-weight if the sum is 0 (logged)."""

    def fuse(self, agent_outputs: list[AgentOutput],
              calibrated_confidence: CalibratedConfidence,
              universe: list[str]) -> FusedDecision:
        """
        1. Transform each agent's `recommendation` into an AssetWeightProposal
           via the corresponding _*_to_proposal function above.
        2. For each asset in `universe`:
             final_allocation[asset] = sum_over_agents(
                 proposal_agent[asset] * confidence_agent
             ) / sum_over_agents(confidence_agent)
           (Guaranteed to sum to 1.0 across assets — see DECISIONS.md ADR-020
           for the proof.)
        3. reasoning = "; ".join(
             f"{agent_name}({confidence:.2f}): {agent_output.reasoning}"
             for agent_name, confidence, agent_output in the three agents,
             sorted by confidence descending
           )
        4. confidence_summary = calibrated_confidence dict, passed through unchanged.

        Raises:
            (none — must not raise if sum(confidence) == 0; instead falls
            back to an equal-weight average of the three proposal vectors,
            records fusion_metadata["fallback_used"] = True, logged at WARNING)
        """
```

**NOT RL-based. NOT PPO-based. Deterministic given its inputs — exhaustively testable with golden-value tests.** See `CONFIDENCE_FUSION.md` for the full worked example and edge-case table; this section mirrors its method signatures only.

---

## 6. Risk Management Layer

```python
class RiskManagementLayer:
    def apply(self, fused_decision: FusedDecision) -> FinalRecommendation:
        """
        Enforces (authoritatively, regardless of upstream correctness):
          - long-only (all weights >= 0)
          - weights sum to 1.0 (within floating-point tolerance)
          - exposure caps (see CONFIGURATION.md)
        Passes `reasoning` and `confidence_summary` through from
        `fused_decision` UNCHANGED (ADR-019) — this method only transforms
        and validates `final_allocation` into `allocation`.
        """
```

**Testing requirement:** must be tested independent of whether upstream modules behave correctly — feed it a deliberately malformed `FusedDecision` (negative weights, weights not summing to 1) and confirm it still produces a valid `FinalRecommendation` with `reasoning`/`confidence_summary` correctly passed through.

---

## 7. Evaluation (ADR-021)

```python
class EvaluationEngine:
    def __init__(self, outcome_label_generator: OutcomeLabelGenerator):
        """Reuses the SAME OutcomeLabelGenerator instance used during
        training/calibration (ADR-024) — never a separate implementation."""

    def evaluate_financial(self, recommendations: list[FinalRecommendation],
                            realized_returns: "pd.Series") -> FinancialMetrics:
        """
        Computes Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Volatility,
        Cumulative Return over the given recommendation history and realized
        returns for the same period.
        Raises:
            EvaluationDataMismatchError: if recommendation timestamps and
            realized_returns index do not align.
        """

    def evaluate_calibration(self, confidence_history: list[CalibratedConfidence],
                              recommendation_history: list[AgentOutput],
                              realized_data: "pd.DataFrame") -> dict[str, CalibrationMetrics]:
        """
        For each agent: generates outcome labels via
        self.outcome_label_generator.generate_label(...) for each historical
        recommendation, then computes ECE, Brier score, and a reliability
        diagram against confidence_history. Returns one CalibrationMetrics
        per agent_name.
        """

    def run_ablation(self, ablation_name: str, **kwargs) -> dict[str, Any]:
        """Runs one of the ablations defined in EXPERIMENT_PLAN.md
        (e.g. "shuffled_confidence", "drop_one_agent", "equal_weight_vs_fused")."""

    def compare_baselines(self, baseline_results: dict[str, FinancialMetrics]) -> dict[str, Any]:
        """Compares this run's FinancialMetrics against the baseline results
        dict (1/N, buy-and-hold, static MVO, DeepTrader, MARS if attempted)."""

    def generate_report(self, financial: FinancialMetrics,
                         calibration: dict[str, CalibrationMetrics],
                         ablations: dict[str, Any] | None,
                         baselines: dict[str, FinancialMetrics] | None,
                         fold_id: str) -> EvaluationReport:
        """Assembles the above into one EvaluationReport."""
```

**File location:** `finrl/agents/ca_marl/evaluation.py`.

**Dependencies:** scikit-learn (calibration metric implementations), `OutcomeLabelGenerator` (reused from `confidence_engine.py`, not reimplemented), realized market data from the Data Pipeline.

**Failure cases:** insufficient data points for a metric (e.g., fewer than 2 points for Sortino) → return `NaN` for that metric with a logged `WARNING`, not a crash; `EvaluationDataMismatchError` on timestamp misalignment.

**Testing responsibilities:** unit-test each metric against synthetic, known-answer inputs — e.g., a synthetic perfectly-calibrated confidence stream should yield `ECE ≈ 0` (already specified narratively in `TESTING_STRATEGY.md` §4; now tied concretely to `EvaluationEngine.evaluate_calibration`).

---

## Integration Requirements Summary

- Every module boundary above is a Python-level call, not a network/service boundary — a monolithic pipeline (single process), not microservices, unless a future ADR changes that.
- Every module logs its inputs (summary, not full data), key decisions, and outputs per `CODING_STANDARDS.md`.
- No module skips a stage (`ARCHITECTURE.md` §3 "golden rules") — every call chain goes through the full sequence: Data → Features → 3 Agents → Confidence Estimation & Calibration → Confidence-Aware Decision Fusion → Risk Management Layer → Final Portfolio Recommendation → Evaluation.
- Config-driven: every constant referenced above (calibration method choice, epsilon values, exposure caps, reward function parameters, label horizons, prediction-consistency *k*) resolves from `configs/*.yaml`, never hardcoded (`CONFIGURATION.md`).
- **No field in any dataclass above is typed `Any` or documented as `TBD`**, except the intentionally open-ended `metadata`/`fusion_metadata` auxiliary fields (Design Review success criteria).

---

**Related documents:** [AGENTS.md](./AGENTS.md) · [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md) · [CONFIDENCE_FUSION.md](./CONFIDENCE_FUSION.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) · [CONFIGURATION.md](./CONFIGURATION.md) · [DECISIONS.md](./DECISIONS.md)
