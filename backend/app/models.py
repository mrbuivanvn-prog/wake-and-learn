from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    cards = relationship("Card", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    question_vn = Column(Text, nullable=True)
    answer_en = Column(Text, nullable=True)
    topic = Column(String(200))
    image_url = Column(String(500))
    examples_en = Column(Text, nullable=True)
    examples_vn = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    next_review = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="cards")
    study_sessions = relationship("StudySession", back_populates="card", cascade="all, delete-orphan")

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ease_factor = Column(Float, default=2.5)
    interval = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    reviewed_at = Column(DateTime)
    
    card = relationship("Card", back_populates="study_sessions")
    user = relationship("User", back_populates="study_sessions")
