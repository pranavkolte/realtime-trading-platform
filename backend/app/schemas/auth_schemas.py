import uuid

from pydantic import BaseModel, EmailStr

from app.database.enums.user_enums import UserTypeEnum


class UserSignupRequestSchema(BaseModel):
    email: EmailStr
    password: str
    name: str
    user_type: UserTypeEnum = UserTypeEnum.trader 

class UserSignupResponseSchema(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    name: str
    user_type: UserTypeEnum
    

class UserLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    