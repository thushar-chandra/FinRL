"""Experiment configuration — all tunable parameters in one place."""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from finrl.agents.ca_marl.config_schema import (
    AgentHyperparameters,
    ConfidenceConfig,
    PPOConfig,
    RiskManagementConfig,
    WalkForwardConfig,
)


# ---------------------------------------------------------------------------
# Default universe — Indian large-cap equity (Nifty 50 constituents as proxy)
# ---------------------------------------------------------------------------
# ADR-011: fixed as-of date prevents hindsight bias.

DEFAULT_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "WIPRO.NS", "AXISBANK.NS", "TITAN.NS", "ASIANPAINT.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "NTPC.NS", "POWERGRID.NS",
]
UNIVERSE_AS_OF_DATE = date(2024, 1, 1)


# ---------------------------------------------------------------------------
# Default data range
# ---------------------------------------------------------------------------

DATA_START = "2020-01-01"
DATA_END = "2024-06-30"


# ---------------------------------------------------------------------------
# Walk-forward parameters
# ---------------------------------------------------------------------------

DEFAULT_WALK_FORWARD = WalkForwardConfig(
    n_folds=4,
    training_window_days=504,    # ~2 trading years
    validation_window_days=63,   # ~3 months
    test_window_days=126,        # ~6 months
    retrain_on="every_fold",
)


# ---------------------------------------------------------------------------
# Agent hyperparameters
# ---------------------------------------------------------------------------

DEFAULT_AGENT_CONFIGS: dict[str, AgentHyperparameters] = {
    name: AgentHyperparameters(
        label_horizon_days=5,
        reward_stability_window=20,
    )
    for name in ["market_agent", "risk_agent", "allocation_agent"]
}


# ---------------------------------------------------------------------------
# PPO hyperparameters (defaults, may be tuned)
# ---------------------------------------------------------------------------

DEFAULT_PPO = PPOConfig(
    learning_rate=3e-4,
    n_steps=128,
    batch_size=32,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    vf_coef=0.5,
    max_grad_norm=0.5,
)


# ---------------------------------------------------------------------------
# Confidence estimation parameters
# ---------------------------------------------------------------------------

DEFAULT_CONFIDENCE = ConfidenceConfig(
    calibration_method="platt",
    prediction_consistency_k=5,
    historical_accuracy_weight=0.4,
    reward_stability_weight=0.3,
    prediction_consistency_weight=0.3,
)


# ---------------------------------------------------------------------------
# Risk management
# ---------------------------------------------------------------------------

DEFAULT_RISK = RiskManagementConfig(max_exposure_per_asset=0.4)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

TOTAL_TIMESTEPS = 5000  # increased from smoke-test value of 2000


# ---------------------------------------------------------------------------
# Experiment metadata
# ---------------------------------------------------------------------------

N_RANDOM_SEEDS = 5  # for statistical rigor (EXPERIMENT_PLAN.md)


# ---------------------------------------------------------------------------
# Walk-forward schedule generator
# ---------------------------------------------------------------------------

@dataclass
class FoldSchedule:
    train_start: int
    train_end: int
    val_start: int
    val_end: int
    test_start: int
    test_end: int


def build_fold_schedules(
    n_timesteps: int,
    config: WalkForwardConfig,
) -> list[FoldSchedule]:
    """Generate chronological fold indices.

    Each fold:
      - training:  [train_start, train_end)
      - validation: [val_start,     val_end)
      - test:       [test_start,    test_end)

    All indices are non-overlapping and advancing.
    """
    tw = config.training_window_days
    vw = config.validation_window_days
    testw = config.test_window_days
    stride = testw  # non-overlapping test windows

    folds: list[FoldSchedule] = []
    cursor = 0
    for _ in range(config.n_folds):
        if cursor + tw + vw + testw > n_timesteps:
            break
        folds.append(FoldSchedule(
            train_start=cursor,
            train_end=cursor + tw,
            val_start=cursor + tw,
            val_end=cursor + tw + vw,
            test_start=cursor + tw + vw,
            test_end=cursor + tw + vw + testw,
        ))
        cursor += stride

    return folds
