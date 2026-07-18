# DECISIONS.md — Architecture Decision Record (ADR)

> Every important decision, in order made. Do not silently reverse any of these without adding a new ADR explaining why — see [OPENCODE.md](./OPENCODE.md) §"How to avoid architectural drift."

---

### ADR-001 — Financial portfolio management as the RL problem domain
- **Problem:** choose a research domain that genuinely fits sequential decision-making under uncertainty.
- **Options considered:** portfolio management; single-asset trading; other sequential-decision domains.
- **Chosen:** portfolio management (long-only, fixed universe, daily data).
- **Reasoning:** decisions are sequential, actions affect future rewards, markets are dynamic and uncertain — naturally fits RL, and no single "correct" answer, unlike supervised learning.
- **Trade-offs:** none significant at this level; this was the founding premise, not contested in review.
- **Future implications:** all downstream decisions (long-only, walk-forward, fixed universe) inherit from this.

### ADR-002 — Sub-agents are analytical/statistical modules, NOT independently RL-trained
> **⚠ SUPERSEDED by ADR-013.** Retained for audit-trail purposes only — do not implement against this entry.

- **Problem:** are Market/Risk/Allocation "agents" full RL policies, analytical modules, or something else?
- **Options considered:** (A) all three as independently trained RL agents; (B) all three as analytical/statistical modules with only the coordinator RL-trained; (C) hybrid (lightweight learned models, still not deep RL).
- **Chosen:** (B), with (C) as a natural evolution path.
- **Reasoning:** removes the largest engineering/stability risk (3× RL training complexity, non-stationary joint training, small-sample instability given daily data over a bounded universe); concentrates the actual RL research content in the coordinator, where the paper's real contribution lives; makes confidence computation via historical track record well-defined (no need for per-agent ensemble/Bayesian machinery).
- **Trade-offs:** the system is not, technically, "Multi-Agent RL" in the strict literature sense — see ADR-006 for how this is handled.
- **Future implications:** ensemble-disagreement or Bayesian confidence methods (ADR-003 alternatives) are only in scope if sub-agents are later upgraded to learned ensembles — explicitly future work, not current scope.

### ADR-003 — Confidence definition: regime-conditioned historical track record, calibrated
- **Problem:** "confidence" was originally left undefined by design (appropriate pre-experimentation), but implementation requires at least a computable v1 definition.
- **Options considered:** (a) calibrated probability of correctness — the target property, not a computation method by itself; (b) ensemble disagreement/deep ensembles; (c) historical track record (frequentist reliability); (d) predictive/action-distribution entropy; (e) reward/value stability.
- **Chosen:** (c) as the computation method, targeting property (a) via post-hoc calibration (Platt or temperature scaling).
- **Reasoning:** simplest to implement given ADR-002 (no ensemble architecture needed per agent); gives calibration a concrete, computable ground-truth label per agent type (see `MODULE_SPECIFICATIONS.md` §4); avoids conflating signal strength with reliability (the flaw in entropy-based confidence for rule-based agents).
- **Trade-offs:** requires careful data-leakage handling — calibration must be fit only on training-window data (see `ARCHITECTURE.md` §5, `TESTING_STRATEGY.md`).
- **Future implications:** ensemble-disagreement (b) and Bayesian uncertainty (future methods) are the documented v2 upgrade path if sub-agents become learned ensembles.

### ADR-004 — PPO (via Stable-Baselines3), not a novel RL algorithm
- **Problem:** which RL algorithm coordinates fusion?
- **Chosen:** PPO via Stable-Baselines3.
- **Reasoning:** stable, well-understood, widely validated in portfolio RL research; the project's novelty is confidence estimation and fusion, not algorithm design (carried over unchanged from the original Research Decisions document).
- **Trade-offs:** none significant; do not revisit without overwhelming justification (per the original Research Decisions document's explicit instruction).

### ADR-005 — PPO's action space: soft trust-weight simplex over 3 agents, not raw asset allocation
> **⚠ SUPERSEDED by ADR-014.** PPO is no longer the fusion mechanism at all; retained for audit-trail purposes only.

- **Problem:** what exactly should PPO learn — direct allocation, hard agent selection, soft gating, dynamic fusion, or residual correction?
- **Options considered:** all five, evaluated in the architecture redesign review.
- **Chosen:** soft gating/dynamic fusion — PPO outputs a 3-way trust-weight vector over Market/Risk/Allocation agent outputs, conditioned on calibrated confidence and regime.
- **Reasoning:** direct allocation bypasses the agent decomposition (defeats the project's purpose); hard selection loses information and is awkward for PPO's continuous-action strengths; the trust-weight simplex keeps PPO's action space small, materially improving sample efficiency given the small, non-stationary daily-data regime (a flagged risk in `DECISIONS.md` Assumption Audit below).
- **Trade-offs:** slightly less expressive than direct allocation, by design — this is the point.
- **Future implications:** upgrade path to an explicit gating sub-network within the policy architecture (mechanistically tighter integration of confidence) is documented as a stronger future version; observation-based integration (ADR also covers this, see below) is the MVP.

### ADR-006 — Confidence integrated as an observation feature, not a reward modifier
> **⚠ SUPERSEDED by ADR-014.** Confidence no longer feeds a PPO observation at all — fusion is a separate, non-RL, deterministic module. Retained for audit-trail purposes only.

- **Problem:** how should calibrated confidence enter PPO's learning process?
- **Options considered:** part of observation; modify reward; modify action space; modify policy architecture (explicit gate); keep external/pre-blended.
- **Chosen:** part of the observation (MVP), with an explicit-gating architecture as a documented stronger future version.
- **Reasoning:** modifying reward risks a self-referential loop (PPO could be rewarded for trusting its own possibly-miscalibrated belief rather than for real outcomes) — rejected as a methodological flaw. Keeping confidence fully external risks making "confidence-aware" cosmetic (PPO never demonstrably uses it) — mitigated by the mandatory shuffled-confidence ablation (`EXPERIMENT_PLAN.md`).
- **Trade-offs:** requires the ablation to prove confidence is load-bearing, not just present.
- **Future implications:** codebase should keep the gating computation as an isolated, swappable module so upgrading to explicit-gate architecture later is a module swap, not a rewrite.

### ADR-007 — Terminology: "Multi-Agent RL" retained in the project name as an organizational metaphor, not a strict technical claim
> **Update (post ADR-013):** this ADR's core tension is resolved, not just reframed. Because the three agents are now genuinely reinforcement-learning agents (implementation-neutral as to shared vs. independent training infrastructure — see ADR-013), "Multi-Agent RL" is an accurate technical description of the agent layer, not merely an organizational metaphor. The remaining nuance — that decision fusion itself is a deterministic formula, not RL-trained — should still be stated plainly in the paper (PPO trains the agents; it does not perform fusion), but this is a scoping clarification, not a terminology-accuracy problem. The options below are kept for audit-trail context.

- **Problem:** given ADR-002, is calling this system "Multi-Agent Reinforcement Learning" accurate?
- **Options considered:** (1) rename to something precise like "Confidence-Aware RL for Hierarchical Portfolio Decision Fusion"; (2) keep "multi-agent" as an organizational/systems description, explicitly stating only the coordination layer is RL-trained.
- **Chosen:** for the codebase and working project name, keep CA-MARL for continuity; **for the paper**, recommendation is (1) or an explicit early disclosure per (2) — final call belongs to the paper-writing phase, not frozen here.
- **Reasoning:** an IEEE-reviewer-level audience familiar with MARS (which is a true multi-agent RL system) will notice the mismatch if undisclosed; precise framing is rewarded by reviewers more than a catchier but imprecise title is.
- **Trade-offs:** less "sophisticated"-sounding title; more defensible claim.
- **Future implications:** **PENDING** — must be finalized before paper submission; tracked in `CURRENT_STATE.md` Pending Decisions.

### ADR-008 — Novelty re-centered on calibrated, validated confidence, not on multi-agent architecture sophistication
- **Problem:** MARS (Chen et al., AAAI 2026) already implements a heterogeneous multi-agent RL ensemble with a meta-controller that dynamically reweights agent trust by regime — closely overlapping the original framing.
- **Chosen:** re-center the contribution claim on explicit, calibrated, human-facing confidence (ECE/Brier/reliability diagrams, shuffled-confidence ablation) as the checkable, falsifiable novelty, with decision-support/explainability framing (vs. MARS's/DeepTrader's autonomous-trading framing) as the secondary differentiator.
- **Reasoning:** MARS's meta-controller's trust-reweighting is opaque/implicit; this project's confidence is explicit, validated, and surfaced to the user — a concrete, checkable difference a reviewer can verify against evidence, unlike "our system is also multi-agent."
- **Trade-offs:** narrower claim than originally framed; also more honest and more defensible.
- **Future implications:** MARS must appear as related work; consider it a stretch-goal baseline (see `EXPERIMENT_PLAN.md`) given 2026-publication reproduction-fidelity risk.

### ADR-009 — Regime/Context module added to the architecture
> **⚠ SUPERSEDED by ADR-016.** Regime signals are now engineered features within Feature Engineering, not a standalone pipeline module. Retained for audit-trail purposes only.

- **Problem:** the original architecture had no explicit market-regime conditioning.
- **Chosen:** add a Regime Module (volatility regime + trend regime) feeding all three agents, the Confidence Engine, and the PPO Coordinator.
- **Reasoning:** both DeepTrader and MARS attribute much of their performance gains to conditioning on market state; its absence was a gap relative to the very baselines this project compares against.
- **Trade-offs:** one more module to build and test within the 5-day sprint (Milestone 3, `IMPLEMENTATION_ROADMAP.md`).
- **Future implications:** v1 is simple threshold/quantile-based; HMM/clustering-based regime detection is future work.

### ADR-010 — Base repository: fork FinRL; PyPortfolioOpt as a library dependency, not a fork
- **Problem:** minimize implementation effort across Modules 1–5 within a 5-day timeline.
- **Options considered:** 10 repositories evaluated (FinRL, FinRL-Meta, ElegantRL, TensorTrade, gym-anytrading, PyPortfolioOpt, Qlib, Riskfolio-Lib, cvxportfolio, stockstats).
- **Chosen:** fork FinRL for the data pipeline/feature scaffold/portfolio environment shell; use PyPortfolioOpt as a pip dependency for the Allocation Agent's optimizer; optionally use stockstats to accelerate Module 2.
- **Reasoning:** FinRL had the closest architecture match of anything surveyed; Qlib was more powerful but too heavy a learning curve for 5 days; TensorTrade's action-scheme model doesn't map cleanly to multi-asset weight vectors.
- **Trade-offs:** FinRL's own agent-training patterns (independent DRL agents) must be explicitly replaced per ADR-002, not inherited.
- **Future implications:** see `MIGRATION_PLAN.md` for the full folder-by-folder decision set.

### ADR-011 — Fixed universe, selection date must be documented
- **Problem:** using "current" (2026) Indian large-cap rankings to define a universe tested over a historical window risks hindsight/survivorship bias.
- **Chosen:** fixed universe remains the design (unchanged from original Research Decisions document), but the **selection methodology and as-of date must be explicitly documented** in `configs/universe.yaml` and disclosed in the paper.
- **Reasoning:** avoids a straightforward, easily-caught reviewer objection at near-zero engineering cost.
- **Status:** **PENDING** — exact ticker list and date not yet finalized (see `CURRENT_STATE.md`).

### ADR-012 — Transaction costs added to reward and evaluation
- **Problem:** original spec had no transaction cost / slippage model; backtests without costs are a near-automatic reviewer objection.
- **Chosen:** add a simple flat/bps transaction-cost term to both the PPO reward and the backtest evaluation.
- **Reasoning:** cheap to add now, expensive to retrofit after results exist.
- **Status:** exact bps value **PENDING** (affects reward function — see `TASKS.md` T-019).

### ADR-013 — Sub-agents are reinforcement learning agents implemented within FinRL (implementation-neutral as to shared vs. independent training)
- **Problem:** ADR-002 rejected RL-trained sub-agents to limit engineering risk. Finalized architecture (per the Team Roles & Study Guide and project presentation) requires the three specialized agents to be reinforcement learning agents.
- **Chosen:** Market Analysis, Risk Assessment, and Portfolio Allocation are each **reinforcement learning agents implemented within the FinRL ecosystem**, trained via Stable-Baselines3 PPO. The architecture does **not** mandate that each agent have a fully independent PPO training pipeline — shared PPO training infrastructure (e.g., a common training utility, shared network components, or a multi-task training loop) is an allowed implementation choice. Documentation must use implementation-neutral phrasing ("three specialized reinforcement learning agents implemented within the FinRL ecosystem") rather than prescriptive phrasing ("three independently PPO-trained agents") unless a future implementation-analysis session explicitly requires independence.
- **Reasoning:** this is now an architectural requirement, not a proposal to be re-litigated; wording is kept neutral specifically so the implementation phase retains freedom to choose the most efficient training arrangement without triggering another architecture-consistency review.
- **Trade-offs:** confidence computation (ADR-003) needs revisiting in light of this — reward stability and prediction consistency (both natural RL-agent signals) are now legitimate, available confidence inputs alongside historical track record, per the Confidence Estimation & Calibration module's stated input list.
- **Future implications:** all documents should describe agent training with the neutral phrasing above; implementation-level decisions about shared vs. independent PPO infrastructure belong in `INTERFACE_CONTRACTS.md`/`FINRL_MAPPING.md`, not in `ARCHITECTURE.md`.

### ADR-014 — Decision fusion is a deterministic confidence-weighted formula, exclusively separate from PPO
- **Problem:** ADR-005/006 made PPO itself the fusion mechanism (a learned trust-weight simplex). Finalized architecture requires fusion to be independent of PPO.
- **Chosen:** Confidence-Aware Decision Fusion is a dedicated, non-RL module. Default formulation: `Final Decision = Σ(Recommendation × Confidence) / Σ(Confidence)`. PPO is never described as combining the agents; it trains the agents (ADR-013), full stop.
- **Reasoning:** per explicit instruction, this separation is treated as a fixed architectural requirement, not a design proposal. It also has the effect of making the project's central contribution (confidence-aware fusion) independently inspectable and testable, decoupled from RL training variance.
- **Trade-offs:** a fixed formula is simpler and more transparent but less expressive than a learned fusion policy; this is accepted as the intended design, not a gap.
- **Future implications:** `CONFIDENCE_FUSION.md` is the authoritative document for this module. A learned-fusion variant may be noted as future work in that document but is explicitly out of current scope.

### ADR-015 — PPO's scope clarified: training algorithm for the RL agents, not a system-level coordinator
- **Problem:** earlier documentation described a "PPO Coordinator" as a distinct pipeline stage performing fusion (see superseded ADR-005/006). This module no longer exists in that form.
- **Chosen:** PPO (via Stable-Baselines3) is the training algorithm used by the three specialized RL agents (ADR-013). There is no separate "PPO Coordinator" module. Any remaining references to a "PPO Coordinator" in older documents refer to what is now the Confidence-Aware Decision Fusion module (ADR-014), which is explicitly NOT PPO-based, and must be corrected wherever found.
- **Reasoning:** avoids the recurring documentation error of implying PPO performs coordination/fusion.
- **Future implications:** all documents must use "Confidence-Aware Decision Fusion module" for the fusion stage and reserve "PPO" / "the RL agents" language strictly for the training of Market/Risk/Allocation agents.

### ADR-016 — Regime signals are Feature Engineering outputs, not a standalone module
- **Problem:** ADR-009 added a standalone Regime/Context module. Finalized architecture does not include one.
- **Chosen:** regime information (bull/bear market indicators, volatility regime, trend regime, market-state features) is engineered directly within Feature Engineering and made available as input features to all three agents, like any other engineered feature.
- **Reasoning:** per explicit instruction; also reduces the pipeline to exactly the stages named in the finalized architecture, with no unlisted stages.
- **Trade-offs:** none material — the underlying motivation for regime-awareness (from DeepTrader/MARS precedent) is fully preserved, just implemented as features rather than a pipeline stage.
- **Future implications:** `MODULE_SPECIFICATIONS.md` and `AGENTS.md` document regime features under Feature Engineering / as inputs to each agent, not as a separate module section.

### ADR-017 — No developer/team-assignment documentation in this repository
- **Problem:** earlier documents (`TASKS.md`, `CURRENT_STATE.md`, `HANDOFF.md`, `PROJECT_CONTEXT.md`) assigned specific modules to "you" vs. "a teammate."
- **Chosen:** the Team Roles Guide is used only to define module responsibilities (already reflected in `AGENTS.md`/`MODULE_SPECIFICATIONS.md`); it is not used to assign implementation ownership. This repository documents one complete engineering implementation with no per-person assignment.
- **Reasoning:** per explicit instruction.
- **Future implications:** all task/status/handoff documentation is written in terms of module dependencies and completion state, never "who" is doing it.

### ADR-018 — No fixed timeline/day estimates in architectural or planning documentation
- **Problem:** earlier `IMPLEMENTATION_ROADMAP.md`/`TASKS.md` assumed a fixed 5-day sprint with day-by-day milestone assignments.
- **Chosen:** planning documentation expresses **implementation order and dependencies only** — no day counts, no sprint structure, no duration estimates.
- **Reasoning:** per explicit instruction.
- **Future implications:** if a real timeline is needed later (e.g., for actual scheduling), it should be maintained outside this documentation set or added back explicitly as a new, separately-flagged decision — not implied by the architecture docs.

### ADR-019 — `FusedDecision` expanded to carry `reasoning` and `confidence_summary`; composition algorithm defined (resolves Design Review C1)
- **Problem:** `RiskManagementLayer.apply()` needed to produce a `FinalRecommendation` (which requires `reasoning` and `confidence_summary`) from a `FusedDecision` that carried neither field — no document specified where these fields came from.
- **Chosen:** `FusedDecision` is expanded to include `reasoning: str` and `confidence_summary: dict[str, float]`, both populated by the Confidence-Aware Decision Fusion module itself (not the Risk Management Layer). `reasoning` is composed deterministically: each agent's own `reasoning` string, annotated with its calibrated confidence, concatenated in descending-confidence order (exact template in `INTERFACE_CONTRACTS.md` §5). `confidence_summary` is the calibrated confidence dict passed through unchanged from Confidence Calibration's output. The Risk Management Layer passes both fields through to `FinalRecommendation` unchanged — it only transforms/validates `final_allocation`.
- **Reasoning:** keeps a strict single-direction data flow (each stage only adds what it is responsible for) and makes every field on `FinalRecommendation` traceable to a specific upstream computation, per the Design Review's explicit requirement that "no required field may appear by magic."
- **Trade-offs:** none material — this is a data-flow clarification, not a new capability.
- **Future implications:** if `reasoning` composition is ever changed (e.g., to an LLM-generated summary instead of the deterministic template), that is a new ADR, not a quiet change, since `AGENTS.md`/`INTERFACE_CONTRACTS.md`/`CONFIDENCE_FUSION.md` all document the current deterministic algorithm as authoritative.

### ADR-020 — `AssetWeightProposal` intermediate representation and per-agent transform functions defined; confidence committed to scalar-per-agent (resolves Design Review C2)
- **Problem:** the fusion formula `Σ(Recommendation × Confidence) / Σ(Confidence)` was not mathematically defined across the three agents' heterogeneous output types (categorical BUY/SELL/HOLD, a risk score, a weight vector), and `FusedDecision.final_allocation` was typed `Any` with "TBD."
- **Chosen:** define a common intermediate representation, `AssetWeightProposal` (`dict[str, float]`, non-negative, sums to 1.0 within floating-point tolerance), and three deterministic transform functions — one per agent — that convert each agent's native `recommendation` into an `AssetWeightProposal` *before* fusion:
  - Market Analysis: BUY→+1/HOLD→0/SELL→−1 per asset, negative values clipped to 0, renormalized to sum to 1; if all assets are non-positive, fall back to equal-weight across the universe (logged).
  - Risk Assessment: per-asset risk score inverted (`1 / (ε + risk_score)`), renormalized to sum to 1 (lower risk → higher weight).
  - Portfolio Allocation: its native weight-vector output is already this shape; defensively re-clipped (negatives → 0) and renormalized (fallback to equal-weight if the sum is 0, logged).
  Fusion then applies the confidence-weighted average **directly on these three `AssetWeightProposal` vectors**: `FinalAllocation[asset] = Σ_agent(Proposal_agent[asset] × Confidence_agent) / Σ_agent(Confidence_agent)`, per-asset, across all three agents. Since each input vector sums to 1, the weighted average is guaranteed to sum to 1 by construction (proof: `Σ_asset Σ_agent(Proposal_agent[asset] × Confidence_agent) = Σ_agent(Confidence_agent × Σ_asset Proposal_agent[asset]) = Σ_agent(Confidence_agent × 1) = Σ_agent(Confidence_agent)`, so dividing by `Σ_agent(Confidence_agent)` yields a sum of exactly 1). Additionally, `raw_confidence`/`calibrated_confidence` are committed to being a single scalar float per agent (not a per-asset dict) — this was previously left ambiguous (`float | dict[str, float]`) and is now fixed to `float` throughout, since a scalar is sufficient given the outcome-label definitions in `MODULE_SPECIFICATIONS.md` §4 are already per-agent, not per-asset.
- **Reasoning:** this is a concrete, fully specified, deterministic algorithm with no remaining `Any`/`TBD` typing, a proven mathematical property (output always sums to 1), and documented fallback behavior for every degenerate case.
- **Trade-offs:** the transform functions are additional code the Confidence-Aware Decision Fusion module owns (not the agents themselves) — this keeps each agent's public output contract unchanged and confines the heterogeneity-handling complexity to the one module whose job is combining heterogeneous inputs.
- **Future implications:** `CONFIDENCE_FUSION.md` is the authoritative source for the transform functions and the full worked algorithm; `INTERFACE_CONTRACTS.md` §5 mirrors the exact signatures.

### ADR-021 — Evaluation formalized as a module with a concrete class, inputs, outputs, and file location (resolves Design Review C3)
- **Problem:** Evaluation was treated as a first-class pipeline stage everywhere (`ARCHITECTURE.md`, `EXPERIMENT_PLAN.md`, `RESEARCH_MAPPING.md`, `TESTING_STRATEGY.md`) but had no formal specification in `MODULE_SPECIFICATIONS.md`, `AGENTS.md`, or `INTERFACE_CONTRACTS.md`.
- **Chosen:** Evaluation is implemented as `EvaluationEngine` in `finrl/agents/ca_marl/evaluation.py`, with `evaluate_financial()`, `evaluate_calibration()`, `run_ablation()`, `compare_baselines()`, and `generate_report()` methods, consuming a sequence of `FinalRecommendation` objects plus realized market returns plus the same `OutcomeLabelGenerator` used during training (see ADR-024) to ensure calibration is scored against the identical label definitions used to fit it. Full detail: `MODULE_SPECIFICATIONS.md` §7, `AGENTS.md` §7, `INTERFACE_CONTRACTS.md` §7.
- **Reasoning:** closes the single largest implementation-readiness gap identified by the Design Review — every other pipeline stage had at least a partial spec; Evaluation had none.
- **Trade-offs:** none material.
- **Future implications:** any new evaluation metric or ablation type is added as a new method on `EvaluationEngine`, documented in the same three files, not as an ad hoc script outside this contract.

### ADR-022 — Confidence Estimation and Confidence Calibration confirmed as ONE combined module; `ARCHITECTURE.md` corrected to match (resolves Design Review C4)
- **Problem:** `ARCHITECTURE.md`'s System Overview and diagrams showed Confidence Estimation and Confidence Calibration as two separate, sequential pipeline stages, while `AGENTS.md`, `MODULE_SPECIFICATIONS.md`, `INTERFACE_CONTRACTS.md`, and `DIRECTORY_STRUCTURE.md` all treated them as one combined module (`confidence_engine.py`, one class with two methods).
- **Chosen:** **Option A — single module.** "Confidence Estimation & Calibration" is one module, internally performing estimation then calibration as two method calls (`estimate_raw_confidence()` then `calibrate()`) but exposed as a single pipeline stage. `ARCHITECTURE.md` is corrected to match (System Overview, both diagrams, module interaction table all now show one combined stage).
- **Reasoning:** four of five documents already treated this as one module; correcting the one outlier (`ARCHITECTURE.md`) requires far less restructuring than splitting four documents into two modules each, and a single module is functionally sufficient — the two-method-call sequence inside it is a normal internal implementation detail, not a reason to expose two pipeline-level boxes.
- **Trade-offs:** none material.
- **Future implications:** if calibration is ever separated out (e.g., to allow swapping calibration methods without touching estimation code), that would be an internal refactor within `confidence_engine.py`, not a pipeline-level architecture change, and would not require a new ADR unless it changed the module's external interface.

### ADR-023 — Prediction Consistency operationalized (resolves Design Review M5)
- **Problem:** "prediction consistency" was named repeatedly as a confidence-estimation input but never defined operationally, unlike historical accuracy (which has an outcome-label table) or reward stability (which has a stated source).
- **Chosen:** Prediction Consistency measures how stable an agent's recommendation is when evaluated under small perturbations of its input state (a proxy for policy decisiveness/reproducibility, distinct from historical correctness). Computed as: sample the agent's policy on *k* nearby historical states within the same regime bucket as the current state (*k* configurable, `configs/confidence.yaml`); for continuous outputs (risk scores, weights), consistency = `1 − coefficient_of_variation` across the *k* samples; for categorical outputs (BUY/SELL/HOLD), consistency = fraction of the *k* samples agreeing with the modal recommendation. Output is a scalar in [0,1] per agent per timestep, stored in the same rolling per-agent, per-regime-bucket history structure as historical accuracy and reward stability. It is one of three inputs combined into `raw_confidence` before calibration — it is not separately calibrated.
- **Reasoning:** matches the level of concreteness already given to the other two confidence inputs, closing the gap the Design Review identified.
- **Trade-offs:** requires the "nearby historical states within the same regime bucket" sampling procedure to be implemented — a bounded, well-specified piece of new code, not an open-ended research question.
- **Future implications:** full detail lives in `MODULE_SPECIFICATIONS.md` §4; method signature in `INTERFACE_CONTRACTS.md` §4.

### ADR-024 — Outcome Label Generator: ownership, timing, and leakage-prevention rule formalized (resolves Design Review M6)
- **Problem:** `MODULE_SPECIFICATIONS.md` §4 defined *what* an outcome label is per agent type, but no document said *who* computes it, *when*, or exactly how leakage is prevented beyond the general statement "fit calibration on training data only."
- **Chosen:** a single `OutcomeLabelGenerator` component, owned by and located within the Confidence Estimation & Calibration module (`confidence_engine.py`), is the sole implementation of label generation — reused by both training-time track-record accumulation and Evaluation's test-time calibration scoring (never reimplemented separately), guaranteeing training and evaluation use an identical definition of "correct." A label for a recommendation made at time *t* can only be generated once realized market data covering that recommendation's label horizon (*t + N*) is available. **Concrete leakage rule:** a (confidence, label) pair is eligible for calibration fitting in walk-forward fold *F* if and only if `recommendation.timestamp + label_horizon ≤ F.training_window.end`; pairs whose horizon extends past the training window end are excluded from that fold (they become eligible in a later fold once enough time has passed).
- **Reasoning:** this replaces a general leakage-avoidance statement with a precise, checkable rule the mandatory calibration-leakage test (`TESTING_STRATEGY.md` §3b) can be written directly against.
- **Trade-offs:** none material.
- **Future implications:** method signature and full detail: `MODULE_SPECIFICATIONS.md` §4, `INTERFACE_CONTRACTS.md` §4.

### ADR-025 — Portfolio Allocation Agent's cross-agent input dependency explicitly rejected (resolves Design Review M8)
- **Problem:** `AGENTS.md`/`INTERFACE_CONTRACTS.md` had left it optional/undecided whether the Allocation Agent's observation space includes the Market/Risk agents' outputs — an unresolved dependency that, combined with ADR-013's implementation-neutral training infrastructure, risked a moving-target training problem (the Allocation Agent's inputs shifting as the Market/Risk agents' policies simultaneously update) with no documented mitigation.
- **Chosen:** **explicitly rejected.** The Portfolio Allocation Agent consumes only Feature Engineering output (technical indicators, volatility/return features, regime features) — the same input contract as the Market Analysis and Risk Assessment agents, symmetrically. It does **not** take Market or Risk agent outputs as part of its observation space.
- **Reasoning:** removes a real, previously-undocumented training-stability risk at zero architectural cost — the original finalized architecture never mandated cross-agent inputs for the Allocation Agent (it only specified "processed market data" as input, same as the other two agents), so this resolution is, if anything, more faithful to the frozen architecture than the optional dependency had been, not a redesign.
- **Trade-offs:** the Allocation Agent cannot directly condition on the Market Agent's directional view or the Risk Agent's risk estimate at the observation level — but it doesn't need to: that combination happens downstream, explicitly, in Confidence-Aware Decision Fusion (ADR-020), which is the correct place for it, not duplicated inside the Allocation Agent's own policy.
- **Future implications:** `AGENTS.md` §3, `MODULE_SPECIFICATIONS.md` §3, and `INTERFACE_CONTRACTS.md` §3 all updated to remove the optional `market_output`/`risk_output` parameters from the Allocation Agent's `predict()` signature.

### ADR-026 — Terminology and cross-reference canonicalization pass (resolves Design Review M2, M3, M4, M7)
- **Problem:** several naming/cross-reference inconsistencies remained live across documents: "Confidence Engine" used as an undefined alternate name (M2); "Final Recommendation" vs. "Final Portfolio Recommendation" used inconsistently, including within `ARCHITECTURE.md` itself (M3); no explicit class-to-file binding (M4); `FINRL_MAPPING.md` missing dependency/execution-order information (M7).
- **Chosen:**
  - **M2:** "Confidence Engine" is retired everywhere in favor of "Confidence Estimation & Calibration" (the module name) or `ConfidenceEngine` (the Python class name, which is an acceptable code-identifier shortening, not a prose synonym).
  - **M3:** "Final Portfolio Recommendation" is the canonical prose/pipeline-stage term (matching the originally finalized architecture's own pipeline diagram); `FinalRecommendation` is the accepted Python class-name shorthand for it — this is a documented, intentional shortening, not an inconsistency, and is stated explicitly wherever the class first appears.
  - **M4:** a Class → File → Purpose → Dependencies → Related Interfaces table is added to `INTERFACE_CONTRACTS.md`, immediately after the Shared Data Structures section.
  - **M7:** `FINRL_MAPPING.md`'s functional-mapping table gains Dependencies, Execution Order, and Downstream Consumers columns.
- **Reasoning:** closes the remaining Major-severity findings from the Design Review without touching any architectural decision.
- **Trade-offs:** none.
- **Future implications:** none beyond keeping future edits consistent with the canonical names above.

---

## Assumption Audit (carried forward, for reference during implementation)

| Assumption | Classification |
|---|---|
| Confidence is learnable/estimable via track record, reward stability, and prediction consistency | Needs Validation (via calibration metrics; broader input set now available per ADR-013) |
| Calibration is possible and meaningful | Needs Validation (contingent on ADR-003's outcome labels, still applicable) |
| Three agents are non-redundant enough to justify fusion | Needs Validation (drop-one-agent ablation, `EXPERIMENT_PLAN.md`) |
| Each RL agent (regardless of shared/independent training infrastructure, ADR-013) can learn a stable policy from the available daily data | Needs Validation — this is now a live implementation risk rather than one design has already mitigated; monitor during training |
| Fixed universe is representative | Safe, conditional on ADR-011 being resolved |
| Long-only, no transaction costs acceptable for v1 | Weak on "no transaction costs" — resolved by ADR-012 |
| Baselines (DeepTrader, MARS) are reimplementable with reasonable effort | Likely Incorrect for MARS specifically — treat as stretch goal (ADR-008) |
| A fixed, deterministic confidence-weighted fusion formula (ADR-014) is sufficient, vs. a learned fusion policy | Needs Validation (this is a design choice made for transparency/simplicity, not yet empirically compared against a learned alternative — note as future work in `CONFIDENCE_FUSION.md`) |

---

**Related documents:** [ARCHITECTURE.md](./ARCHITECTURE.md) · [AGENTS.md](./AGENTS.md) · [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) · [RESEARCH_MAPPING.md](./RESEARCH_MAPPING.md)
