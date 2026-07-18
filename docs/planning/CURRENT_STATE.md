# CURRENT_STATE.md

> Living document — update this file at the end of every work session. See also [HANDOFF.md](./HANDOFF.md) for "what to do next" specifically. This document tracks module/dependency status only — no developer/team assignments (ADR-017) and no timeline/day estimates (ADR-018).

**Last updated:** baseline validation complete; CA-MARL implementation beginning.

---

## Repository State

The architecture is **frozen and fully specified at the interface level**: three specialized reinforcement learning agents (Market Analysis, Risk Assessment, Portfolio Allocation — each consuming Feature Engineering output only, ADR-025), Confidence Estimation & Calibration as one combined module (ADR-022) including a shared `OutcomeLabelGenerator` (ADR-024), Confidence-Aware Decision Fusion with a fully concrete algorithm (`AssetWeightProposal` intermediate representation, per-agent transform functions, a worked numeric example — ADR-020) and defined `reasoning`/`confidence_summary` composition (ADR-019), a Risk Management Layer, and a fully specified Evaluation module (`EvaluationEngine` — ADR-021).

**Baseline validation is complete.** The upstream FinRL baseline has been validated end-to-end on the DOW 30 stock trading task: data pipeline (Yahoo Finance download, technical indicators), training (A2C, DDPG, PPO — 20k timesteps each), and backtesting (three DRL agents all outperformed DJIA during a market downturn). See [`BASELINE_ANALYSIS.md`](../research/BASELINE_ANALYSIS.md) for the full validation report. The `docs/` knowledge base (22+ canonical files) and the validated FinRL baseline are the two concrete engineering artifacts.

## Completed

### Architecture & Design
- [x] Research problem and contribution framing finalized.
- [x] Full architecture frozen, including the frozen-architecture reversal that restored genuinely RL-trained agents with a separate, deterministic, PPO-independent fusion module (ADR-013–ADR-018).
- [x] Independent Design Review completed, identifying 4 Critical and 8 Major issues.
- [x] All 4 Critical and 8 Major Design Review findings resolved and recorded as ADR-019 through ADR-026.

### Baseline Validation
- [x] FinRL repository forked and baseline install verified.
- [x] Data pipeline validated: DOW 30 stock list retrieval, Yahoo Finance download, technical indicator computation, train/trade split.
- [x] PPO baseline trained and validated (agent_ppo.zip, results/ppo/).
- [x] A2C and DDPG baselines also trained and validated (agent_a2c.zip, agent_ddpg.zip).
- [x] Backtest validation completed: all three DRL agents outperformed DJIA baseline in 2026 market downturn.
- [x] Environment setup validated: Python 3.11.9, SB3 2.9.0, PyTorch 2.13.0 (CPU), Gymnasium 1.3.0.
- [x] Known issue documented: TensorboardCallback `rollout_buffer` KeyError for off-policy algorithms (cosmetic only).
- [x] Baseline validation report written: [`BASELINE_ANALYSIS.md`](../research/BASELINE_ANALYSIS.md).

## Missing — CA-MARL Implementation

- [ ] All code in `finrl/agents/ca_marl/` including `market_agent.py`, `risk_agent.py`, `allocation_agent.py`, `confidence_engine.py`, `confidence_fusion.py`, `risk_management.py`, `evaluation.py`, `contracts.py`, `config_schema.py`.
- [ ] Config files in `configs/` (directory placeholders exist; contents not populated).
- [ ] All unit and integration tests for CA-MARL modules.
- [ ] Fixed universe ticker list (Indian large-cap) and as-of selection date.
- [ ] Calibration method final choice (Platt vs. temperature scaling).
- [ ] Walk-forward fold parameters (count, window size, retrain cadence).
- [ ] Transaction cost model (flat bps value).
- [ ] Decision on shared vs. independent PPO training infrastructure across the three agents (ADR-013 leaves this open by design).
- [ ] The confidence-combination function inside `ConfidenceEngine.estimate_raw_confidence()` (how historical accuracy, reward stability, and prediction consistency are combined into one raw score) — flagged as an implementation detail in `INTERFACE_CONTRACTS.md` §4, still open.
- [ ] End-to-end integration of all CA-MARL modules.
- [ ] MARS baseline (stretch goal).

## Blocked

- Nothing is currently blocked on external decisions or documentation ambiguity — the Design Review's Critical and Major findings are resolved, baseline validation is complete, and the remaining open items are CA-MARL implementation-level, to be resolved during Stages 1–5 (`IMPLEMENTATION_ROADMAP.md`).
- **MARS reimplementation** remains a stretch goal, not a committed baseline.

## Technical Debt

- Config directory structure exists as empty placeholder directories (`configs/*.yaml/`) — no YAML files populated yet.
- `finrl/trade.py` still present and functional (should be removed per Stage 5).
- `elegantrl` pinned `--no-deps` in requirements.txt (deviation from upstream, Windows-specific).
- Baseline validation used US equities (DOW 30); CA-MARL target is Indian large-cap — ticker list and data pipeline adaptation pending.

## Known Issues

- **TensorboardCallback `rollout_buffer` KeyError** (cosmetic): `finrl/agents/stablebaselines3/models.py:75` unconditionally accesses `self.locals["rollout_buffer"]`, which does not exist for off-policy algorithms (DDPG, TD3, SAC). The `except BaseException` block catches it gracefully; training continues normally. Does not affect A2C/PPO.
- **TD3/SAC untrained**: timed out on CPU (30-min limit per model). Not required for CA-MARL baseline but would be needed for a full 5-agent ensemble.

## Pending Decisions (implementation-level, to be resolved during CA-MARL development — not architectural, not ambiguous)

| Item | Status |
|---|---|
| Exact ticker list (Indian large-cap) + universe selection as-of date | Open |
| Calibration method: Platt vs. temperature scaling | Open, either acceptable |
| Walk-forward fold count / window sizes / retrain cadence | Open |
| Transaction cost model (flat bps assumed; exact value) | Open |
| Shared vs. independent PPO training infrastructure across the three agents | Open by design (ADR-013) — resolve during Stage 2 |
| Confidence-combination function inside `estimate_raw_confidence()` (weights on historical accuracy / reward stability / prediction consistency) | Open — resolve during Stage 3, record choice in `DECISIONS.md` |
| Whether MARS is attempted as a real baseline or only cited as related work | Open, stretch goal |

---

**Related documents:** [HANDOFF.md](./HANDOFF.md) · [TASKS.md](./TASKS.md) · [DECISIONS.md](../architecture/DECISIONS.md)
