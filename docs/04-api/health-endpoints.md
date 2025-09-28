# Health Check Endpoints - API Reference

**Document Version:** 1.0.0
**Last Updated:** September 21, 2025
**Status:** ✅ Production Ready
**Base URL:** `http://localhost:8009/health`

---

## 📋 **Overview**

Comprehensive health monitoring endpoints for all ToolBoxAI system components including agents, MCP servers, Redis queues, Supabase database, and Docker services. All endpoints support real-time monitoring and alerting integration.

---

## 🤖 **Agent Health Endpoints**

### **Get All Agents Health**
```http
GET /health/agents
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "total_agents": 5,
  "healthy_agents": 5,
  "agents": {
    "agent_content_abc123": {
      "agent_id": "agent_content_abc123",
      "agent_type": "content",
      "status": "healthy",
      "last_activity": "2025-09-21T17:15:00Z",
      "error_count": 0,
      "quality_score": 0.92,
      "performance_metrics": {
        "avg_response_time_ms": 1250,
        "tasks_completed": 45,
        "success_rate": 0.98
      },
      "timestamp": "2025-09-21T17:15:00Z"
    }
  },
  "system_metrics": {
    "agents": {"total": 5, "healthy": 5},
    "tasks": {"completed": 234, "failed": 3},
    "system": {"status": "healthy", "uptime": "24h"}
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Specific Agent Health**
```http
GET /health/agents/{agent_id}
```

**Parameters:**
- `agent_id` (string): Unique agent identifier

**Response:**
```json
{
  "agent_id": "agent_content_abc123",
  "agent_type": "content",
  "status": "healthy",
  "last_activity": "2025-09-21T17:15:00Z",
  "error_count": 0,
  "quality_score": 0.92,
  "performance_metrics": {
    "avg_response_time_ms": 1250,
    "tasks_completed": 45,
    "success_rate": 0.98,
    "last_execution_time": "2025-09-21T17:14:30Z"
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Agents by Type**
```http
GET /health/agents/type/{agent_type}
```

**Parameters:**
- `agent_type` (string): Type of agents (content, quiz, terrain, script, code_review)

**Response:**
```json
{
  "agent_type": "content",
  "total_agents": 1,
  "agents": {
    "agent_content_abc123": {
      "agent_id": "agent_content_abc123",
      "agent_type": "content",
      "status": "healthy",
      "last_activity": "2025-09-21T17:15:00Z",
      "error_count": 0,
      "quality_score": 0.92,
      "performance_metrics": {},
      "timestamp": "2025-09-21T17:15:00Z"
    }
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Agent Metrics Summary**
```http
GET /health/agents/metrics/summary
```

**Response:**
```json
{
  "summary": {
    "total_agents": 5,
    "average_quality_score": 0.89,
    "total_errors": 3,
    "agent_types": {
      "content": 1,
      "quiz": 1,
      "terrain": 1,
      "script": 1,
      "code_review": 1
    }
  },
  "system_metrics": {
    "agents": {"total": 5},
    "system": {"status": "healthy"}
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

---

## 🔗 **MCP Health Endpoints**

### **Get MCP Server Health**
```http
GET /health/mcp
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "server_url": "ws://localhost:9877",
  "response_time_ms": 45.2,
  "active_connections": 3,
  "context_stores": {
    "memory_store": "healthy",
    "persistent_store": "healthy"
  },
  "last_sync": "2025-09-21T17:14:55Z",
  "error_details": null,
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Context Stores Health**
```http
GET /health/mcp/context-stores
```

**Response:**
```json
{
  "overall_status": "healthy",
  "healthy_stores": 3,
  "total_stores": 3,
  "context_stores": {
    "memory_store": {
      "status": "healthy",
      "type": "in_memory",
      "size": 150,
      "last_accessed": "2025-09-21T17:14:58Z"
    },
    "persistent_store": {
      "status": "healthy",
      "type": "file_based",
      "path": "/data/mcp/contexts",
      "last_accessed": "2025-09-21T17:14:55Z"
    },
    "vector_store": {
      "status": "healthy",
      "type": "supabase_vector",
      "provider": "supabase",
      "last_accessed": "2025-09-21T17:14:50Z"
    }
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get MCP Connections Status**
```http
GET /health/mcp/connections
```

**Response:**
```json
{
  "active_connections": 3,
  "max_connections": 100,
  "connection_pool_healthy": true,
  "recent_connections": [
    {
      "client_id": "client_abc123",
      "connected_at": "2025-09-21T17:10:00Z",
      "last_activity": "2025-09-21T17:14:55Z"
    }
  ],
  "error_count": 0,
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get MCP Performance Metrics**
```http
GET /health/mcp/performance
```

**Response:**
```json
{
  "performance_metrics": {
    "response_times": {
      "avg_ms": 150.0,
      "p50_ms": 120.0,
      "p95_ms": 300.0,
      "p99_ms": 500.0
    },
    "throughput": {
      "requests_per_second": 10.5,
      "contexts_per_second": 5.2,
      "sync_operations_per_second": 2.1
    },
    "resource_usage": {
      "memory_usage_mb": 256.0,
      "cpu_usage_percent": 15.2,
      "active_contexts": 150
    },
    "error_rates": {
      "total_errors": 0,
      "error_rate_percent": 0.0,
      "last_error": null
    }
  },
  "collection_time": "2025-09-21T17:15:00Z",
  "timestamp": "2025-09-21T17:15:00Z"
}
```

---

## 📊 **Redis Queue Health Endpoints**

### **Get Queue Health**
```http
GET /health/queue
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "queue_length": 25,
  "memory_usage_bytes": 104857600,
  "redis_version": "7.0.12",
  "connection_pool_size": 10,
  "performance_metrics": {
    "response_time_ms": 12.5,
    "connection_established": true,
    "memory_efficiency": "good"
  },
  "queue_stats": {
    "total_tasks": 25,
    "processing_rate": "normal",
    "avg_processing_time": "150ms",
    "error_rate": "0.1%"
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Detailed Queue Health**
```http
GET /health/queue/detailed
```

**Response:**
```json
{
  "detailed_statistics": {
    "connection_info": {
      "redis_version": "7.0.12",
      "uptime_seconds": 86400,
      "connected_clients": 5,
      "total_connections_received": 1250,
      "keyspace_hits": 9500,
      "keyspace_misses": 500
    },
    "queue_details": {
      "agent_tasks": {"length": 25, "status": "active"},
      "priority_tasks": {"length": 5, "status": "active"},
      "failed_tasks": {"length": 2, "status": "empty"},
      "completed_tasks": {"length": 1200, "status": "active"}
    },
    "memory_analysis": {
      "used_memory": 104857600,
      "used_memory_human": "100MB",
      "used_memory_peak": 134217728,
      "used_memory_peak_human": "128MB",
      "memory_fragmentation_ratio": 1.15,
      "maxmemory": 2147483648,
      "maxmemory_policy": "allkeys-lru"
    },
    "performance_history": {
      "avg_response_time_ms": 45.2,
      "peak_response_time_ms": 120.5,
      "throughput_per_second": 15.8,
      "error_rate_percent": 0.1,
      "last_24h_tasks": 12543
    },
    "task_distribution": {
      "content_generation": 45,
      "quiz_generation": 30,
      "terrain_generation": 15,
      "script_generation": 8,
      "code_review": 2
    }
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Queue Performance Metrics**
```http
GET /health/queue/performance
```

**Response:**
```json
{
  "performance_metrics": {
    "current_performance": {
      "response_time_ms": 12.5,
      "read_write_test": "passed",
      "timestamp": "2025-09-21T17:15:00Z"
    },
    "redis_statistics": {
      "total_commands_processed": 1500000,
      "instantaneous_ops_per_sec": 25,
      "rejected_connections": 0,
      "expired_keys": 1200,
      "evicted_keys": 50
    },
    "queue_performance": {
      "estimated_throughput": 25,
      "performance_grade": "excellent",
      "bottleneck_analysis": "none_detected"
    }
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Queue Tasks Summary**
```http
GET /health/queue/tasks/summary
```

**Response:**
```json
{
  "task_summary": {
    "pending_tasks": 25,
    "processing_tasks": 3,
    "completed_tasks": 1200,
    "failed_tasks": 2,
    "total_tasks": 1230
  },
  "task_types": {
    "content_generation": 10.0,
    "quiz_generation": 7.5,
    "terrain_generation": 3.75,
    "script_generation": 2.5,
    "code_review": 1.25
  },
  "processing_rates": {
    "tasks_per_minute": 12.5,
    "avg_processing_time_seconds": 45.2,
    "success_rate_percent": 98.7,
    "retry_rate_percent": 1.2
  },
  "queue_health": "healthy",
  "timestamp": "2025-09-21T17:15:00Z"
}
```

---

## 🗄️ **Supabase Health Endpoints**

### **Get Supabase Health**
```http
GET /health/supabase
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "response_time_ms": 85.3,
  "tables_accessible": 5,
  "database_size_mb": 125.5,
  "connection_pool": {
    "active_connections": 2,
    "max_connections": 100,
    "pool_healthy": true
  },
  "realtime_status": "healthy",
  "storage_status": "healthy",
  "rls_status": "enabled",
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Supabase Tables Health**
```http
GET /health/supabase/tables
```

**Response:**
```json
{
  "overall_status": "all_accessible",
  "accessible_tables": 5,
  "total_tables": 5,
  "table_details": {
    "agent_instances": {
      "status": "accessible",
      "description": "Agent registration and configuration",
      "last_checked": "2025-09-21T17:15:00Z"
    },
    "agent_executions": {
      "status": "accessible",
      "description": "Task execution records",
      "last_checked": "2025-09-21T17:15:00Z"
    },
    "agent_metrics": {
      "status": "accessible",
      "description": "Performance metrics and statistics",
      "last_checked": "2025-09-21T17:15:00Z"
    },
    "agent_task_queue": {
      "status": "accessible",
      "description": "Task queue management",
      "last_checked": "2025-09-21T17:15:00Z"
    },
    "system_health": {
      "status": "accessible",
      "description": "System health snapshots",
      "last_checked": "2025-09-21T17:15:00Z"
    }
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Supabase Real-time Health**
```http
GET /health/supabase/realtime
```

**Response:**
```json
{
  "overall_status": "healthy",
  "realtime_details": {
    "websocket_connection": "connected",
    "active_subscriptions": 3,
    "subscription_health": {
      "agent_executions": "healthy",
      "agent_metrics": "healthy",
      "system_health": "healthy"
    },
    "last_heartbeat": "2025-09-21T17:14:55Z",
    "error_count": 0
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Supabase Storage Health**
```http
GET /health/supabase/storage
```

**Response:**
```json
{
  "overall_status": "healthy",
  "accessible_buckets": 4,
  "total_buckets": 4,
  "storage_details": {
    "buckets": {
      "agent-outputs": {
        "status": "accessible",
        "file_count": 1250,
        "size_mb": 45.2,
        "last_accessed": "2025-09-21T17:14:50Z"
      },
      "user-uploads": {
        "status": "accessible",
        "file_count": 890,
        "size_mb": 67.8,
        "last_accessed": "2025-09-21T17:14:45Z"
      },
      "system-backups": {
        "status": "accessible",
        "file_count": 24,
        "size_mb": 234.5,
        "last_accessed": "2025-09-21T17:00:00Z"
      },
      "temporary-files": {
        "status": "accessible",
        "file_count": 12,
        "size_mb": 5.2,
        "last_accessed": "2025-09-21T17:14:55Z"
      }
    },
    "upload_test": "passed",
    "download_test": "passed",
    "storage_quota": {
      "used_mb": 352.7,
      "total_mb": 1024,
      "usage_percent": 34.4
    }
  },
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### **Get Supabase Performance Metrics**
```http
GET /health/supabase/performance
```

**Response:**
```json
{
  "performance_metrics": {
    "query_performance": {
      "simple_query_ms": 25.3,
      "complex_query_ms": 63.25,
      "insert_performance_ms": 30.36,
      "update_performance_ms": 37.95
    },
    "throughput": {
      "queries_per_second": 25.5,
      "concurrent_connections": 5,
      "max_throughput": 100
    },
    "resource_usage": {
      "cpu_usage_percent": 15.2,
      "memory_usage_percent": 45.8,
      "storage_usage_percent": 34.4
    }
  },
  "total_check_time_ms": 85.3,
  "performance_grade": "excellent",
  "timestamp": "2025-09-21T17:15:00Z"
}
```

---

## 🔧 **Error Responses**

### **Service Unavailable (503)**
```json
{
  "detail": "Agent service unavailable"
}
```

### **Not Found (404)**
```json
{
  "detail": "Agent agent_xyz_123 not found"
}
```

### **Internal Server Error (500)**
```json
{
  "detail": "Internal server error: Connection timeout"
}
```

---

## 📊 **Health Status Definitions**

### **Agent Status:**
- **healthy:** Agent is operational and responding normally
- **idle:** Agent is ready but not currently processing tasks
- **busy:** Agent is actively processing tasks
- **degraded:** Agent is operational but with reduced performance
- **unhealthy:** Agent is not responding or has critical errors

### **System Status:**
- **healthy:** All components operational (100% healthy agents)
- **degraded:** Most components operational (80%+ healthy agents)
- **unhealthy:** Significant issues detected (<80% healthy agents)

### **Performance Grades:**
- **excellent:** Response time < 100ms
- **good:** Response time < 500ms
- **poor:** Response time > 500ms

---

## 🔍 **Monitoring Integration**

### **Prometheus Metrics:**
All health endpoints expose metrics compatible with Prometheus:

```yaml
# Example Prometheus configuration
- job_name: 'toolboxai-health'
  static_configs:
    - targets: ['localhost:8009']
  metrics_path: '/health/agents'
  scrape_interval: 30s
```

### **Alerting Rules:**
```yaml
groups:
  - name: toolboxai_agents
    rules:
      - alert: AgentUnhealthy
        expr: agent_health_status != 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Agent {{ $labels.agent_id }} is unhealthy"

      - alert: HighQueueDepth
        expr: redis_queue_length > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis queue depth is high: {{ $value }}"
```

### **Dashboard Integration:**
Health endpoints are designed for integration with:
- **Grafana:** Real-time dashboards and visualization
- **Datadog:** Application performance monitoring
- **New Relic:** Full-stack observability
- **Custom Dashboards:** JSON API for custom monitoring solutions

---

## 🚀 **Production Usage**

### **Load Balancer Health Checks:**
```yaml
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health/agents
    port: 8009
  initialDelaySeconds: 30
  periodSeconds: 10

# Kubernetes readiness probe
readinessProbe:
  httpGet:
    path: /health/queue
    port: 8009
  initialDelaySeconds: 5
  periodSeconds: 5
```

### **Automated Monitoring:**
```bash
#!/bin/bash
# Health check script for cron
curl -f http://localhost:8009/health/agents || exit 1
curl -f http://localhost:8009/health/queue || exit 1
curl -f http://localhost:8009/health/supabase || exit 1
echo "All health checks passed"
```

### **Performance Thresholds:**
- **Agent Response Time:** < 30 seconds
- **Queue Response Time:** < 100ms
- **Database Response Time:** < 200ms
- **MCP Response Time:** < 500ms
- **Overall System Health:** > 95% uptime

---

## 🎯 **Implementation Status: COMPLETE**

All health endpoints are **production-ready** with:

- **✅ Complete Coverage:** All system components monitored
- **✅ Docker Integration:** Full containerized environment support
- **✅ Real-time Metrics:** Live performance monitoring
- **✅ Error Handling:** Comprehensive error responses
- **✅ Monitoring Integration:** Prometheus and alerting ready
- **✅ Production Deployment:** Load balancer and Kubernetes ready

The health monitoring system provides complete observability for the ToolBoxAI platform with enterprise-grade reliability and performance monitoring.
