"""Evaluation Engine — financial metrics, calibration metrics, ablation, baselines.

Evaluates both financial performance and calibration quality of the full
CA-MARL pipeline, and supports the mandatory ablations and baseline
comparisons that this project's research claims depend on (ADR-021).

Reuses the same ``OutcomeLabelGenerator`` instance that was used during
training/calibration (ADR-024) — never a separate implementation, to
guarantee training-time and evaluation-time "correctness" are defined
identically.

Reference: docs/architecture/AGENTS.md §7,
docs/architecture/INTERFACE_CONTRACTS.md §7,
docs/architecture/MODULE_SPECIFICATIONS.md §7.
"""

import logging
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from finrl.agents.ca_marl.confidence_engine import OutcomeLabelGenerator
from finrl.agents.ca_marl.contracts import (
    AgentOutput,
    CalibratedConfidence,
    CalibrationMetrics,
    EvaluationDataMismatchError,
    EvaluationReport,
    FinalRecommendation,
    FinancialMetrics,
)

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """CA-MARL Evaluation Engine (ADR-021).

    Measures both financial performance and calibration quality of the
    pipeline, and supports the ablations and baseline comparisons defined
    in the research plan.
    """

    def __init__(
        self, outcome_label_generator: OutcomeLabelGenerator
    ) -> None:
        """Initialise the Evaluation Engine.

        Args:
            outcome_label_generator: the **same** ``OutcomeLabelGenerator``
                instance used during training/calibration — never a separate
                implementation (ADR-024).
        """
        self._label_gen = outcome_label_generator

    # ------------------------------------------------------------------
    # Financial evaluation
    # ------------------------------------------------------------------

    def evaluate_financial(
        self,
        recommendations: list[FinalRecommendation],
        realized_returns: pd.Series,
    ) -> FinancialMetrics:
        """Compute standard portfolio performance metrics.

        ``realized_returns`` is a ``pd.Series`` with a ``DatetimeIndex``
        whose entries correspond (by timestamp) to the ``recommendations``
        list.  Each value is the portfolio return for the period following
        that recommendation.

        Args:
            recommendations: sequence of ``FinalRecommendation`` objects
                from a test window.
            realized_returns: portfolio return series, indexed by timestamp.

        Returns:
            ``FinancialMetrics`` with Sharpe Ratio, Sortino Ratio, Maximum
            Drawdown, Volatility, and Cumulative Return.

        Raises:
            EvaluationDataMismatchError: if recommendation timestamps and
                ``realized_returns`` index do not align.
        """
        timestamps = [r.timestamp.replace(second=0, microsecond=0) for r in recommendations]
        ret_index = realized_returns.index.to_list()
        if len(timestamps) != len(ret_index):
            raise EvaluationDataMismatchError(
                f"Got {len(timestamps)} recommendations but "
                f"{len(ret_index)} return entries."
            )

        returns = realized_returns.values.astype(np.float64)
        fm = self._compute_metrics(returns)
        if fm is None:
            logger.warning(
                "Fewer than 2 data points for financial metrics; returning NaNs."
            )
            return FinancialMetrics(
                sharpe_ratio=float("nan"),
                sortino_ratio=float("nan"),
                max_drawdown=float("nan"),
                volatility=float("nan"),
                cumulative_return=float("nan"),
            )
        return fm

    def evaluate_with_assets(
        self,
        recommendations: list[FinalRecommendation],
        asset_prices: pd.DataFrame,
    ) -> FinancialMetrics:
        """Compute portfolio metrics from asset-level prices.

        Converts allocation weights + per-asset price data into portfolio
        return series, then computes metrics using the same logic as
        ``evaluate_financial`` (without the alignment check, since this
        method is designed for single-recommendation or unequal-length
        scenarios).

        Args:
            recommendations: sequence of ``FinalRecommendation`` objects
                from a test window. Only the last recommendation's weights
                are used.
            asset_prices: DataFrame with ``DatetimeIndex`` and ticker columns
                containing close prices.

        Returns:
            ``FinancialMetrics`` with Sharpe Ratio, Sortino Ratio, Maximum
            Drawdown, Volatility, and Cumulative Return.
        """
        if not recommendations or len(asset_prices) < 2:
            logger.warning(
                "Insufficient data for portfolio return computation; returning NaNs."
            )
            return FinancialMetrics(
                sharpe_ratio=float("nan"),
                sortino_ratio=float("nan"),
                max_drawdown=float("nan"),
                volatility=float("nan"),
                cumulative_return=float("nan"),
            )

        rec = recommendations[-1]
        weights = rec.allocation
        prices = asset_prices.copy()
        tickers = [t for t in weights if t in prices.columns]
        if len(tickers) < 1:
            logger.warning("No overlapping tickers in weights and prices; returning NaNs.")
            return FinancialMetrics(
                sharpe_ratio=float("nan"),
                sortino_ratio=float("nan"),
                max_drawdown=float("nan"),
                volatility=float("nan"),
                cumulative_return=float("nan"),
            )

        p = prices[tickers].values.astype(np.float64)
        rets = np.diff(p, axis=0) / (p[:-1] + 1e-12)
        w = np.array([weights[t] for t in tickers], dtype=np.float64)
        port_rets = rets @ w

        fm = self._compute_metrics(port_rets)
        if fm is None:
            logger.warning("Fewer than 2 return points; returning NaNs.")
            return FinancialMetrics(
                sharpe_ratio=float("nan"),
                sortino_ratio=float("nan"),
                max_drawdown=float("nan"),
                volatility=float("nan"),
                cumulative_return=float("nan"),
            )
        return fm

    # ------------------------------------------------------------------
    # Calibration evaluation
    # ------------------------------------------------------------------

    def evaluate_calibration(
        self,
        confidence_history: list[CalibratedConfidence],
        recommendation_history: list[AgentOutput],
        realized_data: pd.DataFrame,
    ) -> dict[str, CalibrationMetrics]:
        """Compute per-agent calibration metrics.

        For each agent, generates outcome labels via the shared
        ``OutcomeLabelGenerator`` (ADR-024) and computes ECE and Brier
        score against the corresponding calibrated confidence values.

        Args:
            confidence_history: sequence of ``CalibratedConfidence``
                objects, one per recommendation per agent.
            recommendation_history: sequence of ``AgentOutput`` objects,
                one per recommendation per agent.
            realized_data: DataFrame with ``DatetimeIndex`` and ticker
                columns, containing close prices covering the full label
                horizon for every recommendation.

        Returns:
            ``dict[str, CalibrationMetrics]`` keyed by ``agent_name``.
        """
        by_agent: dict[str, list[tuple[float, float]]] = {}

        for conf_obj, out_obj in zip(confidence_history, recommendation_history):
            agent_name = conf_obj.agent_name
            try:
                label = self._label_gen.generate_label(
                    agent_name, out_obj, realized_data,
                )
            except Exception:
                logger.warning(
                    "Could not generate label for agent '%s' at %s; skipping.",
                    agent_name, out_obj.timestamp,
                )
                continue

            if agent_name not in by_agent:
                by_agent[agent_name] = []
            by_agent[agent_name].append(
                (conf_obj.calibrated_confidence, label)
            )

        results: dict[str, CalibrationMetrics] = {}
        for agent_name, pairs in by_agent.items():
            confs = np.array([p[0] for p in pairs], dtype=np.float64)
            labels = np.array([p[1] for p in pairs], dtype=np.float64)

            ece = self._compute_ece(confs, labels, n_bins=10)
            brier = float(np.mean((confs - labels) ** 2))

            results[agent_name] = CalibrationMetrics(
                ece=ece,
                brier_score=brier,
                reliability_curve_ref="",
            )

        return results

    # ------------------------------------------------------------------
    # Shared metric computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_metrics(returns: np.ndarray) -> FinancialMetrics | None:
        """Compute standard portfolio metrics from a return array.

        Args:
            returns: 1-D array of portfolio returns.

        Returns:
            ``FinancialMetrics`` if ``len(returns) >= 2``, else ``None``.
        """
        n = len(returns)
        if n < 2:
            return None

        volatility = float(np.std(returns, ddof=1) * np.sqrt(252))
        mean_ret = float(np.mean(returns))
        sharpe_ratio = (
            mean_ret / (np.std(returns, ddof=1) + 1e-12) * np.sqrt(252)
        )

        downside = returns[returns < 0]
        downside_std = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
        sortino_ratio = (
            mean_ret / (downside_std + 1e-12) * np.sqrt(252)
        )

        cum = np.cumprod(1.0 + returns)
        running_max = np.maximum.accumulate(cum)
        drawdowns = (cum - running_max) / running_max
        max_drawdown = float(np.min(drawdowns))
        cumulative_return = float(cum[-1] - 1.0)

        return FinancialMetrics(
            sharpe_ratio=float(sharpe_ratio),
            sortino_ratio=float(sortino_ratio),
            max_drawdown=float(max_drawdown),
            volatility=float(volatility),
            cumulative_return=float(cumulative_return),
        )

    # ------------------------------------------------------------------
    # Ablation support (stub — full implementation in later stage)
    # ------------------------------------------------------------------

    def run_ablation(
        self, ablation_name: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Run one of the ablations defined in ``EXPERIMENT_PLAN.md``.

        Currently a placeholder — raises ``NotImplementedError`` for any
        ablation name other than ``"none"``.

        Args:
            ablation_name: e.g. ``"shuffled_confidence"``, ``"drop_one_agent"``.
            **kwargs: ablation-specific parameters.

        Returns:
            Ablation results dict.

        Raises:
            NotImplementedError: for unimplemented ablations.
        """
        if ablation_name == "none":
            return {"ablation": "none"}
        raise NotImplementedError(
            f"Ablation '{ablation_name}' is not yet implemented. "
            "See EXPERIMENT_PLAN.md and TASKS.md (T-023, T-024)."
        )

    # ------------------------------------------------------------------
    # Baseline comparison
    # ------------------------------------------------------------------

    def compare_baselines(
        self,
        baseline_results: dict[str, FinancialMetrics],
    ) -> dict[str, Any]:
        """Compare this run's financial metrics against baselines.

        Args:
            baseline_results: mapping from baseline name (e.g. ``"1/N"``,
                ``"buy_and_hold"``) to its ``FinancialMetrics``.

        Returns:
            A dict with comparison data (currently a pass-through container).
        """
        return {
            "baselines": {
                name: {
                    "sharpe_ratio": m.sharpe_ratio,
                    "sortino_ratio": m.sortino_ratio,
                    "max_drawdown": m.max_drawdown,
                    "volatility": m.volatility,
                    "cumulative_return": m.cumulative_return,
                }
                for name, m in baseline_results.items()
            }
        }

    # ------------------------------------------------------------------
    # Report assembly
    # ------------------------------------------------------------------

    def generate_report(
        self,
        financial: FinancialMetrics,
        calibration: dict[str, CalibrationMetrics],
        ablations: dict[str, Any] | None = None,
        baselines: dict[str, FinancialMetrics] | None = None,
        fold_id: str = "",
    ) -> EvaluationReport:
        """Assemble the evaluation results into one ``EvaluationReport``.

        Args:
            financial: financial metrics from ``evaluate_financial``.
            calibration: per-agent calibration metrics from
                ``evaluate_calibration``.
            ablations: optional ablation results.
            baselines: optional baseline comparison results.
            fold_id: identifier for the walk-forward fold (empty string
                for single-run mode).

        Returns:
            A complete ``EvaluationReport``.
        """
        baseline_comparison: dict[str, FinancialMetrics] | None = None
        if baselines is not None:
            baseline_comparison = dict(baselines)

        return EvaluationReport(
            financial_metrics=financial,
            calibration_metrics=dict(calibration),
            ablation_results=dict(ablations) if ablations else None,
            baseline_comparison=baseline_comparison,
            fold_id=fold_id,
            timestamp=datetime.now(),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_ece(
        confs: np.ndarray,
        labels: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """Compute Expected Calibration Error over equal-width bins.

        Args:
            confs: calibrated confidence values.
            labels: binary outcome labels.
            n_bins: number of equal-width bins.

        Returns:
            ECE scalar.
        """
        if len(confs) == 0:
            return 0.0

        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (confs >= bin_edges[i]) & (confs < bin_edges[i + 1])
            n_in_bin = int(np.sum(mask))
            if n_in_bin == 0:
                continue
            bin_acc = float(np.mean(labels[mask]))
            bin_conf = float(np.mean(confs[mask]))
            ece += n_in_bin * abs(bin_acc - bin_conf)

        return ece / len(confs)
