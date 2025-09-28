# ToolBoxAI Celery Workers Documentation

## Overview

This implementation provides a comprehensive Celery background job system for the ToolBoxAI platform with enterprise-grade features:

- **Multi-tenancy** with organization context isolation
- **Redis-based** message broker and result backend (NO AWS dependencies)
- **Self-hosted monitoring** with Prometheus and Flower
- **Production-ready security** with non-root containers
- **Comprehensive task types** for all platform operations

## Features

### 🔐 Security & Multi-tenancy
- **Tenant isolation**: Tasks execute with proper organization context
- **Non-root containers**: All services run as unprivileged users
- **Resource limits**: CPU and memory constraints prevent resource exhaustion
- **Read-only filesystems**: Where possible, containers use read-only root

### 📊 Monitoring & Observability
- **Flower Dashboard**: Real-time task monitoring at port 5555
- **Prometheus Metrics**: Custom metrics exporter at port 9540
- **Structured Logging**: JSON-formatted logs with tenant context
- **Health Checks**: Comprehensive container health monitoring

### 🚀 Performance & Reliability
- **Redis Cluster Support**: Horizontal scaling with Redis clustering
- **Priority Queues**: High/low priority task routing
- **Dead Letter Queue**: Failed task handling and analysis
- **Exponential Backoff**: Smart retry logic with jitter

### 📧 Task Categories

#### Content Tasks (`apps/backend/workers/tasks/content_tasks.py`)
- AI content generation with OpenAI
- Quiz generation and validation
- Content quality analysis
- Batch content processing

#### Email Tasks (`apps/backend/workers/tasks/email_tasks.py`)
- SMTP email sending (SendGrid/SMTP, not AWS SES)
- Template rendering with Jinja2
- Bulk email processing with rate limiting
- Bounce and complaint handling

#### Analytics Tasks (`apps/backend/workers/tasks/analytics_tasks.py`)
- Usage metrics aggregation to PostgreSQL
- Daily/weekly report generation
- Data export in multiple formats
- Performance monitoring

#### Roblox Tasks (`apps/backend/workers/tasks/roblox_tasks.py`)
- Environment synchronization
- Asset deployment and validation
- API endpoint monitoring
- Integration health checks

#### Cleanup Tasks (`apps/backend/workers/tasks/cleanup_tasks.py`)
- File system cleanup with retention policies
- Database maintenance operations
- Session cleanup and optimization
- Dead letter queue management

#### Tenant Tasks (`apps/backend/workers/tasks/tenant_tasks.py`)
- Organization-specific reporting
- Usage tracking and billing sync
- Data backup and archival
- Health monitoring per tenant

## Architecture

### Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Celery Beat   │    │ Celery Workers  │    │    Redis        │
│   Scheduler     │◄──►│   (Multiple)    │◄──►│   Broker        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Flower       │    │   PostgreSQL    │    │   Prometheus    │
│   Monitoring    │    │    Database     │    │    Metrics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Queue Structure

- **high_priority**: Critical tasks (notifications, health checks)
- **default**: General purpose tasks
- **low_priority**: Maintenance and cleanup tasks
- **email**: Email sending and processing
- **analytics**: Data aggregation and reporting
- **ai_generation**: AI content generation tasks
- **roblox**: Roblox integration tasks
- **tenant_operations**: Organization-specific operations

## Quick Start

### 1. Docker Deployment (Recommended)

```bash
# Start all Celery services
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.celery.yml up -d

# Monitor logs
docker compose logs -f celery-worker celery-beat flower
```

### 2. Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="postgresql://user:pass@localhost/db"
export OPENAI_API_KEY="your-key"
export SENDGRID_API_KEY="your-key"

# Start Redis (required)
redis-server

# Start Celery worker
celery -A apps.backend.workers.celery_app worker --loglevel=INFO

# Start Celery beat (in another terminal)
celery -A apps.backend.workers.celery_app beat --loglevel=INFO

# Start Flower monitoring (optional)
celery -A apps.backend.workers.celery_app flower --port=5555
```

### 3. Configuration

Key environment variables:

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_CLUSTER_ENABLED=false
REDIS_CLUSTER_NODES=

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_POOL=prefork
CELERY_LOG_LEVEL=INFO

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
FLOWER_ENABLED=true
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:password

# Email Configuration
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@toolboxai.com
```

## API Usage

### Task Submission

```python
import requests

# Submit a content generation task
response = requests.post('/api/v1/tasks/submit', json={
    'task_type': 'content_generation',
    'task_data': {
        'topic': 'Mathematics',
        'grade_level': '5th Grade',
        'content_type': 'lesson'
    },
    'organization_id': 'org-123',
    'priority': 8
})

task_id = response.json()['task_id']
```

### Task Status Checking

```python
# Check task status
response = requests.get(f'/api/v1/tasks/task/{task_id}')
status = response.json()

print(f"Status: {status['status']}")
if status['status'] == 'SUCCESS':
    print(f"Result: {status['result']}")
```

### Bulk Task Submission

```python
# Submit multiple tasks
response = requests.post('/api/v1/tasks/bulk-submit', json={
    'execution_mode': 'parallel',
    'tasks': [
        {
            'task_type': 'content_generation',
            'task_data': {'topic': 'Science', 'grade_level': '3rd Grade'},
            'organization_id': 'org-123'
        },
        {
            'task_type': 'quiz_generation',
            'task_data': {'content_id': 'content-456'},
            'organization_id': 'org-123'
        }
    ]
})
```

### Tenant-Specific Tasks

```python
# Submit tenant task
response = requests.post('/api/v1/tasks/tenant/org-123', json={
    'task_type': 'usage_report',
    'parameters': {
        'report_type': 'daily_summary',
        'include_analytics': True
    }
})
```

## Monitoring

### Flower Dashboard

Access the Flower dashboard at http://localhost:5555 (default credentials: admin/password)

Features:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Queue management
- Worker management

### Prometheus Metrics

Metrics available at http://localhost:9540/metrics:

- `celery_tasks_total`: Task execution counters
- `celery_task_duration_seconds`: Task execution times
- `celery_active_workers`: Number of active workers
- `celery_queue_length`: Tasks in each queue

### API Endpoints

- `GET /api/v1/tasks/status` - System status
- `GET /api/v1/tasks/workers` - Worker information
- `GET /api/v1/tasks/metrics` - Task metrics
- `GET /api/v1/tasks/queue-stats` - Queue statistics

## Production Deployment

### Security Checklist

- [ ] Use secure Redis password
- [ ] Configure Flower authentication
- [ ] Set resource limits on containers
- [ ] Enable TLS for Redis connections
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure backup for Redis data

### Scaling Guidelines

#### Horizontal Scaling
```bash
# Scale workers
docker compose up --scale celery-worker=4

# Scale with different configurations
docker compose -f docker-compose.yml \
               -f docker-compose.celery.yml \
               -f docker-compose.scale.yml up -d
```

#### Redis Clustering
```bash
# Enable Redis cluster mode
export REDIS_CLUSTER_ENABLED=true
export REDIS_CLUSTER_NODES="redis1:6379,redis2:6379,redis3:6379"
```

### Performance Tuning

#### Worker Configuration
```bash
# CPU-bound tasks
CELERY_WORKER_POOL=prefork
CELERY_WORKER_CONCURRENCY=4

# I/O-bound tasks
CELERY_WORKER_POOL=gevent
CELERY_WORKER_CONCURRENCY=100
```

#### Memory Management
```bash
# Restart workers after processing N tasks (prevents memory leaks)
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Limit memory per worker
docker compose up --memory="1g" celery-worker
```

## Troubleshooting

### Common Issues

#### Workers Not Starting
```bash
# Check Redis connectivity
redis-cli ping

# Check worker logs
docker compose logs celery-worker

# Verify configuration
celery -A apps.backend.workers.celery_app inspect ping
```

#### Tasks Stuck in Queue
```bash
# Check queue lengths
celery -A apps.backend.workers.celery_app inspect active

# Purge queues if needed
celery -A apps.backend.workers.celery_app purge
```

#### Memory Issues
```bash
# Monitor worker memory usage
docker stats celery-worker

# Check for memory leaks
celery -A apps.backend.workers.celery_app inspect memdump
```

### Log Analysis

```bash
# View structured logs
docker compose logs celery-worker | jq .

# Filter by tenant
docker compose logs celery-worker | grep "org-123"

# Monitor task failures
docker compose logs celery-worker | grep "ERROR"
```

## Development

### Adding New Task Types

1. Create task function in appropriate module:
```python
@shared_task(bind=True, name="tasks.my_new_task")
def my_new_task(self, param1: str, organization_id: str = None):
    # Set tenant context
    if organization_id:
        self.set_tenant_context(organization_id)

    # Task implementation
    return {"status": "success", "result": "data"}
```

2. Add to task mapping in API:
```python
task_map = {
    # ... existing tasks
    "my_new_task": my_new_task
}
```

3. Add to auto-discovery in celery_app.py:
```python
app.autodiscover_tasks([
    # ... existing modules
    "apps.backend.workers.tasks.my_module"
])
```

### Testing

```bash
# Run task tests
pytest apps/backend/workers/tests/

# Test specific task
python -c "
from apps.backend.workers.tasks.content_tasks import generate_educational_content
result = generate_educational_content.delay({'topic': 'Test'})
print(result.get())
"
```

## Support

### Getting Help

1. Check logs for error messages
2. Verify Redis connectivity
3. Ensure all environment variables are set
4. Check Flower dashboard for task status
5. Review Prometheus metrics for system health

### Useful Commands

```bash
# Check worker status
celery -A apps.backend.workers.celery_app status

# Inspect active tasks
celery -A apps.backend.workers.celery_app inspect active

# Get worker statistics
celery -A apps.backend.workers.celery_app inspect stats

# Monitor task events
celery -A apps.backend.workers.celery_app events

# Shell for debugging
celery -A apps.backend.workers.celery_app shell
```

---

For more information, see the [official Celery documentation](https://docs.celeryq.dev/) and [Redis documentation](https://redis.io/documentation).