from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvestmentBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16, examples=["BTC"])
    name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Bitcoin"])
    quantity: Decimal = Field(..., gt=0, examples=["0.25"])
    purchase_price_usd: Decimal = Field(..., gt=0, examples=["65000.00"])
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=16, examples=["ETH"])
    name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Ethereum"])
    quantity: Decimal | None = Field(default=None, gt=0, examples=["1.5"])
    purchase_price_usd: Decimal | None = Field(default=None, gt=0, examples=["3200.00"])
    purchased_at: datetime | None = None


class Investment(InvestmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
