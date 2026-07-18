# DIRECTORY_STRUCTURE.md

> Current repository structure, forked from FinRL. Status tags: **[EXISTING]** (present on disk), **[NEW]** (specified but not yet implemented), **[GENERATED]** (created at runtime), **[THIRD-PARTY]**. Cross-reference: [FINRL_MAPPING.md](../architecture/FINRL_MAPPING.md) for the reasoning behind each FinRL-folder decision. This repository represents one complete engineering implementation — no per-developer ownership is tracked here (ADR-017).

```
ca-marl/
├── docs/                                   [EXISTING] this knowledge base
│   ├── architecture/                       [EXISTING] architecture specifications
│   │   ├── ARCHITECTURE.md
│   │   ├── MODULE_SPECIFICATIONS.md            research-facing module spec
│   │   ├── AGENTS.md                           engineering-facing module spec
│   │   ├── INTERFACE_CONTRACTS.md              implementation contract
│   │   ├── CONFIDENCE_FUSION.md                dedicated fusion-module spec
│   │   ├── FINRL_MAPPING.md                    functional FinRL reuse mapping
│   │   ├── SYSTEM_WORKFLOW.md                  narrative build/run-time workflow
│   │   └── DECISIONS.md                        Architecture Decision Record
│   ├── implementation/                     [EXISTING] implementation guides
│   │   ├── CODING_STANDARDS.md
│   │   ├── DIRECTORY_STRUCTURE.md              (this file)
│   │   ├── OPENCODE.md
│   │   ├── PROMPT_HISTORY.md
│   │   └── TESTING_STRATEGY.md
│   ├── planning/                           [EXISTING] planning and state
│   │   ├── CURRENT_STATE.md
│   │   ├── HANDOFF.md
│   │   ├── IMPLEMENTATION_ROADMAP.md
│   │   └── TASKS.md
│   ├── research/                           [EXISTING] research documents
│   │   ├── BASELINE_ANALYSIS.md                 FinRL baseline validation report
│   │   ├── EXPERIMENT_PLAN.md
│   │   └── RESEARCH_MAPPING.md
│   └── source/                             [EXISTING] Sphinx-generated reference docs
│       └── reference/
│           ├── reference.md
│           └── publication.md
│
├── README.md                               [EXISTING] project README
│
├── finrl/                                   [EXISTING base, MODIFIED contents below]
│   ├── meta/
│   │   ├── data_processors/                 [EXISTING] KEEP
│   │   ├── preprocessor/                    [EXISTING] extend indicators + regime features (no standalone regime module — ADR-016)
│   │   ├── env_portfolio_allocation/         [EXISTING] extend observation space for regime features / cross-agent signals
│   │   ├── env_stock_trading/               [EXISTING]
│   │   ├── env_cryptocurrency_trading/      [EXISTING]
│   │   ├── data_processor.py                [EXISTING] schema + validation
│   │   ├── meta_config.py                   [EXISTING] fixed-universe config
│   │   └── meta_config_tickers.py           [EXISTING] Indian large-cap universe + Nifty 50 — list/date TODO
│   │
│   ├── agents/
│   │   ├── stablebaseline3/                 [EXISTING] PPO training infrastructure for all three specialized agents (ADR-013)
│   │   ├── elegantrl/                        [EXISTING]
│   │   ├── rllib/                            [EXISTING]
│   │   └── ca_marl/                          [NEW] all CA-MARL-specific modules — see INTERFACE_CONTRACTS.md Class -> File map
│   │       ├── __init__.py                   [NEW]
│   │       ├── market_agent.py               [NEW] MarketAnalysisAgent
│   │       ├── risk_agent.py                 [NEW] RiskAssessmentAgent
│   │       ├── allocation_agent.py           [NEW] PortfolioAllocationAgent (features-only input, ADR-025)
│   │       ├── rl_training_utils.py          [NEW] shared PPO training utilities (if chosen)
│   │       ├── confidence_engine.py          [NEW] ConfidenceEngine + OutcomeLabelGenerator (ADR-022, ADR-024)
│   │       ├── confidence_fusion.py          [NEW] ConfidenceAwareFusion — deterministic, NOT PPO-based (ADR-020)
│   │       ├── risk_management.py            [NEW] RiskManagementLayer (ADR-019)
│   │       ├── evaluation.py                 [NEW] EvaluationEngine (ADR-021)
│   │       ├── contracts.py                  [NEW] shared dataclasses/schemas
│   │       └── config_schema.py              [NEW] typed config loader
│   │
│   ├── applications/
│   │   ├── portfolio_allocation/            [EXISTING] CA-MARL pipeline entrypoint [NEW]
│   │   ├── stock_trading/                   [EXISTING]
│   │   ├── cryptocurrency_trading/          [EXISTING]
│   │   ├── high_frequency_trading/          [EXISTING]
│   │   └── imitation_learning/              [EXISTING]
│   │
│   ├── config.py                            [EXISTING] configuration constants
│   ├── config_tickers.py                    [EXISTING] ticker lists
│   ├── main.py                              [EXISTING] pipeline entry point
│   ├── train.py                             [EXISTING] training loop
│   ├── test.py                              [EXISTING] testing loop
│   └── trade.py                             [EXISTING] live/paper trading (to be removed per Stage 5)
│
├── configs/                                  [NEW] empty placeholder directories
│   ├── universe.yaml/                       [NEW] ticker list + as-of date (TODO)
│   ├── features.yaml/                       [NEW] feature engineering params
│   ├── agents.yaml/                         [NEW] per-agent hyperparameters
│   ├── confidence.yaml/                     [NEW] calibration method, confidence-input weighting
│   ├── ppo.yaml/                            [NEW] PPO hyperparameters
│   └── walk_forward.yaml/                   [NEW] fold count, window sizes (TODO)
│
├── tests/                                    [EXISTING]
│   ├── unit/
│   │   ├── test_data_pipeline.py            [NEW]
│   │   ├── test_feature_engineering.py      [NEW] incl. mandatory leakage test
│   │   ├── test_market_agent.py             [NEW]
│   │   ├── test_risk_agent.py               [NEW]
│   │   ├── test_allocation_agent.py         [NEW]
│   │   ├── test_confidence_engine.py        [NEW] incl. calibration leakage test
│   │   └── test_confidence_fusion.py        [NEW] deterministic golden-value tests
│   ├── integration/
│   │   ├── test_end_to_end_pipeline.py      [NEW]
│   │   └── test_interface_contracts.py      [NEW]
│   └── environments/
│       └── test_env_cashpenalty.py          [EXISTING]
│
├── notebooks/                                [EXISTING]
│   ├── 01_data_exploration.ipynb            [NEW]
│   ├── 02_calibration.ipynb                 [NEW]
│   └── 03_results.ipynb                     [NEW]
│
├── experiments/                              [EXISTING]
│   ├── baselines/                           [EXISTING] empty
│   ├── ablations/                           [EXISTING] empty
│   └── New folder/                          [EXISTING] empty
│
├── trained_models/                           [EXISTING] baseline models
│   ├── agent_a2c.zip
│   ├── agent_a2c_test.zip
│   ├── agent_ddpg.zip
│   ├── agent_ppo.zip
│   └── agent_ppo_test.zip
│
├── results/                                  [GENERATED] baseline results
│   ├── a2c/
│   ├── a2c_test/
│   ├── a2c_test2/
│   ├── ddpg/
│   ├── ppo/
│   ├── ppo_test/
│   ├── ppo_test2/
│   └── td3/
│
├── pyproject.toml / requirements.txt        [EXISTING]
├── setup.py / setup.cfg                     [EXISTING]
├── poetry.lock                              [EXISTING]
├── .pre-commit-config.yaml                  [EXISTING]
├── .gitattributes                           [EXISTING]
├── .gitignore                               [EXISTING]
├── .vscode/                                 [EXISTING]
├── .github/                                 [EXISTING]
├── docker/                                  [EXISTING]
├── backtest_result.png                      [GENERATED]
├── train_data.csv                           [GENERATED]
├── trade_data.csv                           [GENERATED]
└── LICENSE                                  [EXISTING] MIT
```

## Third-Party Dependencies
- **FinRL** (base fork) — MIT
- **Stable-Baselines3**, **Gymnasium** — MIT — PPO training for all three agents
- **scikit-learn** — BSD-3-Clause — calibration utilities
- **scipy**, **cvxpy** — optimization utilities where needed
- **PyPortfolioOpt** (if retained, e.g. as a baseline/reference) — MIT
- **stockstats** (optional) — BSD-3-Clause — feature engineering acceleration
- **pandas**, **numpy**, **yfinance** — installed via `requirements.txt`

Configuration is driven by `configs/*.yaml` files — see the `configs/` section above for the intended schema.

---

**Related documents:** [FINRL_MAPPING.md](../architecture/FINRL_MAPPING.md) · [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) · [INTERFACE_CONTRACTS.md](../architecture/INTERFACE_CONTRACTS.md) · [CODING_STANDARDS.md](./CODING_STANDARDS.md)
