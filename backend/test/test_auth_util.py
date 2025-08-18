import pytest
from unittest.mock import MagicMock

from app.database.models import UserModel
from app.util import auth_util
from jwt.exceptions import InvalidTokenError


@pytest.fixture
def sample_user():
    user = MagicMock(spec=UserModel)
    user.email = "test@example.com"
    user.user_id = 1
    user_type = MagicMock()
    user_type.value = "trader"
    user.user_type = user_type
    return user


@pytest.mark.asyncio
async def test_hash_password_returns_hashed_string():
    pw = "secret"
    hashed = await auth_util.hash_password(pw)
    assert isinstance(hashed, str)
    assert hashed != pw


@pytest.mark.asyncio
async def test_verify_password_success(monkeypatch):
    monkeypatch.setattr(
        auth_util.password_context, "verify", lambda secret, hash: True
    )
    assert await auth_util.verify_password("pw", "hashed")


@pytest.mark.asyncio
async def test_verify_password_failure(monkeypatch):
    monkeypatch.setattr(
        auth_util.password_context, "verify", lambda secret, hash: False
    )
    assert not await auth_util.verify_password("pw", "hashed")


def test_decode_access_token_valid(monkeypatch):
    payload = {"sub": "test"}
    monkeypatch.setattr(auth_util.jwt, "decode", lambda *a, **k: payload)
    assert auth_util.decode_access_token("token") == payload


def test_decode_access_token_expired(monkeypatch):
    class Expired(Exception):
        pass

    monkeypatch.setattr(auth_util.jwt, "ExpiredSignatureError", Expired)
    monkeypatch.setattr(
        auth_util.jwt,
        "decode",
        lambda *a, **k: (_ for _ in ()).throw(Expired()),
    )
    with pytest.raises(ValueError, match="expired"):
        auth_util.decode_access_token("token")


def test_decode_access_token_invalid(monkeypatch):
    monkeypatch.setattr(
        auth_util.jwt,
        "decode",
        lambda *a, **k: (_ for _ in ()).throw(InvalidTokenError()),
    )
    with pytest.raises(ValueError, match="Invalid token"):
        auth_util.decode_access_token("token")


@pytest.mark.asyncio
async def test_create_auth_token_returns_tokens(sample_user, monkeypatch):
    monkeypatch.setattr(
        auth_util.jwt,
        "encode",
        lambda payload, key, algorithm: f"token-{payload['sub']}",
    )
    tokens = await auth_util.create_auth_token(sample_user)
    assert "access_token" in tokens and "refresh_token" in tokens
    assert tokens["access_token"].startswith("token-")
