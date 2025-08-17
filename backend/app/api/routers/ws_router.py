from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import json

from app.api.services.ws_service import ws_manager
from app.util.auth_util import decode_access_token

router = APIRouter()
security = HTTPBearer()

@router.websocket("/update")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for real-time trading updates
    Requires access_token as query parameter: /update?token=your_access_token
    """
    try:
        # Accept connection first
        await websocket.accept()
        
        # Validate token
        if not token:
            await websocket.send_text(json.dumps({
                "event": "error",
                "message": "Missing access token. Use ?token=your_access_token"
            }))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Decode and validate token
        try:
            payload = decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            await websocket.send_text(json.dumps({
                "event": "error", 
                "message": "Invalid or expired token",
                "details": str(e)
            }))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Add client to manager
        await ws_manager.connect(websocket, user_id)
        
        # Send connection success message
        await websocket.send_text(json.dumps({
            "event": "connected",
            "message": "Successfully connected to trading WebSocket",
            "user_id": user_id
        }))
        
        # Keep connection alive and handle messages
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed (ping/pong, subscriptions, etc.)
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, user_id)
            
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "event": "error",
                "message": str(e)
            }))
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
        