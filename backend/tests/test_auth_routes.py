from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from auth import decode_access_token, verify_password
from database import Base, get_db
from db_models import User
from main import app


def test_register_creates_user_with_hashed_password() -> None:
    client = build_test_client()

    response = client.post(
        "/auth/register",
        json={
            "username": "satoshi",
            "email": "satoshi@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 201
    created_user = response.json()
    assert created_user["id"] == 1
    assert created_user["username"] == "satoshi"
    assert created_user["email"] == "satoshi@example.com"
    assert created_user["is_active"] is True
    assert "password" not in created_user
    assert "hashed_password" not in created_user

    with client.app.state.testing_session_local() as db:
        db_user = db.get(User, created_user["id"])
        assert db_user is not None
        assert db_user.hashed_password != "correct-horse-battery-staple"
        assert verify_password("correct-horse-battery-staple", db_user.hashed_password)


def test_register_rejects_duplicate_username() -> None:
    client = build_test_client()
    payload = {
        "username": "satoshi",
        "email": "satoshi@example.com",
        "password": "correct-horse-battery-staple",
    }

    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post(
        "/auth/register",
        json={**payload, "email": "other@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}


def test_register_rejects_duplicate_email() -> None:
    client = build_test_client()
    payload = {
        "username": "satoshi",
        "email": "satoshi@example.com",
        "password": "correct-horse-battery-staple",
    }

    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post(
        "/auth/register",
        json={**payload, "username": "nakamoto"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


def test_login_returns_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    client = build_test_client()
    register_response = client.post(
        "/auth/register",
        json={
            "username": "satoshi",
            "password": "correct-horse-battery-staple",
        },
    )
    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "username": "satoshi",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 200
    token_response = response.json()
    assert token_response["token_type"] == "bearer"
    assert token_response["access_token"]
    assert decode_access_token(token_response["access_token"]).username == "satoshi"


def test_login_rejects_invalid_credentials() -> None:
    client = build_test_client()
    register_response = client.post(
        "/auth/register",
        json={
            "username": "satoshi",
            "password": "correct-horse-battery-staple",
        },
    )
    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "username": "satoshi",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def build_test_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session_local = testing_session_local
    return TestClient(app)
