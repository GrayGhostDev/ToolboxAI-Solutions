"""
Unit tests for Resource Coordinator

Tests resource allocation, API quotas, cost tracking, and optimization.
Covers allocation management, quota enforcement, monitoring, and health checks.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from datetime import datetime, timedelta
from typing import Dict, Any

from core.coordinators.resource_coordinator import (
    ResourceCoordinator,
    ResourceAllocation,
    ResourceUsage,
    SystemResources,
    APIQuota,
    ResourceError,
    create_resource_coordinator
)


@pytest.fixture
def resource_config():
    """Resource coordinator configuration"""
    return {
        'max_cpu_allocation': 0.8,
        'max_memory_allocation': 0.7,
        'reserve_cpu_cores': 1,
        'reserve_memory_mb': 1024,
        'enable_cost_tracking': True,
        'cost_per_api_call': 0.002,
        'cost_per_1k_tokens': 0.02,
        'daily_budget': 50.0
    }


@pytest.fixture
def resource_coordinator(resource_config):
    """Create resource coordinator instance"""
    return ResourceCoordinator(config=resource_config)


@pytest.fixture
async def initialized_coordinator(resource_coordinator):
    """Create and initialize resource coordinator"""
    with patch('psutil.cpu_count', return_value=8):
        with patch('psutil.cpu_percent', return_value=20.0):
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value.total = 16 * 1024 * 1024 * 1024  # 16GB
                mock_memory.return_value.available = 8 * 1024 * 1024 * 1024  # 8GB

                with patch('asyncio.create_task') as mock_create_task:
                    await resource_coordinator.initialize()
                    resource_coordinator.is_initialized = True
                    yield resource_coordinator


@pytest.fixture
def sample_allocation():
    """Sample resource allocation"""
    return ResourceAllocation(
        request_id="test_request_1",
        cpu_cores=2,
        memory_mb=2048,
        gpu_memory_mb=1024,
        api_quota=100,
        token_limit=10000
    )


@pytest.fixture
def sample_usage():
    """Sample resource usage"""
    return ResourceUsage(
        request_id="test_request_1",
        cpu_usage=1.5,
        memory_usage_mb=1500,
        api_calls_made=50,
        tokens_used=5000
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestResourceCoordinatorInitialization:
    """Test resource coordinator initialization"""

    async def test_initialization_success(self, resource_coordinator):
        """Test successful initialization"""
        with patch('psutil.cpu_count', return_value=4):
            with patch('psutil.cpu_percent', return_value=10.0):
                with patch('psutil.virtual_memory') as mock_memory:
                    mock_memory.return_value.total = 8 * 1024 * 1024 * 1024
                    mock_memory.return_value.available = 6 * 1024 * 1024 * 1024

                    with patch('asyncio.create_task') as mock_create_task:
                        await resource_coordinator.initialize()

                        assert resource_coordinator.is_initialized is True
                        assert mock_create_task.call_count == 3  # monitor, cleanup, quota_reset

    async def test_initialization_creates_api_quotas(self, resource_coordinator):
        """Test API quotas are created during initialization"""
        assert 'openai' in resource_coordinator.api_quotas
        assert 'schoology' in resource_coordinator.api_quotas
        assert 'canvas' in resource_coordinator.api_quotas
        assert 'roblox' in resource_coordinator.api_quotas
        assert len(resource_coordinator.api_quotas) == 4

    async def test_initialization_sets_config(self, resource_config):
        """Test configuration is applied"""
        coordinator = ResourceCoordinator(config=resource_config)

        assert coordinator.max_cpu_allocation == 0.8
        assert coordinator.max_memory_allocation == 0.7
        assert coordinator.daily_budget == 50.0
        assert coordinator.enable_cost_tracking is True

    async def test_initialization_starts_background_tasks(self, resource_coordinator):
        """Test background tasks are started"""
        with patch('psutil.cpu_count', return_value=4):
            with patch('psutil.cpu_percent', return_value=10.0):
                with patch('psutil.virtual_memory') as mock_memory:
                    mock_memory.return_value.total = 8 * 1024 * 1024 * 1024
                    mock_memory.return_value.available = 6 * 1024 * 1024 * 1024

                    with patch('asyncio.create_task') as mock_create_task:
                        await resource_coordinator.initialize()

                        # Should create tasks for monitor, cleanup, quota reset
                        assert mock_create_task.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
class TestResourceAllocation:
    """Test resource allocation functionality"""

    async def test_allocate_resources_success(self, initialized_coordinator):
        """Test successful resource allocation"""
        requirements = {
            'cpu_cores': 2,
            'memory_mb': 2048,
            'gpu_memory_mb': 1024,
            'api_quota': 100,
            'token_limit': 10000
        }

        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=6,
                total_memory_mb=16384,
                available_memory_mb=12288,
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096
            )

            allocation = await initialized_coordinator.allocate_resources('test_req_1', requirements)

            assert allocation.request_id == 'test_req_1'
            assert allocation.cpu_cores == 2
            assert allocation.memory_mb == 2048
            assert allocation.gpu_memory_mb == 1024
            assert 'test_req_1' in initialized_coordinator.allocations
            assert 'test_req_1' in initialized_coordinator.usage_tracking

    async def test_allocate_resources_insufficient_cpu(self, initialized_coordinator):
        """Test allocation with insufficient CPU"""
        requirements = {
            'cpu_cores': 10,  # More than available
            'memory_mb': 1024
        }

        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=4,
                total_memory_mb=16384,
                available_memory_mb=12288,
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096
            )

            with pytest.raises(ResourceError, match="Insufficient CPU cores"):
                await initialized_coordinator.allocate_resources('test_req_1', requirements)

    async def test_allocate_resources_insufficient_memory(self, initialized_coordinator):
        """Test allocation with insufficient memory"""
        requirements = {
            'cpu_cores': 2,
            'memory_mb': 20000  # More than available
        }

        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=6,
                total_memory_mb=16384,
                available_memory_mb=10000,
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096
            )

            with pytest.raises(ResourceError, match="Insufficient memory"):
                await initialized_coordinator.allocate_resources('test_req_1', requirements)

    async def test_allocate_resources_duplicate_request(self, initialized_coordinator):
        """Test allocation for duplicate request ID"""
        requirements = {'cpu_cores': 1, 'memory_mb': 512}

        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=6,
                total_memory_mb=16384,
                available_memory_mb=12288,
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096
            )

            # First allocation
            alloc1 = await initialized_coordinator.allocate_resources('test_req_1', requirements)

            # Second allocation with same ID should return existing
            alloc2 = await initialized_coordinator.allocate_resources('test_req_1', requirements)

            assert alloc1 == alloc2

    async def test_allocate_resources_with_ttl(self, initialized_coordinator):
        """Test allocation with custom TTL"""
        requirements = {
            'cpu_cores': 1,
            'memory_mb': 512,
            'ttl_seconds': 1800
        }

        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=6,
                total_memory_mb=16384,
                available_memory_mb=12288,
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096
            )

            allocation = await initialized_coordinator.allocate_resources('test_req_1', requirements)

            assert allocation.ttl_seconds == 1800


@pytest.mark.unit
@pytest.mark.asyncio
class TestResourceRelease:
    """Test resource release functionality"""

    async def test_release_resources_success(self, initialized_coordinator, sample_allocation):
        """Test successful resource release"""
        initialized_coordinator.allocations['test_req_1'] = sample_allocation
        initialized_coordinator.usage_tracking['test_req_1'] = ResourceUsage(request_id='test_req_1')

        with patch.object(initialized_coordinator, '_record_usage_metrics', new_callable=AsyncMock):
            result = await initialized_coordinator.release_resources('test_req_1')

            assert result is True
            assert 'test_req_1' not in initialized_coordinator.allocations
            assert 'test_req_1' not in initialized_coordinator.usage_tracking

    async def test_release_resources_not_found(self, initialized_coordinator):
        """Test release of non-existent allocation"""
        result = await initialized_coordinator.release_resources('nonexistent_req')

        assert result is False

    async def test_release_resources_records_metrics(self, initialized_coordinator, sample_allocation, sample_usage):
        """Test resource release records usage metrics"""
        initialized_coordinator.allocations['test_req_1'] = sample_allocation
        initialized_coordinator.usage_tracking['test_req_1'] = sample_usage

        with patch.object(initialized_coordinator, '_record_usage_metrics', new_callable=AsyncMock) as mock_record:
            await initialized_coordinator.release_resources('test_req_1')

            mock_record.assert_called_once()
            recorded_allocation = mock_record.call_args[0][0]
            recorded_usage = mock_record.call_args[0][1]
            assert recorded_allocation.request_id == 'test_req_1'
            assert recorded_usage.request_id == 'test_req_1'


@pytest.mark.unit
@pytest.mark.asyncio
class TestAPIQuotaManagement:
    """Test API quota checking and consumption"""

    async def test_check_api_quota_available(self, initialized_coordinator):
        """Test quota check when quota is available"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_minute_requests = 10
        quota.requests_per_minute = 60

        result = await initialized_coordinator.check_api_quota('openai', 5, 1000)

        assert result is True

    async def test_check_api_quota_minute_limit_exceeded(self, initialized_coordinator):
        """Test quota check when minute limit exceeded"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_minute_requests = 58
        quota.requests_per_minute = 60

        result = await initialized_coordinator.check_api_quota('openai', 5, 0)

        assert result is False

    async def test_check_api_quota_hour_limit_exceeded(self, initialized_coordinator):
        """Test quota check when hour limit exceeded"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_hour_requests = 3595
        quota.requests_per_hour = 3600

        result = await initialized_coordinator.check_api_quota('openai', 10, 0)

        assert result is False

    async def test_check_api_quota_token_limit_exceeded(self, initialized_coordinator):
        """Test quota check when token limit exceeded"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_minute_tokens = 149000
        quota.tokens_per_minute = 150000

        result = await initialized_coordinator.check_api_quota('openai', 1, 2000)

        assert result is False

    async def test_check_api_quota_unknown_service(self, initialized_coordinator):
        """Test quota check for unknown service"""
        result = await initialized_coordinator.check_api_quota('unknown_service', 1, 0)

        # Should allow unknown services
        assert result is True

    async def test_consume_api_quota_success(self, initialized_coordinator):
        """Test successful quota consumption"""
        quota = initialized_coordinator.api_quotas['openai']
        initial_requests = quota.current_minute_requests
        initial_tokens = quota.current_minute_tokens

        result = await initialized_coordinator.consume_api_quota('openai', 5, 1000)

        assert result is True
        assert quota.current_minute_requests == initial_requests + 5
        assert quota.current_minute_tokens == initial_tokens + 1000

    async def test_consume_api_quota_exceeds_limit(self, initialized_coordinator):
        """Test quota consumption when limit would be exceeded"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_minute_requests = 59
        quota.requests_per_minute = 60

        result = await initialized_coordinator.consume_api_quota('openai', 5, 0)

        assert result is False
        assert quota.current_minute_requests == 59  # Should not be consumed

    async def test_consume_api_quota_tracks_usage(self, initialized_coordinator, sample_allocation):
        """Test quota consumption tracks usage for specific request"""
        initialized_coordinator.allocations['test_req_1'] = sample_allocation
        initialized_coordinator.usage_tracking['test_req_1'] = ResourceUsage(request_id='test_req_1')

        await initialized_coordinator.consume_api_quota('openai', 3, 1500, 'test_req_1')

        usage = initialized_coordinator.usage_tracking['test_req_1']
        assert usage.api_calls_made == 3
        assert usage.tokens_used == 1500

    async def test_consume_api_quota_tracks_costs(self, initialized_coordinator):
        """Test quota consumption tracks costs"""
        daily_key = datetime.now().strftime('%Y-%m-%d')

        await initialized_coordinator.consume_api_quota('openai', 10, 5000)

        # Should track both request and token costs
        request_cost_key = f"{daily_key}_openai_requests"
        token_cost_key = f"{daily_key}_openai_tokens"

        assert request_cost_key in initialized_coordinator.cost_tracking
        assert token_cost_key in initialized_coordinator.cost_tracking


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuotaResets:
    """Test quota reset functionality"""

    async def test_reset_quota_counters_minute(self, initialized_coordinator):
        """Test minute quota counter reset"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_minute_requests = 50
        quota.current_minute_tokens = 10000
        quota.last_reset_minute = datetime.now() - timedelta(minutes=1)

        now = datetime.now()
        await initialized_coordinator._reset_quota_counters(quota, now)

        assert quota.current_minute_requests == 0
        assert quota.current_minute_tokens == 0

    async def test_reset_quota_counters_hour(self, initialized_coordinator):
        """Test hour quota counter reset"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_hour_requests = 1000
        quota.current_hour_tokens = 50000
        quota.last_reset_hour = datetime.now() - timedelta(hours=1)

        now = datetime.now()
        await initialized_coordinator._reset_quota_counters(quota, now)

        assert quota.current_hour_requests == 0
        assert quota.current_hour_tokens == 0

    async def test_reset_quota_counters_day(self, initialized_coordinator):
        """Test day quota counter reset"""
        quota = initialized_coordinator.api_quotas['openai']
        quota.current_day_requests = 5000
        quota.last_reset_day = datetime.now() - timedelta(days=1)

        now = datetime.now()
        await initialized_coordinator._reset_quota_counters(quota, now)

        assert quota.current_day_requests == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestSystemResourceMonitoring:
    """Test system resource monitoring"""

    async def test_get_current_system_resources(self, initialized_coordinator):
        """Test getting current system resources"""
        with patch('psutil.cpu_count', return_value=8):
            with patch('psutil.cpu_percent', return_value=25.0):
                with patch('psutil.virtual_memory') as mock_memory:
                    mock_memory.return_value.total = 16 * 1024 * 1024 * 1024
                    mock_memory.return_value.available = 10 * 1024 * 1024 * 1024

                    resources = await initialized_coordinator._get_current_system_resources()

                    assert resources.total_cpu_cores == 8
                    assert resources.total_memory_mb == 16384
                    assert resources.available_memory_mb > 0

    async def test_get_utilization(self, initialized_coordinator):
        """Test resource utilization calculation"""
        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=4,  # 50% utilized
                total_memory_mb=16384,
                available_memory_mb=8192,  # 50% utilized
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096  # 50% utilized
            )

            utilization = await initialized_coordinator.get_utilization()

            assert utilization['cpu_utilization'] == 50.0
            assert utilization['memory_utilization'] == 50.0
            assert utilization['gpu_utilization'] == 50.0

    async def test_update_system_resources(self, initialized_coordinator):
        """Test updating system resources"""
        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            mock_resources.return_value = SystemResources(
                total_cpu_cores=8,
                available_cpu_cores=6,
                total_memory_mb=16384,
                available_memory_mb=12288,
                total_gpu_memory_mb=8192,
                available_gpu_memory_mb=4096
            )

            with patch.object(initialized_coordinator, '_check_resource_alerts', new_callable=AsyncMock):
                await initialized_coordinator._update_system_resources()

                assert len(initialized_coordinator.resource_history) == 1

    async def test_check_resource_alerts_cpu(self, initialized_coordinator):
        """Test CPU usage alerts"""
        resources = SystemResources(
            total_cpu_cores=8,
            available_cpu_cores=0,  # 100% utilized
            total_memory_mb=16384,
            available_memory_mb=12288,
            total_gpu_memory_mb=8192,
            available_gpu_memory_mb=4096
        )

        # Should log warning for high CPU usage
        await initialized_coordinator._check_resource_alerts(resources)

    async def test_check_resource_alerts_memory(self, initialized_coordinator):
        """Test memory usage alerts"""
        resources = SystemResources(
            total_cpu_cores=8,
            available_cpu_cores=6,
            total_memory_mb=16384,
            available_memory_mb=1000,  # ~94% utilized
            total_gpu_memory_mb=8192,
            available_gpu_memory_mb=4096
        )

        # Should log warning for high memory usage
        await initialized_coordinator._check_resource_alerts(resources)


@pytest.mark.unit
@pytest.mark.asyncio
class TestCostTracking:
    """Test cost tracking functionality"""

    async def test_get_daily_cost(self, initialized_coordinator):
        """Test daily cost calculation"""
        daily_key = datetime.now().strftime('%Y-%m-%d')
        initialized_coordinator.cost_tracking[f"{daily_key}_openai_requests"] = 5.00
        initialized_coordinator.cost_tracking[f"{daily_key}_openai_tokens"] = 3.50
        initialized_coordinator.cost_tracking[f"{daily_key}_roblox_requests"] = 2.25

        daily_cost = await initialized_coordinator._get_daily_cost()

        assert daily_cost == 10.75

    async def test_record_usage_metrics(self, initialized_coordinator, sample_allocation, sample_usage):
        """Test recording usage metrics"""
        sample_usage.start_time = datetime.now() - timedelta(hours=2)

        await initialized_coordinator._record_usage_metrics(sample_allocation, sample_usage)

        # Should have usage metrics recorded
        assert 'usage_metrics' in initialized_coordinator.cost_tracking

    async def test_calculate_efficiency_score(self, initialized_coordinator, sample_allocation, sample_usage):
        """Test efficiency score calculation"""
        # 75% CPU efficiency (1.5 / 2)
        # 73.2% memory efficiency (1500 / 2048)
        # 50% API efficiency (50 / 100)
        # 50% token efficiency (5000 / 10000)

        score = initialized_coordinator._calculate_efficiency_score(sample_allocation, sample_usage)

        # Average of all efficiencies
        assert 60 <= score <= 65


@pytest.mark.unit
@pytest.mark.asyncio
class TestOptimization:
    """Test resource optimization functionality"""

    async def test_optimize_resource_allocation(self, initialized_coordinator):
        """Test optimization recommendations"""
        with patch.object(initialized_coordinator, '_analyze_allocation_patterns', new_callable=AsyncMock) as mock_analyze:
            with patch.object(initialized_coordinator, '_analyze_api_efficiency', new_callable=AsyncMock) as mock_api:
                with patch.object(initialized_coordinator, '_analyze_cost_efficiency', new_callable=AsyncMock) as mock_cost:
                    mock_analyze.return_value = {
                        'avg_cpu_utilization': 40.0,
                        'avg_memory_utilization': 50.0
                    }
                    mock_api.return_value = {
                        'wasted_quota': 25.0,
                        'efficiency': 75.0
                    }
                    mock_cost.return_value = {
                        'potential_daily_savings': 6.50
                    }

                    report = await initialized_coordinator.optimize_resource_allocation()

                    assert 'recommendations' in report
                    assert 'potential_savings' in report
                    assert 'efficiency_metrics' in report
                    assert len(report['recommendations']) > 0

    async def test_analyze_allocation_patterns(self, initialized_coordinator, sample_allocation):
        """Test allocation pattern analysis"""
        # Create test allocations and usage
        initialized_coordinator.allocations['test_req_1'] = sample_allocation
        initialized_coordinator.usage_tracking['test_req_1'] = ResourceUsage(
            request_id='test_req_1',
            cpu_usage=1.5,
            memory_usage_mb=1500
        )

        analysis = await initialized_coordinator._analyze_allocation_patterns()

        assert 'avg_cpu_utilization' in analysis
        assert 'avg_memory_utilization' in analysis
        assert 'total_requests_tracked' in analysis
        assert analysis['total_requests_tracked'] == 1

    async def test_analyze_api_efficiency(self, initialized_coordinator, sample_allocation, sample_usage):
        """Test API efficiency analysis"""
        initialized_coordinator.allocations['test_req_1'] = sample_allocation
        initialized_coordinator.usage_tracking['test_req_1'] = sample_usage

        efficiency = await initialized_coordinator._analyze_api_efficiency()

        assert 'efficiency' in efficiency
        assert 'wasted_quota' in efficiency
        assert efficiency['total_allocated'] == 100
        assert efficiency['total_used'] == 50
        assert efficiency['efficiency'] == 50.0

    async def test_analyze_cost_efficiency(self, initialized_coordinator):
        """Test cost efficiency analysis"""
        daily_key = datetime.now().strftime('%Y-%m-%d')
        initialized_coordinator.cost_tracking[f"{daily_key}_openai_requests"] = 10.00

        with patch.object(initialized_coordinator, '_analyze_api_efficiency', new_callable=AsyncMock) as mock_api:
            with patch.object(initialized_coordinator, '_analyze_allocation_patterns', new_callable=AsyncMock) as mock_alloc:
                mock_api.return_value = {'wasted_quota': 20.0}
                mock_alloc.return_value = {
                    'avg_cpu_utilization': 60.0,
                    'avg_memory_utilization': 70.0
                }

                analysis = await initialized_coordinator._analyze_cost_efficiency()

                assert 'current_daily_cost' in analysis
                assert 'wasted_api_cost' in analysis
                assert 'potential_daily_savings' in analysis
                assert analysis['current_daily_cost'] == 10.00


@pytest.mark.unit
@pytest.mark.asyncio
class TestResourceStatus:
    """Test resource status reporting"""

    async def test_get_resource_status(self, initialized_coordinator):
        """Test comprehensive resource status"""
        with patch.object(initialized_coordinator, '_get_current_system_resources', new_callable=AsyncMock) as mock_resources:
            with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
                with patch.object(initialized_coordinator, '_get_current_alerts', new_callable=AsyncMock) as mock_alerts:
                    mock_resources.return_value = SystemResources(
                        total_cpu_cores=8,
                        available_cpu_cores=6,
                        total_memory_mb=16384,
                        available_memory_mb=12288,
                        total_gpu_memory_mb=8192,
                        available_gpu_memory_mb=4096
                    )
                    mock_util.return_value = {
                        'cpu_utilization': 25.0,
                        'memory_utilization': 25.0,
                        'gpu_utilization': 50.0,
                        'active_allocations': 0
                    }
                    mock_alerts.return_value = []

                    status = await initialized_coordinator.get_resource_status()

                    assert 'system_resources' in status
                    assert 'utilization' in status
                    assert 'active_allocations' in status
                    assert 'quota_status' in status
                    assert 'cost_status' in status
                    assert 'alerts' in status

    async def test_get_current_alerts(self, initialized_coordinator):
        """Test current alerts retrieval"""
        with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
            mock_util.return_value = {
                'cpu_utilization': 95.0,  # Above threshold
                'memory_utilization': 90.0  # Above threshold
            }

            alerts = await initialized_coordinator._get_current_alerts()

            assert len(alerts) >= 2
            assert any('CPU' in alert for alert in alerts)
            assert any('memory' in alert for alert in alerts)


@pytest.mark.unit
@pytest.mark.asyncio
class TestBackgroundTasks:
    """Test background task operations"""

    async def test_resource_monitor_task(self, initialized_coordinator):
        """Test resource monitor background task"""
        initialized_coordinator.is_initialized = True

        with patch.object(initialized_coordinator, '_update_system_resources', new_callable=AsyncMock) as mock_update:
            with patch.object(initialized_coordinator, '_update_usage_tracking', new_callable=AsyncMock) as mock_usage:
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    task = asyncio.create_task(initialized_coordinator._resource_monitor())

                    # Give it time to run
                    await asyncio.sleep(0.1)

                    initialized_coordinator.is_initialized = False
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    async def test_cleanup_expired_allocations(self, initialized_coordinator):
        """Test cleanup of expired allocations"""
        # Create expired allocation
        expired_allocation = ResourceAllocation(
            request_id='expired_req',
            cpu_cores=1,
            memory_mb=512,
            allocated_time=datetime.now() - timedelta(hours=2),
            ttl_seconds=3600  # 1 hour TTL
        )

        initialized_coordinator.allocations['expired_req'] = expired_allocation
        initialized_coordinator.usage_tracking['expired_req'] = ResourceUsage(request_id='expired_req')

        initialized_coordinator.is_initialized = True

        with patch('asyncio.sleep', new_callable=AsyncMock):
            with patch.object(initialized_coordinator, '_record_usage_metrics', new_callable=AsyncMock):
                task = asyncio.create_task(initialized_coordinator._cleanup_expired_allocations())

                # Give it time to run
                await asyncio.sleep(0.1)

                initialized_coordinator.is_initialized = False
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def test_quota_reset_scheduler(self, initialized_coordinator):
        """Test quota reset scheduler"""
        initialized_coordinator.is_initialized = True

        with patch.object(initialized_coordinator, '_reset_quota_counters', new_callable=AsyncMock) as mock_reset:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                task = asyncio.create_task(initialized_coordinator._quota_reset_scheduler())

                # Give it time to run
                await asyncio.sleep(0.1)

                initialized_coordinator.is_initialized = False
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthCheck:
    """Test health check functionality"""

    async def test_get_health_healthy(self, initialized_coordinator):
        """Test health check with healthy system"""
        with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
            with patch.object(initialized_coordinator, '_get_current_alerts', new_callable=AsyncMock) as mock_alerts:
                mock_util.return_value = {
                    'cpu_utilization': 50.0,
                    'memory_utilization': 50.0,
                    'gpu_utilization': 50.0,
                    'active_allocations': 2
                }
                mock_alerts.return_value = []

                health = await initialized_coordinator.get_health()

                assert health['status'] == 'healthy'
                assert 'utilization' in health
                assert 'alerts' in health

    async def test_get_health_degraded(self, initialized_coordinator):
        """Test health check with degraded system"""
        with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
            with patch.object(initialized_coordinator, '_get_current_alerts', new_callable=AsyncMock) as mock_alerts:
                mock_util.return_value = {
                    'cpu_utilization': 92.0,
                    'memory_utilization': 88.0,
                    'gpu_utilization': 50.0,
                    'active_allocations': 5
                }
                mock_alerts.return_value = ['High CPU utilization: 92.0%']

                health = await initialized_coordinator.get_health()

                assert health['status'] == 'degraded'

    async def test_get_health_unhealthy(self, initialized_coordinator):
        """Test health check with unhealthy system"""
        with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
            with patch.object(initialized_coordinator, '_get_current_alerts', new_callable=AsyncMock) as mock_alerts:
                mock_util.return_value = {
                    'cpu_utilization': 97.0,
                    'memory_utilization': 96.0,
                    'gpu_utilization': 95.0,
                    'active_allocations': 10
                }
                mock_alerts.return_value = ['High CPU utilization: 97.0%', 'High memory utilization: 96.0%']

                health = await initialized_coordinator.get_health()

                assert health['status'] == 'unhealthy'

    async def test_get_health_checks_background_tasks(self, initialized_coordinator):
        """Test health check includes background task status"""
        # Create mock tasks
        initialized_coordinator.monitor_task = AsyncMock()
        initialized_coordinator.monitor_task.done.return_value = False
        initialized_coordinator.cleanup_task = AsyncMock()
        initialized_coordinator.cleanup_task.done.return_value = False
        initialized_coordinator.quota_reset_task = AsyncMock()
        initialized_coordinator.quota_reset_task.done.return_value = False

        with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
            with patch.object(initialized_coordinator, '_get_current_alerts', new_callable=AsyncMock) as mock_alerts:
                mock_util.return_value = {
                    'cpu_utilization': 50.0,
                    'memory_utilization': 50.0,
                    'gpu_utilization': 50.0,
                    'active_allocations': 0
                }
                mock_alerts.return_value = []

                health = await initialized_coordinator.get_health()

                assert health['background_tasks_running'] is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestContextManager:
    """Test resource context manager"""

    async def test_resource_context_allocates_and_releases(self, initialized_coordinator):
        """Test context manager allocates and releases resources"""
        requirements = {'cpu_cores': 1, 'memory_mb': 512}

        with patch.object(initialized_coordinator, 'allocate_resources', new_callable=AsyncMock) as mock_allocate:
            with patch.object(initialized_coordinator, 'release_resources', new_callable=AsyncMock) as mock_release:
                mock_allocate.return_value = ResourceAllocation(
                    request_id='ctx_test',
                    cpu_cores=1,
                    memory_mb=512
                )

                async with initialized_coordinator.resource_context('ctx_test', requirements) as allocation:
                    assert allocation.request_id == 'ctx_test'

                # Should release after exiting context
                mock_release.assert_called_once_with('ctx_test')

    async def test_resource_context_releases_on_exception(self, initialized_coordinator):
        """Test context manager releases resources on exception"""
        requirements = {'cpu_cores': 1, 'memory_mb': 512}

        with patch.object(initialized_coordinator, 'allocate_resources', new_callable=AsyncMock) as mock_allocate:
            with patch.object(initialized_coordinator, 'release_resources', new_callable=AsyncMock) as mock_release:
                mock_allocate.return_value = ResourceAllocation(
                    request_id='ctx_test',
                    cpu_cores=1,
                    memory_mb=512
                )

                try:
                    async with initialized_coordinator.resource_context('ctx_test', requirements):
                        raise RuntimeError("Test error")
                except RuntimeError:
                    pass

                # Should still release on exception
                mock_release.assert_called_once_with('ctx_test')


@pytest.mark.unit
@pytest.mark.asyncio
class TestFastAPIRoutes:
    """Test FastAPI route registration"""

    async def test_routes_registered(self, resource_coordinator):
        """Test all routes are registered"""
        routes = [route.path for route in resource_coordinator.app.routes]

        assert '/allocate' in routes
        assert '/status' in routes
        assert '/optimize' in routes
        assert '/metrics' in routes
        assert '/health' in routes

    async def test_quota_routes_registered(self, resource_coordinator):
        """Test quota-related routes"""
        routes = [route.path for route in resource_coordinator.app.routes]

        # Check for quota routes with service parameter
        quota_routes = [r for r in routes if 'quota' in r]
        assert len(quota_routes) >= 2


@pytest.mark.unit
@pytest.mark.asyncio
class TestDataClasses:
    """Test dataclass properties"""

    def test_resource_allocation_expiry(self):
        """Test resource allocation expiration check"""
        # Create expired allocation
        expired_alloc = ResourceAllocation(
            request_id='test',
            cpu_cores=1,
            memory_mb=512,
            allocated_time=datetime.now() - timedelta(hours=2),
            ttl_seconds=3600  # 1 hour
        )

        assert expired_alloc.is_expired is True

    def test_resource_allocation_not_expired(self):
        """Test non-expired allocation"""
        active_alloc = ResourceAllocation(
            request_id='test',
            cpu_cores=1,
            memory_mb=512,
            allocated_time=datetime.now(),
            ttl_seconds=3600
        )

        assert active_alloc.is_expired is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestMetrics:
    """Test metrics collection"""

    async def test_get_metrics(self, initialized_coordinator):
        """Test metrics retrieval"""
        with patch.object(initialized_coordinator, 'get_utilization', new_callable=AsyncMock) as mock_util:
            with patch.object(initialized_coordinator, 'optimize_resource_allocation', new_callable=AsyncMock) as mock_opt:
                mock_util.return_value = {
                    'cpu_utilization': 50.0,
                    'memory_utilization': 60.0,
                    'gpu_utilization': 40.0,
                    'active_allocations': 3
                }
                mock_opt.return_value = {
                    'recommendations': [],
                    'potential_savings': {},
                    'efficiency_metrics': {}
                }

                metrics = await initialized_coordinator.get_metrics()

                assert 'utilization' in metrics
                assert 'optimization' in metrics
                assert 'allocations' in metrics
                assert 'api_quotas' in metrics


@pytest.mark.unit
@pytest.mark.asyncio
class TestShutdownAndCleanup:
    """Test coordinator shutdown"""

    async def test_shutdown_cancels_background_tasks(self, initialized_coordinator):
        """Test shutdown cancels all background tasks"""
        # Create mock tasks
        initialized_coordinator.monitor_task = AsyncMock()
        initialized_coordinator.cleanup_task = AsyncMock()
        initialized_coordinator.quota_reset_task = AsyncMock()

        await initialized_coordinator.shutdown()

        initialized_coordinator.monitor_task.cancel.assert_called_once()
        initialized_coordinator.cleanup_task.cancel.assert_called_once()
        initialized_coordinator.quota_reset_task.cancel.assert_called_once()
        assert initialized_coordinator.is_initialized is False

    async def test_shutdown_releases_all_allocations(self, initialized_coordinator):
        """Test shutdown releases all active allocations"""
        # Create allocations
        initialized_coordinator.allocations['req_1'] = ResourceAllocation(
            request_id='req_1',
            cpu_cores=1,
            memory_mb=512
        )
        initialized_coordinator.allocations['req_2'] = ResourceAllocation(
            request_id='req_2',
            cpu_cores=2,
            memory_mb=1024
        )

        # Create mock tasks
        initialized_coordinator.monitor_task = AsyncMock()
        initialized_coordinator.cleanup_task = AsyncMock()
        initialized_coordinator.quota_reset_task = AsyncMock()

        with patch.object(initialized_coordinator, '_record_usage_metrics', new_callable=AsyncMock):
            await initialized_coordinator.shutdown()

            # All allocations should be released
            assert len(initialized_coordinator.allocations) == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestConvenienceFunctions:
    """Test convenience functions"""

    async def test_create_resource_coordinator(self):
        """Test convenience function creates and initializes coordinator"""
        config = {'daily_budget': 100.0}

        with patch('psutil.cpu_count', return_value=4):
            with patch('psutil.cpu_percent', return_value=10.0):
                with patch('psutil.virtual_memory') as mock_memory:
                    mock_memory.return_value.total = 8 * 1024 * 1024 * 1024
                    mock_memory.return_value.available = 6 * 1024 * 1024 * 1024

                    with patch('asyncio.create_task'):
                        coordinator = await create_resource_coordinator(config=config)

                        assert coordinator is not None
                        assert isinstance(coordinator, ResourceCoordinator)
                        assert coordinator.is_initialized is True
                        assert coordinator.daily_budget == 100.0
