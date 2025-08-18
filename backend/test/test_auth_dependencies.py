import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from jose import jwt
from unittest.mock import patch, MagicMock
import uuid

from app.core import auth_dependencies
from app.database.models.user_models import UserModel

# --- Fixtures ---

@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/user")
    async def get_user(user=Depends(auth_dependencies.get_current_user)):
        return {"user_id": str(user.user_id)}

    @app.get("/admin")
    async def get_admin(user=Depends(auth_dependencies.get_current_admin_user)):
        return {"user_id": str(user.user_id)}

    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def fake_user():
    user = MagicMock(spec=UserModel)
    user.user_id = uuid.uuid4()
    user.user_type.value = "user"
    return user

@pytest.fixture
def fake_admin():
    user = MagicMock(spec=UserModel)
    user.user_id = uuid.uuid4()
    user.user_type.value = "admin"
    return user

@pytest.fixture
def valid_token(fake_user):
    payload = {"user_id": str(fake_user.user_id)}
    return jwt.encode(payload, auth_dependencies.config.JWT_SECRET_KEY, algorithm=auth_dependencies.config.ALGORITHM)

@pytest.fixture
def admin_token(fake_admin):
    payload = {"user_id": str(fake_admin.user_id)}
    return jwt.encode(payload, auth_dependencies.config.JWT_SECRET_KEY, algorithm=auth_dependencies.config.ALGORITHM)

# --- Tests ---

def test_get_current_user_success(client, valid_token, fake_user):
    with patch("app.database.get_db_session") as mock_db:
        mock_db.return_value = iter([MagicMock(query=lambda model: MagicMock(filter=lambda *a, **k: MagicMock(first=lambda: fake_user)))])
        response = client.get("/user", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code == 200
        assert response.json()["user_id"] == str(fake_user.user_id)

def test_get_current_user_invalid_token(client):
    response = client.get("/user", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

def test_get_current_user_missing_user_id(client, valid_token):
    # Token without user_id
    payload = {}
    token = jwt.encode(payload, auth_dependencies.config.JWT_SECRET_KEY, algorithm=auth_dependencies.config.ALGORITHM)
    response = client.get("/user", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

def test_get_current_user_user_not_found(client, valid_token):
    with patch("app.database.get_db_session") as mock_db:
        mock_db.return_value = iter([MagicMock(query=lambda model: MagicMock(filter=lambda *a, **k: MagicMock(first=lambda: None)))])
        response = client.get("/user", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

def test_get_current_admin_user_success(client, admin_token, fake_admin):
    with patch("app.database.get_db_session") as mock_db:
        mock_db.return_value = iter([MagicMock(query=lambda model: MagicMock(filter=lambda *a, **k: MagicMock(first=lambda: fake_admin)))])
        response = client.get("/admin", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert response.json()["user_id"] == str(fake_admin.user_id)

def test_get_current_admin_user_forbidden(client, valid_token, fake_user):
    with patch("app.database.get_db_session") as mock_db:
        mock_db.return_value = iter([MagicMock(query=lambda model: MagicMock(filter=lambda *a, **k: MagicMock(first=lambda: fake_user)))])
        response = client.get("/admin", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"