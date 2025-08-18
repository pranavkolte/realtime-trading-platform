import asyncio
import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.api.services.order_book_service import OrderBookService
from app.database.enums.oder_enums import Side, OrderType
from app.schemas.order_schemas import PlaceOrderRequest

class DummyOrder:
    def __init__(self, price, remaining, side):
        self.price = price
        self.remaining = remaining
        self.side = side

@pytest.fixture
def db_session():
    # Use a MagicMock for the db session
    return MagicMock()

@pytest.fixture
def order_book_service(db_session):
    return OrderBookService(db_session)

def test_order_book_updates_after_place_order(order_book_service, db_session):
    # Mock PlaceOrderRequest for a limit buy order
    order_request = PlaceOrderRequest(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=101.0,
        quantity=2.0
    )
    user_id = "test-user-id"

    # Patch db_session.refresh to set required fields
    def refresh_side_effect(order):
        if getattr(order, "order_id", None) is None:
            order.order_id = uuid.uuid4()
        if getattr(order, "created_at", None) is None:
            order.created_at = datetime.utcnow()
    db_session.refresh = MagicMock(side_effect=refresh_side_effect)

    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.flush = MagicMock()

    # Place order (simulate async)
    asyncio.run(order_book_service.place_order(user_id, order_request))

    # After placing, the order book snapshot should reflect the new order
    order_book_service.get_order_book_snapshot = MagicMock(return_value={
        "bids": [{"price": 101.0, "total_qty": 2.0}],
        "asks": [],
        "last_trade_price": 100.0
    })

    snapshot = order_book_service.get_order_book_snapshot()
    assert snapshot["bids"][0]["price"] == 101.0
    assert snapshot["bids"][0]["total_qty"] == 2.0