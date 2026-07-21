# CA-MARL Project Handoff

## Project Overview

CA-MARL (Confidence-Aware Multi-Agent Reinforcement Learning) is a research framework for portfolio allocation decision support. It uses three specialised PPO-trained RL agents (Market Analysis, Risk Assessment, Portfolio Allocation) whose recommendations are fused via deterministic confidence-weighted averaging. The core research contribution is the explicit confidence estimation and calibration layer.

## Repository State

- **Status:** COMPLETE — architecture, implementation, experiments, statistical analysis, and manuscript are frozen.
- **Last commit:** `8da9fc1` (feature/experimentation branch)
- **Python version:** 3.14.5 (validated environment; Python 3.11+ should work)
- **Project metadata:** `pyproject.toml:name=ca-marl`, `version=2.0.0`

## Completed Work

### Architecture & Implementation
- 7 CA-MARL modules: three RL agents, confidence engine, confidence fusion, risk management, evaluation, data adapter, pipeline orchestrator
- Typed contracts and configuration schemas
- Integration tests (synthetic + historical data)

### Experimental Campaign
- 5 random seeds (42–46) × 4 walk-forward folds = 20 observations
- Frozen dataset: 19 Nifty 50 equities, 2020-01-01 to 2024-06-27 (1,111 days), SHA-256 verified
- 3 baselines: equal-weight, buy-and-hold, mean-variance optimisation
- 7 ablation variants
- Statistical analysis: permutation test, sign test, Kruskal-Wallis, Cohen's d

### Key Result
CA-MARL achieves mean Sharpe 1.885 (95% CI: [1.809, 1.961]) but is not statistically distinguishable from equal-weight (permutation p = 0.3246). The calibration pipeline produces identity mappings (zero calibration pairs accumulated). These findings are honestly reported in the manuscript.

### Manuscript
Complete sections: Methodology, Experimental Setup, Results, Discussion, Limitations, Threats to Validity.
Missing sections: Abstract, Introduction, Related Work, Conclusion.

## Repository Layout

```
finrl/agents/ca_marl/       # Core CA-MARL module implementations
experiments/                 # Experimental campaign framework
  _walk_forward.py           # Walk-forward validation loop
  _pipeline.py               # Experiment pipeline wrapper
  _evaluate.py               # Single-experiment runner
  _config.py                 # All experiment parameters (dataclasses)
  _config.py                 # All experiment parameters
  _data_cache.py             # Versioned dataset (SHA-256)
  _dynamic_verify.py         # Runtime instrumentation
  _publication_outputs.py    # Publication figures + LaTeX tables
  _final_stats.py            # Statistical analyses
  run_campaign.py            # Master campaign runner
  run_ca_marl.py             # Single experiment runner
  run_plots.py               # Plot generation
  run_ablations.py           # Ablation studies
  run_baselines.py           # Baseline strategies
  dataset/                   # Frozen dataset (PKL + metadata JSON)
  results/                   # Campaign result JSON files
  plots/                     # Generated figures + tables
    publication/figures/     # Publication-quality PDFs
    publication/tables/      # LaTeX .tex files
  reports/                   # Research report, artifact manifest
manuscript/                  # Paper manuscript sections (Markdown)
docs/                        # Architecture, implementation, planning docs
tests/                       # Integration tests
```

## Important Files

| File | Purpose |
|------|---------|
| `experiments/_config.py` | All experiment hyperparameters (single source of truth) |
| `experiments/_walk_forward.py` | Walk-forward validation with calibration eligibility |
| `experiments/_data_cache.py` | Dataset loading with SHA-256 verification |
| `experiments/reproducibility_manifest.json` | Locked experiment parameters |
| `experiments/reports/artifact_manifest.json` | Generated artifact inventory |
| `experiments/dataset/metadata.json` | Dataset version + checksums |
| `finrl/agents/ca_marl/contracts.py` | All typed data contracts |
| `finrl/agents/ca_marl/config_schema.py` | Configuration dataclasses |
| `finrl/agents/ca_marl/confidence_engine.py` | Confidence estimation + Platt calibration + OutcomeLabelGenerator |
| `finrl/agents/ca_marl/confidence_fusion.py` | Primary contribution: deterministic fusion |
| `docs/architecture/DECISIONS.md` | Architecture Decision Record (ADR-001 to ADR-026) |

## Reproduction Workflow

```bash
# 1. Install
pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 2. Run full campaign (5 seeds, 4 folds, ~hours on CPU)
python experiments/run_campaign.py

# 3. Generate publication artifacts
python experiments/run_plots.py

# 4. Run tests
pytest tests/
```

## Known Limitations

### Calibration Non-Function (Critical)
The calibration pipeline produces only identity mappings. Root cause: walk-forward stride (126d) equals test window length (126d), so fold k's test window ends after fold k+1's training window. The ADR-024 eligibility check (`timestamp + 5d <= next_train_end`) always fails. The correct implementation exists at `_walk_forward.py:258` (`_collect_calibration_pairs()`) but is never called from `run()`. Frozen — no code fix permitted.

### Market Scope
- Single market: Indian large-cap equities (Nifty 50 proxy)
- Single time period: 2020–2024 bull market
- 19 assets, 1,111 trading days
- No transaction costs, no slippage
- CPU-only training (5,000 PPO timesteps per agent)

### Technical Debt
- `raw_confidence=0.0` stored in AgentOutput (placeholder)
- `_VOL_NORMALIZATION_FACTOR = 10.0` duplicated in `risk_agent.py:62` and `confidence_engine.py:30`
- `market_agent` does not populate `metadata["tie_break_reason"]` (minor contract deviation)
- Ablations use single 80/20 split (not walk-forward), no statistical replication

## Missing Manuscript Sections

The following sections do not exist in `manuscript/` and need to be written:

1. **Abstract** (≤250 words) — Distillation of the entire paper
2. **Introduction** — Problem motivation, gap, contributions
3. **Related Work** — Position vs DeepTrader, MARS, calibration literature
4. **Conclusion** — Summary, honest assessment, future work

`PAPER_BLUEPRINT.md` contains planning content (§1 Research Problem → Introduction, §2 Research Gap → Related Work) that may serve as a starting point. `REFERENCES.md` has 9 entries and should be expanded to 25–35.

## Release Checklist

- [ ] Write Abstract, Introduction, Related Work, Conclusion
- [ ] Expand References to 25–35 entries
- [ ] Choose target venue and check formatting requirements
- [ ] Apply CONSISTENCY_AUDIT.md corrections (regime feature references — partially done in dirty tree)
- [ ] Verify figure/table references in manuscript
- [ ] Create release tag (e.g., `v2.0-release`)
- [ ] Set up DOI (e.g., Zenodo) for frozen dataset
- [ ] Update repository URL in `pyproject.toml` and `manuscript/availability.md`
- [ ] Push to public repository

## Future Work (Post-Publication)

- Fix calibration eligibility (modify stride or connect `_collect_calibration_pairs()`)
- Expand to larger universes and multiple markets
- Add transaction cost modelling (ADR-012)
- Implement regime features (as documented in architecture)
- Hyperparameter sensitivity analysis
- Additional baselines (DeepTrader, MARS reproduction)

## Evidence Traceability

Every claim in the manuscript maps to:
- **F1–F9** findings from `PHASE_3_FREEZE_REPORT.md`
- Specific JSON result files in `experiments/results/`
- Dynamic verification logs in `experiments/dynamic_verify_log.txt`
- Figures and tables in `experiments/plots/publication/`
- CONSISTENCY_AUDIT.md and RESULTS_AUDIT.md verify per-claim accuracy
