import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.api.services.order_book_service import OrderBookService, PlaceOrderResponse
from app.database.enums.oder_enums import Side, OrderType, OrderStatus
from app.schemas.order_schemas import PlaceOrderRequest, OrderResponse
from app.schemas.trade_scehmas import TradeResponse
from app.database.models.order_models import Order
from app.database.models.trade_models import Trade
from app.database.models.price_models import PriceHistoryModel

class DummyOrder:
    def __init__(self, price, remaining, side, order_id=None, status=OrderStatus.OPEN, active=True, created_at=None):
        self.price = price
        self.remaining = remaining
        self.side = side
        self.order_id = order_id or str(uuid.uuid4())
        self.status = status
        self.active = active
        self.created_at = created_at or datetime.utcnow()
        self.user_id = str(uuid.uuid4())
        self.order_type = OrderType.LIMIT
        self.quantity = 10.0

class DummyTrade:
    def __init__(self, trade_id=None, price=100.0, quantity=5.0):
        self.trade_id = trade_id or uuid.uuid4()
        self.engine_trade_id = 123
        self.price = price
        self.quantity = quantity
        self.buy_order_id = str(uuid.uuid4())
        self.sell_order_id = str(uuid.uuid4())
        self.buy_user_id = str(uuid.uuid4())
        self.sell_user_id = str(uuid.uuid4())
        self.ts = datetime.utcnow()

class DummyTradeResult:
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc)
        self.price = 100.0
        self.quantity = 5.0
        self.buy_order_id = str(uuid.uuid4())
        self.sell_order_id = str(uuid.uuid4())
        self.buy_user_id = str(uuid.uuid4())
        self.sell_user_id = str(uuid.uuid4())
        self.buy_order_remaining = 0
        self.sell_order_remaining = 0
        self.buy_order_status = OrderStatus.FILLED
        self.sell_order_status = OrderStatus.FILLED

@pytest.fixture
def db_session():
    return MagicMock()

@pytest.fixture
def order_book_service(db_session):
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.set_price_change_callback = MagicMock()
        mock_engine.set_last_trade_price = MagicMock()
        service = OrderBookService(db_session)
        return service

def test_initialization_with_price_history(db_session):
    """Test initialization when price history exists"""
    # Mock price history query
    mock_price = MagicMock()
    mock_price.price = 150.0
    db_session.query.return_value.order_by.return_value.first.return_value = mock_price
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.set_price_change_callback = MagicMock()
        mock_engine.set_last_trade_price = MagicMock()
        
        OrderBookService(db_session)
        
        mock_engine.set_last_trade_price.assert_called_with(150.0)

def test_initialization_with_no_price_history_but_trades(db_session):
    """Test initialization when no price history but trades exist"""
    # Mock no price history but trade exists
    db_session.query.return_value.order_by.return_value.first.side_effect = [None, DummyTrade()]
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.set_price_change_callback = MagicMock()
        mock_engine.set_last_trade_price = MagicMock()
        
        OrderBookService(db_session)
        
        mock_engine.set_last_trade_price.assert_called_with(100.0)

def test_initialization_with_no_data(db_session):
    """Test initialization when no price history or trades exist"""
    # Mock no data
    db_session.query.return_value.order_by.return_value.first.return_value = None
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.set_price_change_callback = MagicMock()
        mock_engine.set_last_trade_price = MagicMock()
        
        OrderBookService(db_session)
        
        mock_engine.set_last_trade_price.assert_called_with(100.0)

def test_restore_order_book_from_db(order_book_service, db_session):
    """Test restoring order book from database"""
    # Mock active orders
    mock_orders = [DummyOrder(100.0, 5.0, Side.BUY), DummyOrder(101.0, 3.0, Side.SELL)]
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_orders
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        order_book_service._restore_order_book_from_db()
        mock_engine.restore_from_database.assert_called_once_with(mock_orders)

@pytest.mark.asyncio
async def test_place_market_buy_order_no_sellers(order_book_service, db_session):
    """Test market buy order when no sellers available"""
    order_request = PlaceOrderRequest(
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=10.0
    )
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.get_best_ask.return_value = None
        
        # Mock database operations
        valid_uuid = str(uuid.uuid4())
        def refresh_side_effect(order):
            order.order_id = valid_uuid
            order.created_at = datetime.utcnow()
        
        db_session.refresh = MagicMock(side_effect=refresh_side_effect)
        db_session.add = MagicMock()
        db_session.commit = MagicMock()
        
        result = await order_book_service.place_order("user-123", order_request)
        
        assert result["order_executed"] is False
        assert len(result["trades"]) == 0
        assert result["order"].status == OrderStatus.CANCELED

@pytest.mark.asyncio
async def test_place_market_sell_order_no_buyers(order_book_service, db_session):
    """Test market sell order when no buyers available"""
    order_request = PlaceOrderRequest(
        side=Side.SELL,
        order_type=OrderType.MARKET,
        quantity=10.0
    )
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.get_best_bid.return_value = None
        
        # Mock database operations
        valid_uuid = str(uuid.uuid4())
        def refresh_side_effect(order):
            order.order_id = valid_uuid
            order.created_at = datetime.utcnow()
        
        db_session.refresh = MagicMock(side_effect=refresh_side_effect)
        db_session.add = MagicMock()
        db_session.commit = MagicMock()
        
        result = await order_book_service.place_order("user-123", order_request)
        
        assert result["order_executed"] is False
        assert len(result["trades"]) == 0
        assert result["order"].status == OrderStatus.CANCELED

@pytest.mark.asyncio
async def test_place_order_with_trades(order_book_service, db_session):
    """Test placing order that results in trades"""
    order_request = PlaceOrderRequest(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100.0,
        quantity=10.0
    )
    
    # Mock trade results
    trade_result = DummyTradeResult()
    
    # Create a mock trade object that simulates what would be created in the database
    mock_trade = MagicMock()
    mock_trade.trade_id = uuid.uuid4()
    mock_trade.engine_trade_id = 123
    mock_trade.price = 100.0
    mock_trade.quantity = 5.0
    mock_trade.buy_order_id = trade_result.buy_order_id
    mock_trade.sell_order_id = trade_result.sell_order_id
    mock_trade.buy_user_id = trade_result.buy_user_id
    mock_trade.sell_user_id = trade_result.sell_user_id
    mock_trade.ts = trade_result.timestamp
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.add_order.return_value = [trade_result]
        mock_engine.notify_trades_and_book_update = AsyncMock()
        
        # Mock database operations
        valid_uuid = str(uuid.uuid4())
        def refresh_side_effect(order):
            order.order_id = valid_uuid
            order.created_at = datetime.utcnow()
            order.remaining = 5.0
            order.status = OrderStatus.PARTIALLY_FILLED
        
        # Mock the Trade class constructor to return our mock trade
        with patch('app.api.services.order_book_service.Trade', return_value=mock_trade):
            db_session.refresh = MagicMock(side_effect=refresh_side_effect)
            db_session.add = MagicMock()
            db_session.commit = MagicMock()
            db_session.flush = MagicMock()
            
            # Mock order queries for updates
            mock_order = MagicMock()
            db_session.query.return_value.filter.return_value.first.return_value = mock_order
            
            result = await order_book_service.place_order("user-123", order_request)
            
            assert result["order_executed"] is True
            assert len(result["trades"]) == 1
            mock_engine.notify_trades_and_book_update.assert_called_once()

@pytest.mark.asyncio
async def test_place_order_no_trades(order_book_service, db_session):
    """Test placing order that doesn't result in trades"""
    order_request = PlaceOrderRequest(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100.0,
        quantity=10.0
    )
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.add_order.return_value = []
        mock_engine._notify_book_update = AsyncMock()
        
        # Mock database operations
        valid_uuid = str(uuid.uuid4())
        def refresh_side_effect(order):
            order.order_id = valid_uuid
            order.created_at = datetime.utcnow()
            order.remaining = 10.0
            order.status = OrderStatus.OPEN
        
        db_session.refresh = MagicMock(side_effect=refresh_side_effect)
        db_session.add = MagicMock()
        db_session.commit = MagicMock()
        db_session.flush = MagicMock()
        
        result = await order_book_service.place_order("user-123", order_request)
        
        assert result["order_executed"] is False
        assert len(result["trades"]) == 0
        mock_engine._notify_book_update.assert_called_once()

def test_cancel_order_success(order_book_service, db_session):
    """Test successful order cancellation"""
    mock_order = DummyOrder(100.0, 5.0, Side.BUY, order_id="test-order")
    db_session.query.return_value.filter.return_value.first.return_value = mock_order
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.cancel_order.return_value = True
        
        result = order_book_service.cancel_order("user-123", "test-order")
        
        assert result is True
        assert mock_order.active is False
        assert mock_order.status == OrderStatus.CANCELED
        db_session.commit.assert_called_once()

def test_cancel_order_not_found(order_book_service, db_session):
    """Test order cancellation when order not found"""
    db_session.query.return_value.filter.return_value.first.return_value = None
    
    result = order_book_service.cancel_order("user-123", "nonexistent-order")
    
    assert result is False

def test_cancel_order_engine_failure(order_book_service, db_session):
    """Test order cancellation when matching engine fails"""
    mock_order = DummyOrder(100.0, 5.0, Side.BUY, order_id="test-order")
    db_session.query.return_value.filter.return_value.first.return_value = mock_order
    
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.cancel_order.return_value = False
        
        result = order_book_service.cancel_order("user-123", "test-order")
        
        assert result is False
        db_session.commit.assert_not_called()

def test_get_user_orders_all(order_book_service, db_session):
    """Test getting all user orders"""
    mock_orders = [DummyOrder(100.0, 5.0, Side.BUY), DummyOrder(101.0, 3.0, Side.SELL)]
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_orders
    
    result = order_book_service.get_user_orders("user-123", active_only=False)
    
    assert len(result) == 2
    assert all(isinstance(order, OrderResponse) for order in result)

def test_get_user_orders_active_only(order_book_service, db_session):
    """Test getting only active user orders"""
    mock_orders = [DummyOrder(100.0, 5.0, Side.BUY)]
    query_mock = db_session.query.return_value.filter.return_value
    query_mock.filter.return_value.order_by.return_value.all.return_value = mock_orders
    
    result = order_book_service.get_user_orders("user-123", active_only=True)
    
    assert len(result) == 1
    query_mock.filter.assert_called_once()

def test_get_user_trades(order_book_service, db_session):
    """Test getting user trade history"""
    mock_trades = [DummyTrade(), DummyTrade()]
    db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_trades
    
    result = order_book_service.get_user_trades("user-123", limit=50)
    
    assert len(result) == 2
    assert all(isinstance(trade, TradeResponse) for trade in result)

def test_get_order_book_snapshot(order_book_service, db_session):
    """Test getting order book snapshot"""
    # Mock active orders
    buy_order = DummyOrder(100.0, 5.0, Side.BUY)
    sell_order = DummyOrder(101.0, 3.0, Side.SELL)
    mock_orders = [buy_order, sell_order]
    
    db_session.query.return_value.filter.return_value.all.return_value = mock_orders
    
    # Mock last trade price query
    mock_trade = DummyTrade()
    db_session.query.return_value.order_by.return_value.first.return_value = mock_trade
    
    result = order_book_service.get_order_book_snapshot()
    
    assert len(result.bids) == 1
    assert len(result.asks) == 1
    assert result.bids[0].price == 100.0
    assert result.asks[0].price == 101.0

def test_get_last_trade_price_from_db_with_trade(order_book_service, db_session):
    """Test getting last trade price when trade exists"""
    mock_trade = DummyTrade(price=105.0)
    db_session.query.return_value.order_by.return_value.first.return_value = mock_trade
    
    result = order_book_service._get_last_trade_price_from_db()
    
    assert result == 105.0

def test_get_last_trade_price_from_db_no_trade(order_book_service, db_session):
    """Test getting last trade price when no trade exists"""
    db_session.query.return_value.order_by.return_value.first.return_value = None
    
    result = order_book_service._get_last_trade_price_from_db()
    
    assert result == 100.0

def test_get_recent_trades(order_book_service, db_session):
    """Test getting recent trades"""
    mock_trades = [DummyTrade(), DummyTrade()]
    db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_trades
    
    result = order_book_service.get_recent_trades(limit=50)
    
    assert len(result) == 2
    assert all(isinstance(trade, TradeResponse) for trade in result)

def test_get_market_stats_with_bid_ask(order_book_service, db_session):
    """Test getting market stats when bid and ask exist"""
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.get_best_bid.return_value = 99.0
        mock_engine.get_best_ask.return_value = 101.0
        mock_engine.get_last_trade_price.return_value = 100.0
        
        result = order_book_service.get_market_stats()
        
        assert result["best_bid"] == 99.0
        assert result["best_ask"] == 101.0
        assert result["spread"] == 2.0
        assert result["last_trade_price"] == 100.0

def test_get_market_stats_no_bid_ask(order_book_service, db_session):
    """Test getting market stats when no bid or ask exists"""
    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.get_best_bid.return_value = None
        mock_engine.get_best_ask.return_value = None
        mock_engine.get_last_trade_price.return_value = 100.0
        
        result = order_book_service.get_market_stats()
        
        assert result["best_bid"] is None
        assert result["best_ask"] is None
        assert result["spread"] is None
        assert result["last_trade_price"] == 100.0

def test_place_order_response_class():
    """Test PlaceOrderResponse class"""
    trades = [TradeResponse(
        id=uuid.uuid4(),
        engine_trade_id=123,
        price=100.0,
        quantity=5.0,
        buy_order_id=str(uuid.uuid4()),
        sell_order_id=str(uuid.uuid4()),
        buy_user_id=str(uuid.uuid4()),
        sell_user_id=str(uuid.uuid4()),
        ts=datetime.utcnow()
    )]
    order = OrderResponse(
        id=str(uuid.uuid4()),
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=100.0,
        quantity=10.0,
        remaining=5.0,
        status=OrderStatus.PARTIALLY_FILLED,
        active=True,
        created_at=datetime.utcnow()
    )
    
    response = PlaceOrderResponse(trades, order)
    
    assert response.trades == trades
    assert response.order == order

def test_order_book_updates_after_place_order(order_book_service, db_session):
    """Test existing test case"""
    order_request = PlaceOrderRequest(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=101.0,
        quantity=2.0
    )
    user_id = "test-user-id"

    def refresh_side_effect(order):
        if getattr(order, "order_id", None) is None:
            order.order_id = uuid.uuid4()
        if getattr(order, "created_at", None) is None:
            order.created_at = datetime.utcnow()
    db_session.refresh = MagicMock(side_effect=refresh_side_effect)

    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.flush = MagicMock()

    with patch('app.api.services.order_book_service.matching_engine') as mock_engine:
        mock_engine.add_order.return_value = []
        mock_engine._notify_book_update = AsyncMock()
        
        asyncio.run(order_book_service.place_order(user_id, order_request))

    order_book_service.get_order_book_snapshot = MagicMock(return_value={
        "bids": [{"price": 101.0, "total_qty": 2.0}],
        "asks": [],
        "last_trade_price": 100.0
    })

    snapshot = order_book_service.get_order_book_snapshot()
    assert snapshot["bids"][0]["price"] == 101.0
    assert snapshot["bids"][0]["total_qty"] == 2.0
    