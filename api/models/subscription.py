import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..core.database import Base


class PlanEnum(str, enum.Enum):
    free = "free"
    student = "student"
    lifetime = "lifetime"


class StatusEnum(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    expired = "expired"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    plan: Mapped[PlanEnum] = mapped_column(SAEnum(PlanEnum), default=PlanEnum.free)
    status: Mapped[StatusEnum] = mapped_column(SAEnum(StatusEnum), default=StatusEnum.active)
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscription")
