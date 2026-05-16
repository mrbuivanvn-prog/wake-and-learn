from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class VocabularyGroupCreate(BaseModel):
    name: str
    language: str
    profession: str
    words: List[dict]

class LearningSession(BaseModel):
    vocab_id: int
    is_correct: bool
    pronunciation_score: Optional[float] = None

class AlarmConfig(BaseModel):
    mode: str  # 'soft', 'strict', 'hardcore'
    ringtone: str
    wake_up_hour: int
    wake_up_minute: int

class UserGoal(BaseModel):
    target_words: int
    target_days: int
