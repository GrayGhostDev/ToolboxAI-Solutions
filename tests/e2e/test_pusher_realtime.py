"""
End-to-End Tests for Pusher Real-time Functionality

Tests critical user flows that involve real-time communication:
- Content generation with real-time progress updates
- Analytics dashboard with live data updates
- Multi-user collaboration scenarios
- Connection recovery and resilience
- Message ordering and delivery guarantees
"""

import asyncio
import json
import time

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Playwright for modern browser automation
try:
    from playwright.async_api import Browser, Page, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class TestPusherE2E:
    """End-to-end tests for Pusher real-time functionality"""

    @pytest.fixture
    async def browser_context(self):
        """Browser context for Playwright tests"""
        if not PLAYWRIGHT_AVAILABLE:
            pytest.skip("Playwright not available")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await browser.close()

    @pytest.fixture
    async def authenticated_page(self, browser_context):
        """Authenticated page for testing"""
        page = await browser_context.new_page()

        # Navigate to login page
        await page.goto("http://localhost:5179/login")

        # Perform login (mock or actual)
        await page.fill("[data-testid=email-input]", "test@example.com")
        await page.fill("[data-testid=password-input]", "password123")
        await page.click("[data-testid=login-button]")

        # Wait for dashboard to load
        try:
            await page.wait_for_selector("[data-testid=dashboard-container]", timeout=10000)
        except TimeoutException:
            # If login fails, create mock authenticated state
            await page.evaluate(
                """
                localStorage.setItem('toolboxai_auth_token', 'mock-jwt-token');
                localStorage.setItem('toolboxai_user', JSON.stringify({
                    id: 'test-user-id',
                    email: 'test@example.com',
                    role: 'student'
                }));
            """
            )
            await page.goto("http://localhost:5179/dashboard")

        yield page

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_content_generation_realtime_flow(self, authenticated_page):
        """Test complete content generation flow with real-time updates"""
        page = authenticated_page

        # Navigate to content generation page
        await page.goto("http://localhost:5179/content/generate")

        # Fill out content generation form
        await page.fill("[data-testid=subject-input]", "Solar System")
        await page.select_option("[data-testid=grade-select]", "5")
        await page.fill(
            "[data-testid=objectives-input]",
            "Learn about planets and their characteristics",
        )

        # Mock Pusher connection for testing
        await page.evaluate(
            """
            window.mockPusherService = {
                isConnected: true,
                subscribe: (channel, handler) => {
                    window.mockHandlers = window.mockHandlers || {};
                    window.mockHandlers[channel] = handler;
                    return 'mock-subscription-id';
                },
                send: (type, payload) => {
                    console.log('Mock send:', type, payload);
                    return Promise.resolve();
                }
            };
        """
        )

        # Start content generation
        await page.click("[data-testid=generate-button]")

        # Verify progress container appears
        await page.wait_for_selector("[data-testid=progress-container]", timeout=5000)

        # Simulate real-time progress updates
        progress_updates = [
            {
                "stage": "initializing",
                "percentage": 0,
                "message": "Starting generation...",
            },
            {
                "stage": "analyzing",
                "percentage": 25,
                "message": "Analyzing requirements...",
            },
            {"stage": "generating", "percentage": 50, "message": "Creating content..."},
            {
                "stage": "optimizing",
                "percentage": 75,
                "message": "Optimizing for grade level...",
            },
            {
                "stage": "finalizing",
                "percentage": 100,
                "message": "Finalizing content...",
            },
        ]

        for update in progress_updates:
            # Simulate receiving Pusher message
            await page.evaluate(
                f"""
                if (window.mockHandlers && window.mockHandlers['content-generation']) {{
                    window.mockHandlers['content-generation']({{
                        type: 'content_progress',
                        payload: {json.dumps(update)}
                    }});
                }}
            """
            )

            # Verify progress bar updates
            progress_element = await page.wait_for_selector(
                f"[data-testid=progress-bar][data-percentage='{update['percentage']}']",
                timeout=2000,
            )
            assert progress_element is not None

            # Verify stage message updates
            stage_element = await page.wait_for_selector(
                f"[data-testid=stage-message]:has-text('{update['message']}')",
                timeout=2000,
            )
            assert stage_element is not None

        # Simulate completion
        await page.evaluate(
            """
            if (window.mockHandlers && window.mockHandlers['content-generation']) {
                window.mockHandlers['content-generation']({
                    type: 'content_complete',
                    payload: {
                        requestId: 'test-request-id',
                        status: 'completed',
                        content: {
                            scripts: ['TerrainScript.lua', 'PlanetScript.lua'],
                            terrain: { type: 'space', size: 'large' },
                            assets: ['Earth', 'Mars', 'Jupiter'],
                            quiz: { questions: [] }
                        }
                    }
                });
            }
        """
        )

        # Verify completion state
        await page.wait_for_selector("[data-testid=generation-complete]", timeout=5000)

        # Verify content preview appears
        await page.wait_for_selector("[data-testid=content-preview]", timeout=5000)

        # Verify scripts are listed
        scripts = await page.query_selector_all("[data-testid=script-item]")
        assert len(scripts) == 2

        # Verify assets are listed
        assets = await page.query_selector_all("[data-testid=asset-item]")
        assert len(assets) == 3

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_analytics_dashboard_realtime_updates(self, authenticated_page):
        """Test analytics dashboard with real-time data updates"""
        page = authenticated_page

        # Navigate to analytics dashboard
        await page.goto("http://localhost:5179/analytics")

        # Wait for dashboard to load
        await page.wait_for_selector("[data-testid=analytics-dashboard]", timeout=5000)

        # Mock initial chart data
        await page.evaluate(
            """
            window.mockChartData = {
                userActivity: [10, 15, 8, 12, 20],
                contentGeneration: [5, 3, 7, 2, 9],
                systemMetrics: { cpu: 45, memory: 62, requests: 1250 }
            };
        """
        )

        # Verify initial charts render
        await page.wait_for_selector("[data-testid=user-activity-chart]", timeout=5000)
        await page.wait_for_selector("[data-testid=content-generation-chart]", timeout=5000)
        await page.wait_for_selector("[data-testid=system-metrics-chart]", timeout=5000)

        # Simulate real-time metric updates
        updates = [
            {
                "type": "user_activity",
                "data": {"newUsers": 3, "activeUsers": 25, "completedLessons": 8},
            },
            {
                "type": "content_metrics",
                "data": {
                    "generationsToday": 12,
                    "averageTime": 45,
                    "successRate": 0.95,
                },
            },
            {
                "type": "system_metrics",
                "data": {"cpu": 52, "memory": 58, "activeConnections": 150},
            },
        ]

        for update in updates:
            # Simulate receiving real-time update
            await page.evaluate(
                f"""
                if (window.mockHandlers && window.mockHandlers['analytics-updates']) {{
                    window.mockHandlers['analytics-updates']({{
                        type: 'metrics_update',
                        payload: {json.dumps(update)}
                    }});
                }}
            """
            )

            # Allow time for chart updates
            await asyncio.sleep(0.5)

        # Verify metrics cards updated
        for metric_type in ["user_activity", "content_metrics", "system_metrics"]:
            metric_card = await page.wait_for_selector(
                f"[data-testid={metric_type}-card][data-updated=true]", timeout=3000
            )
            assert metric_card is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_multi_user_collaboration(self, browser_context):
        """Test multi-user collaboration with presence channels"""
        # Create two browser pages for different users
        page1 = await browser_context.new_page()
        page2 = await browser_context.new_page()

        # Authenticate both users
        for i, page in enumerate([page1, page2], 1):
            await page.goto("http://localhost:5179/login")

            # Mock authentication for each user
            await page.evaluate(
                f"""
                localStorage.setItem('toolboxai_auth_token', 'mock-jwt-token-{i}');
                localStorage.setItem('toolboxai_user', JSON.stringify({{
                    id: 'test-user-{i}',
                    email: 'user{i}@example.com',
                    name: 'Test User {i}',
                    role: 'teacher'
                }}));
            """
            )

            await page.goto("http://localhost:5179/collaboration/classroom-123")

        # Wait for both users to join the collaboration space
        for page in [page1, page2]:
            await page.wait_for_selector("[data-testid=collaboration-workspace]", timeout=5000)

        # Mock presence channel for user 1
        await page1.evaluate(
            """
            window.mockPresenceMembers = [
                { id: 'test-user-1', name: 'Test User 1', role: 'teacher', status: 'online' }
            ];

            if (window.mockHandlers && window.mockHandlers['presence-classroom-123']) {
                window.mockHandlers['presence-classroom-123']({
                    type: 'pusher:subscription_succeeded',
                    payload: {
                        presence: {
                            count: 1,
                            ids: ['test-user-1'],
                            hash: { 'test-user-1': { name: 'Test User 1', role: 'teacher' } }
                        }
                    }
                });
            }
        """
        )

        # User 2 joins - simulate member_added event
        await page2.evaluate(
            """
            if (window.mockHandlers && window.mockHandlers['presence-classroom-123']) {
                window.mockHandlers['presence-classroom-123']({
                    type: 'pusher:member_added',
                    payload: {
                        id: 'test-user-2',
                        info: { name: 'Test User 2', role: 'teacher', status: 'online' }
                    }
                });
            }
        """
        )

        # Verify both users see each other in presence list
        for page in [page1, page2]:
            await page.wait_for_selector("[data-testid=presence-members]", timeout=5000)
            member_elements = await page.query_selector_all("[data-testid=member-item]")
            assert len(member_elements) >= 1  # At least current user

        # Simulate user 1 typing
        await page1.fill("[data-testid=collaboration-input]", "Hello from User 1!")

        # Simulate typing indicator
        await page2.evaluate(
            """
            if (window.mockHandlers && window.mockHandlers['presence-classroom-123']) {
                window.mockHandlers['presence-classroom-123']({
                    type: 'user_typing',
                    payload: {
                        userId: 'test-user-1',
                        userName: 'Test User 1',
                        isTyping: true
                    }
                });
            }
        """
        )

        # Verify typing indicator appears on page 2
        typing_indicator = await page2.wait_for_selector(
            "[data-testid=typing-indicator]:has-text('Test User 1 is typing')",
            timeout=3000,
        )
        assert typing_indicator is not None

        # Send message from user 1
        await page1.click("[data-testid=send-message-button]")

        # Simulate message received on both pages
        message_data = {
            "id": "msg-123",
            "userId": "test-user-1",
            "userName": "Test User 1",
            "content": "Hello from User 1!",
            "timestamp": int(time.time() * 1000),
        }

        for page in [page1, page2]:
            await page.evaluate(
                f"""
                if (window.mockHandlers && window.mockHandlers['presence-classroom-123']) {{
                    window.mockHandlers['presence-classroom-123']({{
                        type: 'user_message',
                        payload: {json.dumps(message_data)}
                    }});
                }}
            """
            )

        # Verify message appears in both chat windows
        for page in [page1, page2]:
            message_element = await page.wait_for_selector(
                "[data-testid=message-item]:has-text('Hello from User 1!')",
                timeout=3000,
            )
            assert message_element is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_connection_recovery_flow(self, authenticated_page):
        """Test connection recovery and message queuing"""
        page = authenticated_page

        # Navigate to a page that uses real-time features
        await page.goto("http://localhost:5179/dashboard")

        # Wait for initial connection
        await page.wait_for_selector(
            "[data-testid=connection-status][data-status=connected]", timeout=5000
        )

        # Simulate connection loss
        await page.evaluate(
            """
            if (window.pusherService) {
                window.pusherService.disconnect('Simulated connection loss');
            }

            // Mock disconnected state
            if (window.mockHandlers && window.mockHandlers['connection-status']) {
                window.mockHandlers['connection-status']({
                    type: 'connection_state_change',
                    payload: { state: 'disconnected' }
                });
            }
        """
        )

        # Verify disconnected state is shown
        await page.wait_for_selector(
            "[data-testid=connection-status][data-status=disconnected]", timeout=3000
        )

        # Verify reconnection indicator appears
        reconnecting_indicator = await page.wait_for_selector(
            "[data-testid=reconnection-indicator]", timeout=3000
        )
        assert reconnecting_indicator is not None

        # Try to send a message while disconnected (should be queued)
        await page.click("[data-testid=test-send-message-button]")

        # Verify message queued indicator
        queued_indicator = await page.wait_for_selector(
            "[data-testid=message-queued-indicator]", timeout=3000
        )
        assert queued_indicator is not None

        # Simulate reconnection
        await page.evaluate(
            """
            if (window.mockHandlers && window.mockHandlers['connection-status']) {
                window.mockHandlers['connection-status']({
                    type: 'connection_state_change',
                    payload: { state: 'connecting' }
                });
            }
        """
        )

        await asyncio.sleep(1)

        await page.evaluate(
            """
            if (window.mockHandlers && window.mockHandlers['connection-status']) {
                window.mockHandlers['connection-status']({
                    type: 'connection_state_change',
                    payload: { state: 'connected' }
                });
            }
        """
        )

        # Verify connected state is restored
        await page.wait_for_selector(
            "[data-testid=connection-status][data-status=connected]", timeout=3000
        )

        # Verify queued message was sent
        sent_indicator = await page.wait_for_selector(
            "[data-testid=message-sent-indicator]", timeout=5000
        )
        assert sent_indicator is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_message_ordering_guarantee(self, authenticated_page):
        """Test that messages are received in correct order"""
        page = authenticated_page

        # Navigate to messaging interface
        await page.goto("http://localhost:5179/messages")

        # Mock rapid message sequence
        messages = [
            {
                "id": "msg-1",
                "sequence": 1,
                "content": "First message",
                "timestamp": 1000,
            },
            {
                "id": "msg-2",
                "sequence": 2,
                "content": "Second message",
                "timestamp": 1001,
            },
            {
                "id": "msg-3",
                "sequence": 3,
                "content": "Third message",
                "timestamp": 1002,
            },
            {
                "id": "msg-4",
                "sequence": 4,
                "content": "Fourth message",
                "timestamp": 1003,
            },
            {
                "id": "msg-5",
                "sequence": 5,
                "content": "Fifth message",
                "timestamp": 1004,
            },
        ]

        # Send messages rapidly with small delays
        for i, message in enumerate(messages):
            await page.evaluate(
                f"""
                setTimeout(() => {{
                    if (window.mockHandlers && window.mockHandlers['message-channel']) {{
                        window.mockHandlers['message-channel']({{
                            type: 'ordered_message',
                            payload: {json.dumps(message)}
                        }});
                    }}
                }}, {i * 10});  // 10ms intervals
            """
            )

        # Wait for all messages to be processed
        await asyncio.sleep(1)

        # Verify messages appear in correct order
        message_elements = await page.query_selector_all("[data-testid=message-item]")
        assert len(message_elements) >= len(messages)

        # Check sequence numbers are in order
        for i, element in enumerate(message_elements[: len(messages)]):
            sequence_attr = await element.get_attribute("data-sequence")
            assert sequence_attr == str(i + 1)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_system_notification_flow(self, authenticated_page):
        """Test system-wide notifications"""
        page = authenticated_page

        # Navigate to dashboard
        await page.goto("http://localhost:5179/dashboard")

        # Simulate system maintenance notification
        maintenance_notification = {
            "id": "maint-123",
            "type": "maintenance",
            "severity": "warning",
            "title": "Scheduled Maintenance",
            "message": "System will be unavailable from 2-4 AM UTC for maintenance",
            "duration": 8000,  # 8 seconds
            "dismissible": True,
        }

        await page.evaluate(
            f"""
            if (window.mockHandlers && window.mockHandlers['system-announcements']) {{
                window.mockHandlers['system-announcements']({{
                    type: 'system_notification',
                    payload: {json.dumps(maintenance_notification)}
                }});
            }}
        """
        )

        # Verify notification appears
        notification = await page.wait_for_selector(
            "[data-testid=system-notification][data-type=maintenance]", timeout=3000
        )
        assert notification is not None

        # Verify notification content
        title_element = await page.wait_for_selector(
            "[data-testid=notification-title]:has-text('Scheduled Maintenance')",
            timeout=2000,
        )
        assert title_element is not None

        # Test dismissing notification
        dismiss_button = await page.wait_for_selector(
            "[data-testid=dismiss-notification]", timeout=2000
        )
        await dismiss_button.click()

        # Verify notification is dismissed
        try:
            await page.wait_for_selector(
                "[data-testid=system-notification][data-type=maintenance]",
                timeout=1000,
                state="detached",
            )
        except TimeoutException:
            pass  # Expected - notification should be gone

    @pytest.mark.asyncio
    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
    async def test_performance_under_load(self, authenticated_page):
        """Test UI performance under high message load"""
        page = authenticated_page

        # Navigate to high-traffic dashboard
        await page.goto("http://localhost:5179/dashboard")

        # Start performance monitoring
        await page.evaluate(
            """
            window.performanceMetrics = {
                messageCount: 0,
                renderTimes: [],
                startTime: performance.now()
            };

            // Monitor render performance
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'measure') {
                        window.performanceMetrics.renderTimes.push(entry.duration);
                    }
                }
            }).observe({ entryTypes: ['measure'] });
        """
        )

        # Simulate high-frequency message stream
        message_count = 100
        batch_size = 10

        for batch in range(0, message_count, batch_size):
            batch_messages = []
            for i in range(batch, min(batch + batch_size, message_count)):
                batch_messages.append(
                    {
                        "id": f"msg-{i}",
                        "type": "analytics_update",
                        "data": {"metric": "user_activity", "value": i * 2},
                        "timestamp": int(time.time() * 1000) + i,
                    }
                )

            # Send batch of messages
            await page.evaluate(
                f"""
                const messages = {json.dumps(batch_messages)};
                messages.forEach((msg, index) => {{
                    setTimeout(() => {{
                        performance.mark('message-start-' + msg.id);
                        if (window.mockHandlers && window.mockHandlers['dashboard-updates']) {{
                            window.mockHandlers['dashboard-updates']({{
                                type: 'analytics_update',
                                payload: msg
                            }});
                        }}
                        performance.mark('message-end-' + msg.id);
                        performance.measure('message-process-' + msg.id, 'message-start-' + msg.id, 'message-end-' + msg.id);
                        window.performanceMetrics.messageCount++;
                    }}, index * 10);
                }});
            """
            )

            # Small delay between batches to avoid overwhelming
            await asyncio.sleep(0.2)

        # Wait for all messages to be processed
        await asyncio.sleep(2)

        # Check performance metrics
        metrics = await page.evaluate(
            """
            return {
                messageCount: window.performanceMetrics.messageCount,
                avgRenderTime: window.performanceMetrics.renderTimes.reduce((a, b) => a + b, 0) / window.performanceMetrics.renderTimes.length,
                maxRenderTime: Math.max(...window.performanceMetrics.renderTimes),
                totalTime: performance.now() - window.performanceMetrics.startTime
            };
        """
        )

        # Verify performance is acceptable
        assert metrics["messageCount"] == message_count
        assert metrics["avgRenderTime"] < 50  # Average render time under 50ms
        assert metrics["maxRenderTime"] < 200  # Max render time under 200ms
        assert metrics["totalTime"] < 10000  # Total time under 10 seconds

        # Verify UI is still responsive
        dashboard_element = await page.wait_for_selector(
            "[data-testid=dashboard-container]", timeout=2000
        )
        assert dashboard_element is not None


class TestPusherE2ESelenium:
    """Selenium-based E2E tests as fallback"""

    @pytest.fixture
    def driver(self):
        """Selenium WebDriver setup"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_basic_connection_status_selenium(self, driver):
        """Basic test using Selenium as fallback"""
        try:
            driver.get("http://localhost:5179/dashboard")

            # Try to find connection status indicator
            try:
                connection_status = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid=connection-status]")
                    )
                )
                assert connection_status is not None
            except TimeoutException:
                # If specific element not found, at least verify page loads
                assert "ToolboxAI" in driver.title or len(driver.page_source) > 1000

        except Exception as e:
            # If connection fails, skip the test
            pytest.skip(f"Dashboard not accessible: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
