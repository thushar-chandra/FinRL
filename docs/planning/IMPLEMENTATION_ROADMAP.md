# IMPLEMENTATION_ROADMAP.md

> Implementation order and dependencies only — **no timeline/day estimates** (ADR-018). No developer/team assignments (ADR-017). Task-level breakdown lives in [TASKS.md](./TASKS.md); current status lives in [CURRENT_STATE.md](./CURRENT_STATE.md); narrative version lives in [SYSTEM_WORKFLOW.md](./SYSTEM_WORKFLOW.md).

---

## Stage 1 — Data Foundation

- **Objective:** Data Pipeline → Feature Engineering (including regime features) → walk-forward validation scaffolding → testing.
- **Files affected:** `finrl/meta/data_processors/`, `finrl/meta/preprocessor/`, `finrl/meta/meta_config_tickers.py`, `configs/universe.yaml`, `configs/features.yaml`, `tests/unit/test_data_pipeline.py`, `tests/unit/test_feature_engineering.py`.
- **Dependencies:** none (first stage).
- **Acceptance criteria:** pipeline downloads the fixed universe + Nifty 50 with one consistent, validated, versioned schema; full feature set (technical indicators, volatility, returns, **and regime features** — bull/bear, volatility regime, trend regime, market-state) produced; the mandatory no-lookahead leakage test passes for every rolling/EWMA/regime feature.
- **Testing:** `test_data_pipeline.py`, `test_feature_engineering.py` (leakage test is the single highest-priority test in this stage — do not proceed to Stage 2 until it is green).
- **Risk:** leakage bugs are easy to introduce silently and hard to catch by inspection; yfinance API flakiness/rate limits (mitigate with caching).

## Stage 2 — Specialized Reinforcement Learning Agents

- **Objective:** implement Market Analysis Agent → Risk Assessment Agent → Portfolio Allocation Agent, each as a reinforcement learning agent implemented within the FinRL ecosystem, trained via Stable-Baselines3 PPO (ADR-013). Each agent consumes Feature Engineering output only — the Portfolio Allocation Agent does **not** take Market/Risk agent outputs as input (ADR-025, resolving a previously-open cross-agent dependency question). Shared vs. independent PPO training infrastructure is decided during this stage.
- **Files affected:** `finrl/agents/ca_marl/market_agent.py`, `risk_agent.py`, `allocation_agent.py`, optionally `rl_training_utils.py`, `configs/agents.yaml`, `configs/ppo.yaml`.
- **Dependencies:** Stage 1.
- **Acceptance criteria:** each agent produces the common output contract (`AGENTS.md`, `INTERFACE_CONTRACTS.md`) without exceptions, including `metadata["reward_stability"]` and a working `prediction_consistency()` method (ADR-023); training sanity checks pass; deterministic tie-break/fallback behavior documented and tested.
- **Testing:** `test_market_agent.py`, `test_risk_agent.py`, `test_allocation_agent.py`, including `prediction_consistency()` unit tests.
- **Risk:** RL training instability/non-convergence; monitor closely rather than assuming convergence.

## Stage 3 — Confidence & Fusion

- **Objective:** implement Confidence Estimation & Calibration — one combined module (ADR-022), including the `OutcomeLabelGenerator` (ADR-024) — then Confidence-Aware Decision Fusion, using the `AssetWeightProposal` transform functions and worked algorithm defined in `CONFIDENCE_FUSION.md` (ADR-020). This stage carries the project's central research contribution.
- **Files affected:** `finrl/agents/ca_marl/confidence_engine.py` (both `ConfidenceEngine` and `OutcomeLabelGenerator`), `confidence_fusion.py`, `configs/confidence.yaml`, `tests/unit/test_confidence_engine.py`, `test_confidence_fusion.py`.
- **Dependencies:** Stage 2 (needs all three agents' outputs and training-derived signals).
- **Acceptance criteria:** raw confidence computed from historical accuracy (via `OutcomeLabelGenerator`), reward stability, and prediction consistency; calibration fit strictly on `is_eligible_for_fold()`-eligible pairs (the mandatory calibration-leakage test passes); ECE/Brier/reliability diagnostics computed and sane; Confidence-Aware Decision Fusion reproduces the `CONFIDENCE_FUSION.md` worked numeric example exactly, and handles the `Σ(Confidence)=0` and per-agent proposal fallbacks correctly. PPO must never appear in the fusion code path.
- **Testing:** `test_confidence_engine.py` (incl. calibration-leakage test against the concrete ADR-024 rule), `test_confidence_fusion.py` (golden-value tests, including the worked example).
- **Risk:** this is where the project's central research claim lives — insufficient rigor here undermines everything downstream.

## Stage 4 — Risk Management, Evaluation & Experiments

- **Objective:** implement the Risk Management Layer (passing `reasoning`/`confidence_summary` through unchanged, ADR-019); implement `EvaluationEngine` (ADR-021) — financial metrics, calibration metrics (reusing the Stage 3 `OutcomeLabelGenerator`), ablation support, baseline comparison; implement baselines and run the mandatory ablations.
- **Files affected:** `finrl/agents/ca_marl/risk_management.py`, `evaluation.py`, `experiments/baselines/`, `experiments/ablations/`.
- **Dependencies:** Stage 3.
- **Acceptance criteria:** Risk Management Layer enforces long-only/sum-to-one/exposure caps authoritatively, tested independent of upstream correctness (feed it deliberately malformed input and confirm valid output, including correct `reasoning`/`confidence_summary` pass-through); `EvaluationEngine`'s metric functions pass synthetic known-answer tests; baselines (1/N, buy-and-hold, static MVO, DeepTrader committed, MARS stretch goal) run against the same walk-forward folds; mandatory ablations (`EvaluationEngine.run_ablation("shuffled_confidence")`, `run_ablation("drop_one_agent")`) implemented and reported honestly regardless of outcome direction.
- **Testing:** financial validation tests (`TESTING_STRATEGY.md` §5), full ablation suite (`EXPERIMENT_PLAN.md`).
- **Risk:** transaction-cost consistency between training reward and backtest evaluation; MARS reproduction-fidelity risk (stretch goal only).

## Stage 5 — Integration

- **Objective:** end-to-end integration of all prior stages; bug fixing; documentation finalization.
- **Files affected:** `finrl/main.py`, `tests/integration/test_end_to_end_pipeline.py`, `test_interface_contracts.py`, all `docs/*.md` (final consistency pass).
- **Dependencies:** Stages 1–4.
- **Acceptance criteria:** full pipeline runs from raw data to final recommendation without exceptions; `INTERFACE_CONTRACTS.md` schemas validated end-to-end; documentation (`CURRENT_STATE.md`, `RESEARCH_MAPPING.md`) reflects the as-built system with no contradictions.
- **Testing:** `test_end_to_end_pipeline.py`, `test_interface_contracts.py`.
- **Risk:** integration-time discovery of mismatches between stages implemented in isolation — mitigated by `INTERFACE_CONTRACTS.md` being the shared, frozen contract every stage builds against.

---

**Related documents:** [SYSTEM_WORKFLOW.md](./SYSTEM_WORKFLOW.md) · [TASKS.md](./TASKS.md) · [CURRENT_STATE.md](./CURRENT_STATE.md) · [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) · [EXPERIMENT_PLAN.md](./EXPERIMENT_PLAN.md)
