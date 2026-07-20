"""Experiment-level pipeline wrapper with timestamp injection.

Replicates the CA-MARL inference flow but patches AgentOutput timestamps
to match historical data indices — a permitted experiment workaround for
the known issue documented in IMPLEMENTATION_FREEZE.md §Known Minor Issues.

Does NOT modify any architecture code. Uses only public APIs and contracts.
"""

import logging
from copy import deepcopy
from typing import Any

import pandas as pd

from finrl.agents.ca_marl.config_schema import (
    AgentHyperparameters,
    ConfidenceConfig,
    PPOConfig,
    RiskManagementConfig,
)
from finrl.agents.ca_marl.confidence_engine import (
    ConfidenceEngine,
    OutcomeLabelGenerator,
)
from finrl.agents.ca_marl.confidence_fusion import ConfidenceAwareFusion
from finrl.agents.ca_marl.contracts import (
    AgentOutput,
    EvaluationReport,
    FinalRecommendation,
    FusedDecision,
)
from finrl.agents.ca_marl.evaluation import EvaluationEngine
from finrl.agents.ca_marl.pipeline import build_agents
from finrl.agents.ca_marl.risk_management import RiskManagementLayer

logger = logging.getLogger(__name__)


def _patch_timestamps(
    agent_outputs: list[AgentOutput],
    price_index: pd.DatetimeIndex,
) -> list[AgentOutput]:
    """Patch AgentOutput timestamps to align with the price index.

    Replaces ``pd.Timestamp.now()`` (set by the agent's ``predict``) with
    the last timestamp from the price index, enabling historical evaluation.
    """
    ts = price_index[-1]
    for ao in agent_outputs:
        object.__setattr__(ao, "timestamp", ts)
    return agent_outputs


def train_and_infer(
    train_features: pd.DataFrame,
    train_forward_returns: pd.DataFrame,
    test_features: pd.DataFrame,
    test_realized_prices: pd.DataFrame,
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    ppo_config: PPOConfig,
    confidence_config: ConfidenceConfig,
    risk_config: RiskManagementConfig,
    total_timesteps: int = 5000,
    prediction_consistency_k: int = 5,
    calib_pairs: list[tuple[str, float, float]] | None = None,
    outcome_label_gen: OutcomeLabelGenerator | None = None,
    eval_realized_prices: pd.DataFrame | None = None,
    val_features: pd.DataFrame | None = None,
    val_realized_prices: pd.DataFrame | None = None,
    calib_engine: ConfidenceEngine | None = None,
) -> dict[str, Any]:
    """Train agents, run inference with timestamp patching, and evaluate.

    This is the experiment-layer equivalent of ``pipeline.run_pipeline``
    but with correct historical timestamps injected after ``predict()``.

    Args:
        train_features: training feature DataFrame.
        train_forward_returns: training forward returns.
        test_features: inference feature DataFrame.
        test_realized_prices: realized prices for the test window (used
            for portfolio return computation).
        universe: asset tickers.
        agent_configs: per-agent hyperparameters.
        ppo_config: PPO hyperparameters.
        confidence_config: confidence estimation parameters.
        risk_config: risk management parameters.
        total_timesteps: PPO training timesteps per agent.
        prediction_consistency_k: k for prediction consistency.
        calib_pairs: optional calibration training data.
        outcome_label_gen: optional OutcomeLabelGenerator.
        eval_realized_prices: extended realized prices covering the label
            horizon beyond the test window for calibration evaluation.
            If ``None``, ``test_realized_prices`` is used (calibration
            metrics will be empty for the final window).

    Returns:
        Dict with keys: final_recommendation, evaluation_report,
        agent_outputs, calibrated_confidences, fused_decision.
    """
    eval_prices = (
        eval_realized_prices if eval_realized_prices is not None
        else test_realized_prices
    )
    # --- Train ---
    trained = build_agents(
        train_features, train_forward_returns, universe,
        agent_configs, ppo_config,
        total_timesteps=total_timesteps,
    )

    # --- Predict on validation window (for calibration pair collection) ---
    val_agent_outputs: list[AgentOutput] | None = None
    if val_features is not None:
        val_market_out = trained["market_agent"].predict(val_features)
        val_risk_out = trained["risk_agent"].predict(val_features)
        val_alloc_out = trained["allocation_agent"].predict(val_features)
        val_agent_outputs = [val_market_out, val_risk_out, val_alloc_out]
        if val_realized_prices is not None:
            val_agent_outputs = _patch_timestamps(val_agent_outputs, val_realized_prices.index)

    # --- Predict ---
    market_agent = trained["market_agent"]
    risk_agent = trained["risk_agent"]
    alloc_agent = trained["allocation_agent"]

    market_out = market_agent.predict(test_features)
    risk_out = risk_agent.predict(test_features)
    alloc_out = alloc_agent.predict(test_features)
    agent_outputs = [market_out, risk_out, alloc_out]

    # --- Patch timestamps (known issue workaround) ---
    agent_outputs = _patch_timestamps(agent_outputs, test_realized_prices.index)

    # --- Prediction consistency ---
    pcs = {
        "market_agent": market_agent.prediction_consistency(
            test_features, prediction_consistency_k
        ),
        "risk_agent": risk_agent.prediction_consistency(
            test_features, prediction_consistency_k
        ),
        "allocation_agent": alloc_agent.prediction_consistency(
            test_features, prediction_consistency_k
        ),
    }

    # --- Confidence estimation ---
    if outcome_label_gen is None:
        outcome_label_gen = OutcomeLabelGenerator(agent_configs)
    if calib_engine is None:
        calib_engine = ConfidenceEngine(outcome_label_gen, confidence_config)
    raw_confs = calib_engine.estimate_raw_confidence(agent_outputs, pcs)

    calib_engine.fit_calibration(calib_pairs or [])
    calibrated = calib_engine.calibrate(raw_confs)

    # --- Fusion ---
    fusion = ConfidenceAwareFusion(agent_configs=agent_configs)
    fused: FusedDecision = fusion.fuse(agent_outputs, calibrated, universe)

    # --- Risk management ---
    risk_mgr = RiskManagementLayer(risk_config)
    final_rec: FinalRecommendation = risk_mgr.apply(fused)

    # --- Evaluation ---
    eval_engine = EvaluationEngine(outcome_label_gen)
    fm = eval_engine.evaluate_with_assets([final_rec], test_realized_prices)
    calib_metrics = eval_engine.evaluate_calibration(
        list(calibrated.values()), agent_outputs, eval_prices,
    )
    eval_report = eval_engine.generate_report(
        financial=fm,
        calibration=calib_metrics,
        fold_id="experiment",
    )

    return {
        "final_recommendation": final_rec,
        "evaluation_report": eval_report,
        "agent_outputs": agent_outputs,
        "val_agent_outputs": val_agent_outputs,
        "calibrated_confidences": calibrated,
        "raw_confidences": raw_confs,
        "fused_decision": fused,
        "calib_engine": calib_engine,
    }
