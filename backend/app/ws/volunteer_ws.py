import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any, Callable
from fastapi import WebSocket, WebSocketDisconnect
from backend.app.logging.logger import broker_logger, log_event
from backend.app.ws.user_ws import user_ws_manager

class VolunteerWebSocketManager:
    def __init__(self):
        # Maps node_id -> WebSocket
        self.active_nodes: Dict[str, WebSocket] = {}
        # Callbacks registered for task updates
        self.task_callbacks: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    async def connect(self, node_id: str, websocket: WebSocket):
        async with self._lock:
            self.active_nodes[node_id] = websocket
        broker_logger.info(f"Volunteer Node WebSocket connected: {node_id}")
        await user_ws_manager.broadcast("node_connected", {"node_id": node_id, "timestamp": datetime.utcnow().isoformat()})

    async def disconnect(self, node_id: str, websocket: Optional[WebSocket] = None):
        async with self._lock:
            if node_id in self.active_nodes:
                if websocket is None or self.active_nodes[node_id] == websocket:
                    del self.active_nodes[node_id]
        broker_logger.warning(f"Volunteer Node WebSocket disconnected: {node_id}")
        await user_ws_manager.broadcast("node_disconnected", {"node_id": node_id, "timestamp": datetime.utcnow().isoformat()})

    def is_node_connected(self, node_id: str) -> bool:
        return node_id in self.active_nodes

    async def send_to_node(self, node_id: str, message_type: str, payload: Dict[str, Any]) -> bool:
        """Send message directly to a specific connected volunteer node."""
        async with self._lock:
            ws = self.active_nodes.get(node_id)
        
        if not ws:
            broker_logger.warning(f"Cannot send to {node_id}: Node not connected via WebSocket")
            return False
        
        message = {
            "type": message_type,
            "data": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await ws.send_text(json.dumps(message))
            return True
        except Exception as e:
            broker_logger.error(f"Error sending to node {node_id}: {e}")
            await self.disconnect(node_id)
            return False

volunteer_ws_manager = VolunteerWebSocketManager()
