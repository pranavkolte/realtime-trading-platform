from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.api.services.order_book_service import OrderBookService
from app.api.services.ws_service import ws_manager
from app.database.models.user_models import UserModel
from app.schemas.order_schemas import PlaceOrderRequest, OrderResponse, BookSnapshotResponse
from app.schemas.trade_scehmas import TradeResponse
from app.core.auth_dependencies import get_current_user

router = APIRouter()
ws_service = ws_manager

# Create a response model for place order
class PlaceOrderResponseModel:
    def __init__(self, trades: List[TradeResponse], order: OrderResponse, order_executed: bool):
        self.trades = trades
        self.order = order
        self.order_executed = order_executed

@router.post("/place")
async def place_order(
    order_request: PlaceOrderRequest,
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Place a new buy/sell order
    
    Returns:
    - trades: List of executed trades (if any)
    - order: The order details (updated with current status)
    - order_executed: Boolean indicating if the order was executed immediately
    """
    try:
        order_service = OrderBookService(db_session)
        result = await order_service.place_order(
            user_id=str(current_user.user_id),
            order_request=order_request
        )
        
        # Broadcast order book updates via WebSocket
        order_book = order_service.get_order_book_snapshot()
        await ws_service.broadcast_message({
            "type": "order_book_update",
            "data": order_book.dict()
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to place order: {str(e)}"
        )

@router.delete("/cancel/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Cancel an existing order
    
    - **order_id**: ID of the order to cancel
    """
    try:
        order_service = OrderBookService(db_session)
        success = order_service.cancel_order(
            user_id=current_user.user_id,
            order_id=order_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or cannot be cancelled"
            )
        
        # Broadcast order book updates
        order_book = order_service.get_order_book_snapshot()
        await ws_service.broadcast_message({
            "type": "order_book_update",
            "data": order_book.dict()
        })
        
        return {"message": "Order cancelled successfully", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel order: {str(e)}"
        )

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    active_only: bool = False,
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Get user's orders
    
    - **active_only**: If true, only return active orders (default: false)
    """
    try:
        order_service = OrderBookService(db_session)
        orders = order_service.get_user_orders(
            user_id=current_user.user_id,
            active_only=active_only
        )
        return orders
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get orders: {str(e)}"
        )

@router.get("/my-trades", response_model=List[TradeResponse])
async def get_my_trades(
    limit: int = 50,
    current_user: UserModel = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Get user's trade history
    
    - **limit**: Maximum number of trades to return (default: 50)
    """
    try:
        order_service = OrderBookService(db_session)  # Use the injected session
        trades = order_service.get_user_trades(
            user_id=current_user.user_id,
            limit=limit
        )
        return trades
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get trades: {str(e)}"
        )

@router.get("/book", response_model=BookSnapshotResponse)
async def get_order_book(db: Session = Depends(get_db_session)):
    """
    Get current order book snapshot
    
    Returns current bids, asks, and last trade price
    """
    try:
        order_service = OrderBookService(db)
        order_book = order_service.get_order_book_snapshot()
        return order_book
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get order book: {str(e)}"
        )

@router.get("/recent-trades", response_model=List[TradeResponse])
async def get_recent_trades(
    limit: int = 50,
    db_session: Session = Depends(get_db_session)
):
    """
    Get recent trades for market data
    
    - **limit**: Maximum number of trades to return (default: 50)
    """
    try:
        order_service = OrderBookService(db_session)  # Use the injected session
        trades = order_service.get_recent_trades(limit=limit)
        return trades
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get recent trades: {str(e)}"
        )

@router.get("/market-stats")
async def get_market_stats(db_session: Session = Depends(get_db_session)):
    """
    Get basic market statistics
    
    Returns best bid, best ask, spread, and last trade price
    """
    try:
        order_service = OrderBookService(db_session)
        stats = order_service.get_market_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get market stats: {str(e)}"
        )