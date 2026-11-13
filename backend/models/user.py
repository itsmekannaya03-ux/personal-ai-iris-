import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    job: Mapped[str] = mapped_column(String(255), default="")
    interests: Mapped[str] = mapped_column(ARRAY(String), default=list)
    location: Mapped[str] = mapped_column(String(255), default="")
    goals: Mapped[str] = mapped_column(Text, default="")
    ai_name: Mapped[str] = mapped_column(String(100), default="IRIS")
    ai_personality: Mapped[str] = mapped_column(String(50), default="casual")
    theme: Mapped[str] = mapped_column(String(50), default="blob")
    wake_word: Mapped[str] = mapped_column(String(50), default="hey iris")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    subscription = relationship("Subscription", back_populates="user", uselist=False)
    clones = relationship("Clone", back_populates="user")
    payments = relationship("Payment", back_populates="user")
