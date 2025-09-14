"""
Factory for creating properly configured SwarmController instances.

This module provides a factory function that creates SwarmController with all
required dependencies, handling initialization complexity and providing
sensible defaults for testing and production use.
"""

import logging
from typing import Optional
from .swarm_controller import SwarmController, SwarmConfig
from .worker_pool import WorkerPool, WorkerConfig
from .task_distributor import TaskDistributor, DistributorConfig
from .consensus_engine import ConsensusEngine, ConsensusConfig
from .load_balancer import LoadBalancer, LoadBalancerConfig

logger = logging.getLogger(__name__)


async def create_swarm_controller(
    config: Optional[SwarmConfig] = None,
    worker_config: Optional[WorkerConfig] = None,
    distributor_config: Optional[DistributorConfig] = None,
    consensus_config: Optional[ConsensusConfig] = None,
    balancer_config: Optional[LoadBalancerConfig] = None,
) -> SwarmController:
    """
    Create a properly configured SwarmController with all dependencies.
    
    Args:
        config: SwarmController configuration
        worker_config: WorkerPool configuration
        distributor_config: TaskDistributor configuration
        consensus_config: ConsensusEngine configuration
        balancer_config: LoadBalancer configuration
    
    Returns:
        Initialized SwarmController instance
    """
    # Use default configurations if not provided
    config = config or SwarmConfig()
    worker_config = worker_config or WorkerConfig(
        max_workers=config.max_workers,
        min_workers=config.min_workers
    )
    distributor_config = distributor_config or DistributorConfig()
    consensus_config = consensus_config or ConsensusConfig(
        threshold=config.consensus_threshold
    )
    balancer_config = balancer_config or LoadBalancerConfig(
        strategy=config.load_balancing_strategy
    )
    
    # Create components
    worker_pool = WorkerPool(worker_config)
    task_distributor = TaskDistributor(distributor_config)
    consensus_engine = ConsensusEngine(consensus_config)
    load_balancer = LoadBalancer(balancer_config)
    
    # Create controller
    controller = SwarmController(
        config=config,
        worker_pool=worker_pool,
        task_distributor=task_distributor,
        consensus_engine=consensus_engine,
        load_balancer=load_balancer
    )
    
    # Initialize
    await controller.initialize()
    
    logger.info("SwarmController created and initialized successfully")
    return controller


def create_test_swarm_controller() -> SwarmController:
    """
    Create a SwarmController configured for testing.
    
    Returns:
        SwarmController configured with minimal resources for testing
    """
    config = SwarmConfig(
        max_workers=2,
        min_workers=1,
        task_timeout=10,
        consensus_threshold=0.5,
        auto_scaling=False,
        health_check_interval=60
    )
    
    worker_config = WorkerConfig(max_workers=2, min_workers=1)
    distributor_config = DistributorConfig()
    consensus_config = ConsensusConfig(threshold=0.5)
    balancer_config = LoadBalancerConfig(strategy="round_robin")
    
    # Create components
    worker_pool = WorkerPool(worker_config)
    task_distributor = TaskDistributor(distributor_config)
    consensus_engine = ConsensusEngine(consensus_config)
    load_balancer = LoadBalancer(balancer_config)
    
    # Create controller
    controller = SwarmController(
        config=config,
        worker_pool=worker_pool,
        task_distributor=task_distributor,
        consensus_engine=consensus_engine,
        load_balancer=load_balancer
    )
    
    logger.info("Test SwarmController created")
    return controller