from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from auth import create_access_token, hash_password
from coingecko import CoinGeckoError, get_coingecko_client
from config import get_settings
from database import Base, get_db
from db_models import User
from main import app


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        (
            "post",
            "/transactions",
            {
                "symbol": "BTC",
                "coingecko_id": "bitcoin",
                "quantity": "0.25",
                "transaction_type": "buy",
            },
        ),
        ("get", "/transactions", None),
        ("get", "/transactions/1", None),
        ("get", "/portfolio/current_value", None),
    ],
)
def test_transaction_routes_require_authenticated_user(
    method: str,
    path: str,
    json: dict[str, str] | None,
) -> None:
    client = build_test_client()

    response = client.request(method, path, json=json)

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_login_returns_bearer_token_for_test_user() -> None:
    client = build_test_client()

    response = client.post(
        "/auth/login",
        json={"username": "user-1", "password": "test-password"},
    )

    assert response.status_code == 200
    token_response = response.json()
    assert token_response["token_type"] == "bearer"
    assert token_response["access_token"]


def test_login_rejects_invalid_test_user_password() -> None:
    client = build_test_client()

    response = client.post(
        "/auth/login",
        json={"username": "user-1", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


@pytest.mark.parametrize("token_headers", ["malformed", "expired"])
def test_transaction_routes_reject_malformed_or_expired_tokens(
    token_headers: str,
) -> None:
    client = build_test_client()
    headers = (
        {"Authorization": "Bearer not-a-valid-token"}
        if token_headers == "malformed"
        else expired_token_headers()
    )

    response = client.get("/transactions", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_create_and_list_transactions() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    create_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "buy",
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    created_transaction = create_response.json()
    assert created_transaction["id"] == 1
    assert created_transaction["symbol"] == "BTC"
    assert created_transaction["coingecko_id"] == "bitcoin"
    assert created_transaction["name"] is None
    assert created_transaction["transaction_type"] == "buy"
    assert created_transaction["purchase_price_usd"] == "67000.12"
    assert "current_price_usd" not in created_transaction
    assert created_transaction["purchased_at"]

    list_response = client.get("/transactions", headers=headers)

    assert list_response.status_code == 200
    transactions = list_response.json()
    assert len(transactions) == 1
    assert transactions[0]["id"] == created_transaction["id"]


def test_get_transaction_by_id() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    buy_response = client.post(
        "/transactions",
        json={
            "symbol": "ETH",
            "coingecko_id": "ethereum",
            "name": "Ethereum",
            "quantity": "1.5",
            "transaction_type": "buy",
        },
        headers=headers,
    )
    assert buy_response.status_code == 201

    create_response = client.post(
        "/transactions",
        json={
            "symbol": "ETH",
            "coingecko_id": "ethereum",
            "name": "Ethereum",
            "quantity": "1.5",
            "transaction_type": "sell",
        },
        headers=headers,
    )
    transaction_id = create_response.json()["id"]

    get_response = client.get(f"/transactions/{transaction_id}", headers=headers)

    assert get_response.status_code == 200
    transaction = get_response.json()
    assert transaction["id"] == transaction_id
    assert transaction["symbol"] == "ETH"
    assert transaction["coingecko_id"] == "ethereum"
    assert transaction["name"] == "Ethereum"
    assert transaction["transaction_type"] == "sell"


def test_create_transaction_allows_sell_when_enough_coin_is_owned() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    buy_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "buy",
        },
        headers=headers,
    )
    assert buy_response.status_code == 201

    sell_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "sell",
        },
        headers=headers,
    )

    assert sell_response.status_code == 201
    assert sell_response.json()["transaction_type"] == "sell"


def test_create_transaction_rejects_sell_when_not_enough_coin_is_owned() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    buy_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.10",
            "transaction_type": "buy",
        },
        headers=headers,
    )
    assert buy_response.status_code == 201

    sell_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "sell",
        },
        headers=headers,
    )

    assert sell_response.status_code == 400
    assert sell_response.json() == {
        "detail": "Cannot sell 0.25 BTC; only 0.100000000000 owned"
    }


def test_get_transaction_returns_404_for_missing_id() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    response = client.get("/transactions/999", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}


def test_transaction_queries_are_scoped_to_authenticated_user() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    create_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "buy",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    user_one_transaction_id = create_response.json()["id"]

    user_two_headers = authenticated_headers("user-2")

    list_response = client.get("/transactions", headers=user_two_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    get_response = client.get(
        f"/transactions/{user_one_transaction_id}",
        headers=user_two_headers,
    )
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Transaction not found"}

    portfolio_response = client.get(
        "/portfolio/current_value",
        headers=user_two_headers,
    )
    assert portfolio_response.status_code == 200
    assert portfolio_response.json() == {"coins": [], "total_value_usd": "0"}

    sell_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "sell",
        },
        headers=user_two_headers,
    )
    assert sell_response.status_code == 400
    assert sell_response.json() == {"detail": "Cannot sell 0.25 BTC; only 0 owned"}


def test_create_transaction_returns_502_when_price_fetch_fails() -> None:
    client = build_test_client(coingecko_client=FailingCoinGeckoClient())
    headers = authenticated_headers()

    response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "buy",
        },
        headers=headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "CoinGecko request failed"}


def test_create_transaction_rejects_invalid_transaction_type() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.25",
            "transaction_type": "transfer",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_get_current_portfolio_value_groups_transactions_and_batches_prices() -> None:
    coingecko_client = FakeCoinGeckoClient(
        prices={
            "bitcoin": Decimal("70000.00"),
            "ethereum": Decimal("3000.00"),
        }
    )
    client = build_test_client(coingecko_client=coingecko_client)
    headers = authenticated_headers()

    for payload in [
        {
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.50",
            "transaction_type": "buy",
        },
        {
            "symbol": "BTC",
            "coingecko_id": "bitcoin",
            "quantity": "0.10",
            "transaction_type": "sell",
        },
        {
            "symbol": "ETH",
            "coingecko_id": "ethereum",
            "quantity": "2.00",
            "transaction_type": "buy",
        },
    ]:
        response = client.post("/transactions", json=payload, headers=headers)
        assert response.status_code == 201

    coingecko_client.batch_price_requests.clear()
    response = client.get("/portfolio/current_value", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "coins": [
            {
                "symbol": "BTC",
                "coingecko_id": "bitcoin",
                "quantity": "0.400000000000",
                "current_price_usd": "70000.00",
                "total_value_usd": "28000.00000000000000",
            },
            {
                "symbol": "ETH",
                "coingecko_id": "ethereum",
                "quantity": "2.000000000000",
                "current_price_usd": "3000.00",
                "total_value_usd": "6000.00000000000000",
            },
        ],
        "total_value_usd": "34000.00000000000000",
    }
    assert coingecko_client.batch_price_requests == [["bitcoin", "ethereum"]]


def test_get_current_portfolio_value_returns_empty_portfolio() -> None:
    client = build_test_client()
    headers = authenticated_headers()

    response = client.get("/portfolio/current_value", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"coins": [], "total_value_usd": "0"}


def build_test_client(coingecko_client: object | None = None) -> TestClient:
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

    with testing_session_local() as db:
        create_test_user(db, "user-1")
        create_test_user(db, "user-2")
        db.commit()

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_coingecko_client] = (
        lambda: coingecko_client or FakeCoinGeckoClient()
    )
    app.state.testing_session_local = testing_session_local
    return TestClient(app)


def create_test_user(db: Session, username: str) -> User:
    user = User(
        username=username,
        hashed_password=hash_password("test-password"),
        is_active=True,
    )
    db.add(user)
    return user


def authenticated_headers(username: str = "user-1") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(username)}"}


def expired_token_headers(username: str = "user-1") -> dict[str, str]:
    settings = get_settings()
    token = jwt.encode(
        {"sub": username, "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


class FakeCoinGeckoClient:
    def __init__(self, prices: dict[str, Decimal] | None = None) -> None:
        self.prices = prices or {
            "bitcoin": Decimal("67000.12"),
            "ethereum": Decimal("67000.12"),
        }
        self.batch_price_requests: list[list[str]] = []

    def get_current_price_usd(self, coingecko_id: str) -> Decimal:
        return self.get_current_prices_usd([coingecko_id])[coingecko_id]

    def get_current_prices_usd(self, coingecko_ids: list[str]) -> dict[str, Decimal]:
        self.batch_price_requests.append(coingecko_ids)
        return {
            coingecko_id: self.prices[coingecko_id]
            for coingecko_id in coingecko_ids
        }


class FailingCoinGeckoClient:
    def get_current_price_usd(self, coingecko_id: str) -> Decimal:
        raise CoinGeckoError("CoinGecko request failed")
