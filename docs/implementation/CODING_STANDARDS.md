# CODING_STANDARDS.md

> Applies to all new code in `finrl/agents/ca_marl/` and any modified FinRL files. See [DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md) for where things live and [OPENCODE.md](./OPENCODE.md) for agent-specific workflow rules.

## Python Style Guide
- PEP 8, enforced via `ruff` (already partially configured via FinRL's `.pre-commit-config.yaml` — extend, don't replace).
- Formatting via `black` (or whatever FinRL's pre-commit already uses — check before introducing a second formatter).
- Line length: 100 chars (matches common FinRL contributor convention; adjust in pre-commit config, don't leave inconsistent).

## Naming Conventions
- Modules: `snake_case.py` matching the module's role (`market_agent.py`, not `marketAgent.py` or `agent1.py`).
- Classes: `PascalCase` (`MarketAgent`, `ConfidenceEngine`).
- Functions/variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`, defined in `config_schema.py` or the relevant `configs/*.yaml`, never inline magic numbers.

## Folder Organization
- Mirrors `DIRECTORY_STRUCTURE.md` exactly. New modules go in `finrl/agents/ca_marl/`. Do not scatter CA-MARL logic into FinRL's original folders unless explicitly modifying an existing FinRL file per `MIGRATION_PLAN.md`.

## Imports
- Absolute imports within the package (`from finrl.agents.ca_marl.contracts import AgentOutput`), not relative imports across module boundaries.
- No wildcard imports (`from x import *`).
- Third-party imports grouped and separated from local imports (standard/third-party/local blocks, `ruff`/`isort`-enforced).

## Typing
- Type hints are **mandatory** on all new function signatures (this is a research codebase multiple people/agents will touch — types are load-bearing documentation).
- Use `dataclasses` or `pydantic` models for the common output contract (`contracts.py`) — pydantic preferred if runtime validation is wanted (recommended, given multiple contributors/agents), dataclasses acceptable if simplicity is prioritized early in implementation.
- `mypy` is encouraged but not blocking initially; revisit as a CI gate once the core pipeline is stable.

## Docstrings
- Google-style docstrings on every public class/function: `Args`, `Returns`, `Raises`.
- Every agent module's top-of-file docstring must restate its **single responsibility** (per `AGENTS.md`) — this is a cheap, high-value guard against architectural drift (see `OPENCODE.md`).

## Logging
- Use Python's `logging` module, never bare `print()`.
- Each agent logs at minimum: inputs received (shape/summary, not full data dump), key decision points (e.g., fallback triggered, tie-break invoked), and outputs produced.
- Log level convention: `DEBUG` for per-timestep detail, `INFO` for per-run summaries, `WARNING` for fallback/degraded behavior (e.g., optimizer infeasibility fallback), `ERROR` for genuine failures.

## Comments
- Comment *why*, not *what* (the code should be readable enough to explain "what" on its own given type hints and docstrings).
- Any deviation from the frozen architecture (`ARCHITECTURE.md`) must be flagged with a comment referencing the relevant ADR in `DECISIONS.md`, or must not be made at all without first adding a new ADR.

## Error Handling
- No bare `except:` clauses.
- Each module defines its own exception types where meaningful (e.g., `InsufficientHistoryError` in each RL agent, `LabelNotYetResolvableError` in `confidence_engine.py`, `EvaluationDataMismatchError` in `evaluation.py`) rather than letting generic exceptions propagate unlabeled. Note: `allocation_agent.py` does **not** raise on infeasible/degenerate output — that is returned as-is and corrected authoritatively by `risk_management.py` (`AGENTS.md` §3, §6).
- Fallback behaviors (e.g., Allocation Agent's equal-weight fallback on optimizer infeasibility) must be logged at `WARNING` and recorded in the output contract's `metadata` field — never silent.

## Testing Philosophy
- See `TESTING_STRATEGY.md` for the full strategy. Standard: `pytest`, one test file per module minimum, plus the two mandatory leakage tests (feature engineering, confidence calibration).
- Every new module ships with its test file in the same PR/commit — no "add tests later."

## Git Conventions
- Feature branches: `feature/<module-name>` (e.g., `feature/confidence-fusion`).
- No direct commits to `main`; PRs required, to keep `CURRENT_STATE.md` and `HANDOFF.md` accurate at each merge point.

## Commit Message Format
- [Conventional Commits](https://www.conventionalcommits.org/): `feat(confidence-engine): add regime-conditioned track record accumulation`, `fix(allocation-agent): handle singular covariance fallback`, `docs: update CURRENT_STATE.md after Milestone 4`.
- Every commit that changes an architectural decision must reference the relevant ADR ID (e.g., `refactor(ppo-coordinator): narrow action space per ADR-005`).

---

**Related documents:** [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) · [DIRECTORY_STRUCTURE.md](./DIRECTORY_STRUCTURE.md) · [OPENCODE.md](./OPENCODE.md)
