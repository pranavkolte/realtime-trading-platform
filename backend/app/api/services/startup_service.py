from sqlalchemy import and_, desc

from app.database import get_db_session
from app.database.models.order_models import Order
from app.database.models.trade_models import Trade
from app.database.enums.oder_enums import OrderStatus
from app.api.services.order_matching_service import matching_engine

def restore_matching_engine_from_database():
    """Restore matching engine state from database on startup"""
    print("🚀 Starting order book restoration...")
    
    # Get a database session
    db_session = next(get_db_session())
    
    try:
        # Initialize last trade price
        print("setting last trade price........")
        last_trade = db_session.query(Trade).order_by(desc(Trade.ts)).first()
        if last_trade:
            matching_engine.set_last_trade_price(last_trade.price)

        # Get all active orders
        active_orders = db_session.query(Order).filter(
            and_(
                Order.active == True,
                Order.remaining > 0,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
            )
        ).order_by(Order.created_at).all()
        
        matching_engine.restore_from_database(active_orders, db_session)
        
        print("Order book restoration complete............")
    finally:
        db_session.close()
