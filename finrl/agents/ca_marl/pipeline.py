"""CA-MARL Pipeline Orchestrator — minimal end-to-end runner.

Connects all implemented modules into a single execution sequence:

    Feature Data → Agents → ConfidenceEngine → ConfidenceAwareFusion
    → RiskManagementLayer → EvaluationEngine

No training loop, no walk-forward validation, no optimisation — this is
the minimal proof that every module can execute together.

Reference: docs/architecture/SYSTEM_WORKFLOW.md,
docs/architecture/ARCHITECTURE.md §4 (Execution Flow).
"""

import logging
from typing import Any

import pandas as pd

from finrl.agents.ca_marl.allocation_agent import PortfolioAllocationAgent
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
    EvaluationReport,
)
from finrl.agents.ca_marl.evaluation import EvaluationEngine
from finrl.agents.ca_marl.market_agent import MarketAnalysisAgent
from finrl.agents.ca_marl.risk_agent import RiskAssessmentAgent
from finrl.agents.ca_marl.risk_management import RiskManagementLayer

logger = logging.getLogger(__name__)


def build_agents(
    features: pd.DataFrame,
    forward_returns: pd.DataFrame,
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    ppo_config: PPOConfig,
    total_timesteps: int = 2000,
) -> dict[str, Any]:
    """Train all three specialised RL agents.

    Args:
        features: engineered feature DataFrame ``(T, n_features)``.
        forward_returns: per-asset one-step forward returns ``(T, n_assets)``.
        universe: list of asset tickers.
        agent_configs: per-agent hyperparameters (keys: ``"market_agent"``,
            ``"risk_agent"``, ``"allocation_agent"``).
        ppo_config: PPO hyperparameters (required — not optional).
        total_timesteps: PPO training timesteps per agent.

    Returns:
        A dict with keys ``"market_agent"``, ``"risk_agent"``,
        ``"allocation_agent"`` mapping to trained agent instances.
    """
    feature_columns = list(features.columns)

    logger.info("Training Market Agent...")
    market_agent = MarketAnalysisAgent(
        feature_columns, universe, agent_configs["market_agent"], ppo_config,
    )
    market_agent.train(features, forward_returns, total_timesteps=total_timesteps)

    logger.info("Training Risk Agent...")
    risk_agent = RiskAssessmentAgent(
        feature_columns, universe, agent_configs["risk_agent"], ppo_config,
    )
    risk_agent.train(features, forward_returns, total_timesteps=total_timesteps)

    logger.info("Training Allocation Agent...")
    alloc_agent = PortfolioAllocationAgent(
        feature_columns, universe, agent_configs["allocation_agent"], ppo_config,
    )
    alloc_agent.train(features, forward_returns, total_timesteps=total_timesteps)

    return {
        "market_agent": market_agent,
        "risk_agent": risk_agent,
        "allocation_agent": alloc_agent,
    }


def run_inference(
    trained_agents: dict[str, Any],
    features: pd.DataFrame,
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    confidence_config: ConfidenceConfig,
    risk_config: RiskManagementConfig,
    outcome_label_gen: OutcomeLabelGenerator | None = None,
    prediction_consistency_k: int = 5,
    calibration_training_data: list[tuple[str, float, float]] | None = None,
    realized_prices: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Run inference, fusion, risk management, and optional evaluation.

    Args:
        trained_agents: dict with keys ``"market_agent"``, ``"risk_agent"``,
            ``"allocation_agent"`` from ``build_agents``.
        features: engineered feature DataFrame ``(T, n_features)``.
        universe: list of asset tickers.
        agent_configs: per-agent hyperparameters.
        confidence_config: confidence estimation parameters.
        risk_config: risk management parameters.
        outcome_label_gen: optional ``OutcomeLabelGenerator`` instance. If
            ``None``, a new one is created. Pass the same instance across
            multiple calls to accumulate label history (walk-forward).
        prediction_consistency_k: number of nearby states to sample for
            prediction consistency (ADR-023).
        calibration_training_data: optional list of ``(agent_name, raw_conf,
            label)`` tuples for fitting calibration.
        realized_prices: optional DataFrame with ``DatetimeIndex`` and ticker
            columns for evaluation. If ``None``, evaluation is skipped.

    Returns:
        A dict with keys:
            - ``"final_recommendation"``: ``FinalRecommendation``
            - ``"evaluation_report"``: ``EvaluationReport`` or ``None``
            - ``"agent_outputs"``: ``list[AgentOutput]``
            - ``"calibrated_confidences"``: ``dict[str, CalibratedConfidence]``
            - ``"fused_decision"``: ``FusedDecision``
    """
    market_agent = trained_agents["market_agent"]
    risk_agent = trained_agents["risk_agent"]
    alloc_agent = trained_agents["allocation_agent"]

    # ------------------------------------------------------------------
    # Phase 1: Predict
    # ------------------------------------------------------------------
    logger.info("Running inference...")
    market_out = market_agent.predict(features)
    risk_out = risk_agent.predict(features)
    alloc_out = alloc_agent.predict(features)
    agent_outputs = [market_out, risk_out, alloc_out]

    # --- Prediction consistency ---
    pcs = {
        "market_agent": market_agent.prediction_consistency(
            features, prediction_consistency_k
        ),
        "risk_agent": risk_agent.prediction_consistency(
            features, prediction_consistency_k
        ),
        "allocation_agent": alloc_agent.prediction_consistency(
            features, prediction_consistency_k
        ),
    }

    # ------------------------------------------------------------------
    # Phase 2: Confidence Estimation & Calibration
    # ------------------------------------------------------------------
    logger.info("Estimating confidence...")
    if outcome_label_gen is None:
        outcome_label_gen = OutcomeLabelGenerator(agent_configs)
    engine = ConfidenceEngine(outcome_label_gen, confidence_config)

    raw_confs = engine.estimate_raw_confidence(agent_outputs, pcs)

    if calibration_training_data is not None:
        engine.fit_calibration(calibration_training_data)
    else:
        engine.fit_calibration([])

    calibrated = engine.calibrate(raw_confs)

    # ------------------------------------------------------------------
    # Phase 3: Fusion
    # ------------------------------------------------------------------
    logger.info("Fusing decisions...")
    fusion = ConfidenceAwareFusion(agent_configs=agent_configs)
    fused = fusion.fuse(agent_outputs, calibrated, universe)

    # ------------------------------------------------------------------
    # Phase 4: Risk Management
    # ------------------------------------------------------------------
    logger.info("Enforcing constraints...")
    risk_mgr = RiskManagementLayer(risk_config)
    final_rec = risk_mgr.apply(fused)

    # ------------------------------------------------------------------
    # Phase 5: Evaluation
    # ------------------------------------------------------------------
    logger.info("Evaluating...")
    eval_report: EvaluationReport | None = None
    if realized_prices is not None:
        eval_engine = EvaluationEngine(outcome_label_gen)
        fm = eval_engine.evaluate_with_assets(
            [final_rec], realized_prices,
        )
        calib_metrics = eval_engine.evaluate_calibration(
            list(calibrated.values()), agent_outputs, realized_prices,
        )
        eval_report = eval_engine.generate_report(
            financial=fm,
            calibration=calib_metrics,
            fold_id="single_run",
        )

    return {
        "final_recommendation": final_rec,
        "evaluation_report": eval_report,
        "agent_outputs": agent_outputs,
        "calibrated_confidences": calibrated,
        "fused_decision": fused,
    }


def run_pipeline(
    features: pd.DataFrame,
    forward_returns: pd.DataFrame,
    universe: list[str],
    realized_prices: pd.DataFrame | None = None,
    agent_configs: dict[str, AgentHyperparameters] | None = None,
    ppo_config: PPOConfig | None = None,
    confidence_config: ConfidenceConfig | None = None,
    risk_config: RiskManagementConfig | None = None,
    prediction_consistency_k: int = 5,
    calibration_training_data: list[tuple[str, float, float]] | None = None,
    total_timesteps: int = 2000,
    outcome_label_gen: OutcomeLabelGenerator | None = None,
) -> dict[str, Any]:
    """Convenience function: train agents then run inference (single call).

    For two-phase usage (build-time vs. run-time), call ``build_agents``
    and ``run_inference`` separately.

    Args:
        features: engineered feature DataFrame ``(T, n_features)``.
        forward_returns: per-asset one-step forward returns ``(T, n_assets)``.
        universe: list of asset tickers.
        realized_prices: optional DataFrame with ``DatetimeIndex`` and ticker
            columns for evaluation.
        agent_configs: per-agent hyperparameters. Required — no internal
            defaults.
        ppo_config: PPO hyperparameters. Required — no internal defaults.
        confidence_config: confidence estimation parameters. Required — no
            internal defaults.
        risk_config: risk management parameters. Required — no internal
            defaults.
        prediction_consistency_k: number of nearby states to sample for
            prediction consistency (ADR-023).
        calibration_training_data: optional list of ``(agent_name, raw_conf,
            label)`` tuples for fitting calibration.
        total_timesteps: PPO training timesteps per agent.
        outcome_label_gen: optional ``OutcomeLabelGenerator``. If ``None``,
            a new one is created.

    Returns:
        Same return dict as ``run_inference``.
    """
    if agent_configs is None or ppo_config is None or confidence_config is None or risk_config is None:
        raise ValueError(
            "agent_configs, ppo_config, confidence_config, and risk_config are required. "
            "See configs/*.yaml or config_schema.py for expected fields."
        )

    trained = build_agents(
        features, forward_returns, universe,
        agent_configs, ppo_config,
        total_timesteps=total_timesteps,
    )
    return run_inference(
        trained, features, universe,
        agent_configs, confidence_config, risk_config,
        outcome_label_gen=outcome_label_gen,
        prediction_consistency_k=prediction_consistency_k,
        calibration_training_data=calibration_training_data,
        realized_prices=realized_prices,
    )
