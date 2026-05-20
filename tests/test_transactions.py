from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


def test_create_and_list_transactions() -> None:
    client = build_test_client()

    create_response = client.post(
        "/transactions",
        json={
            "symbol": "BTC",
            "quantity": "0.25",
            "purchase_price_usd": "65000.00",
        },
    )

    assert create_response.status_code == 201
    created_transaction = create_response.json()
    assert created_transaction["id"] == 1
    assert created_transaction["symbol"] == "BTC"
    assert created_transaction["name"] is None
    assert created_transaction["purchased_at"]

    list_response = client.get("/transactions")

    assert list_response.status_code == 200
    transactions = list_response.json()
    assert len(transactions) == 1
    assert transactions[0]["id"] == created_transaction["id"]


def test_get_transaction_by_id() -> None:
    client = build_test_client()

    create_response = client.post(
        "/transactions",
        json={
            "symbol": "ETH",
            "name": "Ethereum",
            "quantity": "1.5",
            "purchase_price_usd": "3200.00",
        },
    )
    transaction_id = create_response.json()["id"]

    get_response = client.get(f"/transactions/{transaction_id}")

    assert get_response.status_code == 200
    transaction = get_response.json()
    assert transaction["id"] == transaction_id
    assert transaction["symbol"] == "ETH"
    assert transaction["name"] == "Ethereum"


def test_get_transaction_returns_404_for_missing_id() -> None:
    client = build_test_client()

    response = client.get("/transactions/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}


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

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
