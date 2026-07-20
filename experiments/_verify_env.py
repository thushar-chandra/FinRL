"""Quick environment verification."""
import logging
import sys
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger('verify')

from experiments._data_cache import get_cached_dataset, dataset_info
from experiments._utils import RESULTS_DIR, PLOTS_DIR, find_all_results
from experiments._config import DEFAULT_WALK_FORWARD, build_fold_schedules

# Dataset
info = dataset_info()
logger.info('Dataset info: %s', info.get('dataset_version', 'unknown'))

data = get_cached_dataset()
logger.info('Features: %s', data['features'].shape)
logger.info('Prices: %s', data['realized_prices'].shape)
logger.info('Universe: %d tickers', len(data['universe']))
logger.info('Date range: %s to %s',
            data['realized_prices'].index[0],
            data['realized_prices'].index[-1])

# Folds
schedules = build_fold_schedules(len(data['features']), DEFAULT_WALK_FORWARD)
logger.info('Walk-forward: %d folds', len(schedules))
for i, s in enumerate(schedules):
    logger.info('  Fold %d: train=[%d:%d] val=[%d:%d] test=[%d:%d]',
                i+1, s.train_start, s.train_end,
                s.val_start, s.val_end,
                s.test_start, s.test_end)

# Results
cam_files = sorted(RESULTS_DIR.glob('campaign_v1_seed_*.json'))
logger.info('Campaign result files: %d', len(cam_files))
for f in cam_files:
    import json
    d = json.loads(f.read_text())
    agg = d.get('aggregated', {})
    sr = agg.get('sharpe_ratio', {}).get('mean', 'N/A')
    cr = agg.get('cumulative_return', {}).get('mean', 'N/A')
    nf = len(d.get('folds', []))
    logger.info('  %s: Sharpe=%s, CumRet=%s, folds=%d', f.name, sr, cr, nf)

# Plots
plots = sorted(PLOTS_DIR.glob('*'))
logger.info('Generated plots/tables: %d', len(plots))
for p in plots:
    sz = p.stat().st_size / 1024
    logger.info('  %s (%.1f KB)', p.name, sz)

print()
print('Environment verification complete.')
print(f'  Results dir: {RESULTS_DIR}')
print(f'  Plots dir:   {PLOTS_DIR}')
print(f'  Dataset:     {info.get("dataset_version", "N/A")}')
print(f'  Campaign results: {len(cam_files)} seeds, {len(schedules)} folds')
print(f'  Plots/tables: {len(plots)} files')
