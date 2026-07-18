# FINRL_MAPPING.md

> Functional mapping: which FinRL component implements which CA-MARL responsibility. This document answers "what does FinRL give us, functionally, for each responsibility in our architecture?" Cross-referenced, not duplicated.

## Why FinRL

FinRL is the implementation foundation (per the finalized architecture). We reuse its data pipeline, environment abstractions, Stable-Baselines3 PPO integration, training utilities, and evaluation pipeline. We do not rewrite FinRL — we extend it. The functional mapping table below captures each component's disposition (Stage assignment and implementation notes).

## Functional Mapping

| CA-MARL Responsibility | FinRL Component Providing It | Execution Order (Stage) | Depends On | Downstream Consumers | Notes |
|---|---|---|---|---|---|
| Data Pipeline (download, validate, version) | `finrl/meta/data_processors/` | Stage 1 | — (first stage) | Feature Engineering | Existing yfinance-based downloader and multi-source abstraction; extended with validation/versioning. |
| Feature Engineering (technical indicators + regime features) | `finrl/meta/preprocessor/` | Stage 1 | Data Pipeline | Market/Risk/Allocation Agents (Stage 2) | Existing MACD/RSI/Bollinger/SMA computation extended with returns, volatility, EWMA volatility, and regime features (ADR-016). |
| Reinforcement learning training infrastructure for the three specialized agents | `finrl/agents/stablebaseline3/` (Stable-Baselines3 PPO integration) | Stage 2 | Feature Engineering | Confidence Estimation & Calibration, Confidence-Aware Decision Fusion | Whether the three agents share this training infrastructure or each gets its own instantiation is an implementation decision (ADR-013). |
| Portfolio environment (long-only, sum-to-one action space) | `finrl/meta/env_portfolio_allocation/` (`PortfolioOptimizationEnv`) | Stage 2 | Feature Engineering | Portfolio Allocation Agent training loop | Provides the multi-asset, weight-vector action space; extended to carry regime features. Note: per ADR-025, this env's observation space does NOT include Market/Risk agent outputs. |
| Evaluation pipeline scaffold (train/test structure) | `finrl/train.py`, `finrl/test.py` | Stage 1 (scaffold) / Stage 4 (evaluation run) | All prior stages | — (terminal) | Repurposed into the walk-forward validation loop and the entrypoint for `EvaluationEngine` (ADR-021). |
| Confidence Estimation & Calibration, Confidence-Aware Decision Fusion, Risk Management Layer, Evaluation | **Not provided by FinRL — new code.** | Stages 3–4 | The three RL agents (Stage 2) | Each other, in pipeline order; Evaluation is terminal | Expected: these modules are this project's actual research contribution and have no FinRL analogue. See `finrl/agents/ca_marl/` in `DIRECTORY_STRUCTURE.md`. |

## What FinRL Does Not Provide (by design — this is where the contribution lives)

- Any notion of per-agent confidence, historical accuracy tracking, reward-stability signals, or prediction-consistency signals.
- Any calibration mechanism (ECE, Brier score, reliability diagrams).
- Any confidence-weighted fusion mechanism.
- Any explicit distinction between agent recommendation and agent trustworthiness.

These gaps are filled entirely by new code in `finrl/agents/ca_marl/`, as detailed in `AGENTS.md`, `MODULE_SPECIFICATIONS.md`, and `INTERFACE_CONTRACTS.md`.

## Scope of This Document

`FINRL_MAPPING.md` answers a functional question: "which FinRL component provides which CA-MARL responsibility, at which stage, and with what notes?" It does not enumerate every individual FinRL file — the functional mapping table above covers the components with Stage assignments and implementation guidance. Folder-by-folder decisions are subsumed into the table's Stage column (which implies KEEP/MODIFY for components assigned to a stage) and the dedicated new-code row for modules with no FinRL analogue.

---

**Related documents:** [DIRECTORY_STRUCTURE.md](../implementation/DIRECTORY_STRUCTURE.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [INTERFACE_CONTRACTS.md](./INTERFACE_CONTRACTS.md)
