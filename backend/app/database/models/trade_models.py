import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    ForeignKey,
    DateTime
)

from app.database import Base

class Trade(Base):
    __tablename__ = "trades"
    trade_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    engine_trade_id = Column(Integer, index=True, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)

    buy_order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    sell_order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    buy_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    sell_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)

    ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    buyer = relationship("User", foreign_keys=[buy_user_id], back_populates="trades_bought")
    seller = relationship("User", foreign_keys=[sell_user_id], back_populates="trades_sold")
