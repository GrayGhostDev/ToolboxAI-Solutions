#!/usr/bin/env python3
"""Fix all educational agents to use AgentConfig properly."""

import re

# List of agent files to fix and their names
agent_files = [
    ("core/agents/educational/assessment_design_agent.py", "AssessmentDesignAgent"),
    ("core/agents/educational/educational_validation_agent.py", "EducationalValidationAgent"),
    ("core/agents/educational/adaptive_learning_agent.py", "AdaptiveLearningAgent")
]

for file_path, agent_name in agent_files:
    try:
        with open(file_path) as f:
            content = f.read()

        # Pattern to find the old super().__init__ call with named parameters
        pattern = r'super\(\).__init__\([^)]*\)'

        # Find all matches
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            # Replace the old pattern with new AgentConfig pattern
            new_init = f'''config = AgentConfig(
            name="{agent_name}"
        )
        super().__init__(config)'''

            content = re.sub(pattern, new_init, content, count=1)

            with open(file_path, 'w') as f:
                f.write(content)

            print(f"✅ Fixed {file_path}")
        else:
            print(f"⏭️  {file_path} doesn't need fixing or already fixed")

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

print("\nDone! Educational agents should now use AgentConfig properly.")