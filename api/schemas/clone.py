from pydantic import BaseModel
from typing import Optional


class CloneResponse(BaseModel):
    id: str
    base_model_version: str
    os_type: Optional[str] = None
    last_active: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class InstallerResponse(BaseModel):
    profile: dict
    model: str
    ai_name: str
    theme: str
    wake_word: str
