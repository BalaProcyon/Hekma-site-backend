from pydantic import BaseModel
from typing import TypeVar

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}

