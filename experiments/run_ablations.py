#!/usr/bin/env python
"""Run all CA-MARL ablation studies.

Usage:
    python experiments/run_ablations.py [--seed 42] [--timesteps 5000]
"""

import argparse
import logging
import sys

from experiments._ablations import (
    run_drop_one_agent,
    run_equal_weight_fusion,
    run_no_calibration,
    run_shuffled_confidence,
)
from experiments._config import (
    DEFAULT_AGENT_CONFIGS,
    DEFAULT_CONFIDENCE,
    DEFAULT_PPO,
    DEFAULT_RISK,
    DEFAULT_UNIVERSE,
    DATA_START,
    DATA_END,
    TOTAL_TIMESTEPS,
)
from experiments._utils import (
    configure_logging,
    result_path,
    save_results,
    set_all_seeds,
)

logger = logging.getLogger("run_ablations")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run CA-MARL ablation studies")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timesteps", type=int, default=TOTAL_TIMESTEPS)
    args = parser.parse_args()

    set_all_seeds(args.seed)
    universe = DEFAULT_UNIVERSE

    from finrl.agents.ca_marl.confidence_engine import (
        ConfidenceEngine,
        OutcomeLabelGenerator,
    )
    from finrl.agents.ca_marl.data_adapter import download_and_prepare
    from finrl.agents.ca_marl.evaluation import EvaluationEngine
    from experiments._pipeline import train_and_infer

    data = download_and_prepare(
        ticker_list=universe,
        start_date=DATA_START,
        end_date=DATA_END,
    )
    features = data["features"]
    forward_returns = data["forward_returns"]
    realized_prices = data["realized_prices"]
    universe = data["universe"]

    split = int(len(features) * 0.8)
    train_feat = features.iloc[:split]
    train_ret = forward_returns.iloc[:split]
    test_feat = features.iloc[split:]
    test_prices = realized_prices.iloc[split:]

    label_horizon = max(c.label_horizon_days for c in DEFAULT_AGENT_CONFIGS.values())
    eval_end = min(split + label_horizon + 5, len(realized_prices))
    eval_prices = realized_prices.iloc[split:eval_end]

    outcome_label_gen = OutcomeLabelGenerator(DEFAULT_AGENT_CONFIGS)

    result = train_and_infer(
        train_features=train_feat,
        train_forward_returns=train_ret,
        test_features=test_feat,
        test_realized_prices=test_prices,
        eval_realized_prices=eval_prices,
        universe=universe,
        agent_configs=DEFAULT_AGENT_CONFIGS,
        ppo_config=DEFAULT_PPO,
        confidence_config=DEFAULT_CONFIDENCE,
        risk_config=DEFAULT_RISK,
        total_timesteps=args.timesteps,
        outcome_label_gen=outcome_label_gen,
    )

    agent_outputs = result["agent_outputs"]
    calibrated = result["calibrated_confidences"]
    eval_engine = EvaluationEngine(outcome_label_gen)

    # --- Run ablations ---
    ablations: dict[str, dict] = {
        "ca_marl": {
            "financial_metrics": {
                "sharpe_ratio": result["evaluation_report"].financial_metrics.sharpe_ratio,
                "sortino_ratio": result["evaluation_report"].financial_metrics.sortino_ratio,
                "max_drawdown": result["evaluation_report"].financial_metrics.max_drawdown,
                "volatility": result["evaluation_report"].financial_metrics.volatility,
                "cumulative_return": result["evaluation_report"].financial_metrics.cumulative_return,
            }
        } if result["evaluation_report"] else {},
    }

    logger.info("Running ablation: equal_weight_fusion")
    ablations["equal_weight_fusion"] = run_equal_weight_fusion(
        agent_outputs, calibrated, universe,
        DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices,
    )

    logger.info("Running ablation: no_calibration")
    ablations["no_calibration"] = run_no_calibration(
        agent_outputs, calibrated, universe,
        DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices,
        raw_confidences=result["raw_confidences"],
    )

    logger.info("Running ablation: shuffled_confidence")
    ablations["shuffled_confidence"] = run_shuffled_confidence(
        agent_outputs, calibrated, universe,
        DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices,
        seed=args.seed + 999,
    )

    for drop in ["market_agent", "risk_agent", "allocation_agent"]:
        logger.info("Running ablation: drop_one_agent (%s)", drop)
        ablations[f"drop_{drop}"] = run_drop_one_agent(
            agent_outputs, calibrated, universe,
            DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices,
            drop_agent=drop,
        )

    # --- Print results ---
    print()
    print("=" * 60)
    print("ABLATION RESULTS")
    print("=" * 60)
    for name, ab in ablations.items():
        fm = ab.get("financial_metrics", {})
        sr = fm.get("sharpe_ratio", "N/A")
        cr = fm.get("cumulative_return", "N/A")
        if isinstance(sr, float):
            print(f"  {name:25s}: Sharpe={sr:.4f}, Return={cr:+.2%}")
        else:
            print(f"  {name:25s}: Sharpe={sr}")

    # --- Save ---
    path = result_path("ablations", args.seed)
    save_results(ablations, path)
    print(f"  Results saved: {path}")
    print()


if __name__ == "__main__":
    main()
