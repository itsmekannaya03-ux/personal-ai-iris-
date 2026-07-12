from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.subscription import Subscription, PlanEnum, StatusEnum
from ..schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/create")
async def create_subscription(
    data: SubscriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        sub = Subscription(user_id=user.id)
        db.add(sub)

    if data.plan == PlanEnum.free:
        sub.plan = PlanEnum.free
        sub.status = StatusEnum.active
        await db.commit()
        return {"url": None}

    # For paid plans, return a Stripe Checkout URL
    # In production, create a Stripe Checkout Session here
    prices = {
        PlanEnum.student: 9900,    # ₹99 in paise
        PlanEnum.lifetime: 99900,  # ₹999 in paise
    }

    # Placeholder: directly activate for testing
    sub.plan = data.plan
    sub.status = StatusEnum.active
    await db.commit()

    return {"url": "/dashboard/download"}


@router.get("/status", response_model=SubscriptionResponse)
async def subscription_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        sub = Subscription(user_id=user.id)
        db.add(sub)
        await db.commit()

    return SubscriptionResponse.model_validate(sub)
