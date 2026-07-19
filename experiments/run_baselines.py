#!/usr/bin/env python
"""Run baseline strategies and store results.

Usage:
    python experiments/run_baselines.py
"""

import argparse
import logging

from experiments._baselines import run_all_baselines
from experiments._config import (
    DEFAULT_UNIVERSE,
    DATA_START,
    DATA_END,
)
from experiments._utils import (
    configure_logging,
    result_path,
    save_results,
    set_all_seeds,
)

logger = logging.getLogger("run_baselines")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run baseline strategies")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_all_seeds(args.seed)
    universe = DEFAULT_UNIVERSE

    from finrl.agents.ca_marl.data_adapter import download_and_prepare

    data = download_and_prepare(
        ticker_list=universe,
        start_date=DATA_START,
        end_date=DATA_END,
    )
    realized_prices = data["realized_prices"]

    logger.info("Running baselines on %d assets, %d timesteps",
                len(realized_prices.columns), len(realized_prices))

    metrics = run_all_baselines(realized_prices)

    print()
    print("=" * 60)
    print("BASELINE RESULTS")
    print("=" * 60)
    for name, m in metrics.items():
        print(f"  {name:20s}: Sharpe={m.sharpe_ratio:.4f}, "
              f"Sortino={m.sortino_ratio:.4f}, "
              f"Return={m.cumulative_return:+.2%}, "
              f"MaxDD={m.max_drawdown:.4f}")
    print()

    results = {
        name: {
            "sharpe_ratio": m.sharpe_ratio,
            "sortino_ratio": m.sortino_ratio,
            "max_drawdown": m.max_drawdown,
            "volatility": m.volatility,
            "cumulative_return": m.cumulative_return,
        }
        for name, m in metrics.items()
    }

    path = result_path("baselines", args.seed)
    save_results(results, path)
    print(f"Results saved: {path}")


if __name__ == "__main__":
    main()
