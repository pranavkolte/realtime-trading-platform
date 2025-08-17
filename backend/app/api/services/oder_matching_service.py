import heapq
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from app.database.enums.oder_enums import Side, OrderType, OrderStatus
from app.database.models.order_models import Order

@dataclass
class TradeResult:
    buy_order_id: UUID
    sell_order_id: UUID
    buy_user_id: UUID
    sell_user_id: UUID
    price: float
    quantity: float
    timestamp: datetime
    buy_order_remaining: float
    sell_order_remaining: float
    buy_order_status: OrderStatus
    sell_order_status: OrderStatus

class OrderMatchingEngine:
    def __init__(self):
        # Buy orders: max heap (negative prices for max behavior)
        self._buy_orders: List[Tuple[float, datetime, Order]] = []
        # Sell orders: min heap (positive prices for min behavior)
        self._sell_orders: List[Tuple[float, datetime, Order]] = []
        # Order lookup for quick access
        self._orders: Dict[str, Order] = {}
        # Trade counter for engine trade IDs
        self._trade_counter = 0
        # Last trade price - persistent across all trades
        self._last_trade_price = 100.0

    def add_order(self, order: Order) -> List[TradeResult]:
        """Add order to the engine and return any resulting trades"""
        trades = []
        
        if order.side == Side.BUY:
            trades = self._process_buy_order(order)
        else:
            trades = self._process_sell_order(order)
        
        # Add remaining quantity to order book if not fully filled
        if order.remaining > 0 and order.status == OrderStatus.OPEN:
            self._add_to_book(order)
        
        return trades

    def _process_buy_order(self, buy_order: Order) -> List[TradeResult]:
        """Process a buy order against sell orders"""
        trades = []
        
        while (buy_order.remaining > 0 and 
               self._sell_orders and 
               self._can_match(buy_order, self._sell_orders[0][2])):
            
            # Get best sell order
            _, _, sell_order = heapq.heappop(self._sell_orders)
            
            # Skip if order is no longer active
            if not sell_order.active or sell_order.remaining <= 0:
                continue
            
            trade = self._execute_trade(buy_order, sell_order)
            if trade:
                trades.append(trade)
            
            # Re-add sell order if it still has remaining quantity
            if sell_order.remaining > 0:
                heapq.heappush(self._sell_orders, 
                             (sell_order.price, sell_order.created_at, sell_order))
        
        return trades

    def _process_sell_order(self, sell_order: Order) -> List[TradeResult]:
        """Process a sell order against buy orders"""
        trades = []
        
        while (sell_order.remaining > 0 and 
               self._buy_orders and 
               self._can_match(self._buy_orders[0][2], sell_order)):
            
            # Get best buy order (note: prices are negative in heap)
            _, _, buy_order = heapq.heappop(self._buy_orders)
            
            # Skip if order is no longer active
            if not buy_order.active or buy_order.remaining <= 0:
                continue
            
            trade = self._execute_trade(buy_order, sell_order)
            if trade:
                trades.append(trade)
            
            # Re-add buy order if it still has remaining quantity
            if buy_order.remaining > 0:
                heapq.heappush(self._buy_orders, 
                             (-buy_order.price, buy_order.created_at, buy_order))
        
        return trades

    def _can_match(self, buy_order: Order, sell_order: Order) -> bool:
        """Check if buy and sell orders can be matched"""
        if buy_order.order_type == OrderType.MARKET or sell_order.order_type == OrderType.MARKET:
            return True
        return buy_order.price >= sell_order.price

    def _execute_trade(self, buy_order: Order, sell_order: Order) -> Optional[TradeResult]:
        """Execute trade between buy and sell orders"""
        if buy_order.remaining <= 0 or sell_order.remaining <= 0:
            return None
        
        # Determine trade quantity
        trade_quantity = min(buy_order.remaining, sell_order.remaining)
        
        # Determine trade price (price discovery)
        if buy_order.order_type == OrderType.MARKET:
            trade_price = sell_order.price
        elif sell_order.order_type == OrderType.MARKET:
            trade_price = buy_order.price
        else:
            # For limit orders, use the price of the order that was in the book first
            if buy_order.created_at < sell_order.created_at:
                trade_price = buy_order.price
            else:
                trade_price = sell_order.price
        
        # Update order quantities
        buy_order.remaining -= trade_quantity
        sell_order.remaining -= trade_quantity
        
        # Update order status
        if buy_order.remaining == 0:
            buy_order.status = OrderStatus.FILLED
        elif buy_order.remaining < buy_order.quantity:
            buy_order.status = OrderStatus.PARTIALLY_FILLED
    
        if sell_order.remaining == 0:
            sell_order.status = OrderStatus.FILLED
        elif sell_order.remaining < sell_order.quantity:
            sell_order.status = OrderStatus.PARTIALLY_FILLED
    
        # Update last trade price in the engine
        self._last_trade_price = trade_price
    
        # Create trade result
        self._trade_counter += 1
        return TradeResult(
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
            buy_user_id=buy_order.user_id,
            sell_user_id=sell_order.user_id,
            price=trade_price,
            quantity=trade_quantity,
            timestamp=datetime.utcnow(),
            buy_order_remaining=buy_order.remaining,
            sell_order_remaining=sell_order.remaining,
            buy_order_status=buy_order.status,
            sell_order_status=sell_order.status
        )

    def get_last_trade_price(self) -> float:
        """Get the last trade price"""
        return self._last_trade_price

    def set_last_trade_price(self, price: float):
        """Set the last trade price (for initialization from database)"""
        self._last_trade_price = price

    def _add_to_book(self, order: Order):
        """Add order to the appropriate order book"""
        self._orders[str(order.order_id)] = order
        
        if order.side == Side.BUY:
            heapq.heappush(self._buy_orders, 
                         (-order.price, order.created_at, order))
        else:
            heapq.heappush(self._sell_orders, 
                         (order.price, order.created_at, order))

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        if order_id in self._orders:
            order = self._orders[order_id]
            order.active = False
            order.status = OrderStatus.CANCELED
            del self._orders[order_id]
            return True
        return False

    def get_order_book_snapshot(self) -> Dict:
        """Get current order book snapshot"""
        # Aggregate buy orders by price
        buy_levels = defaultdict(float)
        for _, _, order in self._buy_orders:
            if order.active and order.remaining > 0:
                buy_levels[order.price] += order.remaining
        
        # Aggregate sell orders by price
        sell_levels = defaultdict(float)
        for _, _, order in self._sell_orders:
            if order.active and order.remaining > 0:
                sell_levels[order.price] += order.remaining
        
        # Sort and format
        bids = [{"price": price, "total_qty": qty} 
                for price, qty in sorted(buy_levels.items(), reverse=True)]
        asks = [{"price": price, "total_qty": qty} 
                for price, qty in sorted(sell_levels.items())]
        
        return {
            "bids": bids[:10],  # Top 10 levels
            "asks": asks[:10],  # Top 10 levels
        }

    def get_best_bid(self) -> Optional[float]:
        """Get the best bid price"""
        while self._buy_orders:
            _, _, order = self._buy_orders[0]
            if order.active and order.remaining > 0:
                return order.price
            heapq.heappop(self._buy_orders)
        return None

    def get_best_ask(self) -> Optional[float]:
        """Get the best ask price"""
        while self._sell_orders:
            _, _, order = self._sell_orders[0]
            if order.active and order.remaining > 0:
                return order.price
            heapq.heappop(self._sell_orders)
        return None

# Global instance
matching_engine = OrderMatchingEngine()
