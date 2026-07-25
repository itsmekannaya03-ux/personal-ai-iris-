from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ..models.subscription import PlanEnum


class SubscriptionCreate(BaseModel):
    plan: PlanEnum


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True
