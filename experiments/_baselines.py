"""Baseline portfolio strategies for CA-MARL comparison.

Implements the four committed baselines from EXPERIMENT_PLAN.md:
  1. Equal Weight (1/N) — daily rebalanced
  2. Buy and Hold — equal-weight at start, held throughout
  3. Static Mean-Variance Optimization (MVO) — Markowitz, no rebalancing
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from finrl.agents.ca_marl.contracts import FinancialMetrics
from finrl.agents.ca_marl.evaluation import EvaluationEngine

logger = logging.getLogger(__name__)


def equal_weight(
    prices: pd.DataFrame,
    eval_engine: EvaluationEngine | None = None,
) -> FinancialMetrics:
    """Daily-rebalanced equal-weight (1/N) portfolio.

    Each day, capital is split equally across all assets.
    """
    weights = {ticker: 1.0 / len(prices.columns) for ticker in prices.columns}
    port_rets = _portfolio_returns_from_weights(weights, prices)
    return _safe_metrics(port_rets, eval_engine)


def buy_and_hold(
    prices: pd.DataFrame,
    eval_engine: EvaluationEngine | None = None,
) -> FinancialMetrics:
    """Buy-and-hold: buy equal-dollar at start, hold to end, no rebalancing."""
    n = len(prices.columns)
    initial_weights = np.array([1.0 / n] * n)
    norm = prices / prices.iloc[0]
    port_value = norm @ initial_weights
    port_rets = port_value.pct_change().dropna().values
    return _safe_metrics(port_rets, eval_engine)


def static_mvo(
    prices: pd.DataFrame,
    eval_engine: EvaluationEngine | None = None,
    risk_aversion: float = 1.0,
    fit_prices: pd.DataFrame | None = None,
) -> FinancialMetrics:
    """Static mean-variance optimisation (Markowitz, no rebalancing).

    Estimates the optimal weights from a pre-test estimation period
    using sample mean and covariance, then holds that portfolio
    throughout the test period.

    Args:
        prices: DataFrame with DatetimeIndex and ticker columns for
            the evaluation period.
        eval_engine: optional EvaluationEngine (used for label_gen consistency).
        risk_aversion: risk aversion parameter (higher → more conservative).
        fit_prices: DataFrame with DatetimeIndex and ticker columns for
            the estimation period. If ``None``, uses ``prices`` for both
            estimation and evaluation (WARNING: this introduces look-ahead
            bias and must NOT be used for comparative experiments).

    Raises:
        ValueError: if ``fit_prices`` has fewer than 2 rows.
    """
    fit = fit_prices if fit_prices is not None else prices
    if len(fit) < 2:
        raise ValueError(
            f"Need at least 2 rows for MVO estimation; got {len(fit)}."
        )
    returns = fit.pct_change().dropna()
    mu = returns.mean().values * 252
    sigma = returns.cov().values * 252

    n = len(prices.columns)

    def neg_utility(w: np.ndarray) -> float:
        ret = w @ mu
        risk = w @ sigma @ w
        return -(ret - 0.5 * risk_aversion * risk)

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bounds = [(0.0, 1.0)] * n
    w0 = np.ones(n) / n

    result = minimize(neg_utility, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        logger.warning("MVO optimisation did not converge; falling back to equal-weight.")
        w_opt = w0
    else:
        w_opt = result.x

    weights = {ticker: float(w_opt[i]) for i, ticker in enumerate(prices.columns)}
    port_rets = _portfolio_returns_from_weights(weights, prices)
    return _safe_metrics(port_rets, eval_engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _portfolio_returns_from_weights(
    weights: dict[str, float],
    prices: pd.DataFrame,
) -> np.ndarray:
    """Compute daily portfolio return series from fixed weights and prices."""
    tickers = [t for t in weights if t in prices.columns]
    w = np.array([weights[t] for t in tickers])
    p = prices[tickers].values.astype(np.float64)
    rets = np.diff(p, axis=0) / (p[:-1] + 1e-12)
    return rets @ w


def _safe_metrics(
    returns: np.ndarray,
    eval_engine: EvaluationEngine | None,
) -> FinancialMetrics:
    """Compute FinancialMetrics from a return array, using EvaluationEngine if available."""
    if eval_engine is not None:
        result = eval_engine._compute_metrics(returns)
        if result is not None:
            return result
    return _compute_metrics_direct(returns)


def _compute_metrics_direct(returns: np.ndarray) -> FinancialMetrics:
    """Direct metric computation (fallback when no EvaluationEngine available)."""
    if len(returns) < 2:
        return FinancialMetrics(
            sharpe_ratio=float("nan"),
            sortino_ratio=float("nan"),
            max_drawdown=float("nan"),
            volatility=float("nan"),
            cumulative_return=float("nan"),
        )
    vol = float(np.std(returns, ddof=1) * np.sqrt(252))
    mean_ret = float(np.mean(returns))
    sharpe = mean_ret / (np.std(returns, ddof=1) + 1e-12) * np.sqrt(252)
    downside = returns[returns < 0]
    downside_std = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
    sortino = mean_ret / (downside_std + 1e-12) * np.sqrt(252)
    cum = np.cumprod(1.0 + returns)
    running_max = np.maximum.accumulate(cum)
    drawdowns = (cum - running_max) / running_max
    max_dd = float(np.min(drawdowns))
    cum_ret = float(cum[-1] - 1.0)
    return FinancialMetrics(
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=max_dd,
        volatility=vol,
        cumulative_return=cum_ret,
    )


# ---------------------------------------------------------------------------
# Baseline runner
# ---------------------------------------------------------------------------


def run_all_baselines(
    prices: pd.DataFrame,
    eval_engine: EvaluationEngine | None = None,
    fit_prices: pd.DataFrame | None = None,
) -> dict[str, FinancialMetrics]:
    """Run all baseline strategies and return their metrics.

    Args:
        prices: DataFrame with DatetimeIndex and ticker columns for
            the evaluation period.
        eval_engine: optional EvaluationEngine for consistent metric computation.
        fit_prices: optional DataFrame with DatetimeIndex and ticker
            columns for MVO estimation. If ``None``, MVO uses ``prices``
            (introduces look-ahead bias — see ``static_mvo``).

    Returns:
        dict[str, FinancialMetrics] keyed by baseline name.
    """
    logger.info("Running baselines on %d assets, %d timesteps",
                len(prices.columns), len(prices))
    return {
        "equal_weight": equal_weight(prices, eval_engine),
        "buy_and_hold": buy_and_hold(prices, eval_engine),
        "static_mvo": static_mvo(prices, eval_engine, fit_prices=fit_prices),
    }
