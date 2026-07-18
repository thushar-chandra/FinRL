# AGENTS.md

> Engineering-facing specification: Python classes, interfaces, API contracts, configuration, failure cases, testing. Research-facing detail (purpose, theory, mathematical formulation, assumptions) lives in [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md) — cross-referenced below, not duplicated. Concrete method signatures and data structures live in [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md), including the Class → File map. Read after [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Common Output Contract

Every agent (Market Analysis, Risk Assessment, Portfolio Allocation) returns this schema. Never break it without an ADR (see `DECISIONS.md`). Full method-level contract: `INTERFACE_CONTRACTS.md`.

```json
{
  "agent_name": "market_agent",
  "recommendation": "...",
  "confidence": 0.0,
  "raw_confidence": 0.0,
  "reasoning": "...",
  "timestamp": "2026-07-17T00:00:00Z",
  "metadata": {}
}
```

- `confidence`/`raw_confidence` are scalar floats per agent (ADR-020) — never a per-asset dict.
- `confidence` is populated by Confidence Calibration; agents themselves only populate `raw_confidence`-relevant signals (see §4 below).
- `metadata` is intentionally open-ended (TODO: finalize per-agent metadata schema — flexible per `DECISIONS.md` "What Can Change"), except `metadata["reward_stability"]` and `metadata["tie_break_reason"]`, which are required keys per `INTERFACE_CONTRACTS.md`.

---

## 1. Market Analysis RL Agent

**Purpose / theory / assumptions:** see `MODULE_SPECIFICATIONS.md` §1.

**Class/interface:** `MarketAnalysisAgent` (`finrl/agents/ca_marl/market_agent.py` — see `INTERFACE_CONTRACTS.md` Class → File map). Implemented as a reinforcement learning agent within the FinRL ecosystem, trained via Stable-Baselines3 PPO (ADR-013). Whether this agent shares training infrastructure with the Risk/Allocation agents or is trained independently is an implementation decision.

**Inputs:** processed feature DataFrame from Feature Engineering — technical indicators (RSI, MACD, EMA/SMA, volume) **and regime features** (bull/bear indicator, volatility regime, trend regime, market-state features; ADR-016 — no separate Regime Module).

**Outputs:** recommendation (BUY/SELL/HOLD-style, per asset) + `metadata["reward_stability"]` + reasoning. Exact schema: `INTERFACE_CONTRACTS.md` §1.

**Configuration:** hyperparameters, reward function, network architecture, and label horizon live in config (`configs/*.yaml`) — never hardcoded.

**Failure cases:** insufficient training data/history (`InsufficientHistoryError`, not a silent default); training instability/non-convergence (documented sanity check, not discovered only at evaluation time); ambiguous output at inference time — deterministic tie-break, recorded in `metadata["tie_break_reason"]`.

**Testing:** see `TESTING_STRATEGY.md` — output-contract compliance; RL-specific sanity checks (reward trending sanely, no NaN policy outputs); `prediction_consistency()` unit-tested against synthetic near-identical states (should return a high score) and synthetic wildly-varying states (should return a low score).

**Communication with other modules:** feeds Confidence Estimation & Calibration and Confidence-Aware Decision Fusion directly. Does not call other agents (ADR-025).

---

## 2. Risk Assessment RL Agent

**Purpose / theory / assumptions:** see `MODULE_SPECIFICATIONS.md` §2.

**Class/interface:** `RiskAssessmentAgent` (`finrl/agents/ca_marl/risk_agent.py`). Reinforcement learning agent within FinRL, PPO-trained (ADR-013).

**Inputs:** feature DataFrame including volatility/return features and regime features.

**Outputs:** `{expected_volatility, risk_score}` per asset + `metadata["reward_stability"]` + reasoning.

**Configuration:** see `configs/*.yaml`.

**Failure cases:** insufficient history for volatility warm-up; regime-boundary discontinuities smoothed at the feature-engineering level, not inside this agent.

**Testing:** see `TESTING_STRATEGY.md`; `prediction_consistency()` unit-tested via the coefficient-of-variation formula (ADR-023).

**Communication with other modules:** feeds Confidence Estimation & Calibration and Confidence-Aware Decision Fusion directly. Does not call other agents.

---

## 3. Portfolio Allocation RL Agent

**Purpose / theory / assumptions:** see `MODULE_SPECIFICATIONS.md` §3.

**Class/interface:** `PortfolioAllocationAgent` (`finrl/agents/ca_marl/allocation_agent.py`). Reinforcement learning agent within FinRL, PPO-trained (ADR-013).

**Inputs:** feature DataFrame + regime features **only** — per ADR-025, this agent does **not** take Market or Risk agent outputs as input. Its observation space is symmetric with the other two agents.

**Outputs:** per-asset allocation weights (not guaranteed long-only/sum-to-one at this layer — deferred to Risk Management Layer) + `metadata["reward_stability"]` + reasoning.

**Configuration:** see `configs/*.yaml`.

**Failure cases:** degenerate/infeasible output must be returned as-is, not raised as an error or clipped here — enforcement is exclusively the Risk Management Layer's job (§6 below).

**Testing:** see `TESTING_STRATEGY.md`; `prediction_consistency()` as in §2.

**Communication with other modules:** feeds Confidence Estimation & Calibration and Confidence-Aware Decision Fusion directly. Does not consume, and is not consumed by, the Market or Risk agents (ADR-025).

---

## 4. Confidence Estimation & Calibration (one combined module — ADR-022)

**Purpose / theory:** see `MODULE_SPECIFICATIONS.md` §4. **Never makes an investment decision.**

**Class/interface:** `ConfidenceEngine` (`finrl/agents/ca_marl/confidence_engine.py`), which also owns `OutcomeLabelGenerator` (same file, ADR-024). Both classes and their exact methods: `INTERFACE_CONTRACTS.md` §4.

**Inputs:** all three agents' `AgentOutput`s (recommendation, `metadata["reward_stability"]`, and each agent's own `prediction_consistency()` result) plus realized market data (via `OutcomeLabelGenerator`, for historical accuracy).

**Responsibilities:** `OutcomeLabelGenerator` computes per-recommendation outcome labels once realized data covers the label horizon, and gates which (confidence, label) pairs are eligible for calibration fitting in a given walk-forward fold (ADR-024's leakage rule). `ConfidenceEngine.estimate_raw_confidence()` combines historical accuracy + reward stability + prediction consistency into a scalar raw confidence per agent. `fit_calibration()`/`calibrate()` normalize and calibrate (Platt/temperature scaling — method choice is an implementation detail, record final choice in `DECISIONS.md`) and produce ECE/Brier/reliability diagnostics.

**Outputs:** `CalibratedConfidence` (scalar per agent) + diagnostics, passed to Confidence-Aware Decision Fusion. Reused by Evaluation (§7) via the same `OutcomeLabelGenerator` instance.

**Failure cases:** cold-start (insufficient track record in a regime bucket) → uninformative-prior fallback (0.5), logged; `LabelNotYetResolvableError` if a label is requested before its horizon has elapsed.

**Testing:** see `TESTING_STRATEGY.md`, including the mandatory calibration-leakage test, now checkable directly against `OutcomeLabelGenerator.is_eligible_for_fold()`.

**Communication with other modules:** consumes from all three RL agents; produces to Confidence-Aware Decision Fusion; `OutcomeLabelGenerator` is also called by Evaluation.

---

## 5. Confidence-Aware Decision Fusion

**This module is documented in full, dedicated detail in [CONFIDENCE_FUSION.md](./CONFIDENCE_FUSION.md)** — the `AssetWeightProposal` intermediate representation, transform functions, worked numeric example, and `reasoning`/`confidence_summary` composition. Summary for cross-reference only:

- **Exclusively separate from PPO** (ADR-014, ADR-015) — deterministic, not RL-trained.
- **Class/interface:** `ConfidenceAwareFusion` (`finrl/agents/ca_marl/confidence_fusion.py`).
- **Inputs:** each agent's `AgentOutput` + `CalibratedConfidence`.
- **Process:** transform each agent's recommendation into an `AssetWeightProposal`, then apply `Final = Σ(Proposal × Confidence) / Σ(Confidence)` per asset (ADR-020) — guaranteed to sum to 1.
- **Outputs:** `FusedDecision`, including `final_allocation`, `reasoning`, and `confidence_summary` (ADR-019), passed to the Risk Management Layer.

See `CONFIDENCE_FUSION.md` for everything else.

---

## 6. Risk Management Layer

**Purpose / theory:** see `MODULE_SPECIFICATIONS.md` §6.

**Class/interface:** `RiskManagementLayer` (`finrl/agents/ca_marl/risk_management.py`). Method: `apply(fused_decision: FusedDecision) -> FinalRecommendation` — full signature: `INTERFACE_CONTRACTS.md` §6.

**Inputs:** `FusedDecision` from Confidence-Aware Decision Fusion.

**Responsibilities:** authoritatively enforce long-only (all weights ≥ 0), sum-to-one (within floating-point tolerance), and exposure caps (`configs/*.yaml`) on `final_allocation` — regardless of whether upstream modules already satisfied these properties. Pass `reasoning` and `confidence_summary` through **unchanged** (ADR-019) — this module only transforms/validates the allocation itself.

**Outputs:** `FinalRecommendation` ("Final Portfolio Recommendation" is the canonical prose term for this stage's output — ADR-026; `FinalRecommendation` is the accepted class-name shorthand).

**Failure cases:** none should propagate as exceptions — malformed input (negative weights, non-summing weights) must still produce a valid, constraint-satisfying `FinalRecommendation`, by construction of this layer's own enforcement logic.

**Testing:** must be tested independent of upstream correctness — feed it a deliberately malformed `FusedDecision` and confirm valid output, including correct pass-through of `reasoning`/`confidence_summary`. See `TESTING_STRATEGY.md` §5.

**Communication with other modules:** consumes from Confidence-Aware Decision Fusion; produces to the final output and to Evaluation.

---

## 7. Evaluation

**Purpose / theory:** see `MODULE_SPECIFICATIONS.md` §7.

**Class/interface:** `EvaluationEngine` (`finrl/agents/ca_marl/evaluation.py`). Methods: `evaluate_financial()`, `evaluate_calibration()`, `run_ablation()`, `compare_baselines()`, `generate_report()` — full signatures: `INTERFACE_CONTRACTS.md` §7.

**Inputs:** a sequence of `FinalRecommendation` objects across a walk-forward fold's test window, realized market returns for the same period, the accumulated `CalibratedConfidence` history, and the **same** `OutcomeLabelGenerator` instance used during training (ADR-024 — never a separate implementation, to guarantee identical label definitions between calibration-fitting time and evaluation time).

**Responsibilities:** compute financial metrics (Sharpe, Sortino, Max Drawdown, Volatility, Cumulative Return), compute calibration metrics (ECE, Brier score, reliability diagrams) per agent, run the mandatory ablations (shuffled-confidence, drop-one-agent — `EXPERIMENT_PLAN.md`), compare against baselines, and assemble an `EvaluationReport`.

**Outputs:** `EvaluationReport` (financial metrics, per-agent calibration metrics, ablation results, baseline comparison).

**Configuration:** see `configs/*.yaml`.

**Failure cases:** insufficient data points for a given metric (e.g., Sortino with fewer than 2 points) → `NaN` for that metric, logged at `WARNING`, not a crash; `EvaluationDataMismatchError` on timestamp misalignment between recommendations and realized-return series.

**Testing:** unit-test each metric against synthetic known-answer inputs (e.g., a perfectly-calibrated synthetic confidence stream should yield `ECE ≈ 0` — `TESTING_STRATEGY.md` §4). This is the module responsible for the numbers reported in `RESEARCH_MAPPING.md`'s Experimental Results section, so its own correctness is treated with the same rigor as the two mandatory leakage tests.

**Communication with other modules:** consumes from the Risk Management Layer's output history and from Confidence Estimation & Calibration's `OutcomeLabelGenerator`; is the terminal stage of the pipeline.

---

**Related documents:** [ARCHITECTURE.md](./ARCHITECTURE.md) · [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md) · [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md) · [CONFIDENCE_FUSION.md](./CONFIDENCE_FUSION.md) · [DECISIONS.md](./DECISIONS.md) · [TESTING_STRATEGY.md](../implementation/TESTING_STRATEGY.md)
