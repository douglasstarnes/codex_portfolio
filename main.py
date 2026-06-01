from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from auth_routes import router as auth_router
from coingecko import (
    CoinGeckoClient,
    CoinGeckoConfigError,
    CoinGeckoError,
    CoinGeckoPriceNotFoundError,
    get_coingecko_client,
)
from database import Base, engine, get_db
from db_models import InvestmentTransaction, User
from models import CoinValue, Investment, InvestmentCreate, PortfolioValue


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Codex Portfolio", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/transactions", response_model=Investment, status_code=201)
def create_transaction(
    investment: InvestmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    coingecko_client: CoinGeckoClient = Depends(get_coingecko_client),
) -> InvestmentTransaction:
    if investment.transaction_type == "sell":
        existing_transactions = db.scalars(
            select(InvestmentTransaction).where(
                InvestmentTransaction.coingecko_id == investment.coingecko_id
            )
        ).all()
        owned_quantity = sum(
            (
                transaction.quantity
                if transaction.transaction_type == "buy"
                else -transaction.quantity
                for transaction in existing_transactions
            ),
            Decimal("0"),
        )
        if owned_quantity < investment.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot sell {investment.quantity} {investment.symbol}; "
                    f"only {owned_quantity} owned"
                ),
            )

    try:
        purchase_price_usd = coingecko_client.get_current_price_usd(investment.coingecko_id)
    except CoinGeckoConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CoinGeckoPriceNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CoinGeckoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    transaction = InvestmentTransaction(
        **investment.model_dump(),
        purchase_price_usd=purchase_price_usd,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@app.get("/transactions", response_model=list[Investment])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InvestmentTransaction]:
    return list(db.scalars(select(InvestmentTransaction)).all())


@app.get("/portfolio/current_value", response_model=PortfolioValue)
def get_current_portfolio_value(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    coingecko_client: CoinGeckoClient = Depends(get_coingecko_client),
) -> PortfolioValue:
    transactions = list(db.scalars(select(InvestmentTransaction)).all())
    net_quantities: dict[str, Decimal] = {}
    symbols: dict[str, str] = {}

    for transaction in transactions:
        multiplier = Decimal("1") if transaction.transaction_type == "buy" else Decimal("-1")
        net_quantities[transaction.coingecko_id] = (
            net_quantities.get(transaction.coingecko_id, Decimal("0"))
            + (transaction.quantity * multiplier)
        )
        symbols[transaction.coingecko_id] = transaction.symbol

    net_quantities = {
        coingecko_id: quantity
        for coingecko_id, quantity in net_quantities.items()
        if quantity != Decimal("0")
    }

    try:
        current_prices = coingecko_client.get_current_prices_usd(list(net_quantities))
    except CoinGeckoConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CoinGeckoPriceNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CoinGeckoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    coins = [
        CoinValue(
            symbol=symbols[coingecko_id],
            coingecko_id=coingecko_id,
            quantity=quantity,
            current_price_usd=current_prices[coingecko_id],
            total_value_usd=quantity * current_prices[coingecko_id],
        )
        for coingecko_id, quantity in net_quantities.items()
    ]

    return PortfolioValue(
        coins=coins,
        total_value_usd=sum(
            (coin.total_value_usd for coin in coins),
            Decimal("0"),
        ),
    )


@app.get("/transactions/{transaction_id}", response_model=Investment)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvestmentTransaction:
    transaction = db.get(InvestmentTransaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction
