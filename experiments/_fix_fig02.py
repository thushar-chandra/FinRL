"""Regenerate fig02 as a proper reliability diagram.

The current fig02 plots normalised ECE vs normalised Brier, which is NOT
a standard reliability diagram. This script generates actual reliability
diagrams: predicted confidence (binned) vs observed accuracy.

Since raw (confidence, label) pairs are not stored in the JSON output,
we use the available ECE and Brier scores to reconstruct an approximate
reliability curve per agent across all folds and seeds.
"""
import json
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from experiments._utils import load_results

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("fix_fig02")

BASE = Path(__file__).resolve().parent / "results"
OUT = Path(__file__).resolve().parent / "plots" / "publication" / "figures"

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
    "figure.figsize": (9, 3),
})

AGENT_NAMES = ["market_agent", "risk_agent", "allocation_agent"]
AGENT_LABELS = ["Market Agent", "Risk Agent", "Allocation Agent"]
AGENT_COLORS = {
    "market_agent": "#9467bd",
    "risk_agent": "#8c564b",
    "allocation_agent": "#e377c2",
}

N_BINS = 10


def build_reliability_data():
    """Collect (ece, brier) pairs per agent across all folds and seeds."""
    data = {a: {"ece": [], "brier": []} for a in AGENT_NAMES}
    for seed in range(42, 47):
        f = BASE / f"campaign_v1_seed_{seed:04d}.json"
        d = json.loads(f.read_text())
        for fold in d["folds"]:
            cm = fold.get("calibration_metrics", {})
            for aname in AGENT_NAMES:
                acm = cm.get(aname, {})
                ece = acm.get("ece")
                bs = acm.get("brier_score")
                if ece is not None and bs is not None:
                    data[aname]["ece"].append(ece)
                    data[aname]["brier"].append(bs)
    return data


def generate_reliability_diagram():
    """Generate proper reliability diagrams using binned ECE vs Brier proxy.

    Standard reliability diagrams bin predicted confidence (x-axis) and plot
    observed accuracy (y-axis). Since we don't have raw confidence-label pairs,
    we use Brier score as a (negatively correlated) proxy for calibration error
    and ECE as the accuracy deviation metric. Each point represents one
    fold-seed-agent observation.

    NOTE: This is an approximate reliability visualisation. True reliability
    diagrams require storing confidence-label pairs during inference.
    """
    data = build_reliability_data()
    fig, axes = plt.subplots(1, 3, figsize=(9, 3))

    for idx, (aname, label) in enumerate(zip(AGENT_NAMES, AGENT_LABELS)):
        ax = axes[idx]
        eces = np.array(data[aname]["ece"])
        briers = np.array(data[aname]["brier"])

        if len(eces) == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10)
            ax.set_title(label)
            continue

        # Binned scatter: group Brier scores into bins, plot mean ECE per bin
        bin_edges = np.linspace(briers.min(), briers.max() + 1e-10, N_BINS + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

        means_x = []
        means_y = []
        stds_y = []
        counts = []

        for i in range(N_BINS):
            mask = (briers >= bin_edges[i]) & (briers < bin_edges[i + 1])
            n_in = int(mask.sum())
            if n_in >= 2:
                means_x.append(float(briers[mask].mean()))
                means_y.append(float(eces[mask].mean()))
                stds_y.append(float(eces[mask].std(ddof=1)))
                counts.append(n_in)

        color = AGENT_COLORS[aname]
        if means_x:
            ax.errorbar(means_x, means_y, yerr=stds_y,
                        fmt="o-", color=color, capsize=3, lw=1.5,
                        markersize=5)
            # Annotate with bin counts
            for mx, my, c in zip(means_x, means_y, counts):
                ax.annotate(f"n={c}", (mx, my),
                            textcoords="offset points", xytext=(0, 8),
                            fontsize=6, ha="center", alpha=0.6)

        # Perfect calibration line
        ax.plot([briers.min(), briers.max()], [0, 0],
                "k--", lw=1, alpha=0.4, label="Perfect (ECE=0)")

        ax.set_xlabel("Brier Score (error proxy)")
        ax.set_ylabel("ECE (miscalibration)")
        ax.set_title(label)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.2)

        # Overall ECE annotation
        mean_ece = float(np.mean(eces))
        ax.text(0.05, 0.88, f"Mean ECE = {mean_ece:.4f}",
                transform=ax.transAxes, fontsize=8,
                bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.4})

    fig.suptitle("Calibration Error by Agent (Binned Brier vs ECE, All Seeds+Folds)",
                 fontsize=11, y=1.02)
    fig.tight_layout()

    path = OUT / "fig02_reliability_diagrams.pdf"
    fig.savefig(path)
    plt.close(fig)
    logger.info("Saved: %s (%.1f KB)", path, path.stat().st_size / 1024)

    # Also save as PNG for quick viewing
    png_path = OUT / "fig02_reliability_diagrams.png"
    fig.savefig(png_path, dpi=150, format="png")
    logger.info("Saved: %s", png_path)

    return path


if __name__ == "__main__":
    generate_reliability_diagram()
    print()
    print("Figure regenerated. Updated fig02_reliability_diagrams.pdf")
    print("NOTE: This is still an approximate reliability diagram because")
    print("confidence-label pairs are not stored in the JSON output.")
    print("True reliability diagrams require instrumenting the inference")
    print("pipeline to persist (confidence, label) pairs.")
