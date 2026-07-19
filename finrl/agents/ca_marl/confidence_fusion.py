"""Confidence-Aware Decision Fusion — the project's primary research contribution.

Deterministic, PPO-independent module (ADR-014, ADR-015) that transforms each
agent's heterogeneous recommendation into a common ``AssetWeightProposal``
representation and fuses them using calibrated confidence (ADR-020).

Reference: docs/architecture/CONFIDENCE_FUSION.md,
docs/architecture/MODULE_SPECIFICATIONS.md §5,
docs/architecture/AGENTS.md §5,
docs/architecture/INTERFACE_CONTRACTS.md §5.
"""

import logging
from datetime import datetime
from typing import Any

from finrl.agents.ca_marl.config_schema import AgentHyperparameters
from finrl.agents.ca_marl.contracts import (
    AgentOutput,
    AssetWeightProposal,
    CalibratedConfidence,
    FusedDecision,
)

logger = logging.getLogger(__name__)

_AGENT_MARKET = "market_agent"
_AGENT_RISK = "risk_agent"
_AGENT_ALLOCATION = "allocation_agent"

_EXPECTED_AGENTS = frozenset({_AGENT_MARKET, _AGENT_RISK, _AGENT_ALLOCATION})


class ConfidenceAwareFusion:
    """Deterministic, confidence-weighted decision fusion.

    Transforms each specialised agent's heterogeneous ``recommendation`` into
    a common ``AssetWeightProposal`` (per-asset weight vector, non-negative,
    sums to 1.0), then applies the fusion formula::

        final_allocation[asset] = (
            Σ_agent(proposal_agent[asset] * calibrated_confidence_agent)
        ) / Σ_agent(calibrated_confidence_agent)

    The result is guaranteed to sum to 1.0 across assets (ADR-020 proof).

    Never RL-trained, never PPO-based — fully deterministic and exhaustively
    unit-testable via golden-value tests (CONFIDENCE_FUSION.md §Testing).

    Inputs: ``AgentOutput`` from all three agents + ``dict[str, CalibratedConfidence]``.
    Outputs: ``FusedDecision`` (final_allocation, reasoning, confidence_summary,
    fusion_metadata).

    Reference: INTERFACE_CONTRACTS.md §5, CONFIDENCE_FUSION.md.
    """

    def __init__(
        self,
        agent_configs: dict[str, AgentHyperparameters] | None = None,
    ) -> None:
        """Initialise the fusion module.

        Args:
            agent_configs: optional mapping from agent name to its
                ``AgentHyperparameters``, used to resolve per-agent epsilon
                values for the risk-to-proposal transform. If ``None``,
                defaults are used (epsilon=1e-6).
        """
        self._agent_configs = (
            dict(agent_configs) if agent_configs is not None else {}
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fuse(
        self,
        agent_outputs: list[AgentOutput],
        calibrated_confidences: dict[str, CalibratedConfidence],
        universe: list[str],
    ) -> FusedDecision:
        """Fuse three agent recommendations into a single portfolio allocation.

        Args:
            agent_outputs: one ``AgentOutput`` per agent (market, risk,
                allocation). Must have exactly three entries with agent names
                ``"market_agent"``, ``"risk_agent"``, ``"allocation_agent"``.
            calibrated_confidences: output of
                ``ConfidenceEngine.calibrate()`` — a dict mapping each
                ``agent_name`` to its ``CalibratedConfidence``.
            universe: the full list of asset tickers in the investment
                universe. Every asset in this list appears in
                ``final_allocation``.

        Returns:
            ``FusedDecision`` with confidence-weighted ``final_allocation``,
            composed ``reasoning`` (agents sorted by descending confidence,
            ADR-019), passed-through ``confidence_summary``, and
            ``fusion_metadata`` with auditability information.

        Raises:
            ValueError: if the number of agent outputs is not exactly three
                or if an expected agent is missing.
        """
        self._validate_inputs(agent_outputs, calibrated_confidences)

        agent_map = self._build_agent_map(agent_outputs)
        conf_map = self._extract_confidence_values(calibrated_confidences)

        proposals = self._compute_proposals(agent_map, universe)
        fusion_metadata: dict[str, Any] = {
            "per_agent_proposals": {
                name: dict(prop) for name, prop in proposals.items()
            },
        }

        final_allocation, fallback_used = self._fuse_weighted_average(
            proposals, conf_map, universe,
        )
        fusion_metadata["fallback_used"] = fallback_used

        reasoning = self._compose_reasoning(agent_map, conf_map)
        confidence_summary = {
            name: cc.calibrated_confidence
            for name, cc in calibrated_confidences.items()
        }

        return FusedDecision(
            final_allocation=final_allocation,
            reasoning=reasoning,
            confidence_summary=confidence_summary,
            fusion_metadata=fusion_metadata,
            timestamp=datetime.now(),
        )

    # ------------------------------------------------------------------
    # Per-agent transform functions (ADR-020)
    # ------------------------------------------------------------------

    def _market_to_proposal(
        self,
        recommendation: dict[str, str],
        universe: list[str],
    ) -> AssetWeightProposal:
        """Transform Market Analysis recommendation to ``AssetWeightProposal``.

        BUY → +1, HOLD → 0, SELL → -1 per asset.  Negative values are
        clipped to 0, then renormalised to sum to 1.  If all assets are
        non-positive, falls back to equal-weight across ``universe`` (logged).
        """
        clipped: dict[str, float] = {}
        for asset in universe:
            raw = recommendation.get(asset, "HOLD")
            score = 1.0 if raw == "BUY" else (0.0 if raw == "HOLD" else -1.0)
            clipped[asset] = max(score, 0.0)

        total = sum(clipped.values())
        if total > 0.0:
            proposal = {a: v / total for a, v in clipped.items()}
        else:
            n = len(universe)
            logger.warning(
                "Market agent: no BUY signals in recommendation; "
                "falling back to equal-weight across %d assets.",
                n,
            )
            proposal = {a: 1.0 / n for a in universe}

        return proposal

    def _risk_to_proposal(
        self,
        recommendation: dict[str, dict[str, float]],
        universe: list[str],
        epsilon: float | None = None,
    ) -> AssetWeightProposal:
        """Transform Risk Assessment recommendation to ``AssetWeightProposal``.

        Per-asset ``risk_score`` is inverted via ``1 / (epsilon + risk_score)``,
        then renormalised to sum to 1 (lower risk → higher weight).

        Args:
            recommendation: ``{asset: {"expected_volatility": float,
                "risk_score": float}}``.
            universe: full asset list.
            epsilon: small constant to avoid division by zero.  If ``None``,
                defaults to ``1e-6`` (may be overridden by per-agent config).
        """
        if epsilon is None:
            epsilon = 1e-6

        inv: dict[str, float] = {}
        for asset in universe:
            scores = recommendation.get(asset, {"risk_score": 1.0})
            risk = float(scores.get("risk_score", 1.0))
            inv[asset] = 1.0 / (epsilon + risk)

        total = sum(inv.values())
        if total > 0.0:
            proposal = {a: v / total for a, v in inv.items()}
        else:
            n = len(universe)
            logger.warning(
                "Risk agent: all risk_score values produced zero inverse; "
                "falling back to equal-weight across %d assets.",
                n,
            )
            proposal = {a: 1.0 / n for a in universe}

        return proposal

    def _allocation_to_proposal(
        self,
        recommendation: dict[str, float],
        universe: list[str],
    ) -> AssetWeightProposal:
        """Transform Portfolio Allocation recommendation to ``AssetWeightProposal``.

        Defensive re-clip (negatives → 0) and renormalise to sum to 1.
        Falls back to equal-weight if the sum of clipped weights is zero
        (logged).
        """
        clipped: dict[str, float] = {}
        for asset in universe:
            w = recommendation.get(asset, 0.0)
            clipped[asset] = max(float(w), 0.0)

        total = sum(clipped.values())
        if total > 0.0:
            proposal = {a: v / total for a, v in clipped.items()}
        else:
            n = len(universe)
            logger.warning(
                "Allocation agent: all weights are zero or negative; "
                "falling back to equal-weight across %d assets.",
                n,
            )
            proposal = {a: 1.0 / n for a in universe}

        return proposal

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        agent_outputs: list[AgentOutput],
        calibrated_confidences: dict[str, CalibratedConfidence],
    ) -> None:
        """Verify that exactly three agents are present and accounted for."""
        if len(agent_outputs) != 3:
            raise ValueError(
                f"Expected exactly 3 agent outputs, got {len(agent_outputs)}."
            )

        names = {ao.agent_name for ao in agent_outputs}
        if names != _EXPECTED_AGENTS:
            raise ValueError(
                f"Expected agents {_EXPECTED_AGENTS}, got {names}."
            )

        missing = _EXPECTED_AGENTS - set(calibrated_confidences.keys())
        if missing:
            raise ValueError(
                f"Missing calibrated confidence for agent(s): {missing}."
            )

    @staticmethod
    def _build_agent_map(
        agent_outputs: list[AgentOutput],
    ) -> dict[str, AgentOutput]:
        """Index agent outputs by agent name for O(1) lookup."""
        return {ao.agent_name: ao for ao in agent_outputs}

    @staticmethod
    def _extract_confidence_values(
        calibrated_confidences: dict[str, CalibratedConfidence],
    ) -> dict[str, float]:
        """Extract scalar calibrated confidence from the full objects."""
        return {
            name: cc.calibrated_confidence
            for name, cc in calibrated_confidences.items()
        }

    def _compute_proposals(
        self,
        agent_map: dict[str, AgentOutput],
        universe: list[str],
    ) -> dict[str, AssetWeightProposal]:
        """Compute the AssetWeightProposal for each agent.

        Delegates to the per-agent transform function based on ``agent_name``.
        """
        proposals: dict[str, AssetWeightProposal] = {}

        for name in [_AGENT_MARKET, _AGENT_RISK, _AGENT_ALLOCATION]:
            ao = agent_map[name]
            if name == _AGENT_MARKET:
                proposals[name] = self._market_to_proposal(
                    ao.recommendation, universe,
                )
            elif name == _AGENT_RISK:
                cfg = self._agent_configs.get(name)
                eps = cfg.epsilon if cfg is not None else None
                proposals[name] = self._risk_to_proposal(
                    ao.recommendation, universe, epsilon=eps,
                )
            elif name == _AGENT_ALLOCATION:
                proposals[name] = self._allocation_to_proposal(
                    ao.recommendation, universe,
                )

        return proposals

    @staticmethod
    def _fuse_weighted_average(
        proposals: dict[str, AssetWeightProposal],
        conf_map: dict[str, float],
        universe: list[str],
    ) -> tuple[dict[str, float], bool]:
        """Apply the confidence-weighted fusion formula.

        Returns:
            ``(final_allocation, fallback_used)``.
        """
        conf_sum = sum(conf_map.values())
        fallback_used = conf_sum < 1e-12

        if fallback_used:
            logger.warning(
                "Sum of calibrated confidences is %.6f (≈ 0); "
                "falling back to equal-weight average of proposals.",
                conf_sum,
            )
            n_agents = len(proposals)
            final_allocation: dict[str, float] = {}
            for asset in universe:
                total = sum(
                    proposals[name].get(asset, 0.0) for name in proposals
                )
                final_allocation[asset] = total / n_agents
        else:
            final_allocation = {}
            for asset in universe:
                weighted = sum(
                    proposals[name].get(asset, 0.0) * conf_map[name]
                    for name in proposals
                )
                final_allocation[asset] = weighted / conf_sum

        return final_allocation, fallback_used

    @staticmethod
    def _compose_reasoning(
        agent_map: dict[str, AgentOutput],
        conf_map: dict[str, float],
    ) -> str:
        """Compose ``reasoning`` string per ADR-019.

        Agents are sorted by calibrated confidence descending.  Each entry
        is ``"{agent_name}({confidence:.2f}): {agent_output.reasoning}"``,
        joined with ``"; "``.
        """
        sorted_agents = sorted(
            conf_map.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        parts: list[str] = []
        for name, conf in sorted_agents:
            ao = agent_map.get(name)
            reason = ao.reasoning if ao is not None else ""
            parts.append(f"{name}({conf:.2f}): {reason}")
        return "; ".join(parts)
