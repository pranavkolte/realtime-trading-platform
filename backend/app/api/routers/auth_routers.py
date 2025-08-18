from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.api.services.auth_service import AuthService
from app.database import get_db_session
from app.schemas.auth_schemas import (
    UserSignupRequestSchema,
    UserSignupResponseSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
)

router = APIRouter()


@router.post(
    path="/signup",
    response_model=UserSignupResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def signup_user(
    signup_data: UserSignupRequestSchema,
    db_session: Session = Depends(get_db_session),
) -> JSONResponse:
    try:
        user: UserSignupResponseSchema = await AuthService.signup(
            db_session=db_session, signup_request_data=signup_data
        )
        return JSONResponse(
            content={
                "message": "User created successfully",
                "data": user.model_dump(mode="json"),
            },
            status_code=status.HTTP_201_CREATED,
        )

    except IntegrityError as e:
        return JSONResponse(
            content={"message": "User email already exists", "error": str(e)},
            status_code=status.HTTP_409_CONFLICT,
        )

    except Exception as e:
        return JSONResponse(
            content={"message": "User creation failed", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    path="/login",
    response_model=UserLoginResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def login_user(
    signin_data: UserLoginRequestSchema,
    db_session: Session = Depends(get_db_session),
) -> JSONResponse:
    try:
        user: UserLoginResponseSchema = await AuthService.login(
            db_session=db_session, login_request_data=signin_data
        )
        return JSONResponse(
            content={
                "message": "User logged in successfully",
                "data": user.model_dump(mode="json"),
            },
            status_code=status.HTTP_200_OK,
        )

    except ValueError as e:
        return JSONResponse(
            content={"message": "Login failed", "error": str(e)},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return JSONResponse(
            content={"message": "Login failed", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
