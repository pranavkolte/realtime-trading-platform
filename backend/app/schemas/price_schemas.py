from pydantic import BaseModel
from datetime import datetime

class PriceHistory(BaseModel):
    timestamp: datetime
    price: float

    class Config:
        from_attributes = True  # For Pydantic v2

class PriceHistoryResponse(BaseModel):
    price: PriceHistory

    class Config:
        from_attributes = True

