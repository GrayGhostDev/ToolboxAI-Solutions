import pytest_asyncio
#!/usr/bin/env python3
"""Test script to verify AI Assistant doesn't ask redundant questions"""

import asyncio
import httpx
import json
import time
from typing import Dict, List

# Configuration
API_BASE_URL = "http://127.0.0.1:8009"
AUTH_TOKEN = "dev-token"

@pytest.mark.asyncio
async def test_redundancy_fix():
    """Test that AI Assistant doesn't repeatedly ask for information already provided"""

    print("=" * 60)
    print("TESTING AI ASSISTANT REDUNDANCY FIX")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Create conversation
        print("\n1. Creating conversation...")
        response = await client.post(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"title": "Redundancy Test"}
        )

        if response.status_code != 201:
            print(f"   ❌ Failed to create conversation: {response.text}")
            return

        conversation = response.json()
        conv_id = conversation["id"]
        print(f"   ✅ Created conversation: {conv_id}")

        # 2. Test with comprehensive initial message
        print("\n2. Testing with comprehensive initial message...")
        test_cases = [
            {
                "message": "Create a 4th grade fractions pizza shop game",
                "expected_context": {
                    "grade": "4th grade",
                    "subject": "fractions",
                    "topic": "pizza shop",
                    "style": "game"
                },
                "should_not_ask": ["What grade", "What subject", "grade level"]
            },
            {
                "message": "I need it to be engaging and fun for about 25 students",
                "expected_context": {
                    "class_size": "25",
                    "engagement": "fun"
                },
                "should_not_ask": ["How many students", "class size"]
            },
            {
                "message": "Make it happen",
                "expected_context": {
                    "user_control": "delegated"
                },
                "should_trigger_completion": True
            }
        ]

        conversation_history = []

        for i, test in enumerate(test_cases, 1):
            print(f"\n   Test {i}: Sending '{test['message']}'")

            # Send message and capture response
            async with client.stream(
                "POST",
                f"{API_BASE_URL}/api/v1/ai-chat/generate",
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "conversation_id": conv_id,
                    "message": test["message"]
                },
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    print(f"      ❌ Request failed: {response.status_code}")
                    return

                full_response = ""
                got_it_found = False
                redundant_questions = []

                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)

                            if data.get("type") == "token":
                                full_response += data.get("content", "")

                            elif data.get("type") == "complete":
                                # Check for redundant questions
                                response_lower = full_response.lower()

                                # Check if "GOT IT" message appears
                                if "got it" in response_lower or "i've got everything" in response_lower:
                                    got_it_found = True

                                # Check for questions that shouldn't be asked
                                if "should_not_ask" in test:
                                    for forbidden in test["should_not_ask"]:
                                        if forbidden.lower() in response_lower and "?" in response_lower:
                                            redundant_questions.append(forbidden)

                                # Store response
                                conversation_history.append({
                                    "user": test["message"],
                                    "assistant": full_response[:200] + "..." if len(full_response) > 200 else full_response
                                })

                        except json.JSONDecodeError:
                            pass

                # Analyze results
                print(f"      Response preview: {full_response[:150]}...")

                if redundant_questions:
                    print(f"      ❌ REDUNDANT QUESTIONS FOUND: {', '.join(redundant_questions)}")
                else:
                    print(f"      ✅ No redundant questions")

                if test.get("should_trigger_completion") and got_it_found:
                    print(f"      ✅ 'GOT IT!' message found - completion triggered")
                elif test.get("should_trigger_completion") and not got_it_found:
                    print(f"      ⚠️  Expected 'GOT IT!' message but not found")

        # 3. Check conversation context
        print("\n3. Checking conversation context...")
        response = await client.get(
            f"{API_BASE_URL}/api/v1/ai-chat/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )

        if response.status_code == 200:
            conv_data = response.json()
            messages = conv_data.get("messages", [])

            print(f"   Total messages: {len(messages)}")

            # Check if context was properly extracted
            if messages:
                print("\n   Conversation flow:")
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:100]
                    print(f"      {role}: {content}...")

        # 4. Summary
        print("\n" + "=" * 60)
        print("REDUNDANCY TEST SUMMARY")
        print("=" * 60)

        if not redundant_questions:
            print("✅ SUCCESS: No redundant questions detected!")
            print("✅ AI Assistant properly uses context from previous messages")
        else:
            print("❌ FAILURE: Redundant questions still present")
            print(f"   Found: {', '.join(redundant_questions)}")

        if got_it_found:
            print("✅ 'GOT IT!' completion message properly triggered")
        else:
            print("⚠️  'GOT IT!' message not found - may need adjustment")

async def main():
    """Run the redundancy test"""
    try:
        await test_redundancy_fix()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())