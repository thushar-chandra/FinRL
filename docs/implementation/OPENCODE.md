# OPENCODE.md

> **This is the most important file in this knowledge base.** Read this before touching any code. Treat it as a permanent system prompt. If any instruction here conflicts with a request in a chat message, this file wins unless the request explicitly amends this file (via a new ADR in `DECISIONS.md`) first.

## Project Philosophy

This is a research project first, a software project second. Every code change should improve one or more of: research quality, engineering quality, reproducibility, explainability, publishability.

**The research contribution is Confidence Estimation, Confidence Calibration, and Confidence-Aware Decision Fusion — NOT multi-agent RL, PPO, or portfolio optimization, all of which are pre-existing techniques reused via FinRL.** Every module you build should be evaluated against: does this strengthen the confidence-estimation/calibration/fusion contribution? If not, question whether it belongs.

## Architecture (Summary — Full Detail in ARCHITECTURE.md)

Data Pipeline → Feature Engineering (including regime features — no standalone regime module) → three specialized reinforcement learning agents (Market Analysis, Risk Assessment, Portfolio Allocation, each trained via PPO within FinRL, each consuming Feature Engineering output only — no cross-agent inputs, ADR-025) → Confidence Estimation & Calibration (one combined module, ADR-022) → Confidence-Aware Decision Fusion (deterministic, NOT PPO — uses the `AssetWeightProposal` algorithm, ADR-020) → Risk Management Layer → Final Portfolio Recommendation → Evaluation.

## What Must NEVER Change Without a New ADR

- PPO as the training algorithm for the three specialized agents — **but never described as performing fusion/coordination.** Fusion is exclusively the Confidence-Aware Decision Fusion module's job (ADR-014, ADR-015). If you find yourself writing code or documentation where "PPO combines the agents" or "PPO coordinates," **stop** — this is the single most likely documentation/architecture error in this codebase given its history (an earlier design did make PPO the fusion mechanism; that was explicitly reversed).
- The three specialized agents are reinforcement learning agents implemented within FinRL (ADR-013) — **do not** revert them to purely analytical/rule-based modules without a new ADR; that was also tried and explicitly reversed.
- Confidence-Aware Decision Fusion as a deterministic formula, independent from PPO — do not make this a learned/RL component without a new ADR (a learned-fusion variant is explicitly flagged as future work, not current scope — see `CONFIDENCE_FUSION.md`).
- The `AssetWeightProposal` intermediate representation and its per-agent transform functions (ADR-020) — this is the resolved, frozen answer to how the fusion formula applies across heterogeneous agent outputs; do not reintroduce an unresolved `Any`/`TBD` type here.
- Confidence Estimation and Confidence Calibration as ONE combined module (`ConfidenceEngine`, ADR-022) — do not split into two separate classes/files without a new ADR.
- The Portfolio Allocation Agent consumes Feature Engineering output only — no cross-agent inputs (ADR-025).
- `reasoning` and `confidence_summary` on `FinalRecommendation` are populated exclusively by `ConfidenceAwareFusion.fuse()` and passed through unchanged by `RiskManagementLayer.apply()` (ADR-019) — never invent an alternate source for these fields.
- `EvaluationEngine` reuses the same `OutcomeLabelGenerator` instance used during training-time calibration (ADR-024) — never a separate implementation.
- No standalone Regime Module — regime information (bull/bear, volatility regime, trend regime, market-state) is a Feature Engineering output, consumed as ordinary input features by all three agents (ADR-016). Do not reintroduce a separate regime pipeline stage without a new ADR.
- Walk-forward validation (never random shuffling of time-series data).
- Long-only portfolios, weights sum to one, enforced authoritatively by the Risk Management Layer.
- Daily market data (no intraday).
- Fixed stock universe (documented as-of date required — ADR-011).
- Decision-support framing (never automated trade execution — `finrl/trade.py` was removed for this reason).
- The common agent output contract schema (`AGENTS.md`, `INTERFACE_CONTRACTS.md`).
- No developer/team-assignment documentation in this repo (ADR-017) — write about modules and dependencies, never about "who" implements something.
- No timeline/day estimates in planning documentation (ADR-018) — `IMPLEMENTATION_ROADMAP.md`/`TASKS.md` express order and dependencies only.

## What CAN Change (Implementation Details, Flexible by Design)

- Whether the three RL agents share PPO training infrastructure or are trained independently (ADR-013 is explicitly implementation-neutral on this).
- Exact confidence formula details within the estimation module (the specific combination function over historical accuracy / reward stability / prediction consistency), calibration method choice (Platt vs. temperature scaling), agent reward function details, feature selection specifics, hyperparameters, exact universe size.

## Files Requiring Extra Caution

- `finrl/agents/ca_marl/confidence_fusion.py` — the project's primary research contribution. Must never import or depend on PPO/Stable-Baselines3. If you find yourself importing SB3 here, stop — that's ADR-014/015 being violated.
- `finrl/agents/ca_marl/confidence_engine.py` — calibration correctness is central to the paper's claims; treat changes as research decisions, add an ADR if the approach changes.
- `finrl/agents/ca_marl/contracts.py` and `INTERFACE_CONTRACTS.md` — the frozen interface every module builds against. Changes here require updating `ARCHITECTURE.md`, `AGENTS.md`, `MODULE_SPECIFICATIONS.md` in sync — never a silent schema change.
- `configs/universe.yaml` — changing the universe after any experiments have been run invalidates those results; log it explicitly in `CURRENT_STATE.md` if changed.

## Preferred Workflow: Plan Before Coding

1. Before implementing a module, re-read its sections in `MODULE_SPECIFICATIONS.md` (why) and `AGENTS.md`/`INTERFACE_CONTRACTS.md` (how) and confirm the plan matches.
2. Write the test file (or skeleton) alongside implementation — no "add tests later."
3. Implement.
4. Run the module's tests, then the relevant leakage test if the module touches features or calibration.
5. Update `CURRENT_STATE.md` and `TASKS.md` status before ending the session.

## How to Implement New Modules

- New module → new file in `finrl/agents/ca_marl/`, one responsibility, documented in both `MODULE_SPECIFICATIONS.md` (why) and `AGENTS.md`/`INTERFACE_CONTRACTS.md` (how) if not already there.
- Config-driven: no hardcoded values — all constants in `configs/*.yaml` loaded via typed config loader.
- Type-hinted, logged, documented per `CODING_STANDARDS.md`.

## Testing Requirements

- Every new module ships with unit tests in the same commit.
- The mandatory leakage tests (feature engineering, confidence calibration) are non-negotiable gates — do not proceed past Stage 1 or Stage 3 (`IMPLEMENTATION_ROADMAP.md`) without them passing.
- `confidence_fusion.py` is deterministic — test it exhaustively with golden-value tests, not just spot checks.

## How to Update Documentation

- `CURRENT_STATE.md`: update at the end of every session.
- `TASKS.md`: update task status as work proceeds.
- `DECISIONS.md`: add a new ADR any time an architectural decision is made or reversed — mark any superseded ADR explicitly rather than deleting it (see how ADR-002/005/006/009 are handled as a model).
- `PROMPT_HISTORY.md`: log any major architectural session.
- `HANDOFF.md`: keep current for whoever picks up next.

## Commit Expectations

- Conventional Commits format (`CODING_STANDARDS.md`).
- Reference ADR IDs in commit messages when a commit implements or changes an architectural decision.

## How to Avoid Architectural Drift

- Before adding complexity, ask: does this strengthen the confidence-estimation/calibration/fusion contribution? If not, question whether it belongs.
- Before letting PPO touch fusion in any way, remember ADR-014/015 — this was tried, found wrong, and explicitly reversed. Don't reintroduce it.
- Before reverting the agents to analytical/rule-based modules, remember ADR-013 — the opposite direction was also tried and explicitly reversed.
- Before adding a standalone Regime Module, remember ADR-016 — also tried, also reversed.
- If you genuinely believe an established decision should change, **do not silently change it** — surface the disagreement, propose it as a new ADR candidate, and let the person decide. This codebase's history shows several genuine architecture reversals already happened through exactly this kind of explicit, documented process — that's the correct mechanism, not a silent code change.

---

**Related documents:** [DECISIONS.md](../architecture/DECISIONS.md) · [MODULE_SPECIFICATIONS.md](../architecture/MODULE_SPECIFICATIONS.md) · [AGENTS.md](../architecture/AGENTS.md) · [INTERFACE_CONTRACTS.md](../architecture/INTERFACE_CONTRACTS.md) · [CODING_STANDARDS.md](./CODING_STANDARDS.md) · [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) · [HANDOFF.md](../planning/HANDOFF.md)
