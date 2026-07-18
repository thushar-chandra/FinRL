# CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for Portfolio Decision Support

> **Placement note:** per the documentation generation brief, this file lives in `docs/README.md`. For GitHub display purposes, copy or symlink it to the repository root as `README.md` — internal links below are written relative to the `docs/` folder.

## What The Research Contribution Is — And Is Not

Multi-Agent Reinforcement Learning, PPO, and portfolio optimization are **not** this project's novelty — all three are established techniques, reused here via a fork of [FinRL](https://github.com/AI4Finance-Foundation/FinRL) (see [`FINRL_MAPPING.md`](./FINRL_MAPPING.md)). The three specialized agents genuinely are reinforcement learning agents, trained via Stable-Baselines3 PPO within the FinRL ecosystem.

**The actual contribution is:** Confidence Estimation, Confidence Calibration, and Confidence-Aware Decision Fusion — plus the resulting improvements in transparency, robustness, and risk-aware decision support. See [`DECISIONS.md`](./DECISIONS.md) ADR-013–ADR-015 for the full reasoning, and [`CONFIDENCE_FUSION.md`](./CONFIDENCE_FUSION.md) for the primary contribution's dedicated specification.

## What This Is

CA-MARL produces long-only portfolio allocation recommendations for a fixed universe of Indian large-cap equities. Three specialized reinforcement learning agents — Market Analysis, Risk Assessment, and Portfolio Allocation — each produce a recommendation. A dedicated Confidence Estimation and Calibration layer scores how much each recommendation should be trusted. A Confidence-Aware Decision Fusion module — a deterministic formula, **not PPO, not RL-trained** — combines the three recommendations weighted by that calibrated confidence. A Risk Management Layer enforces long-only/sum-to-one/exposure constraints before the system outputs a final recommendation: an allocation, reasoning, and a confidence summary.

## What This Is Not

- Not an automated trading bot, execution engine, or brokerage integration.
- Not a high-frequency or intraday trading system.
- Not an attempt to invent a new RL algorithm — PPO (via Stable-Baselines3) is used as-is.
- Not a claim of novelty for multi-agent RL, PPO, or portfolio optimization themselves — see "What The Research Contribution Is — And Is Not" above.

## Architecture, In One Sentence

Historical market data flows through a feature pipeline (which includes regime features — bull/bear, volatility regime, trend regime, market-state — as ordinary engineered features, not a separate module) into three specialized reinforcement learning agents, each consuming Feature Engineering output only (no cross-agent inputs); each agent's recommendation, together with signals from its own training process (historical accuracy, reward stability, prediction consistency), is scored for confidence and calibrated by one combined Confidence Estimation & Calibration module; a dedicated Confidence-Aware Decision Fusion module transforms each agent's heterogeneous recommendation into a common weight-vector representation and combines them using calibrated confidence, producing an allocation, reasoning, and a confidence summary with every field traceable to its source; the result passes through a Risk Management Layer before being surfaced as the Final Portfolio Recommendation, and is measured by a dedicated Evaluation module on both financial and calibration grounds.

Full detail: [`ARCHITECTURE.md`](./ARCHITECTURE.md). Research rationale: [`MODULE_SPECIFICATIONS.md`](./MODULE_SPECIFICATIONS.md). Engineering contract: [`AGENTS.md`](./AGENTS.md), [`INTERFACE_CONTRACTS.md`](./INTERFACE_CONTRACTS.md).

## Related Work

- **DeepTrader** (Wang et al., AAAI 2021) — single-agent DRL with market-condition embedding; informs this project's reward design and regime-feature motivation.
- **MARS** (Chen et al., AAAI 2026) — heterogeneous multi-agent RL with a meta-controller dynamically reweighting agent trust by regime; closest prior art, discussed in `DECISIONS.md` and `RESEARCH_MAPPING.md`.

## Repository Structure

See [`DIRECTORY_STRUCTURE.md`](./DIRECTORY_STRUCTURE.md) for the complete, annotated tree. This repository is a fork of [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL); see [`MIGRATION_PLAN.md`](./MIGRATION_PLAN.md) and [`FINRL_MAPPING.md`](./FINRL_MAPPING.md) for what was kept, modified, removed, or replaced, and why.

## Getting Started

```bash
git clone <this-repo>
cd ca-marl
pip install -e .
pip install stockstats scikit-learn  # see CONFIGURATION.md for the full dependency list
```

**TODO:** finalize and document exact setup/run commands once Stage 1 (`IMPLEMENTATION_ROADMAP.md`) is complete.

## Project Status

This is an active research project. Current implementation status: see [`CURRENT_STATE.md`](./CURRENT_STATE.md). Immediate next steps: see [`HANDOFF.md`](./HANDOFF.md).

## Documentation Index

| Document | Purpose |
|---|---|
| [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) | Vision, objectives, non-goals, constraints |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, diagrams, data/confidence flow |
| [MODULE_SPECIFICATIONS.md](./MODULE_SPECIFICATIONS.md) | Research-facing: purpose, theory, math, per module |
| [AGENTS.md](./AGENTS.md) | Engineering-facing: classes, contracts, failure cases, per module |
| [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md) | Concrete implementation contract (method signatures, schemas) |
| [CONFIDENCE_FUSION.md](./CONFIDENCE_FUSION.md) | Dedicated spec for the primary research contribution |
| [FINRL_MAPPING.md](./FINRL_MAPPING.md) | Functional mapping: FinRL components → CA-MARL responsibilities |
| [SYSTEM_WORKFLOW.md](./SYSTEM_WORKFLOW.md) | Narrative build-time and run-time workflow |
| [DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md) | Full repo tree |
| [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) | FinRL fork decisions, folder by folder |
| [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) | Staged implementation order (no timeline) |
| [CURRENT_STATE.md](./CURRENT_STATE.md) | Live status |
| [DECISIONS.md](./DECISIONS.md) | Architecture Decision Record |
| [CODING_STANDARDS.md](./CODING_STANDARDS.md) | Style, conventions |
| [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) | Test plan, incl. mandatory leakage tests |
| [RESEARCH_MAPPING.md](./RESEARCH_MAPPING.md) | Paper claims ↔ code/experiments |
| [EXPERIMENT_PLAN.md](./EXPERIMENT_PLAN.md) | Experiments, baselines, ablations |
| [CONFIGURATION.md](./CONFIGURATION.md) | Dependencies, config philosophy |
| [TASKS.md](./TASKS.md) | Kanban backlog (no effort estimates, no owners) |
| [OPENCODE.md](./OPENCODE.md) | Instructions for AI coding agents |
| [HANDOFF.md](./HANDOFF.md) | What to do next |
| [PROMPT_HISTORY.md](./PROMPT_HISTORY.md) | Changelog of major architectural decisions |

## License

MIT (inherited from FinRL — see `LICENSE`).

## Disclaimer

This is a research and educational project. Nothing in this repository constitutes financial advice or a recommendation to trade real money. This system produces recommendation objects for decision support, not executable trades. Consult a qualified professional before making investment decisions.

---

**Related documents:** [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) · [ARCHITECTURE.md](./ARCHITECTURE.md)
