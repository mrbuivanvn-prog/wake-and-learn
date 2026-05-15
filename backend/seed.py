#!/usr/bin/env python
from app.database import SessionLocal, engine, Base
from app.models import User, Card, StudySession
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    # Tạo bảng
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    db = SessionLocal()
    
    try:
        # Kiểm tra đã có dữ liệu chưa
        existing_user = db.query(User).filter(User.username == "demo_user").first()
        if existing_user:
            logger.info("Database already seeded")
            return
        
        # Tạo user demo
        demo_user = User(
            username="demo_user",
            email="demo@example.com"
        )
        db.add(demo_user)
        db.flush()
        
        # Tạo cards mẫu
        cards_data = [
            {
                "question": "What is the capital of France?",
                "answer": "Paris is the capital and most populous city of France.",
                "topic": "Geography",
                "difficulty": "easy"
            },
            {
                "question": "What is the chemical formula for water?",
                "answer": "H2O - Water is composed of two hydrogen atoms and one oxygen atom.",
                "topic": "Chemistry",
                "difficulty": "easy"
            },
            {
                "question": "Who wrote Romeo and Juliet?",
                "answer": "William Shakespeare wrote Romeo and Juliet.",
                "topic": "Literature",
                "difficulty": "medium"
            },
            {
                "question": "What is 2 + 2?",
                "answer": "4",
                "topic": "Mathematics",
                "difficulty": "easy"
            }
        ]
        
        for card_data in cards_data:
            card = Card(
                user_id=demo_user.id,
                question=card_data["question"],
                answer=card_data["answer"],
                topic=card_data["topic"],
                difficulty=card_data["difficulty"],
                next_review=datetime.now()
            )
            db.add(card)
        
        db.commit()
        logger.info("Successfully seeded database")
        print("✅ Database seeded successfully!")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        print(f"❌ Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
