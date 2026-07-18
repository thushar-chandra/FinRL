# MODULE_SPECIFICATIONS.md

> Research-facing specification: purpose, theory, mathematical formulation, inputs/outputs, assumptions — for every module. Engineering-facing detail (classes, interfaces, API contracts, configuration, failure cases, testing) lives in [AGENTS.md](./AGENTS.md); concrete method signatures live in [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md). Cross-referenced throughout; content is intentionally not duplicated between these documents.

---

## 1. Market Analysis RL Agent

**Purpose:** learn a market-direction recommendation policy (BUY/SELL/HOLD-style) from historical price/feature dynamics.

**Theory:** frames market-timing as a sequential decision problem, fitting reinforcement learning's core setup (sequential decisions, delayed reward, no single "correct" label). Same founding rationale as `DECISIONS.md` ADR-001, applied at the individual-agent level.

**Mathematical formulation:** state = feature vector at time *t* (technical indicators + regime features), action = recommendation, reward = a function of subsequent realized return (reward shaping informed by DeepTrader's precedent, `RESEARCH_MAPPING.md`). Trained via PPO (Schulman et al., 2017).

**Inputs:** engineered features from Feature Engineering, including regime features (bull/bear indicator, volatility regime, trend regime, market-state features — ADR-016).

**Outputs:** a recommendation plus signals for confidence estimation — reward stability (a natural training-process by-product) and prediction consistency (§4 below).

**Assumptions:** markets exhibit enough exploitable short/medium-term structure for an RL policy to learn better-than-random timing; daily-frequency data provides sufficient signal.

---

## 2. Risk Assessment RL Agent

**Purpose:** learn to estimate portfolio/asset-level risk and volatility, and detect elevated uncertainty — not to maximize return.

**Theory:** the relationship between observable features and realized risk may be regime-dependent; an RL formulation lets risk-estimation behavior be shaped by a reward signal tied to forecast accuracy, rather than fixed a priori.

**Mathematical formulation:** state = feature vector (volatility, return, regime features), action = a risk estimate, reward = a function of forecast accuracy against realized volatility. Trained via PPO.

**Inputs:** feature DataFrame including volatility/return features and regime features.

**Outputs:** risk assessment plus training-derived confidence-estimation signals.

**Assumptions:** realized volatility and drawdown history are meaningful proxies for "risk" (MPT-concept-informed, without performing full mean-variance optimization — that's the Allocation Agent's job, no overlap).

---

## 3. Portfolio Allocation RL Agent

**Purpose:** learn per-asset allocation weights (long-only, sum-to-one) rather than directional or risk-only signals.

**Theory:** allocation is where market-direction and risk information must ultimately combine into a concrete, constrained decision — but per ADR-025, that combination happens explicitly in Confidence-Aware Decision Fusion, not by feeding Market/Risk agent outputs directly into this agent's own observation space. Keeping this agent's input symmetric with the other two (Feature Engineering output only) avoids a moving-target training problem that would otherwise arise if this agent's policy depended on two other simultaneously-updating policies.

**Mathematical formulation:** state = feature vector + regime features (no cross-agent inputs — ADR-025), action = a weight vector (post-processed to satisfy long-only/sum-to-one *authoritatively* by the Risk Management Layer, never assumed satisfied here), reward = risk-adjusted realized return. Trained via PPO.

**Inputs:** feature DataFrame + regime features only.

**Outputs:** allocation weights plus training-derived confidence-estimation signals.

**Assumptions:** a learned allocation policy, conditioned on the same engineered features as the other two agents, can still produce a useful allocation proposal even without directly observing the other agents' outputs — the combination of perspectives happens downstream in fusion (ADR-020), which is the correct place for it, not duplicated inside this agent's policy.

---

## 4. Confidence Estimation & Calibration (one combined module — ADR-022)

**Purpose:** quantify how much each agent's recommendation should be trusted, and place that trust estimate on a comparable, validated scale across agents.

**Theory:** the project's central research motivation is that most portfolio RL systems answer "what to do" without answering "how much to trust it." This module operationalizes "trust" as a calibrated probability-like quantity: a confidence score is well-calibrated if, among all instances assigned confidence *c*, the empirical rate of validated outcomes is approximately *c* (Guo et al., 2017).

**Mathematical formulation — three raw confidence inputs (scalar per agent, ADR-020):**

1. **Historical accuracy** — rolling empirical correctness rate of the agent's recommendations against the outcome label (table below), restricted to labels that have actually resolved.
2. **Reward stability** — `1 / variance(recent realized rewards)`, exposed by each agent via `metadata["reward_stability"]` (a natural by-product of RL training).
3. **Prediction consistency** (operationalized per ADR-023 — resolves the previously-unspecified gap):
   - **What it measures:** how stable an agent's recommendation is under small perturbations of its input state — a proxy for policy decisiveness/reproducibility, distinct from historical correctness.
   - **Why it matters:** a policy that flips its recommendation under near-identical conditions is less trustworthy even if it happens to have a good historical accuracy score by chance; this input catches that failure mode.
   - **How it is computed:** sample the agent's policy on *k* nearby historical states within the same regime bucket as the current state (*k* is configured in `configs/confidence.yaml`). For continuous outputs (risk scores, weights): `consistency = 1 − coefficient_of_variation` across the *k* samples. For categorical outputs (BUY/SELL/HOLD): `consistency = (fraction of the k samples agreeing with the modal recommendation)`.
   - **Inputs:** the agent's own policy (callable), the current state, *k* nearby states from the same regime bucket.
   - **Outputs:** a scalar in [0,1] per agent per timestep.
   - **Storage:** accumulated in the same rolling, per-agent, per-regime-bucket history structure as historical accuracy and reward stability.
   - **Use within confidence estimation:** one of the three inputs combined into `raw_confidence` (combination function — e.g. weighted average, and its weights — is an implementation detail; record the final choice in `DECISIONS.md`).
   - **Interaction with calibration:** consistency itself is not separately calibrated; it is only calibrated as part of the combined `raw_confidence` value.

**Outcome label per agent type** (needed for historical accuracy and calibration ground truth):

| Agent | Outcome label |
|---|---|
| Market Analysis | Sign/magnitude of subsequent forward return vs. recommendation direction |
| Risk Assessment | Realized volatility within predicted band |
| Portfolio Allocation | Realized risk-adjusted return of proposed weights vs. a reference (e.g., equal-weight) |

**Outcome Label Generator — ownership, timing, leakage prevention (ADR-024):** a single `OutcomeLabelGenerator` component, owned by this module, is the *sole* implementation of the table above — reused, never reimplemented, by Evaluation (§7). A label for a recommendation made at time *t* is generated once realized market data covering that recommendation's label horizon (*t + N*, *N* configured per agent type) becomes available. **Leakage rule:** a (confidence, label) pair is eligible for calibration fitting in walk-forward fold *F* if and only if `recommendation.timestamp + label_horizon ≤ F.training_window.end`; pairs whose horizon extends past the fold's training window end are excluded from that fold (they become eligible in a later fold). This same component and rule are used identically at evaluation time, guaranteeing training-time calibration and test-time evaluation share one definition of "correct."

**Calibration mapping:** raw confidence → calibrated confidence via Platt scaling or temperature scaling (method choice is an implementation detail).

**Diagnostics:** Expected Calibration Error (ECE), Brier score, reliability diagrams.

**Inputs:** all three agents' recommendations, `metadata["reward_stability"]`, `prediction_consistency()` results, and realized market data (via `OutcomeLabelGenerator`).

**Outputs:** calibrated confidence per agent, plus diagnostics.

**Assumptions:** confidence is learnable and meaningfully calibratable from the three input signals above (flagged "Needs Validation" in `DECISIONS.md`'s Assumption Audit — a claim the calibration diagnostics must support empirically).

---

## 5. Confidence-Aware Decision Fusion

**This is the project's primary research contribution.** Full detail — the `AssetWeightProposal` intermediate representation, per-agent transform functions, the worked numeric example, and `reasoning`/`confidence_summary` composition — lives in [CONFIDENCE_FUSION.md](./CONFIDENCE_FUSION.md). Summary for cross-reference:

**Purpose:** combine the three agents' recommendations into a single decision, weighted by calibrated confidence, rather than combining them with equal weight.

**Theory:** operationalizes the project's founding analogy — asking three analysts for advice and naturally weighting the more reliable one's opinion more heavily, rather than averaging blindly.

**Mathematical formulation (ADR-020, fully resolved — no remaining ambiguity):** each agent's heterogeneous recommendation is first transformed into a common intermediate representation, `AssetWeightProposal` (a per-asset weight vector, non-negative, sums to 1), via a deterministic, agent-specific transform function. The fusion formula `Final[asset] = Σ_agent(Proposal_agent[asset] × Confidence_agent) / Σ_agent(Confidence_agent)` is then applied directly on these three proposal vectors, per asset — a construction that is provably guaranteed to sum to 1 across assets (proof in `CONFIDENCE_FUSION.md`).

**Assumptions:** a deterministic, confidence-weighted average over transformed proposals is a sufficient fusion mechanism for this project's scope (an explicit design choice, with a learned-fusion alternative noted as future work, not current scope).

---

## 6. Risk Management Layer

**Purpose:** enforce portfolio-level constraints on the fused decision before it becomes the Final Portfolio Recommendation — long-only, weight normalization, portfolio validation, risk limits.

**Theory:** even if every upstream module behaves correctly, the fused decision must be authoritatively constrained at this layer — this is what guarantees the "recommendation, not execution" framing always produces a valid, investable portfolio object regardless of any upstream anomaly.

**Mathematical formulation:** projection of the fused weight vector onto the long-only simplex (clipping/renormalization), plus any additional exposure-cap constraints (`CONFIGURATION.md`). `reasoning` and `confidence_summary` are passed through unchanged (ADR-019) — this layer's mathematical work is confined to the allocation vector itself.

**Inputs:** `FusedDecision` from Confidence-Aware Decision Fusion.

**Outputs:** the Final Portfolio Recommendation (canonical prose term, ADR-026; `FinalRecommendation` is the class-name shorthand).

**Assumptions:** simple projection/renormalization is sufficient for constraint satisfaction (vs. a more complex constrained-optimization re-solve) — acceptable for v1 scope, consistent with the project's stated preference for simplicity over unnecessary sophistication.

---

## 7. Evaluation (ADR-021)

**Purpose:** measure both financial performance and calibration quality of the full pipeline, and support the mandatory ablations and baseline comparisons that this project's research claims depend on.

**Theory:** a decision-support system whose central claim is "confidence is calibrated and functionally useful" is only as credible as the evaluation that measures those two properties independently — financial metrics alone would only show that the system works, not that the confidence layer specifically is doing anything. Evaluation is therefore designed around two parallel measurement tracks (financial and calibration) plus a set of ablations designed to isolate the confidence layer's contribution specifically.

**Mathematical formulation:**
- **Financial track:** standard portfolio performance metrics computed over a walk-forward fold's test-window recommendation history — Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Portfolio Volatility, Cumulative Return.
- **Calibration track:** using the *same* `OutcomeLabelGenerator` defined in §4 (never reimplemented separately, to guarantee training-time and evaluation-time "correctness" are defined identically), compute Expected Calibration Error, Brier score, and reliability diagrams per agent, over the test window.
- **Ablation track:** shuffled-confidence (does confidence-aware fusion actually outperform confidence-blind fusion?), drop-one-agent (does the three-agent decomposition add value?) — see `EXPERIMENT_PLAN.md` for the full ablation list and what each isolates.
- **Baseline track:** comparison against 1/N, buy-and-hold, static mean-variance, DeepTrader (committed), MARS (stretch goal) — same walk-forward folds.

**Inputs:** the Final Portfolio Recommendation history for a fold's test window, realized market returns for that period, the accumulated calibrated-confidence history, and the shared `OutcomeLabelGenerator`.

**Outputs:** a structured evaluation report combining all four tracks above.

**Assumptions:** walk-forward, fold-by-fold evaluation with multiple seeds is sufficient to characterize both financial and calibration performance without additional statistical machinery beyond what `EXPERIMENT_PLAN.md` already specifies (paired significance tests, confidence intervals).

---

**Related documents:** [AGENTS.md](./AGENTS.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md) · [CONFIDENCE_FUSION.md](./CONFIDENCE_FUSION.md) · [DECISIONS.md](./DECISIONS.md)
