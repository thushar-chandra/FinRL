"""CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for
Portfolio Decision Support.

This package implements the full CA-MARL pipeline as specified in the
frozen architecture (docs/architecture/).  Submodules are added as each
stage of the pipeline is implemented.

Current state: shared contracts, configuration schemas, all three
specialised RL agents (Market, Risk, Allocation), Confidence
Estimation & Calibration, Confidence-Aware Decision Fusion,
Risk Management Layer, and Evaluation Engine.
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

from finrl.agents.ca_marl.market_agent import MarketAnalysisAgent
from finrl.agents.ca_marl.risk_agent import RiskAssessmentAgent
from finrl.agents.ca_marl.allocation_agent import PortfolioAllocationAgent
from finrl.agents.ca_marl.confidence_engine import (
    ConfidenceEngine,
    OutcomeLabelGenerator,
)
from finrl.agents.ca_marl.confidence_fusion import ConfidenceAwareFusion
from finrl.agents.ca_marl.risk_management import RiskManagementLayer
from finrl.agents.ca_marl.evaluation import EvaluationEngine
from finrl.agents.ca_marl.pipeline import (
    build_agents,
    run_inference,
    run_pipeline,
)
from finrl.agents.ca_marl.data_adapter import download_and_prepare

__all__ = [
    # --- Agents ---
    "MarketAnalysisAgent",
    "RiskAssessmentAgent",
    "PortfolioAllocationAgent",
    # --- Confidence & Calibration ---
    "ConfidenceEngine",
    "OutcomeLabelGenerator",
    # --- Fusion ---
    "ConfidenceAwareFusion",
    # --- Risk Management ---
    "RiskManagementLayer",
    # --- Evaluation ---
    "EvaluationEngine",
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
    # --- Pipeline ---
    "build_agents",
    "run_inference",
    "run_pipeline",
    # --- Data adapter ---
    "download_and_prepare",
    # --- Evaluation data structures ---
    "FinancialMetrics",
    "CalibrationMetrics",
    "EvaluationReport",
    # --- Exceptions ---
    "InsufficientHistoryError",
    "LabelNotYetResolvableError",
    "EvaluationDataMismatchError",
]
