from typing import List
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timezone

from app.database.models.order_models import Order
from app.database.models.trade_models import Trade
from app.database.models.price_models import PriceHistoryModel
from app.database.enums.oder_enums import OrderStatus, Side, OrderType
from app.schemas.order_schemas import PlaceOrderRequest, OrderResponse, BookSnapshotResponse, BookLevel
from app.schemas.trade_scehmas import TradeResponse
from app.api.services.order_matching_service import matching_engine
from app.api.services.ws_service import ws_manager

class PlaceOrderResponse:
    def __init__(self, trades: List[TradeResponse], order: OrderResponse):
        self.trades = trades
        self.order = order

class OrderBookService:
    def __init__(self, db: Session):
        self.db = db

        # Initialize last trade price from DB
        self._initialize_last_trade_price_from_price_history()

        async def save_and_broadcast_price(price):
            now = datetime.now(timezone.utc)
            price_entry = PriceHistoryModel(price=price, timestamp=now)
            self.db.add(price_entry)
            self.db.commit()
            # Broadcast price change event
            await ws_manager.broadcast_price_change(price, now)

        # Register the async callback
        matching_engine.set_price_change_callback(save_and_broadcast_price)

    def _initialize_last_trade_price_from_price_history(self):
        """Initialize last trade price from the most recent price in price_history table"""
        last_price = (
            self.db.query(PriceHistoryModel)
            .order_by(PriceHistoryModel.timestamp.desc())
            .first()
        )
        if last_price:
            matching_engine.set_last_trade_price(last_price.price)
        else:
            # Fallback to last trade if no price history
            last_trade = self.db.query(Trade).order_by(desc(Trade.ts)).first()
            if last_trade:
                matching_engine.set_last_trade_price(last_trade.price)
            else:
                matching_engine.set_last_trade_price(100.0)

    def _restore_order_book_from_db(self):
        """Restore the matching engine order book from database"""
        # Get all active orders with remaining quantity
        active_orders = self.db.query(Order).filter(
            and_(
                Order.active,
                Order.remaining > 0,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
            )
        ).order_by(Order.created_at).all()
        
        # Restore the matching engine state
        matching_engine.restore_from_database(active_orders)

    async def place_order(self, user_id: str, order_request: PlaceOrderRequest) -> dict:
        """Place a new order and return any resulting trades plus the order details"""
        
        # For market orders, check if there are any matching orders available
        if order_request.order_type == OrderType.MARKET:
            if order_request.side == Side.BUY:
                # Buy market order: check if there are any sell orders
                best_ask = matching_engine.get_best_ask()
                if best_ask is None:
                    # No sellers available, cancel the market order
                    order = Order(
                        user_id=user_id,
                        side=order_request.side,
                        order_type=order_request.order_type,
                        price=None,  # No price for cancelled market order
                        quantity=order_request.quantity,
                        remaining=0,  # No remaining since it's cancelled
                        status=OrderStatus.CANCELED,
                        active=False
                    )
                    self.db.add(order)
                    self.db.commit()
                    self.db.refresh(order)
                    
                    order_response = OrderResponse(
                        id=order.order_id,
                        side=order.side,
                        order_type=order.order_type,
                        price=None,
                        quantity=order.quantity,
                        remaining=order.remaining,
                        status=order.status,
                        active=order.active,
                        created_at=order.created_at
                    )
                    
                    return {
                        "trades": [],
                        "order": order_response,
                        "order_executed": False
                    }
            else:
                # Sell market order: check if there are any buy orders
                best_bid = matching_engine.get_best_bid()
                if best_bid is None:
                    # No buyers available, cancel the market order
                    order = Order(
                        user_id=user_id,
                        side=order_request.side,
                        order_type=order_request.order_type,
                        price=None,  # No price for cancelled market order
                        quantity=order_request.quantity,
                        remaining=0,  # No remaining since it's cancelled
                        status=OrderStatus.CANCELED,
                        active=False
                    )
                    self.db.add(order)
                    self.db.commit()
                    self.db.refresh(order)
                    
                    order_response = OrderResponse(
                        id=order.order_id,
                        side=order.side,
                        order_type=order.order_type,
                        price=None,
                        quantity=order.quantity,
                        remaining=order.remaining,
                        status=order.status,
                        active=order.active,
                        created_at=order.created_at
                    )
                    
                    return {
                        "trades": [],
                        "order": order_response,
                        "order_executed": False
                    }
    
        # Create order object
        order = Order(
            user_id=user_id,
            side=order_request.side,
            order_type=order_request.order_type,
            price=order_request.price,  # Will be None for market orders
            quantity=order_request.quantity,
            remaining=order_request.quantity,
            status=OrderStatus.OPEN,
            active=True
        )
        
        # Add to database
        self.db.add(order)
        self.db.flush()  # Get the order ID
        
        # Process through matching engine
        trade_results = matching_engine.add_order(order)
        
        # Handle WebSocket notifications for trades
        if trade_results:
            await matching_engine.notify_trades_and_book_update(trade_results)
        else:
            # Just send order book update if no trades
            await matching_engine._notify_book_update()
        
        # Save trades to database and update affected orders
        trades = []
        updated_orders = {}  # order_id -> (remaining, status)
        
        for trade_result in trade_results:
            trade = Trade(
                engine_trade_id=int(trade_result.timestamp.timestamp()),
                price=trade_result.price,
                quantity=trade_result.quantity,
                buy_order_id=trade_result.buy_order_id,
                sell_order_id=trade_result.sell_order_id,
                buy_user_id=trade_result.buy_user_id,
                sell_user_id=trade_result.sell_user_id,
                ts=trade_result.timestamp
            )
            self.db.add(trade)
            trades.append(trade)
            
            # Store order updates
            updated_orders[str(trade_result.buy_order_id)] = (
                trade_result.buy_order_remaining, 
                trade_result.buy_order_status
            )
            updated_orders[str(trade_result.sell_order_id)] = (
                trade_result.sell_order_remaining, 
                trade_result.sell_order_status
            )
        
        # Update all affected orders in the database
        for order_id, (remaining, status) in updated_orders.items():
            db_order = self.db.query(Order).filter(Order.order_id == order_id).first()
            if db_order:
                db_order.remaining = remaining
                db_order.status = status
                # Set active to False when order is filled, keep True for partially filled
                if status == OrderStatus.FILLED:
                    db_order.active = False
                elif status == OrderStatus.PARTIALLY_FILLED:
                    db_order.active = True  # Keep active for partially filled orders
                # OPEN orders remain active = True by default

        # Commit all changes
        self.db.commit()
        
        # Refresh the order to get updated values
        self.db.refresh(order)
        
        # Create trade responses
        trade_responses = [TradeResponse(
            id=trade.trade_id,
            engine_trade_id=trade.engine_trade_id,
            price=trade.price,
            quantity=trade.quantity,
            buy_order_id=trade.buy_order_id,
            sell_order_id=trade.sell_order_id,
            buy_user_id=trade.buy_user_id,
            sell_user_id=trade.sell_user_id,
            ts=trade.ts
        ) for trade in trades]
        
        # Create order response
        order_response = OrderResponse(
            id=order.order_id,
            side=order.side,
            order_type=order.order_type,
            price=order.price if order.order_type == OrderType.LIMIT else None,  # Don't return price for market orders
            quantity=order.quantity,
            remaining=order.remaining,
            status=order.status,
            active=order.active,
            created_at=order.created_at
        )
        
        # Return both trades and order information
        return {
            "trades": trade_responses,
            "order": order_response,
            "order_executed": len(trade_responses) > 0
        }

    def cancel_order(self, user_id: str, order_id: str) -> bool:
        """Cancel an order"""
        # Find order in database
        order = self.db.query(Order).filter(
            and_(
                Order.order_id == order_id,
                Order.user_id == user_id,
                Order.active
            )
        ).first()
        
        if not order:
            return False
        
        # Cancel in matching engine
        success = matching_engine.cancel_order(str(order_id))
        
        if success:
            # Update in database
            order.active = False
            order.status = OrderStatus.CANCELED
            self.db.commit()
        
        return success

    def get_user_orders(self, user_id: str, active_only: bool = False) -> List[OrderResponse]:
        """Get user's orders"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if active_only:
            query = query.filter(Order.active)
        
        orders = query.order_by(desc(Order.created_at)).all()
        
        return [OrderResponse(
            id=order.order_id,
            side=order.side,
            order_type=order.order_type,
            price=order.price,
            quantity=order.quantity,
            remaining=order.remaining,
            status=order.status,
            active=order.active,
            created_at=order.created_at
        ) for order in orders]

    def get_user_trades(self, user_id: str, limit: int = 50) -> List[TradeResponse]:
        """Get user's trade history"""
        trades = self.db.query(Trade).filter(
            (Trade.buy_user_id == user_id) | (Trade.sell_user_id == user_id)
        ).order_by(desc(Trade.ts)).limit(limit).all()
        
        return [TradeResponse(
            id=trade.trade_id,
            engine_trade_id=trade.engine_trade_id,
            price=trade.price,
            quantity=trade.quantity,
            buy_order_id=trade.buy_order_id,
            sell_order_id=trade.sell_order_id,
            buy_user_id=trade.buy_user_id,
            sell_user_id=trade.sell_user_id,
            ts=trade.ts
        ) for trade in trades]

    def get_order_book_snapshot(self) -> BookSnapshotResponse:
        """Get current order book snapshot from database"""
        # Get active orders from database - only LIMIT orders with valid prices
        active_orders = self.db.query(Order).filter(
            and_(
                Order.active,
                Order.remaining > 0,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
                Order.order_type == OrderType.LIMIT,  # Only limit orders
                Order.price.isnot(None)  # Only orders with valid prices
            )
        ).all()
        
        # Aggregate by price level
        buy_levels = defaultdict(float)
        sell_levels = defaultdict(float)
        
        for order in active_orders:
            if order.side == Side.BUY:
                buy_levels[order.price] += order.remaining
            else:
                sell_levels[order.price] += order.remaining
        
        # Format for response
        bids = [BookLevel(price=price, total_qty=qty) 
                for price, qty in sorted(buy_levels.items(), reverse=True)][:10]
        asks = [BookLevel(price=price, total_qty=qty) 
                for price, qty in sorted(sell_levels.items())][:10]
        
        return BookSnapshotResponse(
            bids=bids,
            asks=asks,
            last_trade_price=self._get_last_trade_price_from_db()
        )

    def _get_last_trade_price_from_db(self) -> float:
        """Get last trade price from database"""
        last_trade = self.db.query(Trade).order_by(desc(Trade.ts)).first()
        return last_trade.price if last_trade else 100.0

    def get_recent_trades(self, limit: int = 50) -> List[TradeResponse]:
        """Get recent trades for market data"""
        trades = self.db.query(Trade).order_by(desc(Trade.ts)).limit(limit).all()
        
        return [TradeResponse(
            id=trade.trade_id,
            engine_trade_id=trade.engine_trade_id,
            price=trade.price,
            quantity=trade.quantity,
            buy_order_id=trade.buy_order_id,
            sell_order_id=trade.sell_order_id,
            buy_user_id=trade.buy_user_id,
            sell_user_id=trade.sell_user_id,
            ts=trade.ts
        ) for trade in trades]

    def get_market_stats(self) -> dict:
        """Get basic market statistics"""
        best_bid = matching_engine.get_best_bid()
        best_ask = matching_engine.get_best_ask()
        
        # Calculate spread
        spread = None
        if best_bid and best_ask:
            spread = best_ask - best_bid
        
        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "last_trade_price": matching_engine.get_last_trade_price()
        }