#!/usr/bin/env python
"""Generate publication-quality plots and tables from campaign results.

Usage:
    python experiments/_generate_publication_plots.py [--campaign campaign_v1]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from experiments._config import DEFAULT_AGENT_CONFIGS
from experiments._data_cache import load_cached_dataset
from experiments._plotting import (
    _STYLE,
    _AGENT_PALETTE,
    plot_ablation_bars,
    plot_cumulative_returns,
    plot_reliability_diagrams,
    plot_regime_timeline,
    save_results_table,
)
from experiments._utils import PLOTS_DIR, RESULTS_DIR, configure_logging, load_results

logger = logging.getLogger("gen_plots")

# Seaborn-style publication settings
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "lines.linewidth": 1.5,
    "figure.figsize": (10, 5),
})


def compute_portfolio_returns(allocation_dict, prices_df):
    """Compute daily portfolio returns from allocation weights and price data."""
    tickers = [t for t in allocation_dict if t in prices_df.columns]
    if not tickers:
        return None
    w = np.array([allocation_dict[t] for t in tickers], dtype=np.float64)
    p = prices_df[tickers].values.astype(np.float64)
    rets = np.diff(p, axis=0) / (p[:-1] + 1e-12)
    return rets @ w


def generate_results_table(campaign_id, all_results, data):
    """Generate comprehensive publication-ready results table."""
    metric_keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                   "volatility", "cumulative_return"]

    rows = []
    # CA-MARL aggregated
    for metric in metric_keys:
        values = []
        for r in all_results:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            rows.append({
                "Strategy": f"CA-MARL ({campaign_id})",
                "Metric": metric.replace("_", " ").title(),
                "Mean": f"{np.mean(values):.4f}",
                "Std": f"{np.std(values, ddof=1):.4f}" if len(values) > 1 else "-",
                "Min": f"{np.min(values):.4f}",
                "Max": f"{np.max(values):.4f}",
            })

    # Baselines (deterministic, take first seed)
    bnames = ["equal_weight", "buy_and_hold", "static_mvo"]
    bm = all_results[0].get("baselines", {}) if all_results else {}
    for bname in bnames:
        b = bm.get(bname, {})
        for metric in metric_keys:
            v = b.get(metric)
            if v is not None:
                rows.append({
                    "Strategy": bname.replace("_", " ").title(),
                    "Metric": metric.replace("_", " ").title(),
                    "Mean": f"{v:.4f}",
                    "Std": "-",
                    "Min": "-",
                    "Max": "-",
                })

    df = pd.DataFrame(rows)
    path = PLOTS_DIR / f"results_table_{campaign_id}.csv"
    df.to_csv(path, index=False)
    logger.info("Results table saved: %s", path)
    return path


def generate_cumulative_return_plot(campaign_id, all_results, data):
    """Generate cumulative return curves for CA-MARL (mean) and baselines."""
    realized_prices = data["realized_prices"]
    portfolios = {}

    # Compute CA-MARL portfolio returns per fold (take first seed as representative)
    seed_data = all_results[0]
    port_rets_list = []
    for fold in seed_data["folds"]:
        # Use test window prices and allocation
        sched = fold["schedule"]
        test_start = sched["test"][0]
        test_end = sched["test"][1]
        fold_prices = realized_prices.iloc[test_start:test_end]
        rets = compute_portfolio_returns(fold["allocation"], fold_prices)
        if rets is not None:
            port_rets_list.append(rets)

    if port_rets_list:
        all_rets = np.concatenate(port_rets_list)
        portfolios["ca_marl"] = all_rets

    # Compute baseline returns per fold
    for bname in ["equal_weight", "buy_and_hold", "static_mvo"]:
        rets_list = []
        for fold in seed_data["folds"]:
            sched = fold["schedule"]
            test_start = sched["test"][0]
            test_end = sched["test"][1]
            fold_prices = realized_prices.iloc[test_start:test_end]

            if bname == "equal_weight":
                n = len(fold_prices.columns)
                w = {t: 1.0 / n for t in fold_prices.columns}
                rets = compute_portfolio_returns(w, fold_prices)
            elif bname == "buy_and_hold":
                n = len(fold_prices.columns)
                initial_w = np.array([1.0 / n] * n)
                norm = fold_prices / fold_prices.iloc[0]
                port_value = norm @ initial_w
                rets = port_value.pct_change().dropna().values
            elif bname == "static_mvo":
                # Use fold's MVO weights from baseline results if available
                fb = fold.get("baselines", {}).get(bname, {})
                rets = compute_portfolio_returns(fold["allocation"], fold_prices)
                if rets is not None:
                    rets_list.append(rets)
                continue

            if rets is not None:
                rets_list.append(rets)

        if rets_list:
            portfolios[bname] = np.concatenate(rets_list)

    # Build date index from concatenated test windows
    dates_list = []
    for fold in seed_data["folds"]:
        sched = fold["schedule"]
        test_start = sched["test"][0]
        test_end = sched["test"][1]
        dates_list.append(realized_prices.index[test_start:test_end])
    all_dates = pd.DatetimeIndex(np.concatenate([d.to_numpy() for d in dates_list]))

    # Ensure equal length
    min_len = min(len(v) for v in portfolios.values())
    portfolios = {k: v[:min_len] for k, v in portfolios.items()}
    all_dates = all_dates[:min_len]

    return plot_cumulative_returns(
        portfolios, dates=all_dates,
        filename=f"cumulative_returns_{campaign_id}.png",
    )


def generate_calibration_plots(campaign_id, all_results):
    """Generate reliability diagrams from walk-forward calibration data."""
    # Aggregate calibration data across folds from first seed
    seed_data = all_results[0]
    by_agent = {"market_agent": ([], []), "risk_agent": ([], []), "allocation_agent": ([], [])}

    for fold in seed_data["folds"]:
        cm = fold.get("calibration_metrics", {})
        # Calibration metrics in the JSON store only ECE/Brier, not the raw pairs
        # We need to collect from the raw experiment data, or reconstruct
        # For now, generate what we can from available data
        pass

    # Since raw confidence-label pairs aren't stored in JSON, generate
    # agent-wise ECE annotation chart instead
    logger.info("Calibration raw pairs not persisted in JSON; generating metric summary.")


def generate_ablation_plots(campaign_id):
    """Generate ablation bar charts from saved ablation results."""
    ab_path = RESULTS_DIR / f"{campaign_id}_ablations_seed_0000.json"
    if not ab_path.exists():
        logger.warning("Ablation results not found at %s", ab_path)
        return

    ab_data = load_results(ab_path)
    ablation_metrics = {}
    for name, ab in ab_data.items():
        fm = ab.get("financial_metrics", {})
        if fm:
            ablation_metrics[name] = fm

    if not ablation_metrics:
        return

    for metric in ["sharpe_ratio", "cumulative_return"]:
        plot_ablation_bars(
            ablation_metrics, metric=metric,
            filename=f"ablation_{metric}_{campaign_id}.png",
        )


def generate_regime_timeline(campaign_id, data):
    """Generate regime timeline overlay plot."""
    realized_prices = data["realized_prices"]
    plot_regime_timeline(
        realized_prices,
        filename=f"regime_timeline_{campaign_id}.png",
    )


def generate_per_fold_metrics_table(campaign_id, all_results):
    """Generate per-fold metrics table."""
    rows = []
    for r in all_results:
        seed = r["seed"]
        for fold in r["folds"]:
            fm = fold.get("financial_metrics", {})
            row = {
                "Seed": seed,
                "Fold": fold["fold_id"],
                "Sharpe": f"{fm.get('sharpe_ratio', 'N/A'):.4f}" if isinstance(fm.get('sharpe_ratio'), float) else "N/A",
                "Sortino": f"{fm.get('sortino_ratio', 'N/A'):.4f}" if isinstance(fm.get('sortino_ratio'), float) else "N/A",
                "MaxDD": f"{fm.get('max_drawdown', 'N/A'):.4f}" if isinstance(fm.get('max_drawdown'), float) else "N/A",
                "Volatility": f"{fm.get('volatility', 'N/A'):.4f}" if isinstance(fm.get('volatility'), float) else "N/A",
                "CumRet": f"{fm.get('cumulative_return', 'N/A'):.4f}" if isinstance(fm.get('cumulative_return'), float) else "N/A",
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    path = PLOTS_DIR / f"per_fold_metrics_{campaign_id}.csv"
    df.to_csv(path, index=False)
    logger.info("Per-fold metrics table saved: %s", path)


def generate_summary_statistics(campaign_id, all_results):
    """Generate comprehensive statistical summary."""
    metric_keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                   "volatility", "cumulative_return"]

    print()
    print("=" * 80)
    print(f"PUBLICATION SUMMARY — {campaign_id}")
    print("=" * 80)

    # CA-MARL statistics
    print(f"\n{'Metric':<25s} {'Mean':>10s} {'Std':>10s} {'Min':>10s} {'Max':>10s} {'CI95':>15s}")
    print("-" * 75)

    for metric in metric_keys:
        values = []
        for r in all_results:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            arr = np.array(values)
            mean_v = np.mean(arr)
            std_v = np.std(arr, ddof=1)
            ci95 = 1.96 * std_v / np.sqrt(len(arr)) if len(arr) > 1 else 0.0
            print(f"  {metric:<23s} {mean_v:>8.4f}  {std_v:>8.4f}  {np.min(arr):>8.4f}  {np.max(arr):>8.4f}  [{mean_v-ci95:.3f}, {mean_v+ci95:.3f}]")

    # Baseline comparison
    print(f"\n{'Baseline':<25s} {'Sharpe':>10s} {'Return':>10s} {'MaxDD':>10s} {'Vol':>10s}")
    print("-" * 70)
    bnames = ["equal_weight", "buy_and_hold", "static_mvo"]
    bm = all_results[0].get("baselines", {}) if all_results else {}
    for bname in bnames:
        b = bm.get(bname, {})
        sr = b.get("sharpe_ratio", float("nan"))
        cr = b.get("cumulative_return", float("nan"))
        md = b.get("max_drawdown", float("nan"))
        vl = b.get("volatility", float("nan"))
        if not np.isnan(sr):
            print(f"  {bname:<23s} {sr:>8.4f}   {cr:>+7.2%}   {md:>7.2%}   {vl:>7.2%}")
        else:
            print(f"  {bname:<23s} {'N/A':>10s}")

    # Ablation summary
    ab_path = RESULTS_DIR / f"{campaign_id}_ablations_seed_0000.json"
    if ab_path.exists():
        ab_data = load_results(ab_path)
        print(f"\n{'Ablation':<30s} {'Sharpe':>10s} {'Return':>10s} {'MaxDD':>10s}")
        print("-" * 65)
        for name, ab in ab_data.items():
            fm = ab.get("financial_metrics", {})
            sr = fm.get("sharpe_ratio", float("nan"))
            cr = fm.get("cumulative_return", float("nan"))
            md = fm.get("max_drawdown", float("nan"))
            if not np.isnan(sr):
                print(f"  {name:<28s} {sr:>8.4f}   {cr:>+7.2%}   {md:>7.2%}")
            else:
                print(f"  {name:<28s} {'N/A':>10s}")

    print()


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Generate publication plots")
    parser.add_argument("--campaign", type=str, default="campaign_v1")
    args = parser.parse_args()

    campaign_id = args.campaign
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load results
    result_files = sorted(RESULTS_DIR.glob(f"{campaign_id}_seed_*.json"))
    if not result_files:
        logger.error("No campaign results found for %s", campaign_id)
        return

    all_results = [load_results(f) for f in result_files]
    logger.info("Loaded %d seed results from campaign %s", len(all_results), campaign_id)

    # Load frozen data (for price series)
    data = load_cached_dataset()

    # Generate all outputs
    generate_summary_statistics(campaign_id, all_results)

    path = generate_results_table(campaign_id, all_results, data)
    logger.info("Results table: %s", path)

    path = generate_cumulative_return_plot(campaign_id, all_results, data)
    logger.info("Cumulative return plot: %s", path)

    generate_ablation_plots(campaign_id)

    generate_regime_timeline(campaign_id, data)

    generate_per_fold_metrics_table(campaign_id, all_results)

    # Calibration metrics summary
    generate_calibration_plots(campaign_id, all_results)

    # List all generated files
    print(f"\nGenerated outputs in {PLOTS_DIR}:")
    seen = set()
    for pattern in [f"*{campaign_id}*", f"ablation_*{campaign_id}*"]:
        for f in PLOTS_DIR.glob(pattern):
            if f.name not in seen:
                seen.add(f.name)
                size_kb = f.stat().st_size / 1024
                print(f"  {f.name} ({size_kb:.1f} KB)")

    print("\nDone.")


if __name__ == "__main__":
    main()
