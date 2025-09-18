#!/usr/bin/env python3
"""Test script to verify improved streaming response times for AI Assistant"""

import asyncio
import httpx
import json
import time
from typing import AsyncGenerator

# Configuration
API_BASE_URL = "http://127.0.0.1:8009"  # Using port 8009
AUTH_TOKEN = "dev-token"

async def test_streaming_response():
    """Test that AI responses start streaming immediately"""

    print("=" * 60)
    print("TESTING STREAMING RESPONSE TIMES")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Create conversation
        print("\n1. Creating conversation...")
        start_time = time.time()

        response = await client.post(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"title": "Streaming Test"}
        )

        if response.status_code != 201:
            print(f"   ❌ Failed to create conversation: {response.text}")
            return

        conversation = response.json()
        conv_id = conversation["id"]
        print(f"   ✅ Created conversation: {conv_id} in {time.time() - start_time:.2f}s")

        # 2. Test streaming response time
        print("\n2. Testing streaming response...")
        message = "Hello! I want to create a 5th grade solar system simulation in Roblox"

        print(f"   Sending: '{message}'")
        start_time = time.time()
        first_token_time = None
        tokens_received = 0

        # Use httpx streaming for NDJSON
        async with client.stream(
            "POST",
            f"{API_BASE_URL}/api/v1/ai-chat/generate",
            headers={
                "Authorization": f"Bearer {AUTH_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "conversation_id": conv_id,
                "message": message
            },
            timeout=60.0
        ) as response:
            if response.status_code != 200:
                print(f"   ❌ Request failed: {response.status_code}")
                return

            print("   Streaming response:")
            full_response = ""

            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)

                        if data.get("type") == "start":
                            print(f"   ✅ Stream started in {time.time() - start_time:.2f}s")

                        elif data.get("type") == "token":
                            if first_token_time is None:
                                first_token_time = time.time() - start_time
                                print(f"   ✅ First token received in {first_token_time:.2f}s")

                            tokens_received += 1
                            full_response += data.get("content", "")

                            # Print first few tokens
                            if tokens_received <= 10:
                                print(f"      Token {tokens_received}: '{data.get('content', '')}'")

                        elif data.get("type") == "complete":
                            total_time = time.time() - start_time
                            print(f"\n   ✅ Response completed in {total_time:.2f}s")
                            print(f"   📊 Stats:")
                            print(f"      - First token time: {first_token_time:.2f}s")
                            print(f"      - Total tokens: {tokens_received}")
                            print(f"      - Response length: {len(full_response)} characters")

                            if first_token_time and first_token_time < 2.0:
                                print(f"   🎉 SUCCESS: First token received within 2 seconds!")
                            else:
                                print(f"   ⚠️  WARNING: First token took longer than expected")

                        elif data.get("type") == "error":
                            print(f"   ❌ Error: {data.get('error')}")

                    except json.JSONDecodeError:
                        # Ignore incomplete JSON chunks
                        pass

        # 3. Test multiple messages to verify consistency
        print("\n3. Testing response consistency...")
        test_messages = [
            "Can you help me design interactive planets?",
            "I'd like to add quizzes about each planet",
            "Puzzle"  # Test context understanding
        ]

        for i, msg in enumerate(test_messages, 1):
            print(f"\n   Test {i}: '{msg}'")
            start_time = time.time()

            async with client.stream(
                "POST",
                f"{API_BASE_URL}/api/v1/ai-chat/generate",
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "conversation_id": conv_id,
                    "message": msg
                },
                timeout=60.0
            ) as response:
                if response.status_code == 200:
                    first_token = None
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("type") == "token" and first_token is None:
                                    first_token = time.time() - start_time
                                    print(f"      First token: {first_token:.2f}s")
                                    break
                            except:
                                pass
                else:
                    print(f"      ❌ Failed: {response.status_code}")

        print("\n" + "=" * 60)
        print("STREAMING TEST COMPLETED")
        print("=" * 60)

async def main():
    """Run the streaming test"""
    try:
        await test_streaming_response()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())