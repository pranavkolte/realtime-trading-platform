import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Enum,
    Float,
    Boolean,
    DateTime,
)

from app.database import Base
from app.database.enums.oder_enums import Side, OrderType, OrderStatus

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id = Column(String, ForeignKey("users.user_id"), index=True, nullable=False)

    side = Column(Enum(Side), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    remaining = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.OPEN, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="orders")