import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime

from app.api.routers.order_routers import router

from fastapi import FastAPI

app = FastAPI()
app.include_router(router)


@pytest.fixture
def mock_user():
    class User:
        user_id = "test-user"

    return User()


@pytest.fixture
def mock_admin():
    class Admin:
        user_id = "admin"

    return Admin()


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_order_service():
    mock = MagicMock()
    mock.cancel_order = MagicMock()
    mock.get_order_book_snapshot = MagicMock()
    mock.get_user_orders = MagicMock()
    mock.get_recent_trades = MagicMock()
    return mock


@pytest.fixture
def mock_ws_manager():
    mock = MagicMock()
    mock.broadcast_message = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
def override_dependencies(
    mock_user, mock_admin, mock_db, mock_order_service, mock_ws_manager
):
    from app.api.routers import order_routers

    app.dependency_overrides = {}
    app.dependency_overrides[order_routers.get_current_user] = (
        lambda: mock_user
    )
    app.dependency_overrides[order_routers.get_current_admin_user] = (
        lambda: mock_admin
    )
    app.dependency_overrides[order_routers.get_db_session] = lambda: mock_db
    order_routers.OrderBookService = lambda db: mock_order_service
    order_routers.ws_service = mock_ws_manager


@pytest.mark.asyncio
async def test_cancel_order_success(mock_order_service, mock_ws_manager):
    mock_order_service.cancel_order.return_value = True
    (
        mock_order_service
        .get_order_book_snapshot.return_value
        .dict.return_value
    ) = {
        "bids": [],
        "asks": [],
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/cancel/123")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order_id"] == "123"
    mock_ws_manager.broadcast_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_order_not_found(mock_order_service):
    mock_order_service.cancel_order.return_value = False
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/cancel/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_order_exception(mock_order_service):
    mock_order_service.cancel_order.side_effect = Exception("fail")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/cancel/1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to cancel order" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_orders_success(mock_order_service):
    # Use correct enum values as per your schemas (likely uppercase)
    mock_order_service.get_user_orders.return_value = [
        {
            "id": str(uuid.uuid4()),
            "side": "BUY",  # must be uppercase
            "order_type": "LIMIT",  # must be uppercase
            "price": 100.0,
            "quantity": 10.0,
            "remaining": 5.0,
            "status": "OPEN",  # must be uppercase
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
    ]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/my-orders")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert response.json()[0]["side"] == "BUY"


@pytest.mark.asyncio
async def test_get_my_orders_exception(mock_order_service):
    mock_order_service.get_user_orders.side_effect = Exception("fail")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/my-orders")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to get orders" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_order_book_success(mock_order_service):
    mock_order_service.get_order_book_snapshot.return_value = {
        "bids": [],
        "asks": [],
        "last_trade_price": 100.0,
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/book")
    assert response.status_code == status.HTTP_200_OK
    assert "bids" in response.json()


@pytest.mark.asyncio
async def test_get_order_book_exception(mock_order_service):
    mock_order_service.get_order_book_snapshot.side_effect = Exception("fail")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/book")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to get order book" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_recent_trades_success(mock_order_service):
    # engine_trade_id should be int, not str!
    mock_order_service.get_recent_trades.return_value = [
        {
            "id": str(uuid.uuid4()),
            "engine_trade_id": 123,  # must be int
            "price": 100.0,
            "quantity": 1.0,
            "buy_order_id": str(uuid.uuid4()),
            "sell_order_id": str(uuid.uuid4()),
            "buy_user_id": str(uuid.uuid4()),
            "sell_user_id": str(uuid.uuid4()),
            "ts": datetime.utcnow().isoformat(),
        }
    ]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/recent-trades")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert "price" in response.json()[0]


@pytest.mark.asyncio
async def test_get_recent_trades_exception(mock_order_service):
    mock_order_service.get_recent_trades.side_effect = Exception("fail")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/recent-trades")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to get recent trades" in response.json()["detail"]
