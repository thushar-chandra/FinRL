"""Execute the CA-MARL pipeline on real historical market data.

Downloads a small universe (3 tickers, ~2 years) via Yahoo Finance,
prepares features using FinRL's existing FeatureEngineer, trains agents,
runs inference, and produces a FinalRecommendation + EvaluationReport.

Reference: docs/architecture/ARCHITECTURE.md §4,
docs/implementation/TESTING_STRATEGY.md §2.
"""

import logging
import sys


logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)

UNIVERSE = ["AAPL", "MSFT", "GOOGL"]
START_DATE = "2022-01-01"
END_DATE = "2023-12-31"


def main() -> None:
    from finrl.agents.ca_marl.config_schema import (
        AgentHyperparameters,
        ConfidenceConfig,
        PPOConfig,
        RiskManagementConfig,
    )
    from finrl.agents.ca_marl.data_adapter import download_and_prepare
    from finrl.agents.ca_marl.pipeline import run_pipeline

    # ------------------------------------------------------------------
    # Phase 1: Data preparation (uses FinRL's existing pipeline)
    # ------------------------------------------------------------------
    logger.info("=== Phase 1: Data preparation ===")
    logger.info("Universe: %s", UNIVERSE)
    logger.info("Period: %s to %s", START_DATE, END_DATE)

    data = download_and_prepare(
        ticker_list=UNIVERSE,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    features = data["features"]
    forward_returns = data["forward_returns"]
    realized_prices = data["realized_prices"]
    universe = data["universe"]

    logger.info("Features shape: %s", features.shape)
    logger.info("Forward returns shape: %s", forward_returns.shape)
    logger.info("Realized prices shape: %s", realized_prices.shape)

    n_timesteps = len(features)
    if n_timesteps < 20:
        logger.error("Too few timesteps (%d); aborting.", n_timesteps)
        return

    # ------------------------------------------------------------------
    # Phase 2: Configuration
    # ------------------------------------------------------------------
    logger.info("=== Phase 2: Configuration ===")
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

    # ------------------------------------------------------------------
    # Phase 3: Pipeline execution
    # ------------------------------------------------------------------
    logger.info("=== Phase 3: Pipeline execution ===")
    result = run_pipeline(
        features=features,
        forward_returns=forward_returns,
        universe=universe,
        realized_prices=realized_prices,
        agent_configs=agent_configs,
        ppo_config=ppo_config,
        confidence_config=confidence_config,
        risk_config=risk_config,
        total_timesteps=2000,
    )

    # ------------------------------------------------------------------
    # Phase 4: Results
    # ------------------------------------------------------------------
    logger.info("=== Phase 4: Results ===")
    rec = result["final_recommendation"]
    report = result["evaluation_report"]
    fused = result["fused_decision"]

    logger.info("Final allocation: %s", dict(sorted(rec.allocation.items())))
    logger.info("Allocation sum: %.6f", sum(rec.allocation.values()))
    logger.info("Reasoning: %s", rec.reasoning)
    logger.info("Confidence summary: %s", rec.confidence_summary)

    if report is not None:
        fm = report.financial_metrics
        logger.info("Financial metrics:")
        logger.info("  Sharpe Ratio:      %.4f", fm.sharpe_ratio)
        logger.info("  Sortino Ratio:     %.4f", fm.sortino_ratio)
        logger.info("  Max Drawdown:      %.4f", fm.max_drawdown)
        logger.info("  Volatility:        %.4f", fm.volatility)
        logger.info("  Cumulative Return: %.4f", fm.cumulative_return)
        logger.info("Calibration metrics: %s", report.calibration_metrics)
    else:
        logger.warning("No evaluation report produced.")

    logger.info("Fused decision allocation: %s", fused.final_allocation)
    logger.info("Fusion metadata: %s", fused.fusion_metadata)

    logger.info("=== Historical execution COMPLETE ===")


if __name__ == "__main__":
    main()
