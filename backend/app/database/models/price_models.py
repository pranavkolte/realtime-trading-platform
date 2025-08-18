from datetime import datetime, timezone
from sqlalchemy import Column, Float, DateTime, Integer
from app.database import Base


class PriceHistoryModel(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    price = Column(Float, nullable=False)
