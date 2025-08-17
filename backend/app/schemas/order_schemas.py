from datetime import datetime

from pydantic import BaseModel, Field

from app.database.enums.oder_enums import Side, OrderType, OrderStatus

class PlaceOrderRequest(BaseModel):
    side: Side
    order_type: OrderType
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)

class OrderResponse(BaseModel):
    id: int
    side: Side
    order_type: OrderType
    price: float
    quantity: float
    remaining: float
    status: OrderStatus
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class BookLevel(BaseModel):
    price: float
    total_qty: float

class BookSnapshotResponse(BaseModel):
    bids: list[BookLevel]
    asks: list[BookLevel]
    last_trade_price: float
