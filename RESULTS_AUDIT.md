# RESULTS_AUDIT.md — Results Section Consistency Audit

**Source:** `manuscript/results.md` — 45 lines, 7 subsections.
**Verification basis:** table01–table04 (LaTeX), fig01–fig04 (PDF), PHASE_3_FREEZE_REPORT.md F1–F9, campaign JSON files (5 seeds), ablation JSON, dynamic verification report.

---

## 1. §5.1 Financial Performance — Audit

### Result 1: Mean Sharpe = 1.885 (95% CI: [1.809, 1.961])

| Question | Answer |
|----------|--------|
| **Supports** | H1 (stable, valid recommendations), H6 (positive risk-adjusted returns) |
| **Contradicts** | H3 (confidence-aware fusion superior to EW — CI upper bound 1.961 < EW mean 1.931, confirming CA-MARL is not superior) |
| **Reviewer challenge** | CI uses normal approximation (1.96 × SE) with n=5 seeds. t-distribution (df=4, t=2.776) gives [1.777, 1.993] — 9% wider. Reviewer may ask why normal approximation was chosen for a 5-observation sample. |
| **Discussion needed** | Yes — justify the CI method; note that the within-seed variance (~1.7) dwarfs the cross-seed variance (0.087), making the cross-seed CI a narrow view of uncertainty. |
| **Hidden issue** | Each seed-mean averages 4 folds with very different Sharps (range 0.161–3.597). The cross-seed CI captures only seed uncertainty, not the much larger fold uncertainty. 5 seeds gives low precision for the cross-seed std estimate (χ²-based 95% CI for σ: [0.045, 0.412]). |

### Result 2: 19/20 fold-seed Sharpe positive; one negative (seed 43, fold 01: −0.089)

| Question | Answer |
|----------|--------|
| **Supports** | H6 (partially — predominantly but not universally positive) |
| **Contradicts** | Any claim that CA-MARL universally produces positive returns |
| **Reviewer challenge** | 1/20 negative at a value very close to zero (−0.089) is consistent with random variation. At α = 0.05, 1 false positive in 20 independent tests is expected. |
| **Discussion needed** | Minor — note that the single negative is small and within expected statistical fluctuation |
| **Hidden issue** | The 20 fold-seed combinations are **not independent** — the same 4 folds appear with 5 different seeds. Seed variation within a fold is small (~0.4 range in fold 01, ~0.6 in fold 03). The true degrees of freedom are closer to 4 (folds) than 20. |

### Result 3: Sortino = 3.327, MaxDD = −6.5%, Vol = 11.5%, CumRet = 9.6%

| Question | Answer |
|----------|--------|
| **Supports** | H1, H6 |
| **Contradicts** | Nothing directly |
| **Reviewer challenge** | "Cumulative return over the test period is 9.6%" — ambiguous. The 9.6% is the **mean per-fold return** (4 non-overlapping 126-day windows averaged across 5 seeds), not the **total portfolio return** over the evaluation period. Total compounded return for seed 42 across 4 sequential test windows is ~38%. A reviewer may be confused about what "cumulative return" means here — is it per-window or total? |
| **Discussion needed** | Yes — clarify that CumRet is the mean per-fold return; the total return over the full 2-year test period is higher |
| **Hidden issue** | The per-fold CumRet values are returns within each 126-day test window. Since test windows are sequential (fold 01 test = 2022-04-12 to 2022-10-13, fold 02 test = 2022-10-14 to 2023-04-19, etc.), the true portfolio growth is the product of (1 + r_i) across folds. Reporting the mean rather than compound figure understates the total return. Both metrics should be reported. |

### Result 4: CA-MARL CumRet 9.6% vs EW 9.5% vs BH 9.5%

| Question | Answer |
|----------|--------|
| **Supports** | H6 (positive returns), H3 (indirect — performances are indistinguishable) |
| **Contradicts** | H3 (superiority) |
| **Reviewer challenge** | CA-MARL CumRet (9.6%) is a **5-seed mean**; EW (9.5%) and BH (9.5%) are **single deterministic values** from seed 42's data. The asymmetric comparison (multi-seed vs. single-seed) could be questioned. |
| **Discussion needed** | Minor — clarify that baselines are deterministic per fold and do not vary with seed |
| **Hidden issue** | The EW and BH baselines are computed from seed 42's `realized_prices` DataFrame, which is deterministic (all seeds use the same price data). So the single-value comparison is valid. But "9.5%" for both EW and BH suggests rounding obscures a real difference (EW = 9.49%, BH = 9.51%). |

---

## 2. §5.2 Walk-Forward Analysis — Audit

### Result 5: Per-fold mean Sharpe — 0.161 (fold 01), 0.756 (fold 02), 3.597 (fold 03), 3.027 (fold 04)

| Question | Answer |
|----------|--------|
| **Supports** | H5 (strong regime effect — fold means span 0.161 to 3.597, a 22× range) |
| **Contradicts** | H3 (indirectly — if fold dominates, then strategy differences are secondary) |
| **Reviewer challenge** | Why is fold 01 so much worse than fold 03? Fold 01 test = 2022-04-12 to 2022-10-13 (start of 2022 bear market); fold 03 test = 2023-04-20 to 2023-10-19 (strong bull recovery). The market regime explains this directly — but this is a Discussion point. |
| **Discussion needed** | Yes — this is the paper's most important quantitative finding. The Discussion must address why folds differ. |
| **Hidden issue** | Fold 01 mean has high variance across seeds: range [−0.089, 0.401] = 0.490. Fold 03 is tighter: [3.330, 3.967] = 0.638 in absolute terms but much smaller relative to the mean (CV 0.638/3.597 = 0.18 vs CV 0.490/0.161 = 3.04). The fold 01 mean (0.161) is unreliable — one different seed could make it negative. |

### Result 6: Kruskal-Wallis H = 17.86, p = 0.00047

| Question | Answer |
|----------|--------|
| **Supports** | H5 — strong evidence |
| **Contradicts** | Any claim of stable cross-fold performance |
| **Reviewer challenge** | With only 4 groups (folds) and n=5 per group, Kruskal-Wallis is appropriate. p = 0.00047 is robust. |
| **Discussion needed** | Yes — this is the core evidence for the regime effect claim |
| **Hidden issue** | None — the statistic and p-value are consistent with the data. |

### Result 7: All pairwise post-hoc Mann-Whitney comparisons significant at p < 0.01

| Question | Answer |
|----------|--------|
| **Supports** | H5 |
| **Contradicts** | Nothing |
| **Reviewer challenge** | **Multiple comparison correction is not mentioned.** With 4 groups, there are 6 pairwise comparisons. Family-wise error rate at α = 0.01 per test: 1 − (0.99)⁶ = 0.058. At α = 0.05: 1 − (0.95)⁶ = 0.265. A reviewer may ask whether Bonferroni or FDR correction was applied. |
| **Discussion needed** | Yes — state whether correction was applied and whether all comparisons survive correction |
| **Hidden issue** | Without correction, some "significant" differences may not survive. With Bonferroni (0.05/6 = 0.0083), p < 0.01 for each comparison is still ≤ 0.0083 for most pairs. But this should be verified. |

---

## 3. §5.3 Statistical Comparison with Baselines — Audit

### Result 8: EW Sharpe = 1.931, BH = 1.916, MVO = −0.288

| Question | Answer |
|----------|--------|
| **Supports** | H3 (indirect — CA-MARL 1.885 is in the same range as EW 1.931 and BH 1.916) |
| **Contradicts** | H3 (superiority claim) |
| **Reviewer challenge** | The baseline numbers are computed from seed 42's data only. A reviewer may ask: are these really deterministic? Yes — walk-forward test windows are fixed regardless of RL seed. But the baseline Sharpe can vary if the `realized_prices` used for portfolio return computation differs across seeds (it does not — prices are frozen). So the single value is valid. |
| **Discussion needed** | No — standard practice |
| **Hidden issue** | MVO at −0.288 is anomalously bad. With a 504-day estimation window and 19 assets, the sample covariance matrix is ill-conditioned. The MVO baseline could be improved with shrinkage — this is a known limitation (L6 in freeze report). The large effect size (d = +1.43) vs MVO is misleadingly flattering. |

### Result 9: Permutation test: mean diff = −0.0455, p = 0.3246

| Question | Answer |
|----------|--------|
| **Supports** | H3 not supported |
| **Contradicts** | Any claim that CA-MARL outperforms EW |
| **Reviewer challenge** | **The 20 paired deltas are not independent — they share 4 EW values.** Each of the 4 EW fold-Sharpes is used 5 times (once per seed within that fold). This reduces the effective information in the EW estimates. The permutation test permutes seed assignments within folds, so it correctly accounts for the fold structure. But a reviewer may ask about this dependence. |
| **Discussion needed** | Yes — briefly note the pairing structure and why the permutation test is appropriate |
| **Hidden issue** | With CA-MARL mean diff = −0.0455 and d = −0.03, the effect is not just non-significant — it is **negative in direction**. EW is slightly better. This is a stronger finding than "no significant difference" — the data suggest EW may actually be marginally better. |

### Result 10: Sign test: 7/20 wins (35%), p = 0.2632

| Question | Answer |
|----------|--------|
| **Supports** | H3 not supported |
| **Contradicts** | H3 |
| **Reviewer challenge** | 7/20 is below chance (50%). This is weak evidence against CA-MARL but consistent with no effect. |
| **Discussion needed** | Minimal |
| **Hidden issue** | Sign test discards magnitude information. The mean delta (−0.0455) and the win count (7/20) tell the same story — EW is slightly better — but neither alone is conclusive. |

### Result 11: Cohen's d vs EW = −0.03, vs MVO = +1.43

| Question | Answer |
|----------|--------|
| **Supports** | H3 not supported (EW), H6 indirectly (vs MVO) |
| **Contradicts** | H3 |
| **Reviewer challenge** | d vs EW (−0.03) is negligible. d vs MVO (+1.43) is large but reflects MVO's pathology, not CA-MARL's merit. A reviewer may note that the MVO comparison is not meaningful given its known weaknesses. |
| **Discussion needed** | Yes — contextualize the MVO comparison as reflecting MVO's known issues with short estimation windows |
| **Hidden issue** | Cohen's d for paired designs should use the standard deviation of the differences, not pooled variance. If the paper uses the standard formula (mean_diff / sd_diff), this is correct. If it uses a pooled formula, it would be wrong. Need to verify `_final_stats.py`. |

### Result 12: Per-fold comparisons (EW vs CA-MARL)

| Question | Answer |
|----------|--------|
| **Supports** | H5 (fold-to-fold variation dominates over strategy) |
| **Contradicts** | H3 |
| **Reviewer challenge** | Comparing CA-MARL **multi-seed means** against EW **single deterministic values** mixes statistics of different types. For fold 01, CA-MARL range is [−0.089, 0.401] — seeds vary substantially. The mean (0.161) vs EW (0.300) suggests EW wins, but seed 46's 0.401 beats EW. |
| **Discussion needed** | Yes — note that per-fold CA-MARL has seed variance; the mean vs EW comparison obscures this |
| **Hidden issue** | The per-fold sentence implies EW wins in 2 folds and is near-identical in 2 folds. But the margins are tiny in folds 02–04 (differences of 0.003, 0.046, 0.001). Only fold 01 shows a material CA-MARL deficit (0.161 vs 0.300, difference = 0.139). The paragraph structure slightly overstates EW's advantage. |

---

## 4. §5.4 Training Stability — Audit

### Result 13: Cross-seed Sharpe std = 0.087

| Question | Answer |
|----------|--------|
| **Supports** | H1 (training stable across random initialisations) |
| **Contradicts** | Any claim that seeds produce qualitatively different results |
| **Reviewer challenge** | 5 seeds is minimal for estimating a standard deviation. |
| **Discussion needed** | Minor — note limited sample |
| **Hidden issue** | The std of seed means (0.087) is computed from 5 values. The χ² 95% CI for the true σ is approximately [0.045, 0.412]. The true cross-seed standard deviation could be as high as 0.412, which would change the interpretation from "very stable" to "moderately variable." |

### Result 14: Seed means: 1.823 (seed 45) to 2.035 (seed 46)

| Question | Answer |
|----------|--------|
| **Supports** | H1, H6 |
| **Contradicts** | Nothing |
| **Reviewer challenge** | Seed 46 (2.035) is 11.6% above the mean (1.885) and 11.6% above the next highest (seed 43 at 1.877). Is seed 46 an outlier? The Grubbs test for a single outlier: G = (2.035 − 1.885) / 0.087 = 1.72. Critical value (α = 0.05, n=5) ≈ 1.715 — borderline. The limited seed count makes outlier detection unreliable. |
| **Discussion needed** | Mention that seed 46 is moderately high but not a statistical outlier with this sample size |
| **Hidden issue** | None substantive |

### Result 15: Per-seed fold std: 1.605 (seed 43) to 1.756 (seed 46)

| Question | Answer |
|----------|--------|
| **Supports** | H5 (fold variation is ~20× seed variation) |
| **Contradicts** | H3 (indirect — fold variation swamps strategy effects) |
| **Reviewer challenge** | None — this is a straightforward descriptive statistic |
| **Discussion needed** | Yes — the fold-to-seed variance ratio is a key quantitative finding for the Discussion |
| **Hidden issue** | The per-seed fold std is computed from only 4 observations (one per fold). With df=3, the estimate is noisy. But the gap is so large (1.7 vs 0.087, ratio ≈ 20) that the qualitative conclusion is robust. |

---

## 5. §5.5 Ablation Analysis — Audit

### Result 16: Ablation Sharpe range: 1.842 (drop allocation) to 2.010 (drop market)

| Question | Answer |
|----------|--------|
| **Supports** | H4 (inconclusive — range width 0.168, all variants cluster tightly) |
| **Contradicts** | H4 (if agents were strongly non-redundant, dropping one would cause a large Sharpe drop) |
| **Reviewer challenge** | **The ablation uses a single 80/20 temporal split, not the walk-forward protocol.** The CA-MARL baseline under this protocol (Sharpe = 1.939) differs from the walk-forward cross-seed mean (1.885). Results may not generalize to the walk-forward setting. The manuscript states this caveat (line 33) — good. |
| **Discussion needed** | Yes — the ablation protocol difference limits comparability with the main results |
| **Hidden issue** | **Drop market agent improves Sharpe (2.010 > 1.939).** This is a striking finding: removing the market analysis agent, which is supposed to provide directional recommendations, actually improves performance. This suggests the market agent's recommendations are counterproductive on net. The Discussion must address this. |

### Result 17: EW fusion (1.951), shuffled (1.952), no calibration (1.939)

| Question | Answer |
|----------|--------|
| **Supports** | H2 (not supported — calibration has no effect), H3 (not supported — confidence weighting does not help) |
| **Contradicts** | Any claim that the confidence pipeline provides measurable benefit |
| **Reviewer challenge** | EW fusion (1.951) and shuffled confidence (1.952) both exceed the baseline (1.939). This is a counterintuitive result — weighting agents uniformly outperforms weighting them by confidence. A reviewer will ask: is the confidence weighting actively harmful? |
| **Discussion needed** | Yes — critical. The fact that uniform weighting and random weighting both equal or exceed the baseline suggests the confidence estimates carry no useful signal. |
| **Hidden issue** | The differences (1.951 vs 1.939 vs 1.952) are all within 0.013 Sharpe units. Without confidence intervals or replication, we cannot tell if these are meaningful differences or noise. The ablation is a single run with no error bars. |

---

## 6. §5.6 Calibration Assessment — Audit

### Result 18: Zero calibration pairs across all 4 folds; identity mapping everywhere

| Question | Answer |
|----------|--------|
| **Supports** | H2 not supported — conclusively |
| **Contradicts** | Any claim that calibration produces non-identity mappings |
| **Reviewer challenge** | This is the paper's most important negative finding. A reviewer will immediately ask: **why**? The Results section correctly does not explain why (that is for Discussion). But a reviewer may be frustrated by the absence of an explanation. |
| **Discussion needed** | **Yes — extensive.** This is the central negative finding that requires explanation in §6.2. The root cause (temporal mismatch between test window dates and the ADR-024 eligibility gate, combined with `_collect_calibration_pairs()` never being called) must be explained. |
| **Hidden issue** | The dynamic verification shows 0 pairs accumulated across all 4 engines. But is the zero always guaranteed, or could it change with different walk-forward parameters? The mismatch is intrinsic to stride = test_window_days = 126. With a larger stride or different window sizing, the test windows might not extend past the next training window end. The identity mapping is a consequence of the configuration, not a fundamental flaw in the calibration pipeline. This nuance matters for the Discussion. |

### Result 19: ECE — market 0.170, risk 0.372, allocation 0.493; Brier — 0.035, 0.143, 0.244

| Question | Answer |
|----------|--------|
| **Supports** | H2 not supported (all agents show substantial miscalibration) |
| **Contradicts** | Any claim that the system produces well-calibrated confidence |
| **Reviewer challenge** | The allocation agent ECE (0.493) is close to the theoretical maximum of 0.5 for binary outcomes with Platt scaling. This is essentially random-level calibration. The market agent (0.170) is substantially better. Why are the agents so different? |
| **Discussion needed** | Yes — the agent-level differences in calibration quality need Discussion. Possible explanation: the market agent's categorical output (BUY/SELL/HOLD) maps more naturally to binary correctness labels than the allocation agent's continuous weight vector. |
| **Hidden issue** | These ECE/Brier values are computed on **identity-mapped raw confidence**. We have no information on what post-calibration values would be. The fact that the market agent starts with relatively good calibration (ECE = 0.170) while the allocation agent starts near-random (ECE = 0.493) is itself an interesting finding about the relative quality of the raw confidence signals by agent type. |

---

## 7. §5.7 Verification of Allocation Validity — Audit

### Result 20: fallback_used = false in all 20 fold-seed combinations

| Question | Answer |
|----------|--------|
| **Supports** | H1 (agents produce valid, usable outputs) |
| **Contradicts** | Nothing |
| **Reviewer challenge** | "Valid" here means structural validity (no NaN, non-negative weights, sum ≈ 1.0). This does not mean the allocations are economically sensible. A reviewer may ask for a stronger validity check. |
| **Discussion needed** | Minimal — the finding is clear and non-controversial |
| **Hidden issue** | The `fallback_used` flag covers three cases: (1) agent produces NaN/Inf output, (2) fusion sum of confidences is zero, (3) risk management layer detects constraint violation. That all 20 pass is a basic sanity check, not a substantive result. The space devoted to this finding (§5.7 is a full paragraph) may be disproportionate to its scientific weight. |

---

## 8. Cross-Cutting Issues

### 8.1 CumRet ambiguity

The term "cumulative return" is used ambiguously. In §5.1, it is the mean per-fold return (n=20 fold-seed combinations, mean = 9.55%). But the total portfolio return across the full evaluation period (4 sequential test windows) would be the compounded product, which is substantially higher (~38% for seed 42). A reader unfamiliar with the walk-forward structure may interpret 9.6% as the total return and underestimate the system's raw return generation. **Every use of "cumulative return" should specify "per-fold" or "total across folds."**

### 8.2 Asymmetric CA-MARL vs baseline comparison

CA-MARL metrics are reported as multi-seed means ± CI. Baseline metrics (EW, BH, MVO) are reported as single deterministic values from seed 42. This asymmetry is valid (baselines are seed-independent) but should be explicitly noted to prevent a reviewer from questioning it.

### 8.3 Per-fold paragraph in §5.3

The sentence comparing per-fold means mixes multi-seed CA-MARL means with single deterministic EW values. The margins are tiny in folds 02–04 (differences of 0.003–0.046 Sharpe units). Only fold 01 shows a material difference (0.139). The paragraph structure implies a more systematic EW advantage than the data support.

### 8.4 Ablation methodology

The greatest threat to the ablation results' credibility is the single 80/20 split protocol. The CA-MARL baseline Sharpe under this protocol (1.939) differs from the walk-forward protocol (1.885). If the protocol change shifts the baseline by 0.054, the ablation deltas (max change: −0.058 to +0.071) are within the protocol-induced noise. **The ablation conclusions should be treated as illustrative, not conclusive.**

### 8.5 Drop-market-agent improves performance

The finding that removing the market agent improves Sharpe (2.010 vs 1.939 baseline) demands Discussion. Possible explanations: (1) the market agent's categorical BUY/SELL/HOLD signals, once transformed to weight proposals, add noise rather than signal; (2) the 2020–2024 bull market made directional bets unnecessary; (3) the single-split ablation may not generalize.

### 8.6 Confidence weighting is non-beneficial

Equal-weight fusion (1.951) and shuffled confidence (1.952) matching or exceeding the confidence-weighted baseline (1.939) is a direct challenge to the value of confidence-aware fusion. This is not just "calibration doesn't work" — it's "confidence weighting provides no benefit even when calibration is in the picture." The Discussion must address this honestly.

### 8.7 Post-hoc correction for pairwise comparisons

The §5.2 claim that all 6 pairwise Mann-Whitney comparisons are significant at p < 0.01 should note whether multiple comparison correction was applied. Without correction, the family-wise error rate for 6 tests at α = 0.01 is 5.8%.

---

## 9. Summary of Required Discussion Items

| # | Issue | Section to Address | Priority |
|---|-------|-------------------|----------|
| 1 | Why zero calibration pairs (temporal mismatch, _collect_calibration_pairs never called) | §6.2 | Critical |
| 2 | Market regime as dominant performance factor (fold variation vs strategy variation) | §6.1 | Critical |
| 3 | CA-MARL does not outperform EW (p = 0.3246, d = −0.03) | §6.1 | Critical |
| 4 | Drop-market-agent improves Sharpe — market agent may be counterproductive | §6.3 | High |
| 5 | Confidence weighting not beneficial (EW fusion and shuffled both match/exceed baseline) | §6.1 | High |
| 6 | CumRet ambiguity — clarify per-fold vs total across folds | §5.1 revision | Medium |
| 7 | Ablation protocol limits (single 80/20 split, not walk-forward) | §6.3 | Medium |
| 8 | MVO weakness (short estimation window, ill-conditioned covariance) | §6.3 | Medium |
| 9 | Post-hoc correction for pairwise Mann-Whitney comparisons | §5.2 revision | Medium |
| 10 | Agent-level calibration quality differences (why is allocation so much worse?) | §6.2 | Low |
| 11 | CI method choice (normal vs t-distribution with n=5) | §5.1 revision | Low |
| 12 | Seed 46 as potential mild outlier | §5.4 revision | Low |
