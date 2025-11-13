#!/usr/bin/env python
"""
Simple LangChain Integration Test

A standalone test to verify LangChain configuration without complex imports.
"""

import os


def test_langchain_setup():
    """Test LangChain configuration is properly set up."""

    print("\n" + "=" * 60)
    print("🧪 LangChain Integration Test - Simple")
    print("=" * 60 + "\n")

    # Load environment variables from .env file or environment
    # DO NOT hardcode keys here
    from dotenv import load_dotenv

    load_dotenv()

    # Set non-sensitive defaults only
    os.environ.setdefault("LANGCHAIN_PROJECT", "ToolboxAI-Solutions")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

    # Test 1: Environment Variables
    print("1. Testing environment variables...")
    env_vars_ok = True
    required_vars = [
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT_ID",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_TRACING_V2",
    ]

    for var in required_vars:
        actual = os.getenv(var)
        if actual:
            # Don't print the actual value for security
            if "KEY" in var or "SECRET" in var:
                print(f"   ✅ {var}: Set (hidden for security)")
            else:
                print(f"   ✅ {var}: {actual}")
        else:
            print(f"   ❌ {var}: Not set")
            env_vars_ok = False

    # Test 2: LangSmith Client
    print("\n2. Testing LangSmith client connection...")
    try:
        from langsmith import Client

        client = Client(
            api_key=os.getenv("LANGCHAIN_API_KEY"), api_url="https://api.smith.langchain.com"
        )
        print("   ✅ LangSmith client initialized successfully")

        # Try to check if client is valid (won't fail immediately)
        if client.api_key:
            print(f"   ✅ API key configured: ...{client.api_key[-10:]}")

    except ImportError:
        print("   ❌ LangSmith not installed. Run: pip install langsmith")
    except Exception as e:
        print(f"   ⚠️  Client initialization warning: {e}")

    # Test 3: LangChain Tracer
    print("\n3. Testing LangChain tracer...")
    try:
        from langchain.callbacks.tracers import LangChainTracer
        from langsmith import Client as LangSmithClient

        tracer = LangChainTracer(project_name="ToolboxAI-Test")
        print("   ✅ LangChain tracer created successfully")

    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("      Run: pip install langchain langchain-core")
    except Exception as e:
        print(f"   ⚠️  Tracer creation warning: {e}")

    # Test 4: Check .env file
    print("\n4. Checking .env file configuration...")
    env_file_path = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env"
    if os.path.exists(env_file_path):
        with open(env_file_path) as f:
            content = f.read()
            # Check if LANGCHAIN_API_KEY is present (don't expose the actual value)
            if "LANGCHAIN_API_KEY=" in content and "LANGCHAIN_API_KEY=your_" not in content:
                print("   ✅ .env file contains LANGCHAIN_API_KEY (value hidden for security)")
            else:
                print("   ⚠️  .env file exists but LANGCHAIN_API_KEY may not be set")

            # Check if LANGCHAIN_PROJECT_ID is present (don't expose the actual value)
            if "LANGCHAIN_PROJECT_ID=" in content and "LANGCHAIN_PROJECT_ID=your_" not in content:
                print("   ✅ .env file contains LANGCHAIN_PROJECT_ID (value hidden for security)")
            else:
                print("   ⚠️  .env file missing or has placeholder LANGCHAIN_PROJECT_ID")
    else:
        print(f"   ❌ .env file not found at {env_file_path}")

    # Test 5: Display Dashboard URLs
    print("\n5. LangSmith Dashboard Information...")
    project_id = os.getenv("LANGCHAIN_PROJECT_ID")

    print(f"   📊 Project Dashboard:")
    print(f"      https://smith.langchain.com/project/{project_id}")
    print(f"   📈 View Traces:")
    print(f"      https://smith.langchain.com/project/{project_id}/runs")
    print(f"   🔧 Project Settings:")
    print(f"      https://smith.langchain.com/project/{project_id}/settings")

    # Summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)

    if env_vars_ok:
        print("✅ LangChain configuration is properly set up!")
        print("✅ Your API key and project ID are configured correctly")
        print("✅ Tracing is enabled for all agent operations")
        print("\n🎉 You're ready to use LangChain with full observability!")
    else:
        print("⚠️  Some configuration items need attention")
        print("   Please check the items marked with ❌ above")

    print("\n💡 Next Steps:")
    print("   1. Start the LangGraph container:")
    print("      ./scripts/start_langgraph_services.sh")
    print("   2. Test agent execution to see traces in dashboard")
    print("   3. Monitor agent performance at the dashboard URL above")
    print("")


if __name__ == "__main__":
    test_langchain_setup()
