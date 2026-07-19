#!/usr/bin/env python
"""Master experiment runner — runs CA-MARL across multiple seeds.

Usage:
    python experiments/run_all.py [--seeds 5] [--timesteps 5000] [--folds 4]
"""

import argparse
import logging

from experiments._config import (
    DEFAULT_AGENT_CONFIGS,
    DEFAULT_CONFIDENCE,
    DEFAULT_PPO,
    DEFAULT_RISK,
    DEFAULT_UNIVERSE,
    DEFAULT_WALK_FORWARD,
    DATA_START,
    DATA_END,
    N_RANDOM_SEEDS,
    TOTAL_TIMESTEPS,
)
from experiments._evaluate import run_single_experiment
from experiments._utils import (
    configure_logging,
    load_results,
    find_all_results,
    make_timestamp,
)
from experiments._plotting import (
    save_results_table,
)

logger = logging.getLogger("run_all")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run CA-MARL experiment suite")
    parser.add_argument("--seeds", type=int, default=N_RANDOM_SEEDS,
                        help="Number of random seeds")
    parser.add_argument("--timesteps", type=int, default=TOTAL_TIMESTEPS)
    parser.add_argument("--folds", type=int, default=0,
                        help="Walk-forward folds (0 = simple train/test)")
    parser.add_argument("--start-seed", type=int, default=42)
    args = parser.parse_args()

    universe = DEFAULT_UNIVERSE
    n_folds = args.folds if args.folds > 0 else 1

    from finrl.agents.ca_marl.data_adapter import download_and_prepare

    ts = make_timestamp()
    logger.info("Downloading data...")
    data = download_and_prepare(
        ticker_list=universe,
        start_date=DATA_START,
        end_date=DATA_END,
    )
    features = data["features"]
    forward_returns = data["forward_returns"]
    realized_prices = data["realized_prices"]
    universe = data["universe"]

    logger.info("Data: features=%s, returns=%s, prices=%s, universe=%d",
                features.shape, forward_returns.shape,
                realized_prices.shape, len(universe))

    all_results: dict[str, list[dict]] = {"ca_marl": []}

    for seed in range(args.start_seed, args.start_seed + args.seeds):
        logger.info("--- Seed %d/%d ---", seed - args.start_seed + 1, args.seeds)
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
            seed=seed,
            total_timesteps=args.timesteps,
            include_baselines=True,
            n_folds=n_folds,
            walk_config=DEFAULT_WALK_FORWARD,
        )
        all_results["ca_marl"].append(result)

    # --- Aggregate across seeds ---
    print()
    print("=" * 70)
    print(f"FINAL AGGREGATED RESULTS ({args.seeds} seeds, {n_folds} fold(s))")
    print("=" * 70)

    metric_keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                   "volatility", "cumulative_return"]

    # Aggregate CA-MARL results
    for metric in metric_keys:
        values = []
        for r in all_results["ca_marl"]:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            import numpy as np
            mean_v = np.mean(values)
            std_v = np.std(values, ddof=1) if len(values) > 1 else 0.0
            print(f"  CA-MARL  {metric:20s}: {mean_v:.4f} ± {std_v:.4f} "
                  f"(over {len(values)} seeds)")

    # Aggregate baselines (first seed is representative)
    if all_results["ca_marl"] and all_results["ca_marl"][0].get("baselines"):
        print()
        print("  BASELINES (seed=%d, representative):" % args.start_seed)
        for bname, bm in all_results["ca_marl"][0]["baselines"].items():
            sr = bm.get("sharpe_ratio", "N/A")
            cr = bm.get("cumulative_return", "N/A")
            if isinstance(sr, float):
                print(f"    {bname:20s}: Sharpe={sr:.4f}, Return={cr:+.2%}")
            else:
                print(f"    {bname:20s}: Sharpe={sr}")

    print()

    # --- Save summary table ---
    summary_rows = {}
    for metric in metric_keys:
        values = []
        for r in all_results["ca_marl"]:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            import numpy as np
            summary_rows[f"ca_marl_{metric}_mean"] = float(np.mean(values))
            summary_rows[f"ca_marl_{metric}_std"] = float(
                np.std(values, ddof=1) if len(values) > 1 else 0.0
            )

    table_path = save_results_table(
        {"ca_marl_aggregated": summary_rows},
        filename=f"results_summary_{ts}.csv",
    )
    print(f"Summary table: {table_path}")
    print("Done.")


if __name__ == "__main__":
    main()
