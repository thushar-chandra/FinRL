"""Shared experiment utilities — seeding, serialization, paths."""

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).resolve().parent / "results"
PLOTS_DIR = Path(__file__).resolve().parent / "plots"


def set_all_seeds(seed: int = 42) -> None:
    """Set random seeds across all libraries for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def seed_str(seed: int) -> str:
    return f"seed_{seed:04d}"


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def result_path(experiment_name: str, seed: int, fold_id: str = "") -> Path:
    """Return the JSON results path for an experiment run."""
    parts = [experiment_name, seed_str(seed)]
    if fold_id:
        parts.append(f"fold_{fold_id}")
    filename = "_".join(parts) + ".json"
    return RESULTS_DIR / filename


def serialize(obj: Any) -> Any:
    """Recursively convert an object to JSON-safe types."""
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(v) for v in obj]
    if isinstance(obj, tuple):
        return [serialize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "_asdict"):
        return serialize(obj._asdict())
    return obj


def save_results(results: dict[str, Any], path: Path) -> None:
    """Save experiment results as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(serialize(results), f, indent=2)
    logger.info("Results saved to %s", path)


def load_results(path: Path) -> dict[str, Any]:
    """Load experiment results from JSON."""
    with open(path) as f:
        return json.load(f)


def find_all_results(experiment_name: str) -> list[Path]:
    """List all result files for a given experiment name."""
    return sorted(RESULTS_DIR.glob(f"{experiment_name}_*.json"))


def make_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
        datefmt="%H:%M:%S",
    )


def patch_agent_timestamps(
    agent_outputs: list[Any],
    features: pd.DataFrame,
) -> list[Any]:
    """Patch AgentOutput timestamps to match feature index timestamps.

    Known issue: agents set ``timestamp = pd.Timestamp.now()``, which breaks
    ``OutcomeLabelGenerator`` when realised data is historical.  This is a
    permitted experimental workaround for the known issue documented in
    ``IMPLEMENTATION_FREEZE.md`` §Known Minor Issues.

    Does not modify agent code or architecture contracts — only post-processes
    outputs in the experiment layer.
    """
    if agent_outputs and hasattr(agent_outputs[0], "timestamp"):
        feature_ts = (
            features.index[-1]
            if isinstance(features.index, pd.DatetimeIndex)
            else pd.Timestamp.now()
        )
        for ao in agent_outputs:
            object.__setattr__(ao, "timestamp", feature_ts)
    return agent_outputs


def make_agent_predict_with_timestamp(agent: Any, reference_features: pd.DataFrame) -> Any:
    """Wrap an agent's predict method to inject correct historical timestamps.

    Features DataFrames constructed by ``data_adapter`` use ``reset_index(drop=True)``,
    so they have a RangeIndex, not a DatetimeIndex.  We capture the price-aligned
    timestamp from ``reference_features`` if it has a DatetimeIndex, otherwise fall
    back to ``pd.Timestamp.now()``.

    Returns the agent with predict patched. Does not modify the agent class.
    """
    original_predict = agent.predict

    ref_ts = (
        reference_features.index[-1]
        if isinstance(reference_features.index, pd.DatetimeIndex)
        else pd.Timestamp.now()
    )

    def patched_predict(features: pd.DataFrame) -> Any:
        output = original_predict(features)
        object.__setattr__(output, "timestamp", ref_ts)
        return output

    agent.predict = patched_predict
    return agent


def make_agent_predict_with_datetime(agent: Any, timestamp: pd.Timestamp) -> Any:
    """Patch an agent's predict to always return a specific timestamp.

    Use when the feature DataFrame does not carry a DatetimeIndex and you
    need to align agent outputs with a known chronological date.

    Does not modify the agent class.
    """
    original_predict = agent.predict

    def patched_predict(features: pd.DataFrame) -> Any:
        output = original_predict(features)
        object.__setattr__(output, "timestamp", timestamp)
        return output

    agent.predict = patched_predict
    return agent
