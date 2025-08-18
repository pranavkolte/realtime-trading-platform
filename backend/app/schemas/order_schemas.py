from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.database.enums.oder_enums import Side, OrderType, OrderStatus

class PlaceOrderRequest(BaseModel):
    side: Side
    order_type: OrderType
    quantity: float = Field(gt=0)
    price: Optional[float] = Field(default=None, gt=0)
    
    @field_validator('price')
    def validate_price(cls, v, info):
        order_type = info.data.get('order_type')
        if order_type == OrderType.LIMIT and v is None:
            raise ValueError('Price is required for limit orders')
        if order_type == OrderType.MARKET and v is not None:
            raise ValueError('Price should not be specified for market orders')
        return v

class OrderResponse(BaseModel):
    id: UUID
    side: Side
    order_type: OrderType
    price: Optional[float]
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
