import json
import pytest
from unittest.mock import AsyncMock

import os
os.environ['TESTING'] = 'true'
os.environ['SKIP_AGENTS'] = 'true'

from apps.backend.services.socketio import sio as sio_srv, connected_clients, content_request, ping
from apps.backend.core.config import settings
from apps.backend.services.rate_limit_manager import get_rate_limit_manager
from apps.backend.core.security.rate_limit_manager import RateLimitMode


@pytest.mark.asyncio(loop_scope="function")
async def test_socketio_rbac_blocks_teacher_event_for_student(monkeypatch):
    # Save originals
    original_roles = dict(getattr(settings, "SIO_RBAC_REQUIRED_ROLES", {}))
    try:
        # Require teacher role for content_request
        settings.SIO_RBAC_REQUIRED_ROLES = {"content_request": "teacher"}

        # Prepare connected client with student role
        sid = "sid-student-1"
        connected_clients[sid] = {
            "authenticated": True,
            "user_id": "u-student",
            "role": "student",
        }

        # Patch emit to capture emissions
        emit_mock = AsyncMock()
        monkeypatch.setattr(sio_srv, "emit", emit_mock)

        # Attempt teacher-only event - call the handler function directly
        await content_request(sid, {"topic": "Math"})

        # Expect an error emission with Forbidden
        assert emit_mock.await_count >= 1
        # Find last call args
        called_with = None
        for call in emit_mock.await_args_list:
            if call.args and call.args[0] == "error":
                called_with = call
        assert called_with is not None, "Expected an 'error' event emission"
        payload = called_with.args[1]
        assert isinstance(payload, dict)
        assert "Forbidden" in payload.get("error", "")
    finally:
        settings.SIO_RBAC_REQUIRED_ROLES = original_roles
        connected_clients.pop("sid-student-1", None)


@pytest.mark.asyncio(loop_scope="function")
async def test_socketio_rate_limit_enforced_for_ping(monkeypatch):
    # Configure tight rate limit
    original_limit = getattr(settings, "SIO_RATE_LIMIT_PER_MINUTE", 100)
    settings.SIO_RATE_LIMIT_PER_MINUTE = 1
    rlm = get_rate_limit_manager()
    rlm.set_mode(RateLimitMode.PRODUCTION)
    rlm.clear_all_limits()
    
    try:
        sid = "sid-rate-1"
        connected_clients[sid] = {
            "authenticated": True,
            "user_id": "u-rl",
            "role": "student",
        }

        emit_mock = AsyncMock()
        monkeypatch.setattr(sio_srv, "emit", emit_mock)

        # First ping allowed - call the handler function directly
        await ping(sid, None)
        # Second ping should be rate limited
        await ping(sid, None)

        # Ensure rate limit error was emitted
        # Look for an 'error' event with 'Rate limit' text
        found_rate_error = False
        for call in emit_mock.await_args_list:
            if call.args and call.args[0] == "error":
                if "Rate limit" in call.args[1].get("error", ""):
                    found_rate_error = True
                    break
        assert found_rate_error, "Expected a rate limit error emission on second ping"
    finally:
        settings.SIO_RATE_LIMIT_PER_MINUTE = original_limit
        rlm.clear_all_limits()
        connected_clients.pop("sid-rate-1", None)

