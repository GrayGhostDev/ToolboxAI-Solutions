"""
Integration tests for performance optimization modules.

Tests end-to-end performance optimization workflows including cache warming,
concurrent request handling, optimization lifecycle management, and
cross-component integration.

Target: >95% integration coverage for performance optimization systems.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List

from apps.backend.core.performance_optimization import (
    PerformanceOptimizationManager, get_performance_manager,
    performance_optimization_context, initialize_performance_optimizations,
    get_optimization_health, get_optimization_metrics, warm_all_caches,
    get_optimization_status_for_health_check
)


@pytest.mark.integration
class TestPerformanceOptimizationManager:
    """Test the main performance optimization manager."""

    @pytest.fixture
    def manager(self):
        """Create fresh performance optimization manager."""
        return PerformanceOptimizationManager()

    @pytest.fixture
    def mock_all_optimizations(self):
        """Mock all optimization systems."""
        with patch('apps.backend.core.performance_optimization.initialize_cache') as mock_cache, \
             patch('apps.backend.core.performance_optimization.initialize_db_optimization') as mock_db, \
             patch('apps.backend.core.performance_optimization.get_optimized_pusher_service') as mock_pusher:

            # Mock successful initialization
            mock_cache.return_value = None
            mock_db.return_value = None
            mock_pusher_instance = AsyncMock()
            mock_pusher.return_value = mock_pusher_instance

            yield {
                'cache': mock_cache,
                'db': mock_db,
                'pusher': mock_pusher,
                'pusher_instance': mock_pusher_instance
            }

    async def test_initialize_all_optimizations_success(self, manager, mock_all_optimizations):
        """Test successful initialization of all optimization systems."""
        result = await manager.initialize_all_optimizations()

        assert result["status"] == "completed"
        assert manager.initialized is True
        assert manager.initialization_time is not None
        assert "cache" in result["successful_services"]
        assert "database" in result["successful_services"]
        assert "pusher" in result["successful_services"]
        assert len(result["failed_services"]) == 0

        # Verify all services were initialized
        mock_all_optimizations['cache'].assert_called_once()
        mock_all_optimizations['db'].assert_called_once()
        mock_all_optimizations['pusher'].assert_called_once()

    async def test_initialize_partial_failure(self, manager, mock_all_optimizations):
        """Test initialization with some services failing."""
        # Make database initialization fail
        mock_all_optimizations['db'].side_effect = Exception("Database connection failed")

        result = await manager.initialize_all_optimizations()

        assert result["status"] == "partial_failure"
        assert manager.initialized is True  # Still initialized if at least one service succeeds
        assert "cache" in result["successful_services"]
        assert "pusher" in result["successful_services"]
        assert "database" in result["failed_services"]

        # Verify services status
        assert manager.services_status["cache"]["status"] == "initialized"
        assert manager.services_status["database"]["status"] == "failed"
        assert manager.services_status["pusher"]["status"] == "initialized"

    async def test_initialize_all_failures(self, manager, mock_all_optimizations):
        """Test initialization with all services failing."""
        # Make all services fail
        mock_all_optimizations['cache'].side_effect = Exception("Cache failed")
        mock_all_optimizations['db'].side_effect = Exception("Database failed")
        mock_all_optimizations['pusher'].side_effect = Exception("Pusher failed")

        result = await manager.initialize_all_optimizations()

        assert result["status"] == "partial_failure"
        assert manager.initialized is False
        assert len(result["successful_services"]) == 0
        assert len(result["failed_services"]) == 3

    async def test_already_initialized(self, manager, mock_all_optimizations):
        """Test that double initialization is prevented."""
        # First initialization
        await manager.initialize_all_optimizations()
        first_init_time = manager.initialization_time

        # Second initialization should be skipped
        result = await manager.initialize_all_optimizations()

        assert result["status"] == "already_initialized"
        assert manager.initialization_time == first_init_time

        # Services should only be initialized once
        mock_all_optimizations['cache'].assert_called_once()

    @patch('apps.backend.core.performance_optimization.get_cache_health')
    @patch('apps.backend.core.performance_optimization.get_db_health')
    @patch('apps.backend.core.performance_optimization.get_pusher_health')
    async def test_get_comprehensive_health_status_all_healthy(
        self, mock_pusher_health, mock_db_health, mock_cache_health, manager
    ):
        """Test comprehensive health status when all systems are healthy."""
        # Mock all systems as healthy
        mock_cache_health.return_value = {"status": "healthy", "stats": {"hits": 100}}
        mock_db_health.return_value = {"status": "healthy", "connection_pool": {"active": 5}}
        mock_pusher_health.return_value = {"status": "healthy", "performance": {"events_sent": 50}}

        manager.initialized = True
        manager.initialization_time = datetime.now()

        health = await manager.get_comprehensive_health_status()

        assert health["overall_status"] == "healthy"
        assert health["optimization_enabled"] is True
        assert health["services"]["cache"]["status"] == "healthy"
        assert health["services"]["database"]["status"] == "healthy"
        assert health["services"]["pusher"]["status"] == "healthy"
        assert "timestamp" in health

    @patch('apps.backend.core.performance_optimization.get_cache_health')
    @patch('apps.backend.core.performance_optimization.get_db_health')
    @patch('apps.backend.core.performance_optimization.get_pusher_health')
    async def test_get_comprehensive_health_status_degraded(
        self, mock_pusher_health, mock_db_health, mock_cache_health, manager
    ):
        """Test comprehensive health status when some systems are degraded."""
        # Mock mixed health status
        mock_cache_health.return_value = {"status": "healthy"}
        mock_db_health.return_value = {"status": "unhealthy", "error": "Connection timeout"}
        mock_pusher_health.return_value = {"status": "healthy"}

        health = await manager.get_comprehensive_health_status()

        assert health["overall_status"] == "degraded"
        assert health["services"]["database"]["status"] == "unhealthy"

    @patch('apps.backend.core.performance_optimization.get_cache_health')
    @patch('apps.backend.core.performance_optimization.get_db_health')
    @patch('apps.backend.core.performance_optimization.get_pusher_health')
    async def test_get_comprehensive_health_status_with_errors(
        self, mock_pusher_health, mock_db_health, mock_cache_health, manager
    ):
        """Test comprehensive health status when health checks raise errors."""
        # Mock health check errors
        mock_cache_health.side_effect = Exception("Cache health check failed")
        mock_db_health.return_value = {"status": "healthy"}
        mock_pusher_health.return_value = {"status": "healthy"}

        health = await manager.get_comprehensive_health_status()

        assert health["overall_status"] == "degraded"
        assert health["services"]["cache"]["status"] == "unhealthy"
        assert "error" in health["services"]["cache"]

    @patch('apps.backend.core.performance_optimization.get_cache_health')
    @patch('apps.backend.core.performance_optimization.get_db_health')
    @patch('apps.backend.core.performance_optimization.get_pusher_health')
    async def test_get_performance_metrics(
        self, mock_pusher_health, mock_db_health, mock_cache_health, manager
    ):
        """Test getting comprehensive performance metrics."""
        # Mock health responses with metrics
        mock_cache_health.return_value = {
            "status": "healthy",
            "stats": {"hits": 1500, "misses": 100, "hit_rate": 0.94}
        }
        mock_db_health.return_value = {
            "status": "healthy",
            "connection_pool": {"size": 20, "active": 8},
            "query_performance": {"avg_time": 0.045, "slow_queries": 2},
            "prepared_statements": {"usage": 250}
        }
        mock_pusher_health.return_value = {
            "status": "healthy",
            "performance": {"events_sent": 500, "latency": 0.025}
        }

        manager.initialized = True

        metrics = await manager.get_performance_metrics()

        assert metrics["optimization_enabled"] is True
        assert metrics["cache"]["hits"] == 1500
        assert metrics["database"]["connection_pool"]["size"] == 20
        assert metrics["pusher"]["events_sent"] == 500
        assert "timestamp" in metrics

    async def test_warm_caches_not_initialized(self, manager):
        """Test cache warming when optimizations are not initialized."""
        result = await manager.warm_caches()

        assert result["status"] == "skipped"
        assert result["reason"] == "Performance optimizations not initialized"

    @patch('apps.backend.core.cache.warmer')
    @patch('apps.backend.core.db_optimization.optimizer')
    @patch('apps.backend.core.cache.cache')
    async def test_warm_caches_success(self, mock_cache, mock_optimizer, mock_warmer, manager):
        """Test successful cache warming."""
        manager.initialized = True

        # Mock successful cache warming operations
        mock_warmer.warm_user_dashboard = AsyncMock()
        mock_optimizer.execute_optimized_query = AsyncMock(return_value=[{"count": 1}])
        mock_cache.set = AsyncMock()

        result = await manager.warm_caches()

        assert result["status"] == "completed"
        assert result["successful_warmups"] == 3  # dashboard, query, api caches
        assert result["total_warmups"] == 3

        # Verify warming operations were called
        assert mock_warmer.warm_user_dashboard.call_count == 4  # 4 sample users
        assert mock_optimizer.execute_optimized_query.call_count >= 2
        assert mock_cache.set.call_count >= 3

    @patch('apps.backend.core.cache.warmer')
    async def test_warm_caches_with_errors(self, mock_warmer, manager):
        """Test cache warming with some operations failing."""
        manager.initialized = True

        # Mock some operations failing
        mock_warmer.warm_user_dashboard = AsyncMock(side_effect=Exception("Cache warming failed"))

        result = await manager.warm_caches()

        assert result["status"] == "completed"
        assert result["successful_warmups"] < result["total_warmups"]


@pytest.mark.integration
class TestGlobalPerformanceManager:
    """Test global performance manager functionality."""

    def test_get_performance_manager_singleton(self):
        """Test singleton behavior of get_performance_manager."""
        manager1 = get_performance_manager()
        manager2 = get_performance_manager()

        assert manager1 is manager2
        assert isinstance(manager1, PerformanceOptimizationManager)

    def test_performance_manager_state_persistence(self):
        """Test that performance manager state persists across calls."""
        manager = get_performance_manager()

        # Modify state
        manager.initialized = True
        manager.initialization_time = datetime.now()

        # Get manager again and verify state persisted
        manager2 = get_performance_manager()
        assert manager2.initialized is True
        assert manager2.initialization_time is not None


@pytest.mark.integration
class TestPerformanceOptimizationContext:
    """Test performance optimization context manager."""

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_performance_optimization_context_success(self, mock_get_manager):
        """Test successful context manager usage."""
        mock_manager = AsyncMock()
        mock_manager.initialize_all_optimizations = AsyncMock(
            return_value={"status": "completed"}
        )
        mock_manager.warm_caches = AsyncMock(
            return_value={"status": "completed"}
        )
        mock_get_manager.return_value = mock_manager

        async with performance_optimization_context() as manager:
            assert manager == mock_manager

        # Verify initialization and warming were called
        mock_manager.initialize_all_optimizations.assert_called_once()
        mock_manager.warm_caches.assert_called_once()

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_performance_optimization_context_with_error(self, mock_get_manager):
        """Test context manager with error inside context."""
        mock_manager = AsyncMock()
        mock_manager.initialize_all_optimizations = AsyncMock()
        mock_manager.warm_caches = AsyncMock()
        mock_get_manager.return_value = mock_manager

        with pytest.raises(ValueError):
            async with performance_optimization_context():
                raise ValueError("Test error")

        # Verify initialization still occurred
        mock_manager.initialize_all_optimizations.assert_called_once()


@pytest.mark.integration
class TestConvenienceFunctions:
    """Test convenience functions for performance optimization."""

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_initialize_performance_optimizations(self, mock_get_manager):
        """Test initialize_performance_optimizations convenience function."""
        mock_manager = Mock()
        mock_manager.initialize_all_optimizations = AsyncMock(
            return_value={"status": "completed"}
        )
        mock_get_manager.return_value = mock_manager

        result = await initialize_performance_optimizations()

        assert result["status"] == "completed"
        mock_manager.initialize_all_optimizations.assert_called_once()

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_get_optimization_health(self, mock_get_manager):
        """Test get_optimization_health convenience function."""
        mock_manager = Mock()
        mock_manager.get_comprehensive_health_status = AsyncMock(
            return_value={"overall_status": "healthy"}
        )
        mock_get_manager.return_value = mock_manager

        result = await get_optimization_health()

        assert result["overall_status"] == "healthy"
        mock_manager.get_comprehensive_health_status.assert_called_once()

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_get_optimization_metrics(self, mock_get_manager):
        """Test get_optimization_metrics convenience function."""
        mock_manager = Mock()
        mock_manager.get_performance_metrics = AsyncMock(
            return_value={"optimization_enabled": True}
        )
        mock_get_manager.return_value = mock_manager

        result = await get_optimization_metrics()

        assert result["optimization_enabled"] is True
        mock_manager.get_performance_metrics.assert_called_once()

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_warm_all_caches(self, mock_get_manager):
        """Test warm_all_caches convenience function."""
        mock_manager = Mock()
        mock_manager.warm_caches = AsyncMock(
            return_value={"status": "completed", "successful_warmups": 3}
        )
        mock_get_manager.return_value = mock_manager

        result = await warm_all_caches()

        assert result["status"] == "completed"
        assert result["successful_warmups"] == 3
        mock_manager.warm_caches.assert_called_once()

    @patch('apps.backend.core.performance_optimization.get_performance_manager')
    async def test_get_optimization_status_for_health_check(self, mock_get_manager):
        """Test get_optimization_status_for_health_check function."""
        mock_manager = Mock()
        mock_manager.initialized = True
        mock_manager.initialization_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_manager.services_status = {
            "cache": {"status": "initialized"},
            "database": {"status": "initialized"},
            "pusher": {"status": "failed"}
        }
        mock_get_manager.return_value = mock_manager

        result = await get_optimization_status_for_health_check()

        expected = {
            "performance_optimization": {
                "enabled": True,
                "initialization_time": "2023-01-01T12:00:00",
                "services": {
                    "cache": "initialized",
                    "database": "initialized",
                    "pusher": "failed"
                }
            }
        }

        assert result == expected


@pytest.mark.integration
class TestPerformanceOptimizationIntegration:
    """End-to-end integration tests for performance optimization system."""

    @pytest.fixture
    def mock_all_systems(self):
        """Mock all optimization systems for integration testing."""
        mocks = {}

        # Mock cache system
        with patch('apps.backend.core.performance_optimization.initialize_cache') as mock_init_cache:
            with patch('apps.backend.core.performance_optimization.get_cache_health') as mock_cache_health:
                with patch('apps.backend.core.cache.warmer') as mock_warmer:
                    with patch('apps.backend.core.cache.cache') as mock_cache:
                        mocks['init_cache'] = mock_init_cache
                        mocks['cache_health'] = mock_cache_health
                        mocks['warmer'] = mock_warmer
                        mocks['cache'] = mock_cache

                        # Mock database system
                        with patch('apps.backend.core.performance_optimization.initialize_db_optimization') as mock_init_db:
                            with patch('apps.backend.core.performance_optimization.get_db_health') as mock_db_health:
                                with patch('apps.backend.core.db_optimization.optimizer') as mock_optimizer:
                                    mocks['init_db'] = mock_init_db
                                    mocks['db_health'] = mock_db_health
                                    mocks['optimizer'] = mock_optimizer

                                    # Mock Pusher system
                                    with patch('apps.backend.core.performance_optimization.get_optimized_pusher_service') as mock_get_pusher:
                                        with patch('apps.backend.core.performance_optimization.get_pusher_health') as mock_pusher_health:
                                            mocks['get_pusher'] = mock_get_pusher
                                            mocks['pusher_health'] = mock_pusher_health

                                            # Setup default successful responses
                                            mock_init_cache.return_value = None
                                            mock_init_db.return_value = None
                                            mock_get_pusher.return_value = AsyncMock()

                                            mock_cache_health.return_value = {"status": "healthy", "stats": {"hits": 100}}
                                            mock_db_health.return_value = {"status": "healthy", "connection_pool": {"active": 5}}
                                            mock_pusher_health.return_value = {"status": "healthy", "performance": {"events": 50}}

                                            mock_warmer.warm_user_dashboard = AsyncMock()
                                            mock_optimizer.execute_optimized_query = AsyncMock(return_value=[{"result": "ok"}])
                                            mock_cache.set = AsyncMock()

                                            yield mocks

    async def test_full_optimization_lifecycle(self, mock_all_systems):
        """Test complete optimization lifecycle from initialization to metrics."""
        # Get fresh manager
        manager = PerformanceOptimizationManager()

        # 1. Initialize all optimizations
        init_result = await manager.initialize_all_optimizations()
        assert init_result["status"] == "completed"
        assert len(init_result["successful_services"]) == 3

        # 2. Warm caches
        warm_result = await manager.warm_caches()
        assert warm_result["status"] == "completed"
        assert warm_result["successful_warmups"] >= 1

        # 3. Check health
        health = await manager.get_comprehensive_health_status()
        assert health["overall_status"] == "healthy"
        assert health["optimization_enabled"] is True

        # 4. Get metrics
        metrics = await manager.get_performance_metrics()
        assert metrics["optimization_enabled"] is True
        assert "cache" in metrics
        assert "database" in metrics
        assert "pusher" in metrics

        # 5. Get status for health check endpoint
        status = await get_optimization_status_for_health_check()
        assert status["performance_optimization"]["enabled"] is True

    async def test_concurrent_optimization_operations(self, mock_all_systems):
        """Test concurrent access to optimization systems."""
        manager = PerformanceOptimizationManager()

        # Initialize first
        await manager.initialize_all_optimizations()

        # Run multiple operations concurrently
        tasks = [
            manager.get_comprehensive_health_status(),
            manager.get_performance_metrics(),
            manager.warm_caches(),
            get_optimization_health(),
            get_optimization_metrics()
        ]

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(result is not None for result in results)

        # Specific checks
        health1, metrics1, warm_result, health2, metrics2 = results
        assert health1["overall_status"] == "healthy"
        assert metrics1["optimization_enabled"] is True
        assert warm_result["status"] == "completed"
        assert health2["overall_status"] == "healthy"
        assert metrics2["optimization_enabled"] is True

    async def test_optimization_resilience_to_failures(self, mock_all_systems):
        """Test optimization system resilience to component failures."""
        manager = PerformanceOptimizationManager()

        # Initialize successfully first
        await manager.initialize_all_optimizations()

        # Now simulate component failures during operations
        mock_all_systems['cache_health'].side_effect = Exception("Cache connection lost")
        mock_all_systems['db_health'].return_value = {"status": "unhealthy", "error": "Database timeout"}

        # Health check should handle failures gracefully
        health = await manager.get_comprehensive_health_status()

        assert health["overall_status"] == "degraded"  # Not healthy, but not completely failed
        assert health["services"]["cache"]["status"] == "unhealthy"
        assert health["services"]["database"]["status"] == "unhealthy"
        assert health["services"]["pusher"]["status"] == "healthy"  # Still working

        # Metrics should also handle failures
        metrics = await manager.get_performance_metrics()
        assert metrics["optimization_enabled"] is True
        assert "error" in metrics["cache"]
        assert "error" in metrics["database"]

    async def test_performance_optimization_with_context_manager(self, mock_all_systems):
        """Test using performance optimization with context manager."""
        async with performance_optimization_context() as manager:
            # Manager should be initialized and warmed up
            assert manager.initialized is True

            # Should be able to get health and metrics
            health = await manager.get_comprehensive_health_status()
            assert health["overall_status"] == "healthy"

            metrics = await manager.get_performance_metrics()
            assert metrics["optimization_enabled"] is True

        # After context, manager should still be accessible
        # (Context manager doesn't clean up, just initializes)
        assert manager.initialized is True

    async def test_performance_timing_measurements(self, mock_all_systems):
        """Test that performance timing is properly measured."""
        manager = PerformanceOptimizationManager()

        # Add delay to initialization to test timing
        async def slow_init():
            await asyncio.sleep(0.1)

        mock_all_systems['init_cache'].side_effect = slow_init

        start_time = time.time()
        result = await manager.initialize_all_optimizations()
        end_time = time.time()

        # Should have taken at least 0.1 seconds
        assert end_time - start_time >= 0.1

        # Timing should be recorded in result
        assert result["duration_seconds"] >= 0.1
        assert manager.initialization_time is not None

    async def test_cache_warming_comprehensive(self, mock_all_systems):
        """Test comprehensive cache warming functionality."""
        manager = PerformanceOptimizationManager()
        await manager.initialize_all_optimizations()

        # Track calls to warming functions
        warming_calls = []

        async def track_user_warming(user_id, role):
            warming_calls.append(('user', user_id, role))

        async def track_query_warming(query, params, use_cache=True):
            warming_calls.append(('query', query, params))
            return [{"result": "ok"}]

        async def track_cache_set(key, data, ttl):
            warming_calls.append(('cache', key, data))

        mock_all_systems['warmer'].warm_user_dashboard.side_effect = track_user_warming
        mock_all_systems['optimizer'].execute_optimized_query.side_effect = track_query_warming
        mock_all_systems['cache'].set.side_effect = track_cache_set

        # Perform cache warming
        result = await manager.warm_caches()

        assert result["status"] == "completed"
        assert result["successful_warmups"] == 3

        # Verify different types of warming occurred
        user_warmings = [call for call in warming_calls if call[0] == 'user']
        query_warmings = [call for call in warming_calls if call[0] == 'query']
        cache_sets = [call for call in warming_calls if call[0] == 'cache']

        assert len(user_warmings) == 4  # 4 sample users
        assert len(query_warmings) >= 2  # At least 2 common queries
        assert len(cache_sets) >= 3  # API cache entries


@pytest.mark.integration
class TestPerformanceOptimizationStressTest:
    """Stress tests for performance optimization under load."""

    @pytest.fixture
    def mock_high_load_systems(self):
        """Mock systems configured for high load testing."""
        with patch('apps.backend.core.performance_optimization.initialize_cache') as mock_init_cache:
            with patch('apps.backend.core.performance_optimization.get_cache_health') as mock_cache_health:
                with patch('apps.backend.core.performance_optimization.initialize_db_optimization') as mock_init_db:
                    with patch('apps.backend.core.performance_optimization.get_db_health') as mock_db_health:
                        with patch('apps.backend.core.performance_optimization.get_optimized_pusher_service') as mock_get_pusher:
                            with patch('apps.backend.core.performance_optimization.get_pusher_health') as mock_pusher_health:

                                # Setup responses
                                mock_init_cache.return_value = None
                                mock_init_db.return_value = None
                                mock_get_pusher.return_value = AsyncMock()

                                # Simulate realistic performance metrics
                                mock_cache_health.return_value = {
                                    "status": "healthy",
                                    "stats": {"hits": 50000, "misses": 5000, "hit_rate": 0.91}
                                }
                                mock_db_health.return_value = {
                                    "status": "healthy",
                                    "connection_pool": {"active": 18, "total": 20},
                                    "query_performance": {"avg_time": 0.035, "slow_queries": 15}
                                }
                                mock_pusher_health.return_value = {
                                    "status": "healthy",
                                    "performance": {"events_sent": 10000, "avg_latency": 0.022}
                                }

                                yield {
                                    'cache_health': mock_cache_health,
                                    'db_health': mock_db_health,
                                    'pusher_health': mock_pusher_health
                                }

    async def test_concurrent_health_checks(self, mock_high_load_systems):
        """Test many concurrent health checks."""
        manager = PerformanceOptimizationManager()
        await manager.initialize_all_optimizations()

        # Run 100 concurrent health checks
        tasks = [manager.get_comprehensive_health_status() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 100
        assert all(result["overall_status"] == "healthy" for result in results)

        # Verify health check functions were called many times
        assert mock_high_load_systems['cache_health'].call_count == 100
        assert mock_high_load_systems['db_health'].call_count == 100
        assert mock_high_load_systems['pusher_health'].call_count == 100

    async def test_concurrent_metrics_collection(self, mock_high_load_systems):
        """Test concurrent metrics collection under load."""
        manager = PerformanceOptimizationManager()
        await manager.initialize_all_optimizations()

        # Run concurrent metrics collection
        tasks = [manager.get_performance_metrics() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # All should succeed and contain metrics
        assert len(results) == 50
        assert all(result["optimization_enabled"] is True for result in results)
        assert all("cache" in result for result in results)
        assert all("database" in result for result in results)
        assert all("pusher" in result for result in results)

    async def test_rapid_initialization_attempts(self, mock_high_load_systems):
        """Test rapid concurrent initialization attempts."""
        managers = [PerformanceOptimizationManager() for _ in range(10)]

        # Try to initialize all managers concurrently
        tasks = [manager.initialize_all_optimizations() for manager in managers]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 10
        assert all(result["status"] in ["completed", "partial_failure"] for result in results)

        # All managers should be initialized
        assert all(manager.initialized for manager in managers if len(result.get("successful_services", [])) > 0 for result in results)

    async def test_performance_under_simulated_load(self, mock_high_load_systems):
        """Test performance optimization behavior under simulated load."""
        manager = PerformanceOptimizationManager()
        await manager.initialize_all_optimizations()

        # Simulate load by running various operations concurrently
        async def simulate_user_request():
            # Each "request" checks health and gets metrics
            health = await manager.get_comprehensive_health_status()
            metrics = await manager.get_performance_metrics()
            return health["overall_status"] == "healthy" and metrics["optimization_enabled"]

        # Simulate 200 concurrent "requests"
        start_time = time.time()
        tasks = [simulate_user_request() for _ in range(200)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All requests should succeed
        assert all(results)

        # Should complete in reasonable time (less than 5 seconds)
        total_time = end_time - start_time
        assert total_time < 5.0

        # Average time per request should be reasonable
        avg_time_per_request = total_time / 200
        assert avg_time_per_request < 0.1  # Less than 100ms average


if __name__ == "__main__":
    pytest.main([__file__, "-v"])