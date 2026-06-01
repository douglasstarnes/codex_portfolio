from datetime import UTC, datetime, timedelta

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from jose import jwt

from auth import (
    create_access_token,
    decode_access_token,
    get_current_token_data,
    hash_password,
    verify_password,
)
from config import get_settings
from models import TokenData


def test_hash_password_verifies_password() -> None:
    hashed_password = hash_password("correct-horse-battery-staple")

    assert hashed_password != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed_password) is True
    assert verify_password("incorrect-password", hashed_password) is False


def test_create_and_decode_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")

    token = create_access_token("satoshi")
    token_data = decode_access_token(token)

    assert token_data == TokenData(username="satoshi")


def test_create_access_token_accepts_integer_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")

    token = create_access_token(123)
    token_data = decode_access_token(token)

    assert token_data.username == "123"


def test_decode_access_token_rejects_expired_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    settings = get_settings()
    expired_token = jwt.encode(
        {"sub": "satoshi", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)

    assert exc_info.value.status_code == 401


def test_decode_access_token_rejects_invalid_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-valid-token")

    assert exc_info.value.status_code == 401


def test_decode_access_token_rejects_missing_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(None)

    assert exc_info.value.status_code == 401


def test_bearer_dependency_extracts_authorization_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    app = FastAPI()

    @app.get("/protected")
    def protected(
        token_data: TokenData = Depends(get_current_token_data),
    ) -> dict[str, str | None]:
        return {"username": token_data.username}

    client = TestClient(app)
    token = create_access_token("satoshi")

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"username": "satoshi"}


def test_bearer_dependency_rejects_missing_header() -> None:
    app = FastAPI()

    @app.get("/protected")
    def protected(
        token_data: TokenData = Depends(get_current_token_data),
    ) -> dict[str, str | None]:
        return {"username": token_data.username}

    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 401
