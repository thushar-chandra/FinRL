"""Final statistical analyses using existing JSON experiment outputs.

Performs:
  1. Paired permutation test: CA-MARL vs Equal-Weight (Sharpe ratio)
  2. Win/loss sign test: CA-MARL vs Equal-Weight
  3. Kruskal-Wallis test: Sharpe ratio differences across folds
  4. Effect size (Cohen's d): CA-MARL vs each baseline
"""
import json
import random
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent / "results"

random.seed(42)
np.random.seed(42)

# Load all paired observations
pairs = []  # (seed, fold_id, ca_sharpe, ew_sharpe)
ca_by_fold = {i: [] for i in range(1, 5)}  # fold -> [Sharpe values]

for seed in range(42, 47):
    f = BASE / f"campaign_v1_seed_{seed:04d}.json"
    d = json.loads(f.read_text())
    for fold in d["folds"]:
        fid = int(fold["fold_id"])
        ca_sr = fold["financial_metrics"]["sharpe_ratio"]
        ew_sr = fold["baselines"]["equal_weight"]["sharpe_ratio"]
        pairs.append((seed, fid, ca_sr, ew_sr))
        ca_by_fold[fid].append(ca_sr)

ca_srs = np.array([p[2] for p in pairs])
ew_srs = np.array([p[3] for p in pairs])
deltas = ca_srs - ew_srs

n = len(pairs)

print("=" * 70)
print("TASK 1: FINAL STATISTICAL ANALYSES")
print("=" * 70)

# ------------------------------------------------------------------
# 1. Paired permutation test
# ------------------------------------------------------------------
print()
print("1. PAIRED PERMUTATION TEST: CA-MARL vs EQUAL-WEIGHT")
print("-" * 50)
obs_mean_diff = np.mean(deltas)
obs_median_diff = np.median(deltas)

n_permutations = 100000
count_extreme = 0
for i in range(n_permutations):
    # Sign-flip each pair (under H0: exchangeable)
    flip = np.random.choice([-1, 1], size=n)
    perm_deltas = deltas * flip
    perm_mean = np.mean(perm_deltas)
    if abs(perm_mean) >= abs(obs_mean_diff):
        count_extreme += 1

p_value_perm = (count_extreme + 1) / (n_permutations + 1)  # +1 correction

print(f"  Observations: {n} (5 seeds x 4 folds)")
print(f"  CA-MARL mean Sharpe: {np.mean(ca_srs):.4f}")
print(f"  EW mean Sharpe:      {np.mean(ew_srs):.4f}")
print(f"  Mean delta:          {obs_mean_diff:.4f}")
print(f"  Median delta:        {obs_median_diff:.4f}")
print(f"  Delta std:           {np.std(deltas, ddof=1):.4f}")
print(f"  Permutation p-value: {p_value_perm:.4f} (n_perm={n_permutations})")
print(f"  Significant at 0.05: {p_value_perm < 0.05}")
if p_value_perm < 0.05:
    print(f"  Direction: CA-MARL {'beats' if obs_mean_diff > 0 else 'underperforms'} EW")
else:
    print(f"  Conclusion: Not statistically significant at alpha=0.05")

# ------------------------------------------------------------------
# 2. Win/loss sign test
# ------------------------------------------------------------------
print()
print("2. SIGN TEST: CA-MARL vs EQUAL-WEIGHT (win/loss)")
print("-" * 50)
wins = int(np.sum(deltas > 0))
losses = int(np.sum(deltas < 0))
ties = int(np.sum(deltas == 0))

# Binomial test p-value: P(X >= wins | n=non_ties, p=0.5)
from math import comb
non_ties = wins + losses
p_value_sign = sum(comb(non_ties, k) * (0.5 ** non_ties)
                   for k in range(wins, non_ties + 1)) * 2  # two-tailed

print(f"  CA-MARL wins:  {wins}/{n} ({100*wins/n:.0f}%)")
print(f"  EW wins:       {losses}/{n} ({100*losses/n:.0f}%)")
print(f"  Ties:          {ties}/{n}")
print(f"  Sign test p:   {p_value_sign:.4f} (two-tailed binomial)")
print(f"  Significant at 0.05: {p_value_sign < 0.05}")

# ------------------------------------------------------------------
# 3. Kruskal-Wallis: Sharpe by fold
# ------------------------------------------------------------------
print()
print("3. KRUSKAL-WALLIS TEST: Sharpe ratio by fold")
print("-" * 50)
from scipy import stats as scipy_stats

fold_groups = [ca_by_fold[fid] for fid in sorted(ca_by_fold.keys())]
h_stat, p_value_kw = scipy_stats.kruskal(*fold_groups)

print(f"  Fold 01: mean={np.mean(ca_by_fold[1]):.4f} std={np.std(ca_by_fold[1], ddof=1):.4f}")
print(f"  Fold 02: mean={np.mean(ca_by_fold[2]):.4f} std={np.std(ca_by_fold[2], ddof=1):.4f}")
print(f"  Fold 03: mean={np.mean(ca_by_fold[3]):.4f} std={np.std(ca_by_fold[3], ddof=1):.4f}")
print(f"  Fold 04: mean={np.mean(ca_by_fold[4]):.4f} std={np.std(ca_by_fold[4], ddof=1):.4f}")
print(f"  H-statistic: {h_stat:.4f}")
print(f"  Kruskal-Wallis p-value: {p_value_kw:.6e}")
print(f"  Significant at 0.05: {p_value_kw < 0.05}")
if p_value_kw < 0.05:
    # Post-hoc: pairwise Mann-Whitney
    print()
    print("  Post-hoc pairwise comparisons (Mann-Whitney U):")
    fold_ids = sorted(ca_by_fold.keys())
    for i in range(len(fold_ids)):
        for j in range(i + 1, len(fold_ids)):
            u_stat, p_mw = scipy_stats.mannwhitneyu(
                ca_by_fold[fold_ids[i]], ca_by_fold[fold_ids[j]]
            )
            sig = "SIGNIFICANT" if p_mw < 0.05 else "not significant"
            print(f"    Fold {fold_ids[i]} vs Fold {fold_ids[j]}: U={u_stat:.1f}, p={p_mw:.4f} ({sig})")

# ------------------------------------------------------------------
# 4. Effect sizes: CA-MARL vs each baseline
# ------------------------------------------------------------------
print()
print("4. EFFECT SIZES (Cohen's d): CA-MARL vs baselines")
print("-" * 50)

# For baselines, load the first seed's per-fold data (baselines are deterministic)
d42 = json.loads((BASE / "campaign_v1_seed_0042.json").read_text())
baselines = {"equal_weight": [], "buy_and_hold": [], "static_mvo": []}
for fold in d42["folds"]:
    for bname in baselines:
        baselines[bname].append(fold["baselines"][bname]["sharpe_ratio"])

for bname, bvals in baselines.items():
    b_arr = np.array(bvals)
    # Cohen's d = (mean_diff) / pooled_std
    n1, n2 = len(ca_srs), len(b_arr)
    mean1, mean2 = np.mean(ca_srs), np.mean(b_arr)
    var1 = np.var(ca_srs, ddof=1)
    var2 = np.var(b_arr, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    d_cohen = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0.0
    print(f"  CA-MARL vs {bname:20s}: d = {d_cohen:.4f} "
          f"({'negligible' if abs(d_cohen) < 0.2 else 'small' if abs(d_cohen) < 0.5 else 'medium' if abs(d_cohen) < 0.8 else 'large'})")

# ------------------------------------------------------------------
# 5. Summary
# ------------------------------------------------------------------
print()
print("=" * 70)
print("STATISTICAL ANALYSIS SUMMARY")
print("=" * 70)
print(f"  Permutation test p-value:           {p_value_perm:.4f}")
print(f"  Sign test p-value:                  {p_value_sign:.4f}")
print(f"  Kruskal-Wallis p-value:             {p_value_kw:.6e}")
print(f"  CA-MARL vs EW win rate:             {wins}/{n} ({100*wins/n:.0f}%)")
print(f"  CA-MARL vs EW mean delta:           {obs_mean_diff:.4f}")
print()
print("  Interpretation:")
if p_value_perm < 0.05:
    print("    CA-MARL Sharpe is statistically significantly different from EW.")
else:
    print("    No statistically significant difference detected between CA-MARL and EW.")
if p_value_kw < 0.05:
    print("    Walk-forward folds produce significantly different Sharpe ratios (regime effect).")
else:
    print("    No significant difference in Sharpe across folds.")
print()
print("Done.")
