# TESTING_STRATEGY.md

> See [CODING_STANDARDS.md](./CODING_STANDARDS.md) for the general testing philosophy statement. This document details what to test and why, module by module.

## 1. Unit Testing

One test file per module (`tests/unit/test_<module>.py`), covering:
- Common output contract compliance (every agent returns the exact schema from `AGENTS.md`/`INTERFACE_CONTRACTS.md`).
- Documented failure cases per `AGENTS.md` (e.g., Market Analysis RL Agent's tie-break behavior, Portfolio Allocation RL Agent's downstream-deferred constraint handling, each RL agent's training sanity checks).
- RL-specific sanity checks per agent (reward trending sanely during training smoke tests, no NaN policy outputs) — since all three agents are genuinely RL-trained (ADR-013), this replaces what would otherwise be simple rule-based unit tests.
- `prediction_consistency()` unit-tested per agent against synthetic near-identical states (should score high) and synthetic wildly-varying states (should score low) — see ADR-023.
- `confidence_fusion.py` is a deterministic formula and should be tested exhaustively with golden-value tests (the worked numeric example in `CONFIDENCE_FUSION.md` is the canonical first test case), not just spot checks.
- `evaluation.py`'s metric functions tested against synthetic known-answer inputs (a perfectly-calibrated confidence stream → ECE ≈ 0; a badly-miscalibrated stream → high ECE) — see ADR-021.

## 2. Integration Testing

- `tests/integration/test_end_to_end_pipeline.py`: run the full pipeline (Data Pipeline → Feature Engineering [incl. regime features] → 3 RL Agents → Confidence Estimation & Calibration → Confidence-Aware Decision Fusion → Risk Management Layer → Evaluation) on a small synthetic or short real-data slice. Must complete without exceptions and produce a schema-valid Final Portfolio Recommendation object with every field (`reasoning`, `confidence_summary`) correctly traceable to its source (ADR-019).
- `tests/integration/test_interface_contracts.py`: validates that every module's input/output matches `INTERFACE_CONTRACTS.md` exactly, including the Class → File map — this is the mechanism that keeps modules built against a shared, frozen contract consistent with each other.

## 3. The Two Mandatory Leakage Tests (highest priority in the whole test suite)

### 3a. Feature Engineering Leakage Test
For every rolling/EWMA feature, assert that its value at time *t* is unchanged when future rows (t+1, t+2, ...) are altered or removed. This is the single most reviewer-sensitive correctness property in the entire codebase (lookahead bias silently invalidates every downstream financial result) and must be automated, not eyeballed.

### 3b. Confidence Calibration Leakage Test
Assert that `ConfidenceEngine.fit_calibration()`, called for a given walk-forward fold, only ever receives (confidence, label) pairs for which `OutcomeLabelGenerator.is_eligible_for_fold()` returns `True` (per the concrete leakage rule in `DECISIONS.md` ADR-024: `recommendation.timestamp + label_horizon ≤ fold.training_window.end`). Construct a test case with at least one pair that should be excluded and assert it is in fact excluded from the fitted mapping's training set. This mirrors 3a's rigor for the project's actual novel claim.

## 4. Evaluation Testing (Calibration-Specific)

- ECE, Brier score, and reliability diagram computation must be unit-tested against a synthetic, perfectly-calibrated confidence stream (should yield ECE ≈ 0) and a synthetic, badly-miscalibrated stream (should yield high ECE) — this validates the *metric implementation itself* before trusting it on real results.

## 5. Financial Validation

- Allocation weights: assert long-only (all weights ≥ 0) and sum-to-one (within floating-point tolerance) on every produced final recommendation, enforced authoritatively by the Risk Management Layer — test this layer independently by feeding it deliberately malformed input (negative weights, weights not summing to 1) and confirming valid output regardless.
- Transaction cost application: assert the cost term is applied consistently between agent training reward and the standalone backtest evaluation (a common source of silently inconsistent numbers between training and reported results).

## 6. Performance Testing

- Full walk-forward evaluation (all folds) should complete within a documented time budget (**TODO:** set an explicit wall-clock budget once fold counts are finalized). RL training for the three specialized agents (shared or independent infrastructure per ADR-013) is the main computational cost; Confidence Estimation/Calibration/Fusion/Risk Management are lightweight by comparison.
- Data pipeline: cache yfinance downloads locally; test that repeated runs don't re-hit the API unnecessarily (both a performance and a rate-limit-risk concern).

## 7. Regression Testing

- "Golden output" tests: for a fixed seed and a fixed small data slice, snapshot the full pipeline's output (agent recommendations, confidence scores, final allocation) and assert it doesn't silently drift across commits unless an ADR documents an intentional change.

## 8. Reproducibility

- All randomness (RL training for the three agents, calibration fitting if it has stochastic elements) must accept an explicit seed parameter — no reliance on global random state. `confidence_fusion.py` is deterministic and needs no seed.
- Every experiment run must snapshot its exact config (`configs/*.yaml` at time of run) alongside its results — see `CONFIGURATION.md` §Configuration Philosophy and `EXPERIMENT_PLAN.md`.
- Multiple seeds per configuration are required before reporting any headline result (see `EXPERIMENT_PLAN.md` and `DECISIONS.md` Assumption Audit — "each RL agent can learn a stable policy from the available data" is flagged Needs Validation, and seed variance reporting is the direct mitigation for the reporting side of that risk).

---

**Related documents:** [CODING_STANDARDS.md](./CODING_STANDARDS.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [EXPERIMENT_PLAN.md](./EXPERIMENT_PLAN.md) · [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
