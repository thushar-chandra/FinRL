# PROMPT_HISTORY.md

> Log of every major architectural prompt/session and the decisions that came out of it. Purpose: when multiple AI tools (Claude, OpenCode, Copilot) touch this project over days/weeks, this file prevents one tool from undoing or reintroducing a design another tool's session already resolved. Append new entries at the bottom; never edit past entries except to fix factual errors (note the correction explicitly if you do).

---

### Entry 1 — Project Foundation
**Session:** Initial project definition.
**Input:** Foundation document (research problem, contribution framing, non-goals), Architecture document (six-module pipeline: Data Pipeline, Feature Engineering, three agents, Confidence Engine, PPO Coordinator), Research Decisions document (ADR-style rationale for RL domain choice, three-agent decomposition, PPO choice, FinRL usage, daily data, long-only, fixed universe, walk-forward validation, explainability, decision-support framing).
**Outcome:** established the "what should never change" / "what can change" split later carried into `DECISIONS.md` and `OPENCODE.md`.

### Entry 2 — First Supervisor Review (10-point critical review)
**Session:** Requested a research-supervisor-style review: one-page summary, architecture, data flow, module responsibilities, assumptions, missing engineering decisions, reviewer criticisms, technical risks, ambiguities, recommendations.
**Key findings:** confidence was never formally defined; ambiguity over whether sub-agents are RL-trained or rule-based; no transaction cost model; no calibration evaluation plan; no explainability mechanism named; baseline reimplementation risk (DeepTrader/MARS) flagged early.
**Outcome:** produced `CA-MARL_Research_Supervisor_Review.md` (external artifact, not part of this docs/ set, but its findings are folded into `DECISIONS.md` and `PROJECT_CONTEXT.md`).

### Entry 3 — First-Principles Architecture Redesign (10-question deep review)
**Session:** Explicit instruction to redesign from first principles if a stronger architecture existed, not to preserve the original design by default. Ten specific questions asked: confidence definition, whether sub-agents are RL agents, what PPO should learn, how confidence integrates into PPO, how confidence is computed, whether the system is genuinely MARL, whether novelty is sufficient, assumption audit, architecture redesign, and IEEE reviewer criticisms + solutions.
**Critical finding:** MARS (Chen et al., AAAI 2026) is close prior art — a heterogeneous multi-agent RL ensemble with a meta-controller dynamically reweighting agent trust by regime. This single finding reshaped the rest of the review.
**Decisions made (now recorded as ADRs in `DECISIONS.md`):**
- ADR-002: sub-agents reclassified as analytical/statistical modules, not independently RL-trained.
- ADR-003: confidence defined as regime-conditioned historical track record, calibrated via Platt/temperature scaling.
- ADR-005: PPO's action space narrowed to a soft trust-weight simplex over 3 agents, not raw allocation.
- ADR-006: confidence integrated as an observation feature (MVP), with explicit-gating as a future upgrade path.
- ADR-007/ADR-008: novelty re-centered on calibrated, validated confidence rather than multi-agent architecture sophistication; terminology handling for "Multi-Agent RL" flagged as needing resolution before paper submission.
- ADR-009: Regime/Context module added to the architecture.
**Outcome:** produced `CA-MARL_Architecture_Redesign_Review.md` (external artifact); its conclusions are the current architecture baseline reflected throughout this `docs/` set.

### Entry 4 — Repository Evaluation for 5-Day Engineering Sprint
**Session:** New context introduced — a hard 5-day timeline, solo responsibility for Modules 1–5 (a teammate handles Module 6/PPO Coordinator). Requested: search and score 10 GitHub repositories against the architecture, recommend top 3 with KEEP/MODIFY/REMOVE/BUILD guidance.
**Key findings:** no repository matches the confidence-estimation layer (expected — that's the novel contribution). FinRL (AI4Finance-Foundation/FinRL) was the closest architecture match overall (data pipeline, technical indicators, multi-asset `PortfolioOptimizationEnv`, native Stable-Baselines3 integration). PyPortfolioOpt was the best fit specifically for the Allocation Agent's optimizer. Qlib was powerful but too heavy a learning curve for 5 days. TensorTrade's action-scheme model didn't map cleanly to multi-asset weight vectors.
**Decision made:** ADR-010 — fork FinRL as the primary foundation; use PyPortfolioOpt as a pip dependency (not a fork) for the Allocation Agent; optionally use stockstats for feature-engineering acceleration.
**Outcome:** produced `CA-MARL_Repository_Evaluation.md` (external artifact); its conclusions are reflected in `MIGRATION_PLAN.md` and `DIRECTORY_STRUCTURE.md`.

### Entry 5 — Full Engineering Documentation Knowledge Base (this session)
**Session:** Requested generation of a complete `docs/` knowledge base (18 files: `PROJECT_CONTEXT.md` through this file) to serve as the single source of truth for an AI coding agent (OpenCode) and any human/AI collaborator, synthesizing Entries 1–4 above without contradiction.
**Outcome:** this documentation set. No new architectural decisions were made in this session — the goal was consolidation and cross-referencing, not redesign. Open items carried forward unresolved (see `CURRENT_STATE.md` §Pending Decisions): exact universe ticker list/date, calibration method final pick, walk-forward fold parameters, PPO reward coefficients, final terminology decision for the paper, and whether MARS is attempted as a real baseline or remains related-work-only.

### Entry 6 — Architecture Finalization (First Pass)
**Session:** New source material introduced (Team Roles & Study Guide, project presentation/PPT) establishing a "finalized architecture" declared as the single source of truth, with instructions not to redesign further. This reversed three specific decisions from Entry 3: sub-agents became reinforcement learning agents again (not analytical modules), and decision fusion became a separate deterministic formula-based module explicitly independent from PPO (rather than PPO itself performing fusion).
**Key finding surfaced during review:** this reversal actually resolves a tension Entry 3 couldn't cleanly close — because the three agents are now genuinely independently RL-trained, the system legitimately is Multi-Agent RL, and the confidence layer stands alone as the clearly-scoped novel contribution rather than overlapping with an "is this really MARL?" question.
**Outcome:** produced a Documentation Audit, Architecture Consistency Report, and Updated Documentation Plan (per explicit instruction to audit before editing), flagging four open questions rather than assuming answers: Regime Module status, timeline reconciliation, team-role split, and `MODULE_SPECIFICATIONS.md`/`AGENTS.md` overlap. No files were edited in this session pending approval.

### Entry 7 — Architecture Finalization (Resolved) and Full Documentation Update
**Session:** All four open questions from Entry 6 resolved by explicit instruction: (1) no standalone Regime Module — regime signals fold into Feature Engineering; (2) RL agent implementation described in implementation-neutral language ("three specialized reinforcement learning agents implemented within the FinRL ecosystem"), with shared PPO training infrastructure explicitly permitted rather than mandating independent pipelines; (3) PPO's scope reconfirmed as training-only, never fusion; (4) all developer/team-assignment documentation removed from the repository — the Team Roles Guide informs module responsibilities only; (5) all timeline/day estimates removed from planning documentation, replaced with implementation order only; (6) both `MODULE_SPECIFICATIONS.md` (research-facing) and `AGENTS.md` (engineering-facing) kept, cross-referenced, de-duplicated; (7) new `INTERFACE_CONTRACTS.md` created as the concrete implementation contract for OpenCode.
**Decisions recorded:** ADR-013 (RL agents, implementation-neutral), ADR-014 (deterministic fusion formula, independent from PPO), ADR-015 (PPO scope clarification), ADR-016 (Regime folded into Feature Engineering, supersedes ADR-009), ADR-017 (no team-assignment documentation), ADR-018 (no timeline/day estimates). ADR-002, ADR-005, and ADR-006 marked superseded (not deleted) per standard ADR practice.
**Outcome:** every document in the `docs/` knowledge base updated for full consistency with the frozen architecture: `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `AGENTS.md`, `MIGRATION_PLAN.md`, `DIRECTORY_STRUCTURE.md`, `IMPLEMENTATION_ROADMAP.md`, `TASKS.md`, `README.md`, `OPENCODE.md`, `RESEARCH_MAPPING.md`, `EXPERIMENT_PLAN.md`, `CONFIGURATION.md`, `TESTING_STRATEGY.md`, `CODING_STANDARDS.md`, `CURRENT_STATE.md`, `HANDOFF.md` all updated; new documents `MODULE_SPECIFICATIONS.md`, `CONFIDENCE_FUSION.md`, `INTERFACE_CONTRACTS.md`, `FINRL_MAPPING.md`, `SYSTEM_WORKFLOW.md` created. The architecture is now frozen and internally consistent across all 22 documents. Remaining open items are implementation-level only (see `CURRENT_STATE.md`), not architectural.

### Entry 8 — Independent Design Review and Full Resolution
**Session (Part 1 — Review):** An independent, strict pre-implementation design review was requested across all 22 documents, explicitly not fixing anything, only reporting. Findings: 4 Critical issues (undefined `reasoning`/`confidence_summary` data flow between `FusedDecision` and `FinalRecommendation`; the fusion formula mathematically undefined across the three agents' heterogeneous output types, with `FusedDecision.final_allocation` typed `Any`/"TBD"; Evaluation treated as a first-class pipeline stage everywhere but formally specified nowhere; Confidence Estimation and Confidence Calibration described as one module in some documents and two sequential stages in `ARCHITECTURE.md`) and 8 Major issues (missing Risk Management Layer section in `AGENTS.md`; "Confidence Engine" persisting as an undefined alternate name; "Final Recommendation" vs. "Final Portfolio Recommendation" inconsistency, including within `ARCHITECTURE.md` itself; no class-to-file binding; "prediction consistency" never operationalized; outcome-label ownership/timing/leakage-prevention unstated; `FINRL_MAPPING.md` missing dependency information; the Portfolio Allocation Agent's optional cross-agent dependency left unresolved with an unaddressed training-order risk). Verdict: "Ready after Major Changes," 5/10 overall.
**Session (Part 2 — Resolution):** Every Critical and Major finding was resolved as a concrete engineering decision, not merely acknowledged:
- **C1** resolved: `FusedDecision` expanded with `reasoning`/`confidence_summary`, both populated by `ConfidenceAwareFusion.fuse()` via a deterministic composition algorithm, passed through unchanged by `RiskManagementLayer.apply()`.
- **C2** resolved: a common intermediate representation, `AssetWeightProposal`, plus three deterministic per-agent transform functions, plus a proven sum-to-1 guarantee for the fusion formula applied to these transformed vectors, plus a full worked numeric example. All `Any`/`TBD` typing removed from `FusedDecision.final_allocation`; confidence committed to a scalar per agent (not a per-asset dict).
- **C3** resolved: a formal `EvaluationEngine` module specified consistently across `MODULE_SPECIFICATIONS.md`, `AGENTS.md`, and `INTERFACE_CONTRACTS.md`, with defined inputs, outputs, methods, and failure cases.
- **C4** resolved: Confidence Estimation and Confidence Calibration confirmed as **one** combined module; `ARCHITECTURE.md`'s diagrams and system overview corrected to match the other four documents (rather than splitting those four documents to match the outlier).
- **M1–M8** resolved: `AGENTS.md` §6 (Risk Management Layer) added; "Confidence Engine" retired everywhere in favor of "Confidence Estimation & Calibration"; "Final Portfolio Recommendation" canonicalized as the prose term with `FinalRecommendation` as the documented class-name shorthand; a Class → File → Purpose → Dependencies map added to `INTERFACE_CONTRACTS.md`; Prediction Consistency fully operationalized (k-sample perturbation procedure, per-output-type formula); a single `OutcomeLabelGenerator`, owned by the Confidence Estimation & Calibration module and reused by Evaluation, with a precise, checkable leakage-eligibility rule; `FINRL_MAPPING.md` gained Dependencies/Execution Order/Downstream Consumers columns; the Portfolio Allocation Agent's cross-agent dependency was explicitly rejected (it consumes Feature Engineering output only, symmetric with the other two agents), removing a previously undocumented training-stability risk.
**Decisions recorded:** ADR-019 through ADR-026.
**Outcome:** `DECISIONS.md`, `ARCHITECTURE.md`, `AGENTS.md`, `MODULE_SPECIFICATIONS.md`, `INTERFACE_CONTRACTS.md`, `CONFIDENCE_FUSION.md`, `DIRECTORY_STRUCTURE.md`, `FINRL_MAPPING.md`, `SYSTEM_WORKFLOW.md`, `TESTING_STRATEGY.md`, `TASKS.md`, `IMPLEMENTATION_ROADMAP.md`, `EXPERIMENT_PLAN.md`, `RESEARCH_MAPPING.md`, `CURRENT_STATE.md`, `HANDOFF.md` all updated for full consistency. No new modules were introduced and no architectural decision was reversed — every change resolved a previously acknowledged ambiguity with a concrete answer.

---

## Format for Future Entries

```
### Entry N — <short title>
**Session:** <what was asked>
**Key findings / decisions:** <what changed, with ADR references if applicable>
**Outcome:** <artifact produced, files updated>
```

**Rule:** if a future session proposes reversing a decision recorded here (e.g., "make the sub-agents analytical after all," "let PPO handle fusion again"), that proposal must be evaluated against the reasoning in the relevant ADR (`DECISIONS.md`) explicitly, not simply implemented — see `OPENCODE.md` §"How to avoid architectural drift." This project's history shows genuine architecture reversals have happened more than once already (Entry 3 vs. Entry 6/7) — the mechanism that keeps this manageable is explicit, documented ADRs, not silent code changes.

---

**Related documents:** [DECISIONS.md](./DECISIONS.md) · [OPENCODE.md](./OPENCODE.md) · [CURRENT_STATE.md](./CURRENT_STATE.md)
