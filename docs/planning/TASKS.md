# TASKS.md

> Kanban-style backlog, expressed by dependency and priority only — **no effort/day estimates, no owner assignments** (ADR-017, ADR-018). Stage grouping matches [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md).

| ID | Priority | Description | Dependencies | Acceptance Criteria | Status |
|---|---|---|---|---|---|---|
| T-001 | P0 | Fork FinRL, verify baseline install and existing example run | — | Clean install; existing FinRL portfolio_allocation example runs unmodified | **Completed** — see `BASELINE_ANALYSIS.md` |
| T-002 | P0 | Finalize fixed universe ticker list + as-of selection date, write `configs/universe.yaml` | — | List + date documented, avoids hindsight bias (ADR-011) | **Open — pending decision** |
| T-003 | P0 | Replace FinRL ticker config with fixed universe | T-001, T-002 | Data pipeline downloads exactly the fixed universe + Nifty 50 | Not Started |
| T-004 | P0 | Add data validation (missing dates, schema consistency, versioning) | T-003 | `test_data_pipeline.py` passes | Not Started |
| T-005 | P0 | Extend preprocessor: returns, rolling returns, volatility, EWMA volatility, rolling correlation, **and regime features** (bull/bear indicator, volatility regime, trend regime, market-state) | T-004 | Full feature set matches `MODULE_SPECIFICATIONS.md`/`ARCHITECTURE.md`; no standalone regime module created (ADR-016) | Not Started |
| T-006 | **P0 (highest-priority test in repo)** | Write and pass the feature-engineering leakage test | T-005 | No rolling/EWMA/regime feature uses future data at any timestep | Not Started |
| T-007 | P1 | Implement Market Analysis RL Agent (within FinRL, PPO-trained), incl. `prediction_consistency()` | T-006 | Common output contract compliance (`INTERFACE_CONTRACTS.md`); training sanity checks pass; deterministic tie-break tested; `prediction_consistency()` unit-tested | Not Started |
| T-008 | P1 | Implement Risk Assessment RL Agent (within FinRL, PPO-trained), incl. `prediction_consistency()` | T-006 | Common output contract compliance; EWMA warm-up edge case handled | Not Started |
| T-009 | P1 | Implement Portfolio Allocation RL Agent (within FinRL, PPO-trained), incl. `prediction_consistency()` — features-only input, NO cross-agent dependency (ADR-025) | T-006 | Long-only/sum-to-one enforcement is NOT assumed at this layer — deferred authoritatively to Risk Management Layer | Not Started |
| T-010 | P2 | Decide and document shared vs. independent PPO training infrastructure across the three agents | T-007, T-008, T-009 | Decision recorded in `INTERFACE_CONTRACTS.md`/`FINRL_MAPPING.md` | Not Started |
| T-011 | **P0 (core novelty)** | Implement `OutcomeLabelGenerator` (ADR-024) + Confidence Estimation: historical accuracy, reward stability, prediction consistency per agent | T-007, T-008, T-009 | Produces raw confidence per agent per `MODULE_SPECIFICATIONS.md` §4; `is_eligible_for_fold()` leakage rule implemented | Not Started |
| T-012 | **P0 (core novelty)** | Implement Confidence Calibration (Platt or temperature scaling — pick one, record in `DECISIONS.md`) + ECE/Brier/reliability diagnostics — same `ConfidenceEngine` class as T-011 (ADR-022) | T-011 | Calibration fit strictly on `is_eligible_for_fold()`-eligible pairs; diagnostics sane on smoke test | Not Started |
| T-013 | P1 | Write and pass the confidence-calibration leakage test | T-012 | Constructed test case with an ineligible pair confirmed excluded (ADR-024 rule) | Not Started |
| T-014 | **P0 (primary research contribution)** | Implement Confidence-Aware Decision Fusion: `AssetWeightProposal` transform functions + weighted-average formula (ADR-020) + `reasoning`/`confidence_summary` composition (ADR-019) | T-012 | Worked numeric example in `CONFIDENCE_FUSION.md` passes as a golden-value test; `Σ(Confidence)=0` and per-agent fallback paths handled and logged | Not Started |
| T-015 | P1 | Implement Risk Management Layer (passes `reasoning`/`confidence_summary` through unchanged) | T-014 | Long-only/sum-to-one/exposure caps enforced authoritatively, tested independent of upstream correctness | Not Started |
| T-015b | **P0** | Implement Evaluation (`EvaluationEngine` — ADR-021): financial metrics, calibration metrics (reusing `OutcomeLabelGenerator` from T-011), ablation support, baseline comparison | T-011, T-015 | All metric functions unit-tested against synthetic known-answer inputs | Not Started |
| T-016 | P1 | End-to-end integration test | T-015, T-015b | Full pipeline runs raw-data-to-recommendation-to-evaluation without exceptions | Not Started |
| T-017 | P2 | Remove `finrl/trade.py`; repurpose `train.py`/`test.py` into walk-forward loop | T-001 | Live/paper trading execution structurally removed | Not Started |
| T-018 | P2 | Determine walk-forward fold count/window sizes/retrain cadence | — | Documented in `configs/walk_forward.yaml` | **Open — pending decision** |
| T-019 | P2 | Add transaction cost model (flat bps) to reward and evaluation | T-017 | Cost term applied consistently between training reward and backtest eval | **Open — bps value TBD** |
| T-020 | P3 | Implement baselines: 1/N, buy-and-hold, static MVO | T-009 | All three run against the same walk-forward folds as CA-MARL | Not Started |
| T-021 | P3 | DeepTrader reimplementation | — | Committed baseline reproduced with documented fidelity notes | Not Started |
| T-022 | P4 | MARS reimplementation (stretch goal) | — | Only attempted if T-020/T-021 and core pipeline are solid | Not Started, may not happen |
| T-023 | P2 | Shuffled-confidence ablation, via `EvaluationEngine.run_ablation("shuffled_confidence")` | T-016 | Result reported honestly regardless of outcome direction | Not Started |
| T-024 | P2 | Drop-one-agent ablation, via `EvaluationEngine.run_ablation("drop_one_agent")` | T-016 | Per-agent contribution measured | Not Started |
| T-025 | P3 | Populate `RESEARCH_MAPPING.md` and generate all figures/tables from `EXPERIMENT_PLAN.md` | T-020–T-024 | Every paper claim traceable to an experiment | Not Started |
| T-026 | Ongoing | Keep `CURRENT_STATE.md`, `HANDOFF.md`, `PROMPT_HISTORY.md` updated | — | Never more than one work session out of date | Ongoing |

**Legend:** P0 = blocking/critical path, P1 = high priority, P2 = medium, P3 = lower priority, P4 = stretch goal.

---

**Related documents:** [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) · [CURRENT_STATE.md](./CURRENT_STATE.md) · [HANDOFF.md](./HANDOFF.md) · [BASELINE_ANALYSIS.md](../research/BASELINE_ANALYSIS.md)
