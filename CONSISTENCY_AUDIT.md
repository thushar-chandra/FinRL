# CONSISTENCY_AUDIT.md — Regime Feature References

**Scope:** Every reference to "regime features", "bull/bear", "volatility regime", "trend regime", "market-state features", or "regime conditioning" across the repository.

**Verification basis:** Frozen dataset `features_v1.0.0.pkl` — 1111×152 matrix, zero columns matching regime keywords. `_find_regime_columns()` in all three agents returns an empty list; `_extract_regime_bucket()` returns `"default"` exclusively. The `predict()` call receives no regime-registering columns. **References describing regime features as implemented/consumed by agents are factually incorrect.**

---

## 1. Manuscript Files

### `manuscript/methodology.md`

| # | Section | Text | Supported? | Action |
|---|---------|------|------------|--------|
| 1 | §3.1 System Overview | "regime signals---bull/bear indicators, volatility regime, trend regime, and market-state features---as inputs for the downstream agents" | **NO** — no such columns exist in the frozen features | **Remove** |
| 2 | §3.1 System Overview | "Regime information is incorporated as engineered features rather than as a separate pipeline stage." | **NO** — no regime information of any kind is present | **Remove** |
| 3 | §3.2 RL Agents | "the same feature input: technical indicators, volatility and return statistics, and regime features" | **NO** — agents receive 152 indicator columns only | **Remove** (change to "technical indicators, volatility and return statistics") |
| 4 | §3.3 Confidence | "within the same market regime" (prediction consistency description) | **PARTIAL** — `_find_k_neighbours` always uses `"default"` bucket, no actual regime filtering occurs. The neighbour search degrades gracefully but does not condition on regime | **Revise**: replace "within the same market regime" with "from recent historical states" |

### `manuscript/experimental_setup.md`

| # | Section | Text | Supported? | Action |
|---|---------|------|------------|--------|
| 5 | §4.7 Statistical Methodology | "To test for a regime effect across folds, we use a Kruskal-Wallis test on Sharpe ratios grouped by fold" | **YES** — this refers to fold-to-fold performance variation (Kruskal-Wallis H=17.86, p=0.00047 from `_final_stats.py`), not engineered regime features. The statistical finding F4 is fully supported. | **Keep** |

### `PAPER_BLUEPRINT.md`

| # | Section | Text | Supported? | Action |
|---|---------|------|------------|--------|
| 6 | §4 (H6) | "Performance is regime-dependent" | **YES** — supported by F4 (Kruskal-Wallis p=0.00047) | **Keep** |
| 7 | §5 contribution 7 | "Quantified regime effect" | **YES** — same statistical finding | **Keep** |
| 8 | §6 central narrative | "market regime, rather than strategy choice, is the dominant factor" | **YES** — supported | **Keep** |
| 9 | §1 intro key points | "regime effect dominates" | **YES** — supported | **Keep** |
| 10 | §3 (fig placement) fig04 caption | "volatility regime shading (high/low volatility in shaded regions)" | **NO** — fig04 (`fig_regime_timeline()` in `_publication_outputs.py:316-333`) is called **without** `regime_labels`. The published figure has no regime shading. | **Revise** caption to remove "volatility regime shading" and "high/low volatility in shaded regions" |
| 11 | §3 fig04 point | "contextualizes the regime effect" | **PARTIAL** — the figure shows fold boundaries and prices, which does contextualize fold differences. The "regime effect" meaning (fold variation) is supported. | **Revise** caption to describe fold boundaries only |
| 12 | §6 Discussion | "The regime effect (Kruskal-Wallis p = 0.00047) supports this" | **YES** | **Keep** |
| 13 | §9 Conclusion | "The regime effect is the dominant source of variation" | **YES** | **Keep** |
| 14 | §10 claims C4 | "Walk-forward folds produce significantly different Sharpe distributions (regime effect)" | **YES** | **Keep** |

---

## 2. Architecture & Design Documentation

These documents describe the *intended* design, not the implemented state. All are preserved for historical/audit purposes.

### `docs/architecture/ARCHITECTURE.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 15 | §1 Module 2 | **"including regime signals" (bull/bear indicator, volatility regime, trend regime, market-state features)** | **NO** | **Note** — describes intended design, not implementation |
| 16 | §2 (Mermaid) | Feature Engineering node includes regime features | **NO** | **Note** — same |
| 17 | §3 interaction table | Feature DataFrame includes regime features | **NO** | **Note** |
| 18 | §4 seq diagram | features (incl. regime features) | **NO** | **Note** |

### `docs/architecture/AGENTS.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 19 | §1 Inputs | "and regime features (bull/bear indicator, volatility regime, trend regime, market-state features)" | **NO** | **Note** |
| 20 | §2 Inputs | "feature DataFrame including volatility/return features and regime features" | **NO** | **Note** |
| 21 | §3 Inputs | "feature DataFrame + regime features only" | **NO** | **Note** |
| 22 | §4 Failure cases | "cold-start (insufficient track record in a regime bucket)" | **PARTIAL** — the `"default"` bucket code path works, but regime buckets are not meaningful | **Note** |

### `docs/architecture/MODULE_SPECIFICATIONS.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 23 | §1 Formulation | "state = feature vector (technical indicators + regime features)" | **NO** | **Note** |
| 24 | §1 Inputs | "including regime features (bull/bear indicator, volatility regime, trend regime, market-state features)" | **NO** | **Note** |
| 25 | §2 Formulation | "state = feature vector (volatility, return, regime features)" | **NO** | **Note** |
| 26 | §2 Inputs | "feature DataFrame including volatility/return features and regime features" | **NO** | **Note** |
| 27 | §3 Formulation | "state = feature vector + regime features" | **NO** | **Note** |
| 28 | §3 Inputs | "feature DataFrame + regime features only" | **NO** | **Note** |
| 29 | §4 Prediction consistency | "within the same regime bucket as the current state" | **PARTIAL** — code path exists but always uses `"default"` | **Note** |

### `docs/architecture/DECISIONS.md`

| # | ADR | Text | Supported? | Action |
|---|-----|------|------------|--------|
| 30 | ADR-003 | "regime-conditioned historical track record" | **NO** — no regime conditioning occurs | **Note** |
| 31 | ADR-005 (superseded) | "conditioned on calibrated confidence and regime" | **NO** — superseded ADR | **Note** |
| 32 | ADR-009 (superseded) | "no explicit market-regime conditioning" | **NO** — superseded ADR | **Note** |
| 33 | ADR-016 | "regime information (bull/bear market indicators, volatility regime, trend regime, market-state features) is engineered directly within Feature Engineering" | **NO** — this was the decision but was never implemented | **Note** |
| 34 | ADR-023 | "within the same regime bucket as the current state" | **PARTIAL** — code uses `"default"` always | **Note** |
| 35 | ADR-025 | "regime features" listed as agent input | **NO** | **Note** |

### `docs/architecture/SYSTEM_WORKFLOW.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 36 | §2 | "regime features (bull/bear indicator, volatility regime, trend regime, market-state features)" | **NO** | **Note** |
| 37 | §Stage 1 | "Feature Engineering (including regime features)" | **NO** | **Note** |

### `docs/architecture/INTERFACE_CONTRACTS.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 38 | §1 docstring | "including regime features (bull/bear, volatility regime, trend regime, market-state)" | **NO** — docstring only | **Note** |
| 39 | §3 docstring | "feature DataFrame incl. regime features" | **NO** — docstring only | **Note** |

### `docs/architecture/FINRL_MAPPING.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 40 | Feature Engineering row | "extended with returns, volatility, EWMA volatility, and regime features (ADR-016)" | **NO** | **Note** |
| 41 | Portfolio env row | "extended to carry regime features" | **NO** | **Note** |

---

## 3. Research & Planning Documents

### `docs/research/RESEARCH_MAPPING.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 42 | DeepTrader row | "its market-condition embedding motivates our regime features" | **NO** — regime features not implemented | **Note** |
| 43 | Data & Preprocessing row | "Figure: regime timeline over evaluation period (regime features, not a separate module)" | **NO** — figure has no regime shading | **Note** |

### `docs/research/EXPERIMENT_PLAN.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 44 | Calibration metrics | "computed per agent and per regime bucket" | **NO** — only computed per agent globally | **Note** |
| 45 | Figure list | "reliability diagrams per agent, per regime" | **NO** | **Note** |
| 46 | Figure list | "Regime timeline overlay on the evaluation period (volatility/trend regime over time)" | **NO** — fig04 has no regime overlay | **Note** |
| 47 | Table list | "ECE / Brier score by agent and regime" | **NO** | **Note** |

---

## 4. Implementation Reference

### `PROJECT_IMPLEMENTATION_REFERENCE.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 48 | §Data Adapter | "performs regime-column detection via keyword matching" | **PARTIAL** — the code exists but finds zero columns | **Note** |
| 49 | §Prediction consistency | "agreement fraction across k nearby regime-bucket states" | **PARTIAL** — uses `"default"` bucket | **Note** |
| 50 | §Agent observation | "including technical indicators and regime features" | **NO** | **Note** |
| 51 | §Known issues | "Regime features are not explicitly engineered. Regime-column detection uses keyword heuristics on column names; no regime classifier is implemented." | **YES** — this entry already documents the gap correctly | **Keep** |

---

## 5. Source Code (Docstrings)

### `finrl/agents/ca_marl/market_agent.py`, `risk_agent.py`, `allocation_agent.py`

| # | Function | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 52 | `_find_regime_columns` docstring | "Return the subset of columns that correspond to regime features. Regime features are documented... bull/bear indicator, volatility regime, trend regime, market-state features" | **PARTIAL** — function correctly searches for these keywords, but finds none. The docstring accurately describes what the function looks for, not what exists. | **Note** — code is correct; it gracefully degrades |
| 53 | `_extract_regime_bucket` docstring | "Falls back to the string 'default' when no regime columns are present" | **YES** — this fallback is always taken | **Keep** |
| 54 | `prediction_consistency` docstring | "within the same regime bucket as features (the current state)" | **PARTIAL** — the regime bucket is always `"default"`, so "same regime bucket" = "all historical data" | **Note** |

### `finrl/agents/ca_marl/config_schema.py`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 55 | `AgentHyperparameters` docstring | "features, rolling statistics, correlation, and regime features (bull/bear, volatility regime, trend regime, market-state)" | **NO** — docstring only | **Note** |

---

## 6. Figure/Plot Code

### `experiments/_publication_outputs.py`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 56 | file header | "fig04_regime_timeline.pdf — market regime overlay" | **NO** — figure contains no regime overlay; it is a plain normalized price chart | **Revise** description to "fig04_fold_boundaries.pdf — price chart with fold boundaries" (or similar) |
| 57 | `fig_regime_timeline()` | """Market regime overlay.""" | **NO** — function plots normalized prices with no regime shading | **Revise** docstring |

### `experiments/_plotting.py`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 58 | file header | "Reliability diagrams (calibration curves) per agent, per regime" | **NO** — reliability diagrams are not per-regime | **Note** |
| 59 | `plot_regime_timeline` | "regime_labels: optional array of regime labels (0/1 for bull/bear)" | **PARTIAL** — parameter exists but is never passed with non-None values in publication generation | **Note** |

### `experiments/_generate_publication_plots.py`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 60 | `generate_regime_timeline` | """Generate regime timeline overlay plot.""" | **NO** — `plot_regime_timeline` is called without `regime_labels` | **Revise** docstring |

---

## 7. README

### `README.md`

| # | Location | Text | Supported? | Action |
|---|----------|------|------------|--------|
| 61 | Architecture summary | "which includes regime features — bull/bear, volatility regime, trend regime, market-state — as ordinary engineered features" | **NO** — these features do not exist in the frozen implementation | **Revise** |
| 62 | Related work | "regime-feature motivation" (DeepTrader) | **PARTIAL** — the motivation exists but the features weren't implemented | **Revise** |

---

## 8. Statistical Finding Usage (Keep)

The following use "regime" in the statistical sense (fold-to-fold variation), which is **supported** by the Kruskal-Wallis test (H=17.86, p=0.00047). These require no change:

- `manuscript/experimental_setup.md` §4.7 — "regime effect across folds" (statistical test)
- `PHASE_3_FREEZE_REPORT.md` — "regime effect" (F4, Kruskal-Wallis)
- `PHASE_3_COMPLETION_REPORT.md` — "weakest regime", "strongest regime", "bull market regime" (fold interpretation)
- `PAPER_BLUEPRINT.md` — "regime effect", "regime-dependent", "Performance is regime-dependent" (all statistical)

---

## Summary of Required Actions

| Priority | File | Action |
|----------|------|--------|
| **CRITICAL** | `manuscript/methodology.md` §3.1 | Remove 2 sentences claiming regime signals are computed |
| **CRITICAL** | `manuscript/methodology.md` §3.2 | Replace "and regime features" with "and return statistics" |
| **MEDIUM** | `manuscript/methodology.md` §3.3 | Replace "within the same market regime" with "from recent historical states" |
| **MEDIUM** | `PAPER_BLUEPRINT.md` fig04 caption | Remove "volatility regime shading" — no such shading exists |
| **MEDIUM** | `PAPER_BLUEPRINT.md` fig04 caption | Remove "high/low volatility in shaded regions" |
| **LOW** | `experiments/_publication_outputs.py` | Rename/redescribe fig04 — it is a price chart, not a regime overlay |
| **LOW** | `experiments/_generate_publication_plots.py` | Fix `generate_regime_timeline` docstring |
| **LOW** | `README.md` | Remove regime features from architecture description |
| **NONE** | Architecture docs (`docs/architecture/*.md`) | Preserve as-is (design intent documentation) |
| **NONE** | Source code docstrings | Preserve as-is (graceful fallback documented in code) |
