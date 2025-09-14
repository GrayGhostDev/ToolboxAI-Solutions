"""
WebSocket Performance Tests
Comprehensive WebSocket connection and message throughput tests
"""

import asyncio
import time
import pytest
import websockets

def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        return str(obj)

import json
import statistics
from typing import List, Dict, Any
import concurrent.futures

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Performance tests require external services - run with --run-performance")


@pytest.mark.performance
class TestWebSocketPerformance:
    """WebSocket performance and scalability tests"""
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_connection_establishment(self):
        """Test WebSocket connection establishment time"""
        url = "ws://localhost:9876"
        num_connections = 100
        connection_times = []
        
        async def establish_connection():
            start = time.time()
            try:
                ws = await websockets.connect(url)
                connection_times.append(time.time() - start)
                await ws.close()
                return True
            except Exception:
                return False
        
        # Test connection establishment
        tasks = [establish_connection() for _ in range(num_connections)]
        results = await asyncio.gather(*tasks)
        
        successful_connections = sum(results)
        avg_connection_time = statistics.mean(connection_times) if connection_times else 0
        
        assert successful_connections >= num_connections * 0.95, f"Too many failed connections: {successful_connections}/{num_connections}"
        assert avg_connection_time < 0.1, f"Connection establishment too slow: {avg_connection_time:.3f}s"
        
        print(f"WebSocket Connection Establishment:")
        print(f"  Successful: {successful_connections}/{num_connections}")
        print(f"  Average time: {avg_connection_time*1000:.2f}ms")
        if connection_times:
            print(f"  Min time: {min(connection_times)*1000:.2f}ms")
            print(f"  Max time: {max(connection_times)*1000:.2f}ms")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_message_latency(self):
        """Test WebSocket message round-trip latency"""
        url = "ws://localhost:9876"
        num_messages = 100
        
        latencies = []
        
        async with websockets.connect(url) as ws:
            # Warmup
            await ws.send(json.dumps({"type": "ping"}, default=make_json_serializable))
            await ws.recv()
            
            # Actual test
            for i in range(num_messages):
                start = time.time()
                
                message = {
                    "type": "ping",
                    "id": i,
                    "timestamp": start
                }
                
                await ws.send(json.dumps(message, default=make_json_serializable))
                
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    latency = time.time() - start
                    latencies.append(latency)
                except asyncio.TimeoutError:
                    pass  # Skip timeouts for latency calculation
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies)
            
            assert avg_latency < 0.05, f"WebSocket latency too high: {avg_latency*1000:.2f}ms average"
            assert p95_latency < 0.1, f"WebSocket P95 latency too high: {p95_latency*1000:.2f}ms"
            
            print(f"WebSocket Message Latency:")
            print(f"  Messages: {len(latencies)}/{num_messages}")
            print(f"  Average: {avg_latency*1000:.2f}ms")
            print(f"  P95: {p95_latency*1000:.2f}ms")
            print(f"  Min: {min(latencies)*1000:.2f}ms")
            print(f"  Max: {max(latencies)*1000:.2f}ms")
        else:
            pytest.fail("No successful message exchanges")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_concurrent_connections(self):
        """Test handling of many concurrent WebSocket connections"""
        url = "ws://localhost:9876"
        target_connections = 50  # Reduced for stability
        
        active_connections = []
        connection_errors = 0
        
        async def maintain_connection(connection_id: int):
            """Maintain a WebSocket connection with periodic messages"""
            try:
                async with websockets.connect(url) as ws:
                    active_connections.append(connection_id)
                    
                    # Send periodic messages for 10 seconds
                    for i in range(10):
                        message = {
                            "type": "heartbeat",
                            "connection_id": connection_id,
                            "sequence": i
                        }
                        await ws.send(json.dumps(message, default=make_json_serializable))
                        await asyncio.sleep(1)
                    
                    return True
            except Exception:
                return False
        
        # Start all connections
        start_time = time.time()
        tasks = [maintain_connection(i) for i in range(target_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        failed = target_connections - successful
        
        print(f"Concurrent WebSocket Connections:")
        print(f"  Target: {target_connections}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Success rate: {(successful/target_connections)*100:.1f}%")
        
        # Should handle most connections successfully
        assert successful >= target_connections * 0.8, f"Too many failed connections: {successful}/{target_connections}"
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput"""
        url = "ws://localhost:9876"
        num_clients = 5
        messages_per_client = 50
        
        total_messages_sent = 0
        total_messages_received = 0
        start_time = None
        end_time = None
        
        async def client_throughput_test(client_id: int):
            nonlocal total_messages_sent, total_messages_received, start_time, end_time
            
            messages_sent = 0
            messages_received = 0
            
            try:
                async with websockets.connect(url) as ws:
                    if start_time is None:
                        start_time = time.time()
                    
                    # Send messages rapidly
                    for i in range(messages_per_client):
                        message = {
                            "type": "throughput_test",
                            "client_id": client_id,
                            "message_id": i,
                            "timestamp": time.time()
                        }
                        
                        await ws.send(json.dumps(message, default=make_json_serializable))
                        messages_sent += 1
                        
                        # Try to receive response (non-blocking)
                        try:
                            response = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            messages_received += 1
                        except asyncio.TimeoutError:
                            pass
                    
                    end_time = time.time()
                    
                    return messages_sent, messages_received
            except Exception:
                return messages_sent, messages_received
        
        # Run throughput test
        tasks = [client_throughput_test(i) for i in range(num_clients)]
        results = await asyncio.gather(*tasks)
        
        for sent, received in results:
            total_messages_sent += sent
            total_messages_received += received
        
        if start_time and end_time:
            duration = end_time - start_time
            throughput_sent = total_messages_sent / duration
            throughput_received = total_messages_received / duration
            
            print(f"WebSocket Message Throughput:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Messages sent: {total_messages_sent}")
            print(f"  Messages received: {total_messages_received}")
            print(f"  Send throughput: {throughput_sent:.1f} msg/s")
            print(f"  Receive throughput: {throughput_received:.1f} msg/s")
            
            # Throughput targets
            assert throughput_sent > 50, f"Send throughput too low: {throughput_sent:.1f} msg/s"
        else:
            pytest.fail("Could not measure throughput")
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_memory_usage(self):
        """Test WebSocket memory usage with many connections"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        url = "ws://localhost:9876"
        connections = []
        num_connections = 25  # Moderate number for stability
        
        try:
            # Establish connections
            for i in range(num_connections):
                ws = await websockets.connect(url)
                connections.append(ws)
                
                # Send initial message
                await ws.send(json.dumps({
                    "type": "memory_test",
                    "connection_id": i
                }, default=make_json_serializable))
            
            # Measure memory after connections
            peak_memory = process.memory_info().rss / 1024 / 1024
            
            # Send some messages to test sustained usage
            for i in range(10):
                for j, ws in enumerate(connections):
                    try:
                        await ws.send(json.dumps({
                            "type": "sustained_test",
                            "round": i,
                            "connection": j
                        }, default=make_json_serializable))
                    except Exception:
                        pass
                
                await asyncio.sleep(0.1)
            
            # Final memory measurement
            final_memory = process.memory_info().rss / 1024 / 1024
            
        finally:
            # Clean up connections
            for ws in connections:
                try:
                    await ws.close()
                except Exception:
                    pass
        
        memory_per_connection = (peak_memory - baseline_memory) / num_connections if num_connections > 0 else 0
        
        print(f"WebSocket Memory Usage:")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Peak: {peak_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Per connection: {memory_per_connection:.2f}MB")
        print(f"  Connections: {num_connections}")
        
        # Memory usage should be reasonable
        assert memory_per_connection < 10, f"Too much memory per connection: {memory_per_connection:.2f}MB"
        assert peak_memory - baseline_memory < 500, f"Total memory growth too high: {peak_memory - baseline_memory:.2f}MB"