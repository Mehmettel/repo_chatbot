"""
Kimlik doğrulama - BLUEPRINT core/security; ADR-006 JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.db import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models import User

router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Yeni kullanıcı kaydı; token döner."""
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kayıtlı",
        )
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """E-posta ve şifre ile giriş; token döner."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
        )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Giriş yapmış kullanıcı bilgisi."""
    return UserResponse(id=str(user.id), email=user.email)


@router.post("/ensure-demo")
async def ensure_demo_user():
    """
    Örnek kullanıcıyı (deneme@gmail.com / deneme) oluşturur veya şifresini günceller.
    Giriş yapamıyorsanız bu endpoint'i çağırın (tarayıcıdan veya curl ile).
    """
    try:
        from app.seed_user import seed_default_user
        seed_default_user()
        return {"ok": True, "message": "Örnek hesap hazır. deneme@gmail.com / deneme ile giriş yapın."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Örnek hesap oluşturulamadı. Docker ve veritabanının çalıştığından emin olun: {str(e)}",
        )
