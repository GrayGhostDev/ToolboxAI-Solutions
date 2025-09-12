"""
Resource Coordinator - System-wide resource allocation and optimization

Manages API rate limits, memory allocation, CPU resources, token usage,
and cost tracking for the ToolboxAI Roblox Environment.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
import time
import psutil
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class ResourceAllocation:
    """Resource allocation for a specific request"""
    request_id: str
    cpu_cores: int
    memory_mb: int
    gpu_memory_mb: int = 0
    api_quota: int = 100  # API calls allowed
    token_limit: int = 10000  # Token limit
    allocated_time: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600  # Time to live
    
    @property
    def is_expired(self) -> bool:
        """Check if allocation has expired"""
        return datetime.now() > self.allocated_time + timedelta(seconds=self.ttl_seconds)

@dataclass
class ResourceUsage:
    """Track resource usage for a request"""
    request_id: str
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_memory_usage_mb: float = 0.0
    api_calls_made: int = 0
    tokens_used: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class SystemResources:
    """Current system resource availability"""
    total_cpu_cores: int
    available_cpu_cores: int
    total_memory_mb: int
    available_memory_mb: int
    total_gpu_memory_mb: int
    available_gpu_memory_mb: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class APIQuota:
    """API rate limiting and quota management"""
    service_name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    tokens_per_minute: int
    tokens_per_hour: int
    current_minute_requests: int = 0
    current_hour_requests: int = 0
    current_day_requests: int = 0
    current_minute_tokens: int = 0
    current_hour_tokens: int = 0
    last_reset_minute: datetime = field(default_factory=datetime.now)
    last_reset_hour: datetime = field(default_factory=datetime.now)
    last_reset_day: datetime = field(default_factory=datetime.now)

class ResourceCoordinator:
    """
    System-wide resource allocation and optimization coordinator.
    
    Manages:
    - CPU and memory allocation
    - API rate limiting and quotas
    - Token usage optimization
    - Cost tracking and budgeting
    - Resource monitoring and alerts
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Resource limits
        self.max_cpu_allocation = self.config.get('max_cpu_allocation', 0.8)  # 80% of available
        self.max_memory_allocation = self.config.get('max_memory_allocation', 0.7)  # 70% of available
        self.reserve_cpu_cores = self.config.get('reserve_cpu_cores', 1)
        self.reserve_memory_mb = self.config.get('reserve_memory_mb', 1024)
        
        # Cost tracking
        self.enable_cost_tracking = self.config.get('enable_cost_tracking', True)
        self.cost_per_api_call = self.config.get('cost_per_api_call', 0.002)
        self.cost_per_1k_tokens = self.config.get('cost_per_1k_tokens', 0.02)
        self.daily_budget = self.config.get('daily_budget', 50.0)  # $50 daily budget
        
        # State management
        self.is_initialized = False
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.usage_tracking: Dict[str, ResourceUsage] = {}
        self.api_quotas: Dict[str, APIQuota] = {}
        self.cost_tracking = defaultdict(float)
        
        # Resource monitoring
        self.resource_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        self.alert_thresholds = {
            'cpu_usage': 90.0,
            'memory_usage': 85.0,
            'api_rate': 95.0,
            'daily_cost': 90.0  # 90% of daily budget
        }
        
        # Background tasks
        self.monitor_task = None
        self.cleanup_task = None
        self.quota_reset_task = None
        
        # Thread safety
        self._allocation_lock = threading.RLock()
        
        # FastAPI app
        self.app = FastAPI(title="Resource Coordinator API", version="1.0.0")
        self._setup_routes()
        
        # Initialize API quotas
        self._setup_api_quotas()
    
    async def initialize(self):
        """Initialize the resource coordinator"""
        try:
            logger.info("Initializing Resource Coordinator...")
            
            # Get initial system resources
            await self._update_system_resources()
            
            # Start background monitoring
            self.monitor_task = asyncio.create_task(self._resource_monitor())
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_allocations())
            self.quota_reset_task = asyncio.create_task(self._quota_reset_scheduler())
            
            self.is_initialized = True
            logger.info("Resource Coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"Resource Coordinator initialization failed: {e}")
            raise
    
    def _setup_api_quotas(self):
        """Setup API quotas for different services"""
        
        # OpenAI API quotas
        self.api_quotas['openai'] = APIQuota(
            service_name='openai',
            requests_per_minute=60,
            requests_per_hour=3600,
            requests_per_day=10000,
            tokens_per_minute=150000,
            tokens_per_hour=1000000
        )
        
        # Schoology API quotas
        self.api_quotas['schoology'] = APIQuota(
            service_name='schoology',
            requests_per_minute=30,
            requests_per_hour=1000,
            requests_per_day=5000,
            tokens_per_minute=50000,
            tokens_per_hour=300000
        )
        
        # Canvas API quotas
        self.api_quotas['canvas'] = APIQuota(
            service_name='canvas',
            requests_per_minute=60,
            requests_per_hour=3000,
            requests_per_day=20000,
            tokens_per_minute=100000,
            tokens_per_hour=500000
        )
        
        # Roblox API quotas
        self.api_quotas['roblox'] = APIQuota(
            service_name='roblox',
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=2000,
            tokens_per_minute=20000,
            tokens_per_hour=100000
        )
        
        logger.info(f"Configured API quotas for {len(self.api_quotas)} services")
    
    async def allocate_resources(
        self,
        request_id: str,
        requirements: Dict[str, Any]
    ) -> ResourceAllocation:
        """
        Allocate resources for a request
        
        Args:
            request_id: Unique request identifier
            requirements: Resource requirements dict with keys:
                - cpu_cores: Number of CPU cores needed
                - memory_mb: Memory in MB needed
                - gpu_memory_mb: GPU memory in MB (optional)
                - api_quota: Number of API calls expected
                - token_limit: Token limit for the request
                
        Returns:
            ResourceAllocation object
        """
        with self._allocation_lock:
            # Check if request already has allocation
            if request_id in self.allocations:
                logger.warning(f"Request {request_id} already has resource allocation")
                return self.allocations[request_id]
            
            # Validate requirements
            cpu_cores = requirements.get('cpu_cores', 1)
            memory_mb = requirements.get('memory_mb', 512)
            gpu_memory_mb = requirements.get('gpu_memory_mb', 0)
            api_quota = requirements.get('api_quota', 100)
            token_limit = requirements.get('token_limit', 10000)
            
            # Check resource availability
            system_resources = await self._get_current_system_resources()
            
            if cpu_cores > system_resources.available_cpu_cores:
                raise ResourceError(f"Insufficient CPU cores: need {cpu_cores}, have {system_resources.available_cpu_cores}")
            
            if memory_mb > system_resources.available_memory_mb:
                raise ResourceError(f"Insufficient memory: need {memory_mb}MB, have {system_resources.available_memory_mb}MB")
            
            if gpu_memory_mb > system_resources.available_gpu_memory_mb:
                raise ResourceError(f"Insufficient GPU memory: need {gpu_memory_mb}MB, have {system_resources.available_gpu_memory_mb}MB")
            
            # Create allocation
            allocation = ResourceAllocation(
                request_id=request_id,
                cpu_cores=cpu_cores,
                memory_mb=memory_mb,
                gpu_memory_mb=gpu_memory_mb,
                api_quota=api_quota,
                token_limit=token_limit,
                ttl_seconds=requirements.get('ttl_seconds', 3600)
            )
            
            # Store allocation
            self.allocations[request_id] = allocation
            
            # Initialize usage tracking
            self.usage_tracking[request_id] = ResourceUsage(request_id=request_id)
            
            logger.info(f"Allocated resources for request {request_id}: {cpu_cores} cores, {memory_mb}MB memory")
            
            return allocation
    
    async def release_resources(self, request_id: str) -> bool:
        """Release allocated resources for a request"""
        with self._allocation_lock:
            if request_id in self.allocations:
                allocation = self.allocations[request_id]
                usage = self.usage_tracking.get(request_id)
                
                # Record final usage metrics
                if usage and self.enable_cost_tracking:
                    await self._record_usage_metrics(allocation, usage)
                
                # Clean up
                del self.allocations[request_id]
                if request_id in self.usage_tracking:
                    del self.usage_tracking[request_id]
                
                logger.info(f"Released resources for request {request_id}")
                return True
            
            return False
    
    async def check_api_quota(
        self,
        service: str,
        request_count: int = 1,
        token_count: int = 0
    ) -> bool:
        """
        Check if API quota allows the request
        
        Args:
            service: API service name (openai, schoology, canvas, roblox)
            request_count: Number of requests to check
            token_count: Number of tokens to check
            
        Returns:
            True if quota allows request
        """
        if service not in self.api_quotas:
            logger.warning(f"Unknown API service: {service}")
            return True  # Allow unknown services
        
        quota = self.api_quotas[service]
        now = datetime.now()
        
        # Reset counters if needed
        await self._reset_quota_counters(quota, now)
        
        # Check limits
        if (quota.current_minute_requests + request_count > quota.requests_per_minute or
            quota.current_hour_requests + request_count > quota.requests_per_hour or
            quota.current_day_requests + request_count > quota.requests_per_day):
            return False
        
        if (quota.current_minute_tokens + token_count > quota.tokens_per_minute or
            quota.current_hour_tokens + token_count > quota.tokens_per_hour):
            return False
        
        return True
    
    async def consume_api_quota(
        self,
        service: str,
        request_count: int = 1,
        token_count: int = 0,
        request_id: Optional[str] = None
    ) -> bool:
        """
        Consume API quota for a request
        
        Args:
            service: API service name
            request_count: Number of requests to consume
            token_count: Number of tokens to consume
            request_id: Optional request ID for tracking
            
        Returns:
            True if quota was consumed successfully
        """
        if not await self.check_api_quota(service, request_count, token_count):
            return False
        
        if service not in self.api_quotas:
            return True  # Allow unknown services
        
        quota = self.api_quotas[service]
        
        # Consume quota
        quota.current_minute_requests += request_count
        quota.current_hour_requests += request_count
        quota.current_day_requests += request_count
        quota.current_minute_tokens += token_count
        quota.current_hour_tokens += token_count
        
        # Track usage for specific request
        if request_id and request_id in self.usage_tracking:
            usage = self.usage_tracking[request_id]
            usage.api_calls_made += request_count
            usage.tokens_used += token_count
            usage.last_updated = datetime.now()
        
        # Track costs
        if self.enable_cost_tracking:
            daily_key = datetime.now().strftime('%Y-%m-%d')
            self.cost_tracking[f"{daily_key}_{service}_requests"] += request_count * self.cost_per_api_call
            self.cost_tracking[f"{daily_key}_{service}_tokens"] += (token_count / 1000) * self.cost_per_1k_tokens
        
        logger.debug(f"Consumed {service} quota: {request_count} requests, {token_count} tokens")
        
        return True
    
    async def _reset_quota_counters(self, quota: APIQuota, now: datetime):
        """Reset quota counters based on time windows"""
        
        # Reset minute counter
        if now.minute != quota.last_reset_minute.minute:
            quota.current_minute_requests = 0
            quota.current_minute_tokens = 0
            quota.last_reset_minute = now
        
        # Reset hour counter
        if now.hour != quota.last_reset_hour.hour:
            quota.current_hour_requests = 0
            quota.current_hour_tokens = 0
            quota.last_reset_hour = now
        
        # Reset day counter
        if now.date() != quota.last_reset_day.date():
            quota.current_day_requests = 0
            quota.last_reset_day = now
    
    async def _get_current_system_resources(self) -> SystemResources:
        """Get current system resource availability"""
        
        # Get CPU information
        cpu_count = psutil.cpu_count()
        cpu_usage_percent = psutil.cpu_percent(interval=1)
        available_cpu_cores = max(0, int(cpu_count * (100 - cpu_usage_percent) / 100) - self.reserve_cpu_cores)
        
        # Get memory information
        memory = psutil.virtual_memory()
        total_memory_mb = memory.total // (1024 * 1024)
        available_memory_mb = max(0, memory.available // (1024 * 1024) - self.reserve_memory_mb)
        
        # GPU memory (simplified - would need GPU-specific libraries for real implementation)
        total_gpu_memory_mb = 8192  # Assume 8GB GPU
        used_gpu_memory = sum(
            alloc.gpu_memory_mb for alloc in self.allocations.values()
            if not alloc.is_expired
        )
        available_gpu_memory_mb = max(0, total_gpu_memory_mb - used_gpu_memory)
        
        return SystemResources(
            total_cpu_cores=cpu_count,
            available_cpu_cores=available_cpu_cores,
            total_memory_mb=total_memory_mb,
            available_memory_mb=available_memory_mb,
            total_gpu_memory_mb=total_gpu_memory_mb,
            available_gpu_memory_mb=available_gpu_memory_mb
        )
    
    async def _update_system_resources(self):
        """Update system resource information"""
        resources = await self._get_current_system_resources()
        self.resource_history.append(resources)
        
        # Check for resource alerts
        await self._check_resource_alerts(resources)
    
    async def _check_resource_alerts(self, resources: SystemResources):
        """Check for resource usage alerts"""
        alerts = []
        
        # CPU usage alert
        cpu_usage_percent = ((resources.total_cpu_cores - resources.available_cpu_cores) / 
                           resources.total_cpu_cores) * 100
        if cpu_usage_percent > self.alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {cpu_usage_percent:.1f}%")
        
        # Memory usage alert
        memory_usage_percent = ((resources.total_memory_mb - resources.available_memory_mb) / 
                              resources.total_memory_mb) * 100
        if memory_usage_percent > self.alert_thresholds['memory_usage']:
            alerts.append(f"High memory usage: {memory_usage_percent:.1f}%")
        
        # API rate alerts
        for service, quota in self.api_quotas.items():
            minute_usage_percent = (quota.current_minute_requests / quota.requests_per_minute) * 100
            if minute_usage_percent > self.alert_thresholds['api_rate']:
                alerts.append(f"High {service} API usage: {minute_usage_percent:.1f}%")
        
        # Cost alerts
        if self.enable_cost_tracking:
            daily_cost = await self._get_daily_cost()
            cost_usage_percent = (daily_cost / self.daily_budget) * 100
            if cost_usage_percent > self.alert_thresholds['daily_cost']:
                alerts.append(f"High daily cost usage: {cost_usage_percent:.1f}% (${daily_cost:.2f})")
        
        if alerts:
            logger.warning(f"Resource alerts: {alerts}")
    
    async def _get_daily_cost(self) -> float:
        """Calculate total cost for current day"""
        daily_key = datetime.now().strftime('%Y-%m-%d')
        total_cost = 0.0
        
        for key, cost in self.cost_tracking.items():
            if key.startswith(daily_key):
                total_cost += cost
        
        return total_cost
    
    async def get_utilization(self) -> Dict[str, float]:
        """Get current resource utilization percentages"""
        resources = await self._get_current_system_resources()
        
        cpu_utilization = ((resources.total_cpu_cores - resources.available_cpu_cores) / 
                          resources.total_cpu_cores) * 100
        
        memory_utilization = ((resources.total_memory_mb - resources.available_memory_mb) / 
                            resources.total_memory_mb) * 100
        
        gpu_utilization = ((resources.total_gpu_memory_mb - resources.available_gpu_memory_mb) / 
                          resources.total_gpu_memory_mb) * 100
        
        return {
            'cpu_utilization': cpu_utilization,
            'memory_utilization': memory_utilization,
            'gpu_utilization': gpu_utilization,
            'active_allocations': len([a for a in self.allocations.values() if not a.is_expired])
        }
    
    async def optimize_resource_allocation(self) -> Dict[str, Any]:
        """Optimize resource allocation based on usage patterns"""
        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'recommendations': [],
            'potential_savings': {},
            'efficiency_metrics': {}
        }
        
        # Analyze allocation patterns
        allocation_analysis = await self._analyze_allocation_patterns()
        optimization_report['efficiency_metrics'] = allocation_analysis
        
        # CPU optimization
        if allocation_analysis.get('avg_cpu_utilization', 0) < 50:
            optimization_report['recommendations'].append(
                "Consider reducing default CPU allocation - low average utilization detected"
            )
        
        # Memory optimization
        if allocation_analysis.get('avg_memory_utilization', 0) < 60:
            optimization_report['recommendations'].append(
                "Consider reducing default memory allocation - low average utilization detected"
            )
        
        # API quota optimization
        api_efficiency = await self._analyze_api_efficiency()
        if api_efficiency['wasted_quota'] > 20:
            optimization_report['recommendations'].append(
                f"High API quota waste detected: {api_efficiency['wasted_quota']:.1f}%"
            )
        
        # Cost optimization
        if self.enable_cost_tracking:
            cost_analysis = await self._analyze_cost_efficiency()
            optimization_report['potential_savings'] = cost_analysis
            
            if cost_analysis.get('potential_daily_savings', 0) > 5:
                optimization_report['recommendations'].append(
                    f"Potential daily cost savings: ${cost_analysis['potential_daily_savings']:.2f}"
                )
        
        return optimization_report
    
    async def _analyze_allocation_patterns(self) -> Dict[str, float]:
        """Analyze resource allocation patterns for optimization"""
        if not self.usage_tracking:
            return {}
        
        cpu_utilizations = []
        memory_utilizations = []
        
        for usage in self.usage_tracking.values():
            allocation = self.allocations.get(usage.request_id)
            if allocation:
                if allocation.cpu_cores > 0:
                    cpu_utilizations.append(usage.cpu_usage / allocation.cpu_cores * 100)
                if allocation.memory_mb > 0:
                    memory_utilizations.append(usage.memory_usage_mb / allocation.memory_mb * 100)
        
        return {
            'avg_cpu_utilization': sum(cpu_utilizations) / len(cpu_utilizations) if cpu_utilizations else 0,
            'avg_memory_utilization': sum(memory_utilizations) / len(memory_utilizations) if memory_utilizations else 0,
            'total_requests_tracked': len(self.usage_tracking)
        }
    
    async def _analyze_api_efficiency(self) -> Dict[str, float]:
        """Analyze API quota efficiency"""
        total_allocated = 0
        total_used = 0
        
        for usage in self.usage_tracking.values():
            allocation = self.allocations.get(usage.request_id)
            if allocation:
                total_allocated += allocation.api_quota
                total_used += usage.api_calls_made
        
        if total_allocated == 0:
            return {'wasted_quota': 0, 'efficiency': 100}
        
        efficiency = (total_used / total_allocated) * 100
        wasted_quota = 100 - efficiency
        
        return {
            'efficiency': efficiency,
            'wasted_quota': wasted_quota,
            'total_allocated': total_allocated,
            'total_used': total_used
        }
    
    async def _analyze_cost_efficiency(self) -> Dict[str, float]:
        """Analyze cost efficiency and potential savings"""
        daily_cost = await self._get_daily_cost()
        
        # Estimate potential savings based on usage patterns
        api_efficiency = await self._analyze_api_efficiency()
        wasted_api_cost = daily_cost * (api_efficiency['wasted_quota'] / 100)
        
        allocation_efficiency = await self._analyze_allocation_patterns()
        cpu_waste = max(0, 100 - allocation_efficiency.get('avg_cpu_utilization', 100))
        memory_waste = max(0, 100 - allocation_efficiency.get('avg_memory_utilization', 100))
        
        # Estimate compute cost savings
        compute_waste_factor = (cpu_waste + memory_waste) / 200  # Average waste factor
        estimated_compute_cost = daily_cost * 0.3  # Assume 30% of cost is compute
        wasted_compute_cost = estimated_compute_cost * compute_waste_factor
        
        total_potential_savings = wasted_api_cost + wasted_compute_cost
        
        return {
            'current_daily_cost': daily_cost,
            'wasted_api_cost': wasted_api_cost,
            'wasted_compute_cost': wasted_compute_cost,
            'potential_daily_savings': total_potential_savings,
            'efficiency_score': max(0, 100 - ((total_potential_savings / daily_cost) * 100) if daily_cost > 0 else 100)
        }
    
    async def _record_usage_metrics(self, allocation: ResourceAllocation, usage: ResourceUsage):
        """Record usage metrics for cost tracking and optimization"""
        duration_hours = (datetime.now() - usage.start_time).total_seconds() / 3600
        
        metrics = {
            'request_id': allocation.request_id,
            'duration_hours': duration_hours,
            'allocated_cpu': allocation.cpu_cores,
            'allocated_memory': allocation.memory_mb,
            'used_cpu': usage.cpu_usage,
            'used_memory': usage.memory_usage_mb,
            'api_calls': usage.api_calls_made,
            'tokens_used': usage.tokens_used,
            'efficiency_score': self._calculate_efficiency_score(allocation, usage),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store for analysis
        daily_key = datetime.now().strftime('%Y-%m-%d')
        if 'usage_metrics' not in self.cost_tracking:
            self.cost_tracking['usage_metrics'] = []
        
        self.cost_tracking['usage_metrics'].append(metrics)
        
        logger.debug(f"Recorded usage metrics for {allocation.request_id}")
    
    def _calculate_efficiency_score(self, allocation: ResourceAllocation, usage: ResourceUsage) -> float:
        """Calculate resource usage efficiency score (0-100)"""
        scores = []
        
        # CPU efficiency
        if allocation.cpu_cores > 0:
            cpu_efficiency = min(100, (usage.cpu_usage / allocation.cpu_cores) * 100)
            scores.append(cpu_efficiency)
        
        # Memory efficiency
        if allocation.memory_mb > 0:
            memory_efficiency = min(100, (usage.memory_usage_mb / allocation.memory_mb) * 100)
            scores.append(memory_efficiency)
        
        # API efficiency
        if allocation.api_quota > 0:
            api_efficiency = min(100, (usage.api_calls_made / allocation.api_quota) * 100)
            scores.append(api_efficiency)
        
        # Token efficiency
        if allocation.token_limit > 0:
            token_efficiency = min(100, (usage.tokens_used / allocation.token_limit) * 100)
            scores.append(token_efficiency)
        
        return sum(scores) / len(scores) if scores else 0
    
    async def _resource_monitor(self):
        """Background task to monitor system resources"""
        while self.is_initialized:
            try:
                await self._update_system_resources()
                
                # Update usage tracking for active allocations
                await self._update_usage_tracking()
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Resource monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _update_usage_tracking(self):
        """Update resource usage for all active allocations"""
        current_process = psutil.Process()
        
        for request_id, usage in self.usage_tracking.items():
            if request_id in self.allocations:
                # Update CPU and memory usage (simplified)
                usage.cpu_usage = current_process.cpu_percent()
                usage.memory_usage_mb = current_process.memory_info().rss / (1024 * 1024)
                usage.last_updated = datetime.now()
    
    async def _cleanup_expired_allocations(self):
        """Background task to cleanup expired resource allocations"""
        while self.is_initialized:
            try:
                expired_requests = [
                    request_id for request_id, allocation in self.allocations.items()
                    if allocation.is_expired
                ]
                
                for request_id in expired_requests:
                    await self.release_resources(request_id)
                    logger.info(f"Released expired allocation for request {request_id}")
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(300)
    
    async def _quota_reset_scheduler(self):
        """Background task to handle quota resets"""
        while self.is_initialized:
            try:
                now = datetime.now()
                
                for quota in self.api_quotas.values():
                    await self._reset_quota_counters(quota, now)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Quota reset scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def get_resource_status(self) -> Dict[str, Any]:
        """Get comprehensive resource status"""
        resources = await self._get_current_system_resources()
        utilization = await self.get_utilization()
        
        # API quota status
        quota_status = {}
        for service, quota in self.api_quotas.items():
            quota_status[service] = {
                'minute_usage': f"{quota.current_minute_requests}/{quota.requests_per_minute}",
                'hour_usage': f"{quota.current_hour_requests}/{quota.requests_per_hour}",
                'day_usage': f"{quota.current_day_requests}/{quota.requests_per_day}",
                'minute_utilization': (quota.current_minute_requests / quota.requests_per_minute) * 100,
                'tokens_minute': f"{quota.current_minute_tokens}/{quota.tokens_per_minute}"
            }
        
        # Cost status
        cost_status = {}
        if self.enable_cost_tracking:
            daily_cost = await self._get_daily_cost()
            cost_status = {
                'daily_cost': daily_cost,
                'daily_budget': self.daily_budget,
                'budget_utilization': (daily_cost / self.daily_budget) * 100,
                'estimated_monthly_cost': daily_cost * 30
            }
        
        return {
            'system_resources': asdict(resources),
            'utilization': utilization,
            'active_allocations': len(self.allocations),
            'quota_status': quota_status,
            'cost_status': cost_status,
            'alerts': await self._get_current_alerts()
        }
    
    async def _get_current_alerts(self) -> List[str]:
        """Get current system alerts"""
        alerts = []
        
        # Check current utilization against thresholds
        utilization = await self.get_utilization()
        
        if utilization['cpu_utilization'] > self.alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU utilization: {utilization['cpu_utilization']:.1f}%")
        
        if utilization['memory_utilization'] > self.alert_thresholds['memory_usage']:
            alerts.append(f"High memory utilization: {utilization['memory_utilization']:.1f}%")
        
        # Check budget alerts
        if self.enable_cost_tracking:
            daily_cost = await self._get_daily_cost()
            if (daily_cost / self.daily_budget) * 100 > self.alert_thresholds['daily_cost']:
                alerts.append(f"Approaching daily budget limit: ${daily_cost:.2f}/${self.daily_budget}")
        
        return alerts
    
    @asynccontextmanager
    async def resource_context(
        self,
        request_id: str,
        requirements: Dict[str, Any]
    ):
        """Context manager for automatic resource allocation and cleanup"""
        allocation = await self.allocate_resources(request_id, requirements)
        try:
            yield allocation
        finally:
            await self.release_resources(request_id)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get resource coordinator metrics"""
        utilization = await self.get_utilization()
        optimization = await self.optimize_resource_allocation()
        
        return {
            'utilization': utilization,
            'optimization': optimization,
            'allocations': {
                'total': len(self.allocations),
                'expired': len([a for a in self.allocations.values() if a.is_expired])
            },
            'api_quotas': {
                service: {
                    'minute_utilization': (quota.current_minute_requests / quota.requests_per_minute) * 100,
                    'hour_utilization': (quota.current_hour_requests / quota.requests_per_hour) * 100,
                    'day_utilization': (quota.current_day_requests / quota.requests_per_day) * 100
                }
                for service, quota in self.api_quotas.items()
            },
            'cost_tracking': dict(self.cost_tracking) if self.enable_cost_tracking else {}
        }
    
    async def get_health(self) -> Dict[str, Any]:
        """Get resource coordinator health status"""
        try:
            utilization = await self.get_utilization()
            alerts = await self._get_current_alerts()
            
            # Determine health status
            if alerts:
                if any('High' in alert for alert in alerts):
                    status = 'degraded'
                else:
                    status = 'healthy'
            else:
                status = 'healthy'
            
            # Check for critical resource shortage
            if (utilization['cpu_utilization'] > 95 or 
                utilization['memory_utilization'] > 95):
                status = 'unhealthy'
            
            return {
                'status': status,
                'utilization': utilization,
                'alerts': alerts,
                'background_tasks_running': all([
                    self.monitor_task and not self.monitor_task.done(),
                    self.cleanup_task and not self.cleanup_task.done(),
                    self.quota_reset_task and not self.quota_reset_task.done()
                ]),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Resource health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _setup_routes(self):
        """Setup FastAPI routes for resource management"""
        
        @self.app.post("/allocate")
        async def allocate_endpoint(request: dict):
            """Allocate resources for a request"""
            allocation = await self.allocate_resources(
                request['request_id'],
                request['requirements']
            )
            return asdict(allocation)
        
        @self.app.delete("/allocate/{request_id}")
        async def release_endpoint(request_id: str):
            """Release resources for a request"""
            success = await self.release_resources(request_id)
            return {'success': success}
        
        @self.app.get("/quota/{service}")
        async def check_quota_endpoint(service: str, requests: int = 1, tokens: int = 0):
            """Check API quota availability"""
            available = await self.check_api_quota(service, requests, tokens)
            return {'available': available}
        
        @self.app.post("/quota/{service}/consume")
        async def consume_quota_endpoint(service: str, request: dict):
            """Consume API quota"""
            success = await self.consume_api_quota(
                service,
                request.get('requests', 1),
                request.get('tokens', 0),
                request.get('request_id')
            )
            return {'success': success}
        
        @self.app.get("/status")
        async def status_endpoint():
            """Get resource status"""
            return await self.get_resource_status()
        
        @self.app.get("/optimize")
        async def optimize_endpoint():
            """Get optimization recommendations"""
            return await self.optimize_resource_allocation()
        
        @self.app.get("/metrics")
        async def metrics_endpoint():
            """Get resource metrics"""
            return await self.get_metrics()
        
        @self.app.get("/health")
        async def health_endpoint():
            """Health check"""
            return await self.get_health()
    
    async def shutdown(self):
        """Gracefully shutdown resource coordinator"""
        try:
            logger.info("Shutting down Resource Coordinator...")
            
            # Cancel background tasks
            if self.monitor_task:
                self.monitor_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()
            if self.quota_reset_task:
                self.quota_reset_task.cancel()
            
            # Release all active allocations
            for request_id in list(self.allocations.keys()):
                await self.release_resources(request_id)
            
            self.is_initialized = False
            logger.info("Resource Coordinator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during Resource Coordinator shutdown: {e}")

class ResourceError(Exception):
    """Custom exception for resource-related errors"""
    pass

# Convenience functions
async def create_resource_coordinator(**kwargs) -> ResourceCoordinator:
    """Create and initialize a resource coordinator instance"""
    coordinator = ResourceCoordinator(**kwargs)
    await coordinator.initialize()
    return coordinator