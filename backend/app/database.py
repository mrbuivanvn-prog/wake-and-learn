from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Đường dẫn database
DATABASE_URL = "sqlite:///./database/wakeandlearn.db"

# Tạo engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Cần cho SQLite
)

# Tạo session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho models
Base = declarative_base()

# Dependency để lấy session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
