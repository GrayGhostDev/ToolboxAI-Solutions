#!/usr/bin/env python3
"""Test script to debug swarm endpoint error."""

import sys
import traceback

sys.path.insert(0, "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

try:
    from core.swarm.orchestration_controller import OrchestrationController

    # Try to instantiate the controller
    controller = OrchestrationController()
    print("✅ OrchestrationController instantiated successfully")

    # Check if it has required attributes
    print(f"Sessions: {len(controller.sessions)}")
    print(
        f"Agents: {list(controller.agents.keys()) if hasattr(controller, 'agents') else 'No agents attribute'}"
    )
    print(
        f"Metrics: {controller.metrics if hasattr(controller, 'metrics') else 'No metrics attribute'}"
    )

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
