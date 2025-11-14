"""
Main Coordinator - Master coordination hub for ToolboxAI Roblox Environment

Orchestrates all subsystems including agents, swarm, SPARC, and MCP components
to provide unified educational content generation and management.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)


@dataclass
class SystemHealth:
    """System health status"""

    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    component_health: dict[str, str]
    active_workflows: int
    resource_utilization: dict[str, float]
    error_count: int
    last_error: Optional[str] = None


@dataclass
class ContentGenerationRequest:
    """Educational content generation request"""

    request_id: str
    subject: str
    grade_level: int
    learning_objectives: list[str]
    environment_type: str
    include_quiz: bool
    custom_parameters: dict[str, Any]
    priority: int = 1
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ContentGenerationResult:
    """Educational content generation result"""

    request_id: str
    success: bool
    content: Optional[dict[str, Any]]
    scripts: list[str]
    quiz_data: Optional[dict[str, Any]]
    metrics: dict[str, Any]
    errors: list[str]
    generation_time: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MainCoordinator:
    """
    Master coordination hub that orchestrates all subsystems for educational content generation.

    Integrates:
    - Agent systems (LangChain/LangGraph)
    - Swarm intelligence
    - SPARC framework
    - MCP protocol
    - Resource management
    - Error handling
    """

    def __init__(
        self,
        workflow_coordinator=None,
        resource_coordinator=None,
        sync_coordinator=None,
        error_coordinator=None,
        config: dict[str, Any] = None,
    ):
        self.workflow_coordinator = workflow_coordinator
        self.resource_coordinator = resource_coordinator
        self.sync_coordinator = sync_coordinator
        self.error_coordinator = error_coordinator

        # Configuration
        self.config = config or {}
        self.max_concurrent_requests = self.config.get("max_concurrent_requests", 10)
        self.health_check_interval = self.config.get("health_check_interval", 30)
        self.enable_caching = self.config.get("enable_caching", True)

        # State management
        self.is_initialized = False
        self.active_requests: set[str] = set()
        self.request_history: dict[str, ContentGenerationResult] = {}
        self.system_metrics = defaultdict(float)
        self.cache: dict[str, Any] = {}

        # Component connections
        self.agent_system = None
        self.swarm_controller = None
        self.sparc_manager = None
        self.mcp_client = None

        # Background tasks
        self.health_monitor_task = None
        self.metrics_collector_task = None

        # FastAPI app for REST endpoints
        self.app = FastAPI(title="Main Coordinator API", version="1.0.0")
        self._setup_routes()

    async def initialize(self):
        """Initialize the main coordinator and all subsystems"""
        try:
            logger.info("Initializing Main Coordinator...")

            # Initialize subsystem connections
            await self._initialize_subsystems()

            # Start background monitoring
            await self._start_background_tasks()

            # Validate system health
            health = await self.get_health_status()
            if health.status == "unhealthy":
                raise RuntimeError("System initialization failed - unhealthy state")

            self.is_initialized = True
            logger.info("Main Coordinator initialized successfully")

            # Log initial system state
            await self._log_system_state("initialization_complete")

        except Exception as e:
            logger.error(f"Main Coordinator initialization failed: {e}")
            if self.error_coordinator:
                await self.error_coordinator.handle_error(
                    "main_coordinator_init", e, {"component": "main_coordinator"}
                )
            raise

    async def _initialize_subsystems(self):
        """Initialize connections to all subsystems"""
        try:
            # Import and initialize agent system
            from ..agents.orchestrator import AgentOrchestrator

            self.agent_system = AgentOrchestrator()
            await self.agent_system.initialize()

            # Import and initialize swarm controller
            from ..swarm.swarm_controller import SwarmController
            from ..swarm.swarm_factory import create_test_swarm_controller

            self.swarm_controller = create_test_swarm_controller()
            await self.swarm_controller.initialize()

            # Import and initialize SPARC manager
            from ..sparc.state_manager import StateManager

            self.sparc_manager = StateManager()
            await self.sparc_manager.initialize()

            # Import and initialize MCP client
            from ..mcp.client import MCPClient

            self.mcp_client = MCPClient()
            await self.mcp_client.connect()

            logger.info("All subsystems initialized successfully")

        except ImportError as e:
            logger.warning(f"Subsystem import failed: {e}. Operating in degraded mode.")
        except Exception as e:
            logger.error(f"Subsystem initialization failed: {e}")
            raise

    async def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        self.health_monitor_task = asyncio.create_task(self._health_monitor())
        self.metrics_collector_task = asyncio.create_task(self._metrics_collector())

        logger.info("Background monitoring tasks started")

    async def _health_monitor(self):
        """Background task to monitor system health"""
        while self.is_initialized:
            try:
                health = await self.get_health_status()

                # Handle degraded or unhealthy states
                if health.status != "healthy":
                    await self._handle_health_degradation(health)

                # Update metrics
                self.system_metrics["health_checks"] += 1
                self.system_metrics["last_health_check"] = datetime.now().timestamp()

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _metrics_collector(self):
        """Background task to collect and update system metrics"""
        while self.is_initialized:
            try:
                # Collect metrics from all subsystems
                if self.resource_coordinator:
                    resource_metrics = await self.resource_coordinator.get_metrics()
                    self.system_metrics.update(resource_metrics)

                if self.workflow_coordinator:
                    workflow_metrics = await self.workflow_coordinator.get_metrics()
                    self.system_metrics.update(workflow_metrics)

                # Update MCP with current metrics
                if self.mcp_client:
                    await self.mcp_client.update_context(
                        {
                            "system_metrics": dict(self.system_metrics),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                await asyncio.sleep(60)  # Collect metrics every minute

            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(60)

    async def generate_educational_content(
        self,
        subject: str,
        grade_level: int,
        learning_objectives: list[str],
        environment_type: str = "classroom",
        include_quiz: bool = True,
        custom_parameters: dict[str, Any] = None,
        priority: int = 1,
    ) -> ContentGenerationResult:
        """
        Generate comprehensive educational content using all system capabilities

        Args:
            subject: Academic subject (e.g., "Mathematics", "Science")
            grade_level: Student grade level (1-12)
            learning_objectives: List of specific learning goals
            environment_type: Roblox environment type
            include_quiz: Whether to include assessment components
            custom_parameters: Additional customization parameters
            priority: Request priority (1=low, 5=high)

        Returns:
            ContentGenerationResult with complete generated content
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Create request object
        request = ContentGenerationRequest(
            request_id=request_id,
            subject=subject,
            grade_level=grade_level,
            learning_objectives=learning_objectives,
            environment_type=environment_type,
            include_quiz=include_quiz,
            custom_parameters=custom_parameters or {},
            priority=priority,
        )

        try:
            # Validate request capacity
            if len(self.active_requests) >= self.max_concurrent_requests:
                raise HTTPException(status_code=429, detail="Too many concurrent requests")

            self.active_requests.add(request_id)
            logger.info(f"Starting content generation for request {request_id}")

            # Check cache for similar requests
            if self.enable_caching:
                cached_result = await self._check_cache(request)
                if cached_result:
                    return cached_result

            # Allocate resources
            if self.resource_coordinator:
                await self.resource_coordinator.allocate_resources(
                    request_id,
                    {
                        "cpu_cores": 2,
                        "memory_mb": 1024,
                        "gpu_memory_mb": 512 if include_quiz else 256,
                    },
                )

            # Create comprehensive workflow
            workflow_id = None
            if self.workflow_coordinator:
                workflow_id = await self.workflow_coordinator.create_workflow(
                    "educational_content_generation",
                    {
                        "request": asdict(request),
                        "coordination_mode": "full_orchestration",
                    },
                )

            # Initialize SPARC cycle for adaptive generation
            sparc_context = {}
            if self.sparc_manager:
                sparc_context = await self.sparc_manager.initialize_context(
                    user_profile={"grade_level": grade_level},
                    learning_objectives=learning_objectives,
                )

            # Execute multi-agent content generation
            content_result = await self._orchestrate_content_generation(
                request, workflow_id, sparc_context
            )

            # Generate result object
            generation_time = (datetime.now() - start_time).total_seconds()
            result = ContentGenerationResult(
                request_id=request_id,
                success=True,
                content=content_result.get("content"),
                scripts=content_result.get("scripts", []),
                quiz_data=content_result.get("quiz_data"),
                metrics={
                    "generation_time": generation_time,
                    "agents_used": content_result.get("agents_used", []),
                    "complexity_score": content_result.get("complexity_score", 0),
                    "quality_score": content_result.get("quality_score", 0),
                },
                errors=content_result.get("errors", []),
                generation_time=generation_time,
            )

            # Cache successful results
            if self.enable_caching and result.success:
                await self._cache_result(request, result)

            # Update metrics
            self.system_metrics["content_generations"] += 1
            self.system_metrics["total_generation_time"] += generation_time

            # Store in request history
            self.request_history[request_id] = result

            logger.info(
                f"Content generation completed for request {request_id} in {generation_time:.2f}s"
            )
            return result

        except Exception as e:
            # Handle errors
            generation_time = (datetime.now() - start_time).total_seconds()
            result = ContentGenerationResult(
                request_id=request_id,
                success=False,
                content=None,
                scripts=[],
                quiz_data=None,
                metrics={"generation_time": generation_time},
                errors=[str(e)],
                generation_time=generation_time,
            )

            # Log error
            logger.error(f"Content generation failed for request {request_id}: {e}")

            if self.error_coordinator:
                await self.error_coordinator.handle_error(
                    "content_generation",
                    e,
                    {"request_id": request_id, "subject": subject},
                )

            return result

        finally:
            # Cleanup
            self.active_requests.discard(request_id)
            if self.resource_coordinator:
                await self.resource_coordinator.release_resources(request_id)

    async def _orchestrate_content_generation(
        self,
        request: ContentGenerationRequest,
        workflow_id: Optional[str],
        sparc_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Orchestrate the multi-agent content generation process"""

        # Phase 1: Content Planning (Agent System)
        content_plan = {}
        if self.agent_system:
            content_plan = await self.agent_system.plan_content(
                subject=request.subject,
                grade_level=request.grade_level,
                learning_objectives=request.learning_objectives,
                environment_type=request.environment_type,
            )

        # Phase 2: Parallel Content Generation (Swarm)
        generation_tasks = []
        if self.swarm_controller:
            # Terrain generation task
            generation_tasks.append(
                self.swarm_controller.execute_task(
                    {
                        "type": "terrain_generation",
                        "parameters": {
                            "environment_type": request.environment_type,
                            "subject_theme": request.subject,
                            "size": "large" if request.grade_level >= 6 else "medium",
                        },
                    }
                )
            )

            # Script generation task
            generation_tasks.append(
                self.swarm_controller.execute_task(
                    {
                        "type": "script_generation",
                        "parameters": {
                            "content_plan": content_plan,
                            "learning_objectives": request.learning_objectives,
                        },
                    }
                )
            )

            # Quiz generation task (if requested)
            if request.include_quiz:
                generation_tasks.append(
                    self.swarm_controller.execute_task(
                        {
                            "type": "quiz_generation",
                            "parameters": {
                                "subject": request.subject,
                                "grade_level": request.grade_level,
                                "objectives": request.learning_objectives,
                                "difficulty": "adaptive",
                            },
                        }
                    )
                )

            # Execute all tasks in parallel
            generation_results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        else:
            generation_results = []

        # Phase 3: SPARC-based Adaptation
        if self.sparc_manager and sparc_context:
            # Evaluate initial generation
            evaluation = await self.sparc_manager.evaluate_content(
                content_plan, generation_results, sparc_context
            )

            # Adapt content based on evaluation
            if evaluation.get("needs_adaptation"):
                adapted_content = await self.sparc_manager.adapt_content(
                    generation_results, evaluation, sparc_context
                )
                generation_results = adapted_content

        # Phase 4: Quality Consensus and Assembly
        final_content = await self._assemble_final_content(
            content_plan, generation_results, request
        )

        return final_content

    async def _assemble_final_content(
        self,
        content_plan: dict[str, Any],
        generation_results: list[Any],
        request: ContentGenerationRequest,
    ) -> dict[str, Any]:
        """Assemble final content from all generation phases"""

        content = {
            "metadata": {
                "subject": request.subject,
                "grade_level": request.grade_level,
                "learning_objectives": request.learning_objectives,
                "environment_type": request.environment_type,
                "generation_timestamp": datetime.now().isoformat(),
            },
            "content_plan": content_plan,
            "scripts": [],
            "terrain_data": None,
            "quiz_data": None,
            "agents_used": [],
            "complexity_score": 0,
            "quality_score": 0,
            "errors": [],
        }

        # Process generation results
        for result in generation_results:
            if isinstance(result, Exception):
                content["errors"].append(str(result))
                continue

            if result.get("type") == "terrain_generation":
                content["terrain_data"] = result.get("data")
                content["scripts"].extend(result.get("scripts", []))

            elif result.get("type") == "script_generation":
                content["scripts"].extend(result.get("scripts", []))

            elif result.get("type") == "quiz_generation":
                content["quiz_data"] = result.get("data")

            # Track agents used
            if result.get("agent_id"):
                content["agents_used"].append(result["agent_id"])

        # Calculate quality metrics
        content["complexity_score"] = self._calculate_complexity_score(content)
        content["quality_score"] = self._calculate_quality_score(content)

        return content

    def _calculate_complexity_score(self, content: dict[str, Any]) -> float:
        """Calculate content complexity score (0-100)"""
        score = 0

        # Base complexity from learning objectives
        score += len(content["metadata"]["learning_objectives"]) * 10

        # Environment complexity
        if content["terrain_data"]:
            score += 20

        # Script complexity
        total_script_lines = sum(len(script.split("\n")) for script in content["scripts"])
        score += min(total_script_lines / 10, 30)

        # Quiz complexity
        if content["quiz_data"]:
            num_questions = len(content["quiz_data"].get("questions", []))
            score += min(num_questions * 2, 20)

        return min(score, 100)

    def _calculate_quality_score(self, content: dict[str, Any]) -> float:
        """Calculate content quality score (0-100)"""
        score = 100

        # Deduct for errors
        score -= len(content["errors"]) * 10

        # Deduct if missing expected components
        if not content["scripts"]:
            score -= 20

        if content["metadata"]["environment_type"] != "text_only" and not content["terrain_data"]:
            score -= 15

        # Bonus for comprehensive content
        if content["quiz_data"] and len(content["scripts"]) >= 3:
            score += 10

        return max(0, min(score, 100))

    async def _check_cache(
        self, request: ContentGenerationRequest
    ) -> Optional[ContentGenerationResult]:
        """Check cache for similar content requests"""
        cache_key = (
            f"{request.subject}_{request.grade_level}_{hash(tuple(request.learning_objectives))}"
        )

        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Return cached result with updated timestamp
            cached_result = ContentGenerationResult(**cached_data)
            cached_result.request_id = request.request_id
            cached_result.timestamp = datetime.now()

            logger.info(f"Cache hit for request {request.request_id}")
            return cached_result

        return None

    async def _cache_result(
        self, request: ContentGenerationRequest, result: ContentGenerationResult
    ):
        """Cache successful generation result"""
        cache_key = (
            f"{request.subject}_{request.grade_level}_{hash(tuple(request.learning_objectives))}"
        )

        # Store result data (without request-specific fields)
        cache_data = asdict(result)
        cache_data["request_id"] = None  # Remove request-specific ID

        self.cache[cache_key] = cache_data

        # Limit cache size
        if len(self.cache) > 100:
            # Remove oldest entries
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

    async def get_health_status(self) -> SystemHealth:
        """Get comprehensive system health status"""
        component_health = {}
        error_count = 0
        last_error = None

        # Check subsystem health
        if self.workflow_coordinator:
            try:
                wf_health = await self.workflow_coordinator.get_health()
                component_health["workflow"] = wf_health["status"]
            except Exception as e:
                component_health["workflow"] = "unhealthy"
                error_count += 1
                last_error = str(e)

        if self.resource_coordinator:
            try:
                rc_health = await self.resource_coordinator.get_health()
                component_health["resource"] = rc_health["status"]
            except Exception as e:
                component_health["resource"] = "unhealthy"
                error_count += 1
                last_error = str(e)

        if self.sync_coordinator:
            try:
                sc_health = await self.sync_coordinator.get_health()
                component_health["sync"] = sc_health["status"]
            except Exception as e:
                component_health["sync"] = "unhealthy"
                error_count += 1
                last_error = str(e)

        # Check external subsystems
        subsystem_checks = [
            ("agent_system", self.agent_system),
            ("swarm_controller", self.swarm_controller),
            ("sparc_manager", self.sparc_manager),
            ("mcp_client", self.mcp_client),
        ]

        for name, system in subsystem_checks:
            if system:
                try:
                    if hasattr(system, "get_health"):
                        health = await system.get_health()
                        component_health[name] = health.get("status", "unknown")
                    else:
                        component_health[name] = "healthy"  # Assume healthy if no health check
                except Exception as e:
                    component_health[name] = "unhealthy"
                    error_count += 1
                    last_error = str(e)
            else:
                component_health[name] = "not_initialized"

        # Determine overall status
        unhealthy_count = sum(1 for status in component_health.values() if status == "unhealthy")
        degraded_count = sum(1 for status in component_health.values() if status == "degraded")

        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Get resource utilization
        resource_utilization = {}
        if self.resource_coordinator:
            try:
                resource_utilization = await self.resource_coordinator.get_utilization()
            except (AttributeError, KeyError, TypeError):
                pass

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            component_health=component_health,
            active_workflows=len(self.active_requests),
            resource_utilization=resource_utilization,
            error_count=error_count,
            last_error=last_error,
        )

    async def _handle_health_degradation(self, health: SystemHealth):
        """Handle system health degradation"""
        if health.status == "degraded":
            logger.warning(f"System health degraded: {health.component_health}")
            # Implement degraded mode logic

        elif health.status == "unhealthy":
            logger.error(f"System unhealthy: {health.component_health}")
            # Implement emergency procedures

            if self.error_coordinator:
                await self.error_coordinator.handle_error(
                    "system_health_critical",
                    RuntimeError("System health critical"),
                    {"health_status": asdict(health)},
                )

    async def _log_system_state(self, event: str):
        """Log current system state for monitoring"""
        state = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "active_requests": len(self.active_requests),
            "cache_size": len(self.cache),
            "metrics": dict(self.system_metrics),
        }

        logger.info(f"System state - {event}: {state}")

        # Send to MCP for context
        if self.mcp_client:
            await self.mcp_client.update_context({"system_state": state})

    def _setup_routes(self):
        """Setup FastAPI routes for REST API"""

        @self.app.post("/generate_content")
        async def generate_content_endpoint(request: dict):
            """REST endpoint for content generation"""
            result = await self.generate_educational_content(**request)
            return asdict(result)

        @self.app.get("/health")
        async def health_endpoint():
            """Health check endpoint"""
            health = await self.get_health_status()
            return asdict(health)

        @self.app.get("/metrics")
        async def metrics_endpoint():
            """System metrics endpoint"""
            return dict(self.system_metrics)

        @self.app.get("/requests/{request_id}")
        async def get_request_endpoint(request_id: str):
            """Get request status and result"""
            if request_id in self.request_history:
                return asdict(self.request_history[request_id])
            else:
                raise HTTPException(status_code=404, detail="Request not found")

    async def shutdown(self):
        """Gracefully shutdown the main coordinator"""
        try:
            logger.info("Shutting down Main Coordinator...")

            # Cancel background tasks
            if self.health_monitor_task:
                self.health_monitor_task.cancel()
            if self.metrics_collector_task:
                self.metrics_collector_task.cancel()

            # Wait for active requests to complete (with timeout)
            if self.active_requests:
                logger.info(
                    f"Waiting for {len(self.active_requests)} active requests to complete..."
                )
                timeout = 30
                while self.active_requests and timeout > 0:
                    await asyncio.sleep(1)
                    timeout -= 1

            # Shutdown subsystem connections
            if self.agent_system and hasattr(self.agent_system, "shutdown"):
                await self.agent_system.shutdown()

            if self.swarm_controller and hasattr(self.swarm_controller, "shutdown"):
                await self.swarm_controller.shutdown()

            if self.sparc_manager and hasattr(self.sparc_manager, "shutdown"):
                await self.sparc_manager.shutdown()

            if self.mcp_client and hasattr(self.mcp_client, "disconnect"):
                await self.mcp_client.disconnect()

            self.is_initialized = False
            logger.info("Main Coordinator shutdown complete")

        except Exception as e:
            logger.error(f"Error during Main Coordinator shutdown: {e}")


# Convenience functions for external usage
async def create_main_coordinator(**kwargs) -> MainCoordinator:
    """Create and initialize a main coordinator instance"""
    coordinator = MainCoordinator(**kwargs)
    await coordinator.initialize()
    return coordinator
