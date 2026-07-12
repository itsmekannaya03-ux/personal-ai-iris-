from pydantic import BaseModel
from typing import Optional
from ..models.subscription import PlanEnum


class SubscriptionCreate(BaseModel):
    plan: PlanEnum


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    class Config:
        from_attributes = True
