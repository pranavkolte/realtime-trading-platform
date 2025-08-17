import uuid

from fastapi import Form
from pydantic import BaseModel, EmailStr

from app.database.enums.user_enums import UserTypeEnum


class OAuth2EmailRequestForm:
    def __init__(
        self,
        email: str = Form(...),
        password: str = Form(...),
        scope: str = Form(""),
        client_id: str = Form(None),
        client_secret: str = Form(None),
    ):
        self.email = email
        self.password = password
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret


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
    