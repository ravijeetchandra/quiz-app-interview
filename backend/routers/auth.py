from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User
from schemas import UserRegister, UserLogin, TokenResponse, TokenRefresh, UserOut
from auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, blacklist_token, get_current_user
import uuid
import time
from datetime import timedelta
from config import settings
from collections import defaultdict

router = APIRouter(prefix="/api/auth", tags=["Auth"])

login_attempts = defaultdict(list)
LOGIN_WINDOW = 60
LOGIN_MAX_ATTEMPTS = 5


def _check_login_rate_limit(ip: str):
    now = time.time()
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < LOGIN_WINDOW]
    if len(login_attempts[ip]) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait 60 seconds.")


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name or data.email.split("@")[0],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_ip)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        login_attempts[client_ip].append(time.time())
        raise HTTPException(status_code=401, detail="Invalid email or password")

    login_attempts[client_ip] = []

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    old_jti = payload.get("jti")
    if old_jti:
        blacklist_token(old_jti)

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=new_access, refresh_token=new_refresh, user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(token_data: dict = Depends(decode_token)):
    jti = token_data.get("jti")
    if jti:
        blacklist_token(jti)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserOut.model_validate(user)
