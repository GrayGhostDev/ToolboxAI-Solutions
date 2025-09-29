# Celery Background Job System Documentation

> **Version**: 1.0.0
> **Last Updated**: 2025-01-27
> **Status**: Implementation Complete ✅
> **Infrastructure**: Self-hosted with Redis (No AWS Dependencies)

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Task Implementation](#task-implementation)
5. [Worker Configuration](#worker-configuration)
6. [Monitoring & Observability](#monitoring--observability)
7. [API Integration](#api-integration)
8. [Docker Deployment](#docker-deployment)
9. [Security Considerations](#security-considerations)
10. [Performance Optimization](#performance-optimization)
11. [Troubleshooting](#troubleshooting)

## Overview

The ToolBoxAI platform implements a robust background job processing system using Celery 5.3+ with Redis as both message broker and result backend. This architecture provides asynchronous task execution without any AWS dependencies (no SQS, Lambda, or CloudWatch).

### Key Features
- **Self-Hosted Infrastructure**: Complete control with Redis broker
- **Multi-Tenant Support**: Organization-aware task execution
- **Priority Queues**: Task prioritization and routing
- **Monitoring Dashboard**: Flower for real-time monitoring
- **Retry Logic**: Exponential backoff with dead letter queues
- **Periodic Tasks**: Celery Beat for scheduled operations

### Technology Stack
- **Task Queue**: Celery 5.3.6
- **Message Broker**: Redis 7+ (not AWS SQS)
- **Result Backend**: Redis (not DynamoDB)
- **Monitoring**: Flower + Prometheus (not CloudWatch)
- **Scheduler**: Celery Beat (not CloudWatch Events)
- **Email**: SMTP/SendGrid (not AWS SES)

## Architecture

### System Architecture
```
┌─────────────────────────────────────────────────┐
│              API Request                         │
│                   ↓                              │
│         FastAPI Task Endpoint                    │
│                   ↓                              │
│          Submit Task to Queue                    │
│                   ↓                              │
│      Redis Message Broker (No AWS SQS)           │
│                   ↓                              │
│         Celery Worker Pool                       │
│         (With Tenant Context)                    │
│                   ↓                              │
│          Execute Task Logic                      │
│                   ↓                              │
│      Store Result in Redis Backend               │
│                   ↓                              │
│       Return Task ID to Client                   │
└─────────────────────────────────────────────────┘
```

### Queue Architecture
```
Redis Queues:
├── default         # Standard priority tasks
├── high_priority   # Urgent tasks (content generation)
├── low_priority    # Batch operations
├── email          # Email sending
├── analytics      # Data aggregation
├── ai_generation  # AI/ML tasks
├── roblox         # Roblox sync operations
├── tenant_ops     # Organization management
└── dead_letter    # Failed tasks for analysis
```

## Installation & Setup

### Requirements
```bash
# Add to requirements.txt
celery[redis]==5.3.6
flower==2.0.1
redis==5.0.1
prometheus-client==0.20.0
kombu==5.3.5
```

### Environment Configuration
```bash
# .env configuration (NO AWS KEYS NEEDED)
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_WORKER_CONCURRENCY=4
CELERY_LOG_LEVEL=INFO

# Email configuration (not AWS SES)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SENDGRID_API_KEY=your-sendgrid-key

# Monitoring (not CloudWatch)
FLOWER_PORT=5555
PROMETHEUS_PORT=9540
```

## Task Implementation

### Task Module Structure
```
apps/backend/workers/
├── __init__.py
├── celery_app.py          # Celery application instance
├── config.py              # Worker configuration
├── beat_schedule.py       # Periodic task schedules
└── tasks/
    ├── __init__.py
    ├── content_tasks.py   # AI content generation
    ├── email_tasks.py     # Email sending (SMTP)
    ├── analytics_tasks.py # Data aggregation
    ├── roblox_tasks.py   # Roblox operations
    ├── cleanup_tasks.py  # Maintenance
    └── tenant_tasks.py   # Organization management
```

### Example Task Implementation

#### Content Generation Task
```python
# apps/backend/workers/tasks/content_tasks.py
from celery import shared_task, Task
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TenantAwareTask(Task):
    """Base task class with tenant context"""

    def __call__(self, *args, organization_id: str = None, **kwargs):
        # Set tenant context for database queries
        if organization_id:
            self.request.organization_id = organization_id
        return self.run(*args, **kwargs)

@shared_task(
    bind=True,
    base=TenantAwareTask,
    name='content.generate_lesson',
    queue='ai_generation',
    max_retries=3,
    default_retry_delay=60
)
def generate_lesson_content(
    self,
    topic: str,
    grade_level: str,
    organization_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Generate educational content using OpenAI (not AWS Bedrock)"""
    try:
        logger.info(f"Generating lesson for org {organization_id}: {topic}")

        # Use OpenAI API (not AWS Bedrock)
        from openai import OpenAI
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational content creator."},
                {"role": "user", "content": f"Create a lesson about {topic} for {grade_level}"}
            ]
        )

        # Store in PostgreSQL (not DynamoDB)
        content = response.choices[0].message.content

        return {
            'status': 'success',
            'content': content,
            'organization_id': organization_id
        }

    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

#### Email Task (No AWS SES)
```python
# apps/backend/workers/tasks/email_tasks.py
@shared_task(
    name='email.send_transactional',
    queue='email',
    rate_limit='100/m'  # Rate limiting
)
def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    organization_id: str
) -> bool:
    """Send email using SMTP/SendGrid (not AWS SES)"""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email='noreply@toolboxai.com',
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise
```

### Periodic Tasks with Celery Beat

```python
# apps/backend/workers/beat_schedule.py
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'generate-daily-reports': {
        'task': 'analytics.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'options': {'queue': 'analytics'}
    },
    'cleanup-old-tasks': {
        'task': 'cleanup.remove_old_tasks',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
        'options': {'queue': 'low_priority'}
    },
    'check-tenant-usage': {
        'task': 'tenant.check_usage_limits',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'queue': 'tenant_ops'}
    }
}
```

## Worker Configuration

### Celery Application Configuration
```python
# apps/backend/workers/celery_app.py
from celery import Celery
from kombu import Queue, Exchange
import os

# Create Celery app
app = Celery('toolboxai')

# Configure with Redis (not AWS)
app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/1'),

    # Task configuration
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Performance settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Dead letter queue
    task_dead_letter_queue='dead_letter',
    task_dead_letter_routing_key='dead_letter',
)

# Define queues with priorities
app.conf.task_routes = {
    'content.*': {'queue': 'ai_generation', 'priority': 8},
    'email.*': {'queue': 'email', 'priority': 6},
    'analytics.*': {'queue': 'analytics', 'priority': 4},
    'cleanup.*': {'queue': 'low_priority', 'priority': 2},
}

# Queue configuration
app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('high_priority', Exchange('high_priority'), routing_key='high_priority', priority=10),
    Queue('low_priority', Exchange('low_priority'), routing_key='low_priority', priority=1),
    Queue('email', Exchange('email'), routing_key='email'),
    Queue('ai_generation', Exchange('ai_generation'), routing_key='ai_generation'),
    Queue('dead_letter', Exchange('dead_letter'), routing_key='dead_letter'),
)
```

## Monitoring & Observability

### Flower Dashboard (Not AWS CloudWatch)

Start Flower for real-time monitoring:
```bash
# Start Flower dashboard
celery -A apps.backend.workers.celery_app flower \
    --port=5555 \
    --broker=$REDIS_URL \
    --basic_auth=admin:secure_password
```

Access dashboard at: http://localhost:5555

### Prometheus Metrics

Export metrics for Grafana dashboards:
```python
# apps/backend/workers/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import prometheus_client

# Define metrics
task_counter = Counter('celery_tasks_total', 'Total tasks', ['task_name', 'status'])
task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
queue_size = Gauge('celery_queue_size', 'Queue size', ['queue_name'])

# Start metrics server
prometheus_client.start_http_server(9540)
```

### Structured Logging

```python
# Structured logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}
```

## API Integration

### Task Submission Endpoints

```python
# apps/backend/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import uuid

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

@router.post("/submit")
async def submit_task(
    task_type: str,
    task_data: Dict[str, Any],
    priority: int = 5,
    current_org = Depends(get_current_organization),
    current_user = Depends(get_current_user)
) -> Dict[str, str]:
    """Submit async task to Celery"""

    task_id = str(uuid.uuid4())

    # Route to appropriate task
    if task_type == "content_generation":
        from apps.backend.workers.tasks.content_tasks import generate_lesson_content
        task = generate_lesson_content.apply_async(
            kwargs={
                **task_data,
                'organization_id': current_org.id,
                'user_id': current_user.id
            },
            task_id=task_id,
            priority=priority
        )
    elif task_type == "send_email":
        from apps.backend.workers.tasks.email_tasks import send_email
        task = send_email.apply_async(
            kwargs={**task_data, 'organization_id': current_org.id},
            task_id=task_id
        )
    else:
        raise HTTPException(400, f"Unknown task type: {task_type}")

    return {
        'task_id': task.id,
        'status': 'submitted'
    }

@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_org = Depends(get_current_organization)
) -> Dict[str, Any]:
    """Check task status"""
    from apps.backend.workers.celery_app import app

    result = app.AsyncResult(task_id)

    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result if result.ready() else None,
        'info': result.info
    }
```

## Docker Deployment

### Docker Compose Configuration
```yaml
# infrastructure/docker/compose/docker-compose.celery.yml

services:
  # Celery Worker
  celery-worker:
    image: toolboxai/celery:latest
    container_name: toolboxai-celery-worker
    user: "1005:1005"  # Non-root
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    command: celery -A apps.backend.workers.celery_app worker
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD", "celery", "inspect", "ping"]

  # Celery Beat Scheduler
  celery-beat:
    image: toolboxai/celery:latest
    container_name: toolboxai-celery-beat
    user: "1006:1006"  # Non-root
    command: celery -A apps.backend.workers.celery_app beat
    depends_on:
      - redis

  # Flower Monitoring
  flower:
    image: toolboxai/celery:latest
    container_name: toolboxai-flower
    user: "1007:1007"  # Non-root
    ports:
      - "5555:5555"
    command: celery -A apps.backend.workers.celery_app flower
    environment:
      FLOWER_BASIC_AUTH: admin:${FLOWER_PASSWORD}
```

### Deployment Commands
```bash
# Start all services
docker compose -f docker-compose.yml \
               -f docker-compose.celery.yml up -d

# Scale workers
docker compose -f docker-compose.yml \
               -f docker-compose.celery.yml \
               scale celery-worker=4

# Monitor logs
docker compose logs -f celery-worker celery-beat

# Access Flower dashboard
open http://localhost:5555
```

## Security Considerations

### Task Security
1. **Input Validation**: Validate all task inputs
2. **Rate Limiting**: Implement per-organization rate limits
3. **Authentication**: Verify user/organization context
4. **Encryption**: Use TLS for Redis connections in production
5. **Secrets Management**: Use environment variables, not hardcoded values

### Redis Security
```bash
# Redis configuration for production
requirepass ${REDIS_PASSWORD}
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

### Worker Security
- Run workers as non-root users (UID 1005-1007)
- Use read-only filesystems where possible
- Implement resource limits
- Enable task timeouts

## Performance Optimization

### Worker Optimization
```python
# Optimal worker configuration
CELERY_WORKER_CONCURRENCY = 4  # Number of worker processes
CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # Tasks to prefetch
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart after N tasks
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit
```

### Redis Optimization
```python
# Connection pooling
from redis import ConnectionPool

redis_pool = ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 5   # TCP_KEEPCNT
    }
)
```

### Queue Optimization
- Use priority queues for critical tasks
- Implement task routing based on workload
- Set appropriate task expiration times
- Use task compression for large payloads

## Troubleshooting

### Common Issues

#### Issue: Tasks not being processed
```bash
# Check worker status
celery -A apps.backend.workers.celery_app status

# Inspect active tasks
celery -A apps.backend.workers.celery_app inspect active

# Check Redis connectivity
redis-cli ping
```

#### Issue: Memory leaks in workers
```python
# Configure worker recycling
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000  # 200MB
```

#### Issue: Task failures
```python
# Check dead letter queue
from apps.backend.workers.celery_app import app
dead_tasks = app.control.inspect().reserved()

# Retry failed tasks
task.retry(countdown=60, max_retries=3)
```

### Monitoring Commands
```bash
# Queue statistics
celery -A apps.backend.workers.celery_app inspect stats

# List all queues
celery -A apps.backend.workers.celery_app list bindings

# Purge queue
celery -A apps.backend.workers.celery_app purge -Q queue_name

# Worker pool stats
celery -A apps.backend.workers.celery_app inspect pool_stats
```

## Best Practices

### Do's ✅
- Always set task timeouts
- Use tenant context for multi-tenancy
- Implement proper retry logic
- Monitor queue sizes and worker health
- Use structured logging
- Test task idempotency

### Don'ts ❌
- Don't store large objects in task results
- Avoid synchronous blocking operations
- Don't use pickle serialization (security risk)
- Never hardcode credentials
- Don't ignore task failures

## Migration from AWS

If migrating from AWS services:

| AWS Service | Self-Hosted Alternative |
|------------|------------------------|
| SQS | Redis with Celery |
| Lambda | Celery Workers |
| CloudWatch Events | Celery Beat |
| CloudWatch Logs | Structured logging to stdout |
| CloudWatch Metrics | Prometheus + Grafana |
| DynamoDB | Redis for results |
| SES | SMTP/SendGrid |

## Support Resources

- **Celery Documentation**: [docs.celeryproject.org](https://docs.celeryproject.org/)
- **Redis Documentation**: [redis.io/documentation](https://redis.io/documentation)
- **Flower Documentation**: [flower.readthedocs.io](https://flower.readthedocs.io/)
- **Prometheus**: [prometheus.io/docs](https://prometheus.io/docs/)

## Version History

- **v1.0.0** (2025-01-27): Initial implementation with Redis broker
- **Future v1.1.0**: Add Redis Sentinel support for HA
- **Future v1.2.0**: Implement task result streaming