"""Audit: check specific claims from the review report against actual data."""
import json
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent / "results"

print("=" * 70)
print("CLAIM AUDIT: All 20 fold-seed Sharpe ratios are positive")
print("=" * 70)
neg_count = 0
for seed in range(42, 47):
    f = BASE / f"campaign_v1_seed_{seed:04d}.json"
    d = json.loads(f.read_text())
    for fold in d["folds"]:
        sr = fold["financial_metrics"]["sharpe_ratio"]
        if sr <= 0:
            neg_count += 1
            print(f"  NEGATIVE: seed={seed} fold={fold['fold_id']} Sharpe={sr:.4f}")
print(f"  Negative count: {neg_count}/20")
print(f"  Claim supported: {neg_count == 0}")

print()
print("=" * 70)
print("CLAIM AUDIT: Per-fold CA-MARL vs Equal-Weight (all seeds)")
print("=" * 70)
header = f"{'Seed':>5s} {'Fold':>4s} {'CA-MARL':>10s} {'EW':>10s} {'Delta':>10s}"
print(header)
print("-" * len(header))
ca_wins = 0
total = 0
max_underperform = -float("inf")
for seed in range(42, 47):
    f = BASE / f"campaign_v1_seed_{seed:04d}.json"
    d = json.loads(f.read_text())
    for fold in d["folds"]:
        total += 1
        ca = fold["financial_metrics"]["sharpe_ratio"]
        ew = fold["baselines"]["equal_weight"]["sharpe_ratio"]
        delta = ca - ew
        if ca > ew:
            ca_wins += 1
        else:
            max_underperform = max(max_underperform, delta)  # closest to zero negative
        print(f"{seed:5d} {fold['fold_id']:>4s} {ca:>10.4f} {ew:>10.4f} {delta:>+10.4f}")

print(f"\nCA-MARL beats EW: {ca_wins}/{total} ({100*ca_wins/total:.0f}%)")
print(f"EW beats CA-MARL: {total - ca_wins}/{total} ({(100*(total-ca_wins)/total):.0f}%)")
print(f"Delta range: [{min(d for d in []) if False else 'see above'}]")

print()
print("=" * 70)
print("CLAIM AUDIT: Fold 01 is weakest, Fold 03 is strongest")
print("=" * 70)
fold_srs = {f"Fold {i:02d}": [] for i in range(1, 5)}
for seed in range(42, 47):
    f = BASE / f"campaign_v1_seed_{seed:04d}.json"
    d = json.loads(f.read_text())
    for fold in d["folds"]:
        key = f"Fold {fold['fold_id']}"
        fold_srs[key].append(fold["financial_metrics"]["sharpe_ratio"])

for key in sorted(fold_srs.keys()):
    vals = np.array(fold_srs[key])
    print(f"  {key}: mean={np.mean(vals):.4f} std={np.std(vals, ddof=1):.4f} "
          f"min={np.min(vals):.4f} max={np.max(vals):.4f}")

print()
print("=" * 70)
print("STATISTICAL TEST: Paired t-test CA-MARL vs EW (per fold, seed 42)")
print("=" * 70)
from scipy import stats
f42 = json.loads((BASE / "campaign_v1_seed_0042.json").read_text())
ca_srs = []
ew_srs = []
for fold in f42["folds"]:
    ca_srs.append(fold["financial_metrics"]["sharpe_ratio"])
    ew_srs.append(fold["baselines"]["equal_weight"]["sharpe_ratio"])
t_stat, p_val = stats.ttest_rel(ca_srs, ew_srs)
print(f"  CA-MARL: {np.mean(ca_srs):.4f} +/- {np.std(ca_srs, ddof=1):.4f}")
print(f"  EW:      {np.mean(ew_srs):.4f} +/- {np.std(ew_srs, ddof=1):.4f}")
print(f"  Paired t: t={t_stat:.4f}, p={p_val:.4f}")
print(f"  Statistically significant at alpha=0.05: {p_val < 0.05}")

print()
print("=" * 70)
print("CHECK: Are calibrated confidences stored in JSON?")
print("=" * 70)
d42 = json.loads((BASE / "campaign_v1_seed_0042.json").read_text())
fold0 = d42["folds"][0]
print(f"  Top-level keys in fold: {list(fold0.keys())}")
print(f"  calibration_metrics present: {'calibration_metrics' in fold0}")
cm = fold0.get("calibration_metrics", {})
print(f"  Calibration metrics content: {list(cm.keys())}")
for agent, metrics in cm.items():
    print(f"    {agent}: ECE={metrics.get('ece', 'N/A')}, Brier={metrics.get('brier_score', 'N/A')}")
print(f"  Are calibrated_confidence values stored? {'calibrated_confidences' in fold0}")
print(f"  Are raw_confidence values stored? {'raw_confidences' in fold0}")
