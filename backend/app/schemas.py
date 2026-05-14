from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None

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
    difficulty: Optional[str] = Field("medium")

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

class StudySessionBase(BaseModel):
    card_id: int
    ease_factor: float = Field(default=2.5, ge=1.3)
    interval: int = Field(default=1, ge=1)
    repetitions: int = Field(default=0, ge=0)

class StudySessionCreate(StudySessionBase):
    pass

class StudySessionResponse(StudySessionBase):
    id: int
    user_id: int
    next_review: datetime
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
