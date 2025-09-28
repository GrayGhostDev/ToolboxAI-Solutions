---
title: Scripts & Automation Guide 2025
description: Comprehensive guide for scripts and automation tools
version: 2.0.0
last_updated: 2025-09-14
---

# 🔧 Scripts & Automation Guide 2025

## Overview

This guide provides comprehensive documentation for the ToolboxAI Solutions scripts and automation tools, covering development, deployment, monitoring, and maintenance automation.

## 📁 Scripts Directory Structure

```
scripts/
├── agents/                    # Agent management scripts
├── common/                    # Shared utility scripts
├── database/                  # Database management scripts
├── debugger/                  # Debugging and monitoring scripts
├── deploy/                    # Deployment automation
├── development/               # Development environment scripts
├── docs/                     # Documentation generation scripts
├── maintenance/               # System maintenance scripts
├── monitoring/                # Monitoring and alerting scripts
├── testing/                   # Test automation scripts
└── tools/                     # Development tools and utilities
```

## 🤖 Agent Management Scripts

### Agent Supervisor Control

```bash
#!/bin/bash
# scripts/agents/run_supervisor.sh

set -e

# Configuration
SUPERVISOR_SCRIPT="core/agents/supervisor_advanced.py"
LOG_DIR="logs/agents"
PID_FILE="pids/supervisor.pid"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$PID_FILE")"

# Start supervisor
echo "Starting Advanced Supervisor Agent..."
python "$SUPERVISOR_SCRIPT" \
    --log-level INFO \
    --log-file "$LOG_DIR/supervisor.log" \
    --pid-file "$PID_FILE" \
    --daemon

echo "Supervisor started with PID $(cat "$PID_FILE")"
```

### Agent Health Monitoring

```python
#!/usr/bin/env python3
# scripts/agents/agent_health_monitor.py

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

class AgentHealthMonitor:
    def __init__(self):
        self.agents = [
            "content_agent",
            "quiz_agent",
            "terrain_agent",
            "script_agent",
            "review_agent"
        ]

    async def check_agent_health(self, agent_name: str) -> dict:
        """Check health of specific agent"""
        try:
            # Implementation would check agent health
            return {
                "agent": agent_name,
                "status": "healthy",
                "response_time": 0.1,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }

    async def monitor_all_agents(self):
        """Monitor all agents"""
        results = []
        for agent in self.agents:
            result = await self.check_agent_health(agent)
            results.append(result)

        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": results,
            "summary": {
                "total": len(results),
                "healthy": len([r for r in results if r["status"] == "healthy"]),
                "unhealthy": len([r for r in results if r["status"] == "unhealthy"])
            }
        }

        # Save report
        report_file = Path("logs/agent_health_report.json")
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))

        print(json.dumps(report, indent=2))
        return report

if __name__ == "__main__":
    monitor = AgentHealthMonitor()
    asyncio.run(monitor.monitor_all_agents())
```

## 🗄️ Database Management Scripts

### Database Setup

```bash
#!/bin/bash
# scripts/database/setup_database.sh

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-educational_platform}"
DB_USER="${DB_USER:-eduplatform}"
DB_PASSWORD="${DB_PASSWORD:-password}"

echo "Setting up database: $DB_NAME on $DB_HOST:$DB_PORT"

# Create database
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" || echo "Database may already exist"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Create initial data
echo "Creating initial data..."
python scripts/database/create_initial_data.py

echo "Database setup complete!"
```

### Database Performance Testing

```python
#!/usr/bin/env python3
# scripts/database/performance_test.py

import asyncio
import time
import statistics
from database.connection_manager import get_connection

class DatabasePerformanceTest:
    def __init__(self):
        self.results = []

    async def test_query_performance(self, query: str, iterations: int = 100):
        """Test query performance"""
        times = []

        for i in range(iterations):
            start_time = time.time()

            async with get_connection() as conn:
                await conn.execute(query)

            end_time = time.time()
            times.append(end_time - start_time)

        return {
            "query": query,
            "iterations": iterations,
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0
        }

    async def run_performance_tests(self):
        """Run comprehensive performance tests"""
        tests = [
            "SELECT * FROM users LIMIT 10",
            "SELECT * FROM lessons WHERE grade_level = 7",
            "SELECT COUNT(*) FROM agent_executions",
            "INSERT INTO test_table (name) VALUES ('test')",
            "UPDATE users SET last_login = NOW() WHERE id = 1"
        ]

        results = []
        for query in tests:
            result = await self.test_query_performance(query)
            results.append(result)
            print(f"Query: {query[:50]}...")
            print(f"  Average: {result['avg_time']:.4f}s")
            print(f"  Min: {result['min_time']:.4f}s")
            print(f"  Max: {result['max_time']:.4f}s")
            print()

        return results

if __name__ == "__main__":
    test = DatabasePerformanceTest()
    asyncio.run(test.run_performance_tests())
```

## 🚀 Deployment Scripts

### Automated Deployment

```bash
#!/bin/bash
# scripts/deploy/deploy_pipeline.sh

set -e

# Configuration
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io/toolboxai-solutions}"

echo "Deploying to $ENVIRONMENT environment with version $VERSION"

# Build and push images
echo "Building Docker images..."
docker build -t "$DOCKER_REGISTRY/backend:$VERSION" -f infrastructure/docker/Dockerfile.backend .
docker build -t "$DOCKER_REGISTRY/frontend:$VERSION" -f infrastructure/docker/Dockerfile.frontend .

echo "Pushing images to registry..."
docker push "$DOCKER_REGISTRY/backend:$VERSION"
docker push "$DOCKER_REGISTRY/frontend:$VERSION"

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl set image deployment/backend-deployment \
    backend="$DOCKER_REGISTRY/backend:$VERSION" \
    -n toolboxai-$ENVIRONMENT

kubectl set image deployment/frontend-deployment \
    frontend="$DOCKER_REGISTRY/frontend:$VERSION" \
    -n toolboxai-$ENVIRONMENT

# Wait for rollout
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/backend-deployment -n toolboxai-$ENVIRONMENT
kubectl rollout status deployment/frontend-deployment -n toolboxai-$ENVIRONMENT

# Run health checks
echo "Running health checks..."
python scripts/deploy/verify_deployment.py --environment "$ENVIRONMENT"

echo "Deployment complete!"
```

### Deployment Verification

```python
#!/usr/bin/env python3
# scripts/deploy/verify_deployment.py

import asyncio
import aiohttp
import argparse
import sys
from typing import List, Dict

class DeploymentVerifier:
    def __init__(self, environment: str):
        self.environment = environment
        self.base_urls = {
            "staging": "https://staging-api.toolboxai.com",
            "production": "https://api.toolboxai.com",
            "development": "http://localhost:8008"
        }
        self.base_url = self.base_urls.get(environment, "http://localhost:8008")

    async def check_health_endpoint(self) -> bool:
        """Check health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    async def check_api_endpoints(self) -> List[Dict]:
        """Check API endpoints"""
        endpoints = [
            "/api/v1/lessons/",
            "/api/v1/users/",
            "/api/v1/analytics/",
            "/api/v1/assessments/"
        ]

        results = []
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        results.append({
                            "endpoint": endpoint,
                            "status": response.status,
                            "success": response.status < 400
                        })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint,
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    })

        return results

    async def verify_deployment(self) -> bool:
        """Verify complete deployment"""
        print(f"Verifying deployment for {self.environment} environment...")

        # Check health
        health_ok = await self.check_health_endpoint()
        if not health_ok:
            print("❌ Health check failed")
            return False

        print("✅ Health check passed")

        # Check API endpoints
        endpoint_results = await self.check_api_endpoints()
        failed_endpoints = [r for r in endpoint_results if not r["success"]]

        if failed_endpoints:
            print("❌ Some API endpoints failed:")
            for result in failed_endpoints:
                print(f"  - {result['endpoint']}: {result.get('error', 'Unknown error')}")
            return False

        print("✅ All API endpoints working")
        print("🎉 Deployment verification successful!")
        return True

async def main():
    parser = argparse.ArgumentParser(description="Verify deployment")
    parser.add_argument("--environment", required=True, help="Environment to verify")
    args = parser.parse_args()

    verifier = DeploymentVerifier(args.environment)
    success = await verifier.verify_deployment()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔍 Monitoring Scripts

### Service Monitoring

```bash
#!/bin/bash
# scripts/monitoring/monitor_services.sh

set -e

# Configuration
SERVICES=("fastapi" "flask-bridge" "mcp-server" "redis" "postgres")
LOG_DIR="logs/monitoring"
ALERT_EMAIL="alerts@toolboxai.com"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check service status
check_service() {
    local service=$1
    local status

    case $service in
        "fastapi")
            status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/health || echo "000")
            ;;
        "flask-bridge")
            status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/status || echo "000")
            ;;
        "mcp-server")
            status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9876/health || echo "000")
            ;;
        "redis")
            status=$(redis-cli ping 2>/dev/null | grep -q "PONG" && echo "200" || echo "000")
            ;;
        "postgres")
            status=$(pg_isready -q && echo "200" || echo "000")
            ;;
    esac

    echo "$status"
}

# Function to send alert
send_alert() {
    local service=$1
    local status=$2
    local message="Service $service is $status"

    echo "$(date): $message" >> "$LOG_DIR/alerts.log"

    # Send email alert (if configured)
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Service Alert: $service" "$ALERT_EMAIL"
    fi
}

# Monitor all services
echo "Starting service monitoring..."
while true; do
    for service in "${SERVICES[@]}"; do
        status=$(check_service "$service")

        if [ "$status" != "200" ]; then
            echo "$(date): $service is down (status: $status)"
            send_alert "$service" "down"
        else
            echo "$(date): $service is healthy"
        fi
    done

    sleep 30
done
```

### Performance Monitoring

```python
#!/usr/bin/env python3
# scripts/monitoring/performance_monitor.py

import asyncio
import psutil
import time
import json
from datetime import datetime
from pathlib import Path

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []
        self.log_file = Path("logs/performance_metrics.json")
        self.log_file.parent.mkdir(exist_ok=True)

    def collect_system_metrics(self):
        """Collect system performance metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "process_count": len(psutil.pids())
        }

    def collect_application_metrics(self):
        """Collect application-specific metrics"""
        # This would collect metrics from your application
        return {
            "active_connections": 0,  # Placeholder
            "request_rate": 0,        # Placeholder
            "error_rate": 0,          # Placeholder
            "response_time": 0        # Placeholder
        }

    def save_metrics(self, metrics):
        """Save metrics to file"""
        self.metrics.append(metrics)

        # Keep only last 1000 entries
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

        # Save to file
        self.log_file.write_text(json.dumps(self.metrics, indent=2))

    async def monitor(self, interval: int = 60):
        """Start monitoring"""
        print(f"Starting performance monitoring (interval: {interval}s)")

        while True:
            try:
                system_metrics = self.collect_system_metrics()
                app_metrics = self.collect_application_metrics()

                combined_metrics = {**system_metrics, **app_metrics}
                self.save_metrics(combined_metrics)

                print(f"Metrics collected: CPU={system_metrics['cpu_percent']:.1f}%, "
                      f"Memory={system_metrics['memory_percent']:.1f}%")

            except Exception as e:
                print(f"Error collecting metrics: {e}")

            await asyncio.sleep(interval)

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    asyncio.run(monitor.monitor())
```

## 🛠️ Development Scripts

### Environment Setup

```bash
#!/bin/bash
# scripts/development/setup_environment.sh

set -e

echo "Setting up development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo "$python_version < 3.11" | bc -l)" -eq 1 ]; then
    echo "Error: Python 3.11+ required, found $python_version"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
cd src/dashboard
npm install
cd ../..

# Setup pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "Creating directories..."
mkdir -p logs/{app,agents,monitoring}
mkdir -p pids
mkdir -p test-results

# Setup database
echo "Setting up database..."
python scripts/database/setup_database.sh

echo "Development environment setup complete!"
echo "To activate: source venv/bin/activate"
```

### Code Quality Checks

```bash
#!/bin/bash
# scripts/development/quality_check.sh

set -e

echo "Running code quality checks..."

# Python code quality
echo "Running Python linting..."
flake8 src/ tests/ --max-line-length=100 --exclude=venv/
black --check src/ tests/
isort --check-only src/ tests/

echo "Running Python type checking..."
mypy src/ --ignore-missing-imports

echo "Running Python security scan..."
bandit -r src/ -f json -o security-report.json

# TypeScript code quality
echo "Running TypeScript linting..."
cd src/dashboard
npm run lint
npm run type-check

# Run tests
echo "Running tests..."
cd ../..
python -m pytest tests/ -v --cov=src --cov-report=html

echo "Code quality checks complete!"
```

## 📊 Maintenance Scripts

### Database Cleanup

```python
#!/usr/bin/env python3
# scripts/maintenance/database_cleanup.py

import asyncio
from datetime import datetime, timedelta
from database.connection_manager import get_connection

class DatabaseCleanup:
    def __init__(self):
        self.cleanup_tasks = [
            self.cleanup_old_logs,
            self.cleanup_expired_sessions,
            self.cleanup_old_agent_executions,
            self.cleanup_temp_files
        ]

    async def cleanup_old_logs(self):
        """Clean up old log entries"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM logs WHERE created_at < %s",
                (cutoff_date,)
            )
            print(f"Cleaned up {result.rowcount} old log entries")

    async def cleanup_expired_sessions(self):
        """Clean up expired user sessions"""
        cutoff_date = datetime.utcnow() - timedelta(hours=24)

        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM user_sessions WHERE last_activity < %s",
                (cutoff_date,)
            )
            print(f"Cleaned up {result.rowcount} expired sessions")

    async def cleanup_old_agent_executions(self):
        """Clean up old agent execution logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM agent_executions WHERE created_at < %s",
                (cutoff_date,)
            )
            print(f"Cleaned up {result.rowcount} old agent executions")

    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        import os
        import glob

        temp_dirs = ["logs/temp", "uploads/temp", "cache/temp"]
        total_files = 0

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                files = glob.glob(f"{temp_dir}/*")
                for file in files:
                    if os.path.isfile(file):
                        os.remove(file)
                        total_files += 1

        print(f"Cleaned up {total_files} temporary files")

    async def run_cleanup(self):
        """Run all cleanup tasks"""
        print("Starting database cleanup...")

        for task in self.cleanup_tasks:
            try:
                await task()
            except Exception as e:
                print(f"Error in cleanup task {task.__name__}: {e}")

        print("Database cleanup complete!")

if __name__ == "__main__":
    cleanup = DatabaseCleanup()
    asyncio.run(cleanup.run_cleanup())
```

## 🎯 Best Practices

### Script Development

1. **Error Handling**: Always use `set -e` for bash scripts
2. **Logging**: Include comprehensive logging
3. **Configuration**: Use environment variables for configuration
4. **Documentation**: Document script purpose and usage
5. **Testing**: Test scripts in different environments

### Automation Guidelines

1. **Idempotent**: Scripts should be safe to run multiple times
2. **Rollback**: Include rollback procedures
3. **Monitoring**: Monitor script execution and results
4. **Alerting**: Alert on script failures
5. **Documentation**: Keep automation documentation current

---

*Last Updated: 2025-09-14*
*Version: 2.0.0*
*Compliance: COPPA, FERPA, GDPR, SOC 2 Type 2*

