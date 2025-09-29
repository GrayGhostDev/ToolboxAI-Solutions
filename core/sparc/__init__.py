"""
SPARC Framework - State-Policy-Action-Reward-Context System
===========================================================

The SPARC framework provides a comprehensive system for managing intelligent decision-making
in educational AI agents. It integrates state tracking, policy execution, action management,
reward calculation, and context persistence.

Components:
- StateManager: Environment state tracking and management
- PolicyEngine: Educational policy decisions and learning
- ActionExecutor: Action execution pipeline with safety checks
- RewardCalculator: Learning outcome rewards and progress tracking
- ContextTracker: User context management and session persistence

Usage:
    from core.sparc import SPARCFramework, create_sparc_system

    # Create complete SPARC system
    sparc = create_sparc_system(config)

    # Run SPARC cycle
    result = await sparc.execute_cycle(observation)
"""

from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass, field
from datetime import datetime
import json

# Import all SPARC components
from .state_manager import StateManager, EnvironmentState, SPARCStateManager
from .policy_engine import PolicyEngine, EducationalPolicy
from .action_executor import ActionExecutor, Action, ActionResult
from .reward_calculator import RewardCalculator, RewardSignal
from .context_tracker import ContextTracker, UserContext

__version__ = "1.0.0"
__all__ = [
    "SPARCFramework",
    "SPARCConfig",
    "StateManager",
    "SPARCStateManager",  # Backward compatibility alias
    "PolicyEngine",
    "ActionExecutor",
    "RewardCalculator",
    "ContextTracker",
    "EnvironmentState",
    "EducationalPolicy",
    "Action",
    "ActionResult",
    "RewardSignal",
    "UserContext",
    "create_sparc_system",
    "create_sparc_config",
]

logger = logging.getLogger(__name__)


@dataclass
class SPARCConfig:
    """Configuration for SPARC framework components"""

    # State management
    state_history_size: int = 1000
    state_compression_threshold: int = 500
    state_persistence_interval: float = 30.0

    # Policy engine
    policy_learning_rate: float = 0.01
    policy_exploration_rate: float = 0.1
    policy_decay_factor: float = 0.95
    policy_update_frequency: int = 10

    # Action execution
    max_parallel_actions: int = 5
    action_timeout: float = 30.0
    action_retry_attempts: int = 3
    safety_check_enabled: bool = True

    # Reward calculation
    reward_dimensions: List[str] = field(
        default_factory=lambda: ["learning_progress", "engagement", "accuracy", "creativity", "collaboration"]
    )
    reward_normalization: bool = True
    reward_history_size: int = 100

    # Context tracking
    context_window_size: int = 50
    session_timeout: float = 1800.0  # 30 minutes
    context_compression_enabled: bool = True
    learning_history_retention: int = 30  # days

    # Integration
    agent_integration_enabled: bool = True
    real_time_updates: bool = True
    async_processing: bool = True

    # Logging and monitoring
    logging_level: str = "INFO"
    metrics_enabled: bool = True
    performance_tracking: bool = True


class SPARCFramework:
    """
    Main SPARC framework orchestrating all components.

    The SPARC framework implements a complete cycle of:
    - State observation and management
    - Policy-based decision making
    - Action execution with safety checks
    - Reward calculation and feedback
    - Context tracking and persistence
    """

    def __init__(self, config: SPARCConfig):
        """Initialize SPARC framework with configuration"""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SPARCFramework")

        # Initialize all components
        self.state_manager = StateManager(
            history_size=config.state_history_size,
            compression_threshold=config.state_compression_threshold,
            persistence_interval=config.state_persistence_interval,
        )

        self.policy_engine = PolicyEngine(
            learning_rate=config.policy_learning_rate,
            exploration_rate=config.policy_exploration_rate,
            decay_factor=config.policy_decay_factor,
            update_frequency=config.policy_update_frequency,
        )

        self.action_executor = ActionExecutor(
            max_parallel=config.max_parallel_actions,
            timeout=config.action_timeout,
            retry_attempts=config.action_retry_attempts,
            safety_checks=config.safety_check_enabled,
        )

        self.reward_calculator = RewardCalculator(
            dimensions=config.reward_dimensions,
            normalization=config.reward_normalization,
            history_size=config.reward_history_size,
        )

        self.context_tracker = ContextTracker(
            window_size=config.context_window_size,
            session_timeout=config.session_timeout,
            compression_enabled=config.context_compression_enabled,
            retention_days=config.learning_history_retention,
        )

        # Framework state
        self.cycle_count = 0
        self.last_cycle_time = None
        self.performance_metrics = {}

        self.logger.info("SPARC Framework initialized successfully")

    async def execute_cycle(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete SPARC cycle.

        Args:
            observation: Current environment observation

        Returns:
            Dictionary containing cycle results and next actions
        """
        cycle_start = datetime.now()
        self.cycle_count += 1

        try:
            # 1. STATE: Update environment state
            current_state = await self.state_manager.update_state(observation)
            self.logger.debug(f"State updated: {current_state.summary}")

            # 2. POLICY: Make policy decision
            policy_input = {
                "state": current_state,
                "context": await self.context_tracker.get_current_context(),
                "history": self.state_manager.get_recent_states(10),
            }
            policy_decision = await self.policy_engine.decide(policy_input)
            self.logger.debug(f"Policy decision: {policy_decision.action_type}")

            # 3. ACTION: Execute chosen action
            action = Action(
                type=policy_decision.action_type,
                parameters=policy_decision.parameters,
                priority=policy_decision.priority,
                metadata={"cycle": self.cycle_count, "timestamp": cycle_start.isoformat()},
            )
            action_result = await self.action_executor.execute(action)
            self.logger.debug(f"Action executed: {action_result.success}")

            # 4. REWARD: Calculate rewards
            reward_input = {
                "state": current_state,
                "action": action,
                "result": action_result,
                "context": await self.context_tracker.get_current_context(),
            }
            rewards = await self.reward_calculator.calculate_rewards(reward_input)
            self.logger.debug(f"Rewards calculated: {rewards.total_reward}")

            # 5. CONTEXT: Update context and learning history
            context_update = {
                "state": current_state,
                "action": action,
                "result": action_result,
                "rewards": rewards,
                "cycle": self.cycle_count,
            }
            await self.context_tracker.update_context(context_update)

            # Update policy with feedback
            await self.policy_engine.update_policy(
                state=current_state,
                action=action,
                reward=rewards.total_reward,
                next_state=current_state,  # Will be updated in next cycle
            )

            # Calculate cycle performance
            cycle_time = (datetime.now() - cycle_start).total_seconds()
            self.last_cycle_time = cycle_time
            self.performance_metrics[f"cycle_{self.cycle_count}"] = {
                "duration": cycle_time,
                "success": action_result.success,
                "reward": rewards.total_reward,
                "state_quality": current_state.confidence,
            }

            # Prepare response
            response = {
                "cycle_id": self.cycle_count,
                "timestamp": cycle_start.isoformat(),
                "duration": cycle_time,
                "state": current_state.to_dict(),
                "policy_decision": policy_decision.to_dict(),
                "action": action.to_dict(),
                "action_result": action_result.to_dict(),
                "rewards": rewards.to_dict(),
                "next_actions": policy_decision.next_actions,
                "context_summary": await self.context_tracker.get_context_summary(),
                "performance": {
                    "success_rate": self.calculate_success_rate(),
                    "average_reward": self.calculate_average_reward(),
                    "learning_progress": self.calculate_learning_progress(),
                },
            }

            self.logger.info(f"SPARC cycle {self.cycle_count} completed successfully in {cycle_time:.3f}s")
            return response

        except Exception as e:
            self.logger.error(f"SPARC cycle {self.cycle_count} failed: {e}")
            error_response = {
                "cycle_id": self.cycle_count,
                "timestamp": cycle_start.isoformat(),
                "error": str(e),
                "success": False,
                "recovery_actions": await self.generate_recovery_actions(e),
            }
            return error_response

    async def reset_framework(self):
        """Reset the entire SPARC framework to initial state"""
        self.logger.info("Resetting SPARC framework")

        await self.state_manager.reset()
        await self.policy_engine.reset()
        await self.action_executor.reset()
        await self.reward_calculator.reset()
        await self.context_tracker.reset()

        self.cycle_count = 0
        self.last_cycle_time = None
        self.performance_metrics = {}

        self.logger.info("SPARC framework reset completed")

    async def get_framework_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all SPARC components"""
        return {
            "framework": {
                "version": __version__,
                "cycle_count": self.cycle_count,
                "last_cycle_time": self.last_cycle_time,
                "uptime": (
                    (
                        datetime.now() - datetime.fromisoformat(list(self.performance_metrics.values())[0]["timestamp"])
                    ).total_seconds()
                    if self.performance_metrics
                    else 0
                ),
            },
            "state_manager": await self.state_manager.get_status(),
            "policy_engine": await self.policy_engine.get_status(),
            "action_executor": await self.action_executor.get_status(),
            "reward_calculator": await self.reward_calculator.get_status(),
            "context_tracker": await self.context_tracker.get_status(),
        }

    def calculate_success_rate(self) -> float:
        """Calculate overall success rate across cycles"""
        if not self.performance_metrics:
            return 0.0

        successes = sum(1 for m in self.performance_metrics.values() if m["success"])
        return successes / len(self.performance_metrics)

    def calculate_average_reward(self) -> float:
        """Calculate average reward across cycles"""
        if not self.performance_metrics:
            return 0.0

        total_reward = sum(m["reward"] for m in self.performance_metrics.values())
        return total_reward / len(self.performance_metrics)

    def calculate_learning_progress(self) -> float:
        """Calculate learning progress trend"""
        if len(self.performance_metrics) < 2:
            return 0.0

        recent_cycles = list(self.performance_metrics.values())[-10:]
        early_avg = sum(m["reward"] for m in recent_cycles[:5]) / min(5, len(recent_cycles))
        late_avg = sum(m["reward"] for m in recent_cycles[-5:]) / min(5, len(recent_cycles))

        return (late_avg - early_avg) / max(abs(early_avg), 1e-6)

    async def generate_recovery_actions(self, error: Exception) -> List[str]:
        """Generate recovery actions for errors"""
        recovery_actions = []

        if "timeout" in str(error).lower():
            recovery_actions.extend(
                ["Increase action timeout", "Reduce parallel action count", "Check system resources"]
            )

        if "memory" in str(error).lower():
            recovery_actions.extend(
                ["Clear old state history", "Compress context data", "Restart framework components"]
            )

        if not recovery_actions:
            recovery_actions = ["Reset affected component", "Check configuration settings", "Review error logs"]

        return recovery_actions


def create_sparc_config(**kwargs) -> SPARCConfig:
    """
    Create SPARC configuration with custom parameters.

    Args:
        **kwargs: Configuration parameters to override defaults

    Returns:
        SPARCConfig instance
    """
    return SPARCConfig(**kwargs)


def create_sparc_system(config: Optional[SPARCConfig] = None) -> SPARCFramework:
    """
    Create a complete SPARC system with default or custom configuration.

    Args:
        config: Optional SPARCConfig, uses defaults if None

    Returns:
        Initialized SPARCFramework instance
    """
    if config is None:
        config = SPARCConfig()

    return SPARCFramework(config)


# Factory functions for individual components
def create_state_manager(**kwargs) -> StateManager:
    """Create standalone StateManager"""
    return StateManager(**kwargs)


def create_policy_engine(**kwargs) -> PolicyEngine:
    """Create standalone PolicyEngine"""
    return PolicyEngine(**kwargs)


def create_action_executor(**kwargs) -> ActionExecutor:
    """Create standalone ActionExecutor"""
    return ActionExecutor(**kwargs)


def create_reward_calculator(**kwargs) -> RewardCalculator:
    """Create standalone RewardCalculator"""
    return RewardCalculator(**kwargs)


def create_context_tracker(**kwargs) -> ContextTracker:
    """Create standalone ContextTracker"""
    return ContextTracker(**kwargs)
