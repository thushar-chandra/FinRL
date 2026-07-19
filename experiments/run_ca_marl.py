#!/usr/bin/env python
"""Run the CA-MARL pipeline with walk-forward validation.

Usage:
    python experiments/run_ca_marl.py [--seed 42] [--folds 4] [--timesteps 5000]
"""

import argparse
import logging
import sys

import numpy as np

from experiments._config import (
    DEFAULT_AGENT_CONFIGS,
    DEFAULT_CONFIDENCE,
    DEFAULT_PPO,
    DEFAULT_RISK,
    DEFAULT_UNIVERSE,
    DEFAULT_WALK_FORWARD,
    DATA_START,
    DATA_END,
    TOTAL_TIMESTEPS,
)
from experiments._evaluate import run_single_experiment
from experiments._utils import configure_logging, load_results, find_all_results

logger = logging.getLogger("run_ca_marl")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run CA-MARL experiment")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--folds", type=int, default=1,
                        help="Number of walk-forward folds (1 = simple train/test)")
    parser.add_argument("--timesteps", type=int, default=TOTAL_TIMESTEPS,
                        help="PPO training timesteps per agent")
    parser.add_argument("--universe", type=str, default="default",
                        choices=["default", "dow30"],
                        help="Ticker universe")
    args = parser.parse_args()

    universe = DEFAULT_UNIVERSE

    logger.info("=" * 60)
    logger.info("CA-MARL Experiment")
    logger.info("  Universe: %d tickers", len(universe))
    logger.info("  Seed:     %d", args.seed)
    logger.info("  Folds:    %d", args.folds)
    logger.info("  Timesteps: %d", args.timesteps)
    logger.info("=" * 60)

    from finrl.agents.ca_marl.data_adapter import download_and_prepare

    data = download_and_prepare(
        ticker_list=universe,
        start_date=DATA_START,
        end_date=DATA_END,
    )

    features = data["features"]
    forward_returns = data["forward_returns"]
    realized_prices = data["realized_prices"]
    universe = data["universe"]

    logger.info("Data shapes: features=%s, returns=%s, prices=%s",
                features.shape, forward_returns.shape, realized_prices.shape)

    result = run_single_experiment(
        features=features,
        forward_returns=forward_returns,
        realized_prices=realized_prices,
        universe=universe,
        agent_configs=DEFAULT_AGENT_CONFIGS,
        ppo_config=DEFAULT_PPO,
        confidence_config=DEFAULT_CONFIDENCE,
        risk_config=DEFAULT_RISK,
        experiment_name="ca_marl",
        seed=args.seed,
        total_timesteps=args.timesteps,
        include_baselines=True,
        n_folds=args.folds,
        walk_config=DEFAULT_WALK_FORWARD,
    )

    agg = result.get("aggregated", {})
    print()
    print("=" * 60)
    print("CA-MARL RESULTS (aggregated across folds)")
    print("=" * 60)
    for metric, stats in agg.items():
        if stats.get("mean") is not None:
            print(f"  {metric:20s}: {stats['mean']:.4f} ± {stats['std']:.4f}")
        else:
            print(f"  {metric:20s}: N/A")
    print()

    if result.get("baselines"):
        print("BASELINES:")
        for name, bm in result["baselines"].items():
            sr = bm.get("sharpe_ratio", "N/A")
            if isinstance(sr, float):
                print(f"  {name:20s}: Sharpe={sr:.4f}, "
                      f"Return={bm.get('cumulative_return', 'N/A')}")
            else:
                print(f"  {name:20s}: Sharpe={sr}")

    print()


if __name__ == "__main__":
    main()
