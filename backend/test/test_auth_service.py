import uuid
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.services.auth_service import AuthService
from app.database.enums.user_enums import UserTypeEnum  # << add this
from app.database.models.user_models import UserModel
from app.schemas.auth_schemas import (
    UserSignupRequestSchema,
    UserSignupResponseSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
)


class TestAuthService:

    @pytest.mark.asyncio
    @patch("app.api.services.auth_service.hash_password")
    async def test_signup_success(self, mock_hash_password):
        # Arrange
        mock_db = Mock(spec=Session)
        (mock_db.query.return_value.filter.return_value.first.return_value) = (
            None
        )
        mock_hash_password.return_value = "hashed_password123"

        signup_data = UserSignupRequestSchema(
            email="test@example.com", password="password123", name="Test User"
        )

        # make refresh assign a real UUID
        example_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
        mock_db.refresh.return_value = None

        # Act
        with patch.object(UserModel, "__init__", return_value=None):
            with patch.object(mock_db, "add"), patch.object(mock_db, "commit"):
                with patch.object(mock_db, "refresh") as mock_refresh:
                    mock_refresh.side_effect = lambda user: setattr(
                        user, "user_id", example_uuid
                    )

                    # Mock the user object
                    mock_user_instance = Mock()
                    mock_user_instance.user_id = example_uuid  # << UUID
                    mock_user_instance.email = "test@example.com"
                    mock_user_instance.name = "Test User"
                    mock_user_instance.user_type = (
                        UserTypeEnum.trader
                    )  # << valid enum

                    with patch(
                        "app.api.services.auth_service.UserModel",
                        return_value=mock_user_instance,
                    ):
                        result = await AuthService.signup(mock_db, signup_data)

        # Assert
        assert isinstance(result, UserSignupResponseSchema)
        assert result.user_id == example_uuid
        assert result.user_type == UserTypeEnum.trader
        assert result.email == "test@example.com"
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self):
        # Arrange
        mock_db = Mock(spec=Session)
        existing_user = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_user
        )

        signup_data = UserSignupRequestSchema(
            email="existing@example.com",
            password="password123",
            name="Test User",
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            await AuthService.signup(mock_db, signup_data)

    @pytest.mark.asyncio
    @patch("app.api.services.auth_service.verify_password")
    @patch("app.api.services.auth_service.create_auth_token")
    async def test_login_success(
        self, mock_create_token, mock_verify_password
    ):
        # Arrange
        mock_db = Mock(spec=Session)
        mock_user = Mock()
        mock_user.password = "hashed_password"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        mock_verify_password.return_value = True
        mock_create_token.return_value = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
        }

        login_data = UserLoginRequestSchema(
            email="test@example.com", password="password123"
        )

        # Act
        result = await AuthService.login(mock_db, login_data)

        # Assert
        assert isinstance(result, UserLoginResponseSchema)
        assert result.access_token == "access_token_123"
        assert result.refresh_token == "refresh_token_123"

    @pytest.mark.asyncio
    @patch("app.api.services.auth_service.verify_password")
    async def test_login_invalid_credentials(self, mock_verify_password):
        # Arrange
        mock_db = Mock(spec=Session)
        mock_user = Mock()
        mock_user.password = "hashed_password"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )
        mock_verify_password.return_value = False

        login_data = UserLoginRequestSchema(
            email="test@example.com", password="wrongpassword"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            await AuthService.login(mock_db, login_data)
