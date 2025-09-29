# Orchestrator Migration Guide
*September 26, 2025*

## Overview

The orchestrator consolidation has been completed. All orchestrator functionality has been reorganized under a unified architecture with the MasterOrchestrator as the top-level entry point and domain-specific modules for specialized workflows.

## New Architecture

```
core/orchestration/
├── __init__.py                    # UnifiedOrchestrator, factory functions
├── roblox/                        # Roblox environment & project orchestration
│   └── __init__.py
├── educational/                   # Educational swarm orchestration
│   └── __init__.py
├── github/                        # GitHub workflow orchestration
│   └── __init__.py
├── error_handling/                # Testing & recovery orchestration
│   └── __init__.py
└── sparc/                         # SPARC methodology orchestration
    └── __init__.py
```

## Migration Paths

### For Production Code

#### Old Import (Deprecated):
```python
from core.agents.orchestrator import Orchestrator, OrchestrationRequest
```

#### New Import (Recommended):
```python
from core.orchestration import UnifiedOrchestrator, create_orchestrator
from core.orchestration.roblox import RobloxOrchestrationModule
```

#### Backward Compatible (Temporary):
```python
from core.agents.orchestrator_compat import Orchestrator  # Shows deprecation warning
```

### For Specific Domains

#### Roblox Development:
```python
# Old
from core.agents.orchestrator import Orchestrator

# New
from core.orchestration import create_orchestrator
orchestrator = create_orchestrator()
roblox_module = orchestrator.get_module("roblox")
```

#### Educational Content:
```python
# Old
from core.swarm.orchestration_controller import OrchestrationController

# New
from core.orchestration import create_orchestrator
orchestrator = create_orchestrator()
educational_module = orchestrator.get_module("educational")
```

#### GitHub Operations:
```python
# Old
from core.agents.github_agents.orchestrator import GitHubAgentOrchestrator

# New
from core.orchestration import create_orchestrator
orchestrator = create_orchestrator()
github_module = orchestrator.get_module("github")
```

## API Changes

### UnifiedOrchestrator API

```python
# Create orchestrator
from core.orchestration import create_orchestrator, OrchestratorConfig

config = OrchestratorConfig(
    max_agents_per_type=5,
    enable_health_checks=True
)
orchestrator = create_orchestrator(config)

# Start orchestrator
await orchestrator.start()

# Submit tasks to specific domains
task_id = await orchestrator.submit_task(
    domain="roblox",
    workflow_type="full_environment",
    subject="Math",
    grade_level="5",
    learning_objectives=["Learn fractions"]
)

# Get system status
status = await orchestrator.get_system_status()

# Stop orchestrator
await orchestrator.stop()
```

### Domain-Specific APIs

#### Roblox Module:
```python
roblox_module = orchestrator.get_module("roblox")

# Generate environment (maintains original API)
result = await roblox_module.generate_environment(
    subject="Science",
    grade_level="8",
    learning_objectives=["Understand photosynthesis"]
)

# Review code (maintains original API)
review_result = await roblox_module.review_code(
    code="print('Hello Roblox')",
    language="lua"
)
```

#### Educational Module:
```python
educational_module = orchestrator.get_module("educational")

# Process interaction (maintains original API)
response = await educational_module.process_interaction(
    user_input="Create a quiz about ancient history",
    session_id="session_123"
)

# Create lesson
lesson = await educational_module.create_lesson(
    subject="History",
    grade_level="9",
    learning_objectives=["Understand Roman Empire"]
)
```

## Breaking Changes

### Removed Files
These files have been archived and their functionality integrated:

1. `core/coordinators/task_orchestrator.py` → Use MasterOrchestrator
2. `core/agents/error_handling/testing_orchestrator_agent.py` → Use error_handling module
3. `core/agents/error_handling/auto_recovery_orchestrator_agent.py` → Use error_handling module
4. `core/agents/github_agents/worktree_orchestrator_agent.py` → Use github module
5. `core/sparc/enhanced_orchestrator.py` → Use sparc module

### Changed Imports
Update these imports in your code:

```python
# OLD - Will show deprecation warnings
from core.agents.orchestrator import Orchestrator
from core.coordinators.task_orchestrator import app
from core.agents.error_handling.testing_orchestrator_agent import TestingOrchestratorAgent

# NEW
from core.orchestration import UnifiedOrchestrator, create_orchestrator
from core.agents.master_orchestrator import MasterOrchestrator  # For direct access
from core.orchestration.error_handling import ErrorHandlingOrchestrationModule
```

## Migration Timeline

### Phase 1: Backward Compatibility (Current)
- All old imports work with deprecation warnings
- New imports available alongside old ones
- No breaking changes to existing APIs

### Phase 2: Transition (Next Release)
- Deprecation warnings become more prominent
- Documentation updated to show new patterns
- New features only available in new architecture

### Phase 3: Cleanup (2-3 Releases)
- Remove backward compatibility layers
- Archive old files completely
- All code uses new architecture

## Testing

### Running Tests with New Architecture

```bash
# Test the unified orchestrator
python -c "
from core.orchestration import create_orchestrator
import asyncio

async def test():
    orch = create_orchestrator()
    await orch.start()
    status = await orch.get_system_status()
    print('System Status:', status['overall_health'])
    await orch.stop()

asyncio.run(test())
"
```

### Validate Migration

```bash
# Check for deprecated imports in your code
grep -r "from core.agents.orchestrator import" --include="*.py" .
grep -r "from core.coordinators.task_orchestrator import" --include="*.py" .

# These should be updated to use new imports
```

## Common Migration Patterns

### 1. Simple Orchestrator Usage
```python
# Before
from core.agents.orchestrator import Orchestrator
orch = Orchestrator()
result = await orch.generate_environment(subject="Math", grade_level="5")

# After
from core.orchestration import create_orchestrator
orch = create_orchestrator()
await orch.start()
roblox_module = orch.get_module("roblox")
result = await roblox_module.generate_environment(subject="Math", grade_level="5")
await orch.stop()
```

### 2. Task Orchestration
```python
# Before
from core.coordinators.task_orchestrator import reg
task = reg.claim("worker_id")

# After
from core.orchestration import create_orchestrator
orch = create_orchestrator()
await orch.start()
task_id = await orch.submit_task(domain="educational", task_data={...})
status = await orch.master.get_task_status(task_id)
```

### 3. Educational Interactions
```python
# Before
from core.swarm.orchestration_controller import OrchestrationController
controller = OrchestrationController()
result = await controller.process_interaction("Create a lesson")

# After
from core.orchestration import create_orchestrator
orch = create_orchestrator()
await orch.start()
edu_module = orch.get_module("educational")
result = await edu_module.process_interaction("Create a lesson")
```

## Benefits of New Architecture

1. **Unified Entry Point**: Single orchestrator manages all domains
2. **Better Organization**: Clear separation of domain-specific logic
3. **Reduced Redundancy**: Eliminated 5+ duplicate orchestrator files
4. **Improved Scalability**: Easier to add new domain modules
5. **Better Testing**: Modular architecture enables better unit testing
6. **Resource Management**: Centralized resource monitoring and management

## Support

- **Documentation**: See `docs/orchestration/` for detailed guides
- **Examples**: Check `examples/orchestration/` for usage patterns
- **Issues**: Create GitHub issues for migration problems
- **Backward Compatibility**: Will be maintained for 2-3 releases

## Archive Location

All archived orchestrator files are located in:
`Archive/2025-09-26/core-orchestrators/`

These files are preserved for reference and can be restored if needed during the transition period.