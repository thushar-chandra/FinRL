"""Final verification of all experiment artifacts."""
import json, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("verify")

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
PLOTS = BASE / "plots"
PUB = PLOTS / "publication"
REPORTS = BASE / "reports"

n_ok = 0
n_err = 0

def check(desc, condition):
    global n_ok, n_err
    if condition:
        log.info("  ✓ %s", desc)
        n_ok += 1
    else:
        log.error("  ✗ %s", desc)
        n_err += 1

# ------------------------------------------------------------------
# 1. Dataset
# ------------------------------------------------------------------
log.info("=== Dataset ===")
ds = BASE / "dataset"
check("metadata.json exists", (ds / "metadata.json").exists())
meta = json.loads((ds / "metadata.json").read_text()) if (ds / "metadata.json").exists() else {}
check(f"version {meta.get('dataset_version', 'N/A')}", meta.get("dataset_version") == "v1.0.0")
check("features.pkl exists", (ds / f"features_{meta.get('dataset_version', 'v1.0.0')}.pkl").exists())
check("prices.pkl exists", (ds / f"realized_prices_{meta.get('dataset_version', 'v1.0.0')}.pkl").exists())
check("universe.json exists", (ds / "universe.json").exists())
univ = json.loads((ds / "universe.json").read_text()) if (ds / "universe.json").exists() else []
check(f"universe has {len(univ)} tickers", len(univ) == 19)

# ------------------------------------------------------------------
# 2. Campaign results (5 seeds)
# ------------------------------------------------------------------
log.info("=== Campaign Results ===")
seed_files = sorted(RESULTS.glob("campaign_v1_seed_*.json"))
check(f"{len(seed_files)} seed result files", len(seed_files) == 5)
for sf in seed_files:
    data = json.loads(sf.read_text())
    check(f"{sf.name}: {len(data.get('folds', []))} folds, has aggregated metrics",
          len(data.get("folds", [])) == 4 and "aggregated" in data)
    # Verify baseline data
    bm = data.get("baselines", {})
    for bn in ["equal_weight", "buy_and_hold", "static_mvo"]:
        check(f"{sf.name}: baseline {bn} present", bn in bm)

# ------------------------------------------------------------------
# 3. Ablation results
# ------------------------------------------------------------------
log.info("=== Ablation Results ===")
ab_file = RESULTS / f"campaign_v1_ablations_seed_0000.json"
check("Ablation file exists", ab_file.exists())
ab_data = json.loads(ab_file.read_text())
expected_ablations = {"campaign_v1", "equal_weight_fusion", "no_calibration",
                      "shuffled_confidence", "drop_market_agent",
                      "drop_risk_agent", "drop_allocation_agent"}
existing = set(ab_data.keys())
check(f"All ablations present ({len(existing)}/{len(expected_ablations)})",
      expected_ablations.issubset(existing))
for name, ab in ab_data.items():
    fm = ab.get("financial_metrics", {})
    has_sharpe = "sharpe_ratio" in fm
    check(f"  {name}: has financial_metrics", has_sharpe)

# ------------------------------------------------------------------
# 4. Publication figures
# ------------------------------------------------------------------
log.info("=== Publication Figures ===")
expected_figs = ["fig01_cumulative_returns.pdf", "fig02_reliability_diagrams.pdf",
                 "fig03_ablation_bars.pdf", "fig04_regime_timeline.pdf"]
for fname in expected_figs:
    fpath = PUB / "figures" / fname
    check(f"{fname} exists ({fpath.stat().st_size/1024:.1f} KB)" if fpath.exists() else f"{fname} exists",
          fpath.exists())

# ------------------------------------------------------------------
# 5. Publication tables
# ------------------------------------------------------------------
log.info("=== Publication Tables ===")
expected_tables = ["table01_summary.tex", "table02_per_fold.tex",
                   "table03_ablation.tex", "table04_calibration.tex"]
for tname in expected_tables:
    tpath = PUB / "tables" / tname
    check(f"{tname} exists ({tpath.stat().st_size} bytes)" if tpath.exists() else f"{tname} exists",
          tpath.exists())

# ------------------------------------------------------------------
# 6. Research report
# ------------------------------------------------------------------
log.info("=== Research Report ===")
report = REPORTS / "research_report.md"
check("research_report.md exists", report.exists())
if report.exists():
    text = report.read_text()
    sections = [l for l in text.split("\n") if l.startswith("##")]
    check(f"Report has {len(sections)} sections", len(sections) >= 5)

# ------------------------------------------------------------------
# 7. Existing plots
# ------------------------------------------------------------------
log.info("=== Existing Plots ===")
existing_plots = list(PLOTS.glob("*.png")) + list(PLOTS.glob("*.csv"))
check(f"{len(existing_plots)} existing plots/tables", len(existing_plots) >= 6)

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print()
print("=" * 60)
print(f"VERIFICATION COMPLETE: {n_ok} passed, {n_err} failed")
print("=" * 60)
if n_err > 0:
    print("WARNING: Some checks failed. Review errors above.")
else:
    print("All artifacts verified successfully.")

# ------------------------------------------------------------------
# Artifact manifest
# ------------------------------------------------------------------
manifest = {
    "campaign": {
        "id": "campaign_v1",
        "seeds": [42, 43, 44, 45, 46],
        "folds": 4,
        "dataset_version": "v1.0.0",
        "n_timesteps": 1111,
        "n_assets": 19,
        "total_timesteps_per_agent": 5000,
    },
    "artifacts": {
        "figures": [str(f.relative_to(BASE)) for f in (PUB / "figures").glob("*")],
        "tables": [str(f.relative_to(BASE)) for f in (PUB / "tables").glob("*")],
        "existing_plots": [str(f.relative_to(BASE)) for f in existing_plots],
        "results": [str(f.relative_to(BASE)) for f in seed_files],
        "reports": [str(report.relative_to(BASE))],
    },
    "verification": {
        "n_passed": n_ok,
        "n_failed": n_err,
    },
}

manifest_path = REPORTS / "artifact_manifest.json"
REPORTS.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, indent=2))
log.info("Manifest saved: %s", manifest_path)
