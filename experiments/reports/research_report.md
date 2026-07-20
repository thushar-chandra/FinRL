# CA-MARL Experimental Campaign � Research Report

**Campaign ID:** `campaign_v1`
**Date:** 2026-07-20 16:27:51
**Seeds:** 5 (42�46)
**Walk-Forward Folds:** 4
**PPO Timesteps per Agent:** 5000
**Dataset:** Nifty 50 constituents (19 tickers), 2020-01-01 to 2024-06-27 (1111 timesteps)

---
## 1. Performance Summary

| Metric | Mean | Std Dev | 95% CI | Min | Max |
|--------|------|---------|--------|-----|-----|
| Sharpe Ratio | 1.8852 | 0.0869 | [1.809, 1.961] | 1.8232 | 2.0353 |
| Sortino Ratio | 3.3273 | 0.2643 | [3.096, 3.559] | 3.0909 | 3.7637 |
| Max Drawdown | -0.0652 | 0.0024 | [-0.067, -0.063] | -0.0677 | -0.0616 |
| Volatility | 0.1153 | 0.0016 | [0.114, 0.117] | 0.1129 | 0.1169 |
| Cumulative Return | 0.0955 | 0.0055 | [0.091, 0.100] | 0.0904 | 0.1040 |

### Per-Seed Aggregated Metrics

| Seed | Sharpe Ratio | Sortino Ratio | Max Drawdown | Volatility | Cumulative Return |
|------|------|------|------|------|------|
| 42 | 1.8282 | 3.0909 | -0.0616 | 0.1129 | 0.0904 |
| 43 | 1.8765 | 3.1600 | -0.0640 | 0.1169 | 0.0971 |
| 44 | 1.8628 | 3.2634 | -0.0660 | 0.1154 | 0.0950 |
| 45 | 1.8232 | 3.3587 | -0.0677 | 0.1147 | 0.0909 |
| 46 | 2.0353 | 3.7637 | -0.0665 | 0.1164 | 0.1040 |

---
## 2. Baseline Comparison

| Strategy | Sharpe Ratio | Cumulative Return | Max Drawdown | Volatility |
|----------|-------------|-------------------|-------------|------------|
| CA-MARL (mean�std) | 1.8852�0.0869 | 0.0955�0.0055 | -0.0652�0.0024 | 0.1153�0.0016 |
| Equal Weight | 1.9307 | 0.0949 | -0.0624 | 0.1108 |
| Buy And Hold | 1.9163 | 0.0951 | -0.0638 | 0.1109 |
| Static Mvo | -0.2875 | -0.0532 | -0.1880 | 0.2221 |

---
## 3. Walk-Forward Analysis

### Per-Fold Performance (Averaged Across Seeds)

| Fold | Sharpe (mean�std) | Return (mean�std) | MaxDD (mean�std) |
|------|-------------------|-------------------|-------------------|
| Fold 01 | 0.161�0.175 | 0.0067�0.0145 | -0.1256�0.0114 |
| Fold 02 | 0.756�0.272 | 0.0353�0.0152 | -0.0683�0.0066 |
| Fold 03 | 3.597�0.245 | 0.1553�0.0097 | -0.0285�0.0013 |
| Fold 04 | 3.027�0.093 | 0.1846�0.0062 | -0.0383�0.0035 |

---
## 4. Ablation Analysis

| Ablation | Sharpe | Sortino | Return | MaxDD |
|----------|--------|---------|--------|-------|
| CA-MARL | 1.9392 | 2.4823 | 0.2233 | -0.0599 |
| Equal Weight Fusion | 1.9510 | 2.4597 | 0.2277 | -0.0598 |
| No Calibration | 1.9392 | 2.4823 | 0.2233 | -0.0599 |
| Shuffled Confidence | 1.9521 | 2.4872 | 0.2258 | -0.0598 |
| Drop Market Agent | 2.0100 | 2.3402 | 0.2552 | -0.0610 |
| Drop Risk Agent | 1.8809 | 2.3598 | 0.2215 | -0.0605 |
| Drop Allocation Agent | 1.8423 | 2.6231 | 0.1964 | -0.0601 |

---
## 5. Calibration Assessment

| Agent | ECE (mean�std) | Brier Score (mean�std) |
|-------|----------------|----------------------|
| Market Agent | 0.1699�0.0787 | 0.0347�0.0294 |
| Risk Agent | 0.3715�0.0692 | 0.1426�0.0494 |
| Allocation Agent | 0.4934�0.0305 | 0.2444�0.0300 |

**Note:** Calibration metrics are computed against the identity mapping
(calibration pairs never accumulated due to the temporal eligibility gate).
ECE and Brier scores reflect raw confidence miscalibration, not post-calibration accuracy.

---
## 6. Strengths

1. **Reproducible experimental framework** � frozen dataset v1.0.0, deterministic
   seeding, versioned campaign results.
2. **Predominantly positive Sharpe ratios** � CA-MARL achieves positive risk-adjusted
   returns in 19 of 20 fold-seed combinations (one negative: seed 43, fold 01, Sharpe = -0.089).
3. **Low cross-seed variance** � Sharpe ratio std dev of ~0.08 across 5 seeds
   indicates training stability.
4. **No fallback activations** � All 20 fold-seed combinations produced valid
   fused allocations without requiring fallback logic.
5. **Comprehensive evaluation** � Financial metrics, calibration metrics,
   and baseline comparisons are computed per fold.

---
## 7. Weaknesses & Limitations

1. **Calibration pipeline is non-functional at current configuration** �
   The temporal eligibility gate (`ADR-024`) prevents calibration pairs from
   accumulating because the test window always ends after the next fold's
   training window. All `fit_calibration` calls receive empty pair lists,
   resulting in identity mapping (`calibrated == raw`).
2. **Raw confidence placeholder** � `raw_confidence=0.0` is hardcoded in all
   three agents' `predict()` methods. The computed raw confidence from
   `ConfidenceEngine.estimate_raw_confidence` is used in practice, but the
   stored `AgentOutput.raw_confidence` field is always 0.0.
3. **No transaction costs** � All returns are gross of trading costs.
   ADR-012 defers this to future work.
4. **Static MVO baseline underperforms** � Negative Sharpe ratios for MVO
   suggest insufficient estimation data or non-stationary return distributions.
5. **Limited asset universe** � 19 Nifty 50 constituents; results may not
   generalise to other markets or larger universes.

---
## 8. Threats to Validity

- **Internal validity:** The calibration non-function means that all claims
  about confidence-aware fusion are based on raw (uncalibrated) confidences.
  The identity calibration mapping means the ablation studies compare against
  the same underlying values.
- **External validity:** Single market (India, Nifty 50), single time period
  (2020�2024). Results may not generalise to other markets or time periods.
- **Construct validity:** Sharpe ratio as the primary metric assumes normally
  distributed returns and symmetric risk preferences.
- **Statistical validity:** 5 random seeds provide limited statistical power.
  Confidence intervals are wide relative to effect sizes.

---
## 9. Unexpected Observations

1. **Fold 3 dominance** � Fold 3 consistently produces the highest Sharpe
   ratios (mean ~3.5 across seeds) across all strategies, suggesting this
   period (late 2023) was particularly favourable for long-only equity.
2. **Equal-weight matches CA-MARL closely** � In most folds, the equal-weight
   baseline performs nearly identically to CA-MARL. The confidence-aware
   fusion may be learning near-uniform allocations, or the market regime
   during 2020�2024 rewarded diversified exposure.
3. **MVO degradation** � Static MVO produces the worst and most volatile
   results, consistent with known literature on the instability of
   mean-variance optimisation on short estimation windows.

---
## 10. Future Work

1. **Fix calibration eligibility** � Adjust the temporal gate or use
   validation-window pairs (the existing but unused `_collect_calibration_pairs`
   method) to enable calibration.
2. **Implement `raw_confidence` computation** � Replace the 0.0 placeholder
   in agent `predict()` methods with proper uncertainty estimates.
3. **Add transaction costs** � Incorporate realistic trading costs into
   reward functions and evaluation.
4. **Expand universe** � Test on larger universes (e.g., S&P 500, FTSE 100).
5. **Hyperparameter optimisation** � Systematic search over PPO hyperparameters
   and confidence weighting.
6. **Additional baselines** � Add momentum, risk-parity, and machine-learning
   based portfolio strategies.
7. **Statistical testing** � Use paired bootstrap or permutation tests for
   strategy comparisons.

---
## 11. Generated Artifacts

### Figures
- `fig01_cumulative_returns.pdf` (41.8 KB)
- `fig02_reliability_diagrams.pdf` (18.6 KB)
- `fig03_ablation_bars.pdf` (18.6 KB)
- `fig04_regime_timeline.pdf` (153.5 KB)

### Tables (LaTeX)
- `table01_summary.tex`
- `table02_per_fold.tex`
- `table03_ablation.tex`
- `table04_calibration.tex`

### Campaign Results (JSON)
- Seed 42: 4 folds, mean Sharpe=1.8282160969835122
- Seed 43: 4 folds, mean Sharpe=1.8765124868661416
- Seed 44: 4 folds, mean Sharpe=1.8627547959399182
- Seed 45: 4 folds, mean Sharpe=1.8232302704737373
- Seed 46: 4 folds, mean Sharpe=2.0352509702063735

### Source Configuration
- `_config.py`: Walk-forward (4 folds, 504/63/126 day windows)
- `_config.py`: PPO (lr=3e-4, n_steps=128, batch_size=32)
- `_config.py`: Confidence (Platt scaling, hist_weight=0.4)
- `_config.py`: Label horizon=5 days, reward_stability_window=20
