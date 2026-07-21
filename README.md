# CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for Portfolio Decision Support

## What The Research Contribution Is — And Is Not

Multi-Agent Reinforcement Learning, PPO, and portfolio optimization are **not** this project's novelty — all three are established techniques, reused here via a fork of [FinRL](https://github.com/AI4Finance-Foundation/FinRL) (see [`FINRL_MAPPING.md`](./docs/architecture/FINRL_MAPPING.md)). The three specialized agents genuinely are reinforcement learning agents, trained via Stable-Baselines3 PPO within the FinRL ecosystem.

**The actual contribution is:** Confidence Estimation, Confidence Calibration, and Confidence-Aware Decision Fusion — plus the resulting improvements in transparency, robustness, and risk-aware decision support. See [`DECISIONS.md`](./docs/architecture/DECISIONS.md) ADR-013–ADR-015 for the full reasoning, and [`CONFIDENCE_FUSION.md`](./docs/architecture/CONFIDENCE_FUSION.md) for the primary contribution's dedicated specification.

## What This Is

CA-MARL produces long-only portfolio allocation recommendations for a fixed universe of Indian large-cap equities. Three specialized reinforcement learning agents — Market Analysis, Risk Assessment, and Portfolio Allocation — each produce a recommendation. A dedicated Confidence Estimation and Calibration layer scores how much each recommendation should be trusted. A Confidence-Aware Decision Fusion module — a deterministic formula, **not PPO, not RL-trained** — combines the three recommendations weighted by that calibrated confidence. A Risk Management Layer enforces long-only/sum-to-one/exposure constraints before the system outputs a final recommendation: an allocation, reasoning, and a confidence summary.

## What This Is Not

- Not an automated trading bot, execution engine, or brokerage integration.
- Not a high-frequency or intraday trading system.
- Not an attempt to invent a new RL algorithm — PPO (via Stable-Baselines3) is used as-is.
- Not a claim of novelty for multi-agent RL, PPO, or portfolio optimization themselves — see "What The Research Contribution Is — And Is Not" above.

## Architecture, In One Sentence

Historical market data flows through a feature pipeline (which includes technical indicators and volatility/return statistics as ordinary engineered features, not a separate module) into three specialized reinforcement learning agents, each consuming Feature Engineering output only (no cross-agent inputs); each agent's recommendation, together with signals from its own training process (historical accuracy, reward stability, prediction consistency), is scored for confidence and calibrated by one combined Confidence Estimation & Calibration module; a dedicated Confidence-Aware Decision Fusion module transforms each agent's heterogeneous recommendation into a common weight-vector representation and combines them using calibrated confidence, producing an allocation, reasoning, and a confidence summary with every field traceable to its source; the result passes through a Risk Management Layer before being surfaced as the Final Portfolio Recommendation, and is measured by a dedicated Evaluation module on both financial and calibration grounds.

Full detail: [`ARCHITECTURE.md`](./docs/architecture/ARCHITECTURE.md). Research rationale: [`MODULE_SPECIFICATIONS.md`](./docs/architecture/MODULE_SPECIFICATIONS.md). Engineering contract: [`AGENTS.md`](./docs/architecture/AGENTS.md), [`INTERFACE_CONTRACTS.md`](./docs/architecture/INTERFACE_CONTRACTS.md).

## Related Work

- **DeepTrader** (Wang et al., AAAI 2021) — single-agent DRL with market-condition embedding; informs this project's reward design.
- **MARS** (Chen et al., AAAI 2026) — heterogeneous multi-agent RL with a meta-controller dynamically reweighting agent trust by regime; closest prior art, discussed in [`DECISIONS.md`](./docs/architecture/DECISIONS.md) and [`RESEARCH_MAPPING.md`](./docs/research/RESEARCH_MAPPING.md).

## Repository Structure

See [`DIRECTORY_STRUCTURE.md`](./docs/implementation/DIRECTORY_STRUCTURE.md) for the complete, annotated tree. This repository is a fork of [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL); see [`FINRL_MAPPING.md`](./docs/architecture/FINRL_MAPPING.md) for what was kept, modified, removed, or replaced, and why.

## Getting Started

### Prerequisites

Python 3.11.9 with the following validated environment:

- Stable-Baselines3 2.9.0
- PyTorch 2.13.0 (CPU)
- Gymnasium 1.3.0
- Gym 0.26.2

Install dependencies:

```bash
pip install -e .
pip install stockstats scikit-learn
```

*Note: `elegantrl` is pinned `--no-deps` to avoid `pygame` build failures on Windows.*

### Baseline Validation

The upstream FinRL baseline has been validated end-to-end. See [`BASELINE_ANALYSIS.md`](./docs/research/BASELINE_ANALYSIS.md) for:

- Data pipeline validation (DOW 30, Yahoo Finance download, technical indicators)
- Training validation (A2C, DDPG, PPO completed; TD3, SAC timed out on CPU)
- Backtest validation (all three DRL agents outperformed DJIA during the 2026 downturn)
- Codebase readiness assessment for CA-MARL extension

### Running the CA-MARL Pipeline

*Documentation for the complete CA-MARL pipeline will be updated as implementation proceeds. See [`IMPLEMENTATION_ROADMAP.md`](./docs/planning/IMPLEMENTATION_ROADMAP.md) for the staged implementation plan.*

## Project Status

This is an active research project. **Baseline validation is complete** — the upstream FinRL data pipeline, PPO/A2C/DDPG training, and backtesting have been validated on the DOW 30 universe. Remaining work is implementation of the CA-MARL architecture (specialized RL agents, confidence estimation & calibration, confidence-aware fusion, risk management, evaluation).

Current implementation status: see [`CURRENT_STATE.md`](./docs/planning/CURRENT_STATE.md). Immediate next steps: see [`HANDOFF.md`](./docs/planning/HANDOFF.md).

## Documentation Index

| Document | Purpose |
|---|---|---|
| [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) | System design, diagrams, data/confidence flow |
| [MODULE_SPECIFICATIONS.md](./docs/architecture/MODULE_SPECIFICATIONS.md) | Research-facing: purpose, theory, math, per module |
| [AGENTS.md](./docs/architecture/AGENTS.md) | Engineering-facing: classes, contracts, failure cases, per module |
| [INTERFACE_CONTRACTS.md](./docs/architecture/INTERFACE_CONTRACTS.md) | Concrete implementation contract (method signatures, schemas) |
| [CONFIDENCE_FUSION.md](./docs/architecture/CONFIDENCE_FUSION.md) | Dedicated spec for the primary research contribution |
| [FINRL_MAPPING.md](./docs/architecture/FINRL_MAPPING.md) | Functional mapping: FinRL components → CA-MARL responsibilities |
| [SYSTEM_WORKFLOW.md](./docs/architecture/SYSTEM_WORKFLOW.md) | Narrative build-time and run-time workflow |
| [DECISIONS.md](./docs/architecture/DECISIONS.md) | Architecture Decision Record |
| [DIRECTORY_STRUCTURE.md](./docs/implementation/DIRECTORY_STRUCTURE.md) | Full repo tree |
| [CODING_STANDARDS.md](./docs/implementation/CODING_STANDARDS.md) | Style, conventions |
| [TESTING_STRATEGY.md](./docs/implementation/TESTING_STRATEGY.md) | Test plan, incl. mandatory leakage tests |
| [OPENCODE.md](./docs/implementation/OPENCODE.md) | Instructions for AI coding agents |
| [PROMPT_HISTORY.md](./docs/implementation/PROMPT_HISTORY.md) | Changelog of major architectural decisions |
| [IMPLEMENTATION_ROADMAP.md](./docs/planning/IMPLEMENTATION_ROADMAP.md) | Staged implementation order (no timeline) |
| [CURRENT_STATE.md](./docs/planning/CURRENT_STATE.md) | Live status |
| [TASKS.md](./docs/planning/TASKS.md) | Kanban backlog (no effort estimates, no owners) |
| [HANDOFF.md](./docs/planning/HANDOFF.md) | What to do next |
| [RESEARCH_MAPPING.md](./docs/research/RESEARCH_MAPPING.md) | Paper claims ↔ code/experiments |
| [EXPERIMENT_PLAN.md](./docs/research/EXPERIMENT_PLAN.md) | Experiments, baselines, ablations |
| [BASELINE_ANALYSIS.md](./docs/research/BASELINE_ANALYSIS.md) | FinRL baseline validation report |

## License

MIT (inherited from FinRL — see `LICENSE`).

## Disclaimer

This is a research and educational project. Nothing in this repository constitutes financial advice or a recommendation to trade real money. This system produces recommendation objects for decision support, not executable trades. Consult a qualified professional before making investment decisions.

---

**Related documents:** [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) · [CURRENT_STATE.md](./docs/planning/CURRENT_STATE.md) · [BASELINE_ANALYSIS.md](./docs/research/BASELINE_ANALYSIS.md)
