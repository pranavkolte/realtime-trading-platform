from datetime import datetime
from pydantic import BaseModel

class TradeResponse(BaseModel):
    id: int
    engine_trade_id: int
    price: float
    quantity: float
    buy_order_id: int
    sell_order_id: int
    buy_user_id: str
    sell_user_id: str
    ts: datetime

    class Config:
        from_attributes = True