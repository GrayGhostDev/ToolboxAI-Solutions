"""
Error Handling Agent Swarm

A comprehensive suite of specialized agents for error detection, correction,
debugging, and testing within the ToolBoxAI platform.
"""

from .base_error_agent import BaseErrorAgent, ErrorPriority, ErrorState, ErrorType
from .code_review_sentinel_agent import CodeReviewSentinelAgent
from .debugging_agent import AdvancedDebuggingAgent
from .error_aggregation_intelligence_agent import ErrorAggregationIntelligenceAgent
from .error_correction_agent import ErrorCorrectionAgent

# from .testing_orchestrator_agent import TestingOrchestratorAgent  # Archived - now in orchestration module
from .error_pattern_analysis_agent import ErrorPatternAnalysisAgent
from .integration_testing_coordinator_agent import IntegrationTestingCoordinatorAgent

# from .auto_recovery_orchestrator_agent import AutoRecoveryOrchestratorAgent  # Archived - now in orchestration module
from .swarm_coordinator import ErrorHandlingSwarmCoordinator

__all__ = [
    "BaseErrorAgent",
    "ErrorPriority",
    "ErrorType",
    "ErrorState",
    "ErrorCorrectionAgent",
    "AdvancedDebuggingAgent",
    # "TestingOrchestratorAgent",  # Archived
    "ErrorPatternAnalysisAgent",
    "CodeReviewSentinelAgent",
    "IntegrationTestingCoordinatorAgent",
    "ErrorAggregationIntelligenceAgent",
    # "AutoRecoveryOrchestratorAgent",  # Archived
    "ErrorHandlingSwarmCoordinator",
]
