import pytest
from unittest.mock import AsyncMock
from app.api.services.ws_service import WebSocketManager
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

@pytest.fixture
def ws_manager():
    return WebSocketManager()

@pytest.fixture
def fake_websocket():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws

@pytest.mark.asyncio
async def test_connect_and_disconnect_adds_and_removes(ws_manager, fake_websocket):
    user_id = "user1"
    await ws_manager.connect(fake_websocket, user_id)
    assert user_id in ws_manager.active_connections
    assert fake_websocket in ws_manager.active_connections[user_id]
    assert fake_websocket in ws_manager.all_connections
    ws_manager.disconnect(fake_websocket, user_id)
    assert user_id not in ws_manager.active_connections
    assert fake_websocket not in ws_manager.all_connections

@pytest.mark.asyncio
async def test_send_personal_message_success(ws_manager, fake_websocket):
    user_id = "user2"
    ws_manager.active_connections[user_id] = [fake_websocket]
    msg = {"foo": "bar"}
    await ws_manager.send_personal_message(msg, user_id)
    fake_websocket.send_text.assert_called_once()

@pytest.mark.asyncio
async def test_send_personal_message_disconnect_on_error(ws_manager, fake_websocket):
    user_id = "user3"
    fake_websocket.send_text.side_effect = Exception("fail")
    ws_manager.active_connections[user_id] = [fake_websocket]
    await ws_manager.send_personal_message({"foo": "bar"}, user_id)
    assert fake_websocket not in ws_manager.active_connections.get(user_id, [])

@pytest.mark.asyncio
async def test_broadcast_message_success(ws_manager, fake_websocket):
    ws_manager.all_connections = [fake_websocket]
    ws_manager.active_connections["user4"] = [fake_websocket]
    await ws_manager.broadcast_message({"event": "test"})
    fake_websocket.send_text.assert_called_once()

@pytest.mark.asyncio
async def test_broadcast_message_disconnect_on_error(ws_manager, fake_websocket):
    fake_websocket.send_text.side_effect = Exception("fail")
    ws_manager.all_connections = [fake_websocket]
    ws_manager.active_connections["user5"] = [fake_websocket]
    await ws_manager.broadcast_message({"event": "test"})
    assert fake_websocket not in ws_manager.active_connections.get("user5", [])

@pytest.mark.asyncio
async def test_send_order_status_update_calls_personal(ws_manager):
    user_id = "user6"
    ws_manager.send_personal_message = AsyncMock()
    await ws_manager.send_order_status_update(user_id, {"order": 1})
    ws_manager.send_personal_message.assert_called_once()
    args = ws_manager.send_personal_message.call_args[0][0]
    assert "event" in args or "order" in str(args)

@pytest.mark.asyncio
async def test_broadcast_price_change_calls_broadcast(ws_manager):
    ws_manager.broadcast_message = AsyncMock()
    now = datetime.utcnow()
    await ws_manager.broadcast_price_change(123.45, now)
    ws_manager.broadcast_message.assert_called_once()
    msg = ws_manager.broadcast_message.call_args[0][0]
    assert msg["event"] == "price_change"

def test_json_serializer_decimal(ws_manager):
    assert ws_manager._json_serializer(Decimal("1.23")) == 1.23

def test_json_serializer_datetime(ws_manager):
    now = datetime.utcnow()
    assert ws_manager._json_serializer(now) == now.isoformat()

def test_json_serializer_uuid(ws_manager):
    uid = uuid4()
    assert ws_manager._json_serializer(uid) == str(uid)

def test_json_serializer_type_error(ws_manager):
    class Foo: 
        pass
    with pytest.raises(TypeError):
        ws_manager._json_serializer(Foo())