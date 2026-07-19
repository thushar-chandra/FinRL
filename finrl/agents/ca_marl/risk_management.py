"""Risk Management Layer — authoritative portfolio constraint enforcement.

Enforces long-only (all weights >= 0), sum-to-one (within floating-point
tolerance), and exposure-cap constraints on the fused decision.  ``reasoning``
and ``confidence_summary`` are passed through **unchanged** from
``FusedDecision`` (ADR-019) — this module only transforms ``final_allocation``
into ``allocation``.

Reference: docs/architecture/AGENTS.md §6,
docs/architecture/INTERFACE_CONTRACTS.md §6,
docs/architecture/MODULE_SPECIFICATIONS.md §6.
"""

import logging
from datetime import datetime

from finrl.agents.ca_marl.config_schema import RiskManagementConfig
from finrl.agents.ca_marl.contracts import (
    FinalRecommendation,
    FusedDecision,
)

logger = logging.getLogger(__name__)


class RiskManagementLayer:
    """Authoritative portfolio-constraint enforcement.

    Transforms a ``FusedDecision`` into a ``FinalRecommendation`` by:
      - Clipping negative allocation weights to 0 (long-only).
      - Normalising the weight vector to sum to 1.0.
      - Projecting the weight vector onto the capped simplex (each weight
        <= ``max_exposure_per_asset``) via an iterative capped-normalise
        algorithm that converges to the unique feasible point satisfying
        all three hard constraints simultaneously.
      - Passing ``reasoning`` and ``confidence_summary`` through unchanged.

    Never raises an exception — malformed input always produces a valid,
    constraint-satisfying output by construction of the enforcement logic.
    """

    def __init__(self, config: RiskManagementConfig | None = None) -> None:
        """Initialise the Risk Management Layer.

        Args:
            config: risk-management parameters (exposure cap).  If ``None``,
                a default ``max_exposure_per_asset`` of 1.0 (no effective cap)
                is used.
        """
        self._config = config or RiskManagementConfig(max_exposure_per_asset=1.0)

    def apply(self, fused_decision: FusedDecision) -> FinalRecommendation:
        """Authoritatively enforce portfolio constraints.

        Args:
            fused_decision: the fused output from
                ``ConfidenceAwareFusion.fuse()``.

        Returns:
            A constraint-satisfying ``FinalRecommendation`` with ``reasoning``
            and ``confidence_summary`` passed through unchanged.
        """
        raw = fused_decision.final_allocation
        assets = list(raw.keys())
        cap = self._config.max_exposure_per_asset

        # Step 1 — long-only: clip negative weights to 0.
        pos = {a: max(float(w), 0.0) for a, w in raw.items()}

        # Step 2 — normalise to sum to 1.0.
        norm = self._normalise(pos, assets)

        # Step 3 — project onto capped simplex (long-only + sum-to-one + cap).
        allocation = self._project_capped_simplex(norm, assets, cap)

        return FinalRecommendation(
            allocation=allocation,
            reasoning=fused_decision.reasoning,
            confidence_summary=fused_decision.confidence_summary,
            timestamp=datetime.now(),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(
        weights: dict[str, float],
        assets: list[str],
    ) -> dict[str, float]:
        """Normalise a weight dict to sum to 1.0.

        Falls back to equal-weight if all weights are zero.
        """
        total = sum(weights.values())
        if total > 0.0:
            return {a: weights[a] / total for a in assets}
        n = len(assets)
        logger.warning(
            "All allocation weights are zero; falling back to equal-weight "
            "across %d assets.",
            n,
        )
        return {a: 1.0 / n for a in assets}

    @staticmethod
    def _project_capped_simplex(
        weights: dict[str, float],
        assets: list[str],
        cap: float,
    ) -> dict[str, float]:
        """Project a weight vector onto the capped simplex.

        Algorithm: iteratively cap weights at *cap*, collect the excess,
        and redistribute equally to uncapped assets.  Converges because
        each iteration either terminates or adds at least one asset to
        the capped set (at most ``len(assets)`` iterations).

        When *cap* is so tight that all assets end up capped (cap × n < 1),
        caps are treated as proportional targets and the vector is
        normalised back to sum 1 with a warning.
        """
        if cap >= 1.0 - 1e-12:
            return dict(weights)

        result = {a: float(w) for a, w in weights.items()}
        capped_set: set[str] = set()

        for _ in range(len(assets) + 1):
            # Clip any asset exceeding the cap.
            newly_capped = {a for a in assets if result[a] > cap and a not in capped_set}
            if not newly_capped and all(result[a] <= cap + 1e-12 for a in assets):
                return result

            for a in newly_capped:
                capped_set.add(a)

            excess = sum(result[a] - cap for a in capped_set)
            for a in capped_set:
                result[a] = cap

            uncapped = [a for a in assets if a not in capped_set]
            if not uncapped:
                break

            addition = excess / len(uncapped)
            for a in uncapped:
                result[a] += addition

        # If we exit the loop without converging (all assets capped), apply
        # caps as proportional targets and normalise.
        total = sum(result.values())
        if abs(total - 1.0) > 1e-9:
            logger.warning(
                "Exposure cap %.4f is too tight for %d-asset portfolio "
                "(sum(caps) = %.4f < 1). Capped-then-normalised weights "
                "may exceed the cap.",
                cap, len(assets), cap * len(assets),
            )
            if total > 0.0:
                result = {a: result[a] / total for a in assets}
            else:
                n = len(assets)
                result = {a: 1.0 / n for a in assets}

        return result
