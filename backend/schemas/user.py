from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: str
    password: str
    name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    job: Optional[str] = None
    interests: Optional[list[str]] = None
    location: Optional[str] = None
    goals: Optional[str] = None
    ai_name: Optional[str] = None
    ai_personality: Optional[str] = None
    theme: Optional[str] = None
    wake_word: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    age: Optional[int] = None
    job: str
    interests: list[str]
    location: str
    goals: str
    ai_name: str
    ai_personality: str
    theme: str
    wake_word: str
    created_at: datetime

    class Config:
        from_attributes = True
