"""Final Phase 3 deliverable checks."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CHK = {}

# 1. Dataset
ds = BASE / "dataset"
CHK["dataset_metadata"] = (ds / "metadata.json").exists()
if CHK["dataset_metadata"]:
    meta = json.loads((ds / "metadata.json").read_text())
    CHK["dataset_version"] = meta.get("dataset_version") == "v1.0.0"
    CHK["dataset_features"] = (ds / f"features_{meta['dataset_version']}.pkl").exists()
    CHK["dataset_prices"] = (ds / f"realized_prices_{meta['dataset_version']}.pkl").exists()
    CHK["dataset_universe"] = (ds / "universe.json").exists()
    univ = json.loads((ds / "universe.json").read_text())
    CHK["dataset_universe_size"] = len(univ) == 19

# 2. Campaign results
res = BASE / "results"
seed_files = sorted(res.glob("campaign_v1_seed_*.json"))
CHK["campaign_n_seeds"] = len(seed_files) == 5
all_ok = True
all_4folds = True
for f in seed_files:
    d = json.loads(f.read_text())
    nf = len(d.get("folds", []))
    has_agg = "aggregated" in d
    has_baselines = bool(d.get("baselines"))
    if nf != 4:
        all_4folds = False
    if not (has_agg and has_baselines):
        all_ok = False
CHK["campaign_all_4folds"] = all_4folds
CHK["campaign_all_complete"] = all_ok

# 3. Ablations
chk_ab = (res / "campaign_v1_ablations_seed_0000.json").exists()
if chk_ab:
    ab = json.loads((res / "campaign_v1_ablations_seed_0000.json").read_text())
    expected = {"campaign_v1", "equal_weight_fusion", "no_calibration",
                "shuffled_confidence", "drop_market_agent",
                "drop_risk_agent", "drop_allocation_agent"}
    CHK["ablations_exist"] = chk_ab
    CHK["ablations_all_present"] = expected.issubset(set(ab.keys()))

# 4. Publication figures
fig_dir = BASE / "plots" / "publication" / "figures"
figs = sorted(fig_dir.glob("*.pdf"))
expected_figs = ["fig01_cumulative_returns.pdf", "fig02_reliability_diagrams.pdf",
                 "fig03_ablation_bars.pdf", "fig04_regime_timeline.pdf"]
CHK["pub_figures_all"] = all((fig_dir / f).exists() for f in expected_figs)
CHK["pub_figures_count"] = len(figs)

# 5. Publication tables
tab_dir = BASE / "plots" / "publication" / "tables"
tables = sorted(tab_dir.glob("*.tex"))
expected_tables = ["table01_summary.tex", "table02_per_fold.tex",
                   "table03_ablation.tex", "table04_calibration.tex"]
CHK["pub_tables_all"] = all((tab_dir / f).exists() for f in expected_tables)
CHK["pub_tables_count"] = len(tables)

# 6. Reports
CHK["report_research"] = (BASE / "reports" / "research_report.md").exists()
CHK["report_manifest"] = (BASE / "reports" / "artifact_manifest.json").exists()
CHK["report_reproducibility"] = (BASE / "reproducibility_manifest.json").exists()

# 7. Verification
CHK["verify_dynamic_log"] = (BASE / "dynamic_verify_log.txt").exists()
CHK["verify_dynamic_report"] = (BASE / "dynamic_verify_report.txt").exists()

# 8. Existing plots
existing = list((BASE / "plots").glob("*.png"))
CHK["existing_plots"] = len(existing) >= 4

# Print results
print("=" * 60)
print("PHASE 3 DELIVERABLE CHECKLIST")
print("=" * 60)
ok = 0
total = 0
for k in sorted(CHK.keys()):
    total += 1
    v = CHK[k]
    mark = "+" if v else "!"
    if v:
        ok += 1
    print(f"  [{mark}] {k}: {v}")

print()
print(f"  Passed: {ok}/{total}")
if ok == total:
    print("  RESULT: ALL DELIVERABLES PRESENT")
else:
    missing = [k for k, v in CHK.items() if not v]
    print(f"  MISSING: {missing}")

# Summary
print()
d42 = json.loads((res / "campaign_v1_seed_0042.json").read_text())
print("EXPERIMENT SUMMARY:")
print(f"  Seeds: 42-46 (5 total)")
print(f"  Folds: 4 (walk-forward, 504/63/126 day windows)")
print(f"  Assets: {d42['n_assets']} ({d42['n_timesteps']} timesteps)")
print(f"  PPO timesteps per agent: {d42['config']['ppo']['total_timesteps']}")
print(f"  Calibration: {d42['config']['confidence']['calibration_method']}")
print(f"  Baselines: {list(d42['baselines'].keys())}")
print(f"  CA-MARL mean Sharpe (5 seeds): {sum(json.loads(f.read_text())['aggregated']['sharpe_ratio']['mean'] for f in seed_files)/len(seed_files):.4f}")
print(f"  Equal-weight Sharpe: {d42['baselines']['equal_weight']['sharpe_ratio']:.4f}")

print()
print("Phase 3 deliverable check complete.")
