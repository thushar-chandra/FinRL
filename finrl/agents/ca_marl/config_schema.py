"""Strongly typed configuration models for the CA-MARL system.

Each dataclass corresponds to a documented configuration group from
``configs/*.yaml``.  No file I/O, no YAML parsing, no business logic —
this file defines the schema only.

Reference: docs/implementation/DIRECTORY_STRUCTURE.md,
docs/architecture/INTERFACE_CONTRACTS.md,
docs/architecture/MODULE_SPECIFICATIONS.md,
docs/architecture/CONFIDENCE_FUSION.md,
docs/architecture/AGENTS.md,
docs/architecture/DECISIONS.md.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal


# ---------------------------------------------------------------------------
# configs/universe.yaml — ticker list + as-of date (ADR-011)
# ---------------------------------------------------------------------------

@dataclass
class UniverseConfig:
    """Fixed-universe specification.

    The ticker list and as-of selection date together define the investment
    universe and prevent hindsight bias (ADR-011).  ``as_of_date`` is the
    date at which the ticker list was frozen — any stock delisted or listed
    after this date is excluded.

    Reference: DIRECTORY_STRUCTURE.md (configs/universe.yaml),
    DECISIONS.md ADR-011.
    """

    tickers: Sequence[str]
    as_of_date: date


# ---------------------------------------------------------------------------
# configs/features.yaml — feature engineering parameters
# ---------------------------------------------------------------------------

@dataclass
class FeatureEngineeringConfig:
    """Feature engineering parameters.

    Controls the computation of technical indicators, return / volatility
    features, rolling statistics, correlation, and regime features
    (bull/bear, volatility regime, trend regime, market-state).

    ``technical_indicators`` is a list of stockstats-style column names
    (e.g. ``["macd", "rsi_30", "close_30_sma", "boll_ub", "boll_lb"]``).

    Reference: ARCHITECTURE.md §1, TASKS.md T-005,
    DIRECTORY_STRUCTURE.md (configs/features.yaml).
    """

    technical_indicators: Sequence[str]
    return_windows: Sequence[int]
    volatility_ewma_span: int
    correlation_window: int


# ---------------------------------------------------------------------------
# configs/agents.yaml — per-agent hyperparameters
# ---------------------------------------------------------------------------

@dataclass
class AgentHyperparameters:
    """Hyperparameters shared across the three specialised RL agents.

    Each agent (Market, Risk, Allocation) has its own instance of this
    config, allowing per-agent values for ``label_horizon_days`` and
    ``reward_stability_window``.

    ``epsilon`` is used by ``ConfidenceAwareFusion._risk_to_proposal``
    to avoid division by zero.

    Reference: AGENTS.md (§1-3), INTERFACE_CONTRACTS.md (§1-4),
    CONFIDENCE_FUSION.md (worked example).
    """

    label_horizon_days: int
    reward_stability_window: int
    epsilon: float = 1e-6


# ---------------------------------------------------------------------------
# configs/ppo.yaml — PPO hyperparameters
# ---------------------------------------------------------------------------

@dataclass
class PPOConfig:
    """PPO hyperparameters used by Stable-Baselines3 ``PPO``.

    All fields are required (no defaults) — the exact values depend on
    the asset universe and are configured at deployment time.

    Reference: DIRECTORY_STRUCTURE.md (configs/ppo.yaml),
    IMPLEMENTATION_ROADMAP.md Stage 2, FINRL_MAPPING.md.
    """

    learning_rate: float
    n_steps: int
    batch_size: int
    gamma: float
    gae_lambda: float
    clip_range: float
    ent_coef: float
    vf_coef: float
    max_grad_norm: float


# ---------------------------------------------------------------------------
# configs/confidence.yaml — confidence estimation & calibration parameters
# ---------------------------------------------------------------------------

@dataclass
class ConfidenceConfig:
    """Parameters for the Confidence Estimation & Calibration module.

    ``calibration_method`` selects the mapping from raw to calibrated
    confidence (Platt scaling or temperature scaling — the final choice
    is recorded in ``DECISIONS.md`` per the implementation contract).

    The three weight fields control how ``estimate_raw_confidence``
    combines its inputs (historical accuracy, reward stability, prediction
    consistency).  The exact combination function, including these weights,
    is an implementation detail resolved during Stage 3.

    ``prediction_consistency_k`` is the number of nearby historical
    states sampled for the prediction-consistency check (ADR-023).

    Reference: DIRECTORY_STRUCTURE.md (configs/confidence.yaml),
    MODULE_SPECIFICATIONS.md §4, DECISIONS.md ADR-023.
    """

    calibration_method: Literal["platt", "temperature"]
    prediction_consistency_k: int
    historical_accuracy_weight: float
    reward_stability_weight: float
    prediction_consistency_weight: float


# ---------------------------------------------------------------------------
# configs/walk_forward.yaml — walk-forward validation parameters
# ---------------------------------------------------------------------------

@dataclass
class WalkForwardConfig:
    """Walk-forward validation structure.

    ``n_folds`` is the number of chronological folds.
    ``training_window_days``, ``validation_window_days``, and
    ``test_window_days`` define the size of each fold's windows.
    ``retrain_on`` controls when the agents are retrained: ``"every_fold"``
    (retrain from scratch each fold) or ``"expanding"`` (expand the
    training window without full retrain).

    Reference: DIRECTORY_STRUCTURE.md (configs/walk_forward.yaml),
    TASKS.md T-018, IMPLEMENTATION_ROADMAP.md Stage 1 / Stage 4.
    """

    n_folds: int
    training_window_days: int
    validation_window_days: int
    test_window_days: int
    retrain_on: Literal["every_fold", "expanding"]


# ---------------------------------------------------------------------------
# Risk-management parameters — referenced in configs/*.yaml
# ---------------------------------------------------------------------------

@dataclass
class RiskManagementConfig:
    """Risk-management constraint parameters.

    ``max_exposure_per_asset`` is the upper bound on any single asset's
    weight in the final allocation (the "exposure cap" referenced across
    the pipeline documentation).

    Reference: AGENTS.md §6, INTERFACE_CONTRACTS.md §6,
    MODULE_SPECIFICATIONS.md §6.
    """

    max_exposure_per_asset: float


# ---------------------------------------------------------------------------
# Top-level composed configuration
# ---------------------------------------------------------------------------

@dataclass
class CAMARLConfig:
    """Complete configuration for the CA-MARL pipeline.

    Composes every per-file config group into a single typed object.
    This is the schema that a YAML/JSON loader would populate at startup.
    """

    universe: UniverseConfig
    features: FeatureEngineeringConfig
    market_agent: AgentHyperparameters
    risk_agent: AgentHyperparameters
    allocation_agent: AgentHyperparameters
    ppo: PPOConfig
    confidence: ConfidenceConfig
    walk_forward: WalkForwardConfig
    risk_management: RiskManagementConfig
