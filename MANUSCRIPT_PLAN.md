# MANUSCRIPT_PLAN.md — CA-MARL Paper Writing Execution Plan

> **Status:** Phase 4 — Scientific Analysis
> **Repository State:** Frozen (commit `ba81e82`, tag `v2.0-phase3-complete`)
> **Preceding Document:** `PAPER_BLUEPRINT.md` (authoritative scientific narrative)
> **Purpose:** Project management guide for manuscript writing. Answers what, in what order, with what evidence, and how to verify completion.
> **Scope:** Writing only. No implementation, experimentation, or architectural changes.

---

## 1. Manuscript Overview

### Purpose

This paper communicates the design, implementation, and honest empirical evaluation of CA-MARL — a Confidence-Aware Multi-Agent Reinforcement Learning framework for portfolio allocation. The core contribution is the architecture itself: three specialized PPO-trained RL agents whose recommendations are fused via a deterministic confidence-weighted formula, with an explicit confidence estimation and calibration pipeline. The experimental campaign (5 seeds, 4 walk-forward folds, 19 Indian large-cap equities, 2020–2024) evaluates both financial performance and calibration quality.

### Target Audience

- Academic researchers in quantitative finance, reinforcement learning, and multi-agent systems.
- Reviewers at ML/finance venues who evaluate reproducibility and honest reporting as highly as positive results.
- Practitioners building transparent decision-support systems for portfolio management.

### Research Contribution

The paper makes four contributions:
1. **Architecture**: A complete, modular pipeline for confidence-aware multi-agent portfolio RL.
2. **Empirical evaluation**: 5-seed, 4-fold walk-forward results showing CA-MARL achieves a mean Sharpe ratio of 1.885 (95% CI: [1.809, 1.961]) — comparable to equal-weight but not statistically distinguishable from it (permutation p = 0.3246).
3. **Honest negative finding**: The calibration pipeline produces identity mappings at the current walk-forward configuration due to a temporal mismatch between the test window and the ADR-024 eligibility gate.
4. **Reproducible methodology**: Frozen dataset, versioned results, 47-pass verification suite, dynamic instrumentation, full reproducibility manifest.

### Expected Take-Away

A well-constructed multi-agent portfolio RL system can produce valid, stable allocations that match simple diversification, but confidence calibration requires careful alignment with the walk-forward schedule. The regime effect (Kruskal-Wallis p = 0.00047) dominates performance variation more than strategy choice during bull markets. Transparent reporting of both positive and negative findings is essential for scientific progress in this field.

---

## 2. Target Venue

### Recommendation: Workshop Paper + Extended Journal Submission Track

**Rationale:** The completed work does not claim state-of-the-art performance (CA-MARL matches but does not exceed equal-weight). This makes the paper unsuitable for main-track NeurIPS/ICML/AAAI, where competitiveness is typically expected. However, the work has genuine scientific value:

1. **Reproducibility infrastructure** is unusually rigorous for the field.
2. **Honest negative findings** (calibration non-function, performance parity with equal-weight) are rare and valuable.
3. **The framework itself is novel in architectural terms** (explicit calibrated confidence layer in a portfolio RL context).

### Primary Target: Workshop

**Best fit:** Workshops at NeurIPS, ICML, or AAAI that accept reproducibility papers, negative results, or finance + ML submissions.

Examples:
- **NeurIPS Workshop on Financial AI** — directly aligned; values both methodology and honest evaluation.
- **ICML Workshop on Reproducibility** — the reproducibility infrastructure is a standout contribution.
- **AAAI Workshop on AI in Finance** — accepts negative results; emphasises transparency.

### Secondary Target: Journal

**Best fit:** *Journal of Financial Data Science* or *Quantitative Finance*.

These venues accept methodological contributions without requiring state-of-the-art performance. The reproducible framework and honest empirical evaluation are valued. A journal version would require:
- Extended ablation studies across walk-forward folds (not just single split).
- Additional statistical testing.
- Literature review expansion.

### What Does NOT Fit

| Venue | Why Not |
|-------|---------|
| NeurIPS/ICML/AAAI main track | Performance parity with equal-weight is insufficient for acceptance |
| ICLR | Requires architectural novelty exceeding the current contribution |
| JMLR | Requires theoretical contributions beyond the current scope |
| KDD Applied Data Science | Requires demonstrated deployment or real-world impact |

### Format Length

- Workshop paper: 4–8 pages (excluding references and appendix).
- Journal paper: 15–25 pages.
- Undergraduate thesis: 25–40 pages.

### Recommendation

**Write a workshop paper first (4–8 pages)** targeting a finance + ML workshop. This format is proportionate to the scope of completed work. If accepted, the workshop version builds reputation for an extended journal version. The manuscript plan below assumes workshop format. Where journal/thesis versions differ, notes are provided.

---

## 3. Complete Manuscript Structure

### 3.1 Abstract

| Field | Detail |
|-------|--------|
| **Purpose** | Four-sentence summary: (1) problem, (2) method, (3) key result, (4) limitation + conclusion |
| **Target length** | 150–200 words |
| **Dependencies** | Must be written last. Depends on all other sections. |
| **Completion criteria** | Accurately reflects all sections without overclaiming. Contains every element of the central narrative (PAPER_BLUEPRINT.md §6). No claim without evidence elsewhere in the paper. |

### 3.2 Introduction

| Field | Detail |
|-------|--------|
| **Purpose** | Motivate the problem, state the gap, state research questions, preview contributions |
| **Target length** | Workshop: ~500 words (3 paragraphs). Journal: ~1000 words (5 paragraphs) |
| **Dependencies** | Requires Results and Discussion to be complete (preview must match actual findings) |
| **Completion criteria** | States exactly 4 contributions (PAPER_BLUEPRINT.md §5). Uses neutral language ("comparable to equal-weight", not "outperforms"). Mentions calibration negative finding. |

### 3.3 Related Work

| Field | Detail |
|-------|--------|
| **Purpose** | Position CA-MARL relative to DRL portfolio management, multi-agent RL, and calibration literature |
| **Target length** | Workshop: ~500 words. Journal: ~1500 words |
| **Dependencies** | Methods section must be clear enough to compare with prior work |
| **Completion criteria** | Covers DeepTrader, MARS, calibration literature (Guo et al., Naeini et al.), FinRL ecosystem. States explicitly why CA-MARL differs from each. |

### 3.4 Methodology

| Field | Detail |
|-------|--------|
| **Purpose** | Describe the CA-MARL pipeline in sufficient detail for reproduction |
| **Target length** | Workshop: ~1500 words. Journal: ~3000 words |
| **Dependencies** | None (can be written from architecture docs) |
| **Completion criteria** | All 7 modules described. Fusion formula stated mathematically. Calibration leakage rule stated. Figure reference to fig04 (regime timeline). |

### 3.5 Experimental Setup

| Field | Detail |
|-------|--------|
| **Purpose** | Describe dataset, walk-forward, baselines, training, metrics, statistical methodology |
| **Target length** | Workshop: ~800 words. Journal: ~1500 words |
| **Dependencies** | Methodology must be written first (setup refers to method components) |
| **Completion criteria** | Dataset frozen and versioned. Walk-forward parameters stated. All 4 baselines listed. All 4 ablation studies listed. Statistical tests enumerated. |

### 3.6 Results

| Field | Detail |
|-------|--------|
| **Purpose** | Present experimental findings — Observations only, no interpretation |
| **Target length** | Workshop: ~1200 words. Journal: ~2500 words |
| **Dependencies** | Experimental setup must be written. All figures and tables must exist. |
| **Completion criteria** | Every claim maps to PAPER_BLUEPRINT.md §10 (Claims Matrix) or is removed. One unsupported claim = fail. All figures referenced. All tables referenced. Statistical test results reported. |

### 3.7 Discussion

| Field | Detail |
|-------|--------|
| **Purpose** | Interpret results. Classify every claim as Observation, Interpretation, Hypothesis, or Future Work. |
| **Target length** | Workshop: ~1000 words. Journal: ~2000 words |
| **Dependencies** | Results section must be complete. |
| **Completion criteria** | No mixing of Observation and Interpretation. Calibration negative finding addressed transparently. No overclaims. |

### 3.8 Limitations

| Field | Detail |
|-------|--------|
| **Purpose** | Transparently acknowledge limitations with concrete basis in evidence |
| **Target length** | Workshop: ~300 words. Journal: ~500 words |
| **Dependencies** | Results and Discussion must be complete (limitations derive from findings) |
| **Completion criteria** | All 7 limitations from PAPER_BLUEPRINT.md §7 listed. Each limitation cites specific evidence. |

### 3.9 Threats to Validity

| Field | Detail |
|-------|--------|
| **Purpose** | Address internal, external, construct, and statistical validity |
| **Target length** | Workshop: ~200 words. Journal: ~400 words |
| **Dependencies** | Limitations section written (overlaps partially) |
| **Completion criteria** | Four validity categories addressed. Each cites specific experimental constraints. |

### 3.10 Conclusion

| Field | Detail |
|-------|--------|
| **Purpose** | Summarize contributions, honest assessment, future work |
| **Target length** | Workshop: ~200 words. Journal: ~400 words |
| **Dependencies** | Every other section must be complete |
| **Completion criteria** | No new claims. No overclaims. At least 3 future work items. References back to contributions list. |

### 3.11 References

| Field | Detail |
|-------|--------|
| **Purpose** | Complete bibliography of all cited works |
| **Target length** | 25–35 entries (workshop), 35–50 entries (journal) |
| **Dependencies** | Every section must be finalized (no new citations can appear later) |
| **Completion criteria** | Every citation appears in the text. Every text citation has an entry. All citations verified against original sources. |

### 3.12 Appendix (Optional)

| Field | Detail |
|-------|--------|
| **Purpose** | Supplementary material: full per-fold table, dynamic verification details, dataset details |
| **Target length** | 1–3 pages |
| **Dependencies** | Will be written concurrently with Results and Experimental Setup |
| **Completion criteria** | Only material that would disrupt the main text's flow. Not required for submission unless the venue expects it. |

---

## 4. Writing Order

### Why the Writing Order Differs from the Reading Order

The reading order (Abstract → Introduction → ... → Conclusion) is optimized for the reader's comprehension. The writing order is optimized for the writer's efficiency. The key principle is: **write what is most concrete and least interpretive first, so that by the time you reach interpretive sections, the evidence is fully organized and cannot be misrepresented.**

### Recommended Writing Sequence

```
Phase 1: Foundation (Days 1–3)
┌─────────────────────────────────────────────────────────┐
│  1. Methodology (§3.4)                                   │
│  2. Experimental Setup (§3.5)                            │
└─────────────────────────────────────────────────────────┘
Rationale: These sections are directly derivable from
architectural documentation and config files. No
interpretation required. Builds confidence.

Phase 2: Evidence (Days 4–7)
┌─────────────────────────────────────────────────────────┐
│  3. Results (§3.6)                                       │
│  4. Related Work (§3.3)                                  │
│  5. Appendix (§3.12, if used)                            │
└─────────────────────────────────────────────────────────┘
Rationale: Results are factual, evidence-driven. Every
sentence maps to a finding in PAPER_BLUEPRINT.md §10.
Related Work can be drafted in parallel using literature
notes. Appendix supports Results.

Phase 3: Interpretation (Days 8–11)
┌─────────────────────────────────────────────────────────┐
│  6. Discussion (§3.7)                                    │
│  7. Limitations (§3.8)                                   │
│  8. Threats to Validity (§3.9)                           │
└─────────────────────────────────────────────────────────┘
Rationale: Requires complete Results. Hardest writing.
Must resist overclaiming. Each paragraph classified as
Observation/Interpretation/Hypothesis.

Phase 4: Framing and Polish (Days 12–15)
┌─────────────────────────────────────────────────────────┐
│  9. Introduction (§3.2)                                  │
│ 10. Conclusion (§3.10)                                   │
│ 11. Abstract (§3.1)                                      │
│ 12. References (§3.11)                                   │
│ 13. Full consistency pass                                │
└─────────────────────────────────────────────────────────┘
Rationale: Introduction must accurately preview results.
Conclusion must summarize them. Abstract is the last thing
written — it is the distillation of the entire paper.
References verified in a single pass at the end.
```

### Parallelization Opportunities

- **Methodology and Experimental Setup** can be written in parallel (two authors).
- **Related Work** can be written in parallel with Results (different author, provided they coordinate on terminology).
- **All figure/table captions** should be drafted alongside Results (§3.6), not left until the end.

### What Must Be Sequential

- Discussion → depends on complete Results.
- Introduction → depends on complete Discussion.
- Conclusion → depends on complete Discussion.
- Abstract → depends on every other section.

---

## 5. Evidence Map

### Section-to-Evidence Mapping

| Section | Figures | Tables | Statistical Analyses | Experimental Findings | Equations | Repository Artifacts |
|---------|---------|--------|---------------------|---------------------|-----------|---------------------|
| **Abstract** | — | — | — | F1, F6, F7, F8 (PHASE_3_FREEZE §3.1) | — | — |
| **Introduction** | — | — | — | — | — | ARCHITECTURE.md, RESEARCH_MAPPING.md |
| **Related Work** | — | — | — | — | — | RESEARCH_MAPPING.md citations |
| **§3.4 Methodology** | fig04 | — | — | — | Fusion formula (§3.1 in MODULE_SPECS); confidence aggregation | ARCHITECTURE.md, MODULE_SPECIFICATIONS.md, CONFIDENCE_FUSION.md, AGENTS.md, DECISIONS.md (ADR-014/020/022/024) |
| **§3.5 Experimental Setup** | — | table01 (abbreviated), table04 | Permutation test (method stated), Kruskal-Wallis (method stated) | — | Sharpe ratio formula | _config.py, _final_stats.py, EXPERIMENT_PLAN.md |
| **§3.6 Results** | fig01, fig02, fig03 | table01, table02, table03, table04 | Permutation p = 0.3246, Sign test p = 0.2632, Kruskal-Wallis p = 0.00047, Cohen's d = −0.03 | F1, F2, F3, F4, F5, F6, F7, F8, F9 (PHASE_3_FREEZE §3.1) | — | campaign_v1_seed_*.json, campaign_v1_ablations_*.json, dynamic_verify_report.txt |
| **§3.7 Discussion** | fig01, fig02, fig03 | table01, table02, table03, table04 | Same as §3.6 (interpreted) | F1–F9 | — | Dynamic verification report, PHASE_3_COMPLETION_REPORT.md |
| **§3.8 Limitations** | — | — | — | L1–L7 (PHASE_3_COMPLETION §2.C) | — | PHASE_3_COMPLETION_REPORT.md §2.C |
| **§3.9 Threats to Validity** | — | — | — | L1–L7 (grouped by validity type) | — | PHASE_3_COMPLETION_REPORT.md §8 |
| **§3.10 Conclusion** | — | — | — | F1, F6, F8 (recapped) | — | — |
| **Appendix** | Extended per-fold plots | Extended table02 | Full per-fold stats | — | — | All seed JSON files, _dynamic_verify.py |

### Evidence Classification Legend

- **F1–F9**: Supported Findings (PHASE_3_FREEZE_REPORT.md §3.1)
- **L1–L7**: Limitations (PHASE_3_COMPLETION_REPORT.md §2.C)
- **I1–I4**: Interpretations (PHASE_3_COMPLETION_REPORT.md §2.B)
- **C1–C11**: Claims Matrix (PAPER_BLUEPRINT.md §10)

---

## 6. Citation Plan

### Classification System

| Type | Meaning | Example |
|------|---------|---------|
| **[B]** | Background — provides context the reader needs | "Portfolio optimization dates to Markowitz (1952)..." |
| **[M]** | Method — describes a technique we build on | "We train agents using PPO (Schulman et al., 2017)..." |
| **[C]** | Comparison — prior work with which we compare | "MARS (Chen et al., 2026) uses a meta-controller..." |
| **[S]** | Supporting Evidence — justifies a design choice | "The 1/N puzzle (DeMiguel et al., 2009) suggests..." |
| **[D]** | Discussion — supports an interpretive claim | "Deep ensembles (Lakshminarayanan et al., 2017) offer..." |
| **[F]** | Future Work — points to an extension | "Bayesian uncertainty methods (Hoel et al., 2020) could..." |

### Citation Table

| Section | Citation | Type | Purpose |
|---------|----------|------|---------|
| **Introduction** | Markowitz (1952) | [B] | Origin of portfolio optimization |
| | Wang et al. (2021) — DeepTrader | [B][C] | Prior DRL portfolio work |
| | Chen et al. (2026) — MARS | [B][C] | Closest prior art |
| | Guo et al. (2017) | [B] | Calibration motivation |
| **Related Work** | Wang et al. (2021) — DeepTrader | [C] | Main DRL baseline |
| | Chen et al. (2026) — MARS | [C] | Multi-agent comparison |
| | DeMiguel et al. (2009) | [S] | 1/N puzzle |
| | Schulman et al. (2017) — PPO | [M] | Training algorithm |
| | Jacobs et al. (1991); Jordan & Jacobs (1994) | [M] | MoE gating theory |
| | Guo et al. (2017); Naeini et al. (2015) | [M] | Calibration methodology |
| | Lakshminarayanan et al. (2017) | [D][F] | Deep ensembles |
| | Hoel et al. (2020) | [F] | RL uncertainty |
| | FinRL (Liu et al., 2020) | [M] | Implementation ecosystem |
| **Methodology** | Schulman et al. (2017) — PPO | [M] | Agent training |
| | Guo et al. (2017) | [M] | ECE, reliability diagrams |
| | Platt (1999) | [M] | Platt scaling |
| | ADR-020 (DECISIONS.md) | [M] | Fusion formula design |
| | ADR-024 (DECISIONS.md) | [M] | Leakage rule |
| **Results** | DeMiguel et al. (2009) | [S][D] | Context: 1/N puzzle |
| **Discussion** | DeMiguel et al. (2009) | [S][D] | 1/N puzzle interpretation |
| | Guo et al. (2017) | [D] | Calibration failure analysis |
| | Lakshminarayanan et al. (2017) | [D][F] | Alternative confidence methods |
| **Limitations** | (Design decisions — no citations typically needed) | | |
| **Future Work** | Hoel et al. (2020) | [F] | Bayesian RL uncertainty |
| | Lakshminarayanan et al. (2017) | [F] | Deep ensembles |
| | LCL, others | [F] | Transaction cost models |

### Minimum Citation Checklist

These are the minimum citations for a submission-ready paper:

1. [✓] Markowitz (1952) — portfolio optimization foundation
2. [✓] Schulman et al. (2017) — PPO
3. [✓] Wang et al. (2021) — DeepTrader
4. [✓] Chen et al. (2026) — MARS
5. [✓] Guo et al. (2017) — calibration
6. [✓] Naeini et al. (2015) — calibration
7. [✓] DeMiguel et al. (2009) — 1/N puzzle
8. [✓] Jacobs et al. (1991) — MoE
9. [✓] Jordan & Jacobs (1994) — MoE
10. [✓] Platt (1999) — Platt scaling
11. [Optional] Lakshminarayanan et al. (2017) — deep ensembles
12. [Optional] Hoel et al. (2020) — RL uncertainty

---

## 7. Consistency Rules

### 7.1 System Name

| Rule | Value |
|------|-------|
| **Full name** | Confidence-Aware Multi-Agent Reinforcement Learning |
| **Abbreviation** | CA-MARL |
| **Usage** | "CA-MARL" after first use of full name. Never "CA-MARL framework" (redundant). Never "our system" (vague). |
| **Not acceptable** | "CA-MARL algorithm" (it is a framework/pipeline, not a single algorithm). "CA-MARL model". |

### 7.2 Agent Names

| Canonical Name | Acceptable Short Form | Not Acceptable |
|----------------|----------------------|----------------|
| Market Analysis Agent | market agent | "market predictor", "market model" |
| Risk Assessment Agent | risk agent | "risk estimator", "risk model" |
| Portfolio Allocation Agent | allocation agent | "allocation model", "allocator" |

- Agent names are capitalized in section headings, lowercased within running text.
- Always use "market agent", not "Market Agent" (inconsistent capitalization).

### 7.3 Module and Component Names

| Canonical Name | Not Acceptable |
|----------------|----------------|
| Confidence Estimation and Calibration module | "Confidence Engine" (retired per ADR-026) |
| Confidence-Aware Decision Fusion module | "PPO Coordinator" (retired per ADR-015) |
| Risk Management Layer | "risk layer", "risk manager" |
| Outcome Label Generator | "label generator" (acceptable only after first full use) |
| Final Portfolio Recommendation | "final recommendation" (acceptable; `FinalRecommendation` is class name) |

### 7.4 Metric Notation

| Metric | Symbol | Unit/Range |
|--------|--------|------------|
| Sharpe ratio | \( S \) or Sharpe | Dimensionless (annualized) |
| Sortino ratio | \( S_o \) or Sortino | Dimensionless (annualized) |
| Maximum drawdown | MDD or MaxDD | Decimal (e.g., −0.065) |
| Volatility | \( \sigma \) | Decimal (e.g., 0.115) |
| Cumulative return | \( R_{cum} \) or CumRet | Decimal (e.g., 0.096) |
| Expected Calibration Error | ECE | [0, 1] |
| Brier score | Brier | [0, 1] |

- All metrics reported as decimals, not percentages (except where percentage is clearer, e.g., "9.6% return"). When percentages are used, label explicitly.

### 7.5 Mathematical Symbols

| Symbol | Meaning | Defined In |
|--------|---------|------------|
| \( c_i \) | Calibrated confidence for agent \( i \) | §3.4 (Methodology) |
| \( \hat{c}_i \) | Raw (uncalibrated) confidence for agent \( i \) | §3.4 |
| \( \mathbf{w}_i \) | AssetWeightProposal from agent \( i \) | §3.4 |
| \( \mathbf{w}^* \) | Final fused allocation vector | §3.4 |
| \( N \) | Number of assets (19) | §3.5 |
| \( K \) | Number of walk-forward folds (4) | §3.5 |
| \( T \) | Training window length (504 trading days) | §3.5 |
| \( V \) | Validation window length (63 trading days) | §3.5 |
| \( H \) | Test window length (126 trading days) | §3.5 |
| \( t_{horizon} \) | Label horizon (5 trading days) | §3.4 |

### 7.6 Dataset Naming

| Term | Standard |
|------|----------|
| Dataset | "Nifty 50 constituent stocks" or "19 Indian large-cap equities (Nifty 50 constituents)" |
| Period | "January 2020 to June 2024" (not "2020-2024") |
| Frequency | "Daily" (not "1-day") |
| Ticker format | Use exchange suffix only in code; in prose, use plain names (e.g., "Reliance Industries") or plain tickers (e.g., "RELIANCE") |

### 7.7 Experimental Terminology

| Term | Standard |
|------|----------|
| Walk-forward folds | "Fold 1", "Fold 2", "Fold 3", "Fold 4" (not "fold 01") |
| Seeds | "Seeds 42 through 46" (not "seeds 42–46" without introducing the range) |
| Ablations | "equal-weight fusion", "no calibration", "shuffled confidence", "drop-market agent", "drop-risk agent", "drop-allocation agent" |
| Baselines | "equal-weight (1/N)", "buy-and-hold", "static mean-variance optimization (MVO)" |

### 7.8 Confidence Terminology

| Term | Meaning |
|------|---------|
| Raw confidence | Pre-calibration confidence (combined from historical accuracy, reward stability, prediction consistency) |
| Calibrated confidence | Post-calibration confidence (after Platt scaling) |
| Identity mapping | calibrated_confidence = raw_confidence (happens when `fit_calibration` receives no pairs) |
| Miscalibration | Discrepancy between confidence and empirical accuracy (measured by ECE and Brier) |

### 7.9 General Prose Rules

| Rule | Example |
|------|---------|
| "We" for authors (active voice preferred) | "We evaluate CA-MARL on 19 Indian equities..." |
| Present tense for enduring truths | "CA-MARL decomposes the allocation decision..." |
| Past tense for specific experiments | "CA-MARL achieved a mean Sharpe ratio of 1.885..." |
| Never use "our method" | Use "CA-MARL" |
| Never use "state-of-the-art" | Not supported by evidence |
| Never use "significantly" without statistical test reporting | Use "statistically significant (p < 0.05)" or eliminate |

---

## 8. Section Checklists

### 8.1 Abstract Checklist

- [ ] Four-sentence structure: (1) problem, (2) method, (3) key result, (4) limitation + conclusion
- [ ] No numerical claims that lack support in the main text
- [ ] Sharpe ratio mentioned with 95% CI
- [ ] "Comparable to equal-weight" not "outperforms"
- [ ] Calibration negative finding mentioned or at minimum implied
- [ ] Length: 150–200 words
- [ ] No citations
- [ ] No undefined abbreviations (CA-MARL is defined)

### 8.2 Introduction Checklist

- [ ] States the problem (portfolio allocation under uncertainty; need for transparent confidence)
- [ ] States the research gap (no existing portfolio RL system provides calibrated confidence)
- [ ] States the primary research question (RQ1 from PAPER_BLUEPRINT.md §3)
- [ ] Lists exactly 4 contributions (PAPER_BLUEPRINT.md §5)
- [ ] No overclaims (checked against PAPER_BLUEPRINT.md §10 "Unsupported Claims" table)
- [ ] All contributions verifiable from the main text
- [ ] Length: ~500 words (workshop)

### 8.3 Related Work Checklist

- [ ] Covers DRL for portfolio management (DeepTrader, MARS, MAPS)
- [ ] Covers calibration literature (Guo et al., Naeini et al., Platt scaling)
- [ ] States explicitly why CA-MARL differs from MARS (explicit calibrated confidence vs. implicit meta-controller)
- [ ] No comparative performance claims against unreproduced baselines (MARS is compared architecturally only)
- [ ] Bibliography of all prior works matches References section
- [ ] Length: ~500 words (workshop)

### 8.4 Methodology Checklist

- [ ] Seven modules described in order (Data → Features → Agents → Confidence → Fusion → Risk → Evaluation)
- [ ] The three agents are identified as RL agents trained via PPO
- [ ] The fusion formula is stated mathematically and defined in prose
- [ ] The calibration leakage rule (ADR-024) is stated
- [ ] The Outcome Label Generator is described with the outcome label table
- [ ] The raw confidence formula (3 inputs: historical accuracy, reward stability, prediction consistency) is explained
- [ ] No mention of "PPO Coordinator" (retired per ADR-015)
- [ ] Cross-reference to Confidence-Aware Decision Fusion as primary contribution
- [ ] Architecture diagram or pipeline description is clear enough for independent reproduction
- [ ] Length: ~1500 words (workshop)

### 8.5 Experimental Setup Checklist

- [ ] Dataset described: 19 Nifty 50 constituents, 2020-01-01 to 2024-06-27, 1111 trading days
- [ ] Walk-forward parameters: 4 folds, training_window=504, validation_window=63, test_window=126, stride=126
- [ ] PPO hyperparameters: lr=3e-4, n_steps=128, batch_size=32, total_timesteps=5000
- [ ] Confidence parameters: Platt scaling, hist_weight=0.4, reward_stability_weight=0.3, pred_consistency_weight=0.3
- [ ] All 4 baselines listed: equal-weight (1/N), buy-and-hold, static MVO
- [ ] All 4 ablation types listed: equal-weight fusion, no calibration, shuffled confidence, drop-one-agent
- [ ] Metrics listed: Sharpe, Sortino, MaxDD, Volatility, CumRet, ECE, Brier
- [ ] Statistical methodology described: 5 seeds, paired permutation test, sign test, Kruskal-Wallis, Cohen's d
- [ ] No evaluation claims that contradict Limitations section
- [ ] Length: ~800 words (workshop)

### 8.6 Results Checklist

- [ ] Every paragraph classified as Observation (no Interpretation)
- [ ] Every numerical claim traceable to PAPER_BLUEPRINT.md §10 Claims Matrix
- [ ] All figures referenced in order (fig01 → fig02 → fig03)
- [ ] All tables referenced in order (table01 → table02 → table03 → table04)
- [ ] Statistical test results reported with exact p-values
- [ ] Calibration non-function reported transparently in §5.6
- [ ] "19/20" not "all" — the one negative Sharpe (seed 43, fold 01) is mentioned
- [ ] No claim from the "Unsupported Claims" table (PAPER_BLUEPRINT.md §10) appears
- [ ] Permutation test, sign test, Kruskal-Wallis results all present
- [ ] Cross-seed standard deviation of Sharpe (0.087) reported
- [ ] Length: ~1200 words (workshop)

### 8.7 Discussion Checklist

- [ ] Every paragraph categorized as Observation, Interpretation, Hypothesis, or Future Work (stated or clearly implicit)
- [ ] Calibration negative finding addressed with explanation (temporal mismatch + unused `_collect_calibration_pairs`)
- [ ] Equal-weight parity interpreted (not justified away)
- [ ] Regime effect interpreted as the dominant factor
- [ ] No overclaims (checked against PAPER_BLUEPRINT.md §10 Unsupported Claims)
- [ ] Impact of calibration non-function on results explicitly stated (identity mapping → ECE reflects raw miscalibration)
- [ ] Length: ~1000 words (workshop)

### 8.8 Limitations Checklist

- [ ] All 7 limitations listed (PAPER_BLUEPRINT.md §7)
- [ ] Each limitation cites specific evidence (not generic statements)
- [ ] No limitation is "we could have done better" — each is a genuine constraint
- [ ] Calibration non-function listed as the first limitation
- [ ] Length: ~300 words (workshop)

### 8.9 Threats to Validity Checklist

- [ ] Internal validity addressed (calibration non-function's impact on claims)
- [ ] External validity addressed (single market, single period)
- [ ] Construct validity addressed (Sharpe ratio limitations)
- [ ] Statistical validity addressed (5 seeds, wide CIs)
- [ ] No overlap with Limitations that contradicts or repeats exactly
- [ ] Length: ~200 words (workshop)

### 8.10 Conclusion Checklist

- [ ] No new claims
- [ ] Recaps contributions accurately (PAPER_BLUEPRINT.md §5)
- [ ] Restates the honest assessment (comparable to equal-weight, not superior)
- [ ] Mentions calibration finding
- [ ] Lists at least 3 future work items
- [ ] No performance superiority claims
- [ ] Length: ~200 words (workshop)

### 8.11 References Checklist

- [ ] Every in-text citation has a corresponding entry in References
- [ ] Every References entry is cited in the text
- [ ] All DOIs/URLs are checked and working
- [ ] Author names spelled correctly
- [ ] Conference/journal names formatted consistently (venue abbreviation standard)
- [ ] Year matches
- [ ] No placeholder entries ("TBD")
- [ ] Style matches venue requirements (NeurIPS/ICML/AAAI format)
- [ ] Minimum citation checklist (see §6) is satisfied

### 8.12 Figure Checklist (for each figure)

- [ ] Figure is publication quality (300+ DPI, vector or high-res raster)
- [ ] All fonts are serif (matching paper body)
- [ ] All axis labels are readable at print size
- [ ] Legend is clear and positioned to avoid obscuring data
- [ ] Color scheme is accessible (colorblind-friendly)
- [ ] Figure number matches the citation order in text
- [ ] Caption is self-contained (reader should understand the figure without reading the main text)
- [ ] Statistical annotations present where needed (error bars, confidence bands)
- [ ] Fold boundaries or other reference marks present (where appropriate)
- [ ] Caption includes a "what to look for" sentence

### 8.13 Table Checklist (for each table)

- [ ] Table fits within page width (no overflow)
- [ ] Column headings are clear and self-explanatory
- [ ] Units are stated (where applicable)
- [ ] Footnotes present for any non-obvious interpretations
- [ ] Table number matches citation order
- [ ] Caption is self-contained
- [ ] Statistical significance markers explained in caption or footnote
- [ ] No empty cells (use "—" or "N/A")
- [ ] Decimal places consistent within each column
- [ ] Confidence intervals formatted as [lower, upper]

---

## 9. Cross-Reference Matrix

| Section | Depends On | Figures | Tables | Equations | Supporting Results | Key Citations |
|---------|-----------|---------|--------|-----------|-------------------|--------------|
| **Abstract** | All sections | — | — | — | F1, F6, F7, F8 | None |
| **§1 Introduction** | Results, Discussion | — | — | — | — | Markowitz, DeepTrader, MARS, Guo |
| **§2 Related Work** | Methodology | — | — | — | — | All literature |
| **§3.4 Methodology** | None | fig04 | — | Fusion: \( \mathbf{w}^* = \frac{\sum_i c_i \mathbf{w}_i}{\sum_i c_i} \), ECE formula | — | Schulman, Guo, Platt |
| **§3.5 Experimental Setup** | Methodology | — | table01 (abbreviated) | Sharpe ratio, ECE | Config values | — |
| **§3.6 Results** | Experimental Setup | fig01, fig02, fig03 | table01, table02, table03, table04 | Statistical test formulas | F1–F9, C1–C11 | — |
| **§3.7 Discussion** | Results | fig01, fig02, fig03 | table01–table04 | — | F1–F9, I1–I4 | DeMiguel, Guo |
| **§3.8 Limitations** | Results, Discussion | — | — | — | L1–L7 | — |
| **§3.9 Threats to Validity** | Limitations | — | — | — | L1–L7 (regrouped) | — |
| **§3.10 Conclusion** | All | — | — | — | F1, F6, F8 | — |
| **Appendix** | Results | Extended plots | Extended table02 | — | Per-fold data | — |

### Dependency Graph (Visual)

```
None ──► Methodology ──► Experimental Setup ──► Results ──► Discussion ──► Limitations ──► Threats to Validity
                                    │                                │
                                    │                                ▼
                                    └──────────────────► Introduction
                                                         │
                                                         ▼
                                                    Conclusion
                                                         │
                                                         ▼
                                                    Abstract
                                                         │
                                                         ▼
                                                    References (final pass)
```

---

## 10. Manuscript Timeline

### Logical Milestones (No Fixed Dates)

| Milestone | Sections | Effort Estimate | Nature of Work | Completes When |
|-----------|----------|----------------|----------------|----------------|
| **M1: Foundation** | Methodology (§3.4), Experimental Setup (§3.5) | 3 writing sessions | Direct translation from architecture docs and config files. Low cognitive load. | Both sections pass their checklists. |
| **M2: Evidence** | Results (§3.6), Figure captions, Table captions | 3 writing sessions | Verbatim evidence reporting. Every sentence maps to a finding. Requires figure/table finalization. | All figures final. All tables final. Results passes its checklist. |
| **M3: Context** | Related Work (§2) | 2 writing sessions | Literature synthesis. Can be written after Methodology is stable. | No factual errors in prior work descriptions. Architectural comparisons accurate. |
| **M4: Interpretation** | Discussion (§3.7), Limitations (§3.8), Threats to Validity (§3.9) | 3 writing sessions | Highest cognitive load. Requires complete Results. Every claim classified. | No overclaims. Calibration finding addressed. All limitations evidence-based. |
| **M5: Framing** | Introduction (§1), Conclusion (§3.10), Abstract (§3.1) | 2 writing sessions | Requires all earlier sections complete. | Introduction accurately previews results. Conclusion has no new claims. Abstract is accurate distillation. |
| **M6: Polish** | References (§3.11), Full consistency pass, Grammar pass, Figure/table final check | 2 writing sessions | Mechanical verification. All citations verified. Terminology consistent. | All checklists pass. No errors. |
| **M7: Internal Review** | Full manuscript read-through | 1 writing session + review cycle | Read as a reviewer. Identify weak arguments, missing evidence, overclaims, clarity issues. | All reviewer-reader issues resolved. |
| **M8: Submission** | Formatting, venue-specific requirements, cover letter (if required) | 1 writing session | Compliance with venue formatting. PDF generation. | Meets venue submission requirements. |

### Total Effort Estimate

- **Writing sessions:** 17 sessions (assuming 2–3 hours each = 34–51 hours).
- **Review cycles:** 1 internal review, 1 external review (if co-author or advisor available).
- **Buffer:** 20% for unexpected issues (figure revisions, writing blocks, formatting).

### Parallelization

- **M1 and M3** can be written in parallel (different authors).
- **M2 and M3** can be written in parallel.
- **M5 and M6** must be sequential (M5 before M6).

---

## 11. Final Submission Checklist

### 11.1 Writing Quality

- [ ] Every sentence is grammatically correct
- [ ] No run-on sentences
- [ ] Active voice preferred over passive
- [ ] No undefined abbreviations (all defined at first use)
- [ ] No informal language ("pretty good", "a lot of", "really")
- [ ] Every paragraph has a clear topic sentence
- [ ] No paragraph exceeds ~150 words (readability)
- [ ] British or American English is consistent throughout (choose one)
- [ ] Spelling and punctuation are consistent

### 11.2 Figures

- [ ] All figures numbered and cited in order
- [ ] All captions self-contained
- [ ] All figures at 300+ DPI
- [ ] All fonts serif
- [ ] Colorblind-accessible color scheme
- [ ] No pixelation or artifacts at print resolution
- [ ] Axis labels include units where applicable
- [ ] Legend present and readable
- [ ] Statistical annotations present (error bars, confidence bands)
- [ ] Figure files named consistently (fig01_cumulative_returns.pdf, etc.)
- [ ] No embedded figure titles (captions only)

### 11.3 Tables

- [ ] All tables numbered and cited in order
- [ ] All captions self-contained
- [ ] No overflow beyond page width
- [ ] Decimal places consistent within columns
- [ ] Statistical significance markers explained in caption or footnote
- [ ] Footnotes present for non-obvious interpretations
- [ ] No empty cells
- [ ] Units stated in column headers or caption
- [ ] Table04 (calibration) includes footnote about identity mapping

### 11.4 Statistics

- [ ] Exact p-values reported (not just "p < 0.05" or "p > 0.05")
- [ ] Effect sizes reported (Cohen's d for pairwise comparisons)
- [ ] Confidence intervals reported alongside point estimates
- [ ] No claim of "significance" without statistical test
- [ ] All statistical tests appropriate for the data (non-parametric where normality uncertain)
- [ ] Multiple comparison corrections applied where relevant (or stated as not needed)

### 11.5 Claims and Evidence

- [ ] Every claim supported by evidence cited in the text
- [ ] No claim from the "Unsupported Claims" table (PAPER_BLUEPRINT.md §10) appears
- [ ] Every numerical value verifiable from the JSON results
- [ ] No claim phrased as Interpretation that should be Observation (and vice versa)
- [ ] "19/20" not "all" — the one negative Sharpe is acknowledged
- [ ] Calibration non-function is reported, not hidden
- [ ] No comparative performance claims against unreproduced baselines

### 11.6 Reproducibility

- [ ] Dataset is frozen and versioned (v1.0.0)
- [ ] Random seeds are listed (42, 43, 44, 45, 46)
- [ ] Hyperparameters are fully specified
- [ ] Walk-forward parameters are specified (504/63/126, stride 126)
- [ ] Code repository URL referenced (if permitted by venue)
- [ ] Reproducibility manifest referenced

### 11.7 Citations

- [ ] Every in-text citation has an entry in References
- [ ] Every References entry is cited in the text
- [ ] All DOIs/URLs functional
- [ ] No broken references
- [ ] Venue formatting style applied consistently
- [ ] Author names correctly spelled
- [ ] Years match

### 11.8 Notation

- [ ] All mathematical symbols defined before first use
- [ ] Symbol definitions listed or clearly stated in text
- [ ] No symbol reused for different purposes
- [ ] Consistent notation across text, figures, and tables

### 11.9 Limitations and Threats

- [ ] All 7 limitations listed (PAPER_BLUEPRINT.md §7)
- [ ] Internal, external, construct, and statistical validity addressed
- [ ] No limitation contradicted elsewhere in the paper

### 11.10 Venue Compliance

- [ ] Page limit met (for workshops: 4–8 pages)
- [ ] Font and margin requirements satisfied
- [ ] Bibliography format matches venue style guide
- [ ] Supplementary material prepared (if allowed)
- [ ] Anonymized if required (double-blind review)
- [ ] PDF generated without errors
- [ ] No embedded links to author-identifying information (if anonymous)

### 11.11 Final Read-Through

- [ ] One full read-through as a reviewer
- [ ] One full read-through aloud (catches awkward phrasing)
- [ ] One full read-through focusing only on numbers (verify every metric)
- [ ] All section checklists (from §8) re-verified

---

## Appendix: Revision Tracking

After each milestone, record:
- What was completed
- What changed from the previous version
- What checklist items failed (and were fixed)
- What checklist items remain open

| Milestone | Date | Completed | Changes | Open Items |
|-----------|------|-----------|---------|------------|
| M1: Foundation | | | | |
| M2: Evidence | | | | |
| M3: Context | | | | |
| M4: Interpretation | | | | |
| M5: Framing | | | | |
| M6: Polish | | | | |
| M7: Internal Review | | | | |
| M8: Submission | | | | |
