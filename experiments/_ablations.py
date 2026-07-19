"""Ablation studies for CA-MARL (EXPERIMENT_PLAN.md §Ablation Studies).

Implements all four mandatory ablations:
  1. equal_weight_fusion  — set all confidence weights equal before fusion
  2. no_calibration       — skip Platt/temperature scaling, use raw confidence
  3. shuffled_confidence  — shuffle calibrated confidences across agents
  4. drop_one_agent       — remove one agent at a time

None of these modify the architecture.  They manipulate inputs to the
deterministic fusion formula or the inference pipeline call.
"""

import logging
from typing import Any

import numpy as np

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
    CalibratedConfidence,
    FinalRecommendation,
    FusedDecision,
)
from finrl.agents.ca_marl.evaluation import EvaluationEngine
from finrl.agents.ca_marl.risk_management import RiskManagementLayer

logger = logging.getLogger(__name__)

_AGENT_NAMES = ["market_agent", "risk_agent", "allocation_agent"]


def run_equal_weight_fusion(
    agent_outputs: list[AgentOutput],
    calibrated_confidences: dict[str, CalibratedConfidence],
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    risk_config: RiskManagementConfig,
    eval_engine: EvaluationEngine,
    realized_prices: Any,
) -> dict[str, Any]:
    """Ablation 1: override all calibrated confidences to equal weight.

    This isolates the value of confidence-aware weighting: if confidence-aware
    fusion degrades to equal-weight when all confidences are equal, the
    performance delta measures the contribution of non-uniform weighting.
    """
    eq_confidences = {
        name: CalibratedConfidence(
            agent_name=name,
            calibrated_confidence=1.0 / len(calibrated_confidences),
            diagnostics=cc.diagnostics,
            timestamp=cc.timestamp,
        )
        for name, cc in calibrated_confidences.items()
    }
    return _run_fusion_and_eval(
        agent_outputs, eq_confidences, universe,
        agent_configs, risk_config, eval_engine, realized_prices,
    )


def run_no_calibration(
    agent_outputs: list[AgentOutput],
    calibrated_confidences: dict[str, CalibratedConfidence],
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    risk_config: RiskManagementConfig,
    eval_engine: EvaluationEngine,
    realized_prices: Any,
    raw_confidences: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Ablation 2: use raw confidence values instead of calibrated.

    Isolates the value of the calibration step specifically.

    Uses ``raw_confidences`` (computed by ``ConfidenceEngine``) when
    provided; otherwise falls back to ``AgentOutput.raw_confidence``
    (which is a placeholder value).
    """
    if raw_confidences is None:
        raw_confidences = {ao.agent_name: ao.raw_confidence for ao in agent_outputs}
    raw_conf_objects = {
        name: CalibratedConfidence(
            agent_name=name,
            calibrated_confidence=conf,
            diagnostics={},
            timestamp=agent_outputs[0].timestamp,
        )
        for name, conf in raw_confidences.items()
    }
    return _run_fusion_and_eval(
        agent_outputs, raw_conf_objects, universe,
        agent_configs, risk_config, eval_engine, realized_prices,
    )


def run_shuffled_confidence(
    agent_outputs: list[AgentOutput],
    calibrated_confidences: dict[str, CalibratedConfidence],
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    risk_config: RiskManagementConfig,
    eval_engine: EvaluationEngine,
    realized_prices: Any,
    seed: int = 42,
) -> dict[str, Any]:
    """Ablation 3: shuffle calibrated confidences across agents.

    If performance is statistically indistinguishable from real-confidence
    fusion, confidence is not functionally load-bearing.

    This does NOT require retraining — fusion is deterministic, so we
    just reassign confidence values.
    """
    rng = np.random.default_rng(seed)
    names = list(calibrated_confidences.keys())
    conf_values = [calibrated_confidences[n].calibrated_confidence for n in names]
    rng.shuffle(conf_values)

    shuffled = {
        name: CalibratedConfidence(
            agent_name=name,
            calibrated_confidence=conf_values[i],
            diagnostics=calibrated_confidences[name].diagnostics,
            timestamp=calibrated_confidences[name].timestamp,
        )
        for i, name in enumerate(names)
    }
    return _run_fusion_and_eval(
        agent_outputs, shuffled, universe,
        agent_configs, risk_config, eval_engine, realized_prices,
    )


def run_drop_one_agent(
    agent_outputs: list[AgentOutput],
    calibrated_confidences: dict[str, CalibratedConfidence],
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    risk_config: RiskManagementConfig,
    eval_engine: EvaluationEngine,
    realized_prices: Any,
    drop_agent: str = "",
) -> dict[str, Any]:
    """Ablation 4: drop one agent, measure performance delta.

    The fusion module requires exactly 3 agent outputs (ADR-020), so we
    cannot remove an agent. Instead, we set its calibrated confidence to 0,
    which gives it zero weight in the confidence-weighted fusion formula.

    Args:
        drop_agent: which agent to drop ("market_agent", "risk_agent",
            or "allocation_agent").

    Returns metrics without that agent's contribution.
    """
    dropped = {
        name: CalibratedConfidence(
            agent_name=name,
            calibrated_confidence=0.0,
            diagnostics=cc.diagnostics,
            timestamp=cc.timestamp,
        )
        if name == drop_agent else cc
        for name, cc in calibrated_confidences.items()
    }

    return _run_fusion_and_eval(
        agent_outputs, dropped, universe,
        agent_configs, risk_config, eval_engine, realized_prices,
    )


# ---------------------------------------------------------------------------
# Shared internal helper
# ---------------------------------------------------------------------------


def _run_fusion_and_eval(
    agent_outputs: list[AgentOutput],
    calibrated_confidences: dict[str, CalibratedConfidence],
    universe: list[str],
    agent_configs: dict[str, AgentHyperparameters],
    risk_config: RiskManagementConfig,
    eval_engine: EvaluationEngine,
    realized_prices: Any,
) -> dict[str, Any]:
    """Run fusion + risk management + evaluation for an ablation variant."""
    fusion = ConfidenceAwareFusion(agent_configs=agent_configs)
    fused = fusion.fuse(agent_outputs, calibrated_confidences, universe)

    risk_mgr = RiskManagementLayer(risk_config)
    final: FinalRecommendation = risk_mgr.apply(fused)

    fm = eval_engine.evaluate_with_assets([final], realized_prices)
    calib = eval_engine.evaluate_calibration(
        list(calibrated_confidences.values()),
        agent_outputs,
        realized_prices,
    )

    return {
        "financial_metrics": {
            "sharpe_ratio": fm.sharpe_ratio,
            "sortino_ratio": fm.sortino_ratio,
            "max_drawdown": fm.max_drawdown,
            "volatility": fm.volatility,
            "cumulative_return": fm.cumulative_return,
        },
        "calibration_metrics": {
            name: {"ece": cm.ece, "brier_score": cm.brier_score}
            for name, cm in calib.items()
        },
        "allocation": dict(final.allocation),
        "fallback_used": fused.fusion_metadata.get("fallback_used", False),
    }
