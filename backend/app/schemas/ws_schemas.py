from pydantic import BaseModel
from datetime import datetime

class WSTradeExecutionSchema(BaseModel):
    event: str = "trade_executed"
    timestamp: datetime
    data: dict[str, any]

class WSOrderBookUpdateSchema(BaseModel):
    event: str = "book_update"
    timestamp: datetime
    data: dict[str, any]

class WSOrderStatusSchema(BaseModel):
    event: str = "order_status"
    timestamp: datetime
    data: dict[str, any]

class WSErrorSchema(BaseModel):
    event: str = "error"
    message: str

class WSConnectionSchema(BaseModel):
    event: str = "connected"
    message: str
    user_id: str
