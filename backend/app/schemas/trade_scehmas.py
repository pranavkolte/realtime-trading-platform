from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class TradeResponse(BaseModel):
    id: UUID
    engine_trade_id: int
    price: float
    quantity: float
    buy_order_id: UUID
    sell_order_id: UUID
    buy_user_id: UUID
    sell_user_id: UUID
    ts: datetime

    class Config:
        from_attributes = True
