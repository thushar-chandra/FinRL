# SYSTEM_WORKFLOW.md

> Narrative operational workflow — how the system runs at both build-time (implementation order) and run-time (inference sequence), in plain prose. Ties together [ARCHITECTURE.md](./ARCHITECTURE.md)'s diagrams and [IMPLEMENTATION_ROADMAP.md](../planning/IMPLEMENTATION_ROADMAP.md)'s stages into one connected story. This document contains no timeline/day estimates and no team-assignment information (see `DECISIONS.md` ADR-017, ADR-018) — implementation order only.

## Run-Time Workflow (What Happens When the System Produces a Recommendation)

1. Historical market data is retrieved and validated by the **Data Pipeline**.
2. **Feature Engineering** transforms that data into technical indicators, returns, volatility measures, and regime features (bull/bear indicator, volatility regime, trend regime, market-state features) — all engineered features, with regime information treated exactly like any other feature (there is no separate regime-detection step; see ADR-016).
3. The three **specialized reinforcement learning agents** — Market Analysis, Risk Assessment, Portfolio Allocation — each consume the engineered features **only** (no cross-agent inputs — the Portfolio Allocation Agent's observation space is symmetric with the other two, ADR-025) and produce a recommendation, implemented within the FinRL ecosystem and trained via PPO. Whether they share training infrastructure is an implementation detail invisible at this workflow level; from the workflow's perspective, three recommendations come out.
4. Each agent's recommendation, together with signals available from its training process (historical accuracy — via the shared `OutcomeLabelGenerator`, reward stability, prediction consistency), flows into **Confidence Estimation & Calibration** — one combined module (ADR-022) — which computes a raw confidence value per agent, then calibrates it onto a validated, comparable scale and produces calibration diagnostics (ECE, Brier score, reliability diagrams).
5. The three recommendations and their calibrated confidence values flow into **Confidence-Aware Decision Fusion** — a deterministic module (explicitly not PPO, not RL-trained) that first transforms each agent's heterogeneous recommendation into a common `AssetWeightProposal` vector, then computes `Final Allocation = Σ(Proposal × Confidence) / Σ(Confidence)` per asset, and composes the output's `reasoning` and `confidence_summary` fields (ADR-019, ADR-020 — full algorithm in `CONFIDENCE_FUSION.md`).
6. The fused decision passes through the **Risk Management Layer**, which authoritatively enforces long-only, sum-to-one, and exposure-cap constraints regardless of what came before it, and passes `reasoning`/`confidence_summary` through unchanged.
7. The result is the **Final Portfolio Recommendation** — an allocation, reasoning, and a confidence summary, every field traceable to a documented source (ADR-019) — which is what the system actually outputs. Nothing here executes a trade; this is a recommendation object — it does not execute trades (see non-goals in `ARCHITECTURE.md` and `DECISIONS.md` ADR-015).
8. Separately, **Evaluation** (ADR-021) — a fully specified module, `EvaluationEngine` — measures financial performance (Sharpe, Sortino, Max Drawdown, Volatility, Cumulative Return) and calibration quality (ECE, Brier, reliability diagrams, using the same `OutcomeLabelGenerator` as training) against baselines and ablations.

## Build-Time Workflow (Implementation Order — No Timeline Attached)

This mirrors `IMPLEMENTATION_ROADMAP.md`'s staging; see that document for full detail per stage. In order of dependency, not calendar time:

**Stage 1 — Data Foundation:** Data Pipeline → Feature Engineering (including regime features) → walk-forward validation scaffolding → testing (the mandatory feature-engineering leakage test gates everything downstream).

**Stage 2 — Specialized Agents:** Market Analysis Agent → Risk Assessment Agent → Portfolio Allocation Agent, each implemented as a reinforcement learning agent within the FinRL ecosystem, each consuming Feature Engineering output only (no cross-agent inputs, ADR-025), implementation-neutral as to shared vs. independent PPO infrastructure — see `INTERFACE_CONTRACTS.md`.

**Stage 3 — Confidence & Fusion:** Confidence Estimation & Calibration (one combined module, ADR-022) → Confidence-Aware Decision Fusion. This stage carries the project's central research contribution and is where the mandatory calibration-leakage test gates further progress.

**Stage 4 — Risk & Evaluation:** Risk Management Layer → Evaluation → Experiments (baselines, ablations).

**Stage 5 — Integration:** end-to-end integration of all prior stages → bug fixing → documentation finalization.

Each stage depends on the prior one being functionally complete (schema-valid outputs, passing tests) before the next begins — see `IMPLEMENTATION_ROADMAP.md` for per-stage acceptance criteria and `TASKS.md` for the task-level backlog.

## Where to Look for More Detail

- **Structure** (what each module is, how they connect): `ARCHITECTURE.md`.
- **Research rationale** (why each module is designed this way): `MODULE_SPECIFICATIONS.md`.
- **Engineering contract** (classes, schemas, failure cases): `AGENTS.md`, `INTERFACE_CONTRACTS.md`.
- **FinRL reuse specifics**: `FINRL_MAPPING.md`.
- **Implementation staging with acceptance criteria**: `IMPLEMENTATION_ROADMAP.md`, `TASKS.md`.

---

**Related documents:** [ARCHITECTURE.md](./ARCHITECTURE.md) · [IMPLEMENTATION_ROADMAP.md](../planning/IMPLEMENTATION_ROADMAP.md) · [TASKS.md](../planning/TASKS.md) · [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md)
