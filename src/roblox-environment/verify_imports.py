#!/usr/bin/env python3
"""
Verification script to test all critical imports for ToolboxAI Roblox Environment
"""

import sys
import traceback
import importlib


def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        # Use importlib instead of exec() for security (SonarQube: S1523)
        if package_name:
            module = importlib.import_module(f"{package_name}.{module_name}")
            print(f"✓ {package_name}.{module_name}")
        else:
            module = importlib.import_module(module_name)
            print(f"✓ {module_name}")
        return True
    except ImportError as e:
        print(f"✗ {package_name + '.' if package_name else ''}{module_name}: {e}")
        return False
    except Exception as e:
        print(
            f"✗ {package_name + '.' if package_name else ''}{module_name}: Unexpected error - {e}"
        )
        return False


def main():
    print("=" * 60)
    print("Testing Critical Imports for ToolboxAI Roblox Environment")
    print("=" * 60)

    categories = {
        "Web Frameworks": [
            ("fastapi", None),
            ("uvicorn", None),
            ("flask", None),
            ("flask_cors", None),
        ],
        "LangChain Ecosystem": [
            ("langchain", None),
            ("langchain_openai", None),
            ("langchain_community", None),
            ("langgraph", None),
        ],
        "AI/ML Libraries": [
            ("openai", None),
            ("tiktoken", None),
            ("numpy", None),
            ("sentence_transformers", None),
            ("faiss", None),
        ],
        "Database": [
            ("sqlalchemy", None),
            ("alembic", None),
            ("asyncpg", None),
            ("redis", None),
            ("motor", None),
        ],
        "Authentication": [
            ("jose", None),
            ("passlib", None),
        ],
        "Data Validation": [
            ("pydantic", None),
            ("pydantic_settings", None),
            ("dotenv", None),
            ("yaml", None),
        ],
        "Real-time": [
            ("websockets", None),
            ("socketio", None),
        ],
        "HTTP Clients": [
            ("httpx", None),
            ("aiohttp", None),
            ("requests", None),
        ],
        "Educational Tools": [
            ("wikipedia", None),
            ("duckduckgo_search", None),
        ],
        "Utilities": [
            ("structlog", None),
            ("prometheus_client", None),
            ("psutil", None),
            ("tenacity", None),
        ],
    }

    total_tests = 0
    passed_tests = 0

    for category, modules in categories.items():
        print(f"\n{category}:")
        print("-" * 40)
        for module_name, package_name in modules:
            total_tests += 1
            if test_import(module_name, package_name):
                passed_tests += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} imports successful")
    print("=" * 60)

    # Test specific functionality
    print("\nTesting specific functionality:")
    print("-" * 40)

    try:
        from langchain_openai import ChatOpenAI

        print("✓ Can import ChatOpenAI from langchain_openai")
    except Exception as e:
        print(f"✗ Cannot import ChatOpenAI: {e}")

    try:
        from langchain.agents import AgentExecutor

        print("✓ Can import AgentExecutor from langchain")
    except Exception as e:
        print(f"✗ Cannot import AgentExecutor: {e}")

    try:
        from sentence_transformers import SentenceTransformer

        print("✓ Can import SentenceTransformer")
    except Exception as e:
        print(f"✗ Cannot import SentenceTransformer: {e}")

    try:
        import torch

        print(f"✓ PyTorch installed (version: {torch.__version__})")
    except Exception as e:
        print(f"✗ PyTorch not available: {e}")

    if passed_tests == total_tests:
        print("\n✓ All critical imports successful! Environment is ready.")
        return 0
    else:
        print(
            f"\n⚠ Some imports failed ({total_tests - passed_tests} failures). Please check the errors above."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
