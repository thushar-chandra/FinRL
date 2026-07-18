# EXPERIMENT_PLAN.md

> See [RESEARCH_MAPPING.md](./RESEARCH_MAPPING.md) for which paper claims each experiment supports, and [TESTING_STRATEGY.md](../implementation/TESTING_STRATEGY.md) for the engineering-correctness tests that must pass before any of these experiments are trustworthy. The upstream FinRL baseline has been validated — see [BASELINE_ANALYSIS.md](./BASELINE_ANALYSIS.md).

## Datasets

- **Universe:** fixed Indian large-cap equities + Nifty 50 as macro context. **TODO:** exact ticker list and as-of selection date (`DECISIONS.md` ADR-011, `CURRENT_STATE.md`).
- **Frequency:** daily OHLCV.
- **Split:** walk-forward validation (chronological folds; no random shuffling — carried over unchanged from the original Research Decisions document). **TODO:** exact fold count, window sizes, retraining cadence, and one final untouched test period (`CURRENT_STATE.md` pending items).

## Evaluation Metrics

**Financial metrics:** Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Portfolio Volatility, Cumulative Return.

**Calibration metrics (core contribution — see `RESEARCH_MAPPING.md`):** Expected Calibration Error (ECE), Brier score, reliability diagrams — computed per agent and per regime bucket.

## Baselines

| Baseline | Priority | Notes |
|---|---|---|
| Equal Weight (1/N) | Committed | Trivial, via PyPortfolioOpt or hand-rolled |
| Buy and Hold | Committed | Trivial |
| Static Mean-Variance Optimization (MVO) | Committed | Via PyPortfolioOpt `EfficientFrontier`, no rebalancing |
| DeepTrader | Committed | Reimplementation effort budgeted; reward-function precedent already informs ADR-012 |
| MARS | **Stretch goal only** | 2026 publication; public reference code availability unconfirmed at time of writing — do not commit engineering time here until the committed baselines and core pipeline are solid (see `DECISIONS.md` ADR-008 and the earlier repository/architecture review's explicit warning about reimplementation-fidelity risk) |

**Rule:** never compare only against random guessing (carried over from the original Research Decisions document) — the above list satisfies this by construction.

## Ablation Studies (mandatory, not optional — these are what prove the core claims)

1. **Equal-weight fusion vs. confidence-aware fusion** — isolates the value of confidence-aware weighting itself (the Confidence-Aware Decision Fusion formula reduces to equal-weight averaging when all confidence values are equal — see `CONFIDENCE_FUSION.md`).
2. **With vs. without calibration** — isolates the value of the calibration step specifically (raw vs. calibrated confidence fed into fusion).
3. **Shuffled-confidence sanity check** — randomize/shuffle calibrated confidence values across agents before fusion; if performance is statistically indistinguishable from the real-confidence condition, confidence is not functionally load-bearing (a negative result that must be reported honestly, not hidden). Note: since fusion is a deterministic formula (not PPO/RL-trained), this ablation is exceptionally cheap to run — no retraining required, just re-computing fusion with shuffled inputs.
4. **Drop-one-agent** — remove each of Market/Risk/Allocation agents in turn, measure performance delta, to demonstrate (or fail to demonstrate) non-redundancy of the three-agent decomposition.

## Statistical Rigor

- Multiple random seeds per configuration (exact count **TODO**, minimum recommendation: 5+ for any headline comparison).
- Report mean ± confidence interval, not point estimates — **for both financial metrics AND calibration metrics (ECE, Brier score)**. Since confidence estimation now depends on RL-training-derived signals (reward stability, prediction consistency — ADR-013, ADR-023), calibration quality inherits RL training variance and must be seed-averaged and interval-reported with the same rigor as financial metrics, not just asserted from a single run.
- Paired significance test (e.g., paired t-test or Wilcoxon signed-rank across seeds/folds) against each baseline before claiming outperformance.

## Expected Outputs

**Plots:**
- Reliability diagrams (calibration curves) per agent, per regime.
- Cumulative return curves: CA-MARL vs. all baselines, over the test period.
- Regime timeline overlay on the evaluation period (volatility/trend regime over time).
- Ablation bar charts (equal-weight vs. confidence-aware vs. shuffled; full vs. drop-one-agent).

**Tables:**
- Main results table: financial metrics × (CA-MARL, all baselines), with significance markers.
- Calibration table: ECE / Brier score by agent and regime.
- Ablation results table.
- Universe composition and date-range table (for reproducibility/transparency).

## Explicit Non-Claims (see `RESEARCH_MAPPING.md` §"Claims That Must Never Be Made Without Corresponding Evidence")

This experiment plan is designed so that every headline claim in the paper has a corresponding row in this document. If a result doesn't have an experiment here, it doesn't go in the paper.

---

**Related documents:** [RESEARCH_MAPPING.md](./RESEARCH_MAPPING.md) · [TESTING_STRATEGY.md](../implementation/TESTING_STRATEGY.md) · [BASELINE_ANALYSIS.md](./BASELINE_ANALYSIS.md)
