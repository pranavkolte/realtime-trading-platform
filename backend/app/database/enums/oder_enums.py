import enum


class Side(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, enum.Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
