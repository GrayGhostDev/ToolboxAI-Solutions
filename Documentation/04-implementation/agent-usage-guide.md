# Agent System Usage Guide

## Overview

The ToolboxAI Agent System is a sophisticated multi-agent orchestration framework designed for generating educational content in Roblox environments. This guide provides comprehensive documentation on how to use, configure, and extend the agent system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent Types](#agent-types)
3. [Usage Patterns](#usage-patterns)
4. [Configuration](#configuration)
5. [Examples](#examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                     Orchestrator                         │
│                  (Main Coordination)                     │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │    Supervisor     │
        │  (Task Routing)   │
        └─────────┬─────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┬──────────┐
    ▼             ▼             ▼             ▼          ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│Content │  │  Quiz  │  │Terrain │  │ Script │  │ Review │
│ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

### Supporting Frameworks

- **SPARC Framework**: State-Policy-Action-Reward-Context management
- **Swarm Intelligence**: Parallel task execution and consensus
- **MCP Server**: Model Context Protocol for context management
- **Coordinators**: High-level workflow coordination

## Agent Types

### 1. Content Agent
Generates educational lesson content based on curriculum standards.

```python
from agents.content_agent import ContentAgent

agent = ContentAgent()
result = await agent.generate_lesson({
    "subject": "Science",
    "grade_level": 7,
    "topic": "Photosynthesis",
    "learning_objectives": ["Understand chlorophyll function"]
})
```

### 2. Quiz Agent
Creates interactive quizzes and assessments.

```python
from agents.quiz_agent import QuizAgent

agent = QuizAgent()
quiz = await agent.generate_quiz({
    "subject": "Mathematics",
    "difficulty": "medium",
    "num_questions": 10,
    "question_types": ["multiple_choice", "true_false"]
})
```

### 3. Terrain Agent
Generates 3D terrain and environments in Roblox.

```python
from agents.terrain_agent import TerrainAgent

agent = TerrainAgent()
terrain_script = await agent.generate_terrain({
    "environment_type": "forest",
    "size": "large",
    "features": ["trees", "river", "hills"]
})
```

### 4. Script Agent
Generates Lua scripts for game logic and interactions.

```python
from agents.script_agent import ScriptAgent

agent = ScriptAgent()
scripts = await agent.generate_scripts({
    "script_types": ["game_logic", "ui", "player_controller"],
    "features": ["score_tracking", "timer", "checkpoints"]
})
```

### 5. Review Agent
Reviews and validates generated content for quality and educational value.

```python
from agents.review_agent import ReviewAgent

agent = ReviewAgent()
review = await agent.review_content({
    "content": generated_content,
    "criteria": ["educational_value", "technical_quality", "engagement"]
})
```

## Usage Patterns

### Pattern 1: Simple Content Generation

```python
import asyncio
from agents.orchestrator import Orchestrator

async def generate_simple_lesson():
    orchestrator = Orchestrator()
    
    request = {
        "subject": "Science",
        "grade_level": 6,
        "topic": "Solar System",
        "duration": 45
    }
    
    result = await orchestrator.generate_experience(request)
    return result

# Run
lesson = asyncio.run(generate_simple_lesson())
```

### Pattern 2: Full Educational Experience

```python
async def generate_complete_experience():
    orchestrator = Orchestrator()
    
    request = {
        "subject": "History",
        "grade_level": 8,
        "topic": "Ancient Rome",
        "learning_objectives": [
            "Understand Roman government structure",
            "Learn about daily life in Rome",
            "Explore Roman achievements"
        ],
        "features": {
            "include_quiz": True,
            "include_terrain": True,
            "include_gamification": True,
            "adaptive_difficulty": True
        },
        "environment_type": "ancient_city",
        "duration": 60
    }
    
    result = await orchestrator.generate_experience(request)
    return result
```

### Pattern 3: Parallel Agent Execution

```python
from swarm.swarm_controller import SwarmController

async def parallel_content_generation():
    swarm = SwarmController()
    
    # Define multiple tasks
    tasks = [
        {"type": "content", "data": {"subject": "Math", "topic": "Algebra"}},
        {"type": "quiz", "data": {"num_questions": 20}},
        {"type": "terrain", "data": {"environment": "classroom"}},
        {"type": "script", "data": {"features": ["interaction"]}}
    ]
    
    # Execute in parallel
    results = await swarm.distribute_tasks(tasks)
    return results
```

### Pattern 4: SPARC-Driven Adaptive Learning

```python
from sparc.state_manager import SPARCStateManager

async def adaptive_learning_session():
    sparc = SPARCStateManager()
    
    # Initialize state
    state = {
        "student_performance": 0.75,
        "engagement_level": 0.8,
        "current_difficulty": "medium",
        "topics_covered": ["fractions", "decimals"]
    }
    
    # Execute SPARC cycle
    while not session_complete:
        # Observe current state
        current_state = await sparc.observe_state()
        
        # Decide on action based on policy
        action = sparc.policy.decide(current_state, sparc.context)
        
        # Execute action
        result = await sparc.execute_action(action)
        
        # Calculate reward
        reward = sparc.calculate_reward(result)
        
        # Update policy
        sparc.update_policy(current_state, action, reward)
```

### Pattern 5: Context-Aware Generation with MCP

```python
from mcp.server import MCPServer
from mcp.context_manager import ContextManager

async def context_aware_generation():
    mcp = MCPServer()
    context_manager = ContextManager()
    
    # Set up context
    context = {
        "user": {"id": "student123", "grade": 7, "preferences": {}},
        "session": {"id": "session456", "start_time": "2025-09-07T10:00:00"},
        "history": ["previous_lessons"],
        "performance": {"average_score": 85, "weak_areas": ["geometry"]}
    }
    
    # Update context
    mcp.update_context(context)
    
    # Generate with context awareness
    orchestrator = Orchestrator()
    result = await orchestrator.generate_with_context(
        request={"subject": "Math"},
        context=context
    )
    
    return result
```

## Configuration

### Environment Variables

```bash
# AI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Agent Configuration
ENABLE_CONTENT_GENERATION=true
ENABLE_QUIZ_GENERATION=true
ENABLE_TERRAIN_GENERATION=true
ENABLE_SCRIPT_GENERATION=true

# SPARC Configuration
ENABLE_SPARC_FRAMEWORK=true
SPARC_POLICY_TYPE=adaptive
SPARC_REWARD_FUNCTION=educational_value

# Swarm Configuration
ENABLE_SWARM_INTELLIGENCE=true
SWARM_WORKER_COUNT=5
SWARM_CONSENSUS_THRESHOLD=0.8

# MCP Configuration
ENABLE_MCP_PROTOCOL=true
MCP_PORT=9876
MCP_MEMORY_LIMIT=128000
```

### Agent Configuration File

```python
# config/agents.py

AGENT_CONFIG = {
    "content_agent": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "top_p": 0.9,
        "retry_attempts": 3
    },
    "quiz_agent": {
        "default_questions": 10,
        "difficulty_levels": ["easy", "medium", "hard"],
        "question_types": ["multiple_choice", "true_false", "short_answer"]
    },
    "terrain_agent": {
        "max_terrain_size": 1000,
        "environment_types": ["classroom", "outdoor", "laboratory", "fantasy"],
        "detail_level": "high"
    },
    "script_agent": {
        "max_script_length": 5000,
        "optimization_level": "balanced",
        "security_checks": True
    },
    "review_agent": {
        "criteria": ["educational_value", "technical_quality", "engagement"],
        "min_quality_score": 70,
        "require_approval": True
    }
}
```

## Examples

### Example 1: Mathematics Lesson with Quiz

```python
import asyncio
from agents.orchestrator import Orchestrator

async def create_math_lesson():
    orchestrator = Orchestrator()
    
    result = await orchestrator.generate_experience({
        "subject": "Mathematics",
        "grade_level": 5,
        "topic": "Fractions",
        "learning_objectives": [
            "Add and subtract fractions",
            "Convert between mixed numbers and improper fractions",
            "Solve word problems with fractions"
        ],
        "include_quiz": True,
        "quiz_config": {
            "num_questions": 15,
            "difficulty": "progressive",  # Starts easy, gets harder
            "include_explanations": True
        },
        "environment_type": "classroom",
        "interactive_elements": ["fraction_manipulatives", "number_line"]
    })
    
    print(f"Lesson Title: {result['lesson']['title']}")
    print(f"Quiz Questions: {len(result['quiz']['questions'])}")
    print(f"Quality Score: {result['review']['quality_score']}")
    
    return result

# Execute
lesson = asyncio.run(create_math_lesson())
```

### Example 2: Science Lab with 3D Environment

```python
async def create_science_lab():
    orchestrator = Orchestrator()
    
    result = await orchestrator.generate_experience({
        "subject": "Science",
        "grade_level": 8,
        "topic": "Chemical Reactions",
        "learning_objectives": [
            "Identify types of chemical reactions",
            "Balance chemical equations",
            "Predict reaction products"
        ],
        "environment_type": "laboratory",
        "terrain_config": {
            "include_equipment": ["beakers", "bunsen_burners", "periodic_table"],
            "interactive_experiments": True,
            "safety_features": True
        },
        "include_simulation": True,
        "gamification": {
            "points_system": True,
            "achievements": ["Safety First", "Master Chemist", "Equation Balancer"],
            "leaderboard": True
        }
    })
    
    return result
```

### Example 3: History Experience with Storytelling

```python
async def create_history_experience():
    orchestrator = Orchestrator()
    
    result = await orchestrator.generate_experience({
        "subject": "History",
        "grade_level": 7,
        "topic": "American Revolution",
        "narrative_style": "immersive_storytelling",
        "characters": ["historical_figures", "common_people"],
        "environment_type": "historical_setting",
        "terrain_config": {
            "locations": ["Boston", "Philadelphia", "Valley Forge"],
            "time_period_accurate": True,
            "interactive_timeline": True
        },
        "activities": [
            "decision_making_scenarios",
            "historical_debates",
            "artifact_collection"
        ],
        "assessment_type": "project_based"
    })
    
    return result
```

## Best Practices

### 1. Error Handling

```python
async def safe_content_generation():
    orchestrator = Orchestrator()
    
    try:
        result = await orchestrator.generate_experience(request)
        
        if result['review']['quality_score'] < 70:
            # Regenerate if quality is too low
            result = await orchestrator.regenerate_with_improvements(result)
        
        return result
        
    except ContentGenerationError as e:
        logger.error(f"Content generation failed: {e}")
        # Fallback to simpler generation
        return await orchestrator.generate_simple_content(request)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Return safe default content
        return get_default_content(request)
```

### 2. Performance Optimization

```python
# Use caching for frequently requested content
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_content(subject, topic, grade_level):
    return await orchestrator.generate_experience({
        "subject": subject,
        "topic": topic,
        "grade_level": grade_level
    })

# Batch processing for multiple requests
async def batch_generate(requests):
    swarm = SwarmController()
    tasks = [{"type": "generate", "data": req} for req in requests]
    results = await swarm.distribute_tasks(tasks)
    return results
```

### 3. Context Management

```python
class SessionManager:
    def __init__(self):
        self.mcp = MCPServer()
        self.contexts = {}
    
    async def create_session(self, user_id):
        context = {
            "user_id": user_id,
            "session_id": generate_session_id(),
            "start_time": datetime.now(),
            "history": []
        }
        self.contexts[user_id] = context
        self.mcp.update_context(context)
        return context
    
    async def update_session(self, user_id, data):
        if user_id in self.contexts:
            self.contexts[user_id].update(data)
            self.mcp.update_context(self.contexts[user_id])
```

### 4. Quality Assurance

```python
async def ensure_quality(content):
    review_agent = ReviewAgent()
    
    # Multi-stage review process
    reviews = await asyncio.gather(
        review_agent.check_educational_value(content),
        review_agent.check_technical_quality(content),
        review_agent.check_age_appropriateness(content),
        review_agent.check_accessibility(content)
    )
    
    # Aggregate scores
    total_score = sum(r['score'] for r in reviews) / len(reviews)
    
    if total_score < 80:
        # Get improvement suggestions
        suggestions = review_agent.get_improvement_suggestions(content, reviews)
        # Apply improvements
        content = await apply_improvements(content, suggestions)
    
    return content
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Agent Timeout

**Problem**: Agent takes too long to respond
```python
TimeoutError: Agent response exceeded 30 seconds
```

**Solution**:
```python
# Increase timeout
orchestrator = Orchestrator(timeout=60)

# Or use async timeout
import asyncio
async with asyncio.timeout(45):
    result = await orchestrator.generate_experience(request)
```

#### 2. Context Overflow

**Problem**: Context exceeds token limit
```python
ContextOverflowError: Context exceeds 128K token limit
```

**Solution**:
```python
# Prune context before processing
mcp.prune_context(max_tokens=100000)

# Or use sliding window
context_manager.use_sliding_window(window_size=50000)
```

#### 3. Agent Coordination Failure

**Problem**: Agents fail to coordinate properly
```python
CoordinationError: Agent consensus not reached
```

**Solution**:
```python
# Increase consensus attempts
swarm.consensus_engine.max_attempts = 5

# Or lower consensus threshold
swarm.consensus_engine.threshold = 0.7  # From 0.8
```

#### 4. Quality Score Too Low

**Problem**: Generated content fails quality checks
```python
QualityError: Content quality score 65 below threshold 70
```

**Solution**:
```python
# Enable iterative improvement
orchestrator.enable_iterative_improvement = True
orchestrator.max_improvement_iterations = 3

# Or adjust generation parameters
agent.temperature = 0.6  # Lower for more focused content
agent.top_p = 0.85  # Narrower token selection
```

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('agents')

# Enable debug in agents
orchestrator = Orchestrator(debug=True)
orchestrator.set_log_level(logging.DEBUG)

# Trace agent execution
with orchestrator.trace_execution():
    result = await orchestrator.generate_experience(request)
    # Execution trace will be logged
```

### Performance Monitoring

```python
from monitoring import AgentMonitor

monitor = AgentMonitor()

# Track metrics
with monitor.track_execution():
    result = await orchestrator.generate_experience(request)

# Get metrics
metrics = monitor.get_metrics()
print(f"Execution time: {metrics['execution_time']}s")
print(f"Token usage: {metrics['tokens_used']}")
print(f"API calls: {metrics['api_calls']}")
print(f"Cache hits: {metrics['cache_hits']}")
```

## Advanced Topics

### Custom Agent Development

```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    """Custom agent for specialized tasks."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.specialized_tool = self.load_tool()
    
    async def process(self, request):
        """Process custom request."""
        # Implement custom logic
        result = await self.specialized_tool.execute(request)
        return self.format_response(result)
    
    def load_tool(self):
        """Load specialized tool."""
        # Load custom tool
        return CustomTool()
```

### Agent Communication Protocol

```python
class AgentProtocol:
    """Standard protocol for agent communication."""
    
    @staticmethod
    def create_message(sender, receiver, content, priority="normal"):
        return {
            "id": generate_id(),
            "sender": sender,
            "receiver": receiver,
            "content": content,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def validate_message(message):
        required_fields = ["id", "sender", "receiver", "content"]
        return all(field in message for field in required_fields)
```

### Integration with External Systems

```python
class LMSIntegration:
    """Integration with Learning Management Systems."""
    
    async def sync_with_schoology(self, content):
        """Sync generated content with Schoology."""
        # Implementation
        pass
    
    async def sync_with_canvas(self, content):
        """Sync generated content with Canvas."""
        # Implementation
        pass
    
    async def export_to_scorm(self, content):
        """Export content as SCORM package."""
        # Implementation
        pass
```

## Claude Code Custom Agents

In addition to the ToolboxAI Agent System, we have implemented specialized Claude Code agents for development and maintenance tasks. These agents are located in `.claude/agents/` and can be invoked using the Task tool.

### Available Claude Code Agents

#### 1. code-reviewer
Reviews code for quality, best practices, security issues, and suggests improvements.

#### 2. test-runner  
Executes tests, analyzes coverage, generates reports, and creates new test cases. Uses the `venv_clean` environment.

#### 3. dependency-analyzer
Manages dependencies, checks for vulnerabilities, and resolves conflicts. Always uses the `venv_clean` environment.

#### 4. roblox-lua-validator
Validates Roblox Lua scripts for security issues, memory leaks, and performance optimization.

#### 5. api-endpoint-generator
Creates FastAPI endpoints with full documentation, Pydantic models, and authentication.

#### 6. documentation-generator
Generates comprehensive documentation including API docs, README files, and docstrings.

#### 7. ai-agent-builder
Creates LangChain/LangGraph agents and implements the SPARC framework.

#### 8. database-migrator
Manages PostgreSQL migrations, schema updates, and backup/restore operations.

### Using Claude Code Agents

To invoke a Claude Code agent:

```python
Task(
    description="Review code quality",
    prompt="Review the latest API endpoints for security and best practices",
    subagent_type="code-reviewer"
)
```

These agents complement the main ToolboxAI Agent System by providing specialized development support.

## Conclusion

The ToolboxAI Agent System, combined with Claude Code custom agents, provides a comprehensive framework for both educational content generation and development tasks. By following the patterns and best practices outlined in this guide, you can effectively leverage both systems to create engaging educational experiences while maintaining high code quality.

For additional support and updates, refer to:
- [API Documentation](/Documentation/03-api/)
- [Architecture Guide](/Documentation/02-architecture/)
- [SDK Documentation](/Documentation/11-sdks/)
- [Claude Code Agents](/.claude/agents/)

---

*Last Updated: 2025-09-07*
*Version: 1.1.0*