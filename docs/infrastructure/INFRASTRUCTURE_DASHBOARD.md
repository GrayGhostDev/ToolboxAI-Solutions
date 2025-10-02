# Infrastructure Dashboard Documentation

**Created:** October 1, 2025
**Branch:** development-infrastructure-dashboard
**Status:** ✅ Fully Operational

## Overview

The Infrastructure Dashboard provides comprehensive real-time monitoring of the ToolboxAI platform's system health, performance metrics, and resource utilization. It integrates with the backend observability system to deliver actionable insights for system administrators and DevOps teams.

## Architecture

### Backend Components

#### 1. Infrastructure Metrics Service
**Location:** `apps/backend/services/infrastructure_metrics.py`

Provides comprehensive infrastructure monitoring capabilities:
- **System Metrics:** CPU, memory, disk, network utilization
- **Process Metrics:** Backend process resource usage
- **Platform Info:** OS, architecture, Python version
- **Health Scoring:** Automated health assessment (0-100 scale)
- **Threshold Monitoring:** Automated alerting for resource violations

**Key Features:**
- Real-time metric collection using `psutil`
- Historical metric storage (up to 1000 samples in memory)
- Configurable warning and critical thresholds
- Automatic health score calculation

#### 2. Observability API Endpoints
**Location:** `apps/backend/api/v1/endpoints/observability.py`

Comprehensive API endpoints for infrastructure monitoring:

```bash
# Infrastructure Endpoints
GET  /api/v1/observability/infrastructure/system      # System metrics
GET  /api/v1/observability/infrastructure/process     # Process metrics
GET  /api/v1/observability/infrastructure/platform    # Platform info
GET  /api/v1/observability/infrastructure/summary     # Aggregated summary
GET  /api/v1/observability/infrastructure/health      # Health check
GET  /api/v1/observability/infrastructure/report      # Comprehensive report

# Additional Observability Endpoints
GET  /api/v1/observability/metrics                    # General metrics
GET  /api/v1/observability/traces                     # Distributed traces
GET  /api/v1/observability/anomalies                  # Anomaly detection
GET  /api/v1/observability/health/components          # Component health
POST /api/v1/observability/start-metrics-stream       # Start Pusher streaming
POST /api/v1/observability/stop-metrics-stream        # Stop streaming
```

#### 3. Database Models
**Location:** `database/models/infrastructure_metrics.py`

Stores historical infrastructure data:

- **SystemMetricsHistory:** Time-series system metrics
- **ProcessMetricsHistory:** Process-level metrics
- **InfrastructureHealth:** Health check results
- **InfrastructureAlert:** Alert history
- **MetricAggregation:** Pre-computed aggregations

**Retention Policy:**
- Raw metrics: 30 days (configurable)
- Hourly aggregations: 90 days
- Daily aggregations: 1 year

### Frontend Components

#### 1. InfrastructureMetrics Component
**Location:** `apps/dashboard/src/components/observability/InfrastructureMetrics.tsx`

Modern React component built with Mantine UI:

**Features:**
- Health score ring progress indicator
- Real-time metric cards (CPU, Memory, Disk, Network)
- Process metrics display
- Warning and critical issue alerts
- Auto-refresh every 5 seconds
- Color-coded status indicators

**Visual Elements:**
- Ring progress for health score
- Progress bars for resource utilization
- Badge indicators for warnings/critical issues
- Responsive grid layout

#### 2. ObservabilityDashboard Component
**Location:** `apps/dashboard/src/components/observability/ObservabilityDashboard.tsx`

Comprehensive observability dashboard with multiple tabs:

**Tabs:**
1. **Metrics:** System-wide performance metrics
2. **Infrastructure:** Detailed infrastructure monitoring (uses InfrastructureMetrics)
3. **Traces:** Distributed tracing
4. **Load Balancing:** Circuit breakers, rate limiting
5. **Anomalies:** Anomaly detection
6. **System Health:** Service health status

**Features:**
- Real-time Pusher streaming
- Time range selection (5m, 15m, 1h, 6h, 24h)
- Auto-refresh toggle
- Comprehensive charts (Line, Area, Bar, Radar)
- Alert notifications

#### 3. Observability Service
**Location:** `apps/dashboard/src/services/observability.ts`

TypeScript service layer for API communication:

**Methods:**
- `getInfrastructureReport()` - Complete infrastructure status
- `getInfrastructureSystemMetrics()` - System-level metrics
- `getInfrastructureProcessMetrics()` - Process metrics
- `getInfrastructurePlatformInfo()` - Platform information
- `getInfrastructureSummary(timeWindow)` - Aggregated metrics
- `checkInfrastructureHealth()` - Health status
- `connectMetricsStream(callback)` - Pusher real-time streaming
- `disconnectMetricsStream()` - Stop streaming

## Data Flow

### Metric Collection Flow

```
┌─────────────────┐
│  psutil Library │
│  (System Stats) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ InfrastructureMetricsCollector  │
│ (apps/backend/services/)        │
├─────────────────────────────────┤
│ • collect_system_metrics()      │
│ • collect_process_metrics()     │
│ • check_resource_thresholds()   │
│ • get_comprehensive_report()    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Observability API Endpoints    │
│  (apps/backend/api/v1/)         │
├─────────────────────────────────┤
│ GET /infrastructure/report      │
│ GET /infrastructure/system      │
│ GET /infrastructure/health      │
└────────┬────────────────────────┘
         │
         ├─────────────────┬──────────────────┐
         │                 │                  │
         ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Pusher    │  │  Dashboard   │
│  (History)   │  │  (Real-time) │  │   (Display)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Real-time Streaming Flow

```
1. Dashboard requests stream:
   POST /api/v1/observability/start-metrics-stream

2. Backend starts background task:
   stream_metrics_to_pusher()

3. Every 2 seconds:
   - Collect latest metrics
   - Publish to Pusher channel: 'observability-metrics'
   - Event: 'metrics.updated'

4. Dashboard receives updates:
   - Pusher subscription active
   - Callback processes data
   - UI updates automatically

5. Dashboard stops stream:
   POST /api/v1/observability/stop-metrics-stream
```

## Metrics Reference

### System Metrics

#### CPU
- **cpu_percent** - Current CPU utilization (%)
- **cpu_count** - Number of CPU cores
- **cpu_freq_mhz** - Current CPU frequency (MHz)

**Thresholds:**
- Warning: 70%
- Critical: 90%

#### Memory
- **memory_total_gb** - Total system RAM (GB)
- **memory_used_gb** - Used RAM (GB)
- **memory_available_gb** - Available RAM (GB)
- **memory_percent** - Memory utilization (%)

**Thresholds:**
- Warning: 75%
- Critical: 90%

#### Disk
- **disk_total_gb** - Total disk space (GB)
- **disk_used_gb** - Used disk space (GB)
- **disk_free_gb** - Free disk space (GB)
- **disk_percent** - Disk utilization (%)

**Thresholds:**
- Warning: 80%
- Critical: 95%

#### Network
- **network_bytes_sent** - Total bytes sent
- **network_bytes_recv** - Total bytes received
- **network_connections** - Active network connections

### Process Metrics

- **pid** - Process ID
- **name** - Process name
- **status** - Process status (running, sleeping, etc.)
- **cpu_percent** - Process CPU usage (%)
- **memory_mb** - Process memory usage (MB)
- **memory_percent** - Process memory percentage (%)
- **num_threads** - Number of threads
- **num_fds** - Number of file descriptors (Unix)
- **create_time** - Process start time

### Health Score Calculation

Health score is calculated on a 0-100 scale:

```python
score = 100
score -= (cpu_percent / 100) * 30    # CPU impact: 30%
score -= (memory_percent / 100) * 30 # Memory impact: 30%
score -= (disk_percent / 100) * 20   # Disk impact: 20%
score -= len(warnings) * 5            # Warning deduction
score -= len(critical) * 15           # Critical deduction
```

**Health Levels:**
- **90-100:** Healthy (Green)
- **70-89:** Degraded (Yellow)
- **50-69:** Warning (Orange)
- **0-49:** Critical (Red)

## API Examples

### Get Comprehensive Infrastructure Report

```typescript
// Frontend
const response = await observabilityAPI.getInfrastructureReport();

// Response
{
  "status": "success",
  "timestamp": "2025-10-01T10:30:00Z",
  "platform": {
    "system": "Linux",
    "release": "5.15.0",
    "hostname": "toolboxai-backend-1",
    "python_version": "3.12.0"
  },
  "system": {
    "cpu": {
      "percent": 45.2,
      "count": 8,
      "freq_mhz": 2400
    },
    "memory": {
      "total_gb": 16.0,
      "used_gb": 8.5,
      "available_gb": 7.5,
      "percent": 53.1
    },
    "disk": {
      "total_gb": 500.0,
      "used_gb": 250.0,
      "free_gb": 250.0,
      "percent": 50.0
    },
    "network": {
      "bytes_sent": 1024000000,
      "bytes_recv": 2048000000,
      "connections": 42
    }
  },
  "process": {
    "pid": 12345,
    "name": "python",
    "cpu_percent": 12.5,
    "memory_mb": 512.0,
    "threads": 8,
    "file_descriptors": 156
  },
  "threshold_check": {
    "status": "healthy",
    "warnings": [],
    "critical": [],
    "thresholds": {
      "cpu_warning": 70.0,
      "cpu_critical": 90.0,
      "memory_warning": 75.0,
      "memory_critical": 90.0
    }
  },
  "health_score": 85.5
}
```

### Get Health Check with Alerts

```typescript
const response = await observabilityAPI.checkInfrastructureHealth();

// Response with warnings
{
  "status": "success",
  "data": {
    "status": "degraded",
    "warnings": [
      "CPU usage high: 75.3%",
      "Memory usage high: 78.2%"
    ],
    "critical": [],
    "thresholds": {
      "cpu_warning": 70.0,
      "cpu_critical": 90.0,
      "memory_warning": 75.0,
      "memory_critical": 90.0,
      "disk_warning": 80.0,
      "disk_critical": 95.0
    },
    "timestamp": "2025-10-01T10:30:00Z"
  }
}
```

## Configuration

### Environment Variables

```bash
# Backend (.env)
# No specific env vars needed - uses default psutil
```

### Threshold Configuration

Modify thresholds in `apps/backend/services/infrastructure_metrics.py`:

```python
THRESHOLDS = {
    "cpu_warning": 70.0,      # Adjust CPU warning level
    "cpu_critical": 90.0,     # Adjust CPU critical level
    "memory_warning": 75.0,   # Adjust memory warning level
    "memory_critical": 90.0,  # Adjust memory critical level
    "disk_warning": 80.0,     # Adjust disk warning level
    "disk_critical": 95.0,    # Adjust disk critical level
}
```

### Data Retention

Configure in database models:

```python
# Default retention: 30 days
await cleanup_old_metrics(session, days_to_keep=30)

# Create hourly aggregations
await create_hourly_aggregations(session, timestamp)
```

## Deployment Considerations

### Database Migrations

Create migration for infrastructure models:

```bash
# From project root
alembic revision --autogenerate -m "Add infrastructure metrics models"
alembic upgrade head
```

### Performance Optimization

1. **Database Indexes:** All time-series queries use indexed timestamps
2. **Metric Aggregation:** Hourly/daily aggregations reduce query load
3. **Data Retention:** Automatic cleanup prevents database bloat
4. **Pusher Streaming:** Reduces polling overhead
5. **In-Memory History:** Recent metrics cached for fast access

### Monitoring Best Practices

1. **Set appropriate thresholds** based on your infrastructure
2. **Enable Pusher streaming** for real-time visibility
3. **Configure alerts** for critical issues
4. **Review health scores** regularly
5. **Archive historical data** for compliance

## Troubleshooting

### Common Issues

#### 1. No metrics displayed
- Verify backend is running on port 8009
- Check auth token in localStorage
- Confirm observability router is registered
- Check browser console for API errors

#### 2. Pusher streaming not working
- Verify Pusher credentials in backend .env
- Check Pusher dashboard for connection status
- Confirm /start-metrics-stream endpoint is accessible
- Check browser console for Pusher errors

#### 3. High memory usage
- Adjust in-memory history limit (default: 1000 samples)
- Enable metric aggregation
- Configure data retention policy

#### 4. Slow dashboard loading
- Enable metric aggregations
- Reduce refresh interval
- Optimize time range selection
- Check database query performance

### Debug Commands

```bash
# Test backend endpoints
curl http://localhost:8009/api/v1/observability/infrastructure/report \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check Pusher connectivity
curl http://localhost:8009/api/v1/observability/start-metrics-stream \
  -X POST -H "Authorization: Bearer YOUR_TOKEN"

# View backend logs
docker logs toolboxai-backend-1 --tail 100 -f
```

## Future Enhancements

### Planned Features
- [ ] Custom metric definitions
- [ ] Alert rule configuration UI
- [ ] Metric export (Prometheus, Grafana)
- [ ] Container-specific metrics
- [ ] Multi-node infrastructure support
- [ ] Predictive alerting using ML
- [ ] Automated scaling recommendations
- [ ] Cost optimization insights

### Integration Opportunities
- Prometheus/Grafana export
- PagerDuty/Slack alerting
- AWS CloudWatch integration
- Datadog/New Relic compatibility
- Custom webhook notifications

## Related Documentation

- [Observability System Overview](./OBSERVABILITY_OVERVIEW.md)
- [Backend API Documentation](../backend/API_REFERENCE.md)
- [Database Schema](../database/SCHEMA.md)
- [Pusher Integration](../realtime/PUSHER_GUIDE.md)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review backend logs
3. Test API endpoints directly
4. Contact DevOps team

---

**Last Updated:** October 1, 2025
**Version:** 1.0.0
**Status:** ✅ Production Ready
