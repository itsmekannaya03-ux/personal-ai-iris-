import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Clone(Base):
    __tablename__ = "clones"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    base_model_version: Mapped[str] = mapped_column(String(50), default="llama3.2:3b")
    profile_snapshot: Mapped[str] = mapped_column(Text, default="{}")
    installer_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    os_type: Mapped[str] = mapped_column(String(50), nullable=True)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="clones")
