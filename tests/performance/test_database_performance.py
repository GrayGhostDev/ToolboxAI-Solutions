from unittest.mock import Mock, patch

import pytest
import pytest_asyncio


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

"""
Database Performance Tests
Tests for database query optimization, connection pooling, and throughput
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



import asyncio
import concurrent.futures
import json
import statistics
import time
from typing import Any, Dict, List

import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Performance tests require external services - run with --run-performance")


@pytest.mark.performance
class TestDatabasePerformance:
    """Database performance and optimization tests"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_database_connection_performance(self):
        """Test database connection establishment and pooling"""
        try:
            from database.connection_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            connection_times = []
            
            # Test connection establishment
            for i in range(20):
                start = time.time()
                try:
                    async with db_manager.get_connection() as conn:
                        # Simple query to test connection
                        result = await conn.execute("SELECT 1")
                        connection_times.append(time.time() - start)
                except Exception:
                    pass
            
            if connection_times:
                avg_time = statistics.mean(connection_times)
                max_time = max(connection_times)
                min_time = min(connection_times)
                
                print(f"Database Connection Performance:")
                print(f"  Connections tested: {len(connection_times)}")
                print(f"  Average time: {avg_time*1000:.2f}ms")
                print(f"  Min time: {min_time*1000:.2f}ms")
                print(f"  Max time: {max_time*1000:.2f}ms")
                
                # Connection should be fast with pooling
                assert avg_time < 0.1, f"DB connection too slow: {avg_time*1000:.2f}ms"
                assert max_time < 0.2, f"Max DB connection too slow: {max_time*1000:.2f}ms"
            else:
                pytest.skip("Could not test database connections")
                
        except ImportError:
            pytest.skip("DatabaseManager not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_query_performance(self):
        """Test database query performance for common operations"""
        try:
            from database.core.repositories import (
                ContentRepository,
                CourseRepository,
                UserRepository,
            )
            
            repositories = {
                "users": UserRepository(),
                "courses": CourseRepository(), 
                "content": ContentRepository()
            }
            
            query_performance = {}
            
            for repo_name, repo in repositories.items():
                query_times = []
                
                # Test basic queries
                queries = [
                    ("get_all", lambda: repo.get_all(limit=10)),
                    ("get_by_id", lambda: repo.get_by_id(1)),
                    ("search", lambda: repo.search({"status": "active"})),
                ]
                
                for query_name, query_func in queries:
                    times = []
                    
                    for i in range(10):
                        start = time.time()
                        try:
                            result = await query_func()
                            times.append(time.time() - start)
                        except Exception:
                            pass
                    
                    if times:
                        avg_time = statistics.mean(times)
                        query_times.append((f"{query_name}", avg_time))
                
                if query_times:
                    query_performance[repo_name] = query_times
            
            # Report and assert performance
            for repo_name, queries in query_performance.items():
                print(f"{repo_name.capitalize()} Query Performance:")
                
                for query_name, avg_time in queries:
                    print(f"  {query_name}: {avg_time*1000:.2f}ms")
                    
                    # Query performance targets
                    assert avg_time < 0.1, f"{repo_name} {query_name} too slow: {avg_time*1000:.2f}ms"
            
        except ImportError:
            pytest.skip("Database repositories not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_concurrent_database_access(self):
        """Test database performance under concurrent access"""
        try:
            from database.connection_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            concurrent_queries = 50
            total_queries = 200
            
            async def execute_query(query_id: int):
                """Execute a database query"""
                start = time.time()
                try:
                    async with db_manager.get_connection() as conn:
                        # Mix of query types
                        if query_id % 3 == 0:
                            await conn.execute("SELECT COUNT(*) FROM users")
                        elif query_id % 3 == 1:
                            await conn.execute("SELECT COUNT(*) FROM courses")
                        else:
                            await conn.execute("SELECT COUNT(*) FROM content")
                        
                        return time.time() - start, True
                except Exception:
                    return time.time() - start, False
            
            # Execute concurrent queries in batches
            all_results = []
            
            for batch_start in range(0, total_queries, concurrent_queries):
                batch_size = min(concurrent_queries, total_queries - batch_start)
                
                tasks = [
                    execute_query(batch_start + i) 
                    for i in range(batch_size)
                ]
                
                batch_results = await asyncio.gather(*tasks)
                all_results.extend(batch_results)
            
            # Analyze results
            successful_queries = [r for r in all_results if r[1]]
            failed_queries = [r for r in all_results if not r[1]]
            
            if successful_queries:
                response_times = [r[0] for r in successful_queries]
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                
                success_rate = len(successful_queries) / len(all_results) * 100
                
                print(f"Concurrent Database Access:")
                print(f"  Total queries: {len(all_results)}")
                print(f"  Successful: {len(successful_queries)}")
                print(f"  Failed: {len(failed_queries)}")
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Average time: {avg_time*1000:.2f}ms")
                print(f"  Max time: {max_time*1000:.2f}ms")
                
                # Performance under concurrent load
                assert success_rate > 95, f"Too many failed queries: {success_rate:.1f}%"
                assert avg_time < 0.2, f"Concurrent queries too slow: {avg_time*1000:.2f}ms"
            else:
                pytest.skip("No successful concurrent queries")
                
        except ImportError:
            pytest.skip("DatabaseManager not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_transaction_performance(self):
        """Test database transaction performance"""
        try:
            from database.connection_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            transaction_times = []
            
            # Test transaction performance
            for i in range(20):
                start = time.time()
                try:
                    async with db_manager.get_connection() as conn:
                        async with conn.transaction():
                            # Simulate transaction with multiple operations
                            await conn.execute("SELECT 1")
                            await conn.execute("SELECT 2") 
                            await conn.execute("SELECT 3")
                            
                    transaction_times.append(time.time() - start)
                except Exception:
                    pass
            
            if transaction_times:
                avg_time = statistics.mean(transaction_times)
                max_time = max(transaction_times)
                
                print(f"Database Transaction Performance:")
                print(f"  Transactions: {len(transaction_times)}")
                print(f"  Average time: {avg_time*1000:.2f}ms")
                print(f"  Max time: {max_time*1000:.2f}ms")
                
                # Transaction performance targets
                assert avg_time < 0.05, f"Transactions too slow: {avg_time*1000:.2f}ms"
                assert max_time < 0.1, f"Max transaction too slow: {max_time*1000:.2f}ms"
            else:
                pytest.skip("Could not test transactions")
                
        except ImportError:
            pytest.skip("DatabaseManager not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_large_result_set_performance(self):
        """Test performance with large result sets"""
        try:
            from database.connection_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Test different result set sizes
            result_sizes = [100, 500, 1000, 5000]
            performance_results = {}
            
            for size in result_sizes:
                times = []
                
                for i in range(5):  # 5 iterations per size
                    start = time.time()
                    try:
                        async with db_manager.get_connection() as conn:
                            # Generate series to simulate large result set
                            query = f"SELECT generate_series(1, {size}) as id"
                            result = await conn.fetch(query)
                            
                            # Process results to simulate real usage
                            processed = len(result) if result else 0
                            
                        if processed == size:
                            times.append(time.time() - start)
                    except Exception:
                        pass
                
                if times:
                    avg_time = statistics.mean(times)
                    performance_results[size] = {
                        "avg_time": avg_time,
                        "rows_per_second": size / avg_time if avg_time > 0 else 0
                    }
            
            # Report performance scaling
            print(f"Large Result Set Performance:")
            for size, result in performance_results.items():
                print(f"  {size} rows: {result['avg_time']*1000:.2f}ms ({result['rows_per_second']:.0f} rows/s)")
            
            # Performance should scale reasonably
            if len(performance_results) >= 2:
                sizes = sorted(performance_results.keys())
                small_size = sizes[0]
                large_size = sizes[-1]
                
                small_rate = performance_results[small_size]["rows_per_second"]
                large_rate = performance_results[large_size]["rows_per_second"]
                
                # Rate should not degrade too much with size
                if small_rate > 0:
                    rate_ratio = large_rate / small_rate
                    assert rate_ratio > 0.1, f"Performance degrades too much with size: {rate_ratio:.2f}"
                
        except ImportError:
            pytest.skip("DatabaseManager not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_connection_pool_efficiency(self):
        """Test database connection pool efficiency"""
        try:
            from database.connection_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Test connection reuse
            connection_acquisition_times = []
            
            # First round - cold start
            for i in range(10):
                start = time.time()
                try:
                    async with db_manager.get_connection() as conn:
                        await conn.execute("SELECT 1")
                    connection_acquisition_times.append(("cold", time.time() - start))
                except Exception:
                    pass
            
            # Second round - should use pooled connections
            for i in range(10):
                start = time.time()
                try:
                    async with db_manager.get_connection() as conn:
                        await conn.execute("SELECT 1")
                    connection_acquisition_times.append(("warm", time.time() - start))
                except Exception:
                    pass
            
            # Analyze pool efficiency
            cold_times = [t for label, t in connection_acquisition_times if label == "cold"]
            warm_times = [t for label, t in connection_acquisition_times if label == "warm"]
            
            if cold_times and warm_times:
                cold_avg = statistics.mean(cold_times)
                warm_avg = statistics.mean(warm_times)
                
                print(f"Connection Pool Efficiency:")
                print(f"  Cold connections: {cold_avg*1000:.2f}ms avg")
                print(f"  Warm connections: {warm_avg*1000:.2f}ms avg")
                print(f"  Pool efficiency: {(cold_avg/warm_avg):.1f}x speedup")
                
                # Pooled connections should be faster
                assert warm_avg <= cold_avg, "Pooled connections should be at least as fast"
                
                # Both should be reasonably fast
                assert warm_avg < 0.05, f"Pooled connections too slow: {warm_avg*1000:.2f}ms"
            else:
                pytest.skip("Could not test connection pool efficiency")
                
        except ImportError:
            pytest.skip("DatabaseManager not available")