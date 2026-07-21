## 5 Results

### 5.1 Financial Performance

CA-MARL produces a mean Sharpe ratio of 1.885 (95% CI: [1.809, 1.961]) across five random seeds and four walk-forward folds. Nineteen of twenty fold-seed combinations yield positive Sharpe ratios; one combination (seed 43, fold 01) produces a negative value of \(-0.089\). The mean Sortino ratio is 3.327 (95% CI: [3.096, 3.559]), mean maximum drawdown is \(-6.5\%\) (95% CI: [\(-6.7\%\), \(-6.3\%\)]), mean annualised volatility is 11.5% (95% CI: [11.4%, 11.7%]), and mean per-fold cumulative return is 9.6% (95% CI: [9.1%, 10.0%]). Table 1 reports the full summary statistics.

Figure 2 shows the cumulative return trajectory of each strategy. CA-MARL tracks the equal-weight and buy-and-hold baselines closely throughout the evaluation period, while the static mean-variance portfolio diverges negatively. Across the same test windows, equal-weight achieves a mean per-fold cumulative return of 9.5% and buy-and-hold achieves 9.5%.

### 5.2 Walk-Forward Analysis

Performance varies substantially across walk-forward folds (Table 2). The mean Sharpe ratio across seeds is 0.161 for fold 01, 0.756 for fold 02, 3.597 for fold 03, and 3.027 for fold 04. This cross-fold variation is statistically significant: a Kruskal-Wallis test on Sharpe ratios grouped by fold yields H = 17.86 (p = 0.00047). All uncorrected pairwise post-hoc Mann-Whitney comparisons are significant at p < 0.01.

The temporal structure of the data and the fold boundaries are shown in Figure 1. The pattern of low Sharpe ratios in early folds and high Sharpe ratios in later folds is consistent across all five random seeds (Table 2, rows grouped by seed).

### 5.3 Statistical Comparison with Baselines

Across the same four test windows, the equal-weight (1/N) baseline achieves a Sharpe ratio of 1.931, buy-and-hold achieves 1.916, and static mean-variance optimisation (MVO) achieves \(-0.288\).

The paired permutation test (100,000 permutations) comparing CA-MARL against equal-weight finds a mean Sharpe difference of \(-0.0455\) (p = 0.3246), indicating no statistically significant difference at the \(\alpha = 0.05\) threshold. The two-tailed sign test shows that CA-MARL outperforms equal-weight in 7 of 20 fold-seed comparisons (35%, p = 0.2632). Cohen's d for the CA-MARL versus equal-weight comparison is \(-0.03\) (negligible effect size). Against static MVO, Cohen's d is \(+1.43\) (large effect size).

Equal-weight outperforms CA-MARL in fold 01 (mean Sharpe 0.300 versus 0.161) and fold 03 (3.643 versus 3.597). In fold 02 the comparison is near-identical (CA-MARL 0.756, equal-weight 0.753), as it is in fold 04 (3.027 versus 3.028).

### 5.4 Training Stability

The cross-seed standard deviation of the mean Sharpe ratio is 0.087. Individual seed means range from 1.823 (seed 45) to 2.035 (seed 46). The per-seed standard deviation across folds (Table 2) ranges from 1.605 (seed 43) to 1.756 (seed 46), compared to the cross-seed standard deviation of 0.087.

### 5.5 Ablation Analysis

Ablation results are reported in Table 3 and visualised in Figure 3. All seven ablation variants produce Sharpe ratios within a narrow range of 1.842 to 2.010. The CA-MARL baseline achieves a Sharpe ratio of 1.939 under the ablation configuration.

Equal-weight fusion (unweighted average of agent proposals) yields 1.951, shuffled confidence yields 1.952, and no calibration (using raw confidence directly) yields 1.939---identical to the CA-MARL baseline. Dropping the risk agent yields 1.881, dropping the allocation agent yields 1.842, and dropping the market agent yields 2.010.

The ablation study uses a single temporal 80/20 train/test split rather than the full walk-forward protocol and is reported as an exploratory result without statistical replication.

### 5.6 Calibration Assessment

The calibration pipeline accumulates zero calibration pairs across all four walk-forward folds. Consequently, every agent in every fold receives an identity mapping---calibrated confidence equals raw confidence. This is confirmed by dynamic runtime instrumentation of all four folds.

Diagnostic calibration metrics (Table 4, Figure 4) are computed on the identity-mapped raw confidence estimates. Across all folds and seeds, the mean Expected Calibration Error (ECE) is 0.170 for the market agent, 0.372 for the risk agent, and 0.493 for the allocation agent. The corresponding mean Brier scores are 0.035, 0.143, and 0.244.

Since the calibration output is the identity mapping, these metrics describe the raw confidence estimates rather than post-calibration accuracy.

### 5.7 Verification of Allocation Validity

All 20 fold-seed combinations produce valid portfolio allocations without triggering fallback mechanisms. The `fallback_used` flag is `false` in every case.
