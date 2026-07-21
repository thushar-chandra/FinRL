# CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for Portfolio Decision Support

## What This Is

CA-MARL is a research framework for confidence-aware multi-agent reinforcement learning in portfolio allocation. It produces long-only portfolio allocation recommendations for a fixed universe of Indian large-cap equities. Three specialised reinforcement learning agents — Market Analysis, Risk Assessment, and Portfolio Allocation — each produce a recommendation. A dedicated Confidence Estimation and Calibration layer scores how much each recommendation should be trusted. A Confidence-Aware Decision Fusion module — a deterministic formula, **not PPO, not RL-trained** — combines the three recommendations weighted by that calibrated confidence. A Risk Management Layer enforces long-only/sum-to-one/exposure constraints before the system outputs a final recommendation.

**The research contribution is:** Confidence Estimation, Confidence Calibration, and Confidence-Aware Decision Fusion — plus the resulting improvements in transparency, robustness, and risk-aware decision support.

## What This Is Not

- Not an automated trading bot, execution engine, or brokerage integration.
- Not a high-frequency or intraday trading system.
- Not an attempt to invent a new RL algorithm — PPO (via Stable-Baselines3) is used as-is.
- Not a claim of novelty for multi-agent RL, PPO, or portfolio optimization — see above.

## Repository Status

**COMPLETE.** Architecture, implementation, experiments, statistical analysis, and manuscript are frozen. This repository contains the full reproducible experimental campaign.

## Repository Structure

```
finrl/                        Core framework + CA-MARL modules
  agents/ca_marl/             CA-MARL module implementations
    market_agent.py           Market Analysis RL agent
    risk_agent.py             Risk Assessment RL agent
    allocation_agent.py       Portfolio Allocation RL agent
    confidence_engine.py      Confidence estimation + Platt calibration
    confidence_fusion.py      Confidence-weighted decision fusion
    risk_management.py        Constraint enforcement
    evaluation.py             Financial + calibration metrics
    pipeline.py               Pipeline orchestrator
    data_adapter.py           Data pipeline adapter
    contracts.py              Typed data contracts
    config_schema.py          Configuration schemas
experiments/                  Experimental campaign framework
  _walk_forward.py            Walk-forward validation
  _pipeline.py                Experiment pipeline wrapper
  _evaluate.py                Evaluation runner
  _config.py                  Experiment parameters
  _data_cache.py              Versioned dataset cache
  _dynamic_verify.py          Runtime instrumentation
  _publication_outputs.py     Figures + LaTeX table generation
  dataset/                    Frozen dataset (v1.0.0, SHA-256)
  results/                    Campaign result JSON files
  plots/                      Generated figures and tables
  reports/                    Research report + artifact manifest
configs/                      Configuration stubs (unused — Python dataclasses used instead)
manuscript/                   Paper manuscript sections
docs/                         Architecture, implementation, planning docs
tests/                        Integration tests
```

Full detail: [`DIRECTORY_STRUCTURE.md`](./docs/implementation/DIRECTORY_STRUCTURE.md).

## Experimental Campaign

| Parameter | Value |
|-----------|-------|
| Dataset | 19 Nifty 50 equities, 2020-01-01 to 2024-06-27 (1,111 days) |
| Walk-forward folds | 4 (train=504d, validation=63d, test=126d, stride=126d) |
| Random seeds | 42, 43, 44, 45, 46 |
| PPO timesteps per agent | 5,000 |
| Baseline strategies | Equal-weight, buy-and-hold, mean-variance optimisation |

### Key Results

| Metric | CA-MARL | Equal-Weight |
|--------|---------|-------------|
| Sharpe Ratio | 1.885 (95% CI: [1.809, 1.961]) | 1.931 |
| Sortino Ratio | 3.327 (95% CI: [3.096, 3.559]) | — |
| Max Drawdown | −6.5% (95% CI: [−6.7%, −6.3%]) | — |
| Cumulative Return (per fold) | 9.6% (95% CI: [9.1%, 10.0%]) | 9.5% |

Full results: `experiments/reports/research_report.md` and `manuscript/results.md`.

## Reproducibility

### Prerequisites

Python 3.11+ with the following validated environment (Python 3.14.5 used for the campaign):

- Stable-Baselines3 2.9.0
- PyTorch 2.13.0 (CPU)
- Gymnasium 1.3.0
- See `requirements.txt` for full dependency list

### Install Dependencies

```bash
pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

*Note: `elegantrl` is pinned `--no-deps` to avoid `pygame` build failures on Windows.*

### Reproduce the Campaign

```bash
# Run full experimental campaign (5 seeds, 4 folds)
python experiments/run_campaign.py

# Run single experiment
python experiments/run_ca_marl.py --seed 42 --folds 4

# Generate publication figures and tables
python experiments/run_plots.py

# Run ablation studies
python experiments/run_ablations.py

# Run baselines
python experiments/run_baselines.py
```

### Dataset

The frozen dataset (`experiments/dataset/`, v1.0.0, SHA-256 verified) is included in the repository. To regenerate from source:

```bash
python experiments/_data_cache.py
```

### Verification

```bash
pytest tests/
```

The experimental campaign includes a 47-pass verification suite (see `experiments/reports/artifact_manifest.json`).

## Manuscript

The manuscript is in `manuscript/` as individual Markdown sections:

| Section | File | Status |
|---------|------|--------|
| Methodology | `methodology.md` | Complete |
| Experimental Setup | `experimental_setup.md` | Complete |
| Results | `results.md` | Complete |
| Discussion | `discussion.md` | Complete |
| Limitations | `limitations.md` | Complete |
| Threats to Validity | `threats_to_validity.md` | Complete |
| Code and Data Availability | `availability.md` | Complete |
| References | `references.md` | 9 entries |
| Abstract | — | Not yet written |
| Introduction | — | Not yet written |
| Related Work | — | Not yet written |
| Conclusion | — | Not yet written |

Sections 1–2 (Abstract, Introduction, Related Work) and section 9 (Conclusion) are not yet drafted. The `PAPER_BLUEPRINT.md` contains planning content that may inform these sections.

## Publication Artifacts

- **Figures:** `experiments/plots/publication/figures/` (4 PDFs)
- **Tables:** `experiments/plots/publication/tables/` (4 LaTeX `.tex` files)
- **Campaign data:** `experiments/results/` (5 seed JSON files)
- **Research report:** `experiments/reports/research_report.md`
- **Dynamic verification log:** `experiments/dynamic_verify_log.txt`

## Documentation Index

| Document | Purpose |
|---|---|---|
| [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) | System design, diagrams, data/confidence flow |
| [MODULE_SPECIFICATIONS.md](./docs/architecture/MODULE_SPECIFICATIONS.md) | Research-facing: purpose, theory, math |
| [AGENTS.md](./docs/architecture/AGENTS.md) | Engineering: classes, contracts, failure cases |
| [INTERFACE_CONTRACTS.md](./docs/architecture/INTERFACE_CONTRACTS.md) | Method signatures, schemas |
| [CONFIDENCE_FUSION.md](./docs/architecture/CONFIDENCE_FUSION.md) | Primary contribution specification |
| [DECISIONS.md](./docs/architecture/DECISIONS.md) | Architecture Decision Record |
| [FINRL_MAPPING.md](./docs/architecture/FINRL_MAPPING.md) | FinRL → CA-MARL component mapping |
| [EXPERIMENT_PLAN.md](./docs/research/EXPERIMENT_PLAN.md) | Experiment design |
| [RESEARCH_MAPPING.md](./docs/research/RESEARCH_MAPPING.md) | Paper claims ↔ code/experiments |
| [TESTING_STRATEGY.md](./docs/implementation/TESTING_STRATEGY.md) | Test plan |
| [PROJECT_HANDOFF.md](./PROJECT_HANDOFF.md) | Complete project summary |

## License

MIT (inherited from FinRL — see `LICENSE`).

## Disclaimer

This is a research and educational project. Nothing in this repository constitutes financial advice or a recommendation to trade real money. This system produces recommendation objects for decision support, not executable trades.
