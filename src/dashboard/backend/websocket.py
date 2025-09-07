"""
WebSocket Server Implementation using Socket.IO
Handles real-time communication for the educational platform
"""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import jwt
import socketio
from fastapi import HTTPException
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Create async Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Allow all origins for development
    logger=True,
    engineio_logger=True,  # Enable Engine.IO logging for debugging
    ping_timeout=60,
    ping_interval=25
)

# Create ASGI app
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io'
)

# Store active connections and user sessions
active_connections: Dict[str, Dict[str, Any]] = {}
user_rooms: Dict[str, set] = {}


async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== Connection Handlers ====================

@sio.event
async def connect(sid, environ, auth):
    """Handle new WebSocket connection"""
    try:
        # Extract token from auth
        token = auth.get('token') if auth else None
        
        if not token:
            print(f"Connection rejected for {sid}: No token provided")
            return False
        
        # Verify token
        user_data = await verify_token(token)
        if not user_data:
            print(f"Connection rejected for {sid}: Invalid token")
            return False
        
        # Store connection info
        active_connections[sid] = {
            'user_id': user_data.get('sub'),
            'email': user_data.get('email'),
            'role': user_data.get('role'),
            'connected_at': datetime.now().isoformat()
        }
        
        user_rooms[sid] = set()
        
        print(f"User {user_data.get('email')} connected with session {sid}")
        
        # Send connection confirmation
        await sio.emit('connected', {
            'message': 'Successfully connected to WebSocket server',
            'session_id': sid,
            'user': {
                'id': user_data.get('sub'),
                'email': user_data.get('email'),
                'role': user_data.get('role')
            }
        }, room=sid)
        
        return True
        
    except Exception as e:
        print(f"Connection error for {sid}: {str(e)}")
        return False


@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection"""
    try:
        user_info = active_connections.get(sid)
        if user_info:
            print(f"User {user_info.get('email')} disconnected from session {sid}")
            
            # Leave all rooms
            if sid in user_rooms:
                for room in user_rooms[sid]:
                    await sio.leave_room(sid, room)
                del user_rooms[sid]
            
            # Remove from active connections
            del active_connections[sid]
    except Exception as e:
        print(f"Disconnect error for {sid}: {str(e)}")


# ==================== Room Management ====================

@sio.event
async def join_room(sid, data):
    """Join a specific room (e.g., class room)"""
    try:
        room_id = data.get('roomId')
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required'}, room=sid)
            return
        
        user_info = active_connections.get(sid)
        if not user_info:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return
        
        # Join the room
        await sio.enter_room(sid, room_id)
        user_rooms[sid].add(room_id)
        
        # Notify the room
        await sio.emit('user_joined', {
            'userId': user_info['user_id'],
            'email': user_info['email'],
            'role': user_info['role'],
            'roomId': room_id
        }, room=room_id)
        
        # Confirm to user
        await sio.emit('room_joined', {
            'roomId': room_id,
            'message': f'Successfully joined room {room_id}'
        }, room=sid)
        
        print(f"User {user_info['email']} joined room {room_id}")
        
    except Exception as e:
        print(f"Join room error for {sid}: {str(e)}")
        await sio.emit('error', {'message': 'Failed to join room'}, room=sid)


@sio.event
async def leave_room(sid, data):
    """Leave a specific room"""
    try:
        room_id = data.get('roomId')
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required'}, room=sid)
            return
        
        user_info = active_connections.get(sid)
        if not user_info:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return
        
        # Leave the room
        await sio.leave_room(sid, room_id)
        if sid in user_rooms:
            user_rooms[sid].discard(room_id)
        
        # Notify the room
        await sio.emit('user_left', {
            'userId': user_info['user_id'],
            'email': user_info['email'],
            'roomId': room_id
        }, room=room_id)
        
        # Confirm to user
        await sio.emit('room_left', {
            'roomId': room_id,
            'message': f'Successfully left room {room_id}'
        }, room=sid)
        
        print(f"User {user_info['email']} left room {room_id}")
        
    except Exception as e:
        print(f"Leave room error for {sid}: {str(e)}")
        await sio.emit('error', {'message': 'Failed to leave room'}, room=sid)


# ==================== Gamification Events ====================

@sio.event
async def request_leaderboard(sid, data):
    """Request leaderboard update"""
    try:
        class_id = data.get('classId')
        user_info = active_connections.get(sid)
        
        if not user_info:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return
        
        # In a real implementation, fetch from database
        # For now, send mock leaderboard data
        leaderboard_data = {
            'classId': class_id,
            'leaderboard': [
                {'rank': 1, 'userId': 'user1', 'name': 'John Doe', 'xp': 1500, 'level': 15},
                {'rank': 2, 'userId': 'user2', 'name': 'Jane Smith', 'xp': 1200, 'level': 12},
                {'rank': 3, 'userId': 'user3', 'name': 'Bob Johnson', 'xp': 900, 'level': 9},
            ],
            'userRank': {
                'rank': 4,
                'userId': user_info['user_id'],
                'xp': 800,
                'level': 8
            }
        }
        
        await sio.emit('leaderboard_update', leaderboard_data, room=sid)
        
    except Exception as e:
        print(f"Leaderboard request error for {sid}: {str(e)}")
        await sio.emit('error', {'message': 'Failed to fetch leaderboard'}, room=sid)


# ==================== Heartbeat/Health Check ====================

@sio.event
async def ping(sid):
    """Respond to ping with pong"""
    await sio.emit('pong', room=sid)


@sio.event
async def heartbeat(sid):
    """Handle heartbeat from client"""
    try:
        user_info = active_connections.get(sid)
        if user_info:
            user_info['last_heartbeat'] = datetime.now().isoformat()
            print(f"Heartbeat received from {user_info['email']}")
    except Exception as e:
        print(f"Heartbeat error for {sid}: {str(e)}")


@sio.event
async def pong(sid):
    """Handle pong response from client"""
    pass


# ==================== Broadcast Functions ====================

async def broadcast_notification(user_id: str, notification: Dict[str, Any]):
    """Broadcast notification to a specific user"""
    for sid, user_info in active_connections.items():
        if user_info['user_id'] == user_id:
            await sio.emit('notification', notification, room=sid)


async def broadcast_to_class(class_id: str, event: str, data: Dict[str, Any]):
    """Broadcast event to all users in a class"""
    await sio.emit(event, data, room=class_id)


async def broadcast_xp_update(user_id: str, xp_data: Dict[str, Any]):
    """Broadcast XP update to a user"""
    for sid, user_info in active_connections.items():
        if user_info['user_id'] == user_id:
            await sio.emit('xp_gained', xp_data, room=sid)


async def broadcast_badge_earned(user_id: str, badge_data: Dict[str, Any]):
    """Broadcast badge earned event to a user"""
    for sid, user_info in active_connections.items():
        if user_info['user_id'] == user_id:
            await sio.emit('badge_earned', badge_data, room=sid)


async def broadcast_class_online(class_id: str, class_data: Dict[str, Any]):
    """Broadcast when a class comes online"""
    await sio.emit('class_online', class_data, room=class_id)


async def broadcast_assignment_due(class_id: str, assignment_data: Dict[str, Any]):
    """Broadcast assignment due reminder"""
    await sio.emit('assignment_due', assignment_data, room=class_id)


# ==================== Monitoring Functions ====================

async def get_active_connections_count() -> int:
    """Get count of active connections"""
    return len(active_connections)


async def get_active_users() -> list:
    """Get list of active users"""
    return [
        {
            'user_id': info['user_id'],
            'email': info['email'],
            'role': info['role'],
            'connected_at': info['connected_at']
        }
        for info in active_connections.values()
    ]


async def cleanup_stale_connections():
    """Clean up stale connections (to be called periodically)"""
    current_time = datetime.now()
    stale_threshold = 300  # 5 minutes
    
    for sid in list(active_connections.keys()):
        user_info = active_connections[sid]
        last_heartbeat = user_info.get('last_heartbeat')
        
        if last_heartbeat:
            last_heartbeat_time = datetime.fromisoformat(last_heartbeat)
            if (current_time - last_heartbeat_time).seconds > stale_threshold:
                print(f"Removing stale connection for {user_info['email']}")
                await sio.disconnect(sid)


# Export the Socket.IO app
__all__ = ['socket_app', 'sio', 'broadcast_notification', 'broadcast_to_class', 
           'broadcast_xp_update', 'broadcast_badge_earned', 'broadcast_class_online',
           'broadcast_assignment_due', 'get_active_connections_count', 'get_active_users']