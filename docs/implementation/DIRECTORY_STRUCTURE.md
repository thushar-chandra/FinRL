# DIRECTORY_STRUCTURE.md

> Complete target repository structure, forked from FinRL. Status tags: **[EXISTING]**, **[MODIFIED]**, **[NEW]**, **[GENERATED]**, **[THIRD-PARTY]**. Cross-reference: [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) and [FINRL_MAPPING.md](./FINRL_MAPPING.md) for the reasoning behind each FinRL-folder decision. This repository represents one complete engineering implementation — no per-developer ownership is tracked here (ADR-017).

```
ca-marl/
├── docs/                                   [NEW] this knowledge base
│   ├── PROJECT_CONTEXT.md
│   ├── ARCHITECTURE.md
│   ├── MODULE_SPECIFICATIONS.md            research-facing module spec
│   ├── AGENTS.md                           engineering-facing module spec
│   ├── INTERFACE_CONTRACTS.md              implementation contract
│   ├── CONFIDENCE_FUSION.md                dedicated fusion-module spec
│   ├── FINRL_MAPPING.md                    functional FinRL reuse mapping
│   ├── SYSTEM_WORKFLOW.md                  narrative build/run-time workflow
│   ├── DIRECTORY_STRUCTURE.md              (this file)
│   ├── MIGRATION_PLAN.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── CURRENT_STATE.md
│   ├── DECISIONS.md
│   ├── CODING_STANDARDS.md
│   ├── TESTING_STRATEGY.md
│   ├── RESEARCH_MAPPING.md
│   ├── EXPERIMENT_PLAN.md
│   ├── CONFIGURATION.md
│   ├── TASKS.md
│   ├── OPENCODE.md
│   ├── HANDOFF.md
│   └── PROMPT_HISTORY.md
│
├── README.md
│
├── finrl/                                   [EXISTING base, MODIFIED contents below]
│   ├── meta/
│   │   ├── data_processors/                 [EXISTING] KEEP
│   │   ├── preprocessor/                    [MODIFIED] extend indicators + regime features (no standalone regime module — ADR-016)
│   │   ├── env_portfolio_allocation/         [MODIFIED] extend observation space for regime features / cross-agent signals
│   │   ├── env_stock_trading/               [IGNORED]
│   │   ├── env_cryptocurrency_trading/      [IGNORED]
│   │   ├── data_processor.py                [MODIFIED] schema + validation
│   │   ├── meta_config.py                   [MODIFIED] fixed-universe config
│   │   └── meta_config_tickers.py           [MODIFIED] Indian large-cap universe + Nifty 50 — list/date TODO
│   │
│   ├── agents/
│   │   ├── stablebaseline3/                 [EXISTING, ACTIVELY USED] PPO training infrastructure for all three specialized agents (ADR-013)
│   │   ├── elegantrl/                        [IGNORED]
│   │   ├── rllib/                            [IGNORED]
│   │   └── ca_marl/                          [NEW] all CA-MARL-specific modules — see INTERFACE_CONTRACTS.md's Class -> File map for the authoritative class/file binding
│   │       ├── __init__.py                   [NEW]
│   │       ├── market_agent.py               [NEW] MarketAnalysisAgent
│   │       ├── risk_agent.py                 [NEW] RiskAssessmentAgent
│   │       ├── allocation_agent.py           [NEW] PortfolioAllocationAgent (features-only input, ADR-025 - no cross-agent dependency)
│   │       ├── rl_training_utils.py          [NEW] shared PPO training utilities, IF the implementation chooses shared infrastructure (ADR-013 — implementation-neutral, not mandated)
│   │       ├── confidence_engine.py          [NEW] ConfidenceEngine + OutcomeLabelGenerator (one combined module, ADR-022; OutcomeLabelGenerator owned here per ADR-024 and reused by evaluation.py)
│   │       ├── confidence_fusion.py          [NEW] ConfidenceAwareFusion — deterministic, NOT PPO-based, incl. AssetWeightProposal transform functions (see CONFIDENCE_FUSION.md)
│   │       ├── risk_management.py            [NEW] RiskManagementLayer (long-only / sum-to-one / exposure caps; passes reasoning/confidence_summary through unchanged, ADR-019)
│   │       ├── evaluation.py                 [NEW] EvaluationEngine (financial + calibration metrics, ablations, baselines — ADR-021)
│   │       ├── contracts.py                  [NEW] shared dataclasses/schemas (INTERFACE_CONTRACTS.md — AgentOutput, CalibratedConfidence, FusedDecision, FinalRecommendation, FinancialMetrics, CalibrationMetrics, EvaluationReport)
│   │       └── config_schema.py              [NEW] typed config loader
│   │
│   ├── applications/
│   │   ├── portfolio_allocation/            [MODIFIED] CA-MARL pipeline entrypoint
│   │   ├── stock_trading/                   [IGNORED]
│   │   ├── cryptocurrency_trading/          [IGNORED]
│   │   ├── high_frequency_trading/          [IGNORED]
│   │   └── imitation_learning/              [IGNORED]
│   │
│   ├── config.py                            [MODIFIED]
│   ├── config_tickers.py                    [MODIFIED]
│   ├── main.py                              [MODIFIED] CA-MARL pipeline entrypoint
│   ├── train.py                             [MODIFIED] walk-forward training loop (trains 3 RL agents)
│   ├── test.py                              [MODIFIED] walk-forward evaluation loop
│   └── trade.py                             [REMOVED] live/paper execution out of scope
│
├── configs/                                  [NEW]
│   ├── universe.yaml                        [NEW] fixed ticker list + as-of date (TODO)
│   ├── features.yaml                        [NEW] feature engineering + regime-feature parameters
│   ├── agents.yaml                          [NEW] per-agent hyperparameters, reward function parameters
│   ├── confidence.yaml                      [NEW] calibration method, confidence-input weighting (if any)
│   ├── ppo.yaml                             [NEW] PPO hyperparameters — shared or per-agent sections depending on implementation choice
│   └── walk_forward.yaml                    [NEW] fold count, window sizes, retrain cadence (TODO)
│
├── tests/                                    [MODIFIED/NEW]
│   ├── unit/
│   │   ├── test_data_pipeline.py            [NEW]
│   │   ├── test_feature_engineering.py      [NEW] incl. mandatory leakage test, incl. regime features
│   │   ├── test_market_agent.py             [NEW]
│   │   ├── test_risk_agent.py               [NEW]
│   │   ├── test_allocation_agent.py         [NEW]
│   │   ├── test_confidence_engine.py        [NEW] incl. calibration leakage test
│   │   └── test_confidence_fusion.py        [NEW] deterministic — exhaustive golden-value tests
│   ├── integration/
│   │   ├── test_end_to_end_pipeline.py      [NEW]
│   │   └── test_interface_contracts.py      [NEW] validates INTERFACE_CONTRACTS.md schemas
│   └── environments/
│       └── test_env_cashpenalty.py          [EXISTING] KEEP if relevant
│
├── notebooks/                                [MODIFIED]
│   ├── 01_data_exploration.ipynb            [NEW]
│   ├── 02_calibration_diagnostics.ipynb      [NEW]
│   └── 03_ablation_results.ipynb            [NEW]
│
├── experiments/                              [NEW, GENERATED]
│   ├── baselines/                           [GENERATED]
│   ├── ablations/                           [GENERATED]
│   └── figures/                             [GENERATED]
│
├── pyproject.toml / requirements.txt        [MODIFIED]
├── .pre-commit-config.yaml                  [EXISTING] KEEP
└── LICENSE                                  [EXISTING] MIT
```

## Third-Party Dependencies
- **FinRL** (base fork) — MIT
- **Stable-Baselines3**, **Gymnasium** — MIT — PPO training for all three agents
- **scikit-learn** — BSD-3-Clause — calibration utilities
- **scipy**, **cvxpy** — optimization utilities where needed
- **PyPortfolioOpt** (if retained, e.g. as a baseline/reference) — MIT
- **stockstats** (optional) — BSD-3-Clause — feature engineering acceleration
- **pandas**, **numpy**, **yfinance** — see `CONFIGURATION.md`

---

**Related documents:** [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) · [FINRL_MAPPING.md](./FINRL_MAPPING.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md) · [CONFIGURATION.md](./CONFIGURATION.md)
