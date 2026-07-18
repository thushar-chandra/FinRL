# HANDOFF.md

> Whoever picks this project up next — human or AI agent — read this file, then [CURRENT_STATE.md](./CURRENT_STATE.md), then [TASKS.md](./TASKS.md). No developer/team assignments or timeline information appear here by design (ADR-017, ADR-018).

## Current Progress

Documentation-only phase complete, and the architecture is now **frozen**. Three specialized reinforcement learning agents (Market Analysis, Risk Assessment, Portfolio Allocation), implemented within FinRL and trained via PPO; regime information folded into Feature Engineering (no standalone module); Confidence Estimation → Calibration → Confidence-Aware Decision Fusion (deterministic, explicitly independent from PPO) as the primary research contribution; a Risk Management Layer; Evaluation. No implementation code exists yet.

## Repository Status

- No fork has been created yet.
- No code written.
- The `docs/` knowledge base (22 files) is the first concrete artifact and is now internally consistent with the frozen architecture.

## Known Blockers

None architectural or documentation-level — an independent Design Review identified 4 Critical and 8 Major issues (undefined data flow, undefined fusion algorithm, missing Evaluation spec, module-boundary contradiction, plus terminology gaps), and all were resolved in the following session (see `DECISIONS.md` ADR-019–ADR-026). Remaining items are ordinary implementation-level decisions, not blockers:
1. Universe finalization (exact ticker list + as-of date).
2. Walk-forward parameters (fold count, window sizes, retrain cadence).
3. Shared vs. independent PPO training infrastructure across the three agents (ADR-013 — decide during Stage 2).
4. The exact combination function inside `ConfidenceEngine.estimate_raw_confidence()` (decide during Stage 3, record in `DECISIONS.md`).

## Immediate Next Tasks (in order)

1. Resolve the universe ticker list/date (`TASKS.md` T-002) — highest-leverage unblock available.
2. `T-001`: fork FinRL, verify baseline install.
3. `T-003`–`T-006`: data pipeline + feature engineering (including regime features) + the mandatory leakage test.
4. Proceed through `TASKS.md` in ID order within each priority tier; `IMPLEMENTATION_ROADMAP.md` gives the stage-level narrative if the task list alone isn't enough context; `SYSTEM_WORKFLOW.md` gives the plain-prose version tying stages together.

## Long-Term Roadmap (Order Only — No Timeline)

Stage 1 (Data Foundation) → Stage 2 (Specialized RL Agents) → Stage 3 (Confidence & Fusion — the core research contribution) → Stage 4 (Risk Management & Evaluation, including baselines and mandatory ablations) → Stage 5 (Integration). See `IMPLEMENTATION_ROADMAP.md` for full detail per stage.

## Useful Commands

**TODO:** populate once the repo is forked and the environment is set up (Stage 1). Anticipated:
```bash
pip install -e .
pytest tests/unit/
pytest tests/integration/
python finrl/main.py --config configs/  # exact CLI TBD
```

## Common Pitfalls (anticipate these before they happen)

- **Describing PPO as performing fusion/coordination** — explicitly reversed (ADR-014, ADR-015). PPO trains the three agents; it never combines their outputs.
- **Reverting the three agents to purely analytical/rule-based modules** — explicitly reversed (ADR-013). They are genuinely RL agents.
- **Reintroducing a standalone Regime Module** — explicitly reversed (ADR-016). Regime signals are Feature Engineering outputs.
- **Reintroducing a cross-agent dependency for the Portfolio Allocation Agent** — explicitly rejected (ADR-025). It consumes Feature Engineering output only.
- **Treating Confidence Estimation and Confidence Calibration as two separate pipeline stages** — confirmed as ONE combined module, `ConfidenceEngine` (ADR-022). Don't split it into two classes/files.
- **Implementing the fusion formula directly on raw, heterogeneous agent recommendations** — always transform each agent's recommendation into an `AssetWeightProposal` first (ADR-020); the worked numeric example in `CONFIDENCE_FUSION.md` is the reference to check against.
- **Inventing a source for `reasoning`/`confidence_summary` on `FinalRecommendation`** — both are populated by `ConfidenceAwareFusion.fuse()` and passed through unchanged by `RiskManagementLayer.apply()` (ADR-019); never derive them independently elsewhere.
- **Reimplementing outcome-label logic inside `EvaluationEngine`** instead of reusing the `OutcomeLabelGenerator` from `confidence_engine.py` (ADR-024) — this would break the guarantee that training-time calibration and test-time evaluation share one definition of "correct."
- **Lookahead bias in rolling/EWMA/regime features** — invisible without the mandatory leakage test; do not skip `T-006`.
- **Calibration fit on ineligible pairs** — invisible without the mandatory calibration-leakage test (`T-013`), now checkable directly against `OutcomeLabelGenerator.is_eligible_for_fold()`.
- **Reward/backtest transaction-cost inconsistency** — apply the cost term identically in agent training reward and in `EvaluationEngine.evaluate_financial()`.
- **Universe changed after experiments have started** — invalidates prior results; log it loudly in `CURRENT_STATE.md` if it happens.

## Where to Continue Next

Start at `TASKS.md` T-002 (universe finalization) if that's still open — nearly everything else is downstream of it. If it's resolved, start at T-001/T-003 and proceed in order.

---

**Related documents:** [CURRENT_STATE.md](./CURRENT_STATE.md) · [TASKS.md](./TASKS.md) · [OPENCODE.md](./OPENCODE.md) · [SYSTEM_WORKFLOW.md](./SYSTEM_WORKFLOW.md)
