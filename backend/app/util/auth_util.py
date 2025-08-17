from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import config
from app.database.models import UserModel

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str) -> str:
    return password_context.hash(secret=password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(secret=plain_password, hash=hashed_password)

def decode_access_token(token: str) -> dict:
    """Decode and validate access token"""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.JWTError:
        raise ValueError("Invalid token")

async def create_auth_token(user: UserModel) -> dict[str, str]:

    access_expire_time = datetime.now(tz=timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token_payload: str = {
        "sub": user.email,
        "user_id": str(user.user_id),
        "exp": access_expire_time
    }
    refresh_token_payload: dict = {
        "sub": user.email,
        "user_id": str(user.user_id),
        "exp": access_expire_time + timedelta(days=7)
    }

    access_token = jwt.encode(access_token_payload, config.JWT_SECRET_KEY, algorithm=config.ALGORITHM)
    refresh_token = jwt.encode(refresh_token_payload, config.JWT_SECRET_KEY, algorithm=config.ALGORITHM)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
