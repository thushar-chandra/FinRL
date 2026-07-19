#!/usr/bin/env python
"""Master campaign runner — frozen dataset, 5 seeds, 4 folds, 5000 timesteps.

This script is the single entry point for the publication-ready experimental
campaign.  It loads the frozen dataset (downloads and caches once), runs all
seeds, and saves results under a campaign-specific identifier.

Usage:
    python experiments/run_campaign.py [--campaign campaign_v1]
"""

import argparse
import logging
import sys
import time

import numpy as np

from experiments._config import (
    DEFAULT_AGENT_CONFIGS,
    DEFAULT_CONFIDENCE,
    DEFAULT_PPO,
    DEFAULT_RISK,
    DEFAULT_WALK_FORWARD,
    N_RANDOM_SEEDS,
    TOTAL_TIMESTEPS,
)
from experiments._data_cache import get_cached_dataset
from experiments._evaluate import run_single_experiment
from experiments._utils import (
    configure_logging,
    make_timestamp,
    save_results,
    RESULTS_DIR,
    result_path,
)
from experiments._plotting import save_results_table

logger = logging.getLogger("run_campaign")

CAMPAIGN_ID = "campaign_v1"


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run CA-MARL experimental campaign")
    parser.add_argument("--campaign", type=str, default=CAMPAIGN_ID,
                        help="Campaign identifier (results saved with this prefix)")
    parser.add_argument("--seeds", type=int, default=N_RANDOM_SEEDS,
                        help="Number of random seeds")
    parser.add_argument("--timesteps", type=int, default=TOTAL_TIMESTEPS,
                        help="PPO training timesteps per agent")
    parser.add_argument("--folds", type=int, default=4,
                        help="Walk-forward folds")
    parser.add_argument("--start-seed", type=int, default=42)
    parser.add_argument("--skip-ablations", action="store_true",
                        help="Skip ablation studies")
    args = parser.parse_args()

    campaign_id = args.campaign
    ts = make_timestamp()
    logger.info("=" * 60)
    logger.info("CA-MARL EXPERIMENTAL CAMPAIGN")
    logger.info("  Campaign:     %s", campaign_id)
    logger.info("  Seeds:        %d (start=%d)", args.seeds, args.start_seed)
    logger.info("  Folds:        %d", args.folds)
    logger.info("  Timesteps:    %d", args.timesteps)
    logger.info("  Timestamp:    %s", ts)
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Load frozen dataset
    # ------------------------------------------------------------------
    logger.info("Loading frozen dataset...")
    t0 = time.time()
    data = get_cached_dataset()
    features = data["features"]
    forward_returns = data["forward_returns"]
    realized_prices = data["realized_prices"]
    universe = data["universe"]
    logger.info("Data loaded in %.1fs: features=%s, prices=%s, universe=%d",
                time.time() - t0, features.shape, realized_prices.shape, len(universe))

    # ------------------------------------------------------------------
    # Run CA-MARL for each seed
    # ------------------------------------------------------------------
    all_results = {}
    all_results[campaign_id] = []

    for seed in range(args.start_seed, args.start_seed + args.seeds):
        logger.info("--- Seed %d/%d ---", seed - args.start_seed + 1, args.seeds)
        t0 = time.time()
        result = run_single_experiment(
            features=features,
            forward_returns=forward_returns,
            realized_prices=realized_prices,
            universe=universe,
            agent_configs=DEFAULT_AGENT_CONFIGS,
            ppo_config=DEFAULT_PPO,
            confidence_config=DEFAULT_CONFIDENCE,
            risk_config=DEFAULT_RISK,
            experiment_name=campaign_id,
            seed=seed,
            total_timesteps=args.timesteps,
            include_baselines=True,
            n_folds=args.folds,
            walk_config=DEFAULT_WALK_FORWARD,
        )
        elapsed = time.time() - t0
        all_results[campaign_id].append(result)
        logger.info("Seed %d completed in %.1fs", seed, elapsed)

    # ------------------------------------------------------------------
    # Aggregate across seeds
    # ------------------------------------------------------------------
    print()
    print("=" * 70)
    print(f"CAMPAIGN: {campaign_id} | {args.seeds} seeds, {args.folds} folds, {args.timesteps} timesteps")
    print("=" * 70)

    metric_keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                   "volatility", "cumulative_return"]

    print(f"\n{'Metric':25s} {'CA-MARL Mean':>15s} {'Std':>10s}")
    print("-" * 55)

    for metric in metric_keys:
        values = []
        for r in all_results[campaign_id]:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            mean_v = float(np.mean(values))
            std_v = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            print(f"  {metric:25s} {mean_v:>10.4f}   {std_v:>8.4f}")

    # ------------------------------------------------------------------
    # Aggregate baselines (deterministic, take first seed)
    # ------------------------------------------------------------------
    if all_results[campaign_id] and all_results[campaign_id][0].get("baselines"):
        bnames = ["equal_weight", "buy_and_hold", "static_mvo"]
        print(f"\n{'Baseline':25s} {'Sharpe':>10s} {'Return':>10s}")
        print("-" * 50)
        for bname in bnames:
            bm = all_results[campaign_id][0]["baselines"].get(bname, {})
            sr = bm.get("sharpe_ratio", "N/A")
            cr = bm.get("cumulative_return", "N/A")
            if isinstance(sr, float):
                print(f"  {bname:25s} {sr:>8.4f}    {cr:>+7.2%}")
            else:
                print(f"  {bname:25s} {sr!s:>10s}")

    # ------------------------------------------------------------------
    # Save summary table
    # ------------------------------------------------------------------
    summary_rows = {}
    for metric in metric_keys:
        values = []
        for r in all_results[campaign_id]:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if values:
            summary_rows[f"{campaign_id}_{metric}_mean"] = float(np.mean(values))
            summary_rows[f"{campaign_id}_{metric}_std"] = float(
                np.std(values, ddof=1) if len(values) > 1 else 0.0
            )

    # Add baselines to summary
    if all_results[campaign_id] and all_results[campaign_id][0].get("baselines"):
        for bname in bnames:
            bm = all_results[campaign_id][0]["baselines"].get(bname, {})
            for k in metric_keys:
                v = bm.get(k)
                if v is not None:
                    summary_rows[f"{bname}_{k}"] = float(v)

    table_path = save_results_table(
        {campaign_id: summary_rows},
        filename=f"campaign_summary_{campaign_id}_{ts}.csv",
    )
    print(f"\nSummary table: {table_path}")

    # ------------------------------------------------------------------
    # Ablation studies (unless skipped)
    # ------------------------------------------------------------------
    if not args.skip_ablations:
        print("\n" + "=" * 70)
        print("RUNNING ABLATION STUDIES")
        print("=" * 70)
        _run_ablations(campaign_id, args, features, forward_returns, realized_prices, universe)

    print("\nCampaign complete.")
    print(f"Results saved in: {RESULTS_DIR}")
    print(f"Campaign ID: {campaign_id}")


def _run_ablations(campaign_id, args, features, forward_returns, realized_prices, universe):
    """Run ablation studies for the campaign."""
    from experiments._ablations import (
        run_drop_one_agent,
        run_equal_weight_fusion,
        run_no_calibration,
        run_shuffled_confidence,
    )
    from finrl.agents.ca_marl.confidence_engine import OutcomeLabelGenerator
    from finrl.agents.ca_marl.evaluation import EvaluationEngine
    from experiments._pipeline import train_and_infer

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

    ablations = {
        campaign_id: {
            "financial_metrics": {
                "sharpe_ratio": result["evaluation_report"].financial_metrics.sharpe_ratio,
                "sortino_ratio": result["evaluation_report"].financial_metrics.sortino_ratio,
                "max_drawdown": result["evaluation_report"].financial_metrics.max_drawdown,
                "volatility": result["evaluation_report"].financial_metrics.volatility,
                "cumulative_return": result["evaluation_report"].financial_metrics.cumulative_return,
            }
        } if result["evaluation_report"] else {},
    }

    for ab_name, ab_fn in [
        ("equal_weight_fusion", lambda: run_equal_weight_fusion(
            agent_outputs, calibrated, universe,
            DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices)),
        ("no_calibration", lambda: run_no_calibration(
            agent_outputs, calibrated, universe,
            DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices)),
        ("shuffled_confidence", lambda: run_shuffled_confidence(
            agent_outputs, calibrated, universe,
            DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices,
            seed=42 + 999)),
    ]:
        logger.info("Running ablation: %s", ab_name)
        ablations[ab_name] = ab_fn()

    for drop in ["market_agent", "risk_agent", "allocation_agent"]:
        ab_name = f"drop_{drop}"
        logger.info("Running ablation: %s", ab_name)
        ablations[ab_name] = run_drop_one_agent(
            agent_outputs, calibrated, universe,
            DEFAULT_AGENT_CONFIGS, DEFAULT_RISK, eval_engine, test_prices,
            drop_agent=drop,
        )

    # Print ablation results
    print(f"\n{'Ablation':30s} {'Sharpe':>10s} {'Return':>10s}")
    print("-" * 55)
    for name, ab in ablations.items():
        fm = ab.get("financial_metrics", {})
        sr = fm.get("sharpe_ratio", "N/A")
        cr = fm.get("cumulative_return", "N/A")
        if isinstance(sr, float):
            print(f"  {name:30s} {sr:>8.4f}    {cr:>+7.2%}")
        else:
            print(f"  {name:30s} {sr!s:>10s}")

    # Save ablations
    from experiments._utils import result_path
    ab_path = result_path(f"{campaign_id}_ablations", 0)
    save_results(ablations, ab_path)


if __name__ == "__main__":
    main()
