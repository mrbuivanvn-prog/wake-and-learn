from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import ollama
import json

from .database import engine, Base, get_db
from .models import User, Card, StudySession
from .image_service import ImageService
from .spaced_repetition import SpacedRepetition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

image_service = ImageService()
sr_service = SpacedRepetition()

app = FastAPI(title="Wake and Learn API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ HEALTH ============
@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ============ USER ============
@app.post("/api/users")
def create_user(username: str, email: str, db: Session = Depends(get_db)):
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email}

@app.get("/api/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

# ============ CARD ============
@app.post("/api/cards")
def create_card(card_data: dict, db: Session = Depends(get_db)):
    try:
        user_id = card_data.get("user_id")
        question = card_data.get("question")
        answer = card_data.get("answer")
        topic = card_data.get("topic", "General")
        difficulty = card_data.get("difficulty", "medium")
        
        logger.info(f"📝 Saving card: {question} -> {answer}")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, f"User {user_id} not found")
        
        card = Card(
            user_id=user_id,
            question=question,
            answer=answer,
            topic=topic,
            difficulty=difficulty
        )
        
        db.add(card)
        db.commit()
        db.refresh(card)
        
        logger.info(f"✅ Card saved: id={card.id}")
        return {"id": card.id, "question": card.question, "answer": card.answer, "topic": card.topic}
    except Exception as e:
        logger.error(f"Error saving card: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/users/{user_id}/cards")
def get_cards(user_id: int, db: Session = Depends(get_db)):
    return db.query(Card).filter(Card.user_id == user_id).all()

@app.get("/api/users/{user_id}/due-cards")
def get_due_cards(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    return db.query(Card).filter(Card.user_id == user_id, Card.next_review <= now).all()

# ============ STUDY SESSION ============
@app.post("/api/study-sessions")
def create_study_session(session_data: dict, db: Session = Depends(get_db)):
    card_id = session_data.get("card_id")
    user_id = session_data.get("user_id")
    quality = session_data.get("quality", 1)
    
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    
    interval = quality == 2 and 3 or (quality == 1 and 1 or 0)
    from datetime import timedelta
    card.next_review = datetime.now() + timedelta(days=interval)
    
    session = StudySession(
        card_id=card_id,
        user_id=user_id,
        ease_factor=2.5,
        interval=interval,
        repetitions=1,
        next_review=card.next_review,
        reviewed_at=datetime.now()
    )
    
    db.add(session)
    db.commit()
    return {"status": "ok"}

# ============ AI GENERATE CARD (có tiếng Việt) ============
@app.post("/api/ai/generate-card")
def generate_card(word: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).first()
        if not user:
            user = User(username="demo", email="demo@example.com")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Prompt yêu cầu AI trả về cả tiếng Anh và tiếng Việt
        prompt = f"""Create a bilingual flashcard for the word "{word}".
        
Return ONLY valid JSON in this format:
{{
    "question_en": "What is the meaning of '{word}'?",
    "answer_vi": "nghĩa của từ {word}",
    "question_vi": "'{word}' nghĩa là gì?",
    "answer_en": "meaning of {word}",
    "examples_en": ["Example sentence 1", "Example sentence 2"],
    "examples_vi": ["Ví dụ câu 1", "Ví dụ câu 2"]
}}

Make it useful for learning English-Vietnamese."""
        
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7}
        )
        
        text = response['message']['content'].strip()
        text = text.replace('```json', '').replace('```', '')
        
        try:
            card_data = json.loads(text)
        except:
            card_data = {
                "question_en": f"What is {word}?",
                "answer_vi": f"{word}",
                "examples_en": [f"This is an example with {word}"],
                "examples_vi": [f"Đây là ví dụ với {word}"]
            }
        
        # Tạo card với cả hai ngôn ngữ
        card = Card(
            user_id=user.id,
            question=card_data.get("question_en", f"What is {word}?"),
            answer=card_data.get("answer_vi", word),
            topic="Vocabulary",
            difficulty="medium"
        )
        
        db.add(card)
        db.commit()
        db.refresh(card)
        
        return {
            "card": {
                "id": card.id,
                "question": card.question,
                "answer": card.answer,
                "question_vi": card_data.get("question_vi", f"'{word}' nghĩa là gì?"),
                "answer_en": card_data.get("answer_en", word),
                "examples_en": card_data.get("examples_en", []),
                "examples_vi": card_data.get("examples_vi", [])
            }
        }
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
