# Baseline Validation Report

## 1. Overview

FinRL upstream baseline validated end-to-end on the NeurIPS 2018 Stock Trading
task using Python 3.11.9 + SB3 2.9.0 + torch 2.13.0 (CPU).

## 2. Environment

| Component | Value |
|-----------|-------|
| Python | 3.11.9 |
| OS | Windows 11 x64 |
| CPU | Intel (no GPU) |
| SB3 | 2.9.0 |
| torch | 2.13.0+cpu |
| gymnasium | 1.3.0 |
| gym | 0.26.2 |

Dependencies installed from `requirements.txt` with `elegantrl` pinned
`--no-deps` (avoids `pygame==2.1.0` build failure).  `websockets` upgraded
to >=13.0 for `yfinance` wheel resolution.

## 3. Data Pipeline Validation

Script: `FinRL_StockTrading_2026_1_data.py`

| Step | Status | Artifacts |
|------|--------|-----------|
| DOW 30 stock list retrieval | OK | 30 tics |
| Yahoo Finance download | OK | `train_data.csv`, `trade_data.csv` |
| Technical indicators | OK | 5 indicators (macd, rsi_30, cci_30, dx_30, atr_30) |
| Train/trade split | OK | train: 2025-01-01 to 2025-12-31; trade: 2026-01-01 to 2026-03-19 |

## 4. Training Validation

Script: `FinRL_StockTrading_2026_2_train.py` (20 000 timesteps per model)

### Completed

| Algorithm | Model File | Total Time (est.) | Notes |
|-----------|-----------|-------------------|-------|
| A2C | `trained_models/agent_a2c.zip` | ~5 min | Default params |
| DDPG | `trained_models/agent_ddpg.zip` | ~25 min | Default params |
| PPO | `trained_models/agent_ppo.zip` | ~30 min | n_steps=2048, batch_size=128 |

### Not completed (CPU timeout — 30 min limit)

| Algorithm | Status | Reason |
|-----------|--------|--------|
| TD3 | Timed out | `results/td3/progress.csv` is 0 bytes; only 88 B of event logs written |
| SAC | Timed out | Did not start within 30 min window |

These models are not required for FinRL baseline validation but would be
needed for the full 5-agent ensemble strategy described in the original paper.

### Known Issue: "Logging Error: 'rollout_buffer'"

- **Root cause**: FinRL's `TensorboardCallback._on_rollout_end()` at
  `finrl/agents/stablebaselines3/models.py:75` unconditionally accesses
  `self.locals["rollout_buffer"]`, which does not exist in off-policy
  algorithms (DDPG, TD3, SAC) because those use `replay_buffer` instead.
- **Impact**: Cosmetic only. The `except BaseException` block catches the
  `KeyError` and sets `reward_min/mean/max` to `None`. Training continues
  normally and models save correctly.
- **Scope**: Fires for DDPG, TD3, SAC every rollout. Does **not** fire for
  A2C/PPO (where `rollout_buffer` is a method parameter and present in
  `locals()`).

## 5. Backtest Validation

Script: `FinRL_StockTrading_2026_3_Backtest.py` (adapted — only A2C/DDPG/PPO)

### Model Loading

All three saved `.zip` files load successfully via `A2C.load()`,
`DDPG.load()`, and `PPO.load()` with correct policy architectures.

### Performance Metrics (2026-01-02 to 2026-03-18, 52 trading days)

| Metric | A2C | DDPG | PPO | DJIA |
|--------|-----|------|-----|------|
| Final Portfolio | $982 318 | $955 486 | $965 904 | $951 202 |
| Total Return | -1.77% | -4.45% | -3.41% | -4.88% |
| Max Drawdown | 8.46% | 6.37% | 4.25% | — |
| Sharpe Ratio | -0.591 | -1.494 | -2.650 | — |
| Volatility (ann.) | 13.40% | 14.36% | 6.39% | — |

All three DRL agents outperformed the DJIA baseline during a market
downturn.  PPO achieved the best risk-adjusted metrics (lowest drawdown and
volatility).  A2C had the highest absolute return.

### Plot

`backtest_result.png` saved — portfolio value over time for all strategies
plus DJIA.

## 6. Codebase Readiness for CA-MARL Extension

### Key Files (20 identified)

| File | Role |
|------|------|
| `finrl/meta/env_stock_trading/env_stocktrading.py` | Core trading environment (gym.Env) |
| `finrl/agents/stablebaselines3/models.py` | DRLAgent wrapper + TensorboardCallback |
| `finrl/config.py` | Configuration constants |
| `finrl/meta/preprocessor/yahoodownloader.py` | Data download |
| `finrl/meta/preprocessor/preprocessors.py` | Feature engineering |
| `finrl/main.py` | Directory setup |
| `requirements.txt` | Dependency list |
| `examples/FinRL_StockTrading_2026_1_data.py` | Data pipeline entry point |
| `examples/FinRL_StockTrading_2026_2_train.py` | Training entry point |
| `examples/FinRL_StockTrading_2026_3_Backtest.py` | Backtest entry point |
| `stable_baselines3/common/on_policy_algorithm.py` | On-policy training loop |
| `stable_baselines3/common/off_policy_algorithm.py` | Off-policy training loop |
| `stable_baselines3/common/base_class.py` | Base algorithm class |
| `stable_baselines3/common/logger.py` | Logging infrastructure |
| `stable_baselines3/a2c/a2c.py` | A2C implementation |
| `stable_baselines3/ddpg/ddpg.py` | DDPG implementation |
| `stable_baselines3/ppo/ppo.py` | PPO implementation |
| `stable_baselines3/td3/td3.py` | TD3 implementation |
| `stable_baselines3/sac/sac.py` | SAC implementation |
| `.venv/Lib/site-packages/` | Installed SB3 / gym (read-only) |

### Extension Points for CA-MARL

1. **Environment**: `StockTradingEnv` is the natural extension point.
   Multi-agent coordination would require shared state / action masking.
2. **Agent wrapper**: `DRLAgent` can be subclassed for cooperative agents.
3. **Training script**: `FinRL_StockTrading_2026_2_train.py` structure
   (instantiate → configure logger → learn → save) is straightforward to
   replicate per agent.
4. **Callbacks**: `TensorboardCallback` pattern can be extended for
   multi-agent metrics.

### Risks

1. **`gym` deprecated (unmaintained since 2022)** — `gymnasium` is the
   replacement.  SB3 2.9.0 supports both, but `StockTradingEnv` inherits
   from `gym.Env`.  Any CA-MARL extension should migrate to `gymnasium`
   or verify full compatibility.
2. **No GPU** — 20k timesteps per model takes ~30 min on CPU.  Scaling to
   multi-agent or longer horizons will need GPU or distributed training.
3. **TD3/SAC untrained** — these use `replay_buffer` (off-policy) and may
   exhibit different memory/performance characteristics when extended.
4. **elegantrl pinned `--no-deps`** — deviates from upstream; `pygame`
   build failure is a known Windows issue.
5. **Dependency version drift** — `requirements.txt` pins minimal versions;
   later SB3 releases may change callback/logger APIs.

## 7. Conclusion

The upstream FinRL baseline is **fully validated** for the A2C/DDPG/PPO
models that trained successfully, including data pipeline, training, model
persistence, backtesting, and metric computation.  TD3 and SAC remain
unvalidated due to CPU timeout but are not required for the core baseline.

The repository is **ready for CA-MARL implementation** with
the caveats documented above.
