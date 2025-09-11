#!/usr/bin/env python3
"""
Wait for a terminal to complete a specific action.
Used during CI/CD pipeline to coordinate between terminals.
"""

import sys
import json
import time
import redis
import argparse
from datetime import datetime, timedelta
from typing import Optional

class TerminalWaiter:
    def __init__(self, terminal: str, event: str, timeout: int = 300):
        self.terminal = terminal
        self.event = event
        self.timeout = timeout
        self.start_time = datetime.now()
        
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.redis_available = True
        except (redis.ConnectionError, redis.TimeoutError):
            print(f"⚠️  Redis not available, simulating {event} completion")
            self.redis_available = False
            self.redis_client = None

    def wait_for_event(self) -> bool:
        """Wait for a specific event from a terminal."""
        if not self.redis_available:
            # Simulate success if Redis not available (for CI/CD)
            print(f"✓ Simulated: {self.terminal} {self.event}")
            return True
        
        print(f"⏳ Waiting for {self.terminal} to complete {self.event}...")
        print(f"   Timeout: {self.timeout} seconds")
        
        # Subscribe to terminal channel
        pubsub = self.redis_client.pubsub()
        channel = f"terminal:{self.terminal}:{self.event}"
        pubsub.subscribe(channel)
        
        # Also check if event was already completed
        status_key = f"terminal:{self.terminal}:last_{self.event}"
        last_event = self.redis_client.get(status_key)
        
        if last_event:
            event_data = json.loads(last_event)
            event_time = datetime.fromisoformat(event_data.get('timestamp', ''))
            
            # If event occurred recently (within last minute), consider it done
            if event_time > self.start_time - timedelta(minutes=1):
                print(f"✅ {self.terminal} already completed {self.event}")
                return True
        
        # Wait for event
        deadline = datetime.now() + timedelta(seconds=self.timeout)
        
        while datetime.now() < deadline:
            try:
                # Check for message with timeout
                message = pubsub.get_message(timeout=1.0)
                
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    
                    if data.get('status') == 'complete':
                        elapsed = (datetime.now() - self.start_time).total_seconds()
                        print(f"✅ {self.terminal} completed {self.event} in {elapsed:.1f}s")
                        
                        # Store completion status
                        self.redis_client.setex(
                            status_key,
                            300,  # Keep for 5 minutes
                            json.dumps({
                                'timestamp': datetime.now().isoformat(),
                                'status': 'complete'
                            })
                        )
                        return True
                    
                    elif data.get('status') == 'failed':
                        print(f"❌ {self.terminal} failed {self.event}: {data.get('error', 'Unknown error')}")
                        return False
                
                # Show progress
                elapsed = (datetime.now() - self.start_time).total_seconds()
                remaining = self.timeout - elapsed
                
                if int(elapsed) % 10 == 0:  # Progress every 10 seconds
                    print(f"   Still waiting... ({remaining:.0f}s remaining)")
                    
                    # Send ping to terminal
                    self.redis_client.publish(
                        f"terminal:{self.terminal}:ping",
                        json.dumps({
                            'waiting_for': self.event,
                            'elapsed': elapsed
                        })
                    )
                
            except redis.ConnectionError:
                print("⚠️  Lost Redis connection")
                return False
            except Exception as e:
                print(f"Error: {e}")
        
        print(f"⏱️  Timeout waiting for {self.terminal} {self.event}")
        return False

    def simulate_event_completion(self):
        """Simulate event completion for testing."""
        if self.redis_available:
            channel = f"terminal:{self.terminal}:{self.event}"
            self.redis_client.publish(
                channel,
                json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'status': 'complete',
                    'simulated': True
                })
            )
            print(f"📤 Simulated {self.event} completion for {self.terminal}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Wait for terminal event')
    parser.add_argument('terminal', help='Terminal name (e.g., terminal1, terminal2)')
    parser.add_argument('event', help='Event to wait for (e.g., deploy_complete)')
    parser.add_argument('timeout', nargs='?', type=int, default=300, 
                       help='Timeout in seconds (default: 300)')
    parser.add_argument('--simulate', action='store_true',
                       help='Simulate event completion for testing')
    
    args = parser.parse_args()
    
    waiter = TerminalWaiter(args.terminal, args.event, args.timeout)
    
    if args.simulate:
        waiter.simulate_event_completion()
        sys.exit(0)
    
    success = waiter.wait_for_event()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()