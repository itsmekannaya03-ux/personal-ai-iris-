from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..models.subscription import Subscription, PlanEnum, StatusEnum
from ..models.payment import Payment, PaymentStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # In production, verify Stripe signature here
    event = json.loads(payload)

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("client_reference_id")
        if user_id:
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.status = StatusEnum.active
                if session.get("mode") == "payment":
                    sub.plan = PlanEnum.lifetime
                else:
                    sub.plan = PlanEnum.student

                payment = Payment(
                    user_id=user_id,
                    amount=session.get("amount_total", 0),
                    currency=session.get("currency", "INR"),
                    status=PaymentStatus.completed,
                    payment_method="stripe",
                )
                db.add(payment)
                await db.commit()

    return {"status": "ok"}


@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    event = json.loads(payload)

    if event.get("event") == "payment.captured":
        payment_data = event["payload"]["payment"]["entity"]
        user_id = payment_data.get("notes", {}).get("user_id")
        if user_id:
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.status = StatusEnum.active

                payment = Payment(
                    user_id=user_id,
                    amount=payment_data.get("amount", 0),
                    currency=payment_data.get("currency", "INR"),
                    status=PaymentStatus.completed,
                    payment_method="razorpay",
                )
                db.add(payment)
                await db.commit()

    return {"status": "ok"}
