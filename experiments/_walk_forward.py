"""Walk-forward validation framework for CA-MARL.

Generates chronological fold splits, manages per-fold label eligibility
for leakage-free calibration, and orchestrates the train/infer/evaluate
cycle.
"""

import logging
from datetime import timedelta
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
from finrl.agents.ca_marl.confidence_engine import (
    ConfidenceEngine,
    OutcomeLabelGenerator,
)
from finrl.agents.ca_marl.evaluation import EvaluationEngine

from experiments._baselines import run_all_baselines
from experiments._config import FoldSchedule, build_fold_schedules
from experiments._pipeline import train_and_infer

logger = logging.getLogger(__name__)


class WalkForwardRunner:
    """Orchestrates walk-forward validation across chronological folds.

    For each fold:
      1. Split data into train / validation / test windows by row index.
      2. Train all three agents on the training window.
      3. Collect eligible calibration pairs from the validation window.
      4. Run inference + evaluation on the test window (with timestamp patching).
      5. Accumulate per-fold reports.
    """

    def __init__(
        self,
        features: pd.DataFrame,
        forward_returns: pd.DataFrame,
        realized_prices: pd.DataFrame,
        universe: list[str],
        agent_configs: dict[str, AgentHyperparameters],
        ppo_config: PPOConfig,
        confidence_config: ConfidenceConfig,
        risk_config: RiskManagementConfig,
        walk_config: WalkForwardConfig,
        total_timesteps: int = 5000,
        prediction_consistency_k: int = 5,
        seed: int = 42,
    ):
        self._features = features
        self._forward_returns = forward_returns
        self._realized_prices = realized_prices
        self._universe = universe
        self._agent_configs = agent_configs
        self._ppo_config = ppo_config
        self._confidence_config = confidence_config
        self._risk_config = risk_config
        self._walk_config = walk_config
        self._total_timesteps = total_timesteps
        self._prediction_consistency_k = prediction_consistency_k
        self._seed = seed

    def run(self) -> list[dict[str, Any]]:
        """Run walk-forward validation.

        Returns:
            A list of per-fold result dicts.
        """
        n = len(self._features)
        schedules = build_fold_schedules(n, self._walk_config)

        if not schedules:
            logger.error(
                "Cannot create any fold: n_timesteps=%d, config=%s",
                n, self._walk_config,
            )
            return []

        logger.info(
            "Walk-forward: %d folds over %d timesteps", len(schedules), n,
        )

        outcome_label_gen = OutcomeLabelGenerator(self._agent_configs)

        # Accumulated calibration data from earlier folds (label-leakage-safe).
        accumulated_calib_data: list[tuple[str, float, float]] = []

        fold_results: list[dict[str, Any]] = []

        for fold_idx, schedule in enumerate(schedules):
            fold_id = f"{fold_idx + 1:02d}"
            logger.info("=== Fold %s ===", fold_id)
            logger.info(
                "  Train: [%d:%d]  Val: [%d:%d]  Test: [%d:%d]",
                schedule.train_start, schedule.train_end,
                schedule.val_start, schedule.val_end,
                schedule.test_start, schedule.test_end,
            )

            # --- Split data ---
            train_feat = self._features.iloc[schedule.train_start:schedule.train_end]
            train_ret = self._forward_returns.iloc[schedule.train_start:schedule.train_end]
            val_feat = self._features.iloc[schedule.val_start:schedule.val_end]
            val_prices = self._realized_prices.iloc[schedule.val_start:schedule.val_end]
            test_feat = self._features.iloc[schedule.test_start:schedule.test_end]
            test_prices = self._realized_prices.iloc[schedule.test_start:schedule.test_end]

            # Extend eval prices to cover label horizon.
            label_horizon = max(
                cfg.label_horizon_days for cfg in self._agent_configs.values()
            )
            eval_end = min(
                schedule.test_end + label_horizon + 5,
                len(self._realized_prices),
            )
            eval_prices = self._realized_prices.iloc[schedule.test_start:eval_end]

            if len(train_feat) < 20 or len(test_feat) < 2:
                logger.warning("Fold %s: too few timesteps; skipping.", fold_id)
                continue

            # --- Train + infer + evaluate (with timestamp patching) ---
            np.random.seed(self._seed + fold_idx)
            result = train_and_infer(
                train_features=train_feat,
                train_forward_returns=train_ret,
                test_features=test_feat,
                test_realized_prices=test_prices,
                eval_realized_prices=eval_prices,
                universe=self._universe,
                agent_configs=self._agent_configs,
                ppo_config=self._ppo_config,
                confidence_config=self._confidence_config,
                risk_config=self._risk_config,
                total_timesteps=self._total_timesteps,
                prediction_consistency_k=self._prediction_consistency_k,
                calib_pairs=list(accumulated_calib_data),
                outcome_label_gen=outcome_label_gen,
            )

            rec = result["final_recommendation"]
            report = result["evaluation_report"]
            fused = result["fused_decision"]

            fold_entry: dict[str, Any] = {
                "fold_id": fold_id,
                "schedule": {
                    "train": [schedule.train_start, schedule.train_end],
                    "val": [schedule.val_start, schedule.val_end],
                    "test": [schedule.test_start, schedule.test_end],
                },
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
                    name: {
                        "ece": cm.ece,
                        "brier_score": cm.brier_score,
                    }
                    for name, cm in report.calibration_metrics.items()
                }
                fold_entry["fold_summary"] = (
                    f"Fold {fold_id}: Sharpe={fm.sharpe_ratio:.3f}, "
                    f"Sortino={fm.sortino_ratio:.3f}, "
                    f"Return={fm.cumulative_return:+.2%}"
                )
                logger.info(fold_entry["fold_summary"])
            else:
                fold_entry["fold_summary"] = f"Fold {fold_id}: No evaluation report."
                logger.warning(fold_entry["fold_summary"])

            # --- Baseline comparison on same test window ---
            try:
                train_prices = self._realized_prices.iloc[schedule.train_start:schedule.train_end]
                test_prices = self._realized_prices.iloc[schedule.test_start:schedule.test_end]
                bm = run_all_baselines(
                    test_prices,
                    fit_prices=train_prices,
                )
                fold_entry["baselines"] = {
                    name: {
                        "sharpe_ratio": m.sharpe_ratio,
                        "sortino_ratio": m.sortino_ratio,
                        "max_drawdown": m.max_drawdown,
                        "volatility": m.volatility,
                        "cumulative_return": m.cumulative_return,
                    }
                    for name, m in bm.items()
                }
            except Exception as exc:
                logger.warning("Baseline computation failed for fold %s: %s", fold_id, exc)

            # --- Collect calibration pairs from this test window for future folds ---
            # ADR-024: only accumulate pairs whose label resolves within the
            # next fold's training window to prevent future information leakage.
            next_schedule = (
                schedules[fold_idx + 1] if fold_idx + 1 < len(schedules) else None
            )
            next_train_end = (
                pd.Timestamp(self._realized_prices.index[next_schedule.train_end])
                if next_schedule is not None else None
            )
            conf_map = result["calibrated_confidences"]
            for ao in result["agent_outputs"]:
                try:
                    label = outcome_label_gen.generate_label(
                        ao.agent_name, ao, eval_prices,
                    )
                    if next_train_end is not None:
                        cfg = self._agent_configs.get(
                            ao.agent_name,
                            self._agent_configs.get("market_agent",
                                                     self._agent_configs.get("risk_agent")),
                        )
                        horizon = timedelta(days=cfg.label_horizon_days)
                        if not outcome_label_gen.is_eligible_for_fold(
                            ao, horizon, next_train_end.to_pydatetime(),
                        ):
                            continue
                    accumulated_calib_data.append(
                        (ao.agent_name, ao.raw_confidence, label)
                    )
                except Exception:
                    pass  # normal for last few rows where horizon exceeds data
            logger.info(
                "Calibration pool now has %d pairs across all agents",
                len(accumulated_calib_data),
            )

            fold_results.append(fold_entry)

        return fold_results

    def _collect_calibration_pairs(
        self,
        train_features: pd.DataFrame,
        train_forward_returns: pd.DataFrame,
        val_features: pd.DataFrame,
        val_prices: pd.DataFrame,
        schedule: FoldSchedule,
        label_gen: OutcomeLabelGenerator,
    ) -> list[tuple[str, float, float]]:
        """Generate calibration (confidence, label) pairs from the validation window.

        Uses only fold-eligible recommendations per ADR-024 leakage rule.
        Agents are trained on the training window, then predict on the validation
        window.  Only pairs whose label horizon lands within the training window
        end-date are eligible (no leakage).
        """
        from finrl.agents.ca_marl.pipeline import build_agents

        # Train agents on the training window for calibration data generation.
        trained = build_agents(
            train_features, train_forward_returns, self._universe,
            self._agent_configs, self._ppo_config,
            total_timesteps=self._total_timesteps,
        )

        train_end_date = pd.Timestamp(
            self._realized_prices.index[schedule.train_end]
        )
        pairs: list[tuple[str, float, float]] = []

        for agent_name, agent_obj in trained.items():
            ao = agent_obj.predict(val_features)
            cfg = self._agent_configs.get(agent_name,
                                          self._agent_configs["market_agent"])
            horizon = pd.Timedelta(days=cfg.label_horizon_days)

            # Patch the timestamp to align with the validation window.
            val_ts = val_prices.index[-1]
            object.__setattr__(ao, "timestamp", val_ts)

            if not label_gen.is_eligible_for_fold(ao, horizon,
                                                   train_end_date.to_pydatetime()):
                continue

            try:
                label = label_gen.generate_label(agent_name, ao, val_prices)
                pairs.append((agent_name, ao.raw_confidence, label))
            except Exception as exc:
                logger.debug("Skipping label for %s: %s", agent_name, exc)

        logger.info(
            "Collected %d calibration pairs from validation fold", len(pairs),
        )
        return pairs
