"""
Coordinator System Integration Example

Demonstrates how to use the comprehensive coordinator system for
educational content generation in the ToolboxAI Roblox Environment.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def example_educational_content_generation():
    """
    Example: Complete educational content generation workflow
    """
    try:
        # Import coordinator system
        from . import initialize_coordinators, get_coordinator_system
        
        # Configuration for the coordinator system
        config = {
            'main': {
                'max_concurrent_requests': 5,
                'enable_caching': True
            },
            'workflow': {
                'max_concurrent_workflows': 3
            },
            'resource': {
                'max_cpu_allocation': 0.8,
                'max_memory_allocation': 0.7,
                'enable_cost_tracking': True,
                'daily_budget': 50.0
            },
            'sync': {
                'sync_interval': 5,
                'enable_conflict_resolution': True
            },
            'error': {
                'enable_auto_recovery': True,
                'enable_notifications': False  # Disable for example
            }
        }
        
        # Initialize coordinator system
        logger.info("Initializing coordinator system...")
        coordinator_system = await initialize_coordinators(config)
        
        # Get individual coordinators
        main_coordinator = coordinator_system.get_main_coordinator()
        workflow_coordinator = coordinator_system.get_workflow_coordinator()
        resource_coordinator = coordinator_system.get_resource_coordinator()
        sync_coordinator = coordinator_system.get_sync_coordinator()
        error_coordinator = coordinator_system.get_error_coordinator()
        
        logger.info("Coordinator system initialized successfully")
        
        # Check system health
        health = await main_coordinator.get_health_status()
        logger.info(f"System health: {health.status}")
        
        # Example 1: Generate educational content for Mathematics
        logger.info("=== Example 1: Mathematics Content Generation ===")
        
        math_result = await main_coordinator.generate_educational_content(
            subject="Mathematics",
            grade_level=7,
            learning_objectives=["Fractions", "Decimals", "Percentages"],
            environment_type="interactive_classroom",
            include_quiz=True,
            custom_parameters={
                'difficulty_level': 'intermediate',
                'include_visual_aids': True,
                'gamification_level': 'high'
            }
        )
        
        logger.info(f"Mathematics content generated: {math_result.success}")
        logger.info(f"Generation time: {math_result.generation_time:.2f} seconds")
        logger.info(f"Scripts generated: {len(math_result.scripts)}")
        
        # Example 2: Create a complete course workflow
        logger.info("=== Example 2: Complete Course Generation ===")
        
        course_workflow_id = await workflow_coordinator.create_workflow(
            workflow_type="complete_course_generation",
            parameters={
                'subject': 'Science',
                'grade_level': 6,
                'course_title': 'Solar System Explorer',
                'number_of_lessons': 8,
                'assessment_frequency': 'per_lesson',
                'environment_themes': ['space_station', 'planet_surface', 'asteroid_field']
            },
            priority=3
        )
        
        logger.info(f"Course workflow created: {course_workflow_id}")
        
        # Monitor workflow progress
        for i in range(10):  # Check for up to 10 iterations
            status = await workflow_coordinator.get_workflow_status(course_workflow_id)
            logger.info(f"Course workflow progress: {status['progress']:.1f}%")
            
            if status['status'] in ['completed', 'failed']:
                break
            
            await asyncio.sleep(5)  # Wait 5 seconds between checks
        
        # Example 3: Resource management demonstration
        logger.info("=== Example 3: Resource Management ===")
        
        # Allocate resources for a large content generation task
        allocation = await resource_coordinator.allocate_resources(
            request_id="large_content_task",
            requirements={
                'cpu_cores': 4,
                'memory_mb': 2048,
                'gpu_memory_mb': 1024,
                'api_quota': 500,
                'token_limit': 50000
            }
        )
        
        logger.info(f"Resources allocated: {allocation.cpu_cores} cores, {allocation.memory_mb}MB memory")
        
        # Check API quota
        openai_quota_available = await resource_coordinator.check_api_quota(
            service='openai',
            request_count=10,
            token_count=5000
        )
        
        logger.info(f"OpenAI quota available: {openai_quota_available}")
        
        # Consume some quota
        if openai_quota_available:
            await resource_coordinator.consume_api_quota(
                service='openai',
                request_count=5,
                token_count=2500,
                request_id="large_content_task"
            )
        
        # Get resource status
        resource_status = await resource_coordinator.get_resource_status()
        logger.info(f"Current resource utilization: CPU {resource_status['utilization']['cpu_utilization']:.1f}%")
        
        # Release resources
        await resource_coordinator.release_resources("large_content_task")
        
        # Example 4: State synchronization
        logger.info("=== Example 4: State Synchronization ===")
        
        # Register a component for synchronization
        await sync_coordinator.register_component(
            component_id='example_component',
            initial_state={
                'status': 'active',
                'last_activity': datetime.now().isoformat(),
                'configuration': {
                    'mode': 'educational',
                    'difficulty': 'intermediate'
                }
            }
        )
        
        # Update component state
        updated_state = await sync_coordinator.update_component_state(
            component_id='example_component',
            state_data={
                'status': 'processing',
                'last_activity': datetime.now().isoformat(),
                'current_task': 'content_generation',
                'configuration': {
                    'mode': 'educational',
                    'difficulty': 'advanced'  # Changed difficulty
                }
            }
        )
        
        logger.info(f"Component state updated to version {updated_state.version}")
        
        # Publish an event
        event_id = await sync_coordinator.publish_event(
            event_type='content_generation_started',
            source='example_component',
            data={
                'task_id': 'example_task',
                'estimated_duration': 300,
                'complexity': 'high'
            }
        )
        
        logger.info(f"Event published: {event_id}")
        
        # Example 5: Error handling and recovery
        logger.info("=== Example 5: Error Handling ===")
        
        # Simulate a recoverable error
        try:
            # Simulate a connection error
            raise ConnectionError("Simulated database connection lost")
        except Exception as e:
            error_id = await error_coordinator.handle_error(
                error_type="connection_error",
                error=e,
                context={
                    'database_host': 'localhost',
                    'operation': 'fetch_user_data',
                    'retry_count': 0
                },
                component="database_service",
                severity=error_coordinator.ErrorSeverity.WARNING
            )
            
            logger.info(f"Error handled: {error_id}")
        
        # Simulate a critical error
        try:
            raise RuntimeError("Critical system component failed")
        except Exception as e:
            error_id = await error_coordinator.handle_error(
                error_type="system_failure",
                error=e,
                context={'system_component': 'main_processor'},
                component="core_system",
                severity=error_coordinator.ErrorSeverity.CRITICAL
            )
            
            logger.info(f"Critical error handled: {error_id}")
        
        # Get error summary
        error_summary = await error_coordinator.get_error_summary(1)  # Last hour
        logger.info(f"Errors in last hour: {error_summary['total_errors']}")
        
        # Example 6: System metrics and monitoring
        logger.info("=== Example 6: System Monitoring ===")
        
        # Get comprehensive system metrics
        main_metrics = await main_coordinator.get_health_status()
        workflow_metrics = await workflow_coordinator.get_metrics()
        resource_metrics = await resource_coordinator.get_metrics()
        sync_metrics = await sync_coordinator.get_metrics()
        error_metrics = await error_coordinator.get_metrics()
        
        logger.info("=== System Metrics Summary ===")
        logger.info(f"Overall system health: {main_metrics.status}")
        logger.info(f"Active workflows: {workflow_metrics['active_workflows']}")
        logger.info(f"Resource utilization: {resource_metrics['utilization']}")
        logger.info(f"Sync health: {sync_metrics['sync_status']['sync_health']:.1f}%")
        logger.info(f"Error resolution rate: {error_metrics['error_summary']['resolution_rate']:.1f}%")
        
        # Example 7: Advanced workflow with resource constraints
        logger.info("=== Example 7: Advanced Multi-Subject Workflow ===")
        
        # Create adaptive assessment workflow
        assessment_workflow_id = await workflow_coordinator.create_workflow(
            workflow_type="adaptive_assessment_generation",
            parameters={
                'subjects': ['Mathematics', 'Science', 'English'],
                'grade_level': 8,
                'student_profiles': [
                    {'student_id': 'student_1', 'performance_level': 'high'},
                    {'student_id': 'student_2', 'performance_level': 'medium'},
                    {'student_id': 'student_3', 'performance_level': 'low'}
                ],
                'assessment_type': 'formative',
                'adaptive_difficulty': True
            },
            priority=4
        )
        
        logger.info(f"Adaptive assessment workflow created: {assessment_workflow_id}")
        
        # Wait for workflow completion
        while True:
            status = await workflow_coordinator.get_workflow_status(assessment_workflow_id)
            logger.info(f"Assessment workflow: {status['status']} ({status['progress']:.1f}%)")
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            await asyncio.sleep(3)
        
        # Example 8: Cleanup and shutdown
        logger.info("=== Example 8: System Shutdown ===")
        
        # Get final system status
        final_health = await main_coordinator.get_health_status()
        logger.info(f"Final system health: {final_health.status}")
        
        # Graceful shutdown
        await coordinator_system.shutdown()
        logger.info("Coordinator system shutdown complete")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        raise

async def example_real_time_collaboration():
    """
    Example: Real-time collaboration scenario
    """
    logger.info("=== Real-time Collaboration Example ===")
    
    try:
        from . import coordinator_context
        
        # Use context manager for automatic cleanup
        async with coordinator_context() as coordinator_system:
            sync_coordinator = coordinator_system.get_sync_coordinator()
            
            # Simulate multiple components collaborating
            components = ['teacher_dashboard', 'student_client', 'roblox_studio']
            
            # Register all components
            for component in components:
                await sync_coordinator.register_component(
                    component_id=component,
                    initial_state={
                        'status': 'connected',
                        'user_count': 1 if component == 'teacher_dashboard' else 25,
                        'active_session': str(uuid.uuid4())
                    }
                )
            
            # Simulate real-time state updates
            for i in range(5):
                # Teacher updates lesson content
                await sync_coordinator.update_component_state(
                    component_id='teacher_dashboard',
                    state_data={
                        'status': 'editing',
                        'current_lesson': f'lesson_{i+1}',
                        'edit_timestamp': datetime.now().isoformat()
                    }
                )
                
                # Students receive updates
                await sync_coordinator.publish_event(
                    event_type='lesson_content_updated',
                    source='teacher_dashboard',
                    target='student_client',
                    data={
                        'lesson_id': f'lesson_{i+1}',
                        'content_version': i+1,
                        'requires_reload': True
                    }
                )
                
                # Roblox Studio updates environment
                await sync_coordinator.update_component_state(
                    component_id='roblox_studio',
                    state_data={
                        'status': 'updating_environment',
                        'lesson_id': f'lesson_{i+1}',
                        'environment_ready': True
                    }
                )
                
                await asyncio.sleep(2)  # Simulate real-time updates
            
            # Get synchronization status
            sync_status = await sync_coordinator.get_sync_status()
            logger.info(f"Collaboration sync health: {sync_status['sync_health']:.1f}%")
            
    except Exception as e:
        logger.error(f"Real-time collaboration example failed: {e}")

async def example_error_recovery_scenarios():
    """
    Example: Error recovery scenarios
    """
    logger.info("=== Error Recovery Scenarios Example ===")
    
    try:
        from . import create_error_coordinator
        
        error_coordinator = await create_error_coordinator()
        
        # Scenario 1: API rate limit error (should auto-recover)
        try:
            raise Exception("Rate limit exceeded for OpenAI API")
        except Exception as e:
            await error_coordinator.handle_error(
                error_type="rate_limit",
                error=e,
                context={
                    'api_service': 'openai',
                    'requests_made': 500,
                    'quota_limit': 400
                },
                component="api_client"
            )
        
        # Scenario 2: Memory exhaustion (should trigger cleanup)
        try:
            raise MemoryError("System running out of memory")
        except Exception as e:
            await error_coordinator.handle_error(
                error_type="memory_error",
                error=e,
                context={
                    'memory_usage': '95%',
                    'available_memory': '512MB'
                },
                component="content_generator",
                severity=error_coordinator.ErrorSeverity.ERROR
            )
        
        # Scenario 3: Data corruption (should trigger rollback)
        try:
            raise Exception("State corruption detected")
        except Exception as e:
            await error_coordinator.handle_error(
                error_type="data_corruption",
                error=e,
                context={
                    'corrupted_component': 'user_progress',
                    'last_good_backup': '2024-01-15T10:30:00'
                },
                component="data_store",
                severity=error_coordinator.ErrorSeverity.CRITICAL
            )
        
        # Wait for recovery attempts
        await asyncio.sleep(10)
        
        # Check recovery status
        error_summary = await error_coordinator.get_error_summary(1)
        logger.info(f"Error recovery results: {error_summary['resolution_rate']:.1f}% resolved")
        
        await error_coordinator.shutdown()
        
    except Exception as e:
        logger.error(f"Error recovery example failed: {e}")

async def example_performance_optimization():
    """
    Example: Performance optimization workflow
    """
    logger.info("=== Performance Optimization Example ===")
    
    try:
        from . import create_resource_coordinator, create_workflow_coordinator
        
        # Create coordinators
        resource_coordinator = await create_resource_coordinator()
        workflow_coordinator = await create_workflow_coordinator()
        
        # Simulate high-load scenario
        concurrent_tasks = []
        
        for i in range(3):
            # Create resource-intensive workflow
            workflow_id = await workflow_coordinator.create_workflow(
                workflow_type="educational_content_generation",
                parameters={
                    'subject': f'Subject_{i+1}',
                    'grade_level': 5 + i,
                    'complexity': 'high',
                    'parallel_processing': True
                },
                priority=2
            )
            
            concurrent_tasks.append(workflow_id)
        
        logger.info(f"Created {len(concurrent_tasks)} concurrent workflows")
        
        # Monitor resource utilization
        for i in range(12):  # Monitor for 1 minute
            utilization = await resource_coordinator.get_utilization()
            logger.info(f"Resource utilization - CPU: {utilization['cpu_utilization']:.1f}%, "
                       f"Memory: {utilization['memory_utilization']:.1f}%")
            
            await asyncio.sleep(5)
        
        # Get optimization recommendations
        optimization = await resource_coordinator.optimize_resource_allocation()
        logger.info(f"Optimization recommendations: {len(optimization['recommendations'])}")
        for rec in optimization['recommendations']:
            logger.info(f"  - {rec}")
        
        # Wait for workflows to complete
        for workflow_id in concurrent_tasks:
            status = await workflow_coordinator.get_workflow_status(workflow_id)
            logger.info(f"Workflow {workflow_id}: {status['status']}")
        
        await resource_coordinator.shutdown()
        await workflow_coordinator.shutdown()
        
    except Exception as e:
        logger.error(f"Performance optimization example failed: {e}")

async def example_educational_scenarios():
    """
    Example: Educational-specific scenarios
    """
    logger.info("=== Educational Scenarios Example ===")
    
    try:
        from . import generate_educational_content, create_learning_workflow
        
        # Scenario 1: Elementary science lesson
        logger.info("Generating elementary science content...")
        
        science_content = await generate_educational_content(
            subject="Science",
            grade_level=3,
            learning_objectives=["Animal habitats", "Food chains", "Ecosystems"],
            environment_type="natural_habitat",
            include_quiz=True
        )
        
        if science_content.success:
            logger.info(f"Science content generated with {len(science_content.scripts)} scripts")
            logger.info(f"Complexity score: {science_content.metrics['complexity_score']}")
            logger.info(f"Quality score: {science_content.metrics['quality_score']}")
        
        # Scenario 2: High school mathematics
        logger.info("Generating high school mathematics content...")
        
        math_content = await generate_educational_content(
            subject="Mathematics",
            grade_level=11,
            learning_objectives=["Calculus basics", "Derivatives", "Integration"],
            environment_type="virtual_laboratory",
            include_quiz=True
        )
        
        if math_content.success:
            logger.info(f"Mathematics content generated with {len(math_content.scripts)} scripts")
        
        # Scenario 3: Interactive history lesson
        logger.info("Creating interactive history workflow...")
        
        history_workflow = await create_learning_workflow(
            workflow_type="educational_content_generation",
            parameters={
                'subject': 'History',
                'grade_level': 9,
                'learning_objectives': ['World War II', 'Historical timeline', 'Cause and effect'],
                'environment_type': 'historical_recreation',
                'interaction_level': 'high',
                'include_virtual_artifacts': True
            }
        )
        
        logger.info(f"History workflow created: {history_workflow}")
        
        # Check system health after content generation
        system_health = await monitor_system_health()
        logger.info(f"System health after content generation: {system_health['status']}")
        
    except Exception as e:
        logger.error(f"Educational scenarios example failed: {e}")

def run_example():
    """Run the coordinator system example"""
    async def main():
        logger.info("Starting ToolboxAI Coordinator System Example")
        logger.info("=" * 60)
        
        try:
            # Run all examples
            await example_educational_content_generation()
            await asyncio.sleep(2)
            
            await example_real_time_collaboration()
            await asyncio.sleep(2)
            
            await example_error_recovery_scenarios()
            await asyncio.sleep(2)
            
            await example_performance_optimization()
            await asyncio.sleep(2)
            
            await example_educational_scenarios()
            
            logger.info("=" * 60)
            logger.info("All examples completed successfully!")
            
        except Exception as e:
            logger.error(f"Example execution failed: {e}")
            raise
    
    # Run the async main function
    asyncio.run(main())

if __name__ == "__main__":
    run_example()