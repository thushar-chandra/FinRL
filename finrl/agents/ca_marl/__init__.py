"""CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for
Portfolio Decision Support.

This package implements the full CA-MARL pipeline as specified in the
frozen architecture (docs/architecture/).  Submodules are added as each
stage of the pipeline is implemented.

Current state: shared contracts and configuration schemas.
"""

from finrl.agents.ca_marl.config_schema import (
    AgentHyperparameters,
    CAMARLConfig,
    ConfidenceConfig,
    FeatureEngineeringConfig,
    PPOConfig,
    RiskManagementConfig,
    UniverseConfig,
    WalkForwardConfig,
)

from finrl.agents.ca_marl.contracts import (
    AgentOutput,
    AssetWeightProposal,
    CalibratedConfidence,
    CalibrationMetrics,
    EvaluationDataMismatchError,
    EvaluationReport,
    FinalRecommendation,
    FinancialMetrics,
    FusedDecision,
    InsufficientHistoryError,
    LabelNotYetResolvableError,
)

__all__ = [
    # --- Configuration models ---
    "AgentHyperparameters",
    "CAMARLConfig",
    "ConfidenceConfig",
    "FeatureEngineeringConfig",
    "PPOConfig",
    "RiskManagementConfig",
    "UniverseConfig",
    "WalkForwardConfig",
    # --- Core data structures ---
    "AgentOutput",
    "AssetWeightProposal",
    "CalibratedConfidence",
    "FusedDecision",
    "FinalRecommendation",
    # --- Evaluation data structures ---
    "FinancialMetrics",
    "CalibrationMetrics",
    "EvaluationReport",
    # --- Exceptions ---
    "InsufficientHistoryError",
    "LabelNotYetResolvableError",
    "EvaluationDataMismatchError",
]
