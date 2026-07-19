"""End-to-end integration smoke test for the CA-MARL pipeline.

Validates that every module imports correctly, contracts are respected,
the pipeline completes, and a FinalRecommendation + EvaluationReport are
produced.

Reference: docs/implementation/TESTING_STRATEGY.md §2,
docs/architecture/ARCHITECTURE.md §4,
docs/architecture/INTERFACE_CONTRACTS.md.
"""

import logging
import sys


import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)


def _synthetic_features(n_timesteps: int, n_features: int) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    cols = [f"f{i}" for i in range(n_features)]
    data = rng.normal(0, 1, (n_timesteps, n_features)).cumsum(axis=0)
    return pd.DataFrame(data, columns=cols)


def _synthetic_forward_returns(
    n_timesteps: int, universe: list[str], rng: np.random.Generator
) -> pd.DataFrame:
    return pd.DataFrame(
        rng.normal(0.0005, 0.02, (n_timesteps, len(universe))),
        columns=universe,
    )


def _synthetic_prices(
    n_timesteps: int, universe: list[str], start_date: str, rng: np.random.Generator
) -> pd.DataFrame:
    dates = pd.date_range(start=start_date, periods=n_timesteps, freq="D")
    prices = 100.0 * np.exp(
        np.cumsum(rng.normal(0.0005, 0.02, (n_timesteps, len(universe))), axis=0)
    )
    prices = np.abs(prices) + 10.0
    return pd.DataFrame(prices, index=dates, columns=universe)


def test_pipeline_synthetic() -> None:
    from finrl.agents.ca_marl.config_schema import (
        AgentHyperparameters,
        ConfidenceConfig,
        PPOConfig,
        RiskManagementConfig,
    )
    from finrl.agents.ca_marl.contracts import (
        FinalRecommendation,
    )
    from finrl.agents.ca_marl.pipeline import run_pipeline

    universe = ["AAPL", "MSFT", "GOOGL"]
    n_timesteps = 100
    n_features = 8

    rng = np.random.default_rng(2024)

    features = _synthetic_features(n_timesteps, n_features)
    forward_returns = _synthetic_forward_returns(n_timesteps, universe, rng)

    # Realized prices must cover the label horizon beyond prediction time.
    # Since agents set timestamp = pd.Timestamp.now(), extend far enough
    # into the future to avoid LabelNotYetResolvableError.
    extra_days = 60
    realized_prices = _synthetic_prices(
        n_timesteps + extra_days, universe, "2024-01-01", rng,
    )

    agent_configs = {
        name: AgentHyperparameters(
            label_horizon_days=5, reward_stability_window=20
        )
        for name in ["market_agent", "risk_agent", "allocation_agent"]
    }
    ppo_config = PPOConfig(
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
    confidence_config = ConfidenceConfig(
        calibration_method="platt",
        prediction_consistency_k=5,
        historical_accuracy_weight=0.4,
        reward_stability_weight=0.3,
        prediction_consistency_weight=0.3,
    )
    risk_config = RiskManagementConfig(max_exposure_per_asset=0.4)

    logger.info("=== Running CA-MARL pipeline (synthetic data) ===")
    result = run_pipeline(
        features=features,
        forward_returns=forward_returns,
        universe=universe,
        realized_prices=realized_prices,
        agent_configs=agent_configs,
        ppo_config=ppo_config,
        confidence_config=confidence_config,
        risk_config=risk_config,
        total_timesteps=500,
    )

    # --- Assertions ---
    assert "final_recommendation" in result, "Missing final_recommendation"
    assert "evaluation_report" in result, "Missing evaluation_report"
    assert "agent_outputs" in result, "Missing agent_outputs"
    assert "calibrated_confidences" in result, "Missing calibrated_confidences"
    assert "fused_decision" in result, "Missing fused_decision"

    rec: FinalRecommendation = result["final_recommendation"]
    assert isinstance(rec.allocation, dict), "allocation must be a dict"
    assert len(rec.allocation) > 0, "allocation must not be empty"
    assert abs(sum(rec.allocation.values()) - 1.0) < 1e-6, (
        f"allocation must sum to 1.0, got {sum(rec.allocation.values())}"
    )
    assert all(v >= 0 for v in rec.allocation.values()), "all weights must be >= 0"
    for t in universe:
        assert t in rec.allocation, f"ticker {t} missing from allocation"

    assert isinstance(rec.reasoning, str) and len(rec.reasoning) > 0
    assert isinstance(rec.confidence_summary, dict)

    report = result["evaluation_report"]
    if report is not None:
        assert report.financial_metrics is not None
        assert report.calibration_metrics is not None

    agent_outputs = result["agent_outputs"]
    assert len(agent_outputs) == 3, f"Expected 3 agent outputs, got {len(agent_outputs)}"

    calibrated = result["calibrated_confidences"]
    assert len(calibrated) == 3, f"Expected 3 calibrated confidences, got {len(calibrated)}"

    fused = result["fused_decision"]
    assert fused.final_allocation is not None
    assert abs(sum(fused.final_allocation.values()) - 1.0) < 1e-6

    logger.info("=== Pipeline smoke test PASSED ===")
    logger.info("Final allocation: %s", rec.allocation)
    logger.info("Reasoning: %s", rec.reasoning[:200])
    if report is not None:
        logger.info("Financial metrics: %s", report.financial_metrics)
        logger.info("Calibration metrics: %s", report.calibration_metrics)


if __name__ == "__main__":
    test_pipeline_synthetic()
