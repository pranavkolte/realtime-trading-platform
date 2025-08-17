import json

from fastapi import WebSocket

class WsService:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        to_drop = []
        for ws in self.active:
            try:
                await ws.send_text(data)
            except Exception:
                to_drop.append(ws)
        for ws in to_drop:
            self.disconnect(ws)
