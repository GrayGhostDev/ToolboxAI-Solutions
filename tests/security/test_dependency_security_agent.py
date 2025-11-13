
#!/usr/bin/env python3
"""
Test script for DependencySecurityAgent
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.agents.github_agents import DependencySecurityAgent


@pytest.mark.asyncio
async def test_dependency_security_agent():
    """Test the DependencySecurityAgent functionality."""
    print("🔍 Testing DependencySecurityAgent...")

    # Initialize the agent
    agent = DependencySecurityAgent()

    # Test environment validation
    print("\n📋 Validating environment...")
    validation = await agent.validate_environment()
    for check, result in validation.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}: {result}")

    # Test analysis on current repository
    print("\n🔎 Running dependency security analysis...")
    result = await agent.analyze(
        scan_python=True, scan_nodejs=True, check_licenses=True, repo_path=str(project_root)
    )

    if result["success"]:
        print("✅ Analysis completed successfully!")

        summary = result["summary"]
        print(f"\n📊 Summary:")
        print(f"  • Total vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"  • Critical vulnerabilities: {summary['critical_vulnerabilities']}")
        print(f"  • High vulnerabilities: {summary['high_vulnerabilities']}")
        print(f"  • Outdated packages: {summary['outdated_packages']}")
        print(f"  • License issues: {summary['license_issues']}")
        print(f"  • Risk score: {summary['risk_score']}/100")

        # Show some recommendations
        report = result["report"]
        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["recommendations"][:5]:  # Show first 5
                print(f"  • {rec}")

        # Show files scanned
        python_files = report["python_analysis"].get("files_scanned", [])
        nodejs_files = report["nodejs_analysis"].get("files_scanned", [])

        if python_files:
            print(f"\n🐍 Python files scanned ({len(python_files)}):")
            for file in python_files[:3]:  # Show first 3
                print(f"  • {file}")

        if nodejs_files:
            print(f"\n📦 Node.js files scanned ({len(nodejs_files)}):")
            for file in nodejs_files[:3]:  # Show first 3
                print(f"  • {file}")

    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

    # Test action execution
    print("\n🔧 Testing action execution...")
    action_result = await agent.execute_action(
        "update_package", package="requests", version="2.31.0", package_manager="pip"
    )

    if action_result["success"]:
        print(f"✅ Action executed: {action_result['message']}")
    else:
        print(f"❌ Action failed: {action_result.get('error', 'Unknown error')}")

    # Show metrics
    print("\n📈 Agent metrics:")
    metrics = agent.get_metrics_summary()
    print(f"  • Operations performed: {metrics['operations_performed']}")
    print(f"  • Files processed: {metrics['files_processed']}")
    print(f"  • Errors encountered: {metrics['errors_encountered']}")
    print(f"  • Success rate: {metrics['success_rate']:.1f}%")
    print(f"  • Runtime: {metrics['runtime_seconds']:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(test_dependency_security_agent())
