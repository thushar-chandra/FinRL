# Scientific Audit — CA-MARL Calibration Pipeline

## Goal
Perform a complete independent scientific audit of the CA-MARL calibration pipeline from first principles, ignoring all previous conclusions.

## Constraints & Preferences
- Architecture is FROZEN — no redesign, no simplification, no alternative methods, no speculative fixes.
- No code modifications, no fixes, no reimplementation.
- Every conclusion must cite specific source code, runtime traces, repository history, or documentation.
- "Insufficient evidence" is an acceptable conclusion — no guessing.

## Progress Summary
1. ✅ Phase 1 — Reconstruct the design: complete.
2. ✅ Phase 2 — Static code analysis: COMPLETE (6 findings).
3. ✅ Phase 3 — Dynamic analysis: COMPLETE (executed 4-fold walk-forward with instrumentation).
4. ✅ Phase 4 — Final report: BELOW.

---

## Dynamic Verification Report

### Methodology
- Created `experiments/_dynamic_verify.py` — monkey-patches `ConfidenceEngine`, agent `predict()` methods, `OutcomeLabelGenerator`, and `train_and_infer` with instrumentation logging.
- Patches applied BEFORE importing `_walk_forward` and `_evaluate` modules so module-level import bindings capture instrumented versions.
- No source files modified.
- Dataset: frozen cache (`experiments/dataset/`, 1111 timesteps, 19 Nifty 50 assets, 2020-01-01 to 2024-06-27).
- Config: 4 folds, training_window=504, validation_window=63, test_window=126, stride=126. Agents trained with PPO (5000 timesteps each per fold).
- Full log: `experiments/dynamic_verify_log.txt`, report: `experiments/dynamic_verify_report.txt`.

### Runtime Trace (per fold)

#### Fold 1 (fold_idx=0)
```
[TI] RECEIVED 0 CALIBRATION PAIRS
[PREDICT] market_agent rc=0.0000 rs=26260.5697
[PREDICT] risk_agent rc=0.0000 rs=364.3561
[PREDICT] allocation_agent rc=0.0000 rs=82.4574
[ENGINE#1] created
WARNING: Cold-start for agent 'market_agent': no historical labels yet, using 0.5
WARNING: Cold-start for agent 'risk_agent': no historical labels yet, using 0.5
WARNING: Cold-start for agent 'allocation_agent': no historical labels yet, using 0.5
[ESTIMATE#1] market_agent = 0.6579, risk_agent = 0.5702, allocation_agent = 0.5434
[FIT#1] received 0 pairs
[CALIBRATE#1] market_agent: 0.6579 -> 0.6579  (identity)
[CALIBRATE#1] risk_agent: 0.5702 -> 0.5702    (identity)
[CALIBRATE#1] allocation_agent: 0.5434 -> 0.5434 (identity)
[LABEL] market_agent @ 2022-10-13 = 0.7368
[LABEL] risk_agent @ 2022-10-13 = 0.8421
[LABEL] allocation_agent @ 2022-10-13 = 1.0000
[ELIG] ALL 3 agents @ 2022-10-13 -> NO (2022-10-13 + 5d <= 2022-07-13)
Calibration pool: 0 pairs
```

#### Fold 2 (fold_idx=1)
```
[TI] RECEIVED 0 CALIBRATION PAIRS
[ESTIMATE#2] market_agent = 0.6832, risk_agent = 0.5318, allocation_agent = 0.5234
[FIT#2] received 0 pairs
(identity mapping)
[LABEL] market_agent @ 2023-04-19 = 0.5789
[ELIG] ALL 3 agents @ 2023-04-19 -> NO (2023-04-19 + 5d <= 2023-01-13)
Calibration pool: 0 pairs
```

#### Fold 3 (fold_idx=2)
```
[TI] RECEIVED 0 CALIBRATION PAIRS
[ESTIMATE#3] market_agent = 0.6674, risk_agent = 0.5358, allocation_agent = 0.5200
[FIT#3] received 0 pairs
(identity mapping)
[LABEL] market_agent @ 2023-10-19 = 0.3947
[ELIG] ALL 3 agents @ 2023-10-19 -> NO (2023-10-19 + 5d <= 2023-07-20)
Calibration pool: 0 pairs
```

#### Fold 4 (fold_idx=3)
```
[TI] RECEIVED 0 CALIBRATION PAIRS
[ESTIMATE#4] market_agent = 0.6737, risk_agent = 0.5577, allocation_agent = 0.5268
[FIT#4] received 0 pairs
(identity mapping)
[LABEL] market_agent @ 2024-04-29 = 0.4737
[ELIG] SKIPPED (no next fold), 3 pairs appended unconditionally
Calibration pool: 3 pairs (never consumed)
```

---

### Verification Matrix

| # | Finding | Static Claim | Runtime Result | Verdict | Confidence |
|---|---------|-------------|----------------|---------|------------|
| 1 | `record_outcome()` never called | `_label_history` always empty | 0 calls across 4 engines, 12 label history checks all size=0, cold-start fallback (0.5) used every time | **CONFIRMED** | High |
| 2 | Calibration pairs store 0.0 vs computed raw | `ao.raw_confidence=0.0` stored in pairs | Agent predict: all 12 calls return `rc=0.0000`. Computed raw confidences: range [0.5200, 0.6832], mean=0.5826. But NO pairs reach `fit_calibration` at all (0 pairs across 4 folds) | **PARTIALLY CONFIRMED** — the 0.0 vs computed mismatch exists, but the deeper issue is the eligibility gate prevents ANY pairs from reaching calibration | High |
| 3 | First fold always empty calibration | `fit_calibration([])` for fold 1 | ALL 4 folds receive 0 calibration pairs — not just fold 1. `fit_calibration` always receives `[]`. Every fold uses identity mapping | **UPGRADED** — all folds have empty calibration, not just the first | High |
| 4 | New `ConfidenceEngine` each fold | New instance created, `_label_history` discarded | 4 engines created for 4 folds. `_label_history` size=0 for every engine×agent combination. Even if `record_outcome()` were called, it would record on the wrong instance | **CONFIRMED** | High |
| 5 | `_collect_calibration_pairs()` never called | Method exists but not invoked from `run()` | 0 calls to `_collect_calibration_pairs()` | **CONFIRMED** | High |
| 6 | N-fold expanding accumulation | Pairs accumulate across folds | **REFUTED**. 9 eligibility checks, 0 eligible. `accumulated_calib_data` stays empty for folds 1-3. Only fold 4 accumulates 3 pairs (eligibility skipped because no next fold), but they're never consumed. The expansion is a non-event | **REFUTED** — no accumulation ever happens | High |
| **7** | **ADR-024 + stride makes calibration impossible** (NEW) | Not in original findings | Test window always ends after next fold's training window (fold k test end = cursor+693, fold k+1 train end = cursor+630). So `timestamp + 5d <= next_train_end` can never be satisfied. The test window dates (patched) are always ~63 days AFTER the next fold's training window end. Calibration data can never flow | **NEW FINDING** — fundamental architectural issue | High |

---

### Root Cause Analysis

The walk-forward schedule has:
```
training_window_days=504
validation_window_days=63
test_window_days=126
stride=126
```

For fold k:
- Test window = [cursor+567 : cursor+693], test end = cursor+693
- Next fold's training window = [cursor+126 : cursor+630], train end = cursor+630
- cursor+693 > cursor+630, so test date > next train end → eligibility ALWAYS fails

The ADR-024 leakage rule (`recommendation.timestamp + label_horizon <= fold_training_window_end`) was designed for validation-window pairs, where the prediction timestamp precedes the next fold's training window. But the implementation accumulates from the test window (which is always later), making the check always fail.

The unused `_collect_calibration_pairs()` method at `_walk_forward.py:258` correctly targets the validation window — if invoked, it would produce eligible pairs. But it's never called.

### Impact Summary
- **Calibration is non-functional**: Every fold receives 0 calibration pairs → always identity mapping → `calibrated == raw` for all agents, all folds.
- **Historical accuracy signal is dead**: `hist_accuracy` always 0.5 → raw confidence depends only on `reward_stability` (with extreme variance) and `prediction_consistency`.
- **Calibration metrics are meaningless**: ECE and Brier scores are computed against the identity mapping, measuring nothing useful.
- **The entire calibration pipeline has zero corrective effect**: The `fit_calibration` → `calibrate` step is a no-op at current configuration.

### Relevant File References
- `_walk_forward.py:240-246` — eligibility check + accumulation (always fails for folds 1 to N-1)
- `_walk_forward.py:258-311` — `_collect_calibration_pairs()` — correct implementation using validation window, **never called**
- `_walk_forward.py:74` — `run()` method — does not call `_collect_calibration_pairs()`
- `_pipeline.py:141` — `ConfidenceEngine(outcome_label_gen, confidence_config)` — new instance each fold
- `_pipeline.py:143` — `fit_calibration(calib_pairs or [])` — always receives `[]`
- `_config.py:142-160` — `build_fold_schedules` — stride = test_window_days = 126 creates the temporal mismatch
- `confidence_engine.py:338-342` — cold-start fallback to `hist_acc=0.5`
- `market_agent.py:318`, `risk_agent.py:305`, `allocation_agent.py:294` — `raw_confidence=0.0` placeholder
