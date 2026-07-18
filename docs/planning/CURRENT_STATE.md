# CURRENT_STATE.md

> Living document — update this file at the end of every work session. See also [HANDOFF.md](./HANDOFF.md) for "what to do next" specifically. This document tracks module/dependency status only — no developer/team assignments (ADR-017) and no timeline/day estimates (ADR-018).

**Last updated:** post-Design-Review implementation session (architecture frozen; all Critical/Major Design Review findings resolved at the documentation level; no implementation code has been written yet).

---

## Repository State

No code has been written. The architecture is **frozen and, as of this session, fully specified at the interface level**: three specialized reinforcement learning agents (Market Analysis, Risk Assessment, Portfolio Allocation — each consuming Feature Engineering output only, ADR-025), Confidence Estimation & Calibration as one combined module (ADR-022) including a shared `OutcomeLabelGenerator` (ADR-024), Confidence-Aware Decision Fusion with a fully concrete algorithm (`AssetWeightProposal` intermediate representation, per-agent transform functions, a worked numeric example — ADR-020) and defined `reasoning`/`confidence_summary` composition (ADR-019), a Risk Management Layer, and a fully specified Evaluation module (`EvaluationEngine` — ADR-021). This `docs/` knowledge base (22 canonical files) is the first concrete engineering artifact, and has now passed an independent Design Review followed by a resolution pass addressing every Critical and Major finding.

## Completed

- [x] Research problem and contribution framing finalized (`PROJECT_CONTEXT.md`, `DECISIONS.md`).
- [x] Full architecture frozen, including the frozen-architecture reversal that restored genuinely RL-trained agents with a separate, deterministic, PPO-independent fusion module (ADR-013–ADR-018).
- [x] Independent Design Review completed, identifying 4 Critical and 8 Major issues (undefined `reasoning`/`confidence_summary` data flow, undefined fusion algorithm for heterogeneous outputs, missing Evaluation specification, Confidence Estimation/Calibration module-count contradiction, plus terminology/cross-reference gaps).
- [x] All 4 Critical and 8 Major Design Review findings resolved and recorded as ADR-019 through ADR-026: concrete `FusedDecision`→`FinalRecommendation` data flow; a fully worked `AssetWeightProposal`-based fusion algorithm with a proven sum-to-1 guarantee; a formal Evaluation module (`EvaluationEngine`) added consistently across `MODULE_SPECIFICATIONS.md`, `AGENTS.md`, `INTERFACE_CONTRACTS.md`; Confidence Estimation & Calibration confirmed as one combined module and `ARCHITECTURE.md` corrected to match; Prediction Consistency operationalized; Outcome Label Generator ownership/timing/leakage rule formalized; the Portfolio Allocation Agent's cross-agent dependency explicitly rejected; terminology and cross-reference canonicalization completed ("Confidence Engine" retired, "Final Portfolio Recommendation" canonicalized, a Class→File map added).
- [x] Base repository selected: fork of AI4Finance-Foundation/FinRL, FinRL's DRL-agent training pattern reused for the three specialized agents (`MIGRATION_PLAN.md`, `FINRL_MAPPING.md`, now including explicit dependency/execution-order columns).

## Missing (everything below is unimplemented)

- [ ] All code in `finrl/agents/ca_marl/` (see `DIRECTORY_STRUCTURE.md`), including the newly-specified `evaluation.py` and `OutcomeLabelGenerator` (co-located in `confidence_engine.py`).
- [ ] `configs/` directory and all config files.
- [ ] All tests, including the golden-value test for the `CONFIDENCE_FUSION.md` worked numeric example and the calibration-leakage test against the concrete ADR-024 eligibility rule.
- [ ] Fixed universe ticker list and as-of selection date.
- [ ] Calibration method final choice (Platt vs. temperature scaling).
- [ ] Walk-forward fold parameters (count, window size, retrain cadence).
- [ ] Transaction cost model (flat bps value).
- [ ] Decision on shared vs. independent PPO training infrastructure across the three agents (ADR-013 leaves this open by design).
- [ ] The confidence-combination function inside `ConfidenceEngine.estimate_raw_confidence()` (how historical accuracy, reward stability, and prediction consistency are combined into one raw score) — flagged as an implementation detail in `INTERFACE_CONTRACTS.md` §4, still open.

## Blocked

- Nothing is currently blocked on external decisions or documentation ambiguity — the Design Review's Critical and Major findings are resolved, and the remaining open items above are implementation-level, to be resolved during Stage 2–4 work (`IMPLEMENTATION_ROADMAP.md`).
- **Baseline reproduction of MARS** remains a stretch goal, not a committed baseline.

## Technical Debt

None yet — no code exists.

## Known Issues

None yet.

## Pending Decisions (implementation-level, to be resolved during development — not architectural, not ambiguous)

| Item | Status |
|---|---|
| Exact ticker list + universe selection as-of date | Open |
| Calibration method: Platt vs. temperature scaling | Open, either acceptable |
| Walk-forward fold count / window sizes / retrain cadence | Open |
| Transaction cost model (flat bps assumed; exact value) | Open |
| Shared vs. independent PPO training infrastructure across the three agents | Open by design (ADR-013) — resolve during Stage 2 |
| Confidence-combination function inside `estimate_raw_confidence()` (weights on historical accuracy / reward stability / prediction consistency) | Open — resolve during Stage 3, record choice in `DECISIONS.md` |
| Whether MARS is attempted as a real baseline or only cited as related work | Open, leaning toward stretch goal |

---

**Related documents:** [HANDOFF.md](./HANDOFF.md) · [TASKS.md](./TASKS.md) · [DECISIONS.md](./DECISIONS.md)
