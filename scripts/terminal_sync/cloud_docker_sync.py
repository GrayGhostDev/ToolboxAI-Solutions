#!/usr/bin/env python3
"""
Cloud/Docker Terminal Synchronization
Implements Redis-based inter-terminal communication for cloud orchestration
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

try:
    import redis.asyncio as redis
except ImportError:
    import redis

import docker
import boto3
import kubernetes


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TerminalType(Enum):
    """Terminal types in the system"""
    CLOUD = "cloud"
    DEBUGGER = "debugger"
    TERMINAL1 = "terminal1"
    GITHUB = "github"


class CloudDockerSync:
    """
    Cloud/Docker terminal orchestrator
    Manages containerization, cloud infrastructure, and cross-terminal communication
    """
    
    def __init__(self):
        self.redis_client = None
        self.docker_client = None
        self.k8s_client = None
        self.aws_clients = {}
        self.pubsub = None
        self.tasks = []
        self.infrastructure_status = {
            "docker": "unknown",
            "kubernetes": "unknown",
            "aws": "unknown",
            "databases": "unknown"
        }
        
    async def initialize(self):
        """Initialize all clients and connections"""
        logger.info("Initializing Cloud/Docker Terminal...")
        
        # Initialize Redis
        self.redis_client = await redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        
        # Test Redis connection
        try:
            await self.redis_client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
        
        # Initialize Docker
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("✅ Docker connected")
            self.infrastructure_status["docker"] = "healthy"
        except Exception as e:
            logger.warning(f"⚠️ Docker not available: {e}")
            self.infrastructure_status["docker"] = "unavailable"
        
        # Initialize Kubernetes
        try:
            kubernetes.config.load_incluster_config()
            self.k8s_client = kubernetes.client.ApiClient()
            logger.info("✅ Kubernetes connected (in-cluster)")
            self.infrastructure_status["kubernetes"] = "healthy"
        except:
            try:
                kubernetes.config.load_kube_config()
                self.k8s_client = kubernetes.client.ApiClient()
                logger.info("✅ Kubernetes connected (kubeconfig)")
                self.infrastructure_status["kubernetes"] = "healthy"
            except Exception as e:
                logger.warning(f"⚠️ Kubernetes not available: {e}")
                self.infrastructure_status["kubernetes"] = "unavailable"
        
        # Initialize AWS clients
        try:
            self.aws_clients = {
                'ecs': boto3.client('ecs'),
                'ecr': boto3.client('ecr'),
                'elbv2': boto3.client('elbv2'),
                'cloudwatch': boto3.client('cloudwatch'),
                's3': boto3.client('s3'),
                'autoscaling': boto3.client('application-autoscaling')
            }
            logger.info("✅ AWS clients initialized")
            self.infrastructure_status["aws"] = "healthy"
        except Exception as e:
            logger.warning(f"⚠️ AWS not configured: {e}")
            self.infrastructure_status["aws"] = "unavailable"
        
        # Subscribe to Redis channels
        await self.subscribe_to_channels()
        
        # Broadcast initial status
        await self.broadcast_infrastructure_status("initialized", self.infrastructure_status)
    
    async def subscribe_to_channels(self):
        """Subscribe to relevant Redis channels"""
        channels = [
            'terminal:cloud:deploy',      # Deployment requests
            'terminal:cloud:scale',        # Scaling requests
            'terminal:cloud:backup',       # Backup requests
            'terminal:cloud:rollback',     # Rollback requests
            'terminal:cloud:health',       # Health check requests
            'terminal:all:emergency',      # Emergency broadcasts
        ]
        
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(*channels)
        
        logger.info(f"📡 Subscribed to {len(channels)} channels")
        
        # Start message handler
        asyncio.create_task(self.handle_messages())
    
    async def handle_messages(self):
        """Handle incoming Redis messages"""
        logger.info("👂 Listening for messages...")
        
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                data = json.loads(message['data'])
                
                logger.info(f"📨 Received on {channel}: {data.get('type', 'unknown')}")
                
                try:
                    await self.process_message(channel, data)
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    await self.send_error_response(channel, data, str(e))
    
    async def process_message(self, channel: str, data: Dict):
        """Process incoming message based on channel and type"""
        
        # Extract message type and parameters
        msg_type = data.get('type')
        params = data.get('params', {})
        sender = data.get('sender', 'unknown')
        
        # Route to appropriate handler
        if channel == 'terminal:cloud:deploy':
            await self.handle_deployment_request(msg_type, params, sender)
            
        elif channel == 'terminal:cloud:scale':
            await self.handle_scaling_request(msg_type, params, sender)
            
        elif channel == 'terminal:cloud:backup':
            await self.handle_backup_request(msg_type, params, sender)
            
        elif channel == 'terminal:cloud:rollback':
            await self.handle_rollback_request(msg_type, params, sender)
            
        elif channel == 'terminal:cloud:health':
            await self.handle_health_request(msg_type, params, sender)
            
        elif channel == 'terminal:all:emergency':
            await self.handle_emergency(msg_type, params, sender)
    
    async def handle_deployment_request(self, msg_type: str, params: Dict, sender: str):
        """Handle deployment requests"""
        logger.info(f"🚀 Processing deployment request from {sender}")
        
        if msg_type == 'deploy_containers':
            version = params.get('version', 'latest')
            environment = params.get('environment', 'production')
            services = params.get('services', ['all'])
            
            # Deploy containers
            result = await self.deploy_containers(version, environment, services)
            
            # Send response
            await self.send_deployment_response(sender, result)
            
        elif msg_type == 'deploy_kubernetes':
            namespace = params.get('namespace', 'toolboxai-production')
            manifests = params.get('manifests', [])
            
            # Deploy to Kubernetes
            result = await self.deploy_to_kubernetes(namespace, manifests)
            
            # Send response
            await self.send_deployment_response(sender, result)
    
    async def deploy_containers(self, version: str, environment: str, services: List[str]) -> Dict:
        """Deploy containers using Docker Compose or Swarm"""
        logger.info(f"📦 Deploying containers: {services} @ {version}")
        
        result = {
            'success': False,
            'deployed': [],
            'failed': [],
            'message': ''
        }
        
        if not self.docker_client:
            result['message'] = "Docker not available"
            return result
        
        try:
            # Pull images
            for service in services:
                if service == 'all':
                    # Deploy all services
                    compose_file = PROJECT_ROOT / "config/production/docker-compose.prod.yml"
                    cmd = [
                        "docker-compose",
                        "-f", str(compose_file),
                        "up", "-d",
                        "--remove-orphans"
                    ]
                    
                    # Set environment variables
                    env = os.environ.copy()
                    env['VERSION'] = version
                    env['ENVIRONMENT'] = environment
                    
                    # Execute deployment
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        env=env,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        result['deployed'].append('all')
                        result['success'] = True
                        result['message'] = "All services deployed successfully"
                    else:
                        result['failed'].append('all')
                        result['message'] = f"Deployment failed: {stderr.decode()}"
                else:
                    # Deploy specific service
                    image_name = f"ghcr.io/toolboxai-solutions/{service}:{version}"
                    
                    try:
                        # Pull image
                        logger.info(f"  Pulling {image_name}...")
                        self.docker_client.images.pull(image_name)
                        
                        # Run container
                        container = self.docker_client.containers.run(
                            image_name,
                            detach=True,
                            name=f"toolboxai-{service}",
                            network="toolboxai_network",
                            restart_policy={"Name": "unless-stopped"}
                        )
                        
                        result['deployed'].append(service)
                        logger.info(f"  ✅ {service} deployed")
                        
                    except Exception as e:
                        result['failed'].append(service)
                        logger.error(f"  ❌ {service} failed: {e}")
            
            result['success'] = len(result['failed']) == 0
            
        except Exception as e:
            result['message'] = f"Deployment error: {str(e)}"
            logger.error(result['message'])
        
        return result
    
    async def deploy_to_kubernetes(self, namespace: str, manifests: List[str]) -> Dict:
        """Deploy to Kubernetes cluster"""
        logger.info(f"☸️ Deploying to Kubernetes namespace: {namespace}")
        
        result = {
            'success': False,
            'deployed': [],
            'failed': [],
            'message': ''
        }
        
        if not self.k8s_client:
            result['message'] = "Kubernetes not available"
            return result
        
        try:
            v1 = kubernetes.client.CoreV1Api(self.k8s_client)
            apps_v1 = kubernetes.client.AppsV1Api(self.k8s_client)
            
            # Create namespace if it doesn't exist
            try:
                v1.create_namespace(
                    body=kubernetes.client.V1Namespace(
                        metadata=kubernetes.client.V1ObjectMeta(name=namespace)
                    )
                )
                logger.info(f"  Created namespace: {namespace}")
            except kubernetes.client.ApiException as e:
                if e.status != 409:  # Already exists
                    raise
            
            # Apply manifests
            for manifest in manifests:
                manifest_path = PROJECT_ROOT / "config/kubernetes" / manifest
                
                if manifest_path.exists():
                    cmd = ["kubectl", "apply", "-f", str(manifest_path), "-n", namespace]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        result['deployed'].append(manifest)
                        logger.info(f"  ✅ Applied {manifest}")
                    else:
                        result['failed'].append(manifest)
                        logger.error(f"  ❌ Failed {manifest}: {stderr.decode()}")
            
            result['success'] = len(result['failed']) == 0
            result['message'] = f"Deployed {len(result['deployed'])} manifests"
            
        except Exception as e:
            result['message'] = f"Kubernetes deployment error: {str(e)}"
            logger.error(result['message'])
        
        return result
    
    async def handle_scaling_request(self, msg_type: str, params: Dict, sender: str):
        """Handle auto-scaling requests"""
        logger.info(f"⚖️ Processing scaling request from {sender}")
        
        service = params.get('service')
        replicas = params.get('replicas', 3)
        
        if msg_type == 'scale_kubernetes':
            await self.scale_kubernetes_deployment(service, replicas)
            
        elif msg_type == 'scale_ecs':
            await self.scale_ecs_service(service, replicas)
    
    async def broadcast_infrastructure_status(self, status: str, details: Dict):
        """Broadcast infrastructure status to all terminals"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'terminal': 'cloud',
            'status': status,
            'details': details,
            'infrastructure': self.infrastructure_status
        }
        
        await self.redis_client.publish('terminal:all:infrastructure', json.dumps(message))
        logger.info(f"📢 Broadcasted infrastructure status: {status}")
    
    async def send_deployment_response(self, sender: str, result: Dict):
        """Send deployment response to requesting terminal"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'terminal': 'cloud',
            'type': 'deployment_response',
            'result': result
        }
        
        channel = f'terminal:{sender}:deployment_result'
        await self.redis_client.publish(channel, json.dumps(message))
    
    async def monitor_infrastructure(self):
        """Continuously monitor infrastructure health"""
        while True:
            try:
                # Check Docker
                if self.docker_client:
                    try:
                        self.docker_client.ping()
                        self.infrastructure_status["docker"] = "healthy"
                    except:
                        self.infrastructure_status["docker"] = "degraded"
                
                # Check Kubernetes
                if self.k8s_client:
                    try:
                        v1 = kubernetes.client.CoreV1Api(self.k8s_client)
                        nodes = v1.list_node()
                        ready_nodes = sum(1 for node in nodes.items 
                                        if any(c.type == 'Ready' and c.status == 'True' 
                                             for c in node.status.conditions))
                        self.infrastructure_status["kubernetes"] = f"healthy ({ready_nodes} nodes)"
                    except:
                        self.infrastructure_status["kubernetes"] = "degraded"
                
                # Broadcast status every 60 seconds
                await self.broadcast_infrastructure_status("monitoring", self.infrastructure_status)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            await asyncio.sleep(60)
    
    async def run(self):
        """Main run loop"""
        logger.info("🚀 Cloud/Docker Terminal Starting...")
        
        try:
            # Initialize
            await self.initialize()
            
            # Start monitoring
            monitor_task = asyncio.create_task(self.monitor_infrastructure())
            self.tasks.append(monitor_task)
            
            # Keep running
            await asyncio.gather(*self.tasks)
            
        except KeyboardInterrupt:
            logger.info("⏹️ Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            # Cleanup
            if self.pubsub:
                await self.pubsub.unsubscribe()
            if self.redis_client:
                await self.redis_client.close()


async def main():
    """Main entry point"""
    sync = CloudDockerSync()
    await sync.run()


if __name__ == "__main__":
    asyncio.run(main())