from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    email = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)

class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    alarm_mode = Column(String(20), default="soft")
    daily_goal = Column(Integer, default=5)
    profession = Column(String(100), default="Công nghệ thông tin (IT)")
    learning_language = Column(String(10), default="en")
    streak_days = Column(Integer, default=0)
    last_learned = Column(Date)

class VocabularyGroup(Base):
    __tablename__ = "vocabulary_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    language = Column(String(10), nullable=False)
    profession = Column(String(100))
    created_by_user = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class Vocabulary(Base):
    __tablename__ = "vocabularies"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("vocabulary_groups.id"))
    word = Column(String(200), nullable=False, index=True)  # Index for word lookup
    word_en = Column(String(200), index=True)
    word_zh = Column(String(200), index=True)
    pinyin = Column(String(200))
    meaning = Column(Text)
    pronunciation = Column(String(200))
    mode = Column(String(20), default="en", index=True)  # Index for mode filtering
    level = Column(String(20))
    example = Column(Text)
    example_zh = Column(Text)
    example_vi = Column(Text)
    conversation = Column(Text)
    cloze_text = Column(Text, index=True)  # Index for exercises
    image_url = Column(Text)

class UserLearning(Base):
    __tablename__ = "user_learning"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Primary lookup
    vocab_id = Column(Integer, ForeignKey("vocabularies.id"), index=True)  # Foreign key index
    mastery = Column(Float, default=0.0, index=True)  # Index for mastery filtering
    review_interval = Column(Integer, default=1)
    next_review = Column(Date, default=date.today, index=True)  # CRITICAL: For due cards query
    is_mastered = Column(Boolean, default=False)
    consecutive_correct = Column(Integer, default=0)
    last_reviewed = Column(DateTime, default=datetime.now)
    
    # Composite index for common query pattern
    __table_args__ = (
        Index('ix_userlearning_user_vocab', 'user_id', 'vocab_id'),
        Index('ix_userlearning_user_mastery', 'user_id', 'mastery'),
    )
