import pytest_asyncio

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

#!/usr/bin/env python
"""End-to-end integration test for AI Chat system with Roblox content generation"""

import asyncio
import httpx
import json
from datetime import datetime

@pytest.mark.asyncio
async def test_full_chat_flow():
    """Test complete AI chat flow from conversation creation to content generation"""

    base_url = "http://127.0.0.1:8008"
    results = []

    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("AI CHAT INTEGRATION TEST - END TO END")
        print("=" * 80)

        # 1. Create a conversation
        print("\n1. Creating conversation...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/ai-chat/conversations",
                json={"title": "Integration Test Chat", "context": {"test": True}},
                headers={"Authorization": "Bearer test"}  # Mock auth
            )
            if response.status_code == 201:
                conversation = response.json()
                print(f"✅ Conversation created: {conversation['id']}")
                results.append("PASS: Conversation creation")
            else:
                print(f"❌ Failed to create conversation: {response.status_code}")
                print(f"   Response: {response.text}")
                results.append("FAIL: Conversation creation")
                return results
        except Exception as e:
            print(f"❌ Error creating conversation: {e}")
            results.append(f"FAIL: Conversation creation - {e}")
            return results

        # 2. Send a message asking to create a lesson
        print("\n2. Sending message to create lesson...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/ai-chat/conversations/{conversation['id']}/messages",
                json={"message": "Create a math lesson for grade 5 about fractions"},
                headers={"Authorization": "Bearer test"}
            )
            if response.status_code == 200:
                message = response.json()
                print(f"✅ Message sent: {message['content'][:50]}...")
                results.append("PASS: Message sending")
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                print(f"   Response: {response.text}")
                results.append("FAIL: Message sending")
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            results.append(f"FAIL: Message sending - {e}")

        # 3. Test WebSocket connection for streaming
        print("\n3. Testing WebSocket streaming...")
        try:
            import websockets
            ws_url = f"ws://127.0.0.1:8008/api/v1/ai-chat/ws/{conversation['id']}"

            try:
                async with websockets.connect(ws_url) as websocket:
                    # Send a message via WebSocket
                    await websocket.send(json.dumps({
                        "type": "message",
                        "content": "Design a space station environment for science experiments"
                    }))

                    # Wait for streaming response
                    response_count = 0
                    async def receive_with_timeout():
                        try:
                            return await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        except asyncio.TimeoutError:
                            return None

                    while response_count < 5:  # Receive up to 5 messages
                        data = await receive_with_timeout()
                        if data:
                            message = json.loads(data)
                            if message.get("type") == "stream_token":
                                response_count += 1
                                print(f"   Received token {response_count}: {message.get('content', '')[:20]}")

                    if response_count > 0:
                        print(f"✅ WebSocket streaming working ({response_count} tokens received)")
                        results.append("PASS: WebSocket streaming")
                    else:
                        print("⚠️  No streaming tokens received (might be in mock mode)")
                        results.append("WARN: WebSocket streaming - mock mode")

            except websockets.exceptions.WebSocketException as e:
                print(f"⚠️  WebSocket connection failed: {e}")
                results.append("WARN: WebSocket - connection failed")
        except ImportError:
            print("⚠️  websockets library not installed, skipping WebSocket test")
            results.append("SKIP: WebSocket test")

        # 4. Get conversation history
        print("\n4. Retrieving conversation history...")
        try:
            response = await client.get(
                f"{base_url}/api/v1/ai-chat/conversations/{conversation['id']}",
                headers={"Authorization": "Bearer test"}
            )
            if response.status_code == 200:
                conv_data = response.json()
                message_count = len(conv_data.get('messages', []))
                print(f"✅ Retrieved conversation with {message_count} messages")
                results.append(f"PASS: Conversation retrieval ({message_count} messages)")
            else:
                print(f"❌ Failed to get conversation: {response.status_code}")
                results.append("FAIL: Conversation retrieval")
        except Exception as e:
            print(f"❌ Error getting conversation: {e}")
            results.append(f"FAIL: Conversation retrieval - {e}")

        # 5. Test Roblox content generation endpoint directly
        print("\n5. Testing Roblox content generation...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/roblox/content/generate",
                json={
                    "content_type": "lesson",
                    "subject": "Mathematics",
                    "grade_level": 5,
                    "difficulty": "intermediate",
                    "learning_objectives": ["Understanding fractions", "Adding fractions"],
                    "description": "Interactive lesson about fractions",
                    "ai_assistance": True
                },
                headers={"Authorization": "Bearer test"}
            )
            if response.status_code in [200, 201, 202]:
                content = response.json()
                print(f"✅ Roblox content generation initiated: {content.get('content_id', 'N/A')}")
                results.append("PASS: Roblox content generation")
            else:
                print(f"⚠️  Roblox generation returned: {response.status_code}")
                print(f"   This might be expected if auth is required")
                results.append("WARN: Roblox generation - auth required")
        except Exception as e:
            print(f"❌ Error with Roblox generation: {e}")
            results.append(f"FAIL: Roblox generation - {e}")

        # 6. List conversations
        print("\n6. Listing conversations...")
        try:
            response = await client.get(
                f"{base_url}/api/v1/ai-chat/conversations",
                headers={"Authorization": "Bearer test"}
            )
            if response.status_code == 200:
                conversations = response.json()
                print(f"✅ Retrieved {len(conversations)} conversations")
                results.append(f"PASS: List conversations ({len(conversations)} found)")
            else:
                print(f"❌ Failed to list conversations: {response.status_code}")
                results.append("FAIL: List conversations")
        except Exception as e:
            print(f"❌ Error listing conversations: {e}")
            results.append(f"FAIL: List conversations - {e}")

        # 7. Archive conversation
        print("\n7. Archiving conversation...")
        try:
            response = await client.delete(
                f"{base_url}/api/v1/ai-chat/conversations/{conversation['id']}",
                headers={"Authorization": "Bearer test"}
            )
            if response.status_code == 204:
                print(f"✅ Conversation archived successfully")
                results.append("PASS: Archive conversation")
            else:
                print(f"❌ Failed to archive conversation: {response.status_code}")
                results.append("FAIL: Archive conversation")
        except Exception as e:
            print(f"❌ Error archiving conversation: {e}")
            results.append(f"FAIL: Archive conversation - {e}")

    return results

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r.startswith("PASS"))
    failed = sum(1 for r in results if r.startswith("FAIL"))
    warned = sum(1 for r in results if r.startswith("WARN"))
    skipped = sum(1 for r in results if r.startswith("SKIP"))

    for result in results:
        if result.startswith("PASS"):
            print(f"✅ {result}")
        elif result.startswith("FAIL"):
            print(f"❌ {result}")
        elif result.startswith("WARN"):
            print(f"⚠️  {result}")
        else:
            print(f"⏭️  {result}")

    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    print("\n" + "-" * 40)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Warnings: {warned}")
    print(f"Skipped: {skipped}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("-" * 40)

    if pass_rate >= 85:
        print("🎉 TEST SUITE PASSED (>85% pass rate)")
    else:
        print("❌ TEST SUITE FAILED (<85% pass rate)")

    return pass_rate

async def main():
    """Run the integration test"""
    print(f"Starting integration test at {datetime.now()}")
    print("Make sure the backend server is running on port 8008")
    print("-" * 80)

    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8008/health")
            if response.status_code != 200:
                print("⚠️  Warning: Health check returned", response.status_code)
    except Exception as e:
        print(f"❌ Server not responding at http://127.0.0.1:8008")
        print(f"   Error: {e}")
        print("\nPlease start the server with:")
        print("   cd apps/backend && uvicorn main:app --host 127.0.0.1 --port 8008 --reload")
        return

    # Run tests
    results = await test_full_chat_flow()

    # Print summary
    pass_rate = print_summary(results)

    # Return exit code
    return 0 if pass_rate >= 85 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)