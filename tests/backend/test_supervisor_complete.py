"""
Test CompleteSupervisorAgent with real OpenAI API
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the path to the system
import sys

sys.path.insert(0, "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

from core.agents.base_agent import AgentConfig
from core.agents.supervisor_complete import CompleteSupervisorAgent


@pytest.mark.asyncio
async def test_real_openai():
    """Test with real OpenAI API"""
    print("\n=== Testing CompleteSupervisorAgent with Real OpenAI API ===\n")

    # Verify API key exists
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment!")
        return

    print(f"✓ OpenAI API Key found: {api_key[:8]}...{api_key[-4:]}")

    # Create agent with real config
    config = AgentConfig(
        name="CompleteSupervisor",
        model="gpt-4o",
        temperature=0.7,
        max_retries=3,
        timeout=120,
        verbose=True,
        memory_enabled=True,
        max_context_length=128000,
    )

    try:
        print("\n1. Initializing CompleteSupervisorAgent...")
        agent = CompleteSupervisorAgent(config)
        print("✓ Agent initialized successfully")

        # Test task
        task = (
            "Create an educational game about basic geometry for middle school students with a quiz"
        )
        context = {
            "grade_level": "middle_school",
            "subject": "mathematics",
            "topic": "basic_geometry",
            "learning_objectives": [
                "Understand shapes and their properties",
                "Calculate area and perimeter",
                "Identify geometric patterns",
            ],
        }

        print(f"\n2. Submitting task: {task[:100]}...")
        print(f"   Context: {context}")

        # Execute with real API
        result = await agent.execute(task, context)

        print("\n3. Task completed!")
        print(f"   Success: {result.success}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Tokens used: {result.tokens_used}")

        if result.success:
            print("\n4. Result Output:")
            if isinstance(result.output, dict):
                for key, value in result.output.items():
                    if isinstance(value, str):
                        preview = value[:200] + "..." if len(value) > 200 else value
                    elif isinstance(value, list):
                        preview = f"List with {len(value)} items"
                    elif isinstance(value, dict):
                        preview = f"Dict with {len(value)} keys"
                    else:
                        preview = str(value)[:200]
                    print(f"   - {key}: {preview}")
            else:
                print(f"   {str(result.output)[:500]}")

            if result.metadata:
                print("\n5. Metadata:")
                for key, value in result.metadata.items():
                    print(f"   - {key}: {value}")
        else:
            print(f"\n4. Error: {result.error}")

        # Check agent stats
        print("\n6. Agent Statistics:")
        print(f"   - Total agents: {len(agent.managed_agents)}")
        print(f"   - Agent types: {list(agent.managed_agents.keys())}")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_openai())
