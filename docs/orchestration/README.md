# Orchestration System Architecture
*Unified orchestrator consolidation completed September 26, 2025*

## Overview

The ToolBoxAI orchestration system has been completely refactored into a unified, modular architecture that eliminates redundancy while providing a clear hierarchy of specialized orchestration capabilities.

## Architecture

```
                    ┌─────────────────────────────┐
                    │    UnifiedOrchestrator      │
                    │  (Core Orchestration API)   │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │     MasterOrchestrator      │
                    │  (Task Management & Agents) │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐
│   Roblox    │         │   Educational   │         │   GitHub    │
│ Orchestration│         │  Orchestration  │         │Orchestration│
│   Module    │         │     Module      │         │   Module    │
└─────────────┘         └─────────────────┘         └─────────────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐
│Error Handling│         │      SPARC      │         │             │
│Orchestration │         │  Orchestration  │         │             │
│   Module    │         │     Module      │         │             │
└─────────────┘         └─────────────────┘         └─────────────┘
```

## Core Components

### 1. UnifiedOrchestrator (`core/orchestration/`)
**Primary entry point** for all orchestration operations.

```python
from core.orchestration import create_orchestrator

# Create and start orchestrator
orchestrator = create_orchestrator()
await orchestrator.start()

# Submit domain-specific tasks
task_id = await orchestrator.submit_task(
    domain="roblox",
    workflow_type="full_environment",
    subject="Math",
    grade_level="5"
)

# Get system status
status = await orchestrator.get_system_status()
await orchestrator.stop()
```

### 2. MasterOrchestrator (`core/agents/master_orchestrator.py`)
**Task management and agent coordination** - the operational core.

- **Agent Management**: Manages pools of specialized agents
- **Task Distribution**: Intelligent task routing and load balancing
- **Resource Monitoring**: Tracks system health and performance
- **Auto-scaling**: Dynamic agent pool management

### 3. Domain-Specific Modules

#### Roblox Orchestration Module (`core/orchestration/roblox/`)
Combines Roblox environment generation and project management.

```python
roblox_module = orchestrator.get_module("roblox")

# Generate complete educational environment
result = await roblox_module.generate_environment(
    subject="Science",
    grade_level="8",
    learning_objectives=["Understand photosynthesis"]
)

# Review Lua code
review = await roblox_module.review_code(code, "lua")
```

**Features:**
- Environment orchestration (from original `orchestrator.py`)
- Project orchestration (from `roblox_orchestrator.py`)
- Agent coordination for Roblox workflows
- Quiz and gamification systems

#### Educational Orchestration Module (`core/orchestration/educational/`)
Natural language understanding and adaptive learning.

```python
edu_module = orchestrator.get_module("educational")

# Process natural language interaction
response = await edu_module.process_interaction(
    user_input="Create a quiz about ancient history",
    session_id="session_123"
)

# Create structured lessons
lesson = await edu_module.create_lesson(
    subject="History",
    grade_level="9"
)
```

**Features:**
- Conversational agent coordination (from `orchestration_controller.py`)
- NLU and context management
- Educational agent swarm orchestration
- Session and conversation management

#### GitHub Orchestration Module (`core/orchestration/github/`)
Git operations and repository management.

```python
github_module = orchestrator.get_module("github")

# Pre-commit checks
result = await github_module.pre_commit_check(files=["file.py"])

# Repository health monitoring
health = await github_module.health_check()

# Deployment preparation
deploy_ready = await github_module.prepare_deployment()
```

**Features:**
- LangGraph workflow execution (from `github_agents/orchestrator.py`)
- Large file detection and LFS migration
- Repository health monitoring
- Deployment preparation

#### Error Handling Orchestration Module (`core/orchestration/error_handling/`)
Testing, recovery, and system health management.

```python
error_module = orchestrator.get_module("error_handling")

# Execute comprehensive tests
test_results = await error_module.execute_tests()

# Automatic error recovery
recovery = await error_module.attempt_recovery(error_data)

# System health monitoring
health = await error_module.monitor_health()
```

**Features:**
- Integrated testing orchestration (from `testing_orchestrator_agent.py`)
- Auto-recovery workflows (from `auto_recovery_orchestrator_agent.py`)
- System health monitoring and remediation

#### SPARC Orchestration Module (`core/orchestration/sparc/`)
SPARC methodology implementation for development workflows.

```python
sparc_module = orchestrator.get_module("sparc")

# Full SPARC workflow
result = await sparc_module.execute_full_sparc(requirements)

# Individual phases
spec = await sparc_module.create_specification(requirements)
arch = await sparc_module.design_architecture(spec, pseudocode)
```

**Features:**
- SPARC methodology workflows (from `enhanced_orchestrator.py`)
- Architecture-driven development
- Code generation and refinement

## API Reference

### Core Orchestration

```python
# Factory function
from core.orchestration import create_orchestrator, OrchestratorConfig

config = OrchestratorConfig(
    max_agents_per_type=5,
    enable_health_checks=True,
    health_check_interval=30
)

orchestrator = create_orchestrator(config)
```

### Domain Module Access

```python
# Get specific module
module = orchestrator.get_module("domain_name")

# Submit task to domain
task_id = await orchestrator.submit_task(
    domain="domain_name",
    **task_parameters
)

# Get system-wide status
status = await orchestrator.get_system_status()
```

### Backward Compatibility

```python
# Legacy import (shows deprecation warning)
from core.agents.orchestrator_compat import Orchestrator

# Still works with original API
orch = Orchestrator()
result = await orch.generate_environment(...)
```

## Migration Status

### ✅ Completed
- **Unified Architecture**: Single entry point with modular design
- **Domain Modules**: All specialized orchestration grouped logically
- **Backward Compatibility**: Legacy APIs still work with warnings
- **Archive**: All redundant files safely archived
- **Documentation**: Complete migration guide and API docs

### 🔄 In Progress
- **Integration Testing**: Comprehensive test suite validation
- **Performance Optimization**: Module-specific performance tuning
- **Advanced Features**: Cross-domain workflow orchestration

### 📋 Future Enhancements
- **Cross-Domain Workflows**: Tasks spanning multiple domains
- **Dynamic Module Loading**: Runtime module management
- **Enhanced Analytics**: Detailed orchestration metrics
- **Plugin System**: Third-party orchestration modules

## Archived Files

All archived orchestrator files are preserved in:
`Archive/2025-09-26/core-orchestrators/`

### Archived Components
1. `task_orchestrator.py` → Integrated into MasterOrchestrator
2. `testing_orchestrator_agent.py` → Error Handling Module
3. `auto_recovery_orchestrator_agent.py` → Error Handling Module
4. `worktree_orchestrator_agent.py` → GitHub Module
5. `enhanced_orchestrator.py` → SPARC Module

## Benefits

### 🎯 **Reduced Complexity**
- Eliminated 5+ redundant orchestrator files
- Single entry point for all orchestration
- Clear separation of domain concerns

### 🚀 **Improved Performance**
- Centralized resource management
- Intelligent task distribution
- Auto-scaling agent pools

### 🔧 **Better Maintainability**
- Modular architecture enables independent updates
- Clear import hierarchy prevents circular dependencies
- Standardized APIs across all domains

### 📈 **Enhanced Scalability**
- Easy addition of new domain modules
- Horizontal scaling support
- Resource optimization

### 🛡️ **Backward Compatibility**
- Existing code continues to work
- Gradual migration path
- Deprecation warnings guide updates

## Support

- **Documentation**: See migration guide in archived files
- **Examples**: Check `examples/orchestration/` (to be created)
- **Issues**: GitHub issues for migration problems
- **Timeline**: Backward compatibility maintained for 2-3 releases

## Quick Start

```python
# Modern approach
from core.orchestration import create_orchestrator

async def main():
    # Create orchestrator
    orch = create_orchestrator()
    await orch.start()

    # Use domain-specific modules
    roblox = orch.get_module("roblox")
    result = await roblox.generate_environment(
        subject="Math",
        grade_level="5"
    )

    # Cleanup
    await orch.stop()

# Run
import asyncio
asyncio.run(main())
```

---

*For detailed migration instructions, see: `Archive/2025-09-26/core-orchestrators/ORCHESTRATOR_MIGRATION_GUIDE.md`*