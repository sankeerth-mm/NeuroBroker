import json
import asyncio
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from backend.app.logging.logger import broker_logger

class UserWebSocketManager:
    def __init__(self):
        # Maps user_id or 'all' to set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {"all": set()}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str = "all"):
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            self.active_connections["all"].add(websocket)
        broker_logger.debug(f"User WebSocket connected: {user_id}")

    async def disconnect(self, websocket: WebSocket, user_id: str = "all"):
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
            self.active_connections["all"].discard(websocket)
        broker_logger.debug(f"User WebSocket disconnected: {user_id}")

    async def broadcast(self, event_type: str, data: Any, user_id: str = "all"):
        """Broadcast real-time event message to specific user or all connected dashboards."""
        payload = {
            "event": event_type,
            "data": data,
        }
        message_str = json.dumps(payload, default=str)
        
        async with self._lock:
            targets = list(self.active_connections.get(user_id, set()))
        
        dead_connections = []
        for connection in targets:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                dead_connections.append(connection)
        
        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    if user_id in self.active_connections:
                        self.active_connections[user_id].discard(dead)
                    self.active_connections["all"].discard(dead)

user_ws_manager = UserWebSocketManager()
