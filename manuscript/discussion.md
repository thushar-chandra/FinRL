## 6 Discussion

### 6.1 Interpretation of Main Findings

**Observation.** CA-MARL achieves a mean Sharpe ratio of 1.885 across five seeds and four folds, with 19 of 20 fold-seed combinations yielding positive risk-adjusted returns. Training is stable across random initialisations (cross-seed Sharpe std = 0.087). All three agents consistently produce valid outputs without fallback.

**Observation.** CA-MARL is not statistically distinguishable from equal-weight diversification. The paired permutation test yields p = 0.3246, the sign test shows CA-MARL wins 7 of 20 comparisons (p = 0.2632), and Cohen's d is \(-0.03\) (negligible). Equal-weight fusion within the ablation study (Sharpe 1.951) also matches the CA-MARL baseline (1.939).

**Interpretation.** The 2020--2024 Indian bull market rewarded diversified market exposure broadly. In a sustained rising market, any long-only strategy that remains invested captures the market return, making it difficult for an optimisation-based strategy to meaningfully differentiate from simple diversification. This is consistent with the portfolio optimisation literature: DeMiguel et al. (2009) document that the equal-weight (1/N) portfolio consistently matches or outperforms mean-variance optimisation out of sample across multiple datasets and estimation windows.

**Interpretation.** The close agreement between CA-MARL and equal-weight fusion (1.939 versus 1.951) is consistent with the agents producing approximately diversified allocations. Under this interpretation, each agent independently converges toward a broadly diversified weight distribution, and the confidence-weighted combination of three such proposals remains diversified.

### 6.2 Cross-Fold Performance Variation

**Observation.** Performance varies substantially across walk-forward folds. Fold 01 produces a mean Sharpe ratio of 0.161, fold 03 produces 3.597. The Kruskal-Wallis test confirms that Sharpe ratios are drawn from different distributions across folds (H = 17.86, p = 0.00047). All uncorrected pairwise comparisons are significant.

**Observation.** The per-seed standard deviation across folds ranges from 1.605 to 1.756, approximately twenty times the cross-seed standard deviation of 0.087.

**Interpretation.** The results suggest that temporal market conditions were the dominant source of performance variation for this period and universe. Fold 01's test window (April--October 2022) coincides with the onset of a broad equity market decline, while fold 03's test window (April--October 2023) falls within a strong recovery. The observed pattern---low or negative returns during drawdown periods, high returns during bull phases---is consistent with market-driven performance. This aligns with prior evidence that market-timing effects generally outweigh security-selection effects in portfolio performance (Brinson et al., 1986).

**Speculation.** The near-identical performance of CA-MARL and equal-weight across folds 02--04 (Sharpe differences of 0.003--0.046) suggests that when the broader market trend is favourable, the incremental value of learned allocation strategies over uniform diversification is limited. Whether a more turbulent or trendless market would reveal a larger gap is an open question that the present data cannot address.

### 6.3 Calibration and Confidence Assessment

**Observation.** The calibration pipeline accumulates zero calibration pairs across all four walk-forward folds. Every agent receives the identity mapping: calibrated confidence equals raw confidence in every fold.

**Interpretation.** The temporal alignment between the walk-forward schedule and the data-leakage eligibility rule prevents calibration pairs from accumulating. The eligibility rule requires that a recommendation's timestamp plus the label horizon (5 trading days) does not exceed the next fold's training window end. However, each fold's test window---which is the source of recommendation timestamps---always ends after the next fold's training window end when stride equals test window length (126 days). Consequently, no generated label can ever satisfy the eligibility condition. An alternative accumulation procedure that sources pairs from the validation window was implemented but is not connected to the walk-forward loop. The calibration pipeline is structurally correct; the failure is a configuration-dependent interaction between the walk-forward schedule and the eligibility condition.

**Impact.** Because calibrated confidence equals raw confidence, the reported ECE and Brier scores (Table 4) measure raw miscalibration---not post-calibration accuracy. The allocation agent's mean ECE of 0.493 (near the maximum of 0.5 for binary outcomes) indicates that its raw confidence estimates carry almost no calibration information.

**Observation.** The confidence-weighting mechanism provides no measurable benefit in the frozen experiments. Equal-weight fusion (unweighted agent averaging) produces a Sharpe ratio of 1.951, nearly identical to the CA-MARL baseline of 1.939. Shuffled confidence also matches the baseline (1.952).

**Interpretation.** With the calibration pipeline producing identity mappings, the confidence scores used for fusion are uncalibrated raw values that do not differentiate agent expertise. Even if calibration were functional, the narrow ablation range (1.842--2.010) suggests that the specific values of the confidence weights have limited impact on the fused allocation. This is consistent with all three agents producing similar diversified proposals, making the weighting scheme largely inconsequential.

### 6.4 Ablation Analysis

**Observation.** All seven ablation variants produce Sharpe ratios within a narrow range (1.842--2.010). Dropping the market agent yields the highest Sharpe ratio (2.010); dropping the allocation agent yields the lowest (1.842).

**Interpretation.** The tight clustering of ablation results has two compatible interpretations. First, the three-agent decomposition is robust: no single agent is uniquely critical. Second, the decomposition may be redundant: in this market environment, two agents---or even one---suffice to produce similar allocations. The fact that removing the market agent improves performance suggests that its categorical directional recommendations, once transformed to continuous weight proposals, may introduce noise rather than signal.

**Limitation.** The ablation study uses a single temporal 80/20 train/test split, not the walk-forward protocol. The CA-MARL baseline under this protocol (1.939) exceeds the walk-forward cross-seed mean (1.885), indicating the single split may produce more favourable results. The ablation results are exploratory and do not carry the same evidential weight as the walk-forward findings.

### 6.5 Comparison with Prior Work

The design of CA-MARL is informed by two primary precedents: DeepTrader (Wang et al., 2021) and MARS (Chen et al., 2026). DeepTrader introduced market-condition embeddings for single-agent DRL portfolio allocation. CA-MARL extends this by decomposing the investment decision into three specialised agents and by adding explicit confidence estimation and calibration.

MARS proposed a heterogeneous multi-agent RL architecture with a meta-controller that dynamically reweights agent contributions. CA-MARL differs in two respects. First, CA-MARL uses a deterministic confidence-weighted fusion formula rather than a learned meta-controller, making the fusion process independently auditable. Second, CA-MARL exposes calibrated confidence scores as explicit outputs, whereas MARS's meta-controller weights are implicit.

Neither DeepTrader nor MARS reports calibration metrics or negative findings of the kind documented here. No claim of empirical superiority over either prior system is made.

Beyond direct performance comparison, this paper contributes a reproducible experimental methodology for evaluating confidence-aware multi-agent portfolio systems. The evaluation framework includes a frozen, versioned dataset (v1.0.0, SHA-256 verified), a 4-fold walk-forward protocol with deterministic train/validation/test splits, dynamic runtime instrumentation for verifying pipeline execution, and a complete reproducibility manifest. These methodological contributions enable independent verification and extension of the results, addressing a recognised reproducibility gap in RL-based portfolio research.

### 6.6 The Role of Negative Results

The calibration non-function and the absence of statistically significant improvement over equal-weight are the paper's most informative findings. They document two non-obvious outcomes: first, that a calibration pipeline can be structurally complete yet non-functional due to a configuration-dependent temporal interaction; second, that a three-agent RL system with confidence-weighted fusion can produce allocations that are empirically indistinguishable from naive diversification in the tested market.

Reporting these findings transparently serves two purposes. It provides future researchers with concrete failure modes to avoid, and it contributes to a more reliable empirical literature in RL-based portfolio management, where negative results are under-published.

These findings also clarify the boundaries of the proposed framework. The architecture is designed to support calibrated confidence and differentiated agent contributions, but this support requires a walk-forward schedule that allows calibration pairs to accumulate. The frozen experiments test the architecture as implemented, not the architecture as designed.

### 6.7 Transition to Limitations

Several design choices and experimental constraints limit the generality of these findings. The most consequential is the calibration non-function, which means the system's confidence-aware fusion operates on uncalibrated estimates. Additional limitations---concerning the market universe, transaction costs, statistical power, and ablation methodology---are addressed in the following section.
