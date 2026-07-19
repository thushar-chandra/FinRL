"""Shared contracts and data structures for the CA-MARL pipeline.

All dataclasses, type aliases, and exceptions that cross module boundaries
are defined here. No business logic, algorithms, training, or confidence
estimation code belongs in this file.

Reference: docs/architecture/INTERFACE_CONTRACTS.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

AssetWeightProposal = dict[str, float]
"""Fusion intermediate representation (ADR-020).

Per-asset weight vector, all values >= 0, sums to 1.0 within floating-point
tolerance. Every agent's heterogeneous ``recommendation`` is transformed into
this shape before confidence-weighted averaging.
"""


# ---------------------------------------------------------------------------
# Exceptions — interface-contract errors that cross module boundaries
# ---------------------------------------------------------------------------

class InsufficientHistoryError(Exception):
    """Raised when an agent has insufficient training data or history to
    produce a prediction (e.g., indicator warm-up period not satisfied)."""


class LabelNotYetResolvableError(Exception):
    """Raised when an outcome label is requested before its label horizon
    has elapsed (recommendation.timestamp + label_horizon)."""


class EvaluationDataMismatchError(Exception):
    """Raised when recommendation timestamps and the realized-returns index
    do not align in an evaluation call."""


# ---------------------------------------------------------------------------
# Core pipeline data structures
# ---------------------------------------------------------------------------

@dataclass
class AgentOutput:
    """Output contract for every specialised RL agent.

    Every agent — Market Analysis, Risk Assessment, Portfolio Allocation —
    returns this schema.  ``confidence`` is populated by Confidence
    Calibration, not by the agent itself; the agent provides
    ``metadata["reward_stability"]`` as a raw-confidence-relevant signal.

    Reference: INTERFACE_CONTRACTS.md — Shared Data Structures, §§1-3.
    """

    agent_name: str
    recommendation: Any
    raw_confidence: float
    reasoning: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None


@dataclass
class CalibratedConfidence:
    """Calibrated confidence for a single agent, produced by
    ``ConfidenceEngine.calibrate`` and consumed by
    ``ConfidenceAwareFusion.fuse``.

    ``calibrated_confidence`` is a scalar per agent (ADR-020) — never a
    per-asset dict.  ``diagnostics`` holds ECE, Brier score and the
    reliability-curve artifact path.

    Reference: INTERFACE_CONTRACTS.md — Shared Data Structures.
    """

    agent_name: str
    calibrated_confidence: float
    diagnostics: dict[str, Any]
    timestamp: datetime


@dataclass
class FusedDecision:
    """Output of the Confidence-Aware Decision Fusion module.

    ``final_allocation`` is an ``AssetWeightProposal``-shaped dict (non-negative,
    sums to 1.0).  ``reasoning`` is composed by ``ConfidenceAwareFusion.fuse``
    from per-agent reasoning sorted by descending confidence (ADR-019).
    ``confidence_summary`` is the calibrated-confidence dict passed through
    unchanged.  ``fusion_metadata`` carries auditability info such as
    whether a fallback was used.

    Reference: INTERFACE_CONTRACTS.md — Shared Data Structures, §5.
    """

    final_allocation: dict[str, float]
    reasoning: str
    confidence_summary: dict[str, float]
    fusion_metadata: dict[str, Any]
    timestamp: datetime


@dataclass
class FinalRecommendation:
    """Final Portfolio Recommendation (canonical prose term — ADR-026).

    ``allocation`` is long-only, sums to 1.0, and has passed through the
    Risk Management Layer's authoritative enforcement.  ``reasoning`` and
    ``confidence_summary`` are passed through **unchanged** from
    ``FusedDecision`` (ADR-019).

    Reference: INTERFACE_CONTRACTS.md — Shared Data Structures, §6.
    """

    allocation: dict[str, float]
    reasoning: str
    confidence_summary: dict[str, float]
    timestamp: datetime


# ---------------------------------------------------------------------------
# Evaluation data structures (ADR-021)
# ---------------------------------------------------------------------------

@dataclass
class FinancialMetrics:
    """Standard portfolio-performance metrics over a walk-forward test window."""

    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    cumulative_return: float


@dataclass
class CalibrationMetrics:
    """Calibration-quality metrics for a single agent."""

    ece: float
    brier_score: float
    reliability_curve_ref: str


@dataclass
class EvaluationReport:
    """Structured evaluation report covering all four measurement tracks:
    financial, calibration, ablation, and baseline comparison.

    ``calibration_metrics`` is keyed by ``agent_name``.
    """

    financial_metrics: FinancialMetrics
    calibration_metrics: dict[str, CalibrationMetrics]
    ablation_results: dict[str, Any] | None
    baseline_comparison: dict[str, FinancialMetrics] | None
    fold_id: str
    timestamp: datetime
