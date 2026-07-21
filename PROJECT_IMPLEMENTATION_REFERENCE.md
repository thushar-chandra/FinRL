# CA-MARL Project Implementation Reference

> **Confidence-Aware Multi-Agent Reinforcement Learning for Portfolio Decision Support**
>
> Generated from the actual implementation. Architecture is frozen. No speculation.
> Implementation wins where documentation disagrees.

---

## 1 Executive Summary

**What the project is:** CA-MARL is a multi-agent reinforcement learning system for portfolio allocation that uses three specialised RL agents (Market Analysis, Risk Assessment, Portfolio Allocation), each trained via PPO, whose heterogeneous recommendations are fused using calibrated confidence estimates. Confidence is estimated from historical accuracy, reward stability, and prediction consistency; calibrated via Platt or temperature scaling; and used as weights in a deterministic fusion formula.

**Current implementation status:** Complete and frozen (v2.1-phase4-planning). All core modules, experiment pipeline, walk-forward validation, baselines, ablations, publication plotting, and statistical analysis are implemented.

**Current development phase:** Phase 4 — manuscript planning and scientific analysis. The repository tag is `v2.1-phase4-planning`. Phase 3 (experimentation) is complete. The implementation freeze was declared at `v1.0-implementation-freeze`; subsequent tags (`v1.1-calibration-fixed`, `v2.0-phase3-complete`, `v2.1-phase4-planning`) represent post-freeze experiment-layer and analysis-layer additions that do not alter the frozen architecture.

**Research contribution:** Confidence-aware decision fusion (deterministic, PPO-independent, ADR-020) — a method for combining heterogeneous agent outputs (directional signals, risk scores, allocation weights) into a single portfolio allocation weighted by calibrated confidence scores.

**Repository status:** Frozen. No further implementation changes permitted without a new ADR and architecture-review session.

---

## 2 High-Level Architecture

The system is organised into nine major subsystems:

### 2.1 Data Pipeline (`finrl/agents/ca_marl/data_adapter.py`)

Downloads OHLCV market data from Yahoo Finance via `yfinance`, computes technical indicators through FinRL's `FeatureEngineer`, and pivots the result into three aligned DataFrames: features (T x (n_assets * n_indicators)), forward_returns (T x n_assets), and realized_prices (T x n_assets). Uses a direct `yf.download()` call instead of FinRL's `YahooDownloader` due to a yfinance API compatibility issue (the `proxy` parameter was removed in yfinance >= 1.5).

### 2.2 Feature Engineering

Uses FinRL's existing `FeatureEngineer` from `finrl.meta.preprocessor.preprocessors` with a configurable list of technical indicators (default: the `INDICATORS` list from `finrl.config` — includes MACD, RSI, Bollinger Bands, SMA, etc.). The adapter also performs regime-column detection via keyword matching (`bull`, `bear`, `regime`, `market_state`, `marketstate`) for prediction consistency.

### 2.3 RL Agents (`finrl/agents/ca_marl/`)

Three specialised PPO agents, each with its own Gymnasium environment, action space, and reward function:

- **MarketAnalysisAgent** (`market_agent.py`): Produces per-asset BUY/SELL/HOLD recommendations. Categorical action space (MultiDiscrete[3]^n_assets). Reward = directional-accuracy-weighted return.
- **RiskAssessmentAgent** (`risk_agent.py`): Produces per-asset expected_volatility and risk_score. Continuous action space (Box[0,1]^(2*n_assets)). Reward = negative MAE between predicted and realised volatility/risk.
- **PortfolioAllocationAgent** (`allocation_agent.py`): Produces per-asset raw allocation weights. Continuous action space (Box[-1,1]^n_assets). Reward = portfolio return minus L2 concentration penalty.

All agents share the same training pattern: wrap historical data in a Gymnasium environment, create a `DummyVecEnv`, train with `stable_baselines3.PPO`, and capture per-step rewards via `_RewardCaptureCallback` for stability tracking.

### 2.4 Confidence Engine (`finrl/agents/ca_marl/confidence_engine.py`)

Combines three signals into a raw confidence scalar per agent:
1. **Historical accuracy** (`hist_accuracy`): mean of past outcome labels (falls back to 0.5 on cold-start).
2. **Reward stability** (`rs`): `1 / variance(recent rewards)`, normalised to [0,1] via `rs/(1+rs)`.
3. **Prediction consistency** (`pc`): agreement fraction across k nearby regime-bucket states.

These are combined via a weighted average using configurable weights (default: 0.4 historical + 0.3 reward stability + 0.3 prediction consistency).

### 2.5 Confidence Calibration (`confidence_engine.py`, same module)

Fits either Platt scaling (`sklearn.linear_models.LogisticRegression`) or temperature scaling (`scipy.optimize.minimize_scalar`) on eligible (confidence, label) pairs collected during walk-forward validation. Requires >= 5 pairs per agent; falls back to identity mapping otherwise. Calibration is fold-aware — pairs are gated through `OutcomeLabelGenerator.is_eligible_for_fold()` to prevent information leakage.

### 2.6 Confidence-Aware Fusion (`finrl/agents/ca_marl/confidence_fusion.py`)

The primary research contribution. Deterministic module that transforms each agent's heterogeneous recommendation into a common `AssetWeightProposal` per-asset weight vector (non-negative, sums to 1.0) using per-agent transform functions:

- **Market -> proposal**: BUY->1, HOLD->0, SELL->0, then sum-to-1 normalise.
- **Risk -> proposal**: `1 / (epsilon + risk_score)`, then sum-to-1 normalise (lower risk -> higher weight).
- **Allocation -> proposal**: ReLU-clip negatives, then sum-to-1 normalise.

The fused allocation is the confidence-weighted average of the three proposals. Falls back to equal-weight average when confidence sum is near zero.

### 2.7 Risk Management (`finrl/agents/ca_marl/risk_management.py`)

Authoritative constraint enforcement: long-only (clip negatives to 0), sum-to-1 normalise, capped-simplex projection (iterative algorithm that caps weights at `max_exposure_per_asset` and redistributes excess). Passes `reasoning` and `confidence_summary` through unchanged from `FusedDecision`.

### 2.8 Evaluation (`finrl/agents/ca_marl/evaluation.py`)

Computes five financial metrics (Sharpe ratio, Sortino ratio, maximum drawdown, volatility, cumulative return) from portfolio return series. Computes per-agent calibration metrics (ECE and Brier score) via the shared `OutcomeLabelGenerator`. Supports placeholder ablation runner and baseline comparison container.

### 2.9 Experiment Pipeline (`experiments/`)

Contains walk-forward validation (`_walk_forward.py`), experiment pipeline with timestamp patching (`_pipeline.py`), evaluation orchestrator (`_evaluate.py`), baselines (`_baselines.py`), ablations (`_ablations.py`), data caching (`_data_cache.py`), plotting (`_plotting.py`, `_generate_publication_plots.py`, `_publication_outputs.py`), statistical analysis (`_final_stats.py`), research report generation (`_research_report.py`), and runner scripts (`run_ca_marl.py`, `run_all.py`, `run_campaign.py`, `run_baselines.py`, `run_ablations.py`, `run_plots.py`).

---

## 3 End-to-End Execution Pipeline

The following describes the exact execution sequence, from raw market data to final recommendation to evaluation.

### Phase 0: Data Preparation

1. `data_adapter.download_and_prepare(ticker_list, start_date, end_date)` is called.
2. OHLCV data is downloaded via `_download_yahoo()` -> single `yf.download()` call per ticker, auto-adjusted, concatenated.
3. `FeatureEngineer.preprocess_data(raw)` adds technical indicators (MACD, RSI, SMA, Bollinger Bands, etc.).
4. Data is sorted by date then ticker. A pivot produces:
   - `features`: wide-format DataFrame with columns `{ticker}_{indicator}`, indexed by date.
   - `forward_returns`: per-asset one-step percentage returns, indexed by date.
   - `realized_prices`: close prices (DatetimeIndex x ticker), indexed by date.
5. All three DataFrames are aligned to a common date index via intersection.

### Phase 1: Training (per fold)

6. `build_agents()` creates three agent instances with identical PPO config and per-agent hyperparameters.
7. For each agent:
   - A Gymnasium environment wraps the training feature array and forward returns.
   - `stable_baselines3.PPO("MlpPolicy", env)` is created with the configured PPO hyperparameters.
   - `model.learn(total_timesteps=...)` trains the policy. A `_RewardCaptureCallback` captures per-step rewards for stability tracking.
   - The trained model is stored in memory (no disk save during walk-forward).

### Phase 2: Inference

8. Each agent's `predict(features)` is called with the test-window features. Only the last row is used as the current observation.
9. `predict()` returns an `AgentOutput` with:
   - `agent_name`: e.g. `"market_agent"`
   - `recommendation`: agent-specific payload
   - `raw_confidence`: 0.0 (placeholder)
   - `reasoning`: human-readable summary string
   - `timestamp`: `pd.Timestamp.now()` (patched in experiment pipeline)
   - `metadata["reward_stability"]`: computed from training reward history
10. `prediction_consistency(features, k)` is called for each agent:
    - Extracts the current regime bucket from the features.
    - Finds up to `k` historical rows in the same regime bucket.
    - Runs `model.predict(obs, deterministic=False)` on each neighbour.
    - For market agent: computes modal agreement fraction.
    - For risk/allocation agents: computes 1 - mean(coefficient_of_variation).

### Phase 3: Confidence Estimation & Calibration

11. `ConfidenceEngine.estimate_raw_confidence(agent_outputs, pcs)`:
    - For each agent: looks up `_label_history` (size 0 on first fold due to cold start).
    - Computes `hist_accuracy = mean(history)` or 0.5 fallback.
    - Reads `reward_stability` from metadata, normalises via `rs/(1+rs)`.
    - Reads prediction consistency from `pcs` dict.
    - Computes weighted average.
12. `ConfidenceEngine.fit_calibration(calib_pairs)`:
    - Receives accumulated calibration pairs from earlier folds.
    - Groups by agent name. For agents with >= 5 pairs, fits the configured method.
    - Agents with < 5 pairs retain the identity mapping.
13. `ConfidenceEngine.calibrate(raw_confs)`:
    - For each agent: applies the fitted model (Platt or temperature) to raw confidence.
    - If model is None (identity), calibrated = raw.
    - Computes ECE and Brier score on the fit data.
    - Returns `CalibratedConfidence` per agent.

### Phase 4: Fusion

14. `ConfidenceAwareFusion.fuse(agent_outputs, calibrated_confidences, universe)`:
    - Validates exactly 3 agents are present.
    - For each agent, converts heterogeneous recommendation to `AssetWeightProposal`.
    - Computes confidence-weighted average.
    - Falls back to equal-weight average if confidence sum approx 0.
    - Composes reasoning string sorted by descending confidence.

### Phase 5: Risk Management

15. `RiskManagementLayer.apply(fused_decision)`:
    - Clips negative weights to 0 (long-only).
    - Normalises to sum to 1.0.
    - Projects onto capped simplex.
    - Passes `reasoning` and `confidence_summary` through unchanged.

### Phase 6: Evaluation

16. `EvaluationEngine.evaluate_with_assets([final_rec], realized_prices)` computes portfolio returns.
17. `EvaluationEngine.evaluate_calibration(calibrated, agent_outputs, realized_prices)` computes per-agent ECE and Brier score.
18. Results are assembled into an `EvaluationReport`.

### Walk-Forward Orchestration

Steps 1-18 are orchestrated across N folds by `WalkForwardRunner.run()`. Fold schedules are generated by `build_fold_schedules()`. Per fold: train, validate, test, compute baselines, accumulate calibration pairs.

---

## 4 Repository Structure

```
FinRL/
├── configs/          # Empty directories (placeholder YAML configs)
├── docker/           # Container build scripts
├── docs/             # Architecture, planning, research, implementation docs
├── examples/         # FinRL example notebooks and scripts
├── experiments/      # Main experiment pipeline
│   ├── __init__.py
│   ├── _config.py           # Default config constants, fold schedule generator
│   ├── _pipeline.py         # Experiment-layer pipeline with timestamp patching
│   ├── _walk_forward.py     # Walk-forward validation orchestrator
│   ├── _evaluate.py         # Single experiment runner with aggregation
│   ├── _baselines.py        # Baseline strategies (1/N, buy-and-hold, MVO)
│   ├── _ablations.py        # Ablation studies
│   ├── _data_cache.py       # Versioned dataset caching
│   ├── _plotting.py         # Plotting suite
│   ├── _generate_publication_plots.py
│   ├── _publication_outputs.py   # PDF figures + LaTeX tables
│   ├── _final_stats.py      # Statistical analysis
│   ├── _research_report.py  # Comprehensive report
│   ├── _utils.py            # Seeding, serialization, paths
│   ├── _dynamic_verify.py   # Monkey-patch instrumentation
│   ├── _verify_all.py       # Multi-verification runner
│   ├── _verify_env.py       # Environment verification
│   ├── _audit_check.py      # Audit verification
│   ├── _consistency_audit.py
│   ├── _phase3_checks.py
│   ├── _fix_fig02.py
│   ├── run_ca_marl.py       # Entry: single experiment
│   ├── run_all.py            # Entry: multi-seed suite
│   ├── run_campaign.py       # Entry: publication campaign
│   ├── run_baselines.py      # Entry: standalone baselines
│   ├── run_ablations.py      # Entry: standalone ablations
│   ├── run_plots.py          # Entry: plot generation
│   ├── dataset/              # Frozen dataset cache
│   ├── results/              # JSON experiment results
│   ├── plots/                # Generated plots and tables
│   │   └── publication/      # Publication-quality outputs
│   └── reports/              # Generated reports
├── finrl/                    # Core FinRL framework
│   ├── agents/
│   │   └── ca_marl/          # CA-MARL implementation
│   │       ├── __init__.py
│   │       ├── contracts.py
│   │       ├── config_schema.py
│   │       ├── market_agent.py
│   │       ├── risk_agent.py
│   │       ├── allocation_agent.py
│   │       ├── confidence_engine.py
│   │       ├── confidence_fusion.py
│   │       ├── risk_management.py
│   │       ├── evaluation.py
│   │       ├── pipeline.py
│   │       ├── data_adapter.py
│   │       └── tests/
│   │   ├── elegantrl/
│   │   ├── portfolio_optimization/
│   │   ├── rllib/
│   │   └── stablebaselines3/
│   ├── applications/
│   ├── meta/                 # Data processors, environments, preprocessors
│   └── ...                   # Config, main, plot, test, trade, train
├── tests/integration/        # Integration tests
├── unit_tests/               # FinRL unit tests
├── notebooks/
├── results/                  # TB event logs
├── trained_models/
├── AGENTS.md
├── IMPLEMENTATION_FREEZE.md
├── PHASE_3_COMPLETION_REPORT.md
├── PHASE_3_FREEZE_REPORT.md
├── PAPER_BLUEPRINT.md
├── MANUSCRIPT_PLAN.md
├── pyproject.toml
├── requirements.txt
├── setup.py / setup.cfg
└── README.md
```

---

## 5 Module Inventory

### 5.1 `finrl/agents/ca_marl/contracts.py`

- **Purpose:** Shared data structures and exceptions.
- **Dependencies:** stdlib only.
- **Classes:** `AgentOutput`, `CalibratedConfidence`, `FusedDecision`, `FinalRecommendation`, `FinancialMetrics`, `CalibrationMetrics`, `EvaluationReport`.
- **Exceptions:** `InsufficientHistoryError`, `LabelNotYetResolvableError`, `EvaluationDataMismatchError`.
- **Type alias:** `AssetWeightProposal = dict[str, float]`.

### 5.2 `finrl/agents/ca_marl/config_schema.py`

- **Purpose:** Strongly typed configuration dataclasses.
- **Classes:** `UniverseConfig`, `FeatureEngineeringConfig`, `AgentHyperparameters`, `PPOConfig`, `ConfidenceConfig`, `WalkForwardConfig`, `RiskManagementConfig`, `CAMARLConfig`.

### 5.3 `finrl/agents/ca_marl/market_agent.py`

- **Purpose:** Directional signals (BUY/SELL/HOLD).
- **Action space:** `MultiDiscrete([3]*n)`.
- **Reward:** `mean((action-1) * forward_return)`.
- **Prediction consistency:** modal agreement across k neighbours.

### 5.4 `finrl/agents/ca_marl/risk_agent.py`

- **Purpose:** Per-asset volatility and risk score.
- **Action space:** `Box(0,1, 2n)`.
- **Reward:** `-mean(|vol_pred - vol_real| + |risk_pred - risk_real|) / 2`.
- **Prediction consistency:** 1 - CV across k neighbours.

### 5.5 `finrl/agents/ca_marl/allocation_agent.py`

- **Purpose:** Raw allocation weights.
- **Action space:** `Box(-1,1, n)`.
- **Reward:** `dot(w, ret) - 0.01 * mean(w^2)`.
- **Prediction consistency:** 1 - CV across k neighbours.

### 5.6 `finrl/agents/ca_marl/confidence_engine.py`

- **Purpose:** Label generation, confidence estimation, calibration.
- **Classes:** `OutcomeLabelGenerator`, `ConfidenceEngine`.
- **Calibration methods:** Platt scaling (sklearn) and temperature scaling (scipy).
- **Diagnostics:** ECE (10-bin) and Brier score.

### 5.7 `finrl/agents/ca_marl/confidence_fusion.py`

- **Purpose:** Confidence-weighted fusion.
- **Class:** `ConfidenceAwareFusion`.
- **Transforms:** Market->proposal, Risk->proposal, Allocation->proposal.
- **Fusion:** `sum(w_i * proposal_i) / sum(w_i)`.

### 5.8 `finrl/agents/ca_marl/risk_management.py`

- **Purpose:** Portfolio constraint enforcement.
- **Class:** `RiskManagementLayer`.
- **Algorithm:** long-only clip, sum-to-1 normalise, capped-simplex projection (iterative).

### 5.9 `finrl/agents/ca_marl/evaluation.py`

- **Purpose:** Financial and calibration evaluation.
- **Class:** `EvaluationEngine`.
- **Metrics:** Sharpe, Sortino, max drawdown, volatility, cumulative return, ECE, Brier.

### 5.10 `finrl/agents/ca_marl/pipeline.py`

- **Purpose:** Pipeline orchestration.
- **Functions:** `build_agents()`, `run_inference()`, `run_pipeline()`.

### 5.11 `finrl/agents/ca_marl/data_adapter.py`

- **Purpose:** Data download + feature engineering.
- **Functions:** `_download_yahoo()`, `download_and_prepare()`.

---

## 6 Reinforcement Learning Architecture

### 6.1 Algorithm

All three agents use PPO (`stable_baselines3.PPO` with `MlpPolicy`). Shared PPO config: lr=3e-4, n_steps=128, batch_size=32, gamma=0.99, gae_lambda=0.95, clip_range=0.2, ent_coef=0.01, vf_coef=0.5, max_grad_norm=0.5.

### 6.2 Observation Space

All agents: `Box(-inf, inf, (n_features,), float32)` — the engineered feature vector (including technical indicators and regime features).

### 6.3 Agent Summary

| Agent | Action Space | Output | Reward Function |
|-------|-------------|--------|-----------------|
| Market | `MultiDiscrete([3]*n)` | BUY/SELL/HOLD per asset | `mean((a-1) * fwd_ret)` |
| Risk | `Box(0,1, 2n)` | vol + risk per asset | `-MAE(pred, realised)` |
| Allocation | `Box(-1,1, n)` | raw weights per asset | `dot(w, ret) - 0.01*mean(w^2)` |

### 6.4 Training

Each agent trains independently on the same feature data with its own reward function. Environments step sequentially through the historical data. No inter-agent communication during training (ADR-025).

---

## 7 Confidence System

### 7.1 Outcome Labels

| Agent | Label | Calculation |
|-------|-------|-------------|
| market_agent | [0,1] fraction | Fraction of assets where direction matches forward return sign over horizon |
| risk_agent | 0 or 1 | 1 if realised vol within +/-0.2 of predicted vol |
| allocation_agent | 0 or 1 | 1 if proposed weights beat equal-weight over horizon |

### 7.2 Raw Confidence

`raw = (0.4 * hist_acc + 0.3 * rs_norm + 0.3 * pc) / 1.0`, where:
- `hist_acc = mean(label_history)` or 0.5 on cold start
- `rs_norm = rs / (1+rs)`, with `rs = 1/var(recent_rewards)`
- `pc` = prediction consistency score

### 7.3 Calibration

- **Methods:** Platt scaling (LogisticRegression) or temperature scaling (scipy minimize_scalar)
- **Requirement:** >= 5 (confidence, label) pairs per agent
- **Fallback:** identity mapping (calibrated = raw)
- **Gating:** `is_eligible_for_fold()` checks `timestamp + horizon <= next_train_end`

### 7.4 Fusion

- **Formula:** `final[w] = sum(proposal_i[w] * conf_i) / sum(conf_i)`
- **Fallback:** equal-weight average if `sum(conf) < 1e-12`
- **Properties:** non-negative, sums to 1.0

---

## 8 Data Flow

```
data_adapter.download_and_prepare()
  -> features (DataFrame), forward_returns (DataFrame), realized_prices (DataFrame), universe (list)

build_agents(features, forward_returns, universe, configs)
  -> {market_agent, risk_agent, allocation_agent}  (trained PPO models)

agent.predict(features)
  -> AgentOutput {agent_name, recommendation, raw_confidence=0.0, reasoning, timestamp, metadata}

agent.prediction_consistency(features, k)
  -> float in [0,1]

ConfidenceEngine.estimate_raw_confidence(outputs, pcs)
  -> {agent_name: raw_confidence}

ConfidenceEngine.fit_calibration(pairs)
  -> (stores models internally)

ConfidenceEngine.calibrate(raw_confs)
  -> {agent_name: CalibratedConfidence {calibrated_confidence, diagnostics}}

ConfidenceAwareFusion.fuse(outputs, calibrated, universe)
  -> FusedDecision {final_allocation, reasoning, confidence_summary, fusion_metadata}

RiskManagementLayer.apply(fused)
  -> FinalRecommendation {allocation, reasoning, confidence_summary, timestamp}

EvaluationEngine.evaluate_with_assets([final_rec], prices)
  -> FinancialMetrics {sharpe_ratio, sortino_ratio, max_drawdown, volatility, cumulative_return}
```

---

## 9 Configuration

All configuration is via Python dataclasses defined in `config_schema.py` with defaults in `experiments/_config.py`.

| Group | Key Parameters |
|-------|---------------|
| Universe | 19 Nifty 50 tickers, as-of 2024-01-01 |
| Walk-forward | 4 folds, train=504d, val=63d, test=126d, stride=126 |
| PPO | lr=3e-4, n_steps=128, batch_size=32, gamma=0.99 |
| Confidence | platt, k=5, hist_weight=0.4, rs_weight=0.3, pc_weight=0.3 |
| Risk | max_exposure=0.4 |
| Agent | label_horizon=5d, reward_stability_window=20 |
| Experiment | 5 seeds (42-46), 5000 timesteps per agent |

---

## 10 Evaluation Framework

### 10.1 Metrics

- **Financial:** Sharpe ratio (annualised), Sortino ratio (annualised), max drawdown, volatility (annualised), cumulative return.
- **Calibration:** ECE (10-bin), Brier score.

### 10.2 Baselines

- Equal Weight (1/N, daily rebalanced)
- Buy and Hold (equal-weight at start, held)
- Static MVO (Markowitz, no rebalancing)

### 10.3 Walk-Forward

- 4 non-overlapping folds, stride = test_window = 126 days
- Per fold: train, predict on test, evaluate, accumulate calibration pairs from validation
- Retrain from scratch each fold

### 10.4 Ablations

- Equal-weight fusion (override confidences to equal)
- No calibration (use raw confidences)
- Shuffled confidence (random reassignment)
- Drop one agent (set confidence to 0)

---

## 11 Current Implementation Status

| Component | Status |
|-----------|--------|
| Shared contracts | Implemented, tested, frozen |
| Config schema | Implemented, tested, frozen |
| Market Analysis Agent | Implemented, tested, frozen |
| Risk Assessment Agent | Implemented, tested, frozen |
| Portfolio Allocation Agent | Implemented, tested, frozen |
| Confidence Engine | Implemented, tested, frozen |
| Outcome Label Generator | Implemented, tested, frozen |
| Confidence-Aware Fusion | Implemented, tested, frozen |
| Risk Management Layer | Implemented, tested, frozen |
| Evaluation Engine | Implemented, tested, frozen |
| Pipeline orchestrator | Implemented, tested, frozen |
| Data adapter | Implemented, tested, frozen |
| Integration tests | Implemented, tested |
| Walk-forward validation | Implemented, tested |
| Experiment pipeline | Implemented, tested |
| Baseline strategies | Implemented, tested |
| Ablation studies | Implemented, tested |
| Frozen dataset cache | Implemented, tested |
| Publication plots | Implemented, tested |
| Statistical analysis | Implemented, tested |
| YAML config loading | Not implemented (placeholders) |
| Transaction cost modelling | Not implemented (deferred) |
| Hyperparameter tuning | Not implemented (deferred) |

---

## 12 Known Limitations

1. **Calibration is non-functional at current configuration.** The walk-forward schedule causes every fold to receive 0 calibration pairs because the eligibility check always fails: test window end (cursor+693) exceeds next fold training window end (cursor+630). All folds use identity mapping.

2. **`_collect_calibration_pairs()` is defined but never called.** The method exists at `_walk_forward.py:258` but `run()` never invokes it.

3. **`record_outcome()` is never called in practice.** 0 calls across all 4 folds (confirmed by dynamic verification).

4. **`raw_confidence = 0.0` placeholder in agents.** All three agents set this placeholder; the actual raw confidence is recomputed by the Confidence Engine.

5. **`_VOL_NORMALIZATION_FACTOR` duplicated.** Defined independently in `risk_agent.py:62` and `confidence_engine.py:31`.

6. **`market_agent` does not set `metadata["tie_break_reason"]`.** Minor contract deviation.

7. **yfinance compatibility workaround.** Uses direct `yf.download()` instead of FinRL's `YahooDownloader`.

8. **Ablation studies not integrated into evaluation engine.** `EvaluationEngine.run_ablation()` is a placeholder.

9. **`EvaluationEngine.compare_baselines()` is a pass-through container.**

10. **Regime features are not explicitly engineered.** Regime-column detection uses keyword heuristics on column names; no regime classifier is implemented.

---

## 13 Reproducibility

- **Git tag:** `v2.1-phase4-planning`
- **Git commit:** `f223fde` (HEAD)
- **Implementation freeze date:** 2026-07-19
- **Python version:** 3.14.5 (per manifest)
- **Dataset:** v1.0.0, 19 assets, 1111 timesteps, Yahoo Finance, pickled with SHA-256 checksums
- **Random seeds:** 42, 43, 44, 45, 46 (set via `set_all_seeds()`)
- **Fusion is deterministic.** Risk management is deterministic. Baselines are deterministic.
- **PPO training is non-deterministic** across hardware/platforms.
- **Reproducibility manifest:** `experiments/reproducibility_manifest.json`

---

## 14 Summary

CA-MARL is a complete, frozen multi-agent RL system for portfolio allocation. Three PPO agents (market direction, risk assessment, allocation weights) are trained independently and their heterogeneous outputs fused via calibrated confidence weights. The deterministic fusion formula transforms each agent's recommendation into a common per-asset weight representation and computes a confidence-weighted average. A risk management layer enforces long-only, sum-to-one, and exposure-cap constraints. The system is evaluated via 4-fold walk-forward validation with three baselines and four ablation studies. A frozen dataset, reproducibility manifest, and publication-quality plotting pipeline support the research contribution.
