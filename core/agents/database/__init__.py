"""
Database Agent Swarm Module

This module provides a comprehensive swarm of specialized database agents
using LangGraph patterns for intelligent database management, including:
- Schema evolution and migration management
- Data synchronization across environments
- Query optimization and performance tuning
- Cache management with Redis
- Event sourcing and CQRS patterns
- Data integrity validation and repair
- Automated backup and recovery
- Real-time monitoring and alerting

Author: ToolboxAI Team
Created: 2025-09-16
Version: 1.0.0
"""

from .base_database_agent import BaseDatabaseAgent, DatabaseAgentConfig, DatabaseOperation, DatabaseHealth
from .database_agents import (
    SchemaManagementAgent,
    DataSynchronizationAgent,
    QueryOptimizationAgent,
    CacheManagementAgent
)
from .advanced_agents import (
    EventSourcingAgent,
    DataIntegrityAgent,
    BackupRecoveryAgent,
    MonitoringAgent
)
from .supervisor_agent import DatabaseSupervisorAgent
from .workflow import DatabaseWorkflow, run_database_workflow

__all__ = [
    "BaseDatabaseAgent",
    "DatabaseAgentConfig",
    "DatabaseOperation",
    "DatabaseHealth",
    "SchemaManagementAgent",
    "DataSynchronizationAgent",
    "QueryOptimizationAgent",
    "CacheManagementAgent",
    "EventSourcingAgent",
    "DataIntegrityAgent",
    "BackupRecoveryAgent",
    "MonitoringAgent",
    "DatabaseSupervisorAgent",
    "DatabaseWorkflow",
    "run_database_workflow",
]

__version__ = "1.0.0"