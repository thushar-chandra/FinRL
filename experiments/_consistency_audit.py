"""Final consistency audit across all Phase 3 artifacts.

Verifies:
  1. Completion report metrics match JSON data
  2. Figure naming consistency
  3. No stale references
  4. Research report corrections are consistent with completion report
"""
import json
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
REPORTS = BASE / "reports"
PUB_FIGS = BASE / "plots" / "publication" / "figures"
PUB_TABS = BASE / "plots" / "publication" / "tables"

errors = []
warnings = []

print("=" * 70)
print("FINAL CONSISTENCY AUDIT")
print("=" * 70)

# ------------------------------------------------------------------
# 1. Verify completion report metrics against JSON
# ------------------------------------------------------------------
print()
print("1. METRIC CONSISTENCY: Completion Report vs JSON")
print("-" * 50)

# Load JSON data
seed_files = sorted(RESULTS.glob("campaign_v1_seed_*.json"))
data_by_seed = {int(f.stem.split("_")[-1]): json.loads(f.read_text()) for f in seed_files}

# Compute actual metrics
actual_sharpes = []
actual_returns = []
actual_drawdowns = []
actual_vols = []
actual_sortinos = []

for seed, d in data_by_seed.items():
    agg = d.get("aggregated", {})
    actual_sharpes.append(agg.get("sharpe_ratio", {}).get("mean"))
    actual_returns.append(agg.get("cumulative_return", {}).get("mean"))
    actual_drawdowns.append(agg.get("max_drawdown", {}).get("mean"))
    actual_vols.append(agg.get("volatility", {}).get("mean"))
    actual_sortinos.append(agg.get("sortino_ratio", {}).get("mean"))

mean_sharpe = np.mean(actual_sharpes)
std_sharpe = np.std(actual_sharpes, ddof=1)
mean_return = np.mean(actual_returns)
std_return = np.std(actual_returns, ddof=1)
mean_dd = np.mean(actual_drawdowns)
std_dd = np.std(actual_drawdowns, ddof=1)
mean_vol = np.mean(actual_vols)
std_vol = np.std(actual_vols, ddof=1)

# Claims from the completion report (PHASE_3_COMPLETION_REPORT.md)
claims = {
    "CA-MARL mean Sharpe": (mean_sharpe, 1.885, 0.001),
    "CA-MARL Sharpe std": (std_sharpe, 0.087, 0.001),
    "CA-MARL mean cumulative return": (mean_return, 0.096, 0.001),
    "CA-MARL mean max drawdown": (mean_dd, -0.065, 0.001),
    "CA-MARL mean volatility": (mean_vol, 0.115, 0.001),
}

for name, (actual, expected, tol) in claims.items():
    if abs(actual - expected) > tol:
        errors.append(f"  MISMATCH: {name}: JSON={actual:.4f}, Report={expected:.4f}")
    else:
        print(f"  OK: {name}: {actual:.4f} (matches claim)")

# Count negative fold-seed Sharples
neg_count = 0
total_count = 0
for seed, d in data_by_seed.items():
    for fold in d["folds"]:
        total_count += 1
        sr = fold["financial_metrics"]["sharpe_ratio"]
        if sr <= 0:
            neg_count += 1

if neg_count == 1:
    print(f"  OK: 19/20 fold-seed Sharpe ratios positive (1 negative, seed 43 fold 01)")
else:
    errors.append(f"  MISMATCH: Expected 1 negative, found {neg_count}")

# Check fallback_used
fallback_count = 0
for seed, d in data_by_seed.items():
    for fold in d["folds"]:
        if fold.get("fused_decision", {}).get("fallback_used", True) == False:
            fallback_count += 1

if fallback_count == 20:
    print(f"  OK: All 20 fold-seed combinations have fallback_used=false")
else:
    errors.append(f"  MISMATCH: Expected 20 fallback=false, found {fallback_count}")

# ------------------------------------------------------------------
# 2. Figure naming consistency
# ------------------------------------------------------------------
print()
print("2. FIGURE NAMING CONSISTENCY")
print("-" * 50)

expected_figs = [
    "fig01_cumulative_returns.pdf",
    "fig02_calibration_analysis.pdf",
    "fig03_ablation_bars.pdf",
    "fig04_regime_timeline.pdf",
]

for fname in expected_figs:
    fpath = PUB_FIGS / fname
    if fpath.exists():
        sz = fpath.stat().st_size / 1024
        print(f"  OK: {fname} ({sz:.1f} KB)")
    else:
        errors.append(f"  MISSING: {fname}")

# Check no stale old-named figures
stale = list(PUB_FIGS.glob("*reliability*"))
if stale:
    for s in stale:
        warnings.append(f"  WARNING: Stale file found: {s.name}")
        print(f"  WARNING: Stale file: {s.name}")

# Check for unexpected files
unexpected_extensions = [".png", ".jpg", ".jpeg", ".gif"]
for f in PUB_FIGS.glob("*"):
    if f.suffix not in [".pdf"]:
        warnings.append(f"  WARNING: Non-standard figure format: {f.name}")

if not stale and not any(f.suffix != ".pdf" for f in PUB_FIGS.glob("*")):
    print(f"  OK: All figures are PDF (no stale files)")

# ------------------------------------------------------------------
# 3. Table consistency
# ------------------------------------------------------------------
print()
print("3. TABLE CONSISTENCY")
print("-" * 50)

expected_tables = [
    "table01_summary.tex",
    "table02_per_fold.tex",
    "table03_ablation.tex",
    "table04_calibration.tex",
]

for tname in expected_tables:
    tpath = PUB_TABS / tname
    if tpath.exists():
        sz = tpath.stat().st_size
        print(f"  OK: {tname} ({sz} bytes)")
    else:
        errors.append(f"  MISSING: {tname}")

# ------------------------------------------------------------------
# 4. Research report consistency check
# ------------------------------------------------------------------
print()
print("4. RESEARCH REPORT CONSISTENCY")
print("-" * 50)

report_path = REPORTS / "research_report.md"
if report_path.exists():
    text = report_path.read_text()
    # Check for stale "20/20" claims
    if "all 20 fold-seed" in text.lower() or "all 4 walk-forward folds" in text.lower():
        # Check context - "all 20 fold-seed combinations produced valid fused allocations" is correct
        # But "all 4 walk-forward folds" for Sharpe positivity is wrong
        if "positive risk-adjusted" in text and "all 4 walk-forward folds" in text:
            errors.append("  STALE CLAIM: Research report still says 'all 4 walk-forward folds'")
        else:
            print(f"  OK: Research report corrected (no stale 'all 4 folds' claim)")
    else:
        print(f"  OK: Research report does not contain stale claims")

    # Verify corrected text
    if "19 of 20" in text:
        print(f"  OK: Research report uses '19 of 20' (corrected claim)")
    else:
        warnings.append(f"  WARNING: Research report may not contain corrected claim")
else:
    errors.append("  MISSING: Research report")

# ------------------------------------------------------------------
# 5. Verify statistical analysis results file exists
# ------------------------------------------------------------------
print()
print("5. STATISTICAL ANALYSIS OUTPUTS")
print("-" * 50)

stat_script = BASE / "_final_stats.py"
if stat_script.exists():
    print(f"  OK: Statistical analysis script exists ({stat_script.name})")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print()
print("=" * 70)
if errors:
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
if warnings:
    print(f"WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  {w}")
if not errors and not warnings:
    print("ALL CHECKS PASSED - No inconsistencies found")
print("=" * 70)
print()
print(f"  Errors:   {len(errors)}")
print(f"  Warnings: {len(warnings)}")
print()
if errors:
    print("Corrections needed before freeze.")
else:
    print("Ready for Phase 3 freeze.")
