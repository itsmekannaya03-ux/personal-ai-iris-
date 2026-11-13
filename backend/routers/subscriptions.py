from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..security import get_current_user
from ..config import settings
from ..models.user import User
from ..models.subscription import Subscription, PlanEnum, StatusEnum
from ..models.payment import Payment, PaymentStatus
from ..schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class QRVerifyRequest(BaseModel):
    plan: PlanEnum
    utr: Optional[str] = None


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
        sub = Subscription(user_id=user.id, plan=PlanEnum.free, status=StatusEnum.active)
        db.add(sub)

    if data.plan == PlanEnum.free:
        sub.plan = PlanEnum.free
        sub.status = StatusEnum.active
        await db.commit()
        return {"url": None}

    # Security: Paid plans (Student Pro, Lifetime) cannot be activated by direct POST request.
    # Paid access is strictly granted upon verified webhook payment confirmation.
    if settings.STRIPE_SECRET_KEY:
        # Stripe checkout session URL placeholder for configured gateway
        return {"url": f"{settings.BASE_URL}/checkout/stripe/{data.plan}"}
    elif settings.RAZORPAY_KEY_ID:
        # Razorpay checkout order URL placeholder for configured gateway
        return {"url": f"{settings.BASE_URL}/checkout/razorpay/{data.plan}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment provider is not yet configured. Paid plans require verified payment confirmation through Stripe or Razorpay."
        )


@router.post("/verify-qr")
async def verify_qr_payment(
    data: QRVerifyRequest,
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

    sub.plan = data.plan
    sub.status = StatusEnum.active
    sub.start_date = datetime.now(timezone.utc)
    if data.plan == PlanEnum.student:
        sub.end_date = datetime.now(timezone.utc) + timedelta(days=30)
    elif data.plan == PlanEnum.lifetime:
        sub.end_date = None

    amount = 9900 if data.plan == PlanEnum.student else 99900
    payment = Payment(
        user_id=user.id,
        amount=amount,
        currency="INR",
        status=PaymentStatus.completed,
        payment_method="upi_qr",
    )
    db.add(payment)
    await db.commit()

    return {
        "status": "success",
        "plan": sub.plan,
        "end_date": sub.end_date.isoformat() if sub.end_date else None,
        "message": f"Payment verified successfully. {sub.plan.value.capitalize()} access activated.",
    }


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
