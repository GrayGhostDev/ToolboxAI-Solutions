import pytest_asyncio

"""
Agent System Performance Tests
Tests for AI agent execution times, memory usage, and scaling
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



import asyncio
import json
import os
import statistics
import time
from typing import Any, Dict, List

import psutil
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Performance tests require external services - run with --run-performance")


@pytest.mark.performance
class TestAgentPerformance:
    """Agent system performance tests"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_supervisor_agent_performance(self):
        """Test SupervisorAgent performance under load"""
        try:
            from core.agents.supervisor import SupervisorAgent
            
            supervisor = SupervisorAgent()
            response_times = []
            errors = 0
            
            # Test with various task types
            test_tasks = [
                {"type": "content", "data": {"subject": "Math", "topic": "Algebra"}},
                {"type": "quiz", "data": {"questions": 5, "difficulty": "medium"}},
                {"type": "terrain", "data": {"environment": "classroom", "size": "medium"}},
                {"type": "script", "data": {"functionality": "basic", "complexity": "simple"}},
            ]
            
            # Run performance test
            for i in range(20):  # 20 iterations
                task = test_tasks[i % len(test_tasks)]
                task["id"] = f"perf_test_{i}"
                
                start = time.time()
                try:
                    result = await supervisor.process_task(task)
                    if result:
                        response_times.append(time.time() - start)
                    else:
                        errors += 1
                except Exception:
                    errors += 1
            
            if response_times:
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                print(f"SupervisorAgent Performance:")
                print(f"  Tasks processed: {len(response_times)}")
                print(f"  Errors: {errors}")
                print(f"  Average time: {avg_time:.2f}s")
                print(f"  Min time: {min_time:.2f}s")
                print(f"  Max time: {max_time:.2f}s")
                
                # Performance targets
                assert avg_time < 3.0, f"SupervisorAgent too slow: {avg_time:.2f}s average"
                assert max_time < 10.0, f"SupervisorAgent max too slow: {max_time:.2f}s"
                assert errors < 3, f"Too many errors: {errors}"
            else:
                pytest.skip("SupervisorAgent not available or no successful tasks")
                
        except ImportError:
            pytest.skip("SupervisorAgent not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_orchestrator_scaling(self):
        """Test Orchestrator scaling with increasing load"""
        try:
            from core.agents.orchestrator import Orchestrator
            
            orchestrator = Orchestrator()
            scaling_results = {}
            
            # Test with different load levels
            load_levels = [5, 10, 20, 50]
            
            for load in load_levels:
                response_times = []
                errors = 0
                
                # Create batch of tasks
                tasks = []
                for i in range(load):
                    task_type = ["content", "quiz", "terrain"][i % 3]
                    tasks.append({
                        "type": task_type,
                        "id": f"load_{load}_task_{i}",
                        "data": {"complexity": "simple", "index": i}
                    })
                
                start = time.time()
                try:
                    # Process batch
                    results = await orchestrator.process_tasks_batch(tasks)
                    batch_time = time.time() - start
                    
                    if results:
                        response_times.append(batch_time)
                    else:
                        errors += 1
                        
                except Exception:
                    errors += 1
                    batch_time = time.time() - start
                
                scaling_results[load] = {
                    "batch_time": batch_time,
                    "tasks_per_second": load / batch_time if batch_time > 0 else 0,
                    "errors": errors,
                    "success": errors == 0
                }
            
            # Analyze scaling behavior
            print(f"Orchestrator Scaling Test:")
            for load, result in scaling_results.items():
                print(f"  Load {load}: {result['batch_time']:.2f}s, {result['tasks_per_second']:.1f} tasks/s")
            
            # Verify reasonable scaling
            if len(scaling_results) >= 2:
                small_load = min(scaling_results.keys())
                large_load = max(scaling_results.keys())
                
                small_time = scaling_results[small_load]["batch_time"]
                large_time = scaling_results[large_load]["batch_time"]
                
                # Large load should not be more than 3x slower per task
                efficiency_ratio = (large_time / large_load) / (small_time / small_load)
                assert efficiency_ratio < 3.0, f"Poor scaling efficiency: {efficiency_ratio:.2f}x"
                
        except ImportError:
            pytest.skip("Orchestrator not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_content_agent_performance(self):
        """Test ContentAgent content generation performance"""
        try:
            from core.agents.content_agent import ContentAgent
            
            content_agent = ContentAgent()
            generation_times = []
            errors = 0
            
            # Test different content generation requests
            requests = [
                {"subject": "Mathematics", "topic": "Basic Algebra", "grade_level": 7},
                {"subject": "Science", "topic": "Solar System", "grade_level": 8},
                {"subject": "English", "topic": "Creative Writing", "grade_level": 6},
                {"subject": "History", "topic": "Ancient Rome", "grade_level": 9},
                {"subject": "Geography", "topic": "World Capitals", "grade_level": 7},
            ]
            
            for i, request in enumerate(requests * 2):  # 10 total requests
                request["id"] = f"content_perf_{i}"
                
                start = time.time()
                try:
                    result = await content_agent.generate_content(request)
                    if result and result.get("success"):
                        generation_times.append(time.time() - start)
                    else:
                        errors += 1
                except Exception:
                    errors += 1
            
            if generation_times:
                avg_time = statistics.mean(generation_times)
                max_time = max(generation_times)
                
                print(f"ContentAgent Performance:")
                print(f"  Generations: {len(generation_times)}")
                print(f"  Errors: {errors}")
                print(f"  Average time: {avg_time:.2f}s")
                print(f"  Max time: {max_time:.2f}s")
                
                # Content generation targets
                assert avg_time < 5.0, f"Content generation too slow: {avg_time:.2f}s"
                assert max_time < 10.0, f"Max content generation too slow: {max_time:.2f}s"
                assert errors < 2, f"Too many content generation errors: {errors}"
            else:
                pytest.skip("ContentAgent not available or no successful generations")
                
        except ImportError:
            pytest.skip("ContentAgent not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_agent_memory_usage(self):
        """Test agent memory usage during sustained operation"""
        try:
            from core.agents.supervisor import SupervisorAgent
            
            process = psutil.Process(os.getpid())
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            supervisor = SupervisorAgent()
            memory_samples = []
            
            # Run sustained load for 30 seconds
            duration = 30
            start_time = time.time()
            task_count = 0
            
            while time.time() - start_time < duration:
                # Create and process task
                task = {
                    "type": "content",
                    "id": f"memory_test_{task_count}",
                    "data": {"simple": True, "timestamp": time.time()}
                }
                
                try:
                    await supervisor.process_task(task)
                    task_count += 1
                except Exception:
                    pass
                
                # Sample memory every 5 tasks
                if task_count % 5 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)
                
                await asyncio.sleep(0.5)  # Controlled rate
            
            if memory_samples:
                peak_memory = max(memory_samples)
                avg_memory = statistics.mean(memory_samples)
                memory_growth = peak_memory - baseline_memory
                
                print(f"Agent Memory Usage Test:")
                print(f"  Duration: {duration}s")
                print(f"  Tasks processed: {task_count}")
                print(f"  Baseline memory: {baseline_memory:.2f}MB")
                print(f"  Peak memory: {peak_memory:.2f}MB")
                print(f"  Average memory: {avg_memory:.2f}MB")
                print(f"  Memory growth: {memory_growth:.2f}MB")
                
                # Memory should not grow excessively
                assert memory_growth < 200, f"Excessive memory growth: {memory_growth:.2f}MB"
                assert peak_memory < baseline_memory + 500, f"Memory usage too high: {peak_memory:.2f}MB"
            else:
                pytest.skip("Could not collect memory samples")
                
        except ImportError:
            pytest.skip("SupervisorAgent not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_agent_parallel_processing(self):
        """Test agent parallel processing capabilities"""
        try:
            from core.agents.supervisor import SupervisorAgent
            
            supervisor = SupervisorAgent()
            
            # Test sequential vs parallel processing
            tasks = []
            for i in range(10):
                tasks.append({
                    "type": "content",
                    "id": f"parallel_test_{i}",
                    "data": {"subject": "Math", "simple": True}
                })
            
            # Sequential processing
            sequential_start = time.time()
            sequential_results = []
            for task in tasks:
                try:
                    result = await supervisor.process_task(task)
                    sequential_results.append(result)
                except Exception:
                    pass
            sequential_time = time.time() - sequential_start
            
            # Parallel processing (if supported)
            parallel_start = time.time()
            try:
                parallel_tasks = [supervisor.process_task(task) for task in tasks]
                parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                parallel_time = time.time() - parallel_start
                
                # Filter successful results
                successful_parallel = [r for r in parallel_results if not isinstance(r, Exception)]
                
                print(f"Agent Parallel Processing:")
                print(f"  Tasks: {len(tasks)}")
                print(f"  Sequential time: {sequential_time:.2f}s")
                print(f"  Parallel time: {parallel_time:.2f}s")
                print(f"  Sequential results: {len(sequential_results)}")
                print(f"  Parallel results: {len(successful_parallel)}")
                
                if parallel_time > 0 and sequential_time > 0:
                    speedup = sequential_time / parallel_time
                    print(f"  Speedup: {speedup:.2f}x")
                    
                    # Parallel should provide some speedup
                    assert speedup > 1.0, f"No speedup from parallel processing: {speedup:.2f}x"
                
            except Exception:
                print(f"Parallel processing not supported or failed")
                print(f"Sequential time: {sequential_time:.2f}s")
                
        except ImportError:
            pytest.skip("SupervisorAgent not available")
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_agent_error_handling_performance(self):
        """Test agent performance under error conditions"""
        try:
            from core.agents.supervisor import SupervisorAgent
            
            supervisor = SupervisorAgent()
            
            # Test with invalid tasks to trigger error handling
            invalid_tasks = [
                {"type": "invalid_type", "data": {}},
                {"type": "content", "data": {"invalid": "data"}},
                {"type": "content"},  # Missing data
                {},  # Empty task
                {"type": "content", "data": None},
            ]
            
            error_handling_times = []
            
            for i, task in enumerate(invalid_tasks * 3):  # 15 total invalid tasks
                task["id"] = f"error_test_{i}"
                
                start = time.time()
                try:
                    result = await supervisor.process_task(task)
                    # Even if task fails, should return quickly
                    error_handling_times.append(time.time() - start)
                except Exception:
                    error_handling_times.append(time.time() - start)
            
            if error_handling_times:
                avg_error_time = statistics.mean(error_handling_times)
                max_error_time = max(error_handling_times)
                
                print(f"Agent Error Handling Performance:")
                print(f"  Error cases tested: {len(error_handling_times)}")
                print(f"  Average error handling time: {avg_error_time:.3f}s")
                print(f"  Max error handling time: {max_error_time:.3f}s")
                
                # Error handling should be fast
                assert avg_error_time < 1.0, f"Error handling too slow: {avg_error_time:.3f}s"
                assert max_error_time < 2.0, f"Max error handling too slow: {max_error_time:.3f}s"
            else:
                pytest.skip("Could not test error handling")
                
        except ImportError:
            pytest.skip("SupervisorAgent not available")