#!/usr/bin/env python3
"""Fix all educational agents imports to include AgentConfig."""

import re

# List of agent files to fix
agent_files = [
    "core/agents/educational/learning_analytics_agent.py",
    "core/agents/educational/assessment_design_agent.py",
    "core/agents/educational/educational_validation_agent.py",
    "core/agents/educational/adaptive_learning_agent.py"
]

for file_path in agent_files:
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check if AgentConfig is already imported
        if "from core.agents.base_agent import" in content and "AgentConfig" not in content:
            # Find the existing import and add AgentConfig
            content = re.sub(
                r'from core\.agents\.base_agent import (.+)',
                r'from core.agents.base_agent import \1, AgentConfig',
                content
            )

            with open(file_path, 'w') as f:
                f.write(content)

            print(f"✅ Fixed imports in {file_path}")
        elif "AgentConfig" in content:
            print(f"⏭️  {file_path} already has AgentConfig imported")
        else:
            print(f"❓ {file_path} - couldn't find base_agent import")

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

print("\nDone! All educational agents should now import AgentConfig.")