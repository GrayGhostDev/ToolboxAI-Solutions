#!/usr/bin/env python3
"""
SPARC Framework Example and Integration Demo
===========================================

This script demonstrates the complete SPARC framework integration with
the ToolboxAI Roblox Environment. It shows how to:

1. Initialize the complete SPARC system
2. Execute a full SPARC cycle
3. Integrate with the agent system
4. Handle educational scenarios
5. Monitor and analyze performance

Usage:
    python sparc_example.py [--config config.json] [--demo-scenario scenario_name]
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
import argparse
from pathlib import Path

# Import SPARC framework components
from sparc import (
    SPARCFramework,
    SPARCConfig,
    create_sparc_system,
    create_sparc_config
)
from sparc.state_manager import EnvironmentState, StateType
from sparc.action_executor import Action, ActionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SPARCIntegrationDemo:
    """Demonstrates SPARC framework integration with educational scenarios"""
    
    def __init__(self, config: SPARCConfig):
        self.config = config
        self.sparc_system = None
        
    async def initialize(self):
        """Initialize the SPARC system"""
        logger.info("Initializing SPARC framework...")
        self.sparc_system = create_sparc_system(self.config)
        logger.info("SPARC framework initialized successfully")
    
    async def run_basic_demo(self):
        """Run basic SPARC framework demonstration"""
        logger.info("=== Running Basic SPARC Demo ===")
        
        # Create a sample observation (simulating educational environment)
        observation = {
            'timestamp': datetime.now().isoformat(),
            'source': 'roblox_game',
            'student_id': 'student_123',
            'subject_area': 'mathematics',
            'grade_level': 7,
            'learning_objective': 'fractions_and_decimals',
            
            # Roblox game state
            'game_state': {
                'active_time': 450,  # 7.5 minutes
                'interaction_count': 25,
                'tasks_completed': 3,
                'tasks_attempted': 4,
                'current_difficulty': 0.6,
                'tools_used': ['calculator', 'fraction_blocks', 'visualization']
            },
            
            # Performance indicators
            'quiz_data': {
                'current_score': 0.75,
                'scores': [0.6, 0.7, 0.75],  # Improving trend
                'questions_attempted': 8,
                'questions_correct': 6
            },
            
            # Behavioral data
            'help_requests': 2,
            'failed_attempts': 1,
            'continued_attempts': 2,
            'strategies_attempted': ['visual_approach', 'calculation'],
            'collaboration_type': 'solo'
        }
        
        # Execute SPARC cycle
        logger.info("Executing SPARC cycle...")
        result = await self.sparc_system.execute_cycle(observation)
        
        # Display results
        self._display_cycle_results(result)
        
        return result
    
    async def run_learning_scenario(self, scenario_name: str):
        """Run specific educational learning scenario"""
        scenarios = {
            'struggling_student': self._struggling_student_scenario,
            'advanced_learner': self._advanced_learner_scenario,
            'collaborative_learning': self._collaborative_learning_scenario,
            'creative_project': self._creative_project_scenario
        }
        
        if scenario_name not in scenarios:
            logger.error(f"Unknown scenario: {scenario_name}")
            return
        
        logger.info(f"=== Running {scenario_name.replace('_', ' ').title()} Scenario ===")
        
        scenario_func = scenarios[scenario_name]
        results = await scenario_func()
        
        return results
    
    async def _struggling_student_scenario(self):
        """Scenario: Student struggling with concepts"""
        logger.info("Simulating struggling student scenario...")
        
        # Low performance observation
        observation = {
            'timestamp': datetime.now().isoformat(),
            'source': 'quiz_session',
            'student_id': 'student_struggling',
            'subject_area': 'algebra',
            'grade_level': 8,
            'learning_objective': 'solving_linear_equations',
            
            'quiz_data': {
                'current_score': 0.35,  # Low performance
                'scores': [0.4, 0.3, 0.35],  # Declining/stagnant
                'questions_attempted': 10,
                'questions_correct': 3,
                'time_per_question': 85  # Taking longer than average
            },
            
            'game_state': {
                'active_time': 180,  # Only 3 minutes
                'interaction_count': 8,  # Low interaction
                'help_requests': 4,  # Multiple help requests
                'failed_attempts': 6,
                'continued_attempts': 2  # Low persistence
            },
            
            'error_patterns': ['sign_errors', 'operation_confusion'],
            'engagement_indicators': {
                'attention_span': 0.3,  # Low
                'frustration_level': 0.8  # High
            }
        }
        
        result = await self.sparc_system.execute_cycle(observation)
        
        logger.info("Expected SPARC response for struggling student:")
        logger.info("- Policy should prioritize scaffolding and support")
        logger.info("- Actions should include hints, difficulty reduction")
        logger.info("- Rewards should emphasize effort and small progress")
        
        self._display_cycle_results(result)
        return result
    
    async def _advanced_learner_scenario(self):
        """Scenario: Advanced student needing challenges"""
        logger.info("Simulating advanced learner scenario...")
        
        observation = {
            'timestamp': datetime.now().isoformat(),
            'source': 'roblox_game',
            'student_id': 'student_advanced',
            'subject_area': 'physics',
            'grade_level': 10,
            'learning_objective': 'projectile_motion',
            
            'quiz_data': {
                'current_score': 0.95,  # High performance
                'scores': [0.9, 0.92, 0.95],  # Consistent high performance
                'questions_attempted': 15,
                'questions_correct': 14,
                'time_per_question': 35  # Fast completion
            },
            
            'game_state': {
                'active_time': 720,  # 12 minutes engaged
                'interaction_count': 45,
                'unique_combinations': 8,  # Creative approaches
                'advanced_features_used': ['simulation_mode', 'parameter_tweaking'],
                'self_directed_exploration': True
            },
            
            'creativity_indicators': {
                'original_solutions': 3,
                'novel_approaches': 2,
                'exploration_depth': 0.9
            },
            
            'meta_learning': {
                'strategy_evaluation': True,
                'self_reflection': True,
                'goal_setting': True
            }
        }
        
        result = await self.sparc_system.execute_cycle(observation)
        
        logger.info("Expected SPARC response for advanced learner:")
        logger.info("- Policy should emphasize challenge and creativity")
        logger.info("- Actions should increase difficulty, provide complex problems")
        logger.info("- Rewards should recognize innovation and deep thinking")
        
        self._display_cycle_results(result)
        return result
    
    async def _collaborative_learning_scenario(self):
        """Scenario: Group learning and peer interaction"""
        logger.info("Simulating collaborative learning scenario...")
        
        observation = {
            'timestamp': datetime.now().isoformat(),
            'source': 'roblox_game',
            'student_id': 'student_collab',
            'subject_area': 'engineering',
            'grade_level': 9,
            'learning_objective': 'bridge_design',
            
            'game_state': {
                'active_time': 600,  # 10 minutes
                'interaction_count': 35,
                'collaboration_mode': True,
                'peer_count': 3,
                'shared_workspace': True
            },
            
            'collaboration_data': {
                'messages_sent': 8,
                'messages_received': 12,
                'ideas_contributed': 4,
                'help_provided_to_others': 2,
                'help_received_from_others': 1,
                'group_goals_achieved': 2,
                'total_group_goals': 3
            },
            
            'social_indicators': {
                'leadership_shown': True,
                'communication_quality': 0.8,
                'conflict_resolution': 1,
                'peer_feedback_positive': 0.9
            },
            
            'project_data': {
                'design_iterations': 5,
                'collaborative_decisions': 7,
                'consensus_building': 3
            }
        }
        
        result = await self.sparc_system.execute_cycle(observation)
        
        logger.info("Expected SPARC response for collaborative learning:")
        logger.info("- Policy should emphasize teamwork and communication")
        logger.info("- Actions should facilitate group coordination")
        logger.info("- Rewards should recognize both individual and group contributions")
        
        self._display_cycle_results(result)
        return result
    
    async def _creative_project_scenario(self):
        """Scenario: Creative expression and innovation"""
        logger.info("Simulating creative project scenario...")
        
        observation = {
            'timestamp': datetime.now().isoformat(),
            'source': 'roblox_game',
            'student_id': 'student_creative',
            'subject_area': 'digital_art',
            'grade_level': 6,
            'learning_objective': 'storytelling_through_design',
            
            'game_state': {
                'active_time': 900,  # 15 minutes deeply engaged
                'interaction_count': 60,
                'tools_used': ['brush', 'shapes', 'textures', 'animation', 'lighting'],
                'unique_combinations': 12,
                'experimental_features': 8
            },
            
            'creativity_data': {
                'original_elements': 15,
                'style_variations': 6,
                'narrative_components': 4,
                'aesthetic_choices': 20,
                'iteration_cycles': 8
            },
            
            'expression_indicators': {
                'personal_theme_development': True,
                'emotional_content': 0.8,
                'technical_experimentation': 0.9,
                'artistic_risk_taking': 0.7
            },
            
            'process_data': {
                'planning_time': 120,  # 2 minutes planning
                'creation_time': 600,   # 10 minutes creating
                'reflection_time': 180  # 3 minutes reflecting
            }
        }
        
        result = await self.sparc_system.execute_cycle(observation)
        
        logger.info("Expected SPARC response for creative project:")
        logger.info("- Policy should emphasize exploration and artistic expression")
        logger.info("- Actions should encourage experimentation and reflection")
        logger.info("- Rewards should value creativity, originality, and process")
        
        self._display_cycle_results(result)
        return result
    
    async def run_continuous_learning_simulation(self, duration_minutes: int = 5):
        """Run continuous learning simulation with multiple cycles"""
        logger.info(f"=== Running {duration_minutes}-minute Learning Simulation ===")
        
        student_id = 'student_simulation'
        session_start = datetime.now()
        cycle_count = 0
        performance_history = []
        
        # Simulate learning progression
        base_performance = 0.5
        learning_rate = 0.02
        
        while (datetime.now() - session_start).total_seconds() < duration_minutes * 60:
            cycle_count += 1
            
            # Simulate performance improvement over time
            current_performance = min(1.0, base_performance + (cycle_count * learning_rate))
            performance_history.append(current_performance)
            
            # Create dynamic observation
            observation = {
                'timestamp': datetime.now().isoformat(),
                'source': 'adaptive_learning_system',
                'student_id': student_id,
                'subject_area': 'mathematics',
                'grade_level': 7,
                'learning_objective': 'algebraic_thinking',
                'cycle_number': cycle_count,
                
                'performance_data': {
                    'current_performance': current_performance,
                    'performance_history': performance_history[-10:],  # Last 10 cycles
                    'learning_velocity': learning_rate if cycle_count > 1 else 0
                },
                
                'engagement_data': {
                    'session_duration': (datetime.now() - session_start).total_seconds(),
                    'engagement_level': min(1.0, 0.6 + (current_performance * 0.4)),
                    'attention_span': 0.7 + (current_performance * 0.2)
                },
                
                'adaptive_indicators': {
                    'difficulty_preference': 0.3 + (current_performance * 0.5),
                    'help_seeking_pattern': max(0, 0.3 - (current_performance * 0.2)),
                    'confidence_level': current_performance * 0.8
                }
            }
            
            # Execute SPARC cycle
            result = await self.sparc_system.execute_cycle(observation)
            
            # Log progress periodically
            if cycle_count % 5 == 0:
                logger.info(f"Cycle {cycle_count}: Performance {current_performance:.2f}, "
                          f"Reward {result['rewards']['total_reward']:.2f}")
            
            # Small delay to simulate real-time processing
            await asyncio.sleep(2)  # 2 seconds between cycles
        
        # Final analysis
        logger.info(f"=== Simulation Complete: {cycle_count} cycles ===")
        logger.info(f"Performance improvement: {performance_history[0]:.2f} → {performance_history[-1]:.2f}")
        
        # Get final system status
        final_status = await self.sparc_system.get_framework_status()
        self._display_system_status(final_status)
        
        return {
            'cycles_completed': cycle_count,
            'performance_history': performance_history,
            'final_performance': performance_history[-1] if performance_history else 0,
            'system_status': final_status
        }
    
    def _display_cycle_results(self, result: Dict[str, Any]):
        """Display SPARC cycle results in a readable format"""
        logger.info(f"--- SPARC Cycle {result['cycle_id']} Results ---")
        logger.info(f"Duration: {result['duration']:.3f}s")
        logger.info(f"Success: {result.get('success', True)}")
        
        # State information
        if 'state' in result:
            state = result['state']
            logger.info(f"State: {state.get('state_type', 'unknown')} "
                       f"(quality: {state.get('quality', 'unknown')})")
        
        # Policy decision
        if 'policy_decision' in result:
            policy = result['policy_decision']
            logger.info(f"Policy: {policy.get('action_type', 'unknown')} "
                       f"(confidence: {policy.get('confidence', 0):.2f})")
        
        # Action execution
        if 'action_result' in result:
            action_result = result['action_result']
            logger.info(f"Action: {'Success' if action_result.get('success', False) else 'Failed'}")
        
        # Rewards
        if 'rewards' in result:
            rewards = result['rewards']
            logger.info(f"Reward: {rewards.get('total_reward', 0):.3f}")
            
            # Dimension breakdown
            if 'dimension_breakdown' in rewards:
                logger.info("Reward Dimensions:")
                for dim, value in rewards['dimension_breakdown'].items():
                    logger.info(f"  {dim}: {value:.3f}")
        
        # Performance metrics
        if 'performance' in result:
            perf = result['performance']
            logger.info(f"Success Rate: {perf.get('success_rate', 0):.2f}")
            logger.info(f"Avg Reward: {perf.get('average_reward', 0):.3f}")
            logger.info(f"Learning Progress: {perf.get('learning_progress', 0):.3f}")
        
        logger.info("---")
    
    def _display_system_status(self, status: Dict[str, Any]):
        """Display comprehensive system status"""
        logger.info("=== SPARC System Status ===")
        
        if 'framework' in status:
            fw = status['framework']
            logger.info(f"Cycles: {fw.get('cycle_count', 0)}")
            logger.info(f"Last Cycle Time: {fw.get('last_cycle_time', 0):.3f}s")
        
        # Component statuses
        components = ['state_manager', 'policy_engine', 'action_executor', 
                     'reward_calculator', 'context_tracker']
        
        for component in components:
            if component in status:
                comp_status = status[component]
                logger.info(f"{component.replace('_', ' ').title()}:")
                
                # Show key metrics for each component
                if component == 'state_manager':
                    logger.info(f"  States: {comp_status.get('history_size', 0)}")
                elif component == 'policy_engine':
                    logger.info(f"  Decisions: {comp_status.get('decision_count', 0)}")
                elif component == 'action_executor':
                    logger.info(f"  Actions: {comp_status.get('statistics', {}).get('total_actions', 0)}")
                elif component == 'reward_calculator':
                    logger.info(f"  Calculations: {comp_status.get('calculation_stats', {}).get('total_calculations', 0)}")
                elif component == 'context_tracker':
                    logger.info(f"  Users: {comp_status.get('system_status', {}).get('active_users', 0)}")
        
        logger.info("===")
    
    async def cleanup(self):
        """Cleanup and shutdown SPARC system"""
        if self.sparc_system:
            logger.info("Shutting down SPARC system...")
            await self.sparc_system.reset_framework()
            logger.info("SPARC system shutdown complete")


async def main():
    """Main demo application"""
    parser = argparse.ArgumentParser(description="SPARC Framework Demo")
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--demo-scenario', type=str, 
                       choices=['struggling_student', 'advanced_learner', 
                               'collaborative_learning', 'creative_project'],
                       help='Run specific demo scenario')
    parser.add_argument('--continuous', type=int, default=0,
                       help='Run continuous simulation for N minutes')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        config = create_sparc_config(**config_data)
    else:
        # Use default configuration optimized for educational scenarios
        config = create_sparc_config(
            # State management
            state_history_size=200,
            state_persistence_interval=60.0,
            
            # Policy engine
            policy_learning_rate=0.02,
            policy_exploration_rate=0.15,  # Higher exploration for education
            
            # Action execution
            max_parallel_actions=3,
            action_timeout=45.0,
            
            # Reward calculation
            reward_dimensions=[
                'learning_progress', 'engagement', 'accuracy', 
                'creativity', 'collaboration', 'persistence'
            ],
            reward_normalization=True,
            
            # Context tracking
            context_window_size=100,
            session_timeout=2400.0,  # 40 minutes for educational sessions
            
            # Integration
            real_time_updates=True,
            metrics_enabled=True
        )
    
    # Create and initialize demo
    demo = SPARCIntegrationDemo(config)
    
    try:
        await demo.initialize()
        
        if args.demo_scenario:
            # Run specific scenario
            await demo.run_learning_scenario(args.demo_scenario)
        elif args.continuous:
            # Run continuous simulation
            await demo.run_continuous_learning_simulation(args.continuous)
        else:
            # Run basic demo
            await demo.run_basic_demo()
            
            # Also run a quick scenario demo
            logger.info("\nRunning additional scenario demonstrations...\n")
            for scenario in ['struggling_student', 'advanced_learner']:
                await demo.run_learning_scenario(scenario)
                await asyncio.sleep(1)  # Brief pause between scenarios
    
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())