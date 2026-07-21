# DATASET_AUDIT.md

## 1. Data Source

**Source:** Yahoo Finance, accessed via the `yfinance` Python library.

**How obtained:** The function `_download_yahoo()` in `finrl/agents/ca_marl/data_adapter.py:25-60` downloads OHLCV data by calling `yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)` for each ticker individually. This is a direct download, bypassing the FinRL `YahooDownloader` due to a `yfinance` API compatibility issue (the `proxy` parameter was removed in `yfinance >= 1.5`, documented at line 6 of `data_adapter.py`).

**Evidence:**
- File: `finrl/agents/ca_marl/data_adapter.py`, function `_download_yahoo()` (lines 25-60)
- File: `experiments/_data_cache.py`, function `freeze_dataset()` (lines 70-112) — calls `download_and_prepare()` which calls `_download_yahoo()`
- File: `experiments/dataset/metadata.json`, field `data_source`: `"Yahoo Finance (yfinance)"`

---

## 2. Asset Universe

**Tickers (19 assets, all trading on the National Stock Exchange of India via Yahoo Finance's `.NS` suffix):**

| # | Ticker | Company Name | Exchange |
|---|--------|-------------|----------|
| 1 | `ASIANPAINT.NS` | Asian Paints Ltd | NSE (India) |
| 2 | `AXISBANK.NS` | Axis Bank Ltd | NSE (India) |
| 3 | `BHARTIARTL.NS` | Bharti Airtel Ltd | NSE (India) |
| 4 | `HDFCBANK.NS` | HDFC Bank Ltd | NSE (India) |
| 5 | `HINDUNILVR.NS` | Hindustan Unilever Ltd | NSE (India) |
| 6 | `ICICIBANK.NS` | ICICI Bank Ltd | NSE (India) |
| 7 | `INFY.NS` | Infosys Ltd | NSE (India) |
| 8 | `ITC.NS` | ITC Ltd | NSE (India) |
| 9 | `KOTAKBANK.NS` | Kotak Mahindra Bank Ltd | NSE (India) |
| 10 | `LT.NS` | Larsen & Toubro Ltd | NSE (India) |
| 11 | `MARUTI.NS` | Maruti Suzuki India Ltd | NSE (India) |
| 12 | `NTPC.NS` | NTPC Ltd | NSE (India) |
| 13 | `POWERGRID.NS` | Power Grid Corporation of India Ltd | NSE (India) |
| 14 | `RELIANCE.NS` | Reliance Industries Ltd | NSE (India) |
| 15 | `SBIN.NS` | State Bank of India | NSE (India) |
| 16 | `SUNPHARMA.NS` | Sun Pharmaceutical Industries Ltd | NSE (India) |
| 17 | `TCS.NS` | Tata Consultancy Services Ltd | NSE (India) |
| 18 | `TITAN.NS` | Titan Company Ltd | NSE (India) |
| 19 | `WIPRO.NS` | Wipro Ltd | NSE (India) |

**Total assets:** 19

**Selection rationale:** These are Nifty 50 constituents as of January 1, 2024, chosen to represent the Indian large-cap equity universe. The universe is frozen as of that date to prevent hindsight bias (documented in `experiments/_config.py:27` as `UNIVERSE_AS_OF_DATE = date(2024, 1, 1)`).

**Evidence:**
- File: `experiments/_config.py`, list `DEFAULT_UNIVERSE` (lines 21-26)
- File: `experiments/dataset/universe.json` — identical list of 19 tickers
- File: `experiments/dataset/metadata.json`, field `ticker_universe`
- File: `experiments/reproducibility_manifest.json`, field `dataset_assets: 19`
- Frozen data: `realized_prices_v1.0.0.pkl` — 19 columns verified by Python inspection

---

## 3. Time Period

| Property | Config Value | Actual Frozen Data |
|----------|-------------|-------------------|
| Start date | `2020-01-01` | `2020-01-01` |
| End date | `2024-06-30` | `2024-06-27` |
| Trading days | — | 1,111 |
| Timesteps | — | 1,111 |

**Note:** The config specifies `DATA_END = "2024-06-30"` (`_config.py:35`), but Yahoo Finance returns only available trading days. The last trading day in the frozen dataset is 2024-06-27. All 1,111 rows are non-holiday trading days.

**Evidence:**
- File: `experiments/_config.py`, variables `DATA_START` (line 34), `DATA_END` (line 35)
- Frozen data: `realized_prices_v1.0.0.pkl` — DatetimeIndex verified by Python inspection: first entry `2020-01-01`, last entry `2024-06-27`, length 1,111
- File: `experiments/reproducibility_manifest.json`, field `dataset_timesteps: 1111`

---

## 4. Sampling Frequency

**Frequency:** Daily.

**Determination:**
- The data is downloaded via `yf.download(..., auto_adjust=True)` which returns daily OHLCV data by default.
- The DatetimeIndex of `realized_prices_v1.0.0.pkl` has 1,111 entries spanning 1,639 calendar days (2020-01-01 to 2024-06-27), consistent with daily trading data (excluding weekends and holidays).
- The `FeatureEngineer` documentation in `finrl/meta/preprocessor/preprocessors.py` states: "only apply to daily level data, need to fix for minute level" (line in `clean_data` method), confirming daily frequency is the intended and implemented granularity.

**Evidence:**
- Frozen data: `realized_prices_v1.0.0.pkl` — DatetimeIndex with daily spacing, verified by Python inspection
- File: `finrl/meta/preprocessor/preprocessors.py` — `clean_data()` comment confirming daily-level data

---

## 5. Raw Dataset Schema

The raw data downloaded from Yahoo Finance has this schema (defined in `_download_yahoo()` at `data_adapter.py:45`):

| Column | Type | Description |
|--------|------|-------------|
| `date` | `datetime64` | Trading date |
| `open` | `float64` | Opening price (adjusted for splits/dividends) |
| `high` | `float64` | High price (adjusted) |
| `low` | `float64` | Low price (adjusted) |
| `close` | `float64` | Close price (adjusted) |
| `volume` | `int64` | Trading volume |
| `tic` | `str` | Ticker symbol (e.g., `RELIANCE.NS`) |

The `auto_adjust=True` parameter means OHLCV prices are adjusted for splits and dividends.

**Evidence:**
- File: `finrl/agents/ca_marl/data_adapter.py`, function `_download_yahoo()`, line 45: `df[["Date", "Open", "High", "Low", "Close", "Volume", "tic"]]`, columns renamed at lines 49-58

---

## 6. Feature Engineering

**Technical indicators** (defined in `finrl/config.py:21-30`):

| Indicator | Description | Source |
|-----------|-------------|--------|
| `macd` | Moving Average Convergence Divergence | stockstats |
| `boll_ub` | Bollinger Band Upper | stockstats |
| `boll_lb` | Bollinger Band Lower | stockstats |
| `rsi_30` | Relative Strength Index (30-day) | stockstats |
| `cci_30` | Commodity Channel Index (30-day) | stockstats |
| `dx_30` | Directional Movement Index (30-day) | stockstats |
| `close_30_sma` | 30-day Simple Moving Average of close | stockstats |
| `close_60_sma` | 60-day Simple Moving Average of close | stockstats |

**Computation:** Indicators are added by the FinRL `FeatureEngineer.add_technical_indicator()` method (`preprocessors.py`), which uses the `stockstats.Sdf.retype()` wrapper. Each indicator is computed per ticker independently and merged back onto the date-tic indexed DataFrame.

**Final feature matrix:** 19 tickers × 8 indicators = 152 columns, shape `(1111, 152)`. Column naming format: `{TICKER}_{INDICATOR}`, e.g., `RELIANCE.NS_macd`.

**Regime features: NOT PRESENT.** Despite the architecture documentation describing regime signals (bull/bear indicator, volatility regime, trend regime, market-state features) as engineered inputs, **no regime features exist in the frozen dataset**. A search for columns matching "bull", "bear", "regime", "market_state", or "marketstate" in the feature matrix returns zero matches. The frozen features contain only the 8 technical indicators listed above.

**Total feature dimension per timestep:** 152 (19 assets × 8 indicators).

**Evidence:**
- File: `finrl/config.py`, list `INDICATORS` (lines 21-30)
- File: `finrl/meta/preprocessor/preprocessors.py`, class `FeatureEngineer`, methods `add_technical_indicator()` and `preprocess_data()`
- File: `finrl/agents/ca_marl/data_adapter.py`, function `download_and_prepare()`, lines 82-147
- Frozen data: `features_v1.0.0.pkl` — shape `(1111, 152)`, columns verified by Python inspection. **Zero columns match regime keywords.**
- File: `finrl/agents/ca_marl/market_agent.py`, function `_find_regime_columns()` (lines 37-57) — searches for regime keywords, which would return an empty list on the frozen features.

---

## 7. Data Cleaning

The following preprocessing steps occur in order (implemented in `FeatureEngineer.preprocess_data()` and `download_and_prepare()`):

1. **Sort** by date then ticker (`clean_data()`, line: `df = df.sort_values(["date", "tic"], ignore_index=True)`)
2. **Drop assets with NaN close prices** (`clean_data()`): pivots close prices, drops columns (assets) with any NaN, then filters the DataFrame to keep only surviving tickers.
3. **Add technical indicators** (`add_technical_indicator()`): 8 stockstats indicators computed per ticker, merged on `(tic, date)`.
4. **Forward-fill and backward-fill** missing values resulting from indicator computation (`preprocess_data()`, line: `df = df.ffill().bfill()`).
5. **Pivot to matrix format** (`download_and_prepare()`):
   - Close prices pivoted to `(date × ticker)` matrix.
   - Forward returns computed as `pct_change().shift(-1)` (one-step-ahead fractional return).
   - Feature matrix pivoted to `(date × {ticker_indicator})` format.
6. **Alignment**: The three DataFrames (features, forward_returns, realized_prices) are aligned to a common date index via intersection (`download_and_prepare()`, lines 129-136).
7. **Feature index reset**: The feature DataFrame's index is reset to a `RangeIndex` (from `DatetimeIndex`) before being stored.

**What is NOT done:**
- No VIX or volatility index addition (`use_vix=False` in `data_adapter.py:95`)
- No turbulence index (`use_turbulence=False` in `data_adapter.py:96`)
- No user-defined features (`user_defined_feature=False` default in `FeatureEngineer.__init__`)
- No explicit normalization or standardization of features beyond what stockstats produces
- No duplicate removal (assumes no duplicates from yfinance)

**Evidence:**
- File: `finrl/meta/preprocessor/preprocessors.py`, methods `clean_data()`, `preprocess_data()`, `add_technical_indicator()`
- File: `finrl/agents/ca_marl/data_adapter.py`, function `download_and_prepare()` (lines 63-147)
- Frozen data: `features_v1.0.0.pkl` confirmed zero missing values (verified by Python inspection)

---

## 8. Dataset Version

| Property | Value |
|----------|-------|
| **Version** | v1.0.0 |
| **Storage location** | `experiments/dataset/` |
| **Files** | `features_v1.0.0.pkl`, `forward_returns_v1.0.0.pkl`, `realized_prices_v1.0.0.pkl`, `universe.json` |
| **Metadata** | `metadata.json` |

**SHA-256 checksums (from `metadata.json`, verified against file contents):**

| File | SHA-256 |
|------|---------|
| `features_v1.0.0.pkl` | `020fadb5567cbb53744ebb38564a29dacbf642e3cfa9405b749e6932c7b1519f` |
| `forward_returns_v1.0.0.pkl` | `80cfe297468d7fd7b1ff37b6837bb2a034387638cb5a9a75bf650f436bc26ff9` |
| `realized_prices_v1.0.0.pkl` | `ad3d96dab849283a4d2dcf2af29655cd455abc8d2c44f7f68b13b2a24c8d6d64` |
| `universe.json` | `d6eb6e99fe15b8f7480f33cd73e221bbef3481449cb74b15b8145738f165d05e` |

**Verification:** All four SHA-256 checksums match the stored metadata (confirmed by Python inspection).

**Frozen status:** The dataset is frozen. The `freeze_dataset()` function in `_data_cache.py:70-112` either downloads and caches (first call) or loads from cached files (subsequent calls). All experiment scripts use `get_cached_dataset()` which reads from the frozen cache.

**Evidence:**
- File: `experiments/dataset/metadata.json` — version, checksums, timestamp
- File: `experiments/_data_cache.py` — version string `DATASET_VERSION = "v1.0.0"` (line 27), `freeze_dataset()` (lines 70-112), `load_cached_dataset()` (lines 115-143)
- File: `experiments/reproducibility_manifest.json` — field `dataset_version: "v1.0.0"` (line 15)
- Frozen data files — SHA-256 verification passed

---

## 9. Train/Test Protocol

**Validation type:** Chronological walk-forward validation with non-overlapping test windows.

**Parameters** (from `experiments/_config.py`):

| Parameter | Value |
|-----------|-------|
| Number of folds | 4 |
| Training window | 504 trading days (~2 years) |
| Validation window | 63 trading days (~3 months) |
| Test window | 126 trading days (~6 months) |
| Stride | 126 trading days (equals test window length) |

**Fold schedule** (computed from `build_fold_schedules()` with 1,111 timesteps):

| Fold | Training | Validation | Test |
|------|----------|------------|------|
| 1 | [0:504) — 2020-01-01 to 2022-01-07 | [504:567) — 2022-01-10 to 2022-04-11 | [567:693) — 2022-04-12 to 2022-10-13 |
| 2 | [126:630) — 2020-07-07 to 2022-07-12 | [630:693) — 2022-07-13 to 2022-10-13 | [693:819) — 2022-10-14 to 2023-04-19 |
| 3 | [252:756) — 2021-01-04 to 2023-01-12 | [756:819) — 2023-01-13 to 2023-04-19 | [819:945) — 2023-04-20 to 2023-10-19 |
| 4 | [378:882) — 2021-07-08 to 2023-07-19 | [882:945) — 2023-07-20 to 2023-10-19 | [945:1071) — 2023-10-20 to 2024-04-29 |

**Data leakage prevention:**
- All splits are chronological (no random shuffling).
- Training, validation, and test windows are contiguous and non-overlapping.
- Calibration pairs are subject to the ADR-024 eligibility rule: `recommendation.timestamp + label_horizon ≤ fold_training_window_end`. Pairs whose label horizon extends beyond the training window are deferred.
- The label horizon is 5 trading days for all agents.
- Calibration is fitted strictly on training-window-eligible pairs; the test window never contributes calibration data.
- Agents are retrained from scratch on each fold's training window (no parameter leakage across folds).

**Evaluation:** For each fold, agents are trained on the training window, then run inference and evaluation on the test window. Financial metrics and calibration diagnostics are computed per fold. Five random seeds (42–46) are used, yielding 20 fold-seed combinations per metric.

**Evidence:**
- File: `experiments/_config.py`, class `WalkForwardConfig` and function `build_fold_schedules()` (lines 129-162)
- File: `experiments/_walk_forward.py`, class `WalkForwardRunner.run()` (lines 74-267) — splits data, manages calibration eligibility, runs train/infer/evaluate per fold
- File: `experiments/reproducibility_manifest.json` — all parameters locked
- Fold schedule dates verified by Python inspection of `realized_prices_v1.0.0.pkl` DatetimeIndex

---

## 10. Repository Evidence Index

| Claim | Supporting Files |
|-------|-----------------|
| Data source: Yahoo Finance via yfinance | `finrl/agents/ca_marl/data_adapter.py:25-60`, `experiments/_data_cache.py:70-112`, `experiments/dataset/metadata.json:4` |
| 19 ticker universe | `experiments/_config.py:21-26`, `experiments/dataset/universe.json`, `experiments/dataset/metadata.json:5-25` |
| Universe as-of date | `experiments/_config.py:27` |
| Date range: 2020-01-01 to 2024-06-27 | `experiments/_config.py:34-35`, `experiments/dataset/metadata.json:26-29` |
| 1,111 timesteps | `realized_prices_v1.0.0.pkl` (shape verified), `reproducibility_manifest.json:16` |
| Daily frequency | `finrl/meta/preprocessor/preprocessors.py` (`clean_data()` comment), realized_prices DatetimeIndex verified |
| Raw schema (date, OHLCV, tic) | `finrl/agents/ca_marl/data_adapter.py:30-33,45,49-58` |
| 8 technical indicators from stockstats | `finrl/config.py:21-30`, `preprocessors.py:add_technical_indicator()` |
| 152 feature columns (19 × 8) | `features_v1.0.0.pkl` shape `(1111, 152)` |
| No regime features | `features_v1.0.0.pkl` zero regime-keyword columns |
| Data cleaning: sort, drop-NA assets, ffill/bfill | `preprocessors.py:clean_data()`, `preprocessors.py:preprocess_data()` |
| No VIX, turbulence, or user features | `data_adapter.py:95-96` (`use_vix=False`, `use_turbulence=False`) |
| Dataset version v1.0.0 | `experiments/_data_cache.py:27`, `metadata.json:2`, `reproducibility_manifest.json:15` |
| SHA-256 checksums | `metadata.json:36-41`, verified against file contents |
| Dataset frozen in cache | `experiments/_data_cache.py:70-112` (`freeze_dataset()`) |
| Walk-forward: 4 folds, 504/63/126, stride 126 | `experiments/_config.py:42-48,129-162`, `reproducibility_manifest.json:21-24` |
| Fold schedule (exact dates) | `_config.py:build_fold_schedules()` applied to realized_prices index |
| Calibration leakage rule (ADR-024) | `experiments/_walk_forward.py:240-253`, `finrl/agents/ca_marl/confidence_engine.py:128-145` |
| 5 seeds (42–46) | `reproducibility_manifest.json:6-12`, `experiments/_config.py:112` |
| PPO: 5,000 timesteps, lr=3e-4, batch=32, n_steps=128 | `experiments/_config.py:68-78,105`, `reproducibility_manifest.json:25-27` |

---

## 11. Experimental Setup Summary

> **Dataset.** We evaluate CA-MARL on daily OHLCV data for 19 Indian large-cap equities that are constituents of the Nifty 50 index, sourced from Yahoo Finance via the `yfinance` library. The data spans January 1, 2020 to June 27, 2024 (1,111 trading days). The universe is frozen as of January 1, 2024 to prevent hindsight bias.
>
> **Preprocessing.** Raw prices are adjusted for splits and dividends (`auto_adjust=True`). Assets with missing close prices are removed. Eight technical indicators (MACD, Bollinger Bands, RSI-30, CCI-30, DX-30, 30-day SMA, 60-day SMA) are computed per asset using the `stockstats` library and attached as features. The final feature matrix has 152 dimensions (19 assets × 8 indicators). Missing values from indicator computation are forward- and backward-filled. No additional regime features, volatility indices, or turbulence indices are included.
>
> **Walk-forward validation.** We use 4-fold chronological walk-forward validation with non-overlapping windows. Each fold comprises a training window of 504 trading days, a validation window of 63 days, and a test window of 126 days, with a stride of 126 days between successive folds. Agents are retrained from scratch on each fold's training window. Calibration pairs are accumulated under a temporal eligibility rule that prevents future information leakage. Five random seeds (42–46) are used for all experiments, yielding 20 fold-seed combinations per metric.
