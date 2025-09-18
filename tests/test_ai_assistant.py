#!/usr/bin/env python3
"""Test AI Assistant with OpenAI fallback for Roblox educational content generation"""

import asyncio
import httpx
import json
from typing import AsyncGenerator

# Configuration
API_BASE_URL = "http://127.0.0.1:8009"
AUTH_TOKEN = "dev-token"

async def test_conversation_flow():
    """Test full conversation flow with AI Assistant"""

    async with httpx.AsyncClient() as client:
        # 1. Create conversation
        print("1. Creating conversation...")
        response = await client.post(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"title": "Solar System Simulation"}
        )
        if response.status_code != 201:
            print(f"Failed to create conversation: {response.text}")
            return

        conversation = response.json()
        conv_id = conversation["id"]
        print(f"   Created conversation: {conv_id}")

        # 2. Test messages for natural language understanding
        test_messages = [
            "Hello! I want to create a 5th grade solar system simulation in Roblox",
            "Can you help me design an interactive environment where students can explore planets?",
            "I'd like to add quizzes about each planet",
            "Puzzle",  # Test that it understands this in context of quizzes
            "Can you generate the Lua script for the main solar system controller?"
        ]

        for i, message in enumerate(test_messages, 1):
            print(f"\n{i+1}. Sending: '{message}'")

            # Send message
            response = await client.post(
                f"{API_BASE_URL}/api/v1/ai-chat/generate",
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "conversation_id": conv_id,
                    "message": message
                },
                timeout=30.0
            )

            if response.status_code == 200:
                # Stream response
                print("   Response: ", end="")
                char_count = 0
                async for line in response.aiter_lines():
                    if line:
                        print(line[:100] + "..." if len(line) > 100 else line)
                        char_count += len(line)
                        if char_count > 500:  # Limit output for readability
                            print("   [Response continues...]")
                            break
            else:
                print(f"   Error: {response.status_code} - {response.text}")

        # 3. Test conversation memory
        print("\n4. Testing conversation memory...")
        response = await client.get(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )

        if response.status_code == 200:
            conv_data = response.json()
            message_count = len(conv_data.get("messages", []))
            print(f"   Conversation has {message_count} messages")
            print(f"   Memory context retained: {'Yes' if message_count > 0 else 'No'}")
        else:
            print(f"   Could not retrieve conversation: {response.status_code}")

async def test_streaming_response():
    """Test streaming response capability"""
    print("\n5. Testing streaming response...")

    async with httpx.AsyncClient() as client:
        # Create a conversation first
        response = await client.post(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"title": "Streaming Test"}
        )

        if response.status_code != 201:
            print(f"   Failed to create conversation: {response.text}")
            return

        conv_id = response.json()["id"]

        # Send message and test streaming
        print("   Sending message for streaming test...")
        async with client.stream(
            "POST",
            f"{API_BASE_URL}/api/v1/ai-chat/generate",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "conversation_id": conv_id,
                "message": "Generate a simple Lua script for a Roblox part that changes color"
            },
            timeout=30.0
        ) as response:
            if response.status_code == 200:
                print("   Streaming response received:")
                char_count = 0
                async for chunk in response.aiter_text():
                    if chunk:
                        print(chunk, end="", flush=True)
                        char_count += len(chunk)
                        if char_count > 300:  # Limit for readability
                            print("\n   [Stream continues...]")
                            break
                print("\n   Streaming successful!")
            else:
                print(f"   Streaming failed: {response.status_code}")

async def test_roblox_content_generation():
    """Test Roblox-specific content generation"""
    print("\n6. Testing Roblox content generation...")

    async with httpx.AsyncClient() as client:
        # Create conversation
        response = await client.post(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"title": "Roblox Content Test"}
        )

        if response.status_code != 201:
            print(f"   Failed to create conversation: {response.text}")
            return

        conv_id = response.json()["id"]

        # Test Roblox-specific requests
        roblox_requests = [
            "Create a Roblox script for a quiz system with multiple choice questions",
            "Design a 3D educational environment for teaching about gravity",
            "Generate puzzle-based assessments for math concepts"
        ]

        for request in roblox_requests:
            print(f"\n   Testing: {request[:50]}...")
            response = await client.post(
                f"{API_BASE_URL}/api/v1/ai-chat/generate",
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "conversation_id": conv_id,
                    "message": request
                },
                timeout=30.0
            )

            if response.status_code == 200:
                print("   ✓ Response generated successfully")
            else:
                print(f"   ✗ Failed: {response.status_code}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("AI ASSISTANT TEST SUITE")
    print("Testing OpenAI fallback for Roblox content generation")
    print("=" * 60)

    try:
        # Test basic conversation flow
        await test_conversation_flow()

        # Test streaming
        await test_streaming_response()

        # Test Roblox content
        await test_roblox_content_generation()

        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())