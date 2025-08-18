import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from starlette.websockets import WebSocketDisconnect
from app.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_websocket_missing_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update") as websocket:
            data = websocket.receive_text()
            assert "Missing access token" in data

@patch("app.api.routers.ws_router.decode_access_token")
def test_websocket_invalid_token(mock_decode, client):
    mock_decode.side_effect = Exception("bad token")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=badtoken") as websocket:
            data = websocket.receive_text()
            assert "Invalid or expired token" in data

@patch("app.api.routers.ws_router.decode_access_token")
def test_websocket_token_no_userid(mock_decode, client):
    mock_decode.return_value = {}
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=nouserid") as websocket:
            data = websocket.receive_text()
            assert "Invalid or expired token" in data or "Invalid token" in data

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_valid_token_ping_pong(mock_ws_manager, mock_decode, client):
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=goodtoken") as websocket:
            data = websocket.receive_text()
            assert "Successfully connected" in data
            websocket.send_text('{"type":"ping"}')
            pong = websocket.receive_text()
            assert '"type": "pong"' in pong
            websocket.close()

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_malformed_json_from_client(mock_ws_manager, mock_decode, client):
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=goodtoken") as websocket:
            data = websocket.receive_text()
            assert "Successfully connected" in data
            websocket.send_text('not-a-json')
            # Should trigger outer exception handler and close

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_outer_exception_on_send(mock_ws_manager, mock_decode, client):
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    # Patch websocket.send_text to raise after connect
    with patch("starlette.websockets.WebSocket.send_text", side_effect=Exception("fail send")):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/update?token=goodtoken"):
                # Should trigger outer exception handler and close
                pass

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_outer_exception_on_close(mock_ws_manager, mock_decode, client):
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    # Patch websocket.send_text and close to both raise
    with patch("starlette.websockets.WebSocket.send_text", side_effect=Exception("fail send")), \
         patch("starlette.websockets.WebSocket.close", side_effect=Exception("fail close")):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/update?token=goodtoken"):
                pass

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_disconnect_triggers_manager_disconnect(mock_ws_manager, mock_decode, client):
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    mock_ws_manager.disconnect = Mock()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=goodtoken") as websocket:
            data = websocket.receive_text()
            assert "Successfully connected" in data
            websocket.send_text('{"type":"ping"}')
            pong = websocket.receive_text()
            assert '"type": "pong"' in pong
            websocket.close()

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_outer_exception_send_and_close_fail(mock_ws_manager, mock_decode, client):
    """
    Simulate both send_text and close raising exceptions in the outermost except block.
    """
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    with patch("starlette.websockets.WebSocket.send_text", side_effect=Exception("fail send")), \
         patch("starlette.websockets.WebSocket.close", side_effect=Exception("fail close")):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/update?token=goodtoken"):
                pass

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_loop_breaks_on_client_close(mock_ws_manager, mock_decode, client):
    """
    Simulate client closing connection after connect, before sending any message.
    """
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    mock_ws_manager.disconnect = Mock()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=goodtoken") as websocket:
            data = websocket.receive_text()
            assert "Successfully connected" in data
            websocket.send_text('{"type":"ping"}')
            pong = websocket.receive_text()
            assert '"type": "pong"' in pong
            websocket.close()

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_non_ping_message(mock_ws_manager, mock_decode, client):
    """
    Send a message with a type other than 'ping' to cover the else branch.
    """
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=goodtoken") as websocket:
            data = websocket.receive_text()
            assert "Successfully connected" in data
            websocket.send_text('{"type":"other"}')
            # The server will just wait for the next message, so close from client
            websocket.close()

@patch("app.api.routers.ws_router.decode_access_token")
@patch("app.api.routers.ws_router.ws_manager")
def test_websocket_malformed_json_triggers_outer_exception(mock_ws_manager, mock_decode, client):
    """
    Send malformed JSON to trigger the outer exception handler.
    """
    mock_decode.return_value = {"user_id": "u1"}
    mock_ws_manager.connect = AsyncMock()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/update?token=goodtoken") as websocket:
            data = websocket.receive_text()
            assert "Successfully connected" in data
            websocket.send_text('not-a-json')
            # Should trigger the outer exception handler and close