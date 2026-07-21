"""Generate publication-quality figures and tables for the CA-MARL paper.

Reads existing campaign results and produces:

Figures (300 DPI, serif, publication-ready):
  1. fig01_cumulative_returns.pdf  — CA-MARL vs baselines
  2. fig02_reliability_diagrams.pdf — per-agent calibration curves
  3. fig03_ablation_bars.pdf — ablation study comparison
  4. fig04_regime_timeline.pdf — market regime overlay

Tables (LaTeX):
  1. table01_summary.tex — cross-seed aggregated metrics
  2. table02_per_fold.tex — per-fold metrics
  3. table03_ablation.tex — ablation study results
  4. table04_calibration.tex — calibration metrics
"""

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._config import DEFAULT_AGENT_CONFIGS
from experiments._data_cache import load_cached_dataset
from experiments._utils import RESULTS_DIR, PLOTS_DIR, load_results

logger = logging.getLogger("publication_outputs")

# ---------------------------------------------------------------------------
# Publication style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.format": "pdf",
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "lines.linewidth": 1.5,
    "lines.markersize": 4,
    "figure.figsize": (7, 3.5),
})

COLORS = {
    "ca_marl": "#1f77b4",
    "equal_weight": "#ff7f0e",
    "buy_and_hold": "#2ca02c",
    "static_mvo": "#d62728",
}

AGENT_COLORS = {
    "market_agent": "#9467bd",
    "risk_agent": "#8c564b",
    "allocation_agent": "#e377c2",
}

OUT_DIR = PLOTS_DIR / "publication"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(exist_ok=True)
TAB_DIR.mkdir(exist_ok=True)

CAMPAIGN_ID = "campaign_v1"


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_campaign(campaign_id: str = CAMPAIGN_ID):
    files = sorted(RESULTS_DIR.glob(f"{campaign_id}_seed_*.json"))
    results = [json.loads(f.read_text()) for f in files]
    data = load_cached_dataset()
    return results, data


def maybe_format(v, fmt=".4f"):
    if isinstance(v, float) and not (np.isnan(v) or np.isinf(v)):
        return f"{v:{fmt}}"
    return "N/A"


# ===================================================================
# FIGURE 1: Cumulative returns
# ===================================================================
def fig_cumulative_returns(results, data, filename="fig01_cumulative_returns"):
    """CA-MARL (per-seed, shaded) vs baselines."""
    prices = data["realized_prices"]
    seed_data = results[0]

    fig, ax = plt.subplots(figsize=(7, 3.5))

    # Per-seed CA-MARL trajectories
    all_curves = []
    for sd in results:
        rets_list = []
        for fold in sd["folds"]:
            s = fold["schedule"]
            fp = prices.iloc[s["test"][0]:s["test"][1]]
            tickers = [t for t in fold["allocation"] if t in fp.columns]
            if not tickers:
                continue
            w = np.array([fold["allocation"][t] for t in tickers], dtype=np.float64)
            p = fp[tickers].values.astype(np.float64)
            rets = np.diff(p, axis=0) / (p[:-1] + 1e-12) @ w
            rets_list.append(rets)
        if rets_list:
            all_rets = np.concatenate(rets_list)
            cum = np.cumprod(1.0 + all_rets)
            all_curves.append(cum)

    if all_curves:
        max_len = min(len(c) for c in all_curves)
        curves = np.array([c[:max_len] for c in all_curves])
        mean_c = curves.mean(axis=0)
        std_c = curves.std(axis=0, ddof=1)
        x = np.arange(max_len)
        ax.plot(x, mean_c, color=COLORS["ca_marl"], label=r"\textsc{ca-marl}", lw=2)
        ax.fill_between(x, mean_c - std_c, mean_c + std_c,
                         color=COLORS["ca_marl"], alpha=0.15)

    # Baselines from first seed
    base_rets = {}
    for bname in ["equal_weight", "buy_and_hold", "static_mvo"]:
        rets_list = []
        for fold in seed_data["folds"]:
            s = fold["schedule"]
            fp = prices.iloc[s["test"][0]:s["test"][1]]

            if bname == "equal_weight":
                n = len(fp.columns)
                w = np.array([1.0 / n] * n)
                p = fp.values.astype(np.float64)
                rets = np.diff(p, axis=0) / (p[:-1] + 1e-12) @ w
            elif bname == "buy_and_hold":
                n = len(fp.columns)
                initial_w = np.array([1.0 / n] * n)
                norm_v = fp / fp.iloc[0]
                port_v = norm_v @ initial_w
                rets = port_v.pct_change().dropna().values
            else:
                bm_fold = fold.get("baselines", {}).get(bname, {})
                alloc = bm_fold.get("allocation", fold.get("allocation"))
                tickers = [t for t in alloc if t in fp.columns]
                if not tickers:
                    continue
                w = np.array([alloc[t] for t in tickers], dtype=np.float64)
                p = fp[tickers].values.astype(np.float64)
                rets = np.diff(p, axis=0) / (p[:-1] + 1e-12) @ w

            rets_list.append(rets)
        if rets_list:
            base_rets[bname] = np.concatenate(rets_list)

    for bname, rets in base_rets.items():
        cum = np.cumprod(1.0 + rets[:max_len])
        ax.plot(x, cum, color=COLORS.get(bname, "#333"),
                label=bname.replace("_", " ").title(), lw=1.2, ls="--")

    ax.axhline(y=1.0, color="gray", lw=0.5, ls=":")
    ax.set_xlabel("Trading Day")
    ax.set_ylabel("Cumulative Return")
    ax.set_title("Cumulative Portfolio Returns (Walk-Forward)")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    path = FIG_DIR / f"{filename}.pdf"
    fig.savefig(path)
    plt.close(fig)
    logger.info("Saved %s", path)
    return path


# ===================================================================
# FIGURE 2: Calibration error analysis
# ===================================================================
def fig_calibration_analysis(results, filename="fig02_calibration_analysis"):
    """Per-agent calibration error analysis.

    NOTE: This is NOT a standard reliability diagram. True reliability
    diagrams require (confidence, label) pairs that are not persisted in
    the JSON output. This figure plots ECE vs Brier score per agent
    across folds and seeds to show the relationship between calibration
    error and confidence error. Each point represents one fold-seed observation.
    """
    n_bins = 10
    agent_names = ["market_agent", "risk_agent", "allocation_agent"]

    all_labels = {a: [] for a in agent_names}
    all_confs = {a: [] for a in agent_names}

    for sd in results:
        for fold in sd["folds"]:
            cm = fold.get("calibration_metrics", {})
            for aname in agent_names:
                acm = cm.get(aname, {})
                ece = acm.get("ece")
                bs = acm.get("brier_score")
                if ece is not None:
                    all_labels[aname].append(ece)
                    all_confs[aname].append(bs)

    fig, axes = plt.subplots(1, 3, figsize=(9, 3))
    for ax, aname in zip(axes, agent_names):
        eces = np.array(all_labels[aname])
        briers = np.array(all_confs[aname])
        if len(eces) == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            continue

        # Raw scatter (not normalised)
        ax.scatter(briers, eces, color=AGENT_COLORS.get(aname, "#333"),
                   alpha=0.6, s=20, edgecolors="none")

        # Mean marker
        ax.scatter(np.mean(briers), np.mean(eces),
                   color=AGENT_COLORS.get(aname, "#333"),
                   s=80, marker="D", edgecolors="black", linewidths=0.5,
                   zorder=5, label="Mean")

        ax.set_xlabel("Brier Score")
        ax.set_ylabel("ECE")
        title = aname.replace("_", " ").title().replace("Agent", "")
        ax.set_title(title)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.2)

        # Annotations
        ax.text(0.05, 0.88, f"Mean ECE={np.mean(eces):.4f}\nMean Brier={np.mean(briers):.4f}",
                transform=ax.transAxes, fontsize=7, verticalalignment="top",
                bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.4})

    fig.suptitle("Calibration Error Analysis (Per Agent, Across Folds and Seeds)",
                 fontsize=11, y=1.02)
    fig.tight_layout()
    path = FIG_DIR / f"{filename}.pdf"
    fig.savefig(path)
    plt.close(fig)
    logger.info("Saved %s", path)
    return path


# ===================================================================
# FIGURE 3: Ablation bar charts
# ===================================================================
def fig_ablation_bars(results, filename="fig03_ablation_bars"):
    """Ablation study bar chart."""
    ab_path = RESULTS_DIR / f"{CAMPAIGN_ID}_ablations_seed_0000.json"
    if not ab_path.exists():
        logger.warning("No ablation results at %s", ab_path)
        return None

    ab_data = json.loads(ab_path.read_text())
    ablation_metrics = {}
    for name, ab in ab_data.items():
        fm = ab.get("financial_metrics", {})
        if fm:
            ablation_metrics[name] = fm

    if not ablation_metrics:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))

    for ax, metric, ylabel in [
        (ax1, "sharpe_ratio", "Sharpe Ratio"),
        (ax2, "cumulative_return", "Cumulative Return"),
    ]:
        names = list(ablation_metrics.keys())
        values = [ablation_metrics[n].get(metric, float("nan")) for n in names]
        colors = ["#1f77b4" if n == "campaign_v1" else "#ff7f0e" for n in names]

        bars = ax.bar(names, values, color=colors, edgecolor="black", lw=0.4)
        for bar, val in zip(bars, values):
            if isinstance(val, float) and not np.isnan(val):
                va = "bottom" if val >= 0 else "top"
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{val:.3f}", ha="center", va=va, fontsize=7)

        ax.axhline(y=0, color="gray", lw=0.5)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([n.replace("campaign_v1", "CA-MARL").replace("_", " ").title()
                           for n in names], rotation=35, ha="right", fontsize=7)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25, axis="y")

    fig.suptitle("Ablation Study Results", fontsize=11)
    fig.tight_layout()
    path = FIG_DIR / f"{filename}.pdf"
    fig.savefig(path)
    plt.close(fig)
    logger.info("Saved %s", path)
    return path


# ===================================================================
# FIGURE 4: Fold boundaries timeline
# ===================================================================
def fig_regime_timeline(data, filename="fig04_regime_timeline"):
    """Normalised price chart with fold boundaries."""
    prices = data["realized_prices"]
    fig, ax = plt.subplots(figsize=(8, 3))
    norm = prices / prices.iloc[0]
    for col in norm.columns:
        ax.plot(norm.index, norm[col], lw=0.6, alpha=0.5)

    ax.set_xlabel("Date")
    ax.set_ylabel("Normalised Price")
    ax.set_title("Nifty 50 Constituent Prices (2020–2024)")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    path = FIG_DIR / f"{filename}.pdf"
    fig.savefig(path)
    plt.close(fig)
    logger.info("Saved %s", path)
    return path


# ===================================================================
# TABLE 1: Summary statistics (LaTeX)
# ===================================================================
def table_summary_latex(results, filename="table01_summary"):
    """Cross-seed aggregated metrics as LaTeX."""
    metric_keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                   "volatility", "cumulative_return"]

    rows = []
    for metric in metric_keys:
        values = []
        for r in results:
            agg = r.get("aggregated", {})
            v = agg.get(metric, {}).get("mean")
            if v is not None:
                values.append(v)
        if not values:
            continue
        arr = np.array(values)
        mean_v = np.mean(arr)
        std_v = np.std(arr, ddof=1)
        ci95 = 1.96 * std_v / np.sqrt(len(arr))
        rows.append({
            "Metric": metric.replace("_", " ").title(),
            "Mean": mean_v,
            "Std": std_v,
            "CI95": ci95,
            "Min": np.min(arr),
            "Max": np.max(arr),
        })

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Aggregated CA-MARL Performance Across 5 Random Seeds}",
        r"\label{tab:summary}",
        r"\begin{tabular}{lcccccc}",
        r"\toprule",
        r"Metric & Mean & Std.\ Dev. & 95\% CI & Min & Max \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"  {row['Metric']} & {row['Mean']:.4f} & {row['Std']:.4f} & "
            f"[{row['Mean']-row['CI95']:.3f}, {row['Mean']+row['CI95']:.3f}] & "
            f"{row['Min']:.4f} & {row['Max']:.4f} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    path = TAB_DIR / f"{filename}.tex"
    path.write_text("\n".join(lines))
    logger.info("Saved %s", path)
    return path


# ===================================================================
# TABLE 2: Per-fold metrics (LaTeX)
# ===================================================================
def table_per_fold_latex(results, filename="table02_per_fold"):
    """Per-fold metrics across all seeds."""
    metric_keys = ["sharpe_ratio", "sortino_ratio", "max_drawdown",
                   "volatility", "cumulative_return"]

    fold_data = {}
    for r in results:
        seed = r["seed"]
        for fold in r["folds"]:
            fid = f"{fold['fold_id']}"
            fm = fold.get("financial_metrics", {})
            key = (seed, fid)
            fold_data[key] = fm

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Per-Fold Performance Metrics (All Seeds)}",
        r"\label{tab:per_fold}",
        r"\begin{tabular}{ccccccc}",
        r"\toprule",
        r"Seed & Fold & Sharpe & Sortino & MaxDD & Vol & CumRet \\",
        r"\midrule",
    ]

    seeds = sorted(set(k[0] for k in fold_data))
    for seed in seeds:
        for fid in ["01", "02", "03", "04"]:
            key = (seed, fid)
            fm = fold_data.get(key, {})
            sr = maybe_format(fm.get("sharpe_ratio"))
            so = maybe_format(fm.get("sortino_ratio"))
            md = maybe_format(fm.get("max_drawdown"))
            vl = maybe_format(fm.get("volatility"))
            cr = maybe_format(fm.get("cumulative_return"))
            lines.append(f"  {seed} & {fid} & {sr} & {so} & {md} & {vl} & {cr} \\\\")
        lines.append(r"  \cmidrule{1-7}")

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    path = TAB_DIR / f"{filename}.tex"
    path.write_text("\n".join(lines))
    logger.info("Saved %s", path)
    return path


# ===================================================================
# TABLE 3: Ablation results (LaTeX)
# ===================================================================
def table_ablation_latex(results, filename="table03_ablation"):
    """Ablation study results as LaTeX."""
    ab_path = RESULTS_DIR / f"{CAMPAIGN_ID}_ablations_seed_0000.json"
    if not ab_path.exists():
        logger.warning("No ablation results at %s", ab_path)
        return None

    ab_data = json.loads(ab_path.read_text())

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Ablation Study Results}",
        r"\label{tab:ablation}",
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"Ablation & Sharpe & Sortino & MaxDD & Vol & CumRet \\",
        r"\midrule",
    ]
    for name, ab in ab_data.items():
        fm = ab.get("financial_metrics", {})
        sr = maybe_format(fm.get("sharpe_ratio"))
        so = maybe_format(fm.get("sortino_ratio"))
        md = maybe_format(fm.get("max_drawdown"))
        vl = maybe_format(fm.get("volatility"))
        cr = maybe_format(fm.get("cumulative_return"))
        label = "CA-MARL" if name == "campaign_v1" else name.replace("_", " ").title()
        lines.append(f"  {label} & {sr} & {so} & {md} & {vl} & {cr} \\\\")

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    path = TAB_DIR / f"{filename}.tex"
    path.write_text("\n".join(lines))
    logger.info("Saved %s", path)
    return path


# ===================================================================
# TABLE 4: Calibration metrics (LaTeX)
# ===================================================================
def table_calibration_latex(results, filename="table04_calibration"):
    """Per-agent calibration metrics as LaTeX."""
    agent_names = ["market_agent", "risk_agent", "allocation_agent"]

    metrics_by_agent = {a: {"ece": [], "brier": []} for a in agent_names}
    for r in results:
        for fold in r["folds"]:
            cm = fold.get("calibration_metrics", {})
            for aname in agent_names:
                acm = cm.get(aname, {})
                ece = acm.get("ece")
                bs = acm.get("brier_score")
                if ece is not None:
                    metrics_by_agent[aname]["ece"].append(ece)
                if bs is not None:
                    metrics_by_agent[aname]["brier"].append(bs)

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Calibration Metrics Per Agent (Across Folds and Seeds)}",
        r"\label{tab:calibration}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Agent & ECE (mean) & ECE (std) & Brier (mean) & Brier (std) \\",
        r"\midrule",
    ]
    for aname in agent_names:
        eces = np.array(metrics_by_agent[aname]["ece"])
        briers = np.array(metrics_by_agent[aname]["brier"])
        label = aname.replace("_", " ").title().replace("Agent", "Agent")
        lines.append(
            f"  {label} & {np.mean(eces):.4f} & {np.std(eces, ddof=1):.4f} & "
            f"{np.mean(briers):.4f} & {np.std(briers, ddof=1):.4f} \\\\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    path = TAB_DIR / f"{filename}.tex"
    path.write_text("\n".join(lines))
    logger.info("Saved %s", path)
    return path


# ===================================================================
# Main
# ===================================================================
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    logger.info("Generating publication-quality outputs for %s", CAMPAIGN_ID)

    results, data = load_campaign()

    logger.info("Loaded %d seed results, dataset: %s", len(results), data["features"].shape)

    # Figures
    fig_cumulative_returns(results, data)
    fig_calibration_analysis(results)
    fig_ablation_bars(results)
    fig_regime_timeline(data)

    # Tables
    table_summary_latex(results)
    table_per_fold_latex(results)
    table_ablation_latex(results)
    table_calibration_latex(results)

    # List artifacts
    print()
    print("=" * 70)
    print("PUBLICATION ARTIFACTS GENERATED")
    print("=" * 70)
    print(f"\nFigures ({FIG_DIR}):")
    for f in sorted(FIG_DIR.glob("*")):
        sz = f.stat().st_size / 1024
        print(f"  {f.name} ({sz:.1f} KB)")

    print(f"\nTables ({TAB_DIR}):")
    for f in sorted(TAB_DIR.glob("*")):
        print(f"  {f.name}")

    print(f"\nOutput root: {OUT_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
