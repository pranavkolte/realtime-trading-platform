from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models.user_models import UserModel
from app.util.auth_util import (
    hash_password, 
    verify_password,
    create_auth_token, 
)
from app.schemas.auth_schemas import (
    UserSignupRequestSchema, 
    UserSignupResponseSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
)


class AuthService:
    @staticmethod
    async def signup(db_session: Session, signup_request_data: UserSignupRequestSchema) -> UserSignupResponseSchema:
        try:
            existing_user: UserModel = db_session.query(UserModel).filter(UserModel.email == signup_request_data.email).first()
            if existing_user:
                raise IntegrityError("Email already exists", None, None)
            
            hashed_password: str = await hash_password(signup_request_data.password)
            user = UserModel(
                email=signup_request_data.email,
                password=hashed_password,
                name=signup_request_data.name,
                user_type=signup_request_data.user_type
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            return UserSignupResponseSchema(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                user_type=user.user_type
            )
        except IntegrityError as e:
            db_session.rollback()
            raise e
        except Exception as e:
            db_session.rollback()
            raise e
        
    @staticmethod
    async def login(db_session: Session, login_request_data: UserLoginRequestSchema) -> UserLoginResponseSchema:
        user: UserModel = db_session.query(UserModel).filter(UserModel.email == login_request_data.email).first()
        if not user or not await verify_password(plain_password=login_request_data.password, hashed_password=user.password):
            raise ValueError("Invalid email or password")
        auth_tokens: dict = await create_auth_token(user=user)
        return UserLoginResponseSchema(
            access_token=auth_tokens["access_token"],
            refresh_token=auth_tokens["refresh_token"]
        )
    