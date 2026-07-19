"""Evaluation runner — orchestrates pipeline execution, metric collection,
baseline comparison, and results serialisation for a single experiment."""

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from finrl.agents.ca_marl.config_schema import (
    AgentHyperparameters,
    ConfidenceConfig,
    PPOConfig,
    RiskManagementConfig,
    WalkForwardConfig,
)
from finrl.agents.ca_marl.confidence_engine import OutcomeLabelGenerator
from finrl.agents.ca_marl.evaluation import EvaluationEngine

from experiments._baselines import run_all_baselines
from experiments._pipeline import train_and_infer
from experiments._utils import (
    result_path,
    save_results,
    set_all_seeds,
    seed_str,
)
from experiments._walk_forward import WalkForwardRunner

logger = logging.getLogger(__name__)


def run_single_experiment(
    features: pd.DataFrame,
    forward_returns: pd.DataFrame,
    realized_prices: pd.DataFrame,
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    ppo_config: PPOConfig,
    confidence_config: ConfidenceConfig,
    risk_config: RiskManagementConfig,
    experiment_name: str = "ca_marl",
    seed: int = 42,
    total_timesteps: int = 5000,
    include_baselines: bool = True,
    n_folds: int = 1,
    walk_config: WalkForwardConfig | None = None,
) -> dict[str, Any]:
    """Run a single CA-MARL experiment with a given seed.

    If n_folds == 1: simple train/test split (train on first 80%, test on last 20%).
    If n_folds > 1: walk-forward validation.

    Returns:
        A dict with all results, ready for serialisation.
    """
    set_all_seeds(seed)
    logger.info("=== Experiment: %s | seed=%d ===", experiment_name, seed)

    result: dict[str, Any] = {
        "experiment": experiment_name,
        "seed": seed,
        "seed_label": seed_str(seed),
        "universe": list(universe),
        "n_timesteps": len(features),
        "n_assets": len(universe),
        "config": {
            "ppo": {
                "learning_rate": ppo_config.learning_rate,
                "n_steps": ppo_config.n_steps,
                "batch_size": ppo_config.batch_size,
                "gamma": ppo_config.gamma,
                "total_timesteps": total_timesteps,
            },
            "confidence": {
                "calibration_method": confidence_config.calibration_method,
                "historical_accuracy_weight": confidence_config.historical_accuracy_weight,
                "reward_stability_weight": confidence_config.reward_stability_weight,
                "prediction_consistency_weight": confidence_config.prediction_consistency_weight,
            },
        },
        "folds": [],
        "baselines": {},
        "aggregated": {},
    }

    if n_folds > 1:
        wf_config = walk_config or WalkForwardConfig(
            n_folds=n_folds,
            training_window_days=int(len(features) * 0.5),
            validation_window_days=int(len(features) * 0.125),
            test_window_days=int(len(features) * 0.125),
            retrain_on="every_fold",
        )
        runner = WalkForwardRunner(
            features, forward_returns, realized_prices, universe,
            agent_configs, ppo_config, confidence_config, risk_config,
            wf_config,
            total_timesteps=total_timesteps,
            seed=seed,
        )
        fold_results = runner.run()
        result["folds"] = fold_results
        result["aggregated"] = _aggregate_folds(fold_results)
    else:
        split = int(len(features) * 0.8)
        train_feat = features.iloc[:split]
        train_ret = forward_returns.iloc[:split]
        test_feat = features.iloc[split:]
        test_prices = realized_prices.iloc[split:]

        # Extend realized prices for label horizon coverage.
        label_horizon = max(
            cfg.label_horizon_days for cfg in agent_configs.values()
        )
        eval_extra = min(label_horizon + 5, len(realized_prices) - split)
        eval_prices = realized_prices.iloc[split:split + eval_extra]

        outcome_label_gen = OutcomeLabelGenerator(agent_configs)
        inference_result = train_and_infer(
            train_features=train_feat,
            train_forward_returns=train_ret,
            test_features=test_feat,
            test_realized_prices=test_prices,
            eval_realized_prices=eval_prices,
            universe=universe,
            agent_configs=agent_configs,
            ppo_config=ppo_config,
            confidence_config=confidence_config,
            risk_config=risk_config,
            total_timesteps=total_timesteps,
            outcome_label_gen=outcome_label_gen,
        )

        rec = inference_result["final_recommendation"]
        report = inference_result["evaluation_report"]
        fused = inference_result["fused_decision"]

        fold_entry: dict[str, Any] = {
            "fold_id": "single",
            "allocation": dict(rec.allocation),
            "fused_decision": {
                "final_allocation": dict(fused.final_allocation),
                "fallback_used": fused.fusion_metadata.get("fallback_used", False),
            },
        }
        if report is not None:
            fm = report.financial_metrics
            fold_entry["financial_metrics"] = {
                "sharpe_ratio": fm.sharpe_ratio,
                "sortino_ratio": fm.sortino_ratio,
                "max_drawdown": fm.max_drawdown,
                "volatility": fm.volatility,
                "cumulative_return": fm.cumulative_return,
            }
            fold_entry["calibration_metrics"] = {
                name: {"ece": cm.ece, "brier_score": cm.brier_score}
                for name, cm in report.calibration_metrics.items()
            }
        result["folds"] = [fold_entry]
        result["aggregated"] = _aggregate_folds([fold_entry])

    # --- Baselines ---
    if n_folds > 1 and fold_results:
        # Aggregate per-fold baselines from walk-forward runner.
        bnames = ["equal_weight", "buy_and_hold", "static_mvo"]
        for bname in bnames:
            vals: dict[str, list[float]] = {
                k: [] for k in
                ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                 "volatility", "cumulative_return"]
            }
            for f in fold_results:
                fb = f.get("baselines", {}).get(bname, {})
                for k in vals:
                    v = fb.get(k)
                    if v is not None and not (isinstance(v, float) and np.isnan(v)):
                        vals[k].append(v)
            if vals["sharpe_ratio"]:
                result["baselines"][bname] = {
                    k: float(np.mean(v)) for k, v in vals.items()
                }
    elif include_baselines and n_folds <= 1:
        try:
            split_idx = int(len(features) * 0.8)
            train_prices = realized_prices.iloc[:split_idx]
            test_prices = realized_prices.iloc[split_idx:]
            eval_engine = EvaluationEngine(OutcomeLabelGenerator(agent_configs))
            baseline_metrics = run_all_baselines(test_prices, eval_engine, fit_prices=train_prices)
            result["baselines"] = {
                name: {
                    "sharpe_ratio": m.sharpe_ratio,
                    "sortino_ratio": m.sortino_ratio,
                    "max_drawdown": m.max_drawdown,
                    "volatility": m.volatility,
                    "cumulative_return": m.cumulative_return,
                }
                for name, m in baseline_metrics.items()
            }
        except Exception as exc:
            logger.warning("Baseline computation failed: %s", exc)

    # --- Save ---
    rpath = result_path(experiment_name, seed)
    save_results(result, rpath)

    return result


def _aggregate_folds(folds: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate metrics across folds with mean ± std."""
    keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown", "volatility", "cumulative_return"]
    values: dict[str, list[float]] = {k: [] for k in keys}
    for f in folds:
        fm = f.get("financial_metrics", {})
        for k in keys:
            v = fm.get(k)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                values[k].append(v)

    agg: dict[str, Any] = {}
    for k in keys:
        if values[k]:
            agg[k] = {
                "mean": float(np.mean(values[k])),
                "std": float(np.std(values[k], ddof=1)) if len(values[k]) > 1 else 0.0,
                "min": float(np.min(values[k])),
                "max": float(np.max(values[k])),
            }
        else:
            agg[k] = {"mean": None, "std": None, "min": None, "max": None}
    return agg
