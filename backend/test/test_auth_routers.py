import uuid

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from sqlalchemy.exc import IntegrityError

from app.api.routers.auth_routers import router as auth_router
from app.database.enums.user_enums import UserTypeEnum
from app.schemas.auth_schemas import (
    UserSignupResponseSchema,
    UserLoginResponseSchema
)

# Create test app with router
app = FastAPI()
app.include_router(auth_router)
client = TestClient(app)

class TestAuthRouters:
     
     @patch('app.api.routers.auth_routers.AuthService.signup')
     @patch('app.api.routers.auth_routers.get_db_session')
     def test_signup_success(self, mock_db, mock_signup):
         # Arrange
         mock_db.return_value = Mock()
         test_uuid = uuid.uuid4()
         mock_signup.return_value = UserSignupResponseSchema(
             user_id=test_uuid,
             email="test@example.com",
             name="Test User",
             user_type=UserTypeEnum.trader
         )
         
         # Act
         response = client.post("/signup", json={
             "email": "test@example.com",
             "password": "password123",
             "name": "Test User"
         })
         
         # Assert
         assert response.status_code == 201
         data = response.json()
        # top‐level envelope
         assert data["message"] == "User created successfully"
        # actual payload under "data"
         assert data["data"]["email"] == "test@example.com"
         assert data["data"]["name"] == "Test User"
 
     @patch('app.api.routers.auth_routers.AuthService.signup')
     @patch('app.api.routers.auth_routers.get_db_session')
     def test_signup_duplicate_email(self, mock_db, mock_signup):
         # Arrange
         mock_db.return_value = Mock()
         mock_signup.side_effect = IntegrityError("Email already exists", None, None)
         
         # Act
         response = client.post("/signup", json={
             "email": "existing@example.com",
             "password": "password123",
             "name": "Test User"
         })
         
         # Assert
         assert response.status_code == 409
         assert response.json()["message"] == "User email already exists"
 
     @patch('app.api.routers.auth_routers.AuthService.login')
     @patch('app.api.routers.auth_routers.get_db_session')
     def test_login_success(self, mock_db, mock_login):
         # Arrange
         mock_db.return_value = Mock()
         mock_login.return_value = UserLoginResponseSchema(
             access_token="access_token_123",
             refresh_token="refresh_token_123"
         )
         
         # Act
         response = client.post("/login", json={
             "email": "test@example.com",
             "password": "password123"
         })
         
         # Assert
         assert response.status_code == 200
         data = response.json()
        # top‐level envelope
         assert data["message"] == "User logged in successfully"
        # actual payload under "data"
         assert data["data"]["access_token"] == "access_token_123"
         assert data["data"]["refresh_token"] == "refresh_token_123"
 
     @patch('app.api.routers.auth_routers.AuthService.login')
     @patch('app.api.routers.auth_routers.get_db_session')
     def test_login_invalid_credentials(self, mock_db, mock_login):
         # Arrange
         mock_db.return_value = Mock()
         mock_login.side_effect = ValueError("Invalid email or password")
         
         # Act
         response = client.post("/login", json={
             "email": "test@example.com",
             "password": "wrongpassword"
         })
         
         # Assert
         assert response.status_code == 401
