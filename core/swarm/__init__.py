"""
Swarm Intelligence Coordination System for ToolboxAI Roblox Environment

This module provides a comprehensive swarm intelligence system that enables:
- Parallel agent execution and coordination
- Intelligent task distribution and scheduling
- Consensus-based quality control and validation
- Dynamic resource optimization and load balancing
- Educational content generation at scale

The system is designed to work seamlessly with the existing agent architecture
and SPARC framework, providing scalable solutions for educational content creation.
"""

from .swarm_controller import SwarmController, SwarmConfig, SwarmMetrics
from .worker_pool import WorkerPool, WorkerAgent, WorkerCapability, WorkerStatus
from .task_distributor import TaskDistributor, Task, TaskPriority, TaskStatus
from .consensus_engine import ConsensusEngine, ConsensusResult, VotingStrategy
from .load_balancer import LoadBalancer, ResourceMetrics, LoadBalancingStrategy

from typing import Dict, Any, Optional, List
import asyncio
import logging

__version__ = "1.0.0"
__author__ = "ToolboxAI Solutions"

# Configure logging
logger = logging.getLogger(__name__)

# Export main classes
__all__ = [
    # Core Components
    "SwarmController",
    "WorkerPool",
    "TaskDistributor",
    "ConsensusEngine",
    "LoadBalancer",
    # Data Models
    "SwarmConfig",
    "SwarmMetrics",
    "WorkerAgent",
    "WorkerCapability",
    "WorkerStatus",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "ConsensusResult",
    "VotingStrategy",
    "ResourceMetrics",
    "LoadBalancingStrategy",
    # Factory Functions
    "create_swarm",
    "create_educational_swarm",
    "get_default_config",
]

# Default configuration for educational content generation
DEFAULT_EDUCATIONAL_CONFIG = {
    "max_workers": 10,
    "min_workers": 2,
    "task_timeout": 300,  # 5 minutes
    "consensus_threshold": 0.7,
    "load_balancing_strategy": "round_robin",
    "worker_specializations": [
        "content_generation",
        "quiz_creation",
        "terrain_generation",
        "script_optimization",
        "quality_review",
    ],
    "educational_optimizations": {
        "subject_specialization": True,
        "grade_level_adaptation": True,
        "learning_objective_focus": True,
        "accessibility_compliance": True,
    },
}


def get_default_config() -> Dict[str, Any]:
    """Get default swarm configuration for educational content generation."""
    return DEFAULT_EDUCATIONAL_CONFIG.copy()


async def create_swarm(config: Optional[Dict[str, Any]] = None) -> SwarmController:
    """
    Factory function to create a fully configured swarm controller.

    Args:
        config: Optional configuration dictionary. Uses defaults if not provided.

    Returns:
        Configured SwarmController instance ready for use
    """
    if config is None:
        config = get_default_config()

    # Create swarm configuration
    swarm_config = SwarmConfig(**config)

    # Initialize components
    worker_pool = WorkerPool(
        max_workers=swarm_config.max_workers,
        min_workers=swarm_config.min_workers,
        specializations=swarm_config.worker_specializations,
    )

    task_distributor = TaskDistributor(timeout=swarm_config.task_timeout)

    consensus_engine = ConsensusEngine(threshold=swarm_config.consensus_threshold)

    load_balancer = LoadBalancer(strategy=swarm_config.load_balancing_strategy)

    # Create and initialize swarm controller
    swarm = SwarmController(
        config=swarm_config,
        worker_pool=worker_pool,
        task_distributor=task_distributor,
        consensus_engine=consensus_engine,
        load_balancer=load_balancer,
    )

    await swarm.initialize()

    logger.info(f"Created swarm with {swarm_config.max_workers} max workers")
    return swarm


async def create_educational_swarm(
    subject: str = "general", grade_level: int = 5, max_workers: int = 8
) -> SwarmController:
    """
    Factory function to create a swarm optimized for educational content generation.

    Args:
        subject: Primary subject area (math, science, english, etc.)
        grade_level: Target grade level (K-12)
        max_workers: Maximum number of worker agents

    Returns:
        SwarmController optimized for educational content
    """
    config = get_default_config()

    # Educational optimizations
    config.update(
        {
            "max_workers": max_workers,
            "primary_subject": subject,
            "target_grade_level": grade_level,
            "educational_optimizations": {
                **config["educational_optimizations"],
                "subject_specialization": True,
                "grade_level_adaptation": True,
                "curriculum_alignment": True,
                "assessment_integration": True,
            },
        }
    )

    return await create_swarm(config)


# Initialize default logger configuration
def _setup_logging():
    """Setup default logging configuration for the swarm system."""
    import os
    handlers = [logging.StreamHandler()]

    # Only add file handler if we can write to the log directory
    try:
        log_dir = os.environ.get('LOG_DIR', '/tmp')
        log_file = os.path.join(log_dir, 'swarm.log')
        if os.access(log_dir, os.W_OK):
            handlers.append(logging.FileHandler(log_file))
    except Exception:
        # Silently ignore file handler errors in production
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


# Auto-setup logging when module is imported
_setup_logging()

# Module metadata
__doc__ = __doc__
__all__ = __all__
