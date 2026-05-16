from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CardBase(BaseModel):
    question: str
    answer: str
    topic: Optional[str] = None
    difficulty: str = "medium"

class CardCreate(CardBase):
    user_id: int

class CardResponse(CardBase):
    id: int
    user_id: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    next_review: datetime
    
    class Config:
        from_attributes = True
