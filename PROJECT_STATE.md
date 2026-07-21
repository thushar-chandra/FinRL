# PROJECT_STATE.md — CA-MARL Scientific Analysis & Manuscript Planning

> **Last updated:** 2026-07-21
> **Branch:** `feature/experimentation`
> **Freeze commit:** `ba81e82` (tag: `v2.0-phase3-complete`)
> **Current phase:** Phase 4 — Scientific Analysis / Manuscript Writing

---

## 1. Project Overview

### Research Objective
Design, implement, and honestly evaluate **CA-MARL** — a Confidence-Aware Multi-Agent Reinforcement Learning framework for portfolio allocation. The core contribution is a deterministic confidence-weighted fusion of three specialized PPO-trained agents (Market Analysis, Risk Assessment, Portfolio Allocation), with an explicit confidence estimation and calibration layer.

### Current Phase
**Phase 4 (Scientific Analysis & Manuscript Writing)** — analyzing frozen experimental results and drafting the manuscript. Phases 1 (Architecture), 2 (Implementation), and 3 (Experimentation) are complete and frozen.

### Repository Status
**FROZEN** — no code modifications permitted. The architecture, implementation, dataset, experimental results, figures, and tables are immutable. Only manuscript text and documentation may be edited.

---

## 2. Architecture Status

### Frozen Architecture
The architecture is declared frozen in `IMPLEMENTATION_FREEZE.md` (commit `e51d977`, tag `v1.0-implementation-freeze`). All architectural decisions are documented as ADR-001 through ADR-026 in `docs/architecture/DECISIONS.md`.

### Core Design Principles
1. **Deterministic fusion** — confidence-weighted averaging is NOT RL-trained (key distinction from MARS)
2. **No cross-agent inputs** — each agent consumes shared features only (ADR-025)
3. **Calibration leakage rule** — `timestamp + label_horizon <= fold_train_window_end` (ADR-024)
4. **Long-only, sum-to-one, 40% exposure cap** via risk management layer
5. **Frozen as-of date** for universe selection to prevent hindsight bias (ADR-011)

### Components That Must Not Change
- All 7 CA-MARL modules (agents, confidence engine, fusion, risk management, evaluation, data adapter, pipeline)
- Module interfaces and data contracts (`contracts.py`)
- Configuration schema (`config_schema.py`)
- Experimental results JSON files
- Frozen dataset (`experiments/dataset/`, SHA-256 verified)
- Publication figures/tables (except captions)

---

## 3. Current Git Information

| Property | Value |
|----------|-------|
| **Active branch** | `feature/experimentation` |
| **Latest freeze commit** | `8da9fc1` — "docs: freeze methodology, experimental setup, results, and discussion" |
| **Phase 3 freeze commit** | `ba81e82` — tagged `v2.0-phase3-complete` |
| **Implementation freeze commit** | `e51d977` — tagged `v1.0-implementation-freeze` |
| **Architecture freeze commit** | `3e75e1b` — "docs: freeze CA-MARL architecture before implementation" |
| **Upstream origin** | Fork of `AI4Finance-Foundation/FinRL` |
| **Other branches** | `master`, `feature/implementation-stage1` (merged/stale) |

---

## 4. Repository Map

### Top-Level Directories

| Directory | Purpose |
|-----------|---------|
| `finrl/` | Core FinRL framework (forked) + CA-MARL agents under `finrl/agents/ca_marl/` |
| `experiments/` | Experimental campaign framework, configs, results, plots, reports |
| `configs/` | YAML config directories (empty — actual configs are Python dataclasses in `experiments/_config.py`) |
| `trained_models/` | Pre-trained baseline models (A2C, DDPG, PPO — upstream FinRL) |
| `results/` | Baseline backtest results (upstream FinRL) |
| `docs/` | Architecture design docs, ADRs, research plan, implementation specs |
| `manuscript/` | Paper manuscript sections (methodology, experimental setup, results, discussion) |
| `tests/` | Integration tests (end-to-end pipeline, historical execution) |
| `unit_tests/` | Unit tests |
| `figs/` | Generated figures |
| `notebooks/` | Jupyter notebooks |
| `docker/` | Docker configuration |

### CA-MARL Module Source (`finrl/agents/ca_marl/`)

| File | Purpose | Lines |
|------|---------|-------|
| `market_agent.py` | PPO-trained directional BUY/SELL/HOLD agent | 524 |
| `risk_agent.py` | PPO-trained risk score / volatility estimator | 486 |
| `allocation_agent.py` | PPO-trained raw weight proposer | 479 |
| `confidence_engine.py` | Confidence estimation + Platt calibration + OutcomeLabelGenerator | 596 |
| `confidence_fusion.py` | Deterministic confidence-weighted fusion (primary contribution) | 376 |
| `risk_management.py` | Long-only, sum-to-one, 40% exposure cap enforcement | 167 |
| `evaluation.py` | Financial/calibration metrics, ablation, baseline comparison | 418 |
| `pipeline.py` | Pipeline orchestrator: build_agents, run_inference, run_pipeline | 279 |
| `data_adapter.py` | FinRL data pipeline → CA-MARL inputs | 147 |
| `contracts.py` | Shared typed contracts (AgentOutput, FinalRecommendation, etc.) | 167 |
| `config_schema.py` | Typed dataclass configuration schema | 213 |

### Experiment Scripts (`experiments/`)

| Script | Purpose |
|--------|---------|
| `run_campaign.py` | Master campaign runner — 5 seeds, 4 folds, frozen dataset |
| `run_ca_marl.py` | Single seed/experiment runner |
| `run_baselines.py` | Baseline computation (equal-weight, buy-and-hold, MVO) |
| `run_ablations.py` | Ablation studies |
| `run_plots.py` | Plot generation |
| `run_all.py` | Run everything sequentially |
| `_config.py` | All experiment parameters | 162 |
| `_walk_forward.py` | Walk-forward validation framework | 322 |
| `_pipeline.py` | Experiment-level pipeline wrapper | 189 |
| `_evaluate.py` | Evaluation runner | 233 |
| `_data_cache.py` | Versioned dataset cache (SHA-256) | 161 |
| `_baselines.py` | Baseline strategies | 193 |
| `_ablations.py` | Ablation studies | 227 |
| `_final_stats.py` | Statistical analyses (permutation, Kruskal-Wallis, Cohen's d) | 180 |
| `_dynamic_verify.py` | Runtime instrumentation (monkey-patches) | 693 |
| `_plotting.py` | Plotting utilities |
| `_publication_outputs.py` | Publication-quality figures and LaTeX tables |
| `_research_report.py` | Research report generator |

### Key Top-Level Documentation

| File | Purpose |
|------|---------|
| `AGENTS.md` | Scientific audit of calibration pipeline (7 findings) |
| `PAPER_BLUEPRINT.md` | Master manuscript design document (520 lines) |
| `MANUSCRIPT_PLAN.md` | Paper writing execution plan (798 lines) |
| `IMPLEMENTATION_FREEZE.md` | Implementation freeze declaration |
| `CONSISTENCY_AUDIT.md` | Audit of regime feature references (32 discrepancies found) |
| `DATASET_AUDIT.md` | Comprehensive dataset and experimental setup audit |
| `RESULTS_AUDIT.md` | Results section consistency audit (per-claim verification) |
| `PHASE_3_COMPLETION_REPORT.md` | Phase 3 experimentation completion (344 lines) |
| `PHASE_3_FREEZE_REPORT.md` | Phase 3 final frozen findings (9 supported, 8 unsupported) |

---

## 5. End-to-End Pipeline

```
Data (Yahoo Finance, 19 Nifty 50, 2020-2024)
  → Feature Engineering (8 technical indicators × 19 assets = 152 dims)
    → 3× PPO-trained RL Agents (Market, Risk, Allocation)
      → Confidence Estimation & Calibration (hist_accuracy, reward_stability, pred_consistency)
        → Confidence-Aware Decision Fusion (deterministic weighted average)
          → Risk Management Layer (long-only, sum-to-one, cap enforcement)
            → Final Portfolio Recommendation (allocation + reasoning + confidence summary)
              → Evaluation (Sharpe, Sortino, MaxDD, Vol, CumRet, ECE, Brier)
```

### Data Flow
- **In:** Raw OHLCV from yfinance
- **Features:** MACD, BB_upper, BB_lower, RSI-30, CCI-30, DX-30, SMA-30, SMA-60 (per asset)
- **Out:** Per-asset weights summing to 1.0, long-only, max 40% per asset

### Key Design Decision (ADR-025)
Each agent receives the **same feature input only** — no agent sees another agent's output. This avoids moving-target training problems.

### Key Design Decision (ADR-024)
Calibration pair eligibility: `recommendation.timestamp + label_horizon (5d) <= fold_training_window_end`. Prevents future information from contaminating calibration fitting.

---

## 6. Experiment Pipeline

### Walk-Forward Configuration
| Parameter | Value |
|-----------|-------|
| Folds | 4 |
| Training window | 504 trading days (~2 years) |
| Validation window | 63 days (~3 months) |
| Test window | 126 days (~6 months) |
| Stride | 126 days (= test window) |
| Retrain | Every fold |

### Fold Schedule
| Fold | Training | Validation | Test |
|------|----------|------------|------|
| 1 | 2020-01-01 → 2022-01-07 | 2022-01-10 → 2022-04-11 | 2022-04-12 → 2022-10-13 |
| 2 | 2020-07-07 → 2022-07-12 | 2022-07-13 → 2022-10-13 | 2022-10-14 → 2023-04-19 |
| 3 | 2021-01-04 → 2023-01-12 | 2023-01-13 → 2023-04-19 | 2023-04-20 → 2023-10-19 |
| 4 | 2021-07-08 → 2023-07-19 | 2023-07-20 → 2023-10-19 | 2023-10-20 → 2024-04-29 |

### Training Flow (per fold)
1. Load frozen dataset cache
2. Split into train/validation/test by fold schedule
3. Create FinRL environment on training window
4. Train 3× PPO agents (5,000 timesteps each, Stable-Baselines3)
5. Create a new `ConfidenceEngine` instance (fresh `_label_history`)
6. Run inference on test window → collect `AgentOutput`s
7. Estimate raw confidence (hist_accuracy=0.5 cold-start, reward_stability, pred_consistency)
8. Attempt calibration pair accumulation (receives 0 pairs → identity mapping)
9. Fuse agent outputs via confidence-weighted averaging
10. Enforce risk management constraints
11. Evaluate financial + calibration metrics

### Evaluation Flow (per campaign)
1. Run all 4 folds for 1 seed → per-fold JSON results
2. Aggregate across folds → per-seed summary
3. Repeat for seeds 42–46
4. Compute cross-seed statistics (mean, std, CI)
5. Compute baselines (equal-weight, buy-and-hold, MVO) on same test windows
6. Compute ablations (single 80/20 split)
7. Run statistical analyses (permutation test, sign test, Kruskal-Wallis, Cohen's d)
8. Generate publication-quality figures and LaTeX tables

### Statistical Analysis Results
| Analysis | Result | Interpretation |
|----------|--------|----------------|
| Paired permutation test (100k) | Mean Δ = −0.0455, p = 0.3246 | CA-MARL not distinguishable from equal-weight |
| Sign test (two-tailed) | 7/20 wins, p = 0.2632 | Not significant |
| Kruskal-Wallis (Sharpe × fold) | H = 17.86, p = 0.00047 | Strong regime effect across folds |
| Cohen's d (CA-MARL vs EW) | d = −0.03 | Negligible effect size |
| Cohen's d (CA-MARL vs MVO) | d = +1.43 | Large (but MVO underperforms) |

---

## 7. Verified Assumptions

### Experimentally Validated
| # | Finding | Evidence |
|---|---------|----------|
| F1 | Mean Sharpe = 1.885 (95% CI: [1.809, 1.961]) | 5 seeds × 4 folds |
| F2 | 19/20 Sharpe ratios positive (1 negative: −0.089) | JSON audit |
| F3 | Cross-seed Sharpe std = 0.087 | 5-seed computation |
| F4 | Strong regime effect (Kruskal-Wallis p = 0.00047) | Statistical analysis |
| F5 | All 20 combinations: `fallback_used = false` | JSON verification |
| F6 | CA-MARL vs EW: not significant (p = 0.3246, d = −0.03) | Statistical analysis |
| F7 | CumRet: CA-MARL = 9.6%, EW = 9.5%, BH = 9.5% | JSON data |
| F8 | Zero calibration pairs across all 4 folds | Dynamic verification |
| F9 | Ablation Sharpe range: 1.842–2.010 | Ablation JSON |

### What Remains Exploratory
- Ablation results (single 80/20 split, not walk-forward — no statistical replication)
- Allocation weight analysis vs 1/N (not yet computed)
- Bootstrap confidence intervals for Sharpe difference (not yet computed)

---

## 8. Known Limitations

### Calibration Non-Function (Critical)
- **Root cause:** Walk-forward stride (126d) equals test window length (126d), so fold k's test window ends at cursor+693, but next fold's training window ends at cursor+630. The ADR-024 eligibility check (`timestamp + 5d <= next_train_end`) always fails.
- **Impact:** Zero calibration pairs → identity mapping → `calibrated == raw` for all agents, all folds. Historical accuracy always 0.5 (cold-start). ECE/Brier metrics measure raw miscalibration.
- **Related bug:** `_collect_calibration_pairs()` correctly targets the validation window at `_walk_forward.py:258` but is **never called** from `run()`.
- **Frozen as-is:** No code modification permitted.

### Market Scope
- Single market: Indian large-cap equities (Nifty 50 proxy)
- Single time period: 2020–2024 bull market
- Not tested on: US equities, small-cap, emerging markets, bear markets

### Dataset Constraints
- 1,111 trading days (4.5 years) — limited for multi-year regime analysis
- 19 assets — limited for cross-sectional analysis
- Yahoo Finance data — no transaction-level or bid-ask data
- No regime features, volatility indices, or turbulence indices (despite architecture docs describing them — see CONSISTENCY_AUDIT.md)

### Ablation Limitations
- Ablations use single 80/20 train/test split, **not** walk-forward
- No statistical replication across seeds/folds
- Baseline CA-MARL under single-split protocol (1.939) exceeds walk-forward mean (1.885), suggesting favorable conditions

### Technical Debt
- `raw_confidence=0.0` stored in `AgentOutput` (placeholder — should be computed but calibration pairs never reach engine)
- Configuration duplication: `_VOL_NORMALIZATION_FACTOR = 10.0` in both `risk_agent.py:62` and `confidence_engine.py:31`
- YAML config loading not implemented (Python dataclasses used instead)
- `market_agent` does not populate `metadata["tie_break_reason"]` (minor contract deviation)

---

## 9. Important Implementation Quirks

### Intentional Behaviors

| Quirk | Rationale |
|-------|-----------|
| New `ConfidenceEngine` created each fold (`_pipeline.py:141`) | Avoids state leakage across folds; each fold gets a fresh `_label_history` |
| `_collect_calibration_pairs()` exists but is never called | The method correctly targets the validation window; its non-integration is the calibratation bug |
| Cold-start fallback to `hist_acc = 0.5` | Uninformative prior; correct design choice for Bayesian-like estimation |
| `yf.download()` bypasses FinRL's `YahooDownloader` | yfinance >= 1.5 removed `proxy=` parameter — compatibility shim |
| Agents share feature input (no cross-agent inputs) | ADR-025: prevents moving-target training problem |
| Fusion is deterministic (not RL-trained) | Core differentiator from MARS's meta-controller; independently auditable |
| `fallback_used = false` in all 20 cases | Agents consistently produce valid outputs without triggering the cold-start path |

### Things That Look Like Bugs But Aren't
- **Zero calibration pairs:** Looks like a calibration bug — and it is a functional bug — but the code structure is correct. The failure is a configuration-dependent interaction between stride size and the eligibility rule.
- **ECE of 0.493 for allocation agent:** Looks extreme, but is consistent with near-random raw confidence estimates when identity-mapped.
- **CA-MARL matching equal-weight:** May seem like failure, but is a valid and honestly reported finding that the three-agent architecture produces approximately diversified allocations.

---

## 10. Manuscript Status

### Frozen Sections (written, reviewed, consistent with evidence)
| Section | Status | Lines | Evidence Basis |
|---------|--------|-------|----------------|
| Methodology | ✅ Complete | `manuscript/methodology.md` (92 lines) | Architecture docs, MODULE_SPECIFICATIONS.md |
| Experimental Setup | ✅ Complete | `manuscript/experimental_setup.md` (31 lines) | `_config.py`, experiment plan |
| Results | ✅ Complete | `manuscript/results.md` (45 lines) | F1–F9, figures, tables |
| Discussion | ✅ Complete | `manuscript/discussion.md` (63 lines) | All experimental findings, dynamic verification |

### Remaining Sections (not yet written)
| Section | Priority | Dependencies |
|---------|----------|-------------|
| Abstract | Required | All other sections complete |
| Introduction | Required | Discussion complete |
| Related Work | Required | Methodology complete |
| Limitations | Required | Results + Discussion complete |
| Threats to Validity | Required | Limitations complete |
| Conclusion | Required | All other sections complete |
| References | Required | All citations finalized |

### Evidence Traceability
Every claim in the manuscript maps to a specific finding (F1–F9) from `PHASE_3_FREEZE_REPORT.md` or a specific artifact (JSON, figure, table). The `PAPER_BLUEPRINT.md` §10 Claims Matrix enumerates all 11 claims with their evidence basis. The `RESULTS_AUDIT.md` verifies each results paragraph against the underlying data.

### Required Revisions (per CONSISTENCY_AUDIT.md)
- `manuscript/methodology.md` §3.1 and §3.2: Remove references to "regime features" (4 lines with discrepancies)
- `PAPER_BLUEPRINT.md` §3 fig04 caption: Remove "volatility regime shading" reference
- `manuscript/results.md`: Update fig02 caption to describe "Calibration Error Analysis" not "Reliability Diagrams"

---

## 11. Reviewer Concerns Already Addressed

### Major Fixes Completed
1. **Figure 2 corrected** — renamed from "Reliability Diagrams" to "Calibration Error Analysis" because true reliability diagrams require stored (confidence, label) pairs
2. **Research report corrected** — "CA-MARL achieves positive risk-adjusted returns across all 5 seeds and all 4 walk-forward folds" changed to "19 of 20 fold-seed combinations" (one negative)
3. **Consistency audit** — 32 reference discrepancies between architecture docs and implementation identified; manuscript already corrected
4. **Phase 3 freeze report** — 9 supported findings + 8 explicitly unsupported claims documented to prevent overclaims in the paper
5. **Statistical analyses added** — permutation test, sign test, Kruskal-Wallis, Cohen's d, all from existing JSON without new experiments

### Design Decisions Worth Highlighting
- **Why not MARS meta-controller?** ADR-015: deterministic fusion is independently auditable; learned gating is opaque
- **Why three agents?** ADR-003: decomposing market direction, risk estimation, and allocation mirrors portfolio management practice
- **Why 5 seeds?** ADR-011: practical given CPU-only training; 4 folds × 5 seeds = 20 observations provides reasonable power
- **Why 5000 PPO timesteps?** Determined experimentally — sufficient for convergence on this problem scale
- **Why no transaction costs?** ADR-012: deferred to future work; exact bps value needs careful calibration

---

## 12. Remaining Tasks

### Immediate Next Steps (Manuscript Completion)
1. Write **Introduction** — 3–4 paragraphs motivating the problem, stating the gap, previewing contributions
2. Write **Related Work** — position vs DeepTrader, MARS, calibration literature
3. Write **Limitations** — all 7 limitations from evidence, each with concrete basis
4. Write **Threats to Validity** — internal, external, construct, and statistical
5. Write **Conclusion** — summarize contributions, honest assessment, future work
6. Write **Abstract** — last; distillation of the entire paper
7. Compile **References** — 25–35 entries
8. Apply CONSISTENCY_AUDIT.md manuscript corrections (regime feature references)
9. Apply RESULTS_AUDIT.md recommendations (CI method justification, CumRet clarification, post-hoc corrections)

### Optional Improvements (Low Effort)
- Allocation weight analysis — compute mean learned allocation vs 1/N (~1 hour)
- Bootstrap confidence intervals for Sharpe difference (~1 hour)

### Future Work (Post-Publication)
- Fix calibration eligibility (modify stride or connect `_collect_calibration_pairs()`)
- Implement regime features (as documented in architecture)
- Add transaction cost modelling (ADR-012)
- Expand to larger universes and multiple markets
- Hyperparameter sensitivity analysis
- Additional baselines (DeepTrader reproduction, MARS reproduction)

### Publication Checklist
- [ ] All manuscript sections drafted and verified against evidence
- [ ] Process for CONSISTENCY_AUDIT.md manuscript corrections complete
- [ ] RESULTS_AUDIT.md recommendations reviewed and applied
- [ ] Figures and tables referenced correctly in manuscript
- [ ] No Unsupported Claims (PHASE_3_FREEZE §3.2) appear anywhere
- [ ] All citations verified against original sources
- [ ] Reproducibility manifest updated for manuscript artifacts
- [ ] Target venue format requirements checked

---

## 13. Rules for Future Agents

### Do Not Redesign Architecture
The architecture is **frozen**. No proposals for:
- Alternative fusion methods (learned gates, attention, etc.)
- Additional agents or agent types
- Different calibration methods (beyond Platt/temperature scaling)
- Removal or merging of existing modules
- Changes to module interfaces or data contracts

### Preserve Frozen Implementation
No code modifications except:
- **Bug fixes** that do not affect module contracts (per IMPLEMENTATION_FREEZE.md post-freeze rules)
- **Manuscript text** and documentation only
- All bug fixes must be documented in a clear, auditable manner

### Preserve Reproducibility
- Do not modify frozen dataset (`experiments/dataset/`)
- Do not modify experimental results JSON
- Do not modify publication figures/tables (except captions)
- All claims must cite specific findings (F1–F9), artifacts, or evidence

### Respect Interface Contracts
- All module contracts, data structures, and typed configs are frozen
- `AgentOutput`, `FinalRecommendation`, `AssetWeightProposal`, `ConfidenceConfig`, etc. must not change
- Pipeline orchestration flow (build → infer → fuse → enforce → evaluate) must not change

### Writing Guidelines
- Every claim = Observation (data-driven), Interpretation (analysis), Hypothesis (speculation), or Future Work
- No mixing of categories within a paragraph (per Discussion standards in `PAPER_BLUEPRINT.md`)
- Negative findings (calibration non-function, equal-weight parity) must be reported transparently, not buried
- All evidence must be traceable to specific file + line number, artifact, or statistical result
