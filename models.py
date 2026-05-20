from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransactionType = Literal["buy", "sell"]


class InvestmentBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16, examples=["BTC"])
    coingecko_id: str = Field(..., min_length=1, max_length=100, examples=["bitcoin"])
    name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Bitcoin"])
    quantity: Decimal = Field(..., gt=0, examples=["0.25"])
    transaction_type: TransactionType = Field(..., examples=["buy"])
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=16, examples=["ETH"])
    coingecko_id: str | None = Field(default=None, min_length=1, max_length=100, examples=["ethereum"])
    name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Ethereum"])
    quantity: Decimal | None = Field(default=None, gt=0, examples=["1.5"])
    transaction_type: TransactionType | None = Field(default=None, examples=["sell"])
    purchase_price_usd: Decimal | None = Field(default=None, gt=0, examples=["3200.00"])
    purchased_at: datetime | None = None


class Investment(InvestmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_price_usd: Decimal


class CoinValue(BaseModel):
    symbol: str
    coingecko_id: str
    quantity: Decimal
    current_price_usd: Decimal
    total_value_usd: Decimal


class PortfolioValue(BaseModel):
    coins: list[CoinValue]
    total_value_usd: Decimal
