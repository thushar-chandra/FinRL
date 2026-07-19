"""Versioned immutable dataset cache for the CA-MARL experimental campaign.

Dataset is downloaded exactly once from Yahoo Finance, then saved as versioned
Parquet files. All subsequent experiments load from this cache, guaranteeing
all seeds and configurations use identical market data.

Usage:
    from experiments._data_cache import get_cached_dataset, freeze_dataset
    data = get_cached_dataset()  # loads or downloads + freezes
"""

import hashlib
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from experiments._config import DEFAULT_UNIVERSE, DATA_START, DATA_END

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent / "dataset"
DATASET_VERSION = "v1.0.0"
METADATA_FILE = CACHE_DIR / "metadata.json"
FEATURES_FILE = CACHE_DIR / f"features_{DATASET_VERSION}.pkl"
FORWARD_RETURNS_FILE = CACHE_DIR / f"forward_returns_{DATASET_VERSION}.pkl"
REALIZED_PRICES_FILE = CACHE_DIR / f"realized_prices_{DATASET_VERSION}.pkl"
UNIVERSE_FILE = CACHE_DIR / "universe.json"


def _checksum(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _write_metadata() -> None:
    """Persist dataset metadata to JSON."""
    meta = {
        "dataset_version": DATASET_VERSION,
        "download_timestamp": datetime.utcnow().isoformat(),
        "data_source": "Yahoo Finance (yfinance)",
        "ticker_universe": list(DEFAULT_UNIVERSE),
        "date_range": {"start": DATA_START, "end": DATA_END},
        "files": {
            "features": FEATURES_FILE.name,
            "forward_returns": FORWARD_RETURNS_FILE.name,
            "realized_prices": REALIZED_PRICES_FILE.name,
            "universe": UNIVERSE_FILE.name,
        },
        "checksums": {
            "features": _checksum(FEATURES_FILE),
            "forward_returns": _checksum(FORWARD_RETURNS_FILE),
            "realized_prices": _checksum(REALIZED_PRICES_FILE),
            "universe": _checksum(UNIVERSE_FILE),
        },
    }
    METADATA_FILE.write_text(json.dumps(meta, indent=2))
    logger.info("Dataset metadata written to %s", METADATA_FILE)
    logger.info("  Version: %s", DATASET_VERSION)
    logger.info("  Timestamp: %s", meta["download_timestamp"])
    logger.info("  Checksums: features=%s ...", meta["checksums"]["features"][:16])


def freeze_dataset() -> dict[str, Any]:
    """Download market data once and save as versioned Parquet files.

    Returns the same dict as ``download_and_prepare``.  Idempotent —
    subsequent calls reload from cache.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if METADATA_FILE.exists():
        logger.info("Dataset already frozen at %s", CACHE_DIR)
        return load_cached_dataset()

    logger.info(
        "Downloading and freezing dataset (version %s) ...",
        DATASET_VERSION,
    )

    from finrl.agents.ca_marl.data_adapter import download_and_prepare
    data = download_and_prepare(
        ticker_list=DEFAULT_UNIVERSE,
        start_date=DATA_START,
        end_date=DATA_END,
    )

    features: pd.DataFrame = data["features"]
    forward_returns: pd.DataFrame = data["forward_returns"]
    realized_prices: pd.DataFrame = data["realized_prices"]
    universe: list[str] = data["universe"]

    features.to_pickle(FEATURES_FILE)
    forward_returns.to_pickle(FORWARD_RETURNS_FILE)
    realized_prices.to_pickle(REALIZED_PRICES_FILE)
    UNIVERSE_FILE.write_text(json.dumps(universe, indent=2))

    _write_metadata()

    logger.info("Dataset frozen: %s", CACHE_DIR)
    logger.info("  Features:       %s (%s)", features.shape, FEATURES_FILE.name)
    logger.info("  Forward returns: %s", FORWARD_RETURNS_FILE.name)
    logger.info("  Prices:          %s", REALIZED_PRICES_FILE.name)
    logger.info("  Universe:        %d tickers", len(universe))

    return data


def load_cached_dataset() -> dict[str, Any]:
    """Load the frozen dataset from Parquet cache.

    Returns:
        Same dict shape as ``download_and_prepare``:
        ``{"features", "forward_returns", "realized_prices", "universe"}``.

    Raises:
        FileNotFoundError: if the dataset has not been frozen yet.
    """
    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            "Dataset not frozen. Run freeze_dataset() first."
        )

    meta = json.loads(METADATA_FILE.read_text())
    logger.info("Loading frozen dataset version %s", meta["dataset_version"])

    features = pd.read_pickle(CACHE_DIR / meta["files"]["features"])
    forward_returns = pd.read_pickle(CACHE_DIR / meta["files"]["forward_returns"])
    realized_prices = pd.read_pickle(CACHE_DIR / meta["files"]["realized_prices"])
    universe: list[str] = json.loads(UNIVERSE_FILE.read_text())

    return {
        "features": features,
        "forward_returns": forward_returns,
        "realized_prices": realized_prices,
        "universe": universe,
    }


def get_cached_dataset() -> dict[str, Any]:
    """Get the frozen dataset (download + freeze if first call).

    This is the main entry point for experiments.  Idempotent — subsequent
    calls load from cache.
    """
    if METADATA_FILE.exists():
        return load_cached_dataset()
    return freeze_dataset()


def dataset_info() -> dict[str, Any]:
    """Return dataset metadata as a dict (or None if not frozen)."""
    if not METADATA_FILE.exists():
        return {"status": "not_frozen"}
    return json.loads(METADATA_FILE.read_text())
