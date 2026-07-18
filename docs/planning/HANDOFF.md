# HANDOFF.md

> Whoever picks this project up next — human or AI agent — read this file, then [CURRENT_STATE.md](./CURRENT_STATE.md), then [TASKS.md](./TASKS.md). No developer/team assignments or timeline information appear here by design (ADR-017, ADR-018).

## Current Progress

**Architecture is frozen.** Three specialized reinforcement learning agents (Market Analysis, Risk Assessment, Portfolio Allocation), implemented within FinRL and trained via PPO; regime information folded into Feature Engineering (no standalone module); Confidence Estimation → Calibration → Confidence-Aware Decision Fusion (deterministic, explicitly independent from PPO) as the primary research contribution; a Risk Management Layer; Evaluation.

**Baseline validation is complete.** The upstream FinRL baseline (data pipeline, PPO/A2C/DDPG training, backtesting) has been end-to-end validated on the DOW 30 universe. See [`BASELINE_ANALYSIS.md`](../research/BASELINE_ANALYSIS.md). The remaining work is **CA-MARL implementation** — no further baseline validation is needed.

## Repository Status

- FinRL fork exists and baseline install is verified.
- Trained models exist: `trained_models/agent_ppo.zip`, `agent_a2c.zip`, `agent_ddpg.zip`.
- Data pipeline validated: `train_data.csv`, `trade_data.csv` generated and tested.
- The `docs/` knowledge base (22+ files) is internally consistent with the frozen architecture.
- `configs/` directory placeholders created but not populated.
- No CA-MARL-specific code exists yet.

## Known Blockers

None — Design Review findings (4 Critical, 8 Major) are resolved (ADR-019–ADR-026). Baseline validation is complete. Remaining items are ordinary CA-MARL implementation decisions, not blockers:

1. Universe finalization (Indian large-cap ticker list + as-of date).
2. Walk-forward parameters (fold count, window sizes, retrain cadence).
3. Shared vs. independent PPO training infrastructure across the three agents (ADR-013 — decide during Stage 2).
4. The exact combination function inside `ConfidenceEngine.estimate_raw_confidence()` (decide during Stage 3, record in `DECISIONS.md`).

## Immediate Next Tasks (in order)

**The baseline is done. Begin CA-MARL implementation.**

1. **T-002**: Resolve the Indian large-cap universe ticker list and as-of date — highest-leverage unblock.
2. **T-007/008/009**: Implement the three specialized RL agents (Market Analysis, Risk Assessment, Portfolio Allocation). The FinRL PPO infrastructure is already validated — this is about building the CA-MARL-specific agent classes.
3. **T-011/012/014**: Implement the core research contribution — Confidence Estimation & Calibration, then Confidence-Aware Decision Fusion.
4. Proceed through `TASKS.md` in ID order within each priority tier; `IMPLEMENTATION_ROADMAP.md` gives the stage-level narrative.

## Long-Term Roadmap (Order Only — No Timeline)

Stage 0 (Baseline Validation — **complete**) → Stage 1 (Data Foundation for CA-MARL) → Stage 2 (Specialized RL Agents) → Stage 3 (Confidence & Fusion — the core research contribution) → Stage 4 (Risk Management & Evaluation, including baselines and mandatory ablations) → Stage 5 (Integration). See `IMPLEMENTATION_ROADMAP.md` for full detail per stage.

## Useful Commands

```bash
pip install -e .
pip install stockstats scikit-learn
# Run CA-MARL pipeline (once implemented):
# python finrl/main.py --mode train --config configs/
# Run tests (once implemented):
# pytest tests/unit/
# pytest tests/integration/
# View baseline validation results:
# See trained_models/ and results/ for existing model artifacts
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

Start at `TASKS.md` T-002 (universe finalization) if that's still open — nearly everything else is downstream of it. If T-002 is resolved, begin T-007 (Market Analysis RL Agent). The baseline (T-001) is already complete; skip forward to CA-MARL implementation tasks.

---

**Related documents:** [CURRENT_STATE.md](./CURRENT_STATE.md) · [TASKS.md](./TASKS.md) · [BASELINE_ANALYSIS.md](../research/BASELINE_ANALYSIS.md) · [OPENCODE.md](../implementation/OPENCODE.md) · [SYSTEM_WORKFLOW.md](../architecture/SYSTEM_WORKFLOW.md)
