from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.db.repositories.user_repository import (
    create_user_with_password,
    get_user_by_email,
)
from app.db.session import get_db
from app.schemas.auth import AuthUserRead, RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(db=db, email=payload.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = create_user_with_password(
        db=db,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    access_token = create_access_token(user_id=user.id)

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db=db, email=form_data.username)

    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(
        plain_password=form_data.password,
        password_hash=user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id)

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=AuthUserRead)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user