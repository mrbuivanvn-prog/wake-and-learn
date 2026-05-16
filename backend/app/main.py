from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
import uuid
import jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .database import get_db, init_db
from .models import User, UserSettings, VocabularyGroup, Vocabulary, UserLearning
from .ai_service import ai_service

app = FastAPI(title="Wake & Learn API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Khởi tạo database
init_db()


SECRET_KEY = "supersecretkey_change_me"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



from datetime import datetime

def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(401, "Invalid token")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

@app.get("/")
def root():
    return {"message": "Wake & Learn API", "version": "3.0"}

from pydantic import BaseModel
class LoginRequest(BaseModel):
    username: str
    password: str

class BatchWordRequest(BaseModel):
    words: List[str]
    language: str = "en"

@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")
    token = create_access_token({"sub": str(user.id)})
    return {"token": token, "user_id": user.id, "username": user.username}

@app.post("/auth/register")
def register(req: LoginRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(400, "Username exists")
    hashed_pwd = get_password_hash(req.password)
    user = User(username=req.username, password=hashed_pwd)
    db.add(user)
    db.flush()
    settings = UserSettings(user_id=user.id, daily_goal=5)
    db.add(settings)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"token": token, "user_id": user.id, "username": req.username}

@app.post("/words/batch-ai")
def add_words_batch_ai(req: BatchWordRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """Thêm nhiều từ - AI tự động dịch và tạo nội dung"""
    
    group_name = "Default_ZH" if req.language == "zh" else "Default_EN"
    group = db.query(VocabularyGroup).filter(VocabularyGroup.name == group_name, VocabularyGroup.created_by_user == False).first()
    if not group:
        group = VocabularyGroup(name=group_name, language=req.language, profession="general")
        db.add(group)
        db.flush()
    
    results = []
    for word in req.words:
        word = word.strip().lower()
        if not word:
            continue
        
        # Kiểm tra trùng
        existing = db.query(Vocabulary).filter(Vocabulary.word == word).first()
        if existing:
            continue
        
        # Gọi AI
        meaning = ai_service.translate(word, lang=req.language)
        example_data = ai_service.example(word, meaning, lang=req.language)
        cloze_text = ai_service.cloze(word, example_data["en"], lang=req.language)
        conversation = ai_service.conversation(word, lang=req.language)
        import urllib.parse
        image_prompt = urllib.parse.quote(f"cute cartoon illustration of {word}, vibrant colors, simple, white background")
        image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=400&height=400&nologo=true"
        
        vocab = Vocabulary(
            group_id=group.id,
            word=word,
            meaning=meaning,
            pronunciation=f"/{word}/",
            level="A1",
            example=example_data["en"],
            example_vi=example_data["vi"],
            conversation=conversation,
            cloze_text=cloze_text,
            image_url=image_url
        )
        db.add(vocab)
        db.flush()
        
        learning = UserLearning(vocab_id=vocab.id, user_id=user_id, next_review=date.today())
        db.add(learning)
        
        results.append({"word": word, "meaning": meaning})
    
    db.commit()
    return {"added": len(results), "words": results}

@app.get("/words/today")
def get_today_words(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    today = date.today()
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    limit = settings.daily_goal if settings else 5
    
    learning_list = db.query(UserLearning, Vocabulary, VocabularyGroup)\
        .join(Vocabulary, UserLearning.vocab_id == Vocabulary.id)\
        .join(VocabularyGroup, Vocabulary.group_id == VocabularyGroup.id)\
        .filter(UserLearning.user_id == user_id, UserLearning.next_review <= today)\
        .limit(limit)\
        .all()
    
    words = []
    
    # Get a pool of all meanings for multiple choice distractors
    all_meanings = [m[0] for m in db.query(Vocabulary.meaning).filter(Vocabulary.meaning != None).distinct().all()]
    default_distractors = ["tuyệt vời", "khó khăn", "vui vẻ", "thông minh", "nhanh nhẹn", "đẹp đẽ", "nhà cửa", "thời gian", "kết quả", "bắt đầu"]
    if len(all_meanings) < 10:
        all_meanings.extend(default_distractors)
        
    for learning, vocab, group in learning_list:
        # Lấy nghĩa chính (nghĩa đầu tiên) để hiển thị trên nút trắc nghiệm
        primary_meaning = vocab.meaning.split(',')[0].strip() if vocab.meaning else ""
        
        distractors = [m.split(',')[0].strip() for m in all_meanings if m and m.split(',')[0].strip() != primary_meaning]
        import random
        selected_distractors = random.sample(distractors, min(len(distractors), 3))
        
        options = [primary_meaning] + selected_distractors
        random.shuffle(options)
        
        words.append({
            "id": vocab.id,
            "word": vocab.word,
            "meaning": vocab.meaning,
            "primary_meaning": primary_meaning,
            "pronunciation": vocab.pronunciation,
            "example": vocab.example or "",
            "example_vi": vocab.example_vi or "",
            "conversation": vocab.conversation or "",
            "cloze_text": vocab.cloze_text or "",
            "image_url": vocab.image_url or "",
            "mastery": learning.mastery,
            "language": group.language,
            "options": options
        })
    
    return {"words": words, "count": len(words), "goal": limit}

@app.post("/words/learn")
def learn_word(vocab_id: int, is_correct: bool, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    
    learning = db.query(UserLearning).filter(UserLearning.vocab_id == vocab_id, UserLearning.user_id == user_id).first()
    if not learning:
        raise HTTPException(404, "Word not found")
    
    if is_correct:
        learning.mastery = min(1.0, learning.mastery + 0.15)
        learning.review_interval = min(30, learning.review_interval * 2)
        learning.consecutive_correct += 1
    else:
        learning.mastery = max(0.0, learning.mastery - 0.2)
        learning.review_interval = max(1, learning.review_interval // 2)
        learning.consecutive_correct = 0
    
    learning.next_review = date.today() + timedelta(days=learning.review_interval)
    learning.is_mastered = learning.mastery >= 0.8 and learning.consecutive_correct >= 3
    
    db.commit()
    return {"mastery": learning.mastery, "is_mastered": learning.is_mastered}

@app.get("/stats/dashboard")
def get_dashboard(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    today = date.today()
    
    today_words = db.query(UserLearning).filter(UserLearning.user_id == user_id, UserLearning.next_review <= today).count()
    total_words = db.query(Vocabulary).count()
    mastered_words = db.query(UserLearning).filter(UserLearning.user_id == user_id, UserLearning.is_mastered == True).count()
    
    weak_words = db.query(UserLearning, Vocabulary)\
        .join(Vocabulary, UserLearning.vocab_id == Vocabulary.id)\
        .filter(UserLearning.user_id == user_id, UserLearning.mastery < 0.4)\
        .limit(5)\
        .all()
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    streak = settings.streak_days if settings else 0
    
    return {
        "today_new_words": 5,
        "today_review_words": today_words,
        "streak": streak,
        "progress": {
            "total": total_words,
            "mastered": mastered_words,
            "percentage": round(mastered_words/total_words*100, 1) if total_words > 0 else 0
        },
        "weak_words": [{"word": vocab.word, "mastery": learning.mastery} for learning, vocab in weak_words]
    }

@app.post("/ai/conversation")
def generate_conversation(words: List[str]):
    conversation = ai_service.conversation(words[0]) if words else ""
    return {"conversation": conversation}

@app.get("/words/all")
def get_all_words(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    words = db.query(Vocabulary).all()
    return [{"id": w.id, "word": w.word, "meaning": w.meaning} for w in words]

@app.post("/user/settings")
def update_settings(daily_goal: int, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if settings:
        settings.daily_goal = daily_goal
        db.commit()
    return {"message": "Settings updated"}


from sqlalchemy.sql import func
import random

class SubmitAnswerRequest(BaseModel):
    vocab_id: int
    answer: str

@app.get("/exercises/fill-blank")
def get_fill_blank(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    # Pick 5 vocabularies that have cloze_text
    vocabs = db.query(Vocabulary).filter(Vocabulary.cloze_text != None, Vocabulary.cloze_text != '').order_by(func.random()).limit(5).all()
    res = []
    for v in vocabs:
        res.append({
            "vocab_id": v.id,
            "cloze_text": v.cloze_text,
            "example_vi": v.example_vi
        })
    return res

@app.post("/exercises/fill-blank/submit")
def submit_fill_blank(req: SubmitAnswerRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    vocab = db.query(Vocabulary).filter(Vocabulary.id == req.vocab_id).first()
    if not vocab:
        raise HTTPException(404, "Vocabulary not found")
        
    correct = vocab.word.lower() == req.answer.lower().strip()
    
    # Update learning mastery if user has learned this word
    learning = db.query(UserLearning).filter(UserLearning.vocab_id == vocab.id, UserLearning.user_id == user_id).first()
    if learning:
        if correct:
            learning.mastery = min(1.0, learning.mastery + 0.15)
            learning.consecutive_correct += 1
        else:
            learning.mastery = max(0.0, learning.mastery - 0.2)
            learning.consecutive_correct = 0
        db.commit()    
    return {"correct": correct, "correct_answer": vocab.word if not correct else ""}

if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("🚀 Wake & Learn API v3.0")
    print("="*50)
    print("📝 Demo: demo / demo123")
    print("🌐 http://localhost:8000")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
