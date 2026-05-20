from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from db_models import InvestmentTransaction
from models import Investment, InvestmentCreate


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Codex Portfolio", lifespan=lifespan)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/transactions", response_model=Investment, status_code=201)
def create_transaction(
    investment: InvestmentCreate,
    db: Session = Depends(get_db),
) -> InvestmentTransaction:
    transaction = InvestmentTransaction(**investment.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@app.get("/transactions", response_model=list[Investment])
def list_transactions(db: Session = Depends(get_db)) -> list[InvestmentTransaction]:
    return list(db.scalars(select(InvestmentTransaction)).all())


@app.get("/transactions/{transaction_id}", response_model=Investment)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
) -> InvestmentTransaction:
    transaction = db.get(InvestmentTransaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction
