import pytest

from uuid import uuid4
from datetime import datetime

from app.database.models import order_models, trade_models, user_models  # noqa: F401

from app.api.services.order_matching_service import OrderMatchingEngine, TradeResult  # noqa: F401
from app.database.enums.oder_enums import Side, OrderType, OrderStatus
from app.database.models.order_models import Order

@pytest.fixture
def engine():
    return OrderMatchingEngine()

def make_order(
    side,
    price,
    quantity,
    order_type=OrderType.LIMIT,
    status=OrderStatus.OPEN,
    remaining=None,
    active=True,
    created_at=None,
):
    return Order(
        order_id=uuid4(),
        user_id=uuid4(),
        side=side,
        price=price,
        quantity=quantity,
        remaining=quantity if remaining is None else remaining,
        order_type=order_type,
        status=status,
        active=active,
        created_at=created_at or datetime.utcnow(),
    )

def test_limit_order_match(engine):
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0)

    # Add buy order first (goes to book)
    trades1 = engine.add_order(buy_order)
    assert trades1 == []
    assert engine.get_order_book_snapshot()["bids"][0]["price"] == 100.0

    # Add sell order (should match with buy)
    trades2 = engine.add_order(sell_order)
    assert len(trades2) == 1
    trade = trades2[0]
    assert trade.price == 100.0
    assert trade.quantity == 1.0
    assert trade.buy_order_status == OrderStatus.FILLED
    assert trade.sell_order_status == OrderStatus.FILLED

    # Both orders should be filled and not in the book
    assert engine.get_order_book_snapshot()["bids"] == []
    assert engine.get_order_book_snapshot()["asks"] == []

def test_market_order_match(engine):
    # Add a limit sell order to the book
    sell_order = make_order(Side.SELL, price=101.0, quantity=2.0)
    engine.add_order(sell_order)
    assert engine.get_order_book_snapshot()["asks"][0]["price"] == 101.0

    # Add a market buy order (should match with the limit sell order)
    market_buy = make_order(Side.BUY, price=0, quantity=1.5, order_type=OrderType.MARKET)
    trades = engine.add_order(market_buy)
    assert len(trades) == 1
    trade = trades[0]
    assert trade.price == 101.0  # Market order takes the limit order price
    assert trade.quantity == 1.5
    assert trade.buy_order_status == OrderStatus.FILLED
    assert trade.sell_order_status == OrderStatus.PARTIALLY_FILLED

    # Remaining sell order should be in the book with reduced quantity
    asks = engine.get_order_book_snapshot()["asks"]
    assert asks[0]["price"] == 101.0
    assert asks[0]["total_qty"] == 0.5

def test_market_order_no_match(engine):
    # No sell orders in the book, so market buy should not match and should be cancelled or remain unfilled
    market_buy = make_order(Side.BUY, price=0, quantity=1.0, order_type=OrderType.MARKET)
    trades = engine.add_order(market_buy)
    # Should not match, so no trades
    assert trades == []
    # Market order should not be in the book (since it can't rest)
    assert engine.get_order_book_snapshot()["bids"] == []

def test_market_order_cancelled(engine):
    # Add a limit buy order to the book
    buy_order = make_order(Side.BUY, price=99.0, quantity=1.0)
    engine.add_order(buy_order)
    assert engine.get_order_book_snapshot()["bids"][0]["price"] == 99.0

    # Add a market sell order with no matching buy (simulate by removing buy order)
    # Remove all buy orders to simulate no liquidity
    engine._buy_orders.clear()
    market_sell = make_order(Side.SELL, price=0, quantity=1.0, order_type=OrderType.MARKET)
    trades = engine.add_order(market_sell)
    # Should not match, so no trades
    assert trades == []
    # Market order should not be in the book (since it can't rest)
