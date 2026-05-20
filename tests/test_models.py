from datetime import UTC, datetime
from decimal import Decimal

from models import InvestmentCreate


def test_investment_create_defaults_optional_fields() -> None:
    before_create = datetime.now(UTC)

    investment = InvestmentCreate(
        symbol="BTC",
        quantity=Decimal("0.25"),
        purchase_price_usd=Decimal("65000.00"),
    )

    after_create = datetime.now(UTC)

    assert investment.name is None
    assert before_create <= investment.purchased_at <= after_create


def test_investment_create_allows_explicit_optional_fields() -> None:
    purchased_at = datetime(2026, 1, 1, tzinfo=UTC)

    investment = InvestmentCreate(
        symbol="ETH",
        name="Ethereum",
        quantity=Decimal("1.5"),
        purchase_price_usd=Decimal("3200.00"),
        purchased_at=purchased_at,
    )

    assert investment.name == "Ethereum"
    assert investment.purchased_at == purchased_at
