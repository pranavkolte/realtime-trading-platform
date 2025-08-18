from pydantic import BaseModel
from datetime import datetime
from typing import Any


class WSTradeExecutionSchema(BaseModel):
    event: str = "trade_executed"
    timestamp: datetime
    data: dict[str, Any]


class WSOrderBookUpdateSchema(BaseModel):
    event: str = "book_update"
    timestamp: datetime
    data: dict[str, Any]


class WSOrderStatusSchema(BaseModel):
    event: str = "order_status"
    timestamp: datetime
    data: dict[str, Any]


class WSErrorSchema(BaseModel):
    event: str = "error"
    message: str


class WSConnectionSchema(BaseModel):
    event: str = "connected"
    message: str
    user_id: str
