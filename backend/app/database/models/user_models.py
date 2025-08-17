import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    String,
    Enum,
)

from app.database import Base
from app.database.enums.user_enums import UserTypeEnum

class UserModel(Base):
    __tablename__ = 'users'

    user_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    name = Column(String, nullable=False)



    user_type = Column(Enum(UserTypeEnum), nullable=False, default=UserTypeEnum.trader)
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    trades_bought = relationship("Trade", back_populates="buyer", foreign_keys="Trade.buy_user_id")
    trades_sold = relationship("Trade", back_populates="seller", foreign_keys="Trade.sell_user_id")
