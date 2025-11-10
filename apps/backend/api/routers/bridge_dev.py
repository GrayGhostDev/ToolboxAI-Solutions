"""
Development Bridge Endpoints (Pusher Relay + Plugin Polling)

These endpoints provide a minimal local bridge for the Studio plugin during development.
In production, a dedicated bridge service should implement these with proper auth and Pusher relay.
"""

from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

router = APIRouter(tags=["Dev Bridge"])


class Message(BaseModel):
    id: str
    timestamp: float
    plugin_id: str
    studio_id: str
    data: Dict[str, Any]


_SESSIONS: Dict[str, Dict[str, Any]] = {}
_QUEUES: Dict[str, List[Message]] = {}


@router.post("/register_plugin")
def register_plugin(payload: Dict[str, Any] = Body(...)):
    studio_id = payload.get("studio_id") or "studio"
    session_id = f"session_{int(datetime.utcnow().timestamp())}"
    _SESSIONS[session_id] = {
        "studio_id": studio_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    _QUEUES.setdefault(session_id, [])
    return {"success": True, "session_id": session_id}


@router.post("/unregister_plugin")
def unregister_plugin(payload: Dict[str, Any] = Body(...)):
    session_id = payload.get("session_id")
    _SESSIONS.pop(session_id, None)
    _QUEUES.pop(session_id, None)
    return {"success": True}


@router.post("/plugin/send-message")
def plugin_send_message(msg: Message):
    # In dev, enqueue so polling can see it; production should trigger Pusher
    _QUEUES.setdefault(msg.plugin_id, []).append(msg)
    return {"success": True}


@router.post("/plugin/messages")
def plugin_messages(payload: Dict[str, Any] = Body(...)):
    plugin_id = payload.get("plugin_id")
    messages = _QUEUES.get(plugin_id, [])
    _QUEUES[plugin_id] = []
    return {"messages": [m.model_dump() for m in messages]}


@router.get("/pusher/status")
def pusher_status():
    # Report a static OK status for dev; production should return real state
    return {
        "connected": True,
        "cluster": "mt1",
        "channel": "toolboxai-dev",
        "since": datetime.utcnow().isoformat() + "Z",
    }

