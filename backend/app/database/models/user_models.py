import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    Column,
    String,
)
from sqlalchemy import Enum

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
    