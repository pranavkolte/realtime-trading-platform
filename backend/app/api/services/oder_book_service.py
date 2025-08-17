from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.database.models.order_models import Order
from app.database.models.trade_models import Trade
from app.database.enums.oder_enums import OrderStatus
from app.schemas.order_schemas import PlaceOrderRequest, OrderResponse, BookSnapshotResponse, BookLevel
from app.schemas.trade_scehmas import TradeResponse
from app.api.services.oder_matching_service import matching_engine

class PlaceOrderResponse:
    def __init__(self, trades: List[TradeResponse], order: OrderResponse):
        self.trades = trades
        self.order = order

class OrderBookService:
    def __init__(self, db: Session):
        self.db = db
        # Initialize last trade price from database if available
        self._initialize_last_trade_price()

    def _initialize_last_trade_price(self):
        """Initialize last trade price from the most recent trade in database"""
        last_trade = self.db.query(Trade).order_by(desc(Trade.ts)).first()
        if last_trade:
            matching_engine.set_last_trade_price(last_trade.price)

    async def place_order(self, user_id: str, order_request: PlaceOrderRequest) -> dict:
        """Place a new order and return any resulting trades plus the order details"""
        # Create order object
        order = Order(
            user_id=user_id,
            side=order_request.side,
            order_type=order_request.order_type,
            price=order_request.price,
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
            price=order.price,
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
        """Get current order book snapshot"""
        snapshot = matching_engine.get_order_book_snapshot()
        
        bids = [BookLevel(price=level["price"], total_qty=level["total_qty"]) 
                for level in snapshot["bids"]]
        asks = [BookLevel(price=level["price"], total_qty=level["total_qty"]) 
                for level in snapshot["asks"]]
        
        return BookSnapshotResponse(
            bids=bids,
            asks=asks,
            last_trade_price=matching_engine.get_last_trade_price()
        )

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