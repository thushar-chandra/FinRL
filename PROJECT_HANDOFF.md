# CA-MARL Project Handoff

## Project Overview

CA-MARL (Confidence-Aware Multi-Agent Reinforcement Learning) is a research framework for portfolio allocation decision support. It decomposes the investment decision into three specialised PPO-trained agents — Market Analysis, Risk Assessment, Portfolio Allocation — whose recommendations are fused via deterministic confidence-weighted averaging. The core research contribution is the explicit confidence estimation and calibration layer, which produces per-agent calibrated confidence scores alongside allocation recommendations.

**Motivation:** Portfolio managers deploying DRL-based decision-support systems cannot distinguish high-confidence from low-confidence recommendations. Existing multi-agent RL portfolio systems (DeepTrader, MARS) do not expose calibrated confidence scores. CA-MARL addresses this gap with an auditable, independently-testable confidence pipeline.

**Primary scientific contributions:**
1. A seven-module CA-MARL architecture with deterministic confidence-weighted fusion (not RL-trained, unlike MARS's meta-controller)
2. A reproducible experimental framework: frozen dataset (v1.0.0, SHA-256), 4-fold walk-forward validation, deterministic seeding, complete reproducibility manifest
3. An honest empirical evaluation: CA-MARL achieves mean Sharpe 1.885 (95% CI: [1.809, 1.961]) but is not statistically distinguishable from equal-weight (permutation p = 0.3246)
4. Documented calibration negative finding: zero calibration pairs accumulate at the current walk-forward configuration
5. Quantified regime effect: walk-forward folds produce significantly different Sharpe distributions (Kruskal-Wallis p = 0.00047)

**Repository purpose:** Permanent frozen record of the complete CA-MARL architecture, implementation, experimental campaign, and manuscript. Serves as the reproducible evidence base for the associated paper and as a foundation for future research.

**Intended audience:** Academic reviewers reproducing the experiments, future researchers extending the framework, and maintainers ensuring long-term reproducibility.

---

## Repository Status

| Dimension | Status |
|-----------|--------|
| **Implementation** | FROZEN (v1.0-implementation-freeze, commit `e51d977`, tag `v1.0-implementation-freeze`) |
| **Experiments** | COMPLETE. 5 seeds x 4 folds of walk-forward validation, baselines, ablations. Results versioned in JSON. |
| **Statistical Analysis** | COMPLETE. Permutation test, sign test, Kruskal-Wallis test, Cohen's d — all in `_final_stats.py`. |
| **Repository** | FROZEN. Release commit `ff4412c` (`feature/experimentation` branch). Dataset (v1.0.0), results, figures, and tables are immutable. |
| **Release** | COMPLETE. Tagged for release. Repository finalized at commit `ff4412c` ("release: finalize CA-MARL repository"). |
| **Paper** | IN PROGRESS. Methodology, Experimental Setup, Results, Discussion, Limitations, Threats to Validity, and Availability sections complete. Abstract, Introduction, Related Work, and Conclusion not yet written. |

### Paper Sections

| Section | File | Status |
|---------|------|--------|
| Methodology | `manuscript/methodology.md` | Complete |
| Experimental Setup | `manuscript/experimental_setup.md` | Complete |
| Results | `manuscript/results.md` | Complete |
| Discussion | `manuscript/discussion.md` | Complete |
| Limitations | `manuscript/limitations.md` | Complete |
| Threats to Validity | `manuscript/threats_to_validity.md` | Complete |
| Code and Data Availability | `manuscript/availability.md` | Complete |
| References | `manuscript/references.md` | 9 entries (needs expansion to 25-35) |
| Abstract | — | Not yet written |
| Introduction | — | Not yet written |
| Related Work | — | Not yet written |
| Conclusion | — | Not yet written |

`PAPER_BLUEPRINT.md` contains planning content (Section 1 Research Problem, Section 2 Research Gap) that may serve as a starting point. `MANUSCRIPT_PLAN.md` (798 lines) provides a detailed writing execution plan.

---

## Repository Lifecycle

Information flows through the project in a unidirectional pipeline:

```
Repository (frozen)
  |
  v
Implementation (7 CA-MARL modules, frozen at v1.0)
  |
  v
Experiments (walk-forward campaign, baselines, ablations)
  |
  v
Results (JSON: per-fold metrics, allocations, calibration)
  |
  v
Statistical Analysis (permutation tests, Kruskal-Wallis, effect sizes)
  |
  v
Figures / Tables (publication-quality PDFs and LaTeX)
  |
  v
Manuscript (sections written from evidence, frozen after consistency audit)
  |
  v
Publication (target venue submission)
```

**Modification propagation:** Any change to the repository (e.g., dataset, implementation, experiment parameters) invalidates downstream results. The frozen architecture means only the manuscript and documentation are mutable. Figures and tables must be regenerated if results change. Statistical analyses must be rerun if underlying JSON results change.

---

## Change Impact Guide

| Modification | Re-run Experiments? | Re-generate Figures/Tables? | Re-run Statistics? | Manuscript Impact? |
|---|---|---|---|---|
| Dataset change | Yes — full campaign | Yes | Yes | Sections 4, 5, 6, 7 |
| Agent implementation change | Yes — full campaign | Yes | Yes | Sections 3, 4, 5, 6 |
| Experiment parameter change | Yes — full campaign | Yes | Yes | Sections 4, 5, 6 |
| Bug fix (contract-preserving) | Maybe — depends on scope | Maybe | Maybe | Possibly sections 5, 6 |
| Manuscript text only | No | No | No | Direct |
| Figure/table caption only | No | Minor regeneration | No | Direct |
| Reference update | No | No | No | Direct |

The frozen architecture means no code changes are permitted without a new ADR. The experimental results are immutable. Only manuscript text, captions, and references may be freely edited.

---

## Completed Work

### Architecture & Design

- 7 CA-MARL modules designed and documented: three RL agents, confidence engine (estimation + Platt calibration + OutcomeLabelGenerator), confidence-aware decision fusion, risk management layer, evaluation engine, data adapter, pipeline orchestrator
- 26 Architecture Decision Records (ADR-001 to ADR-026) in `docs/architecture/DECISIONS.md`
- Full typed contracts (`finrl/agents/ca_marl/contracts.py`) and configuration schema (`finrl/agents/ca_marl/config_schema.py`)
- Architecture documentation suite: ARCHITECTURE.md, MODULE_SPECIFICATIONS.md, AGENTS.md, INTERFACE_CONTRACTS.md, CONFIDENCE_FUSION.md, SYSTEM_WORKFLOW.md, FINRL_MAPPING.md
- Research documentation: EXPERIMENT_PLAN.md, RESEARCH_MAPPING.md
- Implementation documentation: DIRECTORY_STRUCTURE.md, TESTING_STRATEGY.md, OPENCODE.md

### Implementation

All seven CA-MARL modules implemented and verified on real historical market data (3-ticker smoke test, 100-timestep synthetic smoke test):

| Module | File | Lines |
|--------|------|-------|
| Market Analysis RL Agent | `market_agent.py` | 524 |
| Risk Assessment RL Agent | `risk_agent.py` | 486 |
| Portfolio Allocation RL Agent | `allocation_agent.py` | 479 |
| Confidence Engine + OutcomeLabelGenerator | `confidence_engine.py` | 596 |
| Confidence-Aware Decision Fusion | `confidence_fusion.py` | 376 |
| Risk Management Layer | `risk_management.py` | 167 |
| Evaluation Engine | `evaluation.py` | 418 |
| Pipeline Orchestrator | `pipeline.py` | 279 |
| Data Adapter | `data_adapter.py` | 147 |

Integration tests pass: `tests/integration/test_end_to_end_pipeline.py` (synthetic) and `tests/integration/test_historical_execution.py` (3-ticker historical data).

### Experiments

- **Dataset:** 19 Nifty 50 equities, 2020-01-01 to 2024-06-27 (1,111 trading days), frozen as v1.0.0 with SHA-256 verification
- **Walk-forward validation:** 4 folds, training window = 504 days, validation = 63 days, test = 126 days, stride = 126 days
- **Random seeds:** 42, 43, 44, 45, 46 (5 seeds x 4 folds = 20 paired observations)
- **PPO timesteps:** 5,000 per agent per fold (CPU training)
- **Experiment scripts:** `run_campaign.py` (master), `run_ca_marl.py` (single), `run_baselines.py`, `run_ablations.py`, `run_plots.py`, `run_all.py`

### Baselines

- Equal-weight (1/N) — daily rebalanced
- Buy-and-hold — equal-weight at start, held throughout
- Static mean-variance optimisation (Markowitz) — estimated on training window

DeepTrader and MARS were planned but could not be reliably reproduced within the project timeline; the manuscript compares architecturally rather than empirically.

### Ablations (Single 80/20 Split, Not Walk-Forward)

- Equal-weight fusion (unweighted average of agent proposals)
- No calibration (raw confidence used directly)
- Shuffled confidence (randomly permuted across agents)
- Drop-one-agent (market, risk, allocation removed in turn)

### Statistical Analyses

| Analysis | Result | Interpretation |
|----------|--------|----------------|
| Paired permutation test (100k) | Mean Delta = -0.0455, p = 0.3246 | CA-MARL not distinguishable from equal-weight |
| Sign test (two-tailed) | 7/20 wins (35%), p = 0.2632 | Not significant |
| Kruskal-Wallis (Sharpe x fold) | H = 17.86, p = 0.00047 | Strong regime effect across folds |
| Cohen's d (CA-MARL vs EW) | d = -0.03 | Negligible effect size |
| Cohen's d (CA-MARL vs MVO) | d = +1.43 | Large (but MVO underperforms) |

### Publication Artifacts

- **Figures (PDF, 300 DPI):** `experiments/plots/publication/figures/fig01_cumulative_returns.pdf`, `fig02_calibration_analysis.pdf`, `fig03_ablation_bars.pdf`, `fig04_regime_timeline.pdf`
- **Tables (LaTeX):** `experiments/plots/publication/tables/table01_summary.tex`, `table02_per_fold.tex`, `table03_ablation.tex`, `table04_calibration.tex`
- **Research report:** `experiments/reports/research_report.md` (full written analysis)
- **Artifact manifest:** `experiments/reports/artifact_manifest.json` (47-pass verification)
- **Reproducibility manifest:** `experiments/reproducibility_manifest.json` (locked parameters, commit, Python version)

### Quality Assurance

- CONSISTENCY_AUDIT.md — 32 discrepancies identified between architecture docs and implementation (regime feature references); manuscript corrected
- RESULTS_AUDIT.md — per-claim verification of every Results paragraph against underlying data
- DATASET_AUDIT.md — comprehensive audit of data provenance, feature engineering, walk-forward schedule
- Dynamic verification — monkey-patched runtime instrumentation confirming calibration pipeline behaviour across all 4 folds
- 47-pass automated verification suite

---

## Research Findings

The following are empirical research findings — outcomes of the experimental campaign — not software defects.

### F1: CA-MARL Mean Sharpe = 1.885 (95% CI: [1.809, 1.961])

Averaged across 5 random seeds and 4 walk-forward folds. Nineteen of twenty fold-seed combinations yield positive Sharpe ratios. Mean Sortino = 3.327, Max Drawdown = -6.5%, per-fold Cumulative Return = 9.6%.

### F2: Not Statistically Distinguishable from Equal-Weight

Paired permutation test: mean Sharpe difference = -0.0455 (CA-MARL minus equal-weight), p = 0.3246. Sign test: CA-MARL wins 7 of 20 comparisons (p = 0.2632). Cohen's d = -0.03 (negligible). Equal-weight Sharpe = 1.931.

### F3: Confidence Weighting Produced Limited Measurable Improvement

Equal-weight fusion (ablation) produces Sharpe = 1.951, nearly identical to CA-MARL baseline (1.939). Shuffled confidence produces Sharpe = 1.952. The specific confidence values are not measurably load-bearing.

### F4: Strong Regime Effect

Kruskal-Wallis H = 17.86, p = 0.00047. Fold mean Sharpe ratios: 0.161 (fold 01), 0.756 (fold 02), 3.597 (fold 03), 3.027 (fold 04). Cross-fold variance is approximately 20x cross-seed variance. Market conditions (2020-2024 Indian bull market) are the dominant performance factor.

### F5: Calibration Pipeline Produces Identity Mappings

Zero calibration pairs accumulate across all 4 folds. All `fit_calibration` calls receive empty pair lists. calibrated == raw for every agent in every fold. Dynamic runtime instrumentation confirms this behaviour. The root cause is a temporal mismatch: stride (126d) equals test window length (126d), so fold k's test window ends after fold k+1's training window, causing the ADR-024 eligibility check to always fail. An alternative accumulation method (`_collect_calibration_pairs()`, `_walk_forward.py:269`) correctly targets the validation window but is never called from `run()`.

### F6: Equal Weight Remained Highly Competitive

Across all folds, equal-weight and buy-and-hold baselines closely match CA-MARL's Sharpe and cumulative return. This is consistent with the "1/N puzzle" (DeMiguel et al., 2009) and reflects the 2020-2024 bull market where diversified long-only exposure was broadly rewarded.

### F7: Ablation Variants Cluster within Narrow Range

Sharpe range: 1.842 (drop allocation agent) to 2.010 (drop market agent). Dropping the market agent improves Sharpe — the agent's categorical signals may introduce noise rather than signal. These results are from a single 80/20 train/test split (not walk-forward) and lack statistical replication.

### F8: Static MVO Underperforms

Mean Sharpe = -0.288, Max Drawdown = -18.8%. The large effect size (d = +1.43) vs MVO reflects the instability of the static MVO baseline with a 504-day estimation window and 19 assets, not CA-MARL's strength.

---

## Implementation Issues

These are confirmed implementation issues supported by repository evidence. They are distinct from research findings.

### Calibration Pipeline Inactive (Confirmed)

- **Evidence:** Dynamic verification confirms 0 calibration pairs across all 4 engines. `fit_calibration` receives [] every fold. `_collect_calibration_pairs()` (correctly targets validation window at `_walk_forward.py:269`) is never called from `run()`.
- **Root cause:** Walk-forward stride (126d) = test window length (126d). For fold k, test window ends at cursor+693; next fold's training window ends at cursor+630. The ADR-024 eligibility check (`_walk_forward.py:250`) always fails for test-window predictions.
- **Impact:** Identity mapping. Historical accuracy always 0.5 (cold-start fallback at `confidence_engine.py:338-342`). ECE/Brier metrics measure raw miscalibration.
- **Reference:** `_walk_forward.py:221-263` (accumulation), `_walk_forward.py:250` (eligibility check), `_pipeline.py:154` (new ConfidenceEngine each fold), `_pipeline.py:157` (fit_calibration([])).

### raw_confidence = 0.0 Placeholder in AgentOutput

- **Evidence:** All 12 agent `predict()` calls return `raw_confidence=0.0`. Computed raw confidences from `ConfidenceEngine.estimate_raw_confidence` range [0.3234, 0.7296] (mean = 0.6107) but are stored separately in the calibration pipeline.
- **Location:** `market_agent.py:318`, `risk_agent.py:305`, `allocation_agent.py:294` — each sets `raw_confidence=0.0` in `predict()`.
- **Impact:** Even if calibration pairs accumulated, `fit_calibration` would receive 0.0 confidence values, not the computed estimates.

### _VOL_NORMALIZATION_FACTOR = 10.0 Duplicated

- **Location:** `risk_agent.py:62` and `confidence_engine.py:31`.
- **Risk:** If changed in one but not the other, training and evaluation signals diverge.

### market_agent Does Not Populate metadata["tie_break_reason"]

- **Location:** `market_agent.py`.
- **Impact:** Minor contract deviation. The market agent has no tie-break logic, so there is nothing to record. Experiments use `FinalRecommendation`, not per-agent metadata directly.

### YAML Configuration Loading Not Implemented

- Architecture documents describe YAML-based configuration. Implementation uses Python dataclasses (`experiments/_config.py`), which are fully functional.

---

## Experimental Limitations

### Internal Validity

| Limitation | Why It Exists | Effect on Interpretation | Should Future Work Address? |
|---|---|---|---|
| Calibration non-functional | Temporal mismatch between stride and eligibility rule prevents pair accumulation | Claims about confidence-aware fusion are based on raw (uncalibrated) confidences; identity mapping means ablation comparisons measure same underlying values | Yes — fix eligibility or connect `_collect_calibration_pairs()` |
| Ablations use single 80/20 split | Computational constraints; full walk-forward ablations would require 5 x 4 x 7 = 140 experiments | Results may not generalise to walk-forward setting (baseline Sharpe differs: 1.939 vs 1.885) | Yes — replicate across walk-forward folds |
| Historical accuracy always 0.5 | Calibration non-function prevents label accumulation | Effective confidence varies only through reward stability and prediction consistency | Yes — fix calibration pipeline |

### External Validity

| Limitation | Why It Exists | Effect on Interpretation | Should Future Work Address? |
|---|---|---|---|
| Single market (Indian large-cap equities) | Fixed research scope (Nifty 50 constituents) | Results may not generalise to other geographies, market structures, or capitalisations | Yes — test on US, European, or emerging markets |
| Single time period (2020-2024 bull market) | Fixed dataset range | Performance is regime-dependent; results may not hold in bear or range-bound markets | Yes — test across multiple market regimes |
| 19 assets | Nifty 50 constituent subset | Limited cross-sectional diversification; results may not scale to larger universes | Yes — expand universe |
| 1,111 trading days (4.5 years) | Data availability | Limited for multi-year regime analysis | Yes — extend time period |
| Daily frequency | Design choice | Applicability to intraday, weekly, or monthly strategies not established | Optional |

### Statistical Validity

| Limitation | Why It Exists | Effect on Interpretation | Should Future Work Address? |
|---|---|---|---|
| 5 random seeds | CPU training constraints (5000 timesteps per agent) | Limited power for detecting small effects; cross-seed variance estimate is noisy | Yes — increase to 20+ seeds |
| 20 paired observations | 5 seeds x 4 folds | Not fully independent (same 4 EW values reused across seeds); wide CIs | Yes — more folds and seeds |
| CI uses normal approximation | Standard choice | t-distribution (df=4) would yield ~9% wider CIs | Low — note in manuscript |
| No multiple comparison correction | Not applied to pairwise Mann-Whitney tests | Family-wise error rate at alpha = 0.01 for 6 tests = 5.8% | Yes — apply Bonferroni or FDR |

### Construct Validity

| Limitation | Why It Exists | Effect on Interpretation | Should Future Work Address? |
|---|---|---|---|
| Sharpe ratio as primary metric | Standard in portfolio literature | Does not account for skewness, kurtosis, or drawdown asymmetry | Report additional metrics (already done: Sortino, MaxDD) |
| Confidence operationalisation | Fixed untuned weights (hist=0.4, rs=0.3, pc=0.3) | May not capture theoretical construct of calibrated trustworthiness | Yes — sensitivity analysis over weighting |
| No transaction costs | Deferred per ADR-012 | All returns are gross; daily rebalancing of 19 assets incurs frictions | Yes — model trading costs |
| MVO baseline disadvantaged | 504-day estimation window for 19-asset covariance matrix | Large effect size vs MVO is misleadingly flattering | Use shrinkage or longer estimation window |

---

## Technical Debt

Technical debt is distinct from research limitations. These are implementation choices that increase maintenance burden or risk.

| Issue | Location | Impact | Priority |
|---|---|---|---|
| raw_confidence=0.0 placeholder | market_agent.py, risk_agent.py, allocation_agent.py | Calibration pairs store 0.0 instead of computed values | High |
| _VOL_NORMALIZATION_FACTOR = 10.0 duplicated | risk_agent.py:62, confidence_engine.py:31 | Divergent if changed in one file only | Medium |
| yf.download() workaround for yfinance >= 1.5 | data_adapter.py | Fragile; may break with future yfinance versions | Low |
| YAML config loading not implemented | — | Architecture docs describe it; Python dataclasses used instead | Low |
| market_agent missing tie_break_reason | market_agent.py | Minor contract deviation | Low |

---

## Repository Layout

```
finrl/
  agents/ca_marl/              # CA-MARL module implementations (11 files)
    market_agent.py             # PPO-trained Market Analysis agent (524 lines)
    risk_agent.py               # PPO-trained Risk Assessment agent (486 lines)
    allocation_agent.py         # PPO-trained Portfolio Allocation agent (479 lines)
    confidence_engine.py        # Confidence estimation + Platt calibration + OutcomeLabelGenerator (596 lines)
    confidence_fusion.py        # Deterministic confidence-weighted fusion (376 lines)
    risk_management.py          # Long-only, sum-to-one, exposure cap enforcement (167 lines)
    evaluation.py               # Financial + calibration metrics, ablations, baselines (418 lines)
    pipeline.py                 # Pipeline orchestrator: build_agents, run_inference, run_pipeline (279 lines)
    data_adapter.py             # FinRL -> CA-MARL data pipeline adapter (147 lines)
    contracts.py                # Typed data contracts (167 lines)
    config_schema.py            # Configuration dataclasses (213 lines)
experiments/                    # Experimental campaign framework
  _config.py                    # All experiment parameters (dataclasses, single source of truth)
  _walk_forward.py              # Walk-forward validation loop (322 lines)
  _pipeline.py                  # Experiment-level pipeline wrapper (189 lines)
  _evaluate.py                  # Single-experiment runner (233 lines)
  _data_cache.py                # Versioned dataset cache, SHA-256 verified (161 lines)
  _baselines.py                 # Baseline strategy implementations (193 lines)
  _ablations.py                 # Ablation study implementations (227 lines)
  _final_stats.py               # Statistical analyses (permutation, Kruskal-Wallis, Cohen's d) (180 lines)
  _dynamic_verify.py            # Runtime instrumentation / monkey-patches (693 lines)
  _publication_outputs.py       # Publication-quality figures + LaTeX tables (585 lines)
  _plotting.py                  # Plotting utilities
  _research_report.py           # Research report generator
  _utils.py                     # Shared utilities
  _verify_all.py                # Automated verification suite (47 checks)
  _generate_publication_plots.py# Publication plot driver
  _consistency_audit.py         # Consistency auditing
  _phase3_checks.py             # Phase 3 verification checks
  _fix_fig02.py                 # Figure 2 correction (reliability diagrams -> calibration analysis)
  run_campaign.py               # Master campaign runner (5 seeds, 4 folds)
  run_ca_marl.py                # Single experiment runner
  run_baselines.py              # Baseline computation
  run_ablations.py              # Ablation studies
  run_plots.py                  # Plot generation
  run_all.py                    # Run everything sequentially
  dataset/                      # Frozen dataset (SHA-256 verified)
    features_v1.0.0.pkl         # Feature matrix (1111 x 152)
    forward_returns_v1.0.0.pkl  # Forward returns
    realized_prices_v1.0.0.pkl  # Realized prices
    metadata.json               # Version, checksums, tickers, date range
    universe.json               # Universe definition
  results/                      # Campaign result JSON files
    campaign_v1_seed_0042.json  # Per-fold metrics, allocations, baselines, calibration
    campaign_v1_seed_0043.json
    campaign_v1_seed_0044.json
    campaign_v1_seed_0045.json
    campaign_v1_seed_0046.json
    campaign_v1_ablations_seed_0000.json  # Ablation results
    dynamic_verify_seed_0042.json
    preliminary/                # Preliminary results
  plots/                        # Generated figures and tables
    publication/figures/        # 4 publication-quality PDFs
    publication/tables/         # 4 LaTeX .tex files
    *.png                       # Exploratory PNG plots
    *.csv                       # Aggregated results CSVs
  reports/                      # Research report + artifact manifest
    research_report.md          # Full written analysis
    artifact_manifest.json      # 47-pass verification
  dynamic_verify_log.txt        # Full runtime instrumentation log
  dynamic_verify_report.txt     # Dynamic verification analysis
  reproducibility_manifest.json # Locked experiment parameters
  ablations/                    # Ablation runner scripts
  baselines/                    # Baseline runner scripts
configs/                        # YAML config directories (empty — Python dataclasses used)
manuscript/                     # Paper manuscript sections
  methodology.md                # Architecture and methods (92 lines)
  experimental_setup.md         # Dataset, walk-forward, hyperparameters (31 lines)
  results.md                    # Experimental findings (45 lines)
  discussion.md                 # Interpretation (63 lines)
  limitations.md                # Implementation and experimental limitations (29 lines)
  threats_to_validity.md        # Validity threats (41 lines)
  availability.md               # Code and data availability (7 lines)
  references.md                 # 9 entries
docs/                           # Architecture, research, planning docs
  architecture/                 # ARCHITECTURE.md, MODULE_SPECIFICATIONS.md, AGENTS.md, etc.
  research/                     # EXPERIMENT_PLAN.md, RESEARCH_MAPPING.md
  implementation/               # DIRECTORY_STRUCTURE.md, TESTING_STRATEGY.md, OPENCODE.md
  planning/                     # Project planning documents
tests/                          # Integration tests
unit_tests/                     # Unit tests
trained_models/                 # Pre-trained upstream FinRL models
results/                        # Upstream FinRL baseline results
figs/                           # Generated figures
notebooks/                      # Jupyter notebooks
docker/                         # Docker configuration
```

---

## Important Files

| File | Purpose |
|------|---------|
| `experiments/_config.py` | All experiment hyperparameters (single source of truth) |
| `experiments/_walk_forward.py` | Walk-forward validation with calibration eligibility |
| `experiments/_pipeline.py` | Experiment-level pipeline with timestamp patching |
| `experiments/_final_stats.py` | Statistical analyses (permutation, Kruskal-Wallis, Cohen's d) |
| `experiments/_dynamic_verify.py` | Runtime instrumentation for calibration verification |
| `experiments/_data_cache.py` | Dataset loading with SHA-256 verification |
| `experiments/reproducibility_manifest.json` | Locked experiment parameters |
| `experiments/reports/artifact_manifest.json` | Generated artifact inventory |
| `experiments/reports/research_report.md` | Full campaign analysis |
| `experiments/dataset/metadata.json` | Dataset version + checksums |
| `experiments/dynamic_verify_log.txt` | Runtime instrumentation log |
| `experiments/dynamic_verify_report.txt` | Dynamic verification analysis |
| `finrl/agents/ca_marl/contracts.py` | All typed data contracts |
| `finrl/agents/ca_marl/config_schema.py` | Configuration dataclasses |
| `finrl/agents/ca_marl/confidence_engine.py` | Confidence estimation + Platt calibration + OutcomeLabelGenerator |
| `finrl/agents/ca_marl/confidence_fusion.py` | Primary contribution: deterministic fusion |
| `docs/architecture/DECISIONS.md` | Architecture Decision Record (ADR-001 to ADR-026) |
| `docs/architecture/ARCHITECTURE.md` | System design, diagrams, data/confidence flow |
| `docs/architecture/MODULE_SPECIFICATIONS.md` | Research-facing module specifications |
| `docs/architecture/CONFIDENCE_FUSION.md` | Fusion specification with worked example |
| `PROJECT_STATE.md` | Comprehensive project state (405 lines) |
| `PAPER_BLUEPRINT.md` | Master manuscript design document (520 lines) |
| `MANUSCRIPT_PLAN.md` | Paper writing execution plan (798 lines) |
| `IMPLEMENTATION_FREEZE.md` | Implementation freeze declaration (94 lines) |
| `CONSISTENCY_AUDIT.md` | Audit of regime feature references (220 lines) |
| `RESULTS_AUDIT.md` | Results section consistency audit (283 lines) |
| `DATASET_AUDIT.md` | Dataset and experimental setup audit (274 lines) |
| `PHASE_3_COMPLETION_REPORT.md` | Phase 3 experimentation completion (344 lines) |
| `PHASE_3_FREEZE_REPORT.md` | Final frozen findings (170 lines) |
| `AGENTS.md` | Scientific audit of calibration pipeline |

---

## Reproduction Workflow

### Prerequisites

- Python 3.11+ (validated on Python 3.14.5)
- Dependencies listed in `pyproject.toml` and `requirements.txt`

### Install

```bash
pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Note: `elegantrl` is pinned with `--no-deps` to avoid `pygame` build failures on Windows.

### Reproduce the Campaign

```bash
# Run full experimental campaign (5 seeds, 4 folds, ~hours on CPU)
python experiments/run_campaign.py

# Run single experiment
python experiments/run_ca_marl.py --seed 42 --folds 4

# Compute baselines
python experiments/run_baselines.py

# Run ablation studies
python experiments/run_ablations.py

# Generate publication figures and tables
python experiments/run_plots.py
```

### Dataset

The frozen dataset (`experiments/dataset/`, v1.0.0, SHA-256 verified) is included in the repository. To regenerate from source:

```bash
python experiments/_data_cache.py
```

### Verification

```bash
# Run integration tests
pytest tests/

# Run automated verification suite (47 checks)
python experiments/run_all.py

# Verify dynamic instrumentation
python experiments/_dynamic_verify.py
```

### Assumptions

- CPU-only training is sufficient (PPO with 5,000 timesteps per agent, 19 assets)
- The frozen dataset is trusted (SHA-256 checksums in `experiments/dataset/metadata.json`)
- Random seeds 42-46 produce deterministic results given the same environment
- Results JSON files in `experiments/results/` are the authoritative source for all metrics

---

## Current Status

### Completed

- [x] Architecture design and documentation (26 ADRs)
- [x] Implementation of all 7 CA-MARL modules
- [x] Integration tests (synthetic + historical)
- [x] Frozen dataset v1.0.0 (SHA-256 verified)
- [x] Walk-forward campaign (5 seeds x 4 folds)
- [x] Baseline comparisons (EW, BH, MVO)
- [x] Ablation studies (equal-weight fusion, no calibration, shuffled confidence, drop-one-agent)
- [x] Statistical analyses (permutation, sign, Kruskal-Wallis, Cohen's d)
- [x] Publication-quality figures (4 PDFs)
- [x] Publication-quality tables (4 LaTeX files)
- [x] Manuscript sections: Methodology, Experimental Setup, Results, Discussion, Limitations, Threats to Validity, Availability, References
- [x] Quality assurance: CONSISTENCY_AUDIT, RESULTS_AUDIT, DATASET_AUDIT, dynamic verification
- [x] Repository cleanup and release engineering

### Remaining Administrative Tasks

- [ ] Write Abstract, Introduction, Related Work, Conclusion
- [ ] Expand References to 25-35 entries
- [ ] Apply RESULTS_AUDIT.md recommendations (CI method justification, CumRet clarification, post-hoc correction note)
- [ ] Choose target venue and check formatting requirements
- [ ] Verify figure/table references in manuscript
- [ ] Create release tag (e.g., v2.0-release)
- [ ] Set up DOI (e.g., Zenodo) for frozen dataset
- [ ] Update repository URL in pyproject.toml and manuscript/availability.md
- [ ] Push to public repository

### Known Implementation Issues

1. Calibration pipeline inactive (temporal mismatch between stride and eligibility rule)
2. raw_confidence=0.0 placeholder in all three agents
3. _VOL_NORMALIZATION_FACTOR duplicated
4. market_agent missing tie_break_reason
5. YAML config loading not implemented

### Research Findings

1. Mean Sharpe = 1.885, not distinguishable from equal-weight (p = 0.3246)
2. Zero calibration pairs; identity mapping throughout
3. Strong regime effect (Kruskal-Wallis p = 0.00047)
4. Ablation variants cluster tightly (Sharpe 1.842-2.010)
5. Equal-weight fusion and shuffled confidence match CA-MARL baseline
6. Dropping market agent improves Sharpe (2.010 vs 1.939)
7. Static MVO underperforms severely (-0.288)

### Repository Version

- **pyproject.toml:** version = "2.0.0", name = "ca-marl"
- **Python:** ^3.11, validated on 3.14.5
- **Last commit:** `ff4412c` ("release: finalize CA-MARL repository", feature/experimentation branch)
- **Phase 3 freeze commit:** `ba81e82` (tagged v2.0-phase3-complete)
- **Implementation freeze commit:** `e51d977` (tagged v1.0-implementation-freeze)
- **Architecture freeze commit:** `3e75e1b`

### Release Status

COMPLETE. Repository finalized at commit `ff4412c`. No further code commits anticipated. Manuscript completion and publication submission are the remaining deliverables.

### Paper Status

IN PROGRESS. 8 of 12 sections complete. 4 sections (Abstract, Introduction, Related Work, Conclusion) remain to be written. References (9 entries) need expansion to 25-35. CONSISTENCY_AUDIT.md corrections pending.

---

## Next Steps

### Critical (Pre-Publication)

1. Write Abstract (<=250 words) — distillation of the entire paper
2. Write Introduction — problem motivation, gap, contributions
3. Write Related Work — position vs DeepTrader, MARS, calibration literature
4. Write Conclusion — summary, honest assessment, future work
5. Expand References to 25-35 entries
6. Apply RESULTS_AUDIT.md key recommendations (CumRet clarification, CI method justification, post-hoc correction)

### High

8. Verify all figure/table references in manuscript
9. Choose target venue and check formatting requirements
10. Verify no Unsupported Claims (PHASE_3_FREEZE.md Section 3.2) appear in manuscript
11. Create public release tag (e.g., v2.0-release)
12. Update repository URL in pyproject.toml and manuscript/availability.md

### Medium

13. RESULTS_AUDIT.md minor recommendations (seed 46 outlier note, agent-level calibration differences, MVO contextualisation)
14. Bootstrap confidence intervals for Sharpe difference (~1 hour, existing JSON data)
15. Allocation weight analysis — compute mean learned allocation vs 1/N (~1 hour, existing JSON data)
16. Set up DOI (e.g., Zenodo) for frozen dataset

### Low

17. Push to public repository
18. Correct fig02/fig04 descriptions in _publication_outputs.py docstrings
19. Correct fig04 description in _generate_publication_plots.py docstring
20. Remove regime-feature references from README.md architecture description

---

## Release Checklist

- [ ] All manuscript sections drafted and verified against evidence
- [x] CONSISTENCY_AUDIT.md manuscript corrections applied
- [ ] RESULTS_AUDIT.md recommendations reviewed and applied
- [ ] Figures and tables referenced correctly in manuscript
- [ ] No Unsupported Claims (PHASE_3_FREEZE.md Section 3.2) appear anywhere
- [ ] All citations verified against original sources
- [ ] Reproducibility manifest updated for manuscript artifacts
- [ ] Target venue format requirements checked
- [ ] Release tag created (e.g., v2.0-release)
- [ ] DOI set up for frozen dataset
- [ ] Repository URL updated in pyproject.toml and availability.md
- [ ] Repository pushed to public location

---

## Future Work

### Implementation Improvements

- Fix calibration eligibility: modify stride to be larger than test window, or connect `_collect_calibration_pairs()` from `run()`
- Replace `raw_confidence=0.0` placeholder with proper uncertainty estimates from the confidence engine
- Extract `_VOL_NORMALIZATION_FACTOR` to a shared configuration constant
- Implement YAML configuration loading for experiment-driven parameter changes

### Research Extensions

- Test on larger universes (S&P 500, FTSE 100) and multiple geographies
- Test on different market regimes (bear market, range-bound, high volatility)
- Implement regime features (as documented in architecture) using regime classifier
- Add transaction cost modelling (ADR-012) with realistic bps estimates
- Hyperparameter sensitivity analysis over PPO parameters and confidence weights

### Experimental Improvements

- Replicate ablations across walk-forward folds (not single 80/20 split)
- Increase random seeds to 20+ for tighter confidence intervals
- Apply multiple comparison correction to pairwise fold tests
- Store (confidence, label) calibration pairs in JSON output to enable reliability diagrams
- Add shrinkage-based MVO baseline (or alternative covariance estimation)
- Add additional baselines: DeepTrader reproduction, MARS reproduction, risk-parity, momentum

### Repository Improvements

- Finalize public repository URL
- Set up DOI for frozen dataset
- Clean up stale branches (master, feature/implementation-stage1)

### Publication Opportunities

- Main paper at financial ML or multi-agent systems venue
- Methodology/negative-result note (calibration non-function finding)
- Reproducibility-track submission (experimental framework contribution)

### Long-term Ideas

- End-to-end learned fusion (moving from deterministic to learned gates, per ADR-005 supersession)
- Ensemble disagreement for confidence (per ADR-003 v2 upgrade path)
- Online calibration that adapts to non-stationary confidence distributions
- Multi-market multi-asset extension with transfer learning across universes
- Integration with a realistic backtesting platform for transaction-level evaluation

---

## Evidence Traceability

Every claim in the manuscript maps to:
- **F1-F9** findings from `PHASE_3_FREEZE_REPORT.md`
- Specific JSON result files in `experiments/results/`
- Dynamic verification logs in `experiments/dynamic_verify_log.txt`
- Figures and tables in `experiments/plots/publication/`
- CONSISTENCY_AUDIT.md and RESULTS_AUDIT.md verify per-claim accuracy
- PAPER_BLUEPRINT.md Section 10 Claims Matrix enumerates all 11 claims with evidence sources
- RESULTS_AUDIT.md verifies each results paragraph against underlying data
