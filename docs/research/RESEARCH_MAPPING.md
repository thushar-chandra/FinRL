# RESEARCH_MAPPING.md

> Maps paper claims to code/experiments. Update this file as the paper draft evolves — it is the traceability matrix that keeps the paper honest (no claim without a corresponding experiment; no experiment without a corresponding paper section). See [EXPERIMENT_PLAN.md](./EXPERIMENT_PLAN.md) for the experiments themselves.

## Related Work (context for reviewers, not a code mapping)

| Prior work | Relevance | Implication for this project |
|---|---|---|
| DeepTrader (Wang et al., AAAI 2021) | Single-agent DRL with market-condition embedding; asymmetric drawdown-based reward | Committed baseline; reward function design borrows its precedent, and its market-condition embedding motivates our regime features (ADR-012, ADR-016) |
| MARS (Chen et al., AAAI 2026) | Heterogeneous multi-agent RL ensemble + meta-controller dynamically reweighting agent trust by regime | Closest prior art. Since our three agents are also genuinely RL-trained (ADR-013), the differentiator is now specifically the explicit, calibrated, independently-testable confidence layer (ADR-014) vs. MARS's implicit meta-controller reweighting — related work section + stretch-goal baseline |
| MAPS, MoE-DRLPM | Adjacent multi-agent/mixture-of-experts portfolio RL systems | Related work, not baselines |
| Mixture-of-Experts gating (Jacobs et al., 1991; Jordan & Jacobs, 1994) | Theoretical grounding for confidence-weighted combination of expert outputs | Cited in Method section justifying the Confidence-Aware Decision Fusion formula (ADR-014) — note: our fusion is a fixed formula, not a learned gate, which is a meaningful point of contrast worth stating explicitly in the paper |
| Calibration (Guo et al., 2017; Naeini et al., 2015) | ECE, temperature/Platt scaling | Cited in Method section justifying confidence calibration (ADR-003, as broadened by ADR-013) |
| Deep ensembles (Lakshminarayanan et al., 2017); ensemble-disagreement RL uncertainty (Hoel et al., 2020) | Alternative confidence-computation methods | Cited as future work, not current implementation |

## Paper Section → Code Mapping

| Paper Section (anticipated) | Implementing Code | Validating Experiment(s) | Figures/Tables |
|---|---|---|---|
| §Data & Preprocessing (incl. regime features) | `finrl/meta/data_processors/`, `finrl/meta/preprocessor/` | Leakage test (§3a `TESTING_STRATEGY.md`) | Table: universe composition + date range; Figure: regime timeline over evaluation period (regime features, not a separate module — ADR-016) |
| §Specialized RL Agents (Market/Risk/Allocation) | `finrl/agents/ca_marl/{market,risk,allocation}_agent.py` | Drop-one-agent ablation | Table: per-agent standalone performance |
| §Confidence Estimation & Calibration (**core contribution**) | `finrl/agents/ca_marl/confidence_engine.py` | Calibration evaluation (ECE, Brier, reliability diagrams) | Figure: reliability diagrams per agent; Table: ECE/Brier by agent |
| §Confidence-Aware Decision Fusion (**core contribution**) | `finrl/agents/ca_marl/confidence_fusion.py` — deterministic, explicitly NOT PPO-based (ADR-014, ADR-015) | Shuffled-confidence ablation | Table: fusion with vs. without calibration vs. shuffled confidence |
| §Risk Management | `finrl/agents/ca_marl/risk_management.py` | Financial validation tests (§5 `TESTING_STRATEGY.md`) | — |
| §Evaluation Methodology | `finrl/agents/ca_marl/evaluation.py` (`EvaluationEngine`, ADR-021) | Metric-function unit tests against synthetic known-answer inputs | — |
| §Experimental Results | full pipeline | Main benchmark comparison, walk-forward evaluation | Table: financial metrics (Sharpe, Sortino, Max Drawdown, Volatility, Cumulative Return) vs. baselines; significance test results |
| §Related Work | n/a (literature only) | n/a | — |
| §Limitations | n/a | Documented explicitly: single market/time window, MARS reproduction risk, deterministic-vs-learned-fusion comparison not yet made | — |

## Claims That Must Never Be Made Without Corresponding Evidence

Per the original Foundation document's research-writing philosophy ("never claim improvements that have not been experimentally demonstrated; never fabricate equations/metrics/citations; mark undecided things as future work"):

- Do not claim "confidence is calibrated" without reporting ECE/Brier/reliability diagram numbers.
- Do not claim "confidence-aware fusion outperforms equal-weight fusion" without the shuffled-confidence ablation result.
- Do not claim "the three-agent decomposition adds value" without the drop-one-agent ablation result.
- Do not claim generalization beyond the single evaluated market/time window without an explicit secondary-market robustness check (or, absent that, an explicit Limitations disclosure — no implied generalization).
- Do not claim outperformance over MARS unless MARS is genuinely reproduced as a baseline (not just cited) — if reproduction isn't completed, MARS appears in Related Work only, with no comparative performance claim.

---

**Related documents:** [EXPERIMENT_PLAN.md](./EXPERIMENT_PLAN.md) · [DECISIONS.md](./DECISIONS.md) · [AGENTS.md](./AGENTS.md)
