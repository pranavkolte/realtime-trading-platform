from fastapi import WebSocket
from typing import Dict, List
import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class WebSocketManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store all connections for broadcasting
        self.all_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        self.all_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Remove user entry if no connections left
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        if websocket in self.all_connections:
            self.all_connections.remove(websocket)

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id][
                :
            ]:  # Create a copy to iterate
                try:
                    await connection.send_text(
                        json.dumps(message, default=self._json_serializer)
                    )
                except Exception:
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.all_connections:
            return

        disconnected = []
        successful_sends = 0

        for connection in self.all_connections[:]:  # Create a copy to iterate
            try:
                await connection.send_text(
                    json.dumps(message, default=self._json_serializer)
                )
                successful_sends += 1
            except Exception:
                disconnected.append(connection)

        # Remove disconnected connections
        for conn in disconnected:
            # Find user_id for this connection
            user_to_disconnect = None
            for user_id, connections in self.active_connections.items():
                if conn in connections:
                    user_to_disconnect = user_id
                    break

            if user_to_disconnect:
                self.disconnect(conn, user_to_disconnect)

    async def send_order_status_update(self, user_id: str, order_data: dict):
        """Send order status update to specific user"""
        message = {
            "event": "order_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": order_data,
        }
        await self.send_personal_message(message, user_id)

    async def broadcast_price_change(self, price: float, timestamp):
        """Broadcast price change event to all clients"""
        message = {
            "event": "price_change",
            "timestamp": timestamp.isoformat(),
            "data": {"price": price, "timestamp": timestamp.isoformat()},
        }
        await self.broadcast_message(message)

    def _json_serializer(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        raise TypeError(
            f"Object of type '{type(obj).__name__}' is not JSON serializable"
        )


# Global WebSocket manager instance
ws_manager = WebSocketManager()
