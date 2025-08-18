import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

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

def test_order_cancel_success(engine):
    """Test successful order cancellation"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    engine.add_order(buy_order)
    
    # Cancel the order
    result = engine.cancel_order(str(buy_order.order_id))
    assert result is True
    assert buy_order.active is False
    assert buy_order.status == OrderStatus.CANCELED

def test_order_cancel_not_found(engine):
    """Test cancellation of non-existent order"""
    result = engine.cancel_order("non-existent-id")
    assert result is False

def test_get_best_bid_with_orders(engine):
    """Test getting best bid when orders exist"""
    buy_order1 = make_order(Side.BUY, price=99.0, quantity=1.0)
    buy_order2 = make_order(Side.BUY, price=100.0, quantity=1.0)
    
    engine.add_order(buy_order1)
    engine.add_order(buy_order2)
    
    best_bid = engine.get_best_bid()
    assert best_bid == 100.0

def test_get_best_bid_empty(engine):
    """Test getting best bid when no orders exist"""
    best_bid = engine.get_best_bid()
    assert best_bid is None

def test_get_best_ask_with_orders(engine):
    """Test getting best ask when orders exist"""
    sell_order1 = make_order(Side.SELL, price=101.0, quantity=1.0)
    sell_order2 = make_order(Side.SELL, price=100.0, quantity=1.0)
    
    engine.add_order(sell_order1)
    engine.add_order(sell_order2)
    
    best_ask = engine.get_best_ask()
    assert best_ask == 100.0

def test_get_best_ask_empty(engine):
    """Test getting best ask when no orders exist"""
    best_ask = engine.get_best_ask()
    assert best_ask is None

def test_set_last_trade_price(engine):
    """Test setting last trade price"""
    engine.set_last_trade_price(150.0)
    assert engine.get_last_trade_price() == 150.0

def test_price_change_callback_sync(engine):
    """Test synchronous price change callback"""
    callback_called = False
    callback_price = None
    
    def price_callback(price):
        nonlocal callback_called, callback_price
        callback_called = True
        callback_price = price
    
    engine.set_price_change_callback(price_callback)
    
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0)
    
    engine.add_order(buy_order)
    engine.add_order(sell_order)
    
    assert callback_called is True
    assert callback_price == 100.0

@pytest.mark.asyncio
async def test_price_change_callback_async(engine):
    """Test asynchronous price change callback"""
    callback_called = False
    callback_price = None
    
    async def async_price_callback(price):
        nonlocal callback_called, callback_price
        callback_called = True
        callback_price = price
    
    engine.set_price_change_callback(async_price_callback)
    
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0)
    
    engine.add_order(buy_order)
    engine.add_order(sell_order)
    
    # Give async callback time to execute
    await asyncio.sleep(0.1)
    
    assert callback_called is True
    assert callback_price == 100.0

def test_partial_fill_both_orders(engine):
    """Test partial fill of both orders"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=2.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=3.0)
    
    engine.add_order(buy_order)
    trades = engine.add_order(sell_order)
    
    assert len(trades) == 1
    trade = trades[0]
    assert trade.quantity == 2.0
    assert trade.buy_order_status == OrderStatus.FILLED
    assert trade.sell_order_status == OrderStatus.PARTIALLY_FILLED
    assert trade.sell_order_remaining == 1.0

def test_order_with_zero_remaining(engine):
    """Test order with zero remaining quantity"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0, remaining=0.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0)
    
    engine.add_order(buy_order)
    trades = engine.add_order(sell_order)
    
    # Should not match since buy order has zero remaining
    assert len(trades) == 0

def test_inactive_order_in_heap(engine):
    """Test inactive orders are skipped in heap processing"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0)
    
    # Add buy order
    engine.add_order(buy_order)
    
    # Make buy order inactive
    buy_order.active = False
    
    # Add sell order - should not match with inactive buy order
    trades = engine.add_order(sell_order)
    assert len(trades) == 0

def test_order_book_snapshot_with_invalid_prices(engine):
    """Test order book snapshot skips orders with None prices"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    sell_order = make_order(Side.SELL, price=101.0, quantity=1.0)
    engine._add_to_book(buy_order)
    engine._add_to_book(sell_order)
    # Corrupt the prices after adding to book
    buy_order.price = None
    sell_order.price = None
    snapshot = engine.get_order_book_snapshot()
    assert snapshot["bids"] == []
    assert snapshot["asks"] == []

@pytest.mark.asyncio
async def test_notify_trades_and_book_update(engine):
    """Test trade and book update notifications"""
    with patch('app.api.services.order_matching_service.ws_manager') as mock_ws:
        mock_ws.send_order_status_update = AsyncMock()
        mock_ws.send_order_book_update = AsyncMock()
        
        trade = TradeResult(
            buy_order_id=uuid4(),
            sell_order_id=uuid4(),
            buy_user_id=uuid4(),
            sell_user_id=uuid4(),
            price=100.0,
            quantity=1.0,
            timestamp=datetime.utcnow(),
            buy_order_remaining=0.0,
            sell_order_remaining=0.0,
            buy_order_status=OrderStatus.FILLED,
            sell_order_status=OrderStatus.FILLED
        )
        
        await engine.notify_trades_and_book_update([trade])
        
        # Should call order status updates for both users
        assert mock_ws.send_order_status_update.call_count == 2
        # Should call book update once
        assert mock_ws.send_order_book_update.call_count == 1

@pytest.mark.asyncio
async def test_notify_trades_exception_handling(engine):
    """Test exception handling in trade notifications"""
    with patch('app.api.services.order_matching_service.ws_manager') as mock_ws:
        mock_ws.send_order_status_update = AsyncMock(side_effect=Exception("Connection error"))
        
        trade = TradeResult(
            buy_order_id=uuid4(),
            sell_order_id=uuid4(),
            buy_user_id=uuid4(),
            sell_user_id=uuid4(),
            price=100.0,
            quantity=1.0,
            timestamp=datetime.utcnow(),
            buy_order_remaining=0.0,
            sell_order_remaining=0.0,
            buy_order_status=OrderStatus.FILLED,
            sell_order_status=OrderStatus.FILLED
        )
        
        # Should not raise exception despite ws_manager failure
        await engine.notify_trades_and_book_update([trade])

def test_restore_from_database_with_trades(engine):
    """Test restoring from database with orders that generate trades"""
    mock_db_session = MagicMock()
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0,
                          created_at=datetime(2023, 1, 1, 10, 0, 0))
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0,
                           created_at=datetime(2023, 1, 1, 10, 0, 1))
    orders = [buy_order, sell_order]
    with patch('app.database.models.trade_models.Trade') as MockTrade:
        engine.restore_from_database(orders, mock_db_session)
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

def test_restore_from_database_without_session(engine):
    """Test restoring from database without db session"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0)
    sell_order = make_order(Side.SELL, price=100.0, quantity=1.0)
    
    orders = [buy_order, sell_order]
    
    # Should not raise exception when no db_session provided
    engine.restore_from_database(orders, None)

def test_multiple_partial_fills(engine):
    """Test multiple partial fills on same order"""
    buy_order = make_order(Side.BUY, price=100.0, quantity=5.0)
    engine.add_order(buy_order)
    
    # First partial fill
    sell_order1 = make_order(Side.SELL, price=100.0, quantity=2.0)
    trades1 = engine.add_order(sell_order1)
    assert len(trades1) == 1
    assert buy_order.status == OrderStatus.PARTIALLY_FILLED
    assert buy_order.remaining == 3.0
    
    # Second partial fill
    sell_order2 = make_order(Side.SELL, price=100.0, quantity=1.0)
    trades2 = engine.add_order(sell_order2)
    assert len(trades2) == 1
    assert buy_order.status == OrderStatus.PARTIALLY_FILLED
    assert buy_order.remaining == 2.0

def test_market_order_price_discovery_sell_side(engine):
    """Test market sell order takes buy limit order price"""
    # Add buy limit order
    buy_order = make_order(Side.BUY, price=99.0, quantity=1.0)
    engine.add_order(buy_order)
    
    # Add market sell order
    market_sell = make_order(Side.SELL, price=0, quantity=1.0, order_type=OrderType.MARKET)
    trades = engine.add_order(market_sell)
    
    assert len(trades) == 1
    assert trades[0].price == 99.0  # Market sell takes buy limit price

def test_limit_order_price_priority(engine):
    """Test limit order price priority based on creation time"""
    # Create orders with different timestamps
    older_time = datetime(2023, 1, 1, 10, 0, 0)
    newer_time = datetime(2023, 1, 1, 10, 0, 1)
    
    buy_order = make_order(Side.BUY, price=100.0, quantity=1.0, created_at=older_time)
    sell_order = make_order(Side.SELL, price=99.0, quantity=1.0, created_at=newer_time)
    
    engine.add_order(buy_order)
    trades = engine.add_order(sell_order)
    
    assert len(trades) == 1
    # Older order (buy) was in book first, so use its price
    assert trades[0].price == 100.0
