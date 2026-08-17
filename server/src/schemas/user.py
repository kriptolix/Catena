from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    fullname: str
    is_admin: int = 0
    active: int = 1


class UserCreate(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    is_admin: Optional[int] = None
    active: Optional[int] = None
    hashed_password: Optional[str] = None


class User(UserBase):
    id: int
    creation_date: datetime

    model_config = ConfigDict(from_attributes=True)