from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ..database import get_db
from ..security import hash_password, verify_password, create_token, create_refresh_token, decode_refresh_token, get_current_user
from ..models.user import User
from ..models.subscription import Subscription, PlanEnum
from ..schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    token: str
    refresh_token: str
    user: UserResponse


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.flush()

    sub = Subscription(user_id=user.id, plan=PlanEnum.free)
    db.add(sub)

    await db.commit()
    await db.refresh(user)

    token = create_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return {"token": token, "refresh_token": refresh_token, "user": UserResponse.model_validate(user)}


@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return {"token": token, "refresh_token": refresh_token, "user": UserResponse.model_validate(user)}


@router.post("/refresh")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user_id = decode_refresh_token(data.refresh_token)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_token = create_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return {"token": new_token, "refresh_token": new_refresh, "user": UserResponse.model_validate(user)}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
