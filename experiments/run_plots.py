#!/usr/bin/env python
"""Generate all plots and tables from experiment results.

Usage:
    python experiments/run_plots.py [--results-dir experiments/results]
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from experiments._plotting import (
    plot_ablation_bars,
    plot_cumulative_returns,
    plot_reliability_diagrams,
    plot_regime_timeline,
    save_results_table,
)
from experiments._utils import (
    RESULTS_DIR,
    configure_logging,
    find_all_results,
    load_results,
)

logger = logging.getLogger("run_plots")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Generate experiment plots")
    parser.add_argument("--results-dir", type=str, default=str(RESULTS_DIR))
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        logger.error("Results directory not found: %s", results_dir)
        return

    # --- Load all CA-MARL results ---
    ca_marl_files = sorted(results_dir.glob("ca_marl_seed_*.json"))
    if not ca_marl_files:
        logger.warning("No CA-MARL results found in %s", results_dir)
        return

    logger.info("Found %d CA-MARL result files", len(ca_marl_files))

    all_results = []
    for fpath in ca_marl_files:
        data = load_results(fpath)
        all_results.append(data)

    # --- Aggregate across seeds ---
    metric_keys = [
        "sharpe_ratio", "sortino_ratio", "max_drawdown",
        "volatility", "cumulative_return",
    ]

    aggregated: dict[str, dict[str, float]] = {}
    for metric in metric_keys:
        values = []
        for r in all_results:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            aggregated[f"ca_marl_{metric}_mean"] = float(np.mean(values))
            aggregated[f"ca_marl_{metric}_std"] = float(
                np.std(values, ddof=1) if len(values) > 1 else 0.0
            )

    # --- Aggregate baselines ---
    bnames = ["equal_weight", "buy_and_hold", "static_mvo"]
    for bname in bnames:
        for metric in metric_keys:
            vals = []
            for r in all_results:
                bm = r.get("baselines", {}).get(bname, {})
                v = bm.get(metric)
                if v is not None:
                    vals.append(v)
            if vals:
                aggregated[f"{bname}_{metric}_mean"] = float(np.mean(vals))
                aggregated[f"{bname}_{metric}_std"] = float(
                    np.std(vals, ddof=1) if len(vals) > 1 else 0.0
                )

    # --- Print summary table ---
    print()
    print("=" * 80)
    print("EXPERIMENT RESULTS SUMMARY")
    print("=" * 80)
    header = f"{'Strategy':25s} {'Sharpe':>10s} {'Sortino':>10s} {'Return':>10s} {'MaxDD':>10s} {'Vol':>10s}"
    print(header)
    print("-" * 80)

    for label in ["ca_marl"] + bnames:
        sr = aggregated.get(f"{label}_sharpe_ratio_mean", float("nan"))
        sr_std = aggregated.get(f"{label}_sharpe_ratio_std", 0)
        so = aggregated.get(f"{label}_sortino_ratio_mean", float("nan"))
        cr = aggregated.get(f"{label}_cumulative_return_mean", float("nan"))
        md = aggregated.get(f"{label}_max_drawdown_mean", float("nan"))
        vl = aggregated.get(f"{label}_volatility_mean", float("nan"))

        if not np.isnan(sr):
            print(
                f"{label:25s} {sr:>7.3f}±{sr_std:.3f} {so:>7.3f} "
                f"{cr:>+7.2%} {md:>7.2%} {vl:>7.2%}"
            )
        else:
            print(f"{label:25s} {'N/A':>10s}")

    print()

    # --- Save results table ---
    table_data = {
        strategy: {
            k: aggregated.get(f"{strategy}_{k}_mean", float("nan"))
            for k in metric_keys
        }
        for strategy in ["ca_marl"] + bnames
    }
    save_results_table(table_data)

    # --- Load ablation results ---
    ablation_files = sorted(results_dir.glob("ablations_seed_*.json"))
    if ablation_files:
        ablation_data = load_results(ablation_files[0])
        # Plot ablation bar charts
        ablation_metrics = {}
        for name, ab in ablation_data.items():
            fm = ab.get("financial_metrics", {})
            if fm:
                ablation_metrics[name] = fm
        if ablation_metrics:
            for metric in ["sharpe_ratio", "cumulative_return"]:
                plot_ablation_bars(
                    ablation_metrics, metric=metric,
                    filename=f"ablation_{metric}.png",
                )

    logger.info("All plots generated in %s", RESULTS_DIR)
    print("Plots saved to:", RESULTS_DIR.parent / "plots")


if __name__ == "__main__":
    main()
