from __future__ import annotations

import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.db import get_db
from backend.deps import get_user_id
from backend.models import User
from backend.security import PASSWORD_PATTERN, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=256)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Enter your full name.")
        return name

    @field_validator("password")
    @classmethod
    def password_rules(cls, value: str) -> str:
        if not re.match(PASSWORD_PATTERN, value):
            raise ValueError("Password must be at least 8 characters with letters, a number, and a symbol.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember: bool = False


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name or "")


def _token_response(user: User, remember: bool = False) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id=user.id, email=user.email, remember=remember),
        user=_user_out(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(body.email).strip().lower()
    user = User(
        id=uuid4(),
        email=email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.") from exc
    db.refresh(user)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(body.email).strip().lower()
    user = db.exec(select(User).where(User.email == email)).first()
    if user is None or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return _token_response(user, remember=body.remember)


@router.get("/me", response_model=UserOut)
def me(user_id: UUID = Depends(get_user_id), db: Session = Depends(get_db)) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return _user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
