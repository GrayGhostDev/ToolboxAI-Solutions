"""
Workflow Coordinator - End-to-end workflow management for educational content generation

Manages complex multi-step educational workflows, templates, progress tracking,
and optimization for the ToolboxAI Roblox Environment.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import uuid
from collections import defaultdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class StepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    name: str
    description: str
    executor: str  # Which system executes this step
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # Default 5 minute timeout
    retry_count: int = 3
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate step duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

@dataclass
class Workflow:
    """Complete workflow definition and state"""
    workflow_id: str
    name: str
    description: str
    workflow_type: str
    steps: List[WorkflowStep]
    parameters: Dict[str, Any]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_time: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    priority: int = 1
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate workflow duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def progress(self) -> float:
        """Calculate workflow progress percentage"""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps if step.status == StepStatus.COMPLETED)
        return (completed_steps / len(self.steps)) * 100

class WorkflowTemplate:
    """Template for creating workflow instances"""
    
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.step_templates = steps
    
    def create_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Workflow:
        """Create workflow instance from template"""
        steps = []
        
        for i, step_template in enumerate(self.step_templates):
            step = WorkflowStep(
                step_id=f"{workflow_id}_step_{i}",
                name=step_template['name'],
                description=step_template['description'],
                executor=step_template['executor'],
                parameters={**step_template.get('parameters', {}), **parameters},
                dependencies=step_template.get('dependencies', []),
                timeout=step_template.get('timeout', 300),
                retry_count=step_template.get('retry_count', 3)
            )
            steps.append(step)
        
        return Workflow(
            workflow_id=workflow_id,
            name=self.name,
            description=self.description,
            workflow_type=self.name.lower().replace(' ', '_'),
            steps=steps,
            parameters=parameters
        )

class WorkflowCoordinator:
    """
    End-to-end workflow management system for educational content generation.
    
    Handles:
    - Workflow templates and instantiation
    - Step-by-step execution with dependencies
    - Progress tracking and reporting
    - Error handling and recovery
    - Workflow optimization and learning
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Core state
        self.is_initialized = False
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.executor_registry: Dict[str, Callable] = {}
        
        # Execution management
        self.max_concurrent_workflows = self.config.get('max_concurrent_workflows', 5)
        self.active_workflows: Set[str] = set()
        self.workflow_queue: List[str] = []
        
        # Metrics and optimization
        self.execution_metrics = defaultdict(list)
        self.step_performance = defaultdict(float)
        self.optimization_data = defaultdict(dict)
        
        # Background tasks
        self.executor_task = None
        self.optimizer_task = None
        
        # FastAPI app for workflow management
        self.app = FastAPI(title="Workflow Coordinator API", version="1.0.0")
        self._setup_routes()
        
        # Setup built-in templates
        self._setup_default_templates()
    
    async def initialize(self):
        """Initialize the workflow coordinator"""
        try:
            logger.info("Initializing Workflow Coordinator...")
            
            # Setup executor registry
            await self._setup_executors()
            
            # Start background tasks
            self.executor_task = asyncio.create_task(self._workflow_executor())
            self.optimizer_task = asyncio.create_task(self._workflow_optimizer())
            
            self.is_initialized = True
            logger.info("Workflow Coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"Workflow Coordinator initialization failed: {e}")
            raise
    
    def _setup_default_templates(self):
        """Setup built-in workflow templates for educational scenarios"""
        
        # Educational Content Generation Workflow
        self.templates['educational_content_generation'] = WorkflowTemplate(
            name="Educational Content Generation",
            description="Complete educational content generation workflow",
            steps=[
                {
                    'name': 'Curriculum Analysis',
                    'description': 'Analyze curriculum standards and learning objectives',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'content_agent'},
                    'timeout': 120
                },
                {
                    'name': 'Environment Planning',
                    'description': 'Plan 3D environment layout and structure',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'terrain_agent'},
                    'dependencies': ['curriculum_analysis'],
                    'timeout': 180
                },
                {
                    'name': 'Script Generation',
                    'description': 'Generate Lua scripts for game mechanics',
                    'executor': 'swarm_controller',
                    'parameters': {'task_type': 'script_generation'},
                    'dependencies': ['environment_planning'],
                    'timeout': 300
                },
                {
                    'name': 'Quiz Creation',
                    'description': 'Create interactive quiz components',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'quiz_agent'},
                    'dependencies': ['curriculum_analysis'],
                    'timeout': 200
                },
                {
                    'name': 'Content Integration',
                    'description': 'Integrate all components into final product',
                    'executor': 'sparc_manager',
                    'parameters': {'integration_mode': 'full'},
                    'dependencies': ['script_generation', 'quiz_creation'],
                    'timeout': 240
                },
                {
                    'name': 'Quality Assurance',
                    'description': 'Review and validate generated content',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'review_agent'},
                    'dependencies': ['content_integration'],
                    'timeout': 180
                }
            ]
        )
        
        # Course Creation Workflow
        self.templates['complete_course_generation'] = WorkflowTemplate(
            name="Complete Course Generation",
            description="Generate a complete course with multiple lessons",
            steps=[
                {
                    'name': 'Course Structure Planning',
                    'description': 'Plan overall course structure and lesson sequence',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'content_agent', 'scope': 'course'},
                    'timeout': 300
                },
                {
                    'name': 'Lesson Content Generation',
                    'description': 'Generate content for individual lessons',
                    'executor': 'swarm_controller',
                    'parameters': {'task_type': 'parallel_lesson_generation'},
                    'dependencies': ['course_structure_planning'],
                    'timeout': 600
                },
                {
                    'name': 'Assessment Design',
                    'description': 'Design comprehensive assessment strategy',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'quiz_agent', 'scope': 'course'},
                    'dependencies': ['lesson_content_generation'],
                    'timeout': 300
                },
                {
                    'name': 'Navigation System',
                    'description': 'Create course navigation and progression system',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'script_agent', 'scope': 'navigation'},
                    'dependencies': ['lesson_content_generation'],
                    'timeout': 240
                },
                {
                    'name': 'Final Assembly',
                    'description': 'Assemble complete course package',
                    'executor': 'sparc_manager',
                    'parameters': {'integration_mode': 'course'},
                    'dependencies': ['assessment_design', 'navigation_system'],
                    'timeout': 300
                }
            ]
        )
        
        # Adaptive Assessment Workflow
        self.templates['adaptive_assessment_generation'] = WorkflowTemplate(
            name="Adaptive Assessment Generation",
            description="Generate adaptive assessment with difficulty adjustment",
            steps=[
                {
                    'name': 'Student Profile Analysis',
                    'description': 'Analyze student performance and learning patterns',
                    'executor': 'sparc_manager',
                    'parameters': {'analysis_type': 'student_profile'},
                    'timeout': 120
                },
                {
                    'name': 'Difficulty Calibration',
                    'description': 'Calibrate assessment difficulty levels',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'quiz_agent', 'mode': 'adaptive'},
                    'dependencies': ['student_profile_analysis'],
                    'timeout': 180
                },
                {
                    'name': 'Question Generation',
                    'description': 'Generate adaptive questions with multiple difficulty levels',
                    'executor': 'swarm_controller',
                    'parameters': {'task_type': 'adaptive_quiz_generation'},
                    'dependencies': ['difficulty_calibration'],
                    'timeout': 400
                },
                {
                    'name': 'Feedback System Creation',
                    'description': 'Create adaptive feedback and hint systems',
                    'executor': 'agent_system',
                    'parameters': {'agent_type': 'script_agent', 'scope': 'feedback'},
                    'dependencies': ['question_generation'],
                    'timeout': 200
                },
                {
                    'name': 'Assessment Assembly',
                    'description': 'Assemble complete adaptive assessment',
                    'executor': 'sparc_manager',
                    'parameters': {'integration_mode': 'adaptive_assessment'},
                    'dependencies': ['feedback_system_creation'],
                    'timeout': 180
                }
            ]
        )
        
        logger.info(f"Loaded {len(self.templates)} workflow templates")
    
    async def _setup_executors(self):
        """Setup executor registry for different step types"""
        
        # Agent System Executor
        async def agent_executor(step: WorkflowStep) -> Dict[str, Any]:
            """Execute step using agent system"""
            from ..agents.orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator()
            
            agent_type = step.parameters.get('agent_type', 'content_agent')
            scope = step.parameters.get('scope', 'default')
            
            result = await orchestrator.execute_agent_task(
                agent_type=agent_type,
                task_data=step.parameters,
                context={'scope': scope, 'step_id': step.step_id}
            )
            
            return result
        
        # Swarm Controller Executor
        async def swarm_executor(step: WorkflowStep) -> Dict[str, Any]:
            """Execute step using swarm controller"""
            from ..swarm.swarm_controller import SwarmController
            controller = SwarmController()
            
            task_type = step.parameters.get('task_type', 'general')
            
            result = await controller.execute_distributed_task(
                task_type=task_type,
                task_data=step.parameters,
                context={'step_id': step.step_id}
            )
            
            return result
        
        # SPARC Manager Executor
        async def sparc_executor(step: WorkflowStep) -> Dict[str, Any]:
            """Execute step using SPARC manager"""
            from ..sparc.state_manager import StateManager
            manager = StateManager()
            
            integration_mode = step.parameters.get('integration_mode', 'default')
            analysis_type = step.parameters.get('analysis_type', 'general')
            
            if analysis_type != 'general':
                result = await manager.analyze_context(
                    analysis_type=analysis_type,
                    data=step.parameters
                )
            else:
                result = await manager.integrate_components(
                    mode=integration_mode,
                    components=step.parameters
                )
            
            return result
        
        # Register executors
        self.executor_registry = {
            'agent_system': agent_executor,
            'swarm_controller': swarm_executor,
            'sparc_manager': sparc_executor
        }
        
        logger.info(f"Registered {len(self.executor_registry)} step executors")
    
    async def create_workflow(
        self,
        workflow_type: str,
        parameters: Dict[str, Any],
        priority: int = 1
    ) -> str:
        """
        Create a new workflow instance from template
        
        Args:
            workflow_type: Template name to use
            parameters: Workflow-specific parameters
            priority: Execution priority (1=low, 5=high)
            
        Returns:
            Workflow ID for tracking
        """
        if workflow_type not in self.templates:
            raise ValueError(f"Unknown workflow template: {workflow_type}")
        
        workflow_id = str(uuid.uuid4())
        template = self.templates[workflow_type]
        
        # Create workflow from template
        workflow = template.create_workflow(workflow_id, parameters)
        workflow.priority = priority
        
        # Store workflow
        self.workflows[workflow_id] = workflow
        
        # Queue for execution
        self.workflow_queue.append(workflow_id)
        self.workflow_queue.sort(key=lambda wid: self.workflows[wid].priority, reverse=True)
        
        logger.info(f"Created workflow {workflow_id} of type {workflow_type}")
        
        # Update metrics
        self.execution_metrics['workflows_created'].append({
            'workflow_id': workflow_id,
            'type': workflow_type,
            'timestamp': datetime.now().isoformat()
        })
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a specific workflow
        
        Args:
            workflow_id: ID of workflow to execute
            
        Returns:
            Workflow execution result
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        try:
            # Mark as running
            workflow.status = WorkflowStatus.RUNNING
            workflow.start_time = datetime.now()
            self.active_workflows.add(workflow_id)
            
            logger.info(f"Starting execution of workflow {workflow_id} ({workflow.name})")
            
            # Execute steps in dependency order
            executed_steps = set()
            
            while len(executed_steps) < len(workflow.steps):
                # Find next executable steps
                executable_steps = []
                
                for step in workflow.steps:
                    if (step.step_id not in executed_steps and 
                        step.status == StepStatus.PENDING and
                        all(dep in executed_steps for dep in step.dependencies)):
                        executable_steps.append(step)
                
                if not executable_steps:
                    # Check for circular dependencies or other issues
                    remaining_steps = [s for s in workflow.steps if s.step_id not in executed_steps]
                    if remaining_steps:
                        raise RuntimeError(f"Cannot execute remaining steps: {[s.name for s in remaining_steps]}")
                    break
                
                # Execute steps in parallel where possible
                step_tasks = []
                for step in executable_steps:
                    task = asyncio.create_task(self._execute_step(step, workflow))
                    step_tasks.append(task)
                
                # Wait for all steps to complete
                step_results = await asyncio.gather(*step_tasks, return_exceptions=True)
                
                # Process results
                for step, result in zip(executable_steps, step_results):
                    if isinstance(result, Exception):
                        step.status = StepStatus.FAILED
                        step.error = str(result)
                        step.end_time = datetime.now()
                        logger.error(f"Step {step.name} failed: {result}")
                    else:
                        step.status = StepStatus.COMPLETED
                        step.result = result
                        step.end_time = datetime.now()
                        executed_steps.add(step.step_id)
                        logger.info(f"Step {step.name} completed successfully")
            
            # Check if all steps completed successfully
            failed_steps = [s for s in workflow.steps if s.status == StepStatus.FAILED]
            
            if failed_steps:
                workflow.status = WorkflowStatus.FAILED
                workflow.error = f"Failed steps: {[s.name for s in failed_steps]}"
                logger.error(f"Workflow {workflow_id} failed with {len(failed_steps)} failed steps")
            else:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.result = await self._assemble_workflow_result(workflow)
                logger.info(f"Workflow {workflow_id} completed successfully")
            
            workflow.end_time = datetime.now()
            
            # Record execution metrics
            await self._record_execution_metrics(workflow)
            
            return asdict(workflow)
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.end_time = datetime.now()
            
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            raise
            
        finally:
            self.active_workflows.discard(workflow_id)
    
    async def _execute_step(self, step: WorkflowStep, workflow: Workflow) -> Dict[str, Any]:
        """Execute an individual workflow step"""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        
        logger.info(f"Executing step: {step.name} (executor: {step.executor})")
        
        try:
            # Get executor function
            if step.executor not in self.executor_registry:
                raise ValueError(f"Unknown executor: {step.executor}")
            
            executor = self.executor_registry[step.executor]
            
            # Execute with timeout
            result = await asyncio.wait_for(
                executor(step),
                timeout=step.timeout
            )
            
            # Record performance
            if step.duration:
                self.step_performance[f"{step.executor}_{step.name}"] = step.duration
            
            return result
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"Step {step.name} timed out after {step.timeout} seconds")
        except Exception as e:
            # Retry logic
            if step.retry_count > 0:
                step.retry_count -= 1
                logger.warning(f"Step {step.name} failed, retrying... ({step.retry_count} retries left)")
                await asyncio.sleep(2)  # Brief delay before retry
                return await self._execute_step(step, workflow)
            else:
                raise
    
    async def _assemble_workflow_result(self, workflow: Workflow) -> Dict[str, Any]:
        """Assemble final workflow result from all step results"""
        result = {
            'workflow_id': workflow.workflow_id,
            'name': workflow.name,
            'type': workflow.workflow_type,
            'success': True,
            'duration': workflow.duration,
            'steps_completed': len([s for s in workflow.steps if s.status == StepStatus.COMPLETED]),
            'total_steps': len(workflow.steps),
            'step_results': {},
            'final_content': {},
            'metadata': {
                'created_time': workflow.created_time.isoformat(),
                'execution_time': workflow.start_time.isoformat() if workflow.start_time else None,
                'completion_time': workflow.end_time.isoformat() if workflow.end_time else None,
                'parameters': workflow.parameters
            }
        }
        
        # Aggregate step results
        for step in workflow.steps:
            if step.result:
                result['step_results'][step.name] = step.result
                
                # Extract content for final assembly
                if step.name == 'Content Integration':
                    result['final_content'] = step.result
                elif 'content' in step.result:
                    result['final_content'].update(step.result['content'])
        
        return result
    
    async def _workflow_executor(self):
        """Background task to execute queued workflows"""
        while self.is_initialized:
            try:
                # Check if we can start new workflows
                if (len(self.active_workflows) < self.max_concurrent_workflows and 
                    self.workflow_queue):
                    
                    workflow_id = self.workflow_queue.pop(0)
                    
                    # Execute workflow in background
                    asyncio.create_task(self.execute_workflow(workflow_id))
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Workflow executor error: {e}")
                await asyncio.sleep(5)
    
    async def _workflow_optimizer(self):
        """Background task to optimize workflow performance"""
        while self.is_initialized:
            try:
                await asyncio.sleep(300)  # Optimize every 5 minutes
                
                # Analyze step performance
                await self._analyze_step_performance()
                
                # Optimize workflow templates
                await self._optimize_templates()
                
                # Clean old execution data
                await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Workflow optimizer error: {e}")
    
    async def _analyze_step_performance(self):
        """Analyze step execution performance for optimization"""
        performance_analysis = {}
        
        for step_key, duration in self.step_performance.items():
            executor, step_name = step_key.split('_', 1)
            
            if executor not in performance_analysis:
                performance_analysis[executor] = {}
            
            performance_analysis[executor][step_name] = {
                'avg_duration': duration,
                'optimization_suggestions': []
            }
            
            # Generate optimization suggestions
            if duration > 300:  # 5 minutes
                performance_analysis[executor][step_name]['optimization_suggestions'].append(
                    'Consider breaking into smaller steps'
                )
            
            if duration > 600:  # 10 minutes
                performance_analysis[executor][step_name]['optimization_suggestions'].append(
                    'High execution time - investigate bottlenecks'
                )
        
        self.optimization_data['step_performance'] = performance_analysis
        logger.debug(f"Step performance analysis: {performance_analysis}")
    
    async def _optimize_templates(self):
        """Optimize workflow templates based on execution history"""
        # Analyze workflow success rates
        for template_name, template in self.templates.items():
            executions = [w for w in self.workflows.values() 
                         if w.workflow_type == template_name.lower().replace(' ', '_')]
            
            if len(executions) >= 5:  # Need minimum executions for analysis
                success_rate = len([w for w in executions if w.status == WorkflowStatus.COMPLETED]) / len(executions)
                avg_duration = sum(w.duration or 0 for w in executions) / len(executions)
                
                optimization_suggestions = []
                
                if success_rate < 0.8:
                    optimization_suggestions.append('Low success rate - review step dependencies')
                
                if avg_duration > 1800:  # 30 minutes
                    optimization_suggestions.append('Long execution time - consider parallelization')
                
                self.optimization_data['templates'][template_name] = {
                    'success_rate': success_rate,
                    'avg_duration': avg_duration,
                    'total_executions': len(executions),
                    'optimization_suggestions': optimization_suggestions
                }
    
    async def _cleanup_old_data(self):
        """Clean up old workflow data and metrics"""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        # Remove old completed workflows
        old_workflows = [
            wid for wid, workflow in self.workflows.items()
            if (workflow.end_time and workflow.end_time < cutoff_time and
                workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED])
        ]
        
        for workflow_id in old_workflows:
            del self.workflows[workflow_id]
        
        # Clean metrics
        cutoff_timestamp = cutoff_time.isoformat()
        for metric_list in self.execution_metrics.values():
            metric_list[:] = [m for m in metric_list if m.get('timestamp', '') > cutoff_timestamp]
        
        if old_workflows:
            logger.info(f"Cleaned up {len(old_workflows)} old workflows")
    
    async def _record_execution_metrics(self, workflow: Workflow):
        """Record workflow execution metrics"""
        metrics = {
            'workflow_id': workflow.workflow_id,
            'type': workflow.workflow_type,
            'duration': workflow.duration,
            'success': workflow.status == WorkflowStatus.COMPLETED,
            'steps_completed': len([s for s in workflow.steps if s.status == StepStatus.COMPLETED]),
            'total_steps': len(workflow.steps),
            'timestamp': datetime.now().isoformat()
        }
        
        self.execution_metrics['workflow_executions'].append(metrics)
        
        # Update aggregate metrics
        if workflow.status == WorkflowStatus.COMPLETED:
            self.execution_metrics['successful_workflows'].append(metrics)
        else:
            self.execution_metrics['failed_workflows'].append(metrics)
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'progress': workflow.progress,
            'duration': workflow.duration,
            'steps': [
                {
                    'name': step.name,
                    'status': step.status.value,
                    'duration': step.duration,
                    'error': step.error
                }
                for step in workflow.steps
            ],
            'result': workflow.result,
            'error': workflow.error
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.now()
            
            # Cancel running steps
            for step in workflow.steps:
                if step.status == StepStatus.RUNNING:
                    step.status = StepStatus.SKIPPED
                    step.end_time = datetime.now()
            
            self.active_workflows.discard(workflow_id)
            logger.info(f"Cancelled workflow {workflow_id}")
            return True
        
        return False
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.PAUSED
            logger.info(f"Paused workflow {workflow_id}")
            return True
        
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.RUNNING
            logger.info(f"Resumed workflow {workflow_id}")
            return True
        
        return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get workflow coordinator metrics"""
        total_workflows = len(self.workflows)
        completed_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.COMPLETED])
        failed_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.FAILED])
        
        return {
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'success_rate': completed_workflows / total_workflows if total_workflows > 0 else 0,
            'active_workflows': len(self.active_workflows),
            'queued_workflows': len(self.workflow_queue),
            'avg_execution_time': self._calculate_avg_execution_time(),
            'step_performance': dict(self.step_performance),
            'optimization_data': dict(self.optimization_data)
        }
    
    def _calculate_avg_execution_time(self) -> float:
        """Calculate average workflow execution time"""
        completed = [w for w in self.workflows.values() 
                    if w.status == WorkflowStatus.COMPLETED and w.duration]
        
        if not completed:
            return 0.0
        
        return sum(w.duration for w in completed) / len(completed)
    
    async def get_health(self) -> Dict[str, Any]:
        """Get workflow coordinator health status"""
        try:
            # Check executor availability
            executor_health = {}
            for name, executor in self.executor_registry.items():
                try:
                    # Test executor with dummy step
                    test_step = WorkflowStep(
                        step_id="health_check",
                        name="Health Check",
                        description="Health check step",
                        executor=name,
                        parameters={'health_check': True}
                    )
                    
                    # Quick timeout for health check
                    await asyncio.wait_for(executor(test_step), timeout=5)
                    executor_health[name] = 'healthy'
                except Exception as e:
                    executor_health[name] = 'unhealthy'
                    logger.warning(f"Executor {name} health check failed: {e}")
            
            # Overall health determination
            unhealthy_executors = sum(1 for status in executor_health.values() if status == 'unhealthy')
            
            if unhealthy_executors == 0:
                status = 'healthy'
            elif unhealthy_executors < len(executor_health) / 2:
                status = 'degraded'
            else:
                status = 'unhealthy'
            
            return {
                'status': status,
                'executor_health': executor_health,
                'active_workflows': len(self.active_workflows),
                'queue_length': len(self.workflow_queue),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _setup_routes(self):
        """Setup FastAPI routes for workflow management"""
        
        @self.app.post("/workflows")
        async def create_workflow_endpoint(request: dict):
            """Create new workflow"""
            workflow_id = await self.create_workflow(
                workflow_type=request['workflow_type'],
                parameters=request['parameters'],
                priority=request.get('priority', 1)
            )
            return {'workflow_id': workflow_id}
        
        @self.app.get("/workflows/{workflow_id}")
        async def get_workflow_endpoint(workflow_id: str):
            """Get workflow status"""
            return await self.get_workflow_status(workflow_id)
        
        @self.app.post("/workflows/{workflow_id}/cancel")
        async def cancel_workflow_endpoint(workflow_id: str):
            """Cancel workflow"""
            success = await self.cancel_workflow(workflow_id)
            return {'success': success}
        
        @self.app.post("/workflows/{workflow_id}/pause")
        async def pause_workflow_endpoint(workflow_id: str):
            """Pause workflow"""
            success = await self.pause_workflow(workflow_id)
            return {'success': success}
        
        @self.app.post("/workflows/{workflow_id}/resume")
        async def resume_workflow_endpoint(workflow_id: str):
            """Resume workflow"""
            success = await self.resume_workflow(workflow_id)
            return {'success': success}
        
        @self.app.get("/templates")
        async def list_templates_endpoint():
            """List available workflow templates"""
            return {
                name: {
                    'name': template.name,
                    'description': template.description,
                    'steps': len(template.step_templates)
                }
                for name, template in self.templates.items()
            }
        
        @self.app.get("/metrics")
        async def metrics_endpoint():
            """Get workflow metrics"""
            return await self.get_metrics()
        
        @self.app.get("/health")
        async def health_endpoint():
            """Health check"""
            return await self.get_health()
    
    async def shutdown(self):
        """Gracefully shutdown workflow coordinator"""
        try:
            logger.info("Shutting down Workflow Coordinator...")
            
            # Cancel background tasks
            if self.executor_task:
                self.executor_task.cancel()
            if self.optimizer_task:
                self.optimizer_task.cancel()
            
            # Cancel active workflows
            for workflow_id in list(self.active_workflows):
                await self.cancel_workflow(workflow_id)
            
            self.is_initialized = False
            logger.info("Workflow Coordinator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during Workflow Coordinator shutdown: {e}")

# Convenience functions
async def create_workflow_coordinator(**kwargs) -> WorkflowCoordinator:
    """Create and initialize a workflow coordinator instance"""
    coordinator = WorkflowCoordinator(**kwargs)
    await coordinator.initialize()
    return coordinator