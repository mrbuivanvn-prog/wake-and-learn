from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from .database import engine, Base, get_db
from .models import User, Card, StudySession
from .schemas import UserCreate, UserResponse, CardCreate, CardResponse
from .ai_service import AIService
from .image_service import ImageService
from .spaced_repetition import SpacedRepetition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo bảng trong database
Base.metadata.create_all(bind=engine)

# Khởi tạo services
ai_service = AIService()
image_service = ImageService()
sr_service = SpacedRepetition()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App started")
    yield
    logger.info("App shutting down")

app = FastAPI(
    title="Wake and Learn API",
    description="AI-powered spaced repetition learning system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= USER ENDPOINTS =============
@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra username đã tồn tại
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Tạo user mới
    new_user = User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ============= CARD ENDPOINTS =============
@app.post("/api/cards", response_model=CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    # Kiểm tra user tồn tại
    user = db.query(User).filter(User.id == card.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Tạo card mới
    new_card = Card(
        user_id=card.user_id,
        question=card.question,
        answer=card.answer,
        topic=card.topic,
        difficulty=card.difficulty or "medium"
    )
    
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card

@app.get("/api/users/{user_id}/cards")
def get_user_cards(user_id: int, db: Session = Depends(get_db)):
    cards = db.query(Card).filter(Card.user_id == user_id).all()
    return cards

@app.get("/api/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card

@app.delete("/api/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    db.delete(card)
    db.commit()
    return {"message": "Card deleted successfully"}

@app.get("/api/users/{user_id}/due-cards")
def get_due_cards(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    due_cards = db.query(Card).filter(
        Card.user_id == user_id,
        Card.next_review <= now
    ).all()
    return due_cards

@app.post("/api/study-sessions")
def create_study_session(session_data: dict, db: Session = Depends(get_db)):
    # Kiểm tra card tồn tại
    card = db.query(Card).filter(Card.id == session_data.get("card_id")).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Tính next_review
    next_review = sr_service.calculate_next_review(
        ease_factor=session_data.get("ease_factor", 2.5),
        interval=session_data.get("interval", 1),
        repetitions=session_data.get("repetitions", 0)
    )
    
    # Tạo study session
    new_session = StudySession(
        card_id=session_data.get("card_id"),
        user_id=session_data.get("user_id"),
        ease_factor=session_data.get("ease_factor", 2.5),
        interval=session_data.get("interval", 1),
        repetitions=session_data.get("repetitions", 0),
        next_review=next_review,
        reviewed_at=datetime.now()
    )
    
    # Cập nhật card next_review
    card.next_review = next_review
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
