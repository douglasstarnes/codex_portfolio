from datetime import UTC, datetime
from decimal import Decimal

from models import InvestmentCreate


def test_investment_create_defaults_optional_fields() -> None:
    before_create = datetime.now(UTC)

    investment = InvestmentCreate(
        symbol="BTC",
        coingecko_id="bitcoin",
        quantity=Decimal("0.25"),
        transaction_type="buy",
    )

    after_create = datetime.now(UTC)

    assert investment.name is None
    assert before_create <= investment.purchased_at <= after_create


def test_investment_create_allows_explicit_optional_fields() -> None:
    purchased_at = datetime(2026, 1, 1, tzinfo=UTC)

    investment = InvestmentCreate(
        symbol="ETH",
        coingecko_id="ethereum",
        name="Ethereum",
        quantity=Decimal("1.5"),
        transaction_type="sell",
        purchased_at=purchased_at,
    )

    assert investment.name == "Ethereum"
    assert investment.transaction_type == "sell"
    assert investment.purchased_at == purchased_at
