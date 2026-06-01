from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import create_access_token, hash_password, verify_password
from database import get_db
from db_models import User
from models import LoginRequest, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    duplicate_filters = [User.username == user.username]
    if user.email is not None:
        duplicate_filters.append(User.email == user.email)

    existing_user = db.scalar(select(User).where(or_(*duplicate_filters)))
    if existing_user is not None:
        if existing_user.username == user.username:
            detail = "Username already registered"
        else:
            detail = "Email already registered"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        ) from exc

    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login_for_access_token(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    user = db.scalar(select(User).where(User.username == credentials.username))
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.username))
