# PAPER_BLUEPRINT.md — CA-MARL Manuscript Design Document

> **Status:** Phase 4 — Scientific Analysis
> **Repository State:** Frozen (commit `ba81e82`, tag `v2.0-phase3-complete`)
> **Purpose:** Master guide for manuscript writing. Not the paper itself.
> **Evidence Basis:** All claims traceable to experimental JSON, dynamic verification logs, statistical analyses, and architectural documentation. No speculation.

---

## 1. Research Problem

### Problem Statement

Portfolio allocation is a sequential decision problem under uncertainty. Deep reinforcement learning (DRL) has been applied to this problem, but existing systems produce point-estimate allocations without quantifying the trustworthiness of their own outputs. A portfolio manager deploying a DRL system cannot distinguish between a high-confidence recommendation backed by consistent evidence and a low-confidence recommendation that the system is uncertain about.

This lack of transparency has two consequences:
1. **Deployment risk**: A manager cannot know when to override or discount the system.
2. **Diagnostic opacity**: When the system underperforms, there is no calibrated signal to attribute the failure to market-direction error, risk misestimation, or allocation suboptimality.

### Importance

- Portfolio management is a high-stakes domain where blind trust in black-box recommendations is unacceptable.
- Existing multi-agent RL portfolio systems (DeepTrader, MARS) do not expose calibrated confidence scores.
- Financial regulation (MiFID II, AI Act) increasingly requires explainability and risk transparency in automated investment advice.

---

## 2. Research Gap

### Literature Gap

| Prior Work | What It Does | What It Does Not Do |
|------------|-------------|---------------------|
| DeepTrader (Wang et al., AAAI 2021) | Single-agent DRL with market-condition embedding | No per-agent confidence estimation; no calibration |
| MARS (Chen et al., AAAI 2026) | Heterogeneous multi-agent RL ensemble with meta-controller | Meta-controller reweighting is opaque/implicit; no calibrated confidence scores |
| MAPS, MoE-DRLPM | Multi-agent / mixture-of-experts portfolio RL | No explicit confidence layer |
| Guo et al. (2017); Naeini et al. (2015) | Calibration methodology (ECE, Platt scaling) | Applied to classification, not to RL-based portfolio agents |

### Limitations This Project Addresses

1. **Lack of explicit confidence**: No prior portfolio RL system produces calibrated, human-facing confidence scores per agent.
2. **Opaque fusion**: Prior systems fuse agent outputs through learned gates or meta-controllers that cannot be independently validated.
3. **Insufficient reproducibility**: Most portfolio RL papers report results from single runs without frozen datasets or versioned experiments.

### Limitations This Project Does NOT Address

- Transaction cost modelling (deferred to future work per ADR-012).
- MARS baseline reproduction (stretch goal per ADR-008).
- Hyperparameter sensitivity analysis.

---

## 3. Research Questions

### Primary Research Question

**RQ1**: Can a confidence-aware multi-agent reinforcement learning framework produce valid portfolio allocations with transparent, calibrated uncertainty estimates?

### Secondary Research Questions

**RQ2**: Can three specialized RL agents (market analysis, risk assessment, portfolio allocation) learn differentiated policies that together produce coherent portfolio decisions?

**RQ3**: Does the confidence-aware fusion mechanism provide measurable benefit over naive equal-weight fusion?

**RQ4**: Can the confidence calibration pipeline produce non-identity mappings under walk-forward validation?

---

## 4. Hypotheses and Experimental Verdicts

| # | Hypothesis | Verdict | Evidence | Notes |
|---|-----------|---------|----------|-------|
| H1 | Three specialized PPO agents can be trained to produce stable, valid recommendations under walk-forward validation. | **Supported** | All 20 fold-seed combinations: `fallback_used = false`. Cross-seed Sharpe std = 0.087. | Agents produce valid outputs without fallback across all folds and seeds. |
| H2 | Confidence can be estimated from historical accuracy, reward stability, and prediction consistency, and calibrated via Platt scaling to produce non-identity mappings. | **Not Supported** | Zero calibration pairs across all 4 folds (dynamic verification). `fit_calibration` receives `[]` every fold. Identity mapping: calibrated = raw. | The calibration pipeline is structurally correct but non-functional due to temporal alignment between the walk-forward schedule and the ADR-024 eligibility gate. |
| H3 | Confidence-aware fusion (CA-MARL) produces superior risk-adjusted returns compared to equal-weight (1/N) baseline. | **Not Supported** | CA-MARL mean Sharpe = 1.885 (95% CI: [1.809, 1.961]). Equal-weight = 1.931. Paired permutation test: p = 0.3246. Sign test: 7/20 wins, p = 0.2632. Cohen's d = −0.03 (negligible). | No statistically significant difference. CA-MARL and equal-weight are effectively indistinguishable in this market and period. |
| H4 | The three-agent decomposition (market, risk, allocation) is non-redundant; each agent contributes meaningfully to the fused decision. | **Inconclusive** | Single-run ablation: Sharpe range 1.842 (drop allocation) to 2.010 (drop market). No statistical testing; single train/test split; not walk-forward. | Insufficient evidence. Ablations lack replication across seeds and folds. |
| H5 | Walk-forward validation reveals temporal non-stationarity that affects strategy performance. | **Supported** | Kruskal-Wallis: H = 17.86, p = 0.00047. Fold 01 mean Sharpe = 0.161; Fold 03 mean Sharpe = 3.597. All pairwise post-hoc comparisons significant at p < 0.01. | Regime effect is the dominant source of performance variation. |
| H6 | The system produces positive risk-adjusted returns. | **Partially Supported** | 19/20 fold-seed Sharpe ratios positive (mean = 1.885). One negative: seed 43, fold 01, Sharpe = −0.089. | Predominantly positive but not universally so. Performance is regime-dependent. |

---

## 5. Actual Contributions

### Engineering Contributions

1. **Complete CA-MARL pipeline**: Seven-module architecture (data → features → 3× RL agents → confidence estimation & calibration → deterministic fusion → risk management → evaluation) implemented on the Indian Nifty 50 universe (19 assets, 1111 trading days, 2020–2024).
2. **Reproducible experimental framework**: Frozen dataset v1.0.0 (SHA-256 verified), deterministic seeding, versioned JSON results, campaign-specific identifiers, full reproducibility manifest.
3. **Walk-forward evaluation harness**: 4-fold chronological validation (504/63/126-day windows, stride 126), with per-fold baselines, calibration metrics, and ablation support.
4. **Publication-quality output generators**: Automated figure and LaTeX table generation from experimental JSON.

### Scientific Contributions

5. **Empirical evaluation of confidence-aware fusion**: CA-MARL produces a mean Sharpe ratio of 1.885 (95% CI: [1.809, 1.961]) — comparable but not superior to equal-weight (1.931). The difference is not statistically significant (permutation p = 0.3246).
6. **Documented calibration non-function**: The confidence calibration pipeline produces identity mappings at the current walk-forward configuration. Zero calibration pairs accumulate across all folds due to a temporal mismatch between the test window and the ADR-024 eligibility gate. This is an honest negative finding.
7. **Quantified regime effect**: Walk-forward folds produce significantly different Sharpe distributions (Kruskal-Wallis p = 0.00047). Fold means range from 0.161 to 3.597. Market regime is the dominant factor in performance variation.
8. **Training stability demonstration**: Five random seeds produce low cross-seed variance (Sharpe std = 0.087), demonstrating training stability across initializations.

### Reproducibility Contributions

9. **Full artifact manifest**: All figures, tables, JSON results, and reports enumerated with file sizes.
10. **47-pass verification suite**: Automated consistency checks across all experimental outputs.
11. **Dynamic verification instrumentation**: Monkey-patched runtime logging confirming calibration pipeline behaviour across all folds.

---

## 6. Central Narrative

### One-Paragraph Summary

CA-MARL is a confidence-aware multi-agent reinforcement learning framework for portfolio allocation that decomposes the investment decision into three specialized RL agents (market analysis, risk assessment, portfolio allocation) and fuses their recommendations using a deterministic confidence-weighted formula. Evaluated on 19 Indian large-cap equities across 2020–2024 with 4-fold walk-forward validation and 5 random seeds, CA-MARL produces positive risk-adjusted returns (mean Sharpe = 1.885) that are comparable to equal-weight diversification but not statistically distinguishable from it. The confidence calibration pipeline, designed to produce calibrated uncertainty estimates per agent, does not produce non-identity mappings due to a temporal alignment issue between the walk-forward schedule and the data-leakage eligibility rule — a negative finding reported transparently. The framework contributes a reproducible experimental methodology, an honest assessment of what confidence-aware fusion achieves and does not achieve, and a concrete demonstration that market regime, rather than strategy choice, is the dominant factor in performance during the 2020–2024 bull market.

---

## 7. Paper Structure

### Title Options

1. **CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for Portfolio Allocation**
2. **Confidence-Aware Multi-Agent RL for Portfolio Allocation: A Reproducible Empirical Evaluation**
3. **Transparent Uncertainty in Multi-Agent Portfolio RL: The CA-MARL Framework**

**Recommendation:** Option 2 — it signals the reproducible methodology contribution and avoids overclaiming performance superiority.

### Abstract (~200 words)

- **Purpose**: Summarize the problem, method, key results, and limitations.
- **Key points**: (1) Three-agent RL architecture with confidence-weighted fusion, (2) empirical evaluation on Nifty 50, (3) comparable to equal-weight, (4) calibration non-function documented, (5) regime effect dominates.
- **No overclaims**: Must not claim outperformance. Must mention calibration limitation.

### 1. Introduction (~1.5 pages)

- **Purpose**: Motivate the problem, state the gap, state the research questions, preview contributions.
- **Arguments**:
  - Portfolio allocation needs transparent uncertainty estimates.
  - Existing DRL portfolio systems (DeepTrader, MARS) do not provide calibrated confidence.
  - CA-MARL addresses this with a three-agent decomposition + confidence-weighted fusion.
  - The paper presents an honest empirical evaluation including negative findings.
- **Evidence**: Citations only. No experimental results.
- **Expected length**: 3–4 paragraphs.

### 2. Related Work (~2 pages)

- **Purpose**: Position CA-MARL relative to existing literature.
- **Sections**:
  - 2.1 DRL for Portfolio Management (DeepTrader, MARS, MAPS, FinRL ecosystem)
  - 2.2 Multi-Agent RL in Finance (MARS as closest prior art; explicit vs. implicit fusion)
  - 2.3 Uncertainty Estimation and Calibration (Guo et al., 2017; Naeini et al., 2015; deep ensembles)
- **Arguments**:
  - MARS uses implicit meta-controller; CA-MARL uses explicit, independently-testable confidence.
  - Calibration methodology is standard (ECE, Platt scaling), but novel in the portfolio RL context.
- **Evidence**: Literature citations. No experimental results.
- **Expected length**: 4–5 paragraphs.

### 3. Method — Architecture (~3 pages)

- **Purpose**: Describe the CA-MARL pipeline in sufficient detail for reproduction.
- **Sections**:
  - 3.1 System Overview (pipeline diagram; the seven modules)
  - 3.2 RL Agents (three specialized PPO agents; shared infrastructure; reward design)
  - 3.3 Confidence Estimation and Calibration (three input signals; OutcomeLabelGenerator; ADR-024 leakage rule; Platt scaling)
  - 3.4 Confidence-Aware Decision Fusion (deterministic weighted average; AssetWeightProposal transforms; sum-to-one proof)
  - 3.5 Risk Management Layer (long-only, sum-to-one enforcement)
- **Arguments**:
  - Architecture is frozen; each module has one responsibility.
  - Fusion is explicitly NOT PPO-based (a key point of distinction from MARS).
  - Calibration leakage rule prevents lookahead bias.
- **Evidence**: Architectural documentation (ARCHITECTURE.md, MODULE_SPECIFICATIONS.md, CONFIDENCE_FUSION.md).
- **Figures**: fig04 (regime timeline, showing fold boundaries)
- **Expected length**: 6–8 paragraphs.

### 4. Experimental Setup (~1.5 pages)

- **Purpose**: Describe dataset, walk-forward procedure, baselines, training hyperparameters, and evaluation metrics.
- **Sections**:
  - 4.1 Dataset (Nifty 50, 19 tickers, 2020-01-01 to 2024-06-27, 1111 trading days, fixed as-of date per ADR-011)
  - 4.2 Walk-Forward Validation (4 folds, 504/63/126-day windows, stride 126)
  - 4.3 Training Configuration (PPO: lr=3e-4, n_steps=128, batch_size=32, total_timesteps=5000 per agent)
  - 4.4 Baselines (equal-weight 1/N, buy-and-hold, static mean-variance optimization)
  - 4.5 Ablation Studies (equal-weight fusion, no calibration, shuffled confidence, drop-one-agent)
  - 4.6 Evaluation Metrics (Sharpe ratio, Sortino ratio, Max Drawdown, Volatility, Cumulative Return; ECE, Brier score)
  - 4.7 Statistical Methodology (5 random seeds, 20 paired observations, permutation test, Kruskal-Wallis, Cohen's d)
- **Evidence**: Config files, experiment plan, campaign runner.
- **Tables**: table01 (summary stats, per-seed), table04 (calibration metrics)
- **Expected length**: 4–5 paragraphs.

### 5. Results (~3 pages)

- **Purpose**: Present experimental findings without interpretation. Every claim must be an Observation.
- **Sections**:
  - 5.1 Financial Performance (overall; CA-MARL mean Sharpe = 1.885; 19/20 positive; baseline comparison)
  - 5.2 Walk-Forward Analysis (per-fold performance; regime effect; Kruskal-Wallis significance)
  - 5.3 Statistical Comparison with Baselines (permutation test, sign test, effect sizes)
  - 5.4 Training Stability (cross-seed variance; no outlier seeds; stable across folds)
  - 5.5 Ablation Analysis (equal-weight fusion, no calibration, shuffled confidence, drop-one-agent)
  - 5.6 Calibration Assessment (ECE and Brier scores; identity mapping; non-functional calibration pipeline)
  - 5.7 Verification of Allocation Validity (fallback_used = false in all cases)
- **Arguments**: Purely descriptive. Use the exact language from the 9 Supported Findings (PHASE_3_FREEZE_REPORT.md §3.1).
- **Evidence**: All figures, all tables.
- **Figures**: fig01 (cumulative returns), fig03 (ablation bars)
- **Tables**: table01, table02, table03, table04
- **Expected length**: 8–12 paragraphs.

### 6. Discussion (~2 pages)

- **Purpose**: Interpret results. Classify every claim as Observation, Interpretation, Hypothesis, or Future Work.
- **Sections**:
  - 6.1 Interpretation of Main Findings
    - **Observation**: CA-MARL matches equal-weight performance (p = 0.3246).
    - **Interpretation**: The 2020–2024 bull market made it difficult for any long-only strategy to meaningfully differentiate. The regime effect (Kruskal-Wallis p = 0.00047) supports this — fold differences dwarf strategy differences.
    - **Interpretation**: CA-MARL learns approximately diversified allocations. The equal-weight fusion ablation (Sharpe = 1.951 vs CA-MARL 1.939) supports this.
  - 6.2 Calibration Non-Function
    - **Observation**: Zero calibration pairs accumulate; identity mapping throughout.
    - **Interpretation**: The temporal mismatch between test window timing and the ADR-024 eligibility gate prevents calibration from functioning at the current walk-forward schedule. The `_collect_calibration_pairs` method (targeting the validation window) exists but is not integrated into the run loop.
    - **Impact**: Calibrated confidences equal raw confidences. ECE and Brier scores measure raw miscalibration, not post-calibration accuracy.
  - 6.3 Comparison with Prior Work (positioning CA-MARL relative to MARS/DeepTrader without claiming superiority)
  - 6.4 The Role of Negative Results
    - **Interpretation**: The calibration negative finding is a useful scientific result — it documents a failure mode that future architectures must address.
- **Evidence**: All experimental results. Dynamic verification report.
- **Expected length**: 6–8 paragraphs.

### 7. Limitations (~1 page)

- **Purpose**: Transparently acknowledge limitations. Each limitation must have a concrete basis in the evidence.
- **List** (from PHASE_3_FREEZE_REPORT.md §2.C):
  1. Calibration is non-functional at the current walk-forward schedule (L1).
  2. Single market, single time period (L2).
  3. No transaction costs (L3).
  4. Five seeds provide limited statistical power (L4).
  5. Ablation results from a single train/test split, not walk-forward (L5).
  6. Static MVO baseline disadvantaged by short estimation window (L6).
  7. No sensitivity analysis over hyperparameters (L7).
- **Expected length**: 3–4 paragraphs.

### 8. Threats to Validity (~0.5 page)

- **Purpose**: Address internal, external, construct, and statistical validity threats concisely.
- **Sections**:
  - Internal validity: Calibration non-function means confidence-aware fusion claims are based on raw confidences.
  - External validity: Single market, single time period, single universe.
  - Construct validity: Sharpe ratio assumes normally distributed returns.
  - Statistical validity: 95% CIs are wide relative to effect sizes; 20 observations limit power.
- **Expected length**: 2–3 paragraphs.

### 9. Conclusion (~0.5 page)

- **Purpose**: Summarize contributions, restate the honest assessment, indicate future work.
- **Key points**:
  - CA-MARL is a reproducible, transparent framework for multi-agent portfolio RL.
  - Performance is comparable to equal-weight; the three-agent decomposition is architecturally sound but its necessity is not proven.
  - The calibration pipeline has a documented temporal dependency that prevents operation at the current configuration — a finding that informs future calibration-aware walk-forward designs.
  - The regime effect is the dominant source of variation.
- **No new claims. No overclaims.**
- **Future work** (brief, ≥3 items): fix calibration eligibility, transaction costs, larger universe, hyperparameter sensitivity, additional baselines.
- **Expected length**: 2–3 paragraphs.

### References

- Estimated 25–35 citations.
- Required venues: Guo et al. (2017), Naeini et al. (2015), Schulman et al. (2017), Wang et al. (2021), Chen et al. (2026), DeMiguel et al. (2009), Lakshminarayanan et al. (2017), Jacobs et al. (1991), Jordan & Jacobs (1994), Markowitz (1952).

### Appendices (Optional)

- A: Full per-fold per-seed results table (extended table02).
- B: Dynamic verification methodology and full log.
- C: Dataset composition and preprocessing details.

---

## 8. Figure Placement

### fig01: Cumulative Returns

| Field | Detail |
|-------|--------|
| **Location** | §5.1 Financial Performance |
| **What it shows** | Cumulative return curves for CA-MARL (mean ± 1 std across 5 seeds) vs. equal-weight, buy-and-hold, and static MVO |
| **Point it supports** | CA-MARL closely tracks equal-weight and buy-and-hold; MVO diverges negatively |
| **Why important** | Visual evidence that CA-MARL performance is comparable to trivial baselines |
| **Caption** | "Cumulative portfolio returns across the full test period. Solid lines show mean across 5 random seeds; shaded region shows ±1 standard deviation. CA-MARL tracks equal-weight and buy-and-hold closely, while static MVO underperforms substantially." |

### fig02: Calibration Analysis

| Field | Detail |
|-------|--------|
| **Location** | §5.6 Calibration Assessment |
| **What it shows** | Scatter plot of ECE vs. Brier score per agent across folds and seeds |
| **Point it supports** | Calibration metrics are computed against identity mapping; agents show miscalibration, especially allocation agent |
| **Why important** | Provides visual evidence of the calibration state. Must be clearly labelled to avoid confusion with reliability diagrams. |
| **Caption** | "Calibration error analysis: Expected Calibration Error (ECE) versus Brier score for each agent across all folds and seeds. The calibration pipeline produces identity mappings (calibrated = raw), so these scores reflect raw confidence miscalibration rather than post-calibration accuracy. Ideal calibration would yield ECE ≈ 0 and Brier ≈ 0." |

### fig03: Ablation Bars

| Field | Detail |
|-------|--------|
| **Location** | §5.5 Ablation Analysis |
| **What it shows** | Sharpe ratio bar chart for all 7 ablation variants |
| **Point it supports** | Ablation variants cluster within a narrow range (1.842–2.010); equal-weight fusion and shuffled confidence are indistinguishable from CA-MARL baseline |
| **Why important** | Demonstrates robustness to individual agent removal and to confidence perturbations; also shows that confidence weighting is not measurably load-bearing |
| **Caption** | "Ablation study results: Sharpe ratio for each ablation variant (single train/test split). All variants cluster within a narrow range (1.842–2.010). CA-MARL, equal-weight fusion, no calibration, and shuffled confidence produce nearly identical values. The dashed line shows the equal-weight baseline Sharpe ratio (1.931) for reference." |

### fig04: Regime Timeline

| Field | Detail |
|-------|--------|
| **Location** | §5.2 Walk-Forward Analysis (or §3 Architecture to illustrate dataset) |
| **What it shows** | Nifty 50 price index over the evaluation period with fold boundary markers |
| **Point it supports** | Illustrates the temporal structure of the data and the walk-forward split; contextualizes the regime effect |
| **Why important** | Provides visual context for the walk-forward design and the non-stationarity finding |
| **Caption** | "Market timeline: Nifty 50 index price with walk-forward fold boundaries (training/validation/test windows per fold). The 2020–2024 period spans the COVID-19 recovery, a low-volatility bull market (2021–2022), and a moderate-volatility recovery." |

---

## 9. Table Placement

### table01: Summary Statistics

| Field | Detail |
|-------|--------|
| **Location** | §4 Experimental Setup (reference) or §5.1 Financial Performance |
| **Content** | Mean, std, 95% CI, min, max for Sharpe, Sortino, MaxDD, Volatility, CumRet across 5 seeds |
| **Point it supports** | CA-MARL achieves positive mean metrics with low cross-seed variance |
| **Why important** | Primary quantitative summary of CA-MARL performance |
| **Caption** | "Aggregated CA-MARL performance metrics across 5 random seeds (42–46) and 4 walk-forward folds (n = 20 seed-fold combinations per metric). 95% confidence intervals are computed using the normal approximation." |

### table02: Per-Fold Metrics

| Field | Detail |
|-------|--------|
| **Location** | §5.2 Walk-Forward Analysis |
| **Content** | Per-seed, per-fold Sharpe, Sortino, MaxDD, Vol, CumRet for all 5 seeds × 4 folds |
| **Point it supports** | Demonstrates fold-to-fold variation; shows the one negative Sharpe (seed 43, fold 01) |
| **Why important** | Shows the complete data underlying the aggregate statistics; enables reviewer scrutiny |
| **Caption** | "Complete per-seed, per-fold financial metrics for all 5 random seeds and 4 walk-forward folds. One of 20 fold-seed combinations (seed 43, fold 01) produces a negative Sharpe ratio (−0.089). The strong fold effect (Fold 01 mean Sharpe = 0.161, Fold 03 mean Sharpe = 3.597) is visually apparent." |

### table03: Ablation Results

| Field | Detail |
|-------|--------|
| **Location** | §5.5 Ablation Analysis |
| **Content** | Sharpe, Sortino, MaxDD, Vol, CumRet for CA-MARL baseline, equal-weight fusion, no calibration, shuffled confidence, drop-market, drop-risk, drop-allocation |
| **Point it supports** | Ablation variants cluster tightly; no variant dramatically outperforms or underperforms |
| **Why important** | Demonstrates robustness and also shows that confidence weighting and individual agents are not uniquely critical |
| **Caption** | "Ablation study results (single 80/20 temporal train/test split). All ablation variants produce Sharpe ratios within [1.842, 2.010]. CA-MARL with equal-weight fusion, no calibration, and shuffled confidence are indistinguishable from the baseline, confirming that (a) calibration has no effect at the current configuration and (b) the fusion formula is robust to moderate confidence perturbations." |

### table04: Calibration Metrics

| Field | Detail |
|-------|--------|
| **Location** | §5.6 Calibration Assessment |
| **Content** | ECE and Brier score mean ± std for market, risk, and allocation agents across folds and seeds |
| **Point it supports** | All agents show substantial miscalibration; allocation agent is most miscalibrated |
| **Why important** | Required for completeness; must be accompanied by footnote that calibration is identity-mapped |
| **Caption** | "Calibration metrics per agent across all folds and seeds. Since the calibration pipeline produces identity mappings (zero calibration pairs accumulated; fit_calibration always receives an empty list), these values represent raw confidence miscalibration — not post-calibration accuracy. ECE = Expected Calibration Error." |
| **Footnote** | "Calibration is identity-mapped at the current walk-forward configuration (see §6.2 for analysis)." |

---

## 10. Claims Matrix

| # | Claim | Supporting Evidence | Figure/Table | Statistical Test | Confidence Level |
|---|-------|-------------------|-------------|-----------------|-----------------|
| C1 | CA-MARL produces positive risk-adjusted returns (mean Sharpe = 1.885) | 5 seeds × 4 folds JSON data | Table 01 | 95% CI [1.809, 1.961] | High |
| C2 | 19/20 fold-seed Sharpe ratios are positive | Verified JSON audit | Table 02 | One negative out of 20 | High |
| C3 | Training is stable across random seeds (Sharpe std = 0.087) | 5-seed computation | Table 01 | Std = 0.087 across seeds | High |
| C4 | Walk-forward folds produce significantly different Sharpe distributions (regime effect) | Statistical analysis | Fig 04, Table 02 | Kruskal-Wallis H = 17.86, p = 0.00047 | High |
| C5 | All 20 fold-seed combinations produce valid allocations without fallback | JSON verification | — | — | High |
| C6 | CA-MARL is not statistically distinguishable from equal-weight (1/N) | Statistical analysis | Fig 01, Table 02 | Permutation p = 0.3246; sign test p = 0.2632; Cohen's d = −0.03 | High |
| C7 | Cumulative return of CA-MARL (9.6%) is similar to EW (9.5%) and B&H (9.5%) | JSON data | Fig 01 | Means within 0.1% | High |
| C8 | Zero calibration pairs accumulate across all 4 folds (identity mapping) | Dynamic verification audit | — | 0 pairs across all engines | High |
| C9 | Static MVO underperforms all other strategies (mean Sharpe = −0.288) | JSON data (seed 42) | Fig 01, Table 02 | Descriptive only | Medium (single seed) |
| C10 | Ablation results cluster within narrow range (Sharpe 1.842–2.010) | Single-run ablation JSON | Table 03 | Range width 0.168 | Low (single run, no replication) |
| C11 | CA-MARL matches equal-weight in 7/20 paired fold-seed comparisons | Statistical analysis | — | Sign test p = 0.2632 | High |

### Unsupported Claims (Must Not Appear)

| Claim | Reason for Exclusion |
|-------|---------------------|
| "CA-MARL outperforms baselines" | Contradicted by C6 (p = 0.3246, d = −0.03) |
| "Confidence-aware fusion improves performance" | Contradicted by C10 (equal-weight fusion gives same result) |
| "Calibration improves reliability" | Contradicted by C8 (identity mapping) |
| "Three-agent architecture is necessary" | Insufficient evidence (C10, single-run ablation) |
| "System generalises to other markets" | Single market tested (L2) |
| "System is calibrated" | Contradicted by C8 |
| "Confidence values differentiate meaningfully" | Confidence values not stored; no evidence available |
| "All 20 Sharpe ratios are positive" | Contradicted by C2 (19/20) |

---

## 11. Reviewer Expectations

### Q1: Why does CA-MARL not beat equal-weight? Isn't the point of RL to learn something better?

- **Where to address**: §6.1 Discussion
- **Response strategy**: This is the primary empirical finding. Acknowledge it directly. Three explanations: (1) The 2020–2024 Indian bull market rewarded diversified exposure broadly; (2) The "1/N puzzle" (DeMiguel et al., 2009) documents that simple diversification often matches or beats optimisation-based strategies out of sample; (3) The confidence calibration was non-functional, which may have limited the system's ability to differentiate between agents' recommendations.
- **Evidence**: Permutation test (p = 0.3246), Cohen's d = −0.03, equal-weight fusion ablation (Sharpe = 1.951 vs CA-MARL 1.939).

### Q2: What is the point of the calibration pipeline if it doesn't work?

- **Where to address**: §6.2 Discussion, §7 Limitations
- **Response strategy**: Frame as an honest negative finding. The pipeline is structurally correct (ASE documented, ADR-024 leakage rule implemented, `_collect_calibration_pairs` method exists). The failure is a temporal alignment issue between the walk-forward schedule and the eligibility gate — a non-obvious interaction discovered through systematic testing. This finding is itself a scientific contribution: it documents a failure mode that future calibration-aware walk-forward designs must account for.
- **Evidence**: Dynamic verification report, PHASE_3_COMPLETION_REPORT §2.A F7, AGENTS.md audit.

### Q3: Five seeds are not enough for statistical rigour.

- **Where to address**: §7 Limitations (L4), §8 Threats to Validity
- **Response strategy**: Acknowledge as a limitation. 5 seeds × 4 folds = 20 paired observations. The permutation test and sign test are appropriate for this sample size, but confidence intervals are wide. Propose larger seed studies as future work.
- **Evidence**: Actual CIs reported in Table 01.

### Q4: Only one market and one time period — how is this generalisable?

- **Where to address**: §7 Limitations (L2), §8 Threats to Validity
- **Response strategy**: Acknowledge as a limitation. The paper does not claim generalisability. The framework is designed to be configurable to other markets; this is noted as future work. The contribution is the framework and evaluation methodology, not a universal claim about CA-MARL's performance.

### Q5: The ablation study uses a single train/test split, not walk-forward. How representative is it?

- **Where to address**: §7 Limitations (L5)
- **Response strategy**: Acknowledge as a limitation. The ablation results are exploratory and should not be given the same weight as the walk-forward results. Future work should replicate ablations across walk-forward folds.

### Q6: Why use equal-weight as a baseline? It's trivial.

- **Where to address**: §2 Related Work, §6.3 Discussion
- **Response strategy**: Equal-weight is the standard baseline in portfolio optimisation literature (DeMiguel et al., 2009). It is not intended to be a challenging competitor — it is a reference point. The fact that CA-MARL matches it honestly is an informative finding, not a weakness. MARS and DeepTrader were planned as additional baselines but could not be reliably reproduced within the project timeline.

### Q7: What does "confidence-aware" mean if the calibration doesn't work and the confidence values are not shown to differentiate?

- **Where to address**: §6.2 Discussion, §6.4 The Role of Negative Results
- **Response strategy**: The term "confidence-aware" refers to the architecture: the system estimates, calibrates, and exposes confidence scores. The experimental finding is that calibration does not produce non-identity mappings at this configuration — this does not invalidate the architectural contribution. The architecture is designed to be confidence-aware; future work with corrected calibration can evaluate whether confidence awareness provides measurable benefit.

### Q8: Why didn't you use reliability diagrams?

- **Where to address**: §5.6 (footnote), §7 Limitations
- **Response strategy**: Reliability diagrams require stored (confidence, label) pairs for binning. These pairs are not persisted in the JSON output format. The existing ECE/Brier scatter plot (fig02) provides a partial alternative. Persisting calibration pairs is straightforward future work.

---

## 12. Writing Strategy

### Recommended Writing Order

| Phase | Sections | Rationale |
|-------|----------|-----------|
| **1. Methods (Architecture + Experimental Setup)** | §3, §4 | Most concrete, least interpretive. Establishes the framework. Can be written directly from architectural documentation and config files. Builds confidence before tackling contentious sections. |
| **2. Results** | §5 | Factual, evidence-driven. Every sentence maps to a Supported Finding or a table/figure. No interpretation required. This section is "safe" to write second. |
| **3. Discussion** | §6 | Requires Results to exist first. Most intellectually demanding writing — must classify every claim as Observation/Interpretation/Hypothesis and resist overclaiming. Write third, after the evidence is fully organized. |
| **4. Limitations + Threats to Validity** | §7, §8 | Straightforward from Phase 3 documentation. Write fourth. These sections change little during revision. |
| **5. Introduction + Related Work** | §1, §2 | Can be drafted in parallel with earlier sections but should be finalized last. The introduction must accurately preview the results, which are only fully understood after Discussion is written. |
| **6. Conclusion** | §9 | Write last. Summarizes everything. Must contain no new claims. |
| **7. Abstract** | — | Write last. Distillation of the entire paper. Revise repeatedly. |
| **8. Figures + Tables + Captions** | Throughout | Draft captions early (they force precise thinking), but finalize after all sections are written. |
| **9. References** | — | Build incrementally. Verify every citation against the original source before submission. |

### Why This Order

- **Methods first**: Least contentious, most factual. Builds momentum.
- **Results second**: The evidence is frozen; no interpretation disputes can arise.
- **Discussion third**: The hard part. Requires the complete evidence base.
- **Introduction and Abstract last**: Must accurately reflect the final paper content. Writing them too early leads to misalignment.

---

## 13. Common Mistakes to Avoid

### Overclaims

| Statement | Why It Is an Overclaim | Correct Replacement |
|-----------|----------------------|-------------------|
| "CA-MARL outperforms equal-weight and buy-and-hold baselines" | Not supported by statistical tests (p = 0.3246, d = −0.03) | "CA-MARL achieves comparable risk-adjusted returns to equal-weight and buy-and-hold baselines" |
| "Confidence-aware fusion improves portfolio performance" | Equal-weight fusion ablation gives same result | "The fusion mechanism produces valid allocations; whether confidence weighting provides benefit over uniform weighting requires the calibration pipeline to be functional" |
| "The three-agent architecture is necessary for good performance" | Single-run ablation shows modest change; no statistical validation | "The three-agent decomposition is architecturally sound; its necessity has not been empirically established" |
| "CA-MARL generates calibrated confidence scores" | Calibration is identity-mapped | "CA-MARL is designed to produce calibrated confidence scores; at the current walk-forward configuration, the calibration pipeline produces identity mappings" |
| "Our system generalises across markets" | Single market (Indian Nifty 50) | "Our evaluation is limited to the Indian Nifty 50 universe; generalisability to other markets is future work" |
| "The system is ready for deployment" | No transaction costs, limited seeds, calibration non-functional | "The system demonstrates feasibility; production deployment would require addressing the limitations identified in §7" |

### Imprecise Language

| Phrase | Problem | Replace With |
|--------|---------|-------------|
| "Significantly better" | Ambiguous (statistical vs. practical significance) | "Statistically significant" or "practically meaningful" — specify which |
| "Our method outperforms" | Overclaim; lacks qualifier | "Our method achieves a mean Sharpe ratio of X, compared to Y for baseline Z" |
| "As expected" | Assumes reader agrees; can hide surprises | State the expectation separately from the observation |
| "The system learns to allocate" | Anthropomorphises; vague | "The trained policy produces allocations with property X" |
| "Confidence is calibrated" | False (identity mapping) | "The calibration pipeline is designed to calibrate confidence; at the current configuration, it produces identity mappings" |

### Structural Mistakes

| Mistake | Why It Weakens the Paper | Correction |
|---------|-------------------------|------------|
| Hiding the calibration non-function | Reviewer will discover it; trust is lost | State it clearly in Results (§5.6) and discuss in Discussion (§6.2) |
| Claiming outperformance in the Abstract | Sets an expectation the paper cannot meet | Use neutral language: "achieves comparable performance to equal-weight" |
| Delaying the negative finding to Limitations | Appears defensive | Present the finding in Results; explain in Discussion; list in Limitations |
| Over-emphasis on architecture novelty | Ignores the central finding (performance parity); misleads reader about the paper's contribution | Balance: architecture description proportionally sized; central finding is the honest empirical evaluation |
| No statistical tests on key comparisons | Claims appear unsupported | Include permutation test, sign test, effect sizes (all completed in `_final_stats.py`) |

### Reviewer-Trigger Mistakes

| Mistake | Trigger | Prevention |
|---------|---------|------------|
| "20/20 Sharpe ratios positive" (actually 19/20) | Reviewer spots the error | Use exact count: "19 of 20 fold-seed combinations" |
| Claiming MARS comparison without reproduction | Reviewer asks for MARS baseline data | Acknowledge MARS as a stretch goal; compare architecturally only |
| "Calibration improves performance" | Reviewer asks for pre/post calibration comparison | State that calibration is identity-mapped; no comparison exists |
| No confidence value distributions | Reviewer asks what the confidence values actually look like | Acknowledge that confidence values are not persisted; propose this as future work |

---

## Appendix: Evidence Source Index

| Evidence Type | Location | What It Contains |
|---------------|----------|-----------------|
| Campaign JSON | `experiments/results/campaign_v1_seed_*.json` | Per-fold metrics, allocations, baselines, calibration for 5 seeds |
| Ablation JSON | `experiments/results/campaign_v1_ablations_seed_0000.json` | 7 ablation variants, single run |
| Dynamic verification | `experiments/dynamic_verify_log.txt`, `experiments/dynamic_verify_report.txt` | Runtime-instrumented confirmation of 0 calibration pairs |
| Statistical analyses | `experiments/_final_stats.py` | Permutation test, sign test, Kruskal-Wallis, Cohen's d |
| Research report | `experiments/reports/research_report.md` | Full written analysis with interpretations |
| Completion report | `PHASE_3_COMPLETION_REPORT.md` | All supported findings, unsupported claims, limitations |
| Freeze report | `PHASE_3_FREEZE_REPORT.md` | Final frozen findings after corrections |
| Consistency audit | `experiments/_consistency_audit.py` (run output) | Zero discrepancies across all artifacts |
| Figures | `experiments/plots/publication/figures/fig*.pdf` | 4 publication figures (cumulative returns, calibration analysis, ablation bars, regime timeline) |
| Tables | `experiments/plots/publication/tables/table*.tex` | 4 LaTeX tables (summary, per-fold, ablation, calibration) |
| Architecture docs | `docs/architecture/*.md` | Frozen architectural decisions, module specs, ADRs |
| Reproducibility | `experiments/reproducibility_manifest.json` | Locked commit, seeds, parameters, Python version |
