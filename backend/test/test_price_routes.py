import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from unittest.mock import MagicMock

from app.api.routers.price_routers import router

app = FastAPI()
app.include_router(router, prefix="/price")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture(autouse=True)
def override_dependencies(mock_db):
    from app.api.routers import price_routers

    app.dependency_overrides = {}
    app.dependency_overrides[price_routers.get_db_session] = lambda: mock_db


def make_price_obj(id, ts=1234567890):
    price = MagicMock()
    price.id = id
    price.timestamp = ts
    price.value = 100 + id
    return price


@pytest.mark.asyncio
async def test_get_price_data_empty(mock_db):
    mock_db.query().order_by().limit().all.return_value = []
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/price/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_price_data_nonempty(monkeypatch, mock_db):
    price_obj = make_price_obj(1)
    # Patch PriceHistoryResponse and PriceHistory.from_orm to return dicts
    from app.api.routers import price_routers

    monkeypatch.setattr(
        price_routers.PriceHistory, "from_orm", staticmethod(lambda x: x)
    )
    monkeypatch.setattr(
        price_routers,
        "PriceHistoryResponse",
        lambda price: {
            "price": {
                "id": price.id,
                "timestamp": price.timestamp,
                "value": price.value,
            }
        },
    )
    mock_db.query().order_by().limit().all.return_value = [price_obj]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/price/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["price"]["id"] == 1


@pytest.mark.asyncio
async def test_get_price_data_limit_param(mock_db):
    mock_db.query().order_by().limit().all.return_value = []
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/price/?limit=10")
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_price_data_limit_validation(mock_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/price/?limit=0")
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
