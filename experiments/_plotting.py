"""Experiment plotting suite.

Generates the four plot types required by EXPERIMENT_PLAN.md:
  1. Reliability diagrams (calibration curves) per agent, per regime
  2. Cumulative return curves (CA-MARL vs baselines)
  3. Regime timeline overlay
  4. Ablation bar charts
"""

import logging
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from experiments._utils import PLOTS_DIR, load_results

logger = logging.getLogger(__name__)

_STYLE = {
    "ca_marl": {"color": "#1f77b4", "marker": "o", "label": "CA-MARL"},
    "equal_weight": {"color": "#ff7f0e", "marker": "s", "label": "Equal Weight (1/N)"},
    "buy_and_hold": {"color": "#2ca02c", "marker": "^", "label": "Buy & Hold"},
    "static_mvo": {"color": "#d62728", "marker": "D", "label": "Static MVO"},
}

_AGENT_PALETTE = {
    "market_agent": "#9467bd",
    "risk_agent": "#8c564b",
    "allocation_agent": "#e377c2",
}


def _ensure_plots_dir() -> Path:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    return PLOTS_DIR


# ---------------------------------------------------------------------------
# 1. Reliability diagrams
# ---------------------------------------------------------------------------

def plot_reliability_diagrams(
    confidence_series: dict[str, tuple[np.ndarray, np.ndarray]],
    n_bins: int = 10,
    filename: str = "reliability_diagrams.png",
) -> Path:
    """Plot calibration curves (reliability diagrams) for each agent.

    Args:
        confidence_series: ``{agent_name: (calibrated_confs, outcome_labels)}``.
        n_bins: number of equal-width bins.
        filename: output filename (saved to PLOTS_DIR).

    Returns:
        Path to the saved figure.
    """
    n_agents = len(confidence_series)
    fig, axes = plt.subplots(1, n_agents, figsize=(5 * n_agents, 4))
    if n_agents == 1:
        axes = [axes]

    for ax, (agent_name, (confs, labels)) in zip(axes, confidence_series.items()):
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        accuracies = []
        confidences = []
        counts = []

        for i in range(n_bins):
            mask = (confs >= bin_edges[i]) & (confs < bin_edges[i + 1])
            n_in = int(np.sum(mask))
            counts.append(n_in)
            if n_in > 0:
                accuracies.append(float(np.mean(labels[mask])))
                confidences.append(float(np.mean(confs[mask])))
            else:
                accuracies.append(0.0)
                confidences.append(0.0)

        color = _AGENT_PALETTE.get(agent_name, "#333333")
        ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5, label="Perfect")
        ax.plot(bin_centers, accuracies, "o-", color=color, lw=2, label=agent_name)
        ax.fill_between(bin_centers, accuracies, bin_centers,
                        alpha=0.15, color=color, label="Gap")

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Accuracy")
        ax.set_title(agent_name)
        ax.legend(fontsize=8)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)

        # ECE annotation
        ece_val = _compute_ece_from_bins(
            np.array(accuracies), np.array(bin_centers), np.array(counts),
        )
        ax.text(0.05, 0.9, f"ECE = {ece_val:.4f}",
                transform=ax.transAxes, fontsize=10,
                bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5})

    fig.suptitle("Reliability Diagrams", fontsize=14)
    fig.tight_layout()
    out_path = _ensure_plots_dir() / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Reliability diagram saved: %s", out_path)
    return out_path


def _compute_ece_from_bins(
    acc: np.ndarray, conf: np.ndarray, counts: np.ndarray,
) -> float:
    total = int(counts.sum())
    if total == 0:
        return 0.0
    return float(np.sum(counts * np.abs(acc - conf)) / total)


# ---------------------------------------------------------------------------
# 2. Cumulative return curves
# ---------------------------------------------------------------------------

def plot_cumulative_returns(
    portfolios: dict[str, np.ndarray],
    dates: pd.DatetimeIndex | None = None,
    filename: str = "cumulative_returns.png",
) -> Path:
    """Plot cumulative return curves for CA-MARL and all baselines.

    Args:
        portfolios: ``{strategy_name: daily_return_array}``.
        dates: optional DatetimeIndex for x-axis labels.
        filename: output filename.

    Returns:
        Path to the saved figure.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    x = dates if dates is not None else np.arange(len(next(iter(portfolios.values()))))

    for name, rets in portfolios.items():
        cum = np.cumprod(1.0 + rets)
        style = _STYLE.get(name, {})
        ax.plot(x, cum, color=style.get("color", "#333"),
                marker=style.get("marker", ""), markevery=max(1, len(rets) // 20),
                label=style.get("label", name), lw=1.5)

    ax.axhline(y=1.0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel("Date" if dates is not None else "Trading Day")
    ax.set_ylabel("Cumulative Return")
    ax.set_title("Cumulative Portfolio Returns")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out_path = _ensure_plots_dir() / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Cumulative return plot saved: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# 3. Regime timeline overlay
# ---------------------------------------------------------------------------

def plot_regime_timeline(
    prices: pd.DataFrame,
    regime_labels: np.ndarray | None = None,
    filename: str = "regime_timeline.png",
) -> Path:
    """Plot asset prices with regime timeline overlay.

    Args:
        prices: DataFrame with DatetimeIndex and ticker columns.
        regime_labels: optional array of regime labels (0/1 for bull/bear).
        filename: output filename.

    Returns:
        Path to the saved figure.
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    norm = prices / prices.iloc[0]
    for col in norm.columns:
        ax.plot(norm.index, norm[col], lw=0.8, alpha=0.6)

    if regime_labels is not None and len(regime_labels) == len(prices):
        regime_mask = np.array(regime_labels).astype(bool)
        idx = prices.index
        ax.fill_between(idx, 0.85, 1.15,
                        where=regime_mask,
                        color="green", alpha=0.1,
                        label="Bull Regime")
        ax.fill_between(idx, 0.85, 1.15,
                        where=~regime_mask,
                        color="red", alpha=0.1,
                        label="Bear Regime")

    ax.set_xlabel("Date")
    ax.set_ylabel("Normalised Price")
    ax.set_title("Market Prices with Regime Overlay")
    if regime_labels is not None:
        ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out_path = _ensure_plots_dir() / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Regime timeline saved: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# 4. Ablation bar charts
# ---------------------------------------------------------------------------

def plot_ablation_bars(
    ablation_results: dict[str, dict[str, float]],
    metric: str = "sharpe_ratio",
    filename: str = "ablation_bars.png",
) -> Path:
    """Plot ablation study results as a bar chart.

    Args:
        ablation_results: ``{ablation_name: {metric_name: value}}``.
        metric: which metric to plot (e.g. "sharpe_ratio", "cumulative_return").
        filename: output filename.

    Returns:
        Path to the saved figure.
    """
    names = list(ablation_results.keys())
    values = [ablation_results[n].get(metric, float("nan")) for n in names]
    colors = ["#1f77b4" if n == "ca_marl" else "#ff7f0e" for n in names]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(names, values, color=colors, edgecolor="black", lw=0.5)

    for bar, val in zip(bars, values):
        if not (isinstance(val, float) and np.isnan(val)):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    ax.axhline(y=0, color="gray", lw=0.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(f"Ablation Study: {metric.replace('_', ' ').title()}")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()

    out_path = _ensure_plots_dir() / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Ablation bar chart saved: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# 5. Aggregate results table (saved as CSV)
# ---------------------------------------------------------------------------

def save_results_table(
    all_results: dict[str, Any],
    filename: str = "results_table.csv",
) -> Path:
    """Save a human-readable results table as CSV.

    Args:
        all_results: dict keyed by experiment/baseline name with metric dicts.
        filename: output filename.

    Returns:
        Path to the saved CSV.
    """
    rows: list[dict[str, Any]] = []
    for name, metrics in all_results.items():
        row = {"strategy": name}
        if isinstance(metrics, dict):
            row.update(metrics)
        rows.append(row)

    df = pd.DataFrame(rows)
    out_path = _ensure_plots_dir() / filename
    df.to_csv(out_path, index=False)
    logger.info("Results table saved: %s", out_path)
    return out_path
