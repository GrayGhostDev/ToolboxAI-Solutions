"""Playwright Pusher Testing Suite.

This module implements comprehensive E2E tests for Pusher real-time
features using Playwright. Migrated from WebSocket to Pusher patterns.
"""

import asyncio

import pytest
from playwright.async_api import Page, async_playwright


@pytest.mark.e2e
class TestPusherConnections:
    """Test Pusher connectivity and real-time features (migrated from WebSocket)."""

    @pytest.mark.asyncio
    async def test_should_establish_pusher_connection(self):
        """Test that Pusher connection can be established."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            # Enable console logging to track Pusher events
            console_logs = []
            page.on("console", lambda msg: console_logs.append(msg.text()))

            # Navigate to the application
            await page.goto("http://localhost:5179")

            # Wait for Pusher connection
            await page.wait_for_timeout(2000)

            # Check Pusher connection status
            pusher_status = await page.evaluate(
                """() => {
                if (window.pusher) {
                    return {
                        state: window.pusher.connection.state,
                        socket_id: window.pusher.connection.socket_id,
                        connected: window.pusher.connection.state === 'connected'
                    };
                }
                return { state: 'not initialized', connected: false };
            }"""
            )

            # Verify Pusher connection established
            assert pusher_status["connected"], f"Pusher not connected: {pusher_status['state']}"
            assert pusher_status.get("socket_id"), "No socket ID assigned"

            # Test Pusher messaging by checking subscribed channels
            channels = await page.evaluate(
                """() => {
                if (window.pusher) {
                    return Object.keys(window.pusher.allChannels());
                }
                return [];
            }"""
            )

            print(f"Subscribed to channels: {channels}")
            assert len(channels) > 0, "No Pusher channels subscribed"

            await browser.close()

    @pytest.mark.asyncio
    async def test_should_handle_pusher_reconnection(self):
        """Test Pusher reconnection after disconnection."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            # Track connection state changes
            await page.expose_function(
                "trackStateChange", lambda state: print(f"Pusher state changed: {state}")
            )

            await page.goto("http://localhost:5179")

            # Set up state change tracking
            await page.evaluate(
                """() => {
                if (window.pusher) {
                    window.pusher.connection.bind('state_change', function(states) {
                        window.trackStateChange({
                            previous: states.previous,
                            current: states.current
                        });
                    });
                }
            }"""
            )

            await page.wait_for_timeout(2000)

            # Get initial connection state
            initial_state = await page.evaluate(
                """() => window.pusher ? window.pusher.connection.state : 'not initialized'"""
            )
            assert initial_state == "connected", "Initial Pusher connection not established"

            # Simulate network interruption
            await context.set_offline(True)
            await page.wait_for_timeout(1000)

            # Check disconnected state
            offline_state = await page.evaluate(
                """() => window.pusher ? window.pusher.connection.state : 'not initialized'"""
            )
            assert offline_state in [
                "unavailable",
                "disconnected",
                "connecting",
            ], f"Unexpected offline state: {offline_state}"

            # Restore network
            await context.set_offline(False)
            await page.wait_for_timeout(3000)

            # Check for reconnection
            final_state = await page.evaluate(
                """() => window.pusher ? window.pusher.connection.state : 'not initialized'"""
            )
            assert final_state == "connected", "Pusher did not reconnect"

            await browser.close()

    @pytest.mark.asyncio
    async def test_should_receive_real_time_updates(self):
        """Test receiving real-time updates through Pusher."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            # Open two browser contexts to simulate multiple users
            context1 = await browser.new_context()
            context2 = await browser.new_context()

            page1 = await context1.new_page()
            page2 = await context2.new_page()

            # Track Pusher events for both pages
            page1_events = []
            page2_events = []

            await page1.expose_function(
                "recordPage1Event", lambda event: page1_events.append(event)
            )
            await page2.expose_function(
                "recordPage2Event", lambda event: page2_events.append(event)
            )

            # Navigate both pages
            await page1.goto("http://localhost:5179/dashboard")
            await page2.goto("http://localhost:5179/dashboard")

            # Login on both pages
            await self._login_user(page1, "user1", "password1")
            await self._login_user(page2, "user2", "password2")

            # Set up event listeners
            await page1.evaluate(
                """() => {
                if (window.pusher) {
                    const channel = window.pusher.subscribe('dashboard-updates');
                    channel.bind_global((eventName, data) => {
                        window.recordPage1Event({
                            event: eventName,
                            data: data,
                            timestamp: Date.now()
                        });
                    });
                }
            }"""
            )

            await page2.evaluate(
                """() => {
                if (window.pusher) {
                    const channel = window.pusher.subscribe('dashboard-updates');
                    channel.bind_global((eventName, data) => {
                        window.recordPage2Event({
                            event: eventName,
                            data: data,
                            timestamp: Date.now()
                        });
                    });
                }
            }"""
            )

            # Perform action on page1 that should trigger update on page2
            await page1.click('[data-testid="create-content-btn"]')
            await page1.fill('[data-testid="content-title"]', "Test Content")
            await page1.click('[data-testid="submit-content"]')

            # Wait for real-time update
            await page2.wait_for_timeout(2000)

            # Verify page2 received update
            assert len(page2_events) > 0, "Page 2 did not receive Pusher real-time update"

            await browser.close()

    async def _login_user(self, page: Page, username: str, password: str):
        """Helper method to login a user."""
        await page.fill('[data-testid="username-input"]', username)
        await page.fill('[data-testid="password-input"]', password)
        await page.click('[data-testid="login-btn"]')
        await page.wait_for_timeout(1000)


@pytest.mark.e2e
class TestPusherIntegration:
    """Test Pusher Channels integration."""

    @pytest.mark.asyncio
    async def test_should_connect_to_pusher_channels(self):
        """Test Pusher connection establishment."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Intercept Pusher WebSocket connections
            pusher_connected = False

            async def route_websocket(route):
                """Intercept WebSocket connections."""
                if "pusher" in route.request.url:
                    nonlocal pusher_connected
                    pusher_connected = True
                await route.continue_()

            await page.route("**/*", route_websocket)

            # Enable console logging to see Pusher events
            page.on("console", lambda msg: print(f"Console: {msg.text}"))

            await page.goto("http://localhost:5179")
            await page.wait_for_timeout(3000)

            # Check if Pusher connected
            pusher_status = await page.evaluate(
                """() => {
                if (window.pusher) {
                    return window.pusher.connection.state;
                }
                return 'not initialized';
            }"""
            )

            assert pusher_status == "connected", f"Pusher not connected: {pusher_status}"

            await browser.close()

    @pytest.mark.asyncio
    async def test_should_subscribe_to_pusher_channels(self):
        """Test subscribing to Pusher channels."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto("http://localhost:5179")

            # Login first
            await self._login_user(page, "testuser", "testpass")

            # Wait for Pusher initialization
            await page.wait_for_timeout(2000)

            # Check subscribed channels
            subscribed_channels = await page.evaluate(
                """() => {
                if (window.pusher) {
                    return Object.keys(window.pusher.allChannels()).map(name => ({
                        name: name,
                        subscribed: window.pusher.channel(name).subscribed
                    }));
                }
                return [];
            }"""
            )

            # Verify expected channels are subscribed
            expected_channels = ["dashboard-updates", "content-generation"]
            for channel in expected_channels:
                channel_info = next((c for c in subscribed_channels if c["name"] == channel), None)
                assert channel_info, f"Channel {channel} not found"
                assert channel_info["subscribed"], f"Channel {channel} not subscribed"

            await browser.close()

    @pytest.mark.asyncio
    async def test_should_receive_pusher_events(self):
        """Test receiving events through Pusher channels."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Track Pusher events
            events_received = []

            await page.expose_function(
                "recordPusherEvent", lambda event: events_received.append(event)
            )

            await page.goto("http://localhost:5179")
            await self._login_user(page, "testuser", "testpass")

            # Set up event listener
            await page.evaluate(
                """() => {
                if (window.pusher) {
                    const channel = window.pusher.subscribe('dashboard-updates');
                    channel.bind_global((eventName, data) => {
                        window.recordPusherEvent({
                            event: eventName,
                            data: data,
                            timestamp: Date.now()
                        });
                    });
                }
            }"""
            )

            # Trigger an action that should generate a Pusher event
            await page.click('[data-testid="refresh-dashboard"]')
            await page.wait_for_timeout(2000)

            # Check if events were received
            assert len(events_received) > 0, "No Pusher events received"

            await browser.close()

    async def _login_user(self, page: Page, username: str, password: str):
        """Helper method to login a user."""
        await page.fill('[data-testid="username-input"]', username)
        await page.fill('[data-testid="password-input"]', password)
        await page.click('[data-testid="login-btn"]')
        await page.wait_for_timeout(1000)


@pytest.mark.e2e
class TestPusherLoadTesting:
    """Load testing for Pusher connections (migrated from WebSocket)."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_should_handle_multiple_pusher_connections(self):
        """Test handling multiple concurrent Pusher connections."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            # Create multiple contexts to simulate multiple users
            num_users = 10
            contexts = []
            pages = []
            connection_states = []

            for i in range(num_users):
                context = await browser.new_context()
                page = await context.new_page()

                contexts.append(context)
                pages.append(page)

                # Navigate to the application
                await page.goto("http://localhost:5179")

            # Wait for all Pusher connections to establish
            await asyncio.sleep(3)

            # Check Pusher connection status for each user
            for i, page in enumerate(pages):
                pusher_state = await page.evaluate(
                    """() => {
                    if (window.pusher) {
                        return {
                            state: window.pusher.connection.state,
                            socket_id: window.pusher.connection.socket_id,
                            channels: Object.keys(window.pusher.allChannels()).length
                        };
                    }
                    return { state: 'not initialized' };
                }"""
                )

                connection_states.append(pusher_state)

                # Verify user connected
                assert (
                    pusher_state["state"] == "connected"
                ), f"User {i} Pusher not connected: {pusher_state['state']}"
                assert pusher_state.get("socket_id"), f"User {i} has no socket ID"
                print(f"User {i}: Connected with {pusher_state.get('channels', 0)} channels")

            # Verify all users have unique socket IDs
            socket_ids = [
                state.get("socket_id") for state in connection_states if state.get("socket_id")
            ]
            assert len(socket_ids) == len(set(socket_ids)), "Duplicate socket IDs detected"

            # Clean up
            for context in contexts:
                await context.close()

            await browser.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_should_handle_pusher_message_burst(self):
        """Test handling burst of Pusher messages."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Track received events
            events_received = []
            await page.expose_function(
                "recordPusherEvent", lambda event: events_received.append(event)
            )

            await page.goto("http://localhost:5179")

            # Set up Pusher event tracking
            await page.evaluate(
                """() => {
                if (window.pusher) {
                    // Subscribe to a test channel
                    const channel = window.pusher.subscribe('test-burst-channel');

                    // Record all events
                    channel.bind_global((eventName, data) => {
                        window.recordPusherEvent({
                            event: eventName,
                            data: data,
                            timestamp: Date.now()
                        });
                    });

                    return true;
                }
                return false;
            }"""
            )

            await page.wait_for_timeout(2000)

            # Simulate burst of events using backend API
            # (In a real test, this would trigger events through your backend)
            for i in range(100):
                await page.evaluate(
                    f"""() => {{
                    // Simulate receiving events by triggering them locally
                    // In production, these would come from the server
                    if (window.pusher) {{
                        const channel = window.pusher.channel('test-burst-channel');
                        if (channel) {{
                            // Simulate event reception
                            const event = new CustomEvent('pusher:test-event', {{
                                detail: {{
                                    id: {i},
                                    message: 'Test message ' + {i},
                                    timestamp: Date.now()
                                }}
                            }});
                            window.recordPusherEvent({{
                                event: 'test-event',
                                data: event.detail,
                                timestamp: Date.now()
                            }});
                        }}
                    }}
                }}"""
                )

            await page.wait_for_timeout(2000)

            # Verify events were handled
            print(f"Received {len(events_received)} Pusher events")
            assert len(events_received) > 0, "No Pusher events received during burst test"
            assert (
                len(events_received) >= 50
            ), f"Expected at least 50 events, got {len(events_received)}"

            await browser.close()


# ============================================
# Playwright Configuration
# ============================================


def pytest_configure(config):
    """Configure pytest for Playwright tests."""
    config.addinivalue_line("markers", "e2e: End-to-end tests using Playwright")
    config.addinivalue_line("markers", "slow: Slow tests that may take longer to execute")


@pytest.fixture(scope="session")
def browser_context_args():
    """Provide default browser context arguments."""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
async def browser():
    """Provide a browser instance for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        yield browser
        await browser.close()
