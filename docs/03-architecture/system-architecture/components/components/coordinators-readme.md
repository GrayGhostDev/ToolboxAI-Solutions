# ToolboxAI Coordinator System

Comprehensive high-level coordination system for the ToolboxAI Roblox Environment, providing orchestration of agents, swarm intelligence, SPARC framework, and MCP protocol for educational content generation.

## 🏗️ Architecture Overview

The coordinator system consists of five main components:

1. **Main Coordinator** - Master orchestration hub
2. **Workflow Coordinator** - End-to-end process management
3. **Resource Coordinator** - System resource allocation
4. **Sync Coordinator** - State synchronization and events
5. **Error Coordinator** - Centralized error handling

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install specific coordinator requirements
pip install fastapi uvicorn websockets pydantic langchain psutil pyyaml
```text
### Basic Usage

```python
import asyncio
from coordinators import initialize_coordinators, generate_educational_content

async def main():
    # Initialize coordinator system
    system = await initialize_coordinators()

    # Generate educational content
    result = await generate_educational_content(
        subject="Mathematics",
        grade_level=7,
        learning_objectives=["Fractions", "Decimals"],
        environment_type="interactive_classroom",
        include_quiz=True
    )

    print(f"Content generated: {result.success}")
    print(f"Scripts: {len(result.scripts)}")

    # Shutdown
    await system.shutdown()

# Run
asyncio.run(main())
```text
### Context Manager Usage

```python
from coordinators import coordinator_context

async def generate_content():
    async with coordinator_context() as system:
        main_coordinator = system.get_main_coordinator()

        result = await main_coordinator.generate_educational_content(
            subject="Science",
            grade_level=6,
            learning_objectives=["Solar System", "Planets"]
        )

        return result
```text
## 📊 Component Details

### Main Coordinator

Central orchestration hub that integrates all subsystems:

```python
from coordinators import create_main_coordinator

coordinator = await create_main_coordinator()

# Generate educational content
result = await coordinator.generate_educational_content(
    subject="History",
    grade_level=8,
    learning_objectives=["World War II", "Timeline"],
    environment_type="historical_recreation"
)

# Check system health
health = await coordinator.get_health_status()
print(f"System status: {health.status}")
```text
### Workflow Coordinator

Manages complex multi-step workflows:

```python
from coordinators import create_workflow_coordinator

coordinator = await create_workflow_coordinator()

# Create complete course workflow
workflow_id = await coordinator.create_workflow(
    workflow_type="complete_course_generation",
    parameters={
        'subject': 'Mathematics',
        'grade_level': 9,
        'number_of_lessons': 12
    }
)

# Monitor progress
status = await coordinator.get_workflow_status(workflow_id)
print(f"Progress: {status['progress']}%")
```text
### Resource Coordinator

Manages system resources and API quotas:

```python
from coordinators import create_resource_coordinator

coordinator = await create_resource_coordinator()

# Allocate resources
allocation = await coordinator.allocate_resources(
    request_id="my_request",
    requirements={
        'cpu_cores': 4,
        'memory_mb': 2048,
        'api_quota': 500
    }
)

# Check API quota
available = await coordinator.check_api_quota('openai', 10, 5000)

# Release resources
await coordinator.release_resources("my_request")
```text
### Sync Coordinator

Handles state synchronization and events:

```python
from coordinators import create_sync_coordinator

coordinator = await create_sync_coordinator()

# Register component
await coordinator.register_component(
    'my_component',
    initial_state={'status': 'active'}
)

# Update state
await coordinator.update_component_state(
    'my_component',
    {'status': 'processing', 'task_id': '123'}
)

# Publish event
event_id = await coordinator.publish_event(
    event_type='task_completed',
    source='my_component',
    data={'task_id': '123', 'result': 'success'}
)
```text
### Error Coordinator

Centralized error handling and recovery:

```python
from coordinators import create_error_coordinator

coordinator = await create_error_coordinator()

# Handle error with automatic recovery
try:
    raise ConnectionError("Database connection lost")
except Exception as e:
    error_id = await coordinator.handle_error(
        error_type="connection_error",
        error=e,
        context={'database': 'main'},
        component="database_service"
    )

# Get error summary
summary = await coordinator.get_error_summary(24)  # Last 24 hours
print(f"Errors: {summary['total_errors']}")
print(f"Resolution rate: {summary['resolution_rate']}%")
```text
## 🔧 Configuration

### Environment-based Configuration

```python
from coordinators.config import get_config_for_environment

# Development configuration
dev_config = get_config_for_environment('development')

# Production configuration
prod_config = get_config_for_environment('production')

# Initialize with specific config
system = await initialize_coordinators(dev_config)
```text
### Custom Configuration

```python
from coordinators.config import CoordinatorSystemConfig, MainCoordinatorConfig

config = CoordinatorSystemConfig(
    main=MainCoordinatorConfig(
        max_concurrent_requests=20,
        enable_caching=True
    ),
    environment="production",
    log_level="INFO"
)

system = await initialize_coordinators(config.to_dict())
```text
### Configuration File

Create `coordinator_config.yaml`:

```yaml
environment: development
log_level: INFO

main:
  max_concurrent_requests: 10
  enable_caching: true

resource:
  daily_budget: 50.0
  enable_cost_tracking: true

error:
  enable_notifications: true
  alert_email: 'admin@example.com'
```text
## 🎓 Educational Workflows

### Complete Course Generation

```python
# Create comprehensive course
workflow_id = await workflow_coordinator.create_workflow(
    "complete_course_generation",
    {
        'subject': 'Science',
        'grade_level': 6,
        'course_title': 'Solar System Explorer',
        'number_of_lessons': 8,
        'assessment_frequency': 'per_lesson'
    }
)
```text
### Adaptive Assessment

```python
# Create adaptive assessment
workflow_id = await workflow_coordinator.create_workflow(
    "adaptive_assessment_generation",
    {
        'subject': 'Mathematics',
        'grade_level': 8,
        'student_profiles': [
            {'student_id': '1', 'performance_level': 'high'},
            {'student_id': '2', 'performance_level': 'medium'}
        ]
    }
)
```text
### Real-time Collaboration

```python
# Register collaborative components
await sync_coordinator.register_component('teacher_dashboard')
await sync_coordinator.register_component('student_client')
await sync_coordinator.register_component('roblox_studio')

# Publish lesson update
await sync_coordinator.publish_event(
    event_type='lesson_content_updated',
    source='teacher_dashboard',
    data={'lesson_id': 'lesson_1', 'content_version': 2}
)
```text
## 🔌 API Endpoints

Each coordinator exposes REST API endpoints:

### Main Coordinator (port 8008)

- `POST /generate_content` - Generate educational content
- `GET /health` - System health check
- `GET /metrics` - System metrics

### Workflow Coordinator

- `POST /workflows` - Create workflow
- `GET /workflows/{id}` - Get workflow status
- `POST /workflows/{id}/cancel` - Cancel workflow

### Resource Coordinator

- `POST /allocate` - Allocate resources
- `GET /quota/{service}` - Check API quota
- `GET /status` - Resource status

### Sync Coordinator

- `POST /register` - Register component
- `POST /state/{component_id}` - Update state
- `WebSocket /ws` - Real-time sync

### Error Coordinator

- `POST /errors` - Report error
- `GET /errors` - List errors
- `GET /summary` - Error summary

## 🧪 Testing

### Integration Tests

```bash
# Run integration tests
python coordinators/integration_test.py

# Run performance benchmark
python -c "
import asyncio
from coordinators.integration_test import benchmark_coordinator_system
asyncio.run(benchmark_coordinator_system())
"
```text
### Unit Tests

```bash
# Run with pytest
pytest coordinators/tests/

# With coverage
pytest coordinators/tests/ --cov=coordinators --cov-report=html
```text
## 📈 Monitoring

### Health Monitoring

```python
# Check overall system health
health = await main_coordinator.get_health_status()
print(f"Status: {health.status}")
print(f"Active workflows: {health.active_workflows}")

# Component-specific health
workflow_health = await workflow_coordinator.get_health()
resource_health = await resource_coordinator.get_health()
```text
### Metrics Collection

```python
# Get comprehensive metrics
main_metrics = await main_coordinator.get_health_status()
workflow_metrics = await workflow_coordinator.get_metrics()
resource_metrics = await resource_coordinator.get_metrics()
sync_metrics = await sync_coordinator.get_metrics()
error_metrics = await error_coordinator.get_metrics()
```text
### Performance Optimization

```python
# Get optimization recommendations
optimization = await resource_coordinator.optimize_resource_allocation()
print("Recommendations:")
for rec in optimization['recommendations']:
    print(f"  - {rec}")
```text
## 🚨 Error Handling

### Automatic Recovery

The system includes automatic recovery for common errors:

- **Connection errors**: Automatic retry with exponential backoff
- **Rate limits**: Wait for quota reset
- **Memory issues**: Resource cleanup and garbage collection
- **Service crashes**: Service restart attempts

### Custom Recovery Strategies

```python
# Add custom recovery strategy
async def custom_recovery(error_record, attempt):
    # Your recovery logic here
    return True  # Return True if recovery successful

error_coordinator.recovery_strategies['custom'] = RecoveryStrategy(
    strategy_id='custom',
    name='Custom Recovery',
    applicable_errors=['custom_error'],
    recovery_function=custom_recovery
)
```text
## 🔧 Troubleshooting

### Common Issues

1. **"Coordinator system not initialized"**

   ```python
   # Ensure you call initialize_coordinators() first
   system = await initialize_coordinators()
   ```

2. **"Resource allocation failed"**

   ```python
   # Check system resources
   status = await resource_coordinator.get_resource_status()
   print(status['utilization'])
   ```

3. **"Workflow execution timeout"**
   ```python
   # Increase timeout in workflow configuration
   config = {'workflow': {'default_step_timeout': 600}}
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('coordinators').setLevel(logging.DEBUG)

# Or use debug configuration
from coordinators.config import get_testing_config
debug_config = get_testing_config()
debug_config.log_level = "DEBUG"
```text
## 📝 Contributing

### Adding New Coordinators

1. Create new coordinator class inheriting from base patterns
2. Implement required methods: `initialize()`, `get_health()`, `shutdown()`
3. Add FastAPI routes with `_setup_routes()`
4. Register in `__init__.py`
5. Add configuration class in `config.py`
6. Write tests in `tests/`

### Adding Recovery Strategies

```python
# Add to ErrorCoordinator
async def my_recovery_strategy(error_record, attempt):
    # Recovery logic
    return success_boolean

error_coordinator.recovery_strategies['my_strategy'] = RecoveryStrategy(
    strategy_id='my_strategy',
    name='My Recovery Strategy',
    applicable_errors=['my_error_type'],
    recovery_function=my_recovery_strategy
)
```text
## 📋 Best Practices

1. **Always use context managers** for automatic cleanup
2. **Monitor resource utilization** to prevent exhaustion
3. **Handle errors gracefully** with appropriate severity levels
4. **Use workflow templates** for common educational scenarios
5. **Enable caching** for improved performance
6. **Configure proper logging** for debugging
7. **Set up monitoring alerts** for production usage
8. **Regular health checks** to ensure system stability

## 🎯 Educational Use Cases

### Classroom Management

- Real-time lesson synchronization
- Student progress tracking
- Adaptive content delivery

### Course Creation

- Multi-lesson course generation
- Assessment integration
- Learning outcome tracking

### Collaborative Learning

- Multi-user environment synchronization
- Shared workspace management
- Real-time collaboration events

### Performance Analytics

- Learning outcome measurement
- Content effectiveness analysis
- Student engagement metrics

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://docs.langchain.com/)
- [LangGraph Guide](https://langchain-ai.github.io/langgraph/)
- [WebSocket Protocol](https://websockets.readthedocs.io/)
- [Roblox Developer Hub](https://developer.roblox.com/)

---

_ToolboxAI Coordinator System v1.0.0_  
_Comprehensive orchestration for educational AI systems_
