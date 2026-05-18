from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List
import uuid
import jwt
import requests
import urllib.parse
import bcrypt
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
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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

@app.get("/auth/me")
def get_me(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return {"username": user.username}

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
    
    # Determine group name based on actual language, not just zh vs en
    if req.language == "zh":
        group_name = "Default_ZH"
    else:
        group_name = "Default_EN"
    
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
        
        # CẤU HÌNH THÔNG MINH: Tự động khởi tạo nếu người dùng chưa chọn mục tiêu
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id, daily_goal=5, profession="Tổng quát", learning_language=req.language)
            db.add(settings)
            db.flush()
            
        mode = settings.learning_language if settings.learning_language else req.language
        profession = settings.profession if settings.profession else "Tổng quát"
        
        pinyin = ""
        pronunciation = ""
        
        if mode == "trilingual":
            # CHẾ ĐỘ 3 NGÔN NGỮ (EN - ZH - VI) - Prompt cực kỳ nghiêm ngặt
            data = ai_service.translate_trilingual(word, profession=profession)
            word_en = data.get("en", word)
            word_zh = data.get("zh", word)
            pinyin = data.get("pinyin", "")
            meaning = data.get("vi", word)
            
            # Fetch English IPA
            pronunciation = ai_service.get_phonetics(word_en, lang="en")
            
            # BẮT BUỘC AI phải dùng đúng từ trong câu ví dụ để bài tập điền từ hoạt động
            ex_data = ai_service.example_trilingual(word_en, word_zh, meaning, profession=profession)
            example_en = ex_data.get("en", "")
            example_zh = ex_data.get("zh", "")
            example_vi = ex_data.get("vi", "")
            
            # Tạo cloze text từ ví dụ tiếng Anh (hoặc Trung tùy chế độ)
            cloze_text = ai_service.cloze(word_en, example_en)
            if "_____" not in cloze_text and word_zh:
                cloze_text = ai_service.cloze(word_zh, example_zh)
            
            conversation = f"EN: {example_en}\nZH: {example_zh}\nVI: {example_vi}"
        elif mode == "zh":
            # CHẾ ĐỘ TIẾNG TRUNG - VIỆT (ZH - VI)
            # Translate the word to get Chinese meaning
            meaning = ai_service.translate(word, lang="zh", profession=profession)
            example_data = ai_service.example(word, meaning, lang="zh", profession=profession)
            cloze_text = ai_service.cloze(word, example_data.get("zh", ""), lang="zh")
            word_zh = word  # The input word IS the Chinese word
            pinyin = ai_service.get_phonetics(word, lang="zh")
            pronunciation = pinyin
            word_en = ""
            example_en = ""
            example_zh = example_data.get("zh", "")
            example_vi = example_data.get("vi", "")
            conversation = ai_service.conversation(word, lang="zh", profession=profession)
        else:
            # CHẾ ĐỘ TIẾNG ANH - VIỆT (EN - VI)
            meaning = ai_service.translate(word, lang="en", profession=profession)
            example_data = ai_service.example(word, meaning, lang="en", profession=profession)
            cloze_text = ai_service.cloze(word, example_data["en"], lang="en")
            conversation = ai_service.conversation(word, lang="en", profession=profession)
            word_en = word
            word_zh = ""
            pinyin = ""
            pronunciation = ai_service.get_phonetics(word, lang="en")
            example_en = example_data["en"]
            example_zh = ""
            example_vi = example_data["vi"]

        image_prompt = urllib.parse.quote(f"cute 3D render of {word}, modern simple professional style, white background")
        image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=400&height=400&nologo=true"
        
        vocab = Vocabulary(
            group_id=group.id,
            word=word,
            word_en=word_en,
            word_zh=word_zh,
            pinyin=pinyin,
            meaning=meaning,
            pronunciation=pronunciation if pronunciation else f"/{word}/",
            mode=mode,
            level="A1",
            example=example_en if mode not in ["zh", "trilingual"] else example_zh,
            example_zh=example_zh,
            example_vi=example_vi,
            conversation=conversation,
            cloze_text=cloze_text,
            image_url=image_url
        )
        db.add(vocab)
        db.flush()
        
        learning = UserLearning(user_id=user_id, vocab_id=vocab.id, next_review=date.today())
        db.add(learning)
        
        results.append({"word": word, "meaning": meaning})
    
    db.commit()
    return {"added": len(results), "words": results}

class CreateManualCardRequest(BaseModel):
    word: str
    meaning: str

@app.post("/words")
def create_manual_card(req: CreateManualCardRequest, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    group_name = "Manual"
    group = db.query(VocabularyGroup).filter(VocabularyGroup.name == group_name).first()
    if not group:
        group = VocabularyGroup(name=group_name, language="en", profession="general", created_by_user=True)
        db.add(group)
        db.flush()
    
    vocab = Vocabulary(
        group_id=group.id,
        word=req.word,
        word_en=req.word,
        meaning=req.meaning,
        mode="en"
    )
    db.add(vocab)
    db.flush()
    
    learning = UserLearning(user_id=user_id, vocab_id=vocab.id, next_review=date.today())
    db.add(learning)
    db.commit()
    return {"message": "Card created", "id": vocab.id}

@app.get("/words/today")
def get_today_words(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    today = date.today()
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    limit = settings.daily_goal if settings else 5
    
    learning_list = db.query(UserLearning, Vocabulary, VocabularyGroup)\
        .join(Vocabulary, UserLearning.vocab_id == Vocabulary.id)\
        .join(VocabularyGroup, Vocabulary.group_id == VocabularyGroup.id)\
        .filter(UserLearning.user_id == user_id, UserLearning.next_review <= today)\
        .filter(Vocabulary.mode == settings.learning_language)\
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
        
        # Lọc bỏ các nghĩa bị rác (chứa [, |, {) khỏi danh sách gợi ý trắc nghiệm
        distractors = [m.split(',')[0].strip() for m in all_meanings 
                       if m and m.split(',')[0].strip() != primary_meaning 
                       and '[' not in m and '|' not in m and '{' not in m]
        import random
        selected_distractors = random.sample(distractors, min(len(distractors), 3))
        
        options = [primary_meaning] + selected_distractors
        random.shuffle(options)
        
        words.append({
            "id": vocab.id,
            "word": vocab.word,
            "word_en": vocab.word_en,
            "word_zh": vocab.word_zh,
            "pinyin": vocab.pinyin,
            "meaning": vocab.meaning,
            "primary_meaning": primary_meaning,
            "pronunciation": vocab.pronunciation,
            "example": vocab.example or "",
            "example_zh": vocab.example_zh or "",
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

@app.get("/settings")
def get_settings(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    return {"settings": settings}

@app.post("/settings")
def update_settings(req: dict, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
    
    settings.daily_goal = int(req.get("daily_goal", 5))
    settings.profession = req.get("profession", "Tổng quát")
    settings.learning_language = req.get("learning_language", "en")
    db.commit()
    return {"message": "Updated"}

@app.delete("/words/all")
def delete_all_words(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """Xoá toàn bộ thẻ của người dùng"""
    db.query(UserLearning).filter(UserLearning.user_id == user_id).delete()
    db.query(Vocabulary).filter(Vocabulary.id.in_(
        db.query(Vocabulary.id).join(VocabularyGroup).filter(VocabularyGroup.user_id == user_id)
    )).delete(synchronize_session=False)
    db.commit()
    return {"message": "Đã xoá toàn bộ thẻ"}

@app.delete("/words/{word_id}")
def delete_word(word_id: int, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    """Xoá một thẻ cụ thể"""
    # Tìm kiếm thẻ đơn giản hơn để tránh lỗi join
    vocab = db.query(Vocabulary).filter(Vocabulary.id == word_id).first()
    if not vocab:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ")
    
    # Chỉ cho phép xoá nếu người dùng có bản ghi học tập cho thẻ này (chứng minh quyền sở hữu)
    learning = db.query(UserLearning).filter(UserLearning.vocab_id == word_id, UserLearning.user_id == user_id).first()
    if not learning:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xoá thẻ này")
    
    # Xoá learning record trước để tránh lỗi ràng buộc
    db.query(UserLearning).filter(UserLearning.vocab_id == word_id).delete(synchronize_session=False)
    db.query(Vocabulary).filter(Vocabulary.id == word_id).delete(synchronize_session=False)
    db.commit()
    return {"message": "Đã xoá thẻ thành công"}

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
    
    # Đếm theo ngôn ngữ
    en_count = db.query(Vocabulary).filter(Vocabulary.word_en != "", Vocabulary.word_zh == "").count()
    zh_count = db.query(Vocabulary).filter(Vocabulary.word_en == "", Vocabulary.word_zh != "").count()
    tri_count = db.query(Vocabulary).filter(Vocabulary.word_en != "", Vocabulary.word_zh != "").count()
    
    return {
        "today_new_words": 5,
        "today_review_words": today_words,
        "streak": streak,
        "counts": {
            "en": en_count,
            "zh": zh_count,
            "trilingual": tri_count
        },
        "progress": {
            "total": total_words,
            "mastered": mastered_words,
            "percentage": round(mastered_words/total_words*100, 1) if total_words > 0 else 0
        },
        "weak_words": [{"word": vocab.word, "mastery": learning.mastery} for learning, vocab in weak_words],
        "settings": {
            "daily_goal": settings.daily_goal if settings else 5,
            "profession": settings.profession if settings else "Tổng quát",
            "learning_language": settings.learning_language if settings else "en"
        }
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
def update_settings(daily_goal: int, profession: str = "Công nghệ thông tin (IT)", learning_language: str = "en", user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if settings:
        settings.daily_goal = daily_goal
        settings.profession = profession
        settings.learning_language = learning_language
        db.commit()
    else:
        settings = UserSettings(user_id=user_id, daily_goal=daily_goal, profession=profession, learning_language=learning_language)
        db.add(settings)
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

class ChatRequest(BaseModel):
    prompt: str

@app.post("/ai/chat")
def ai_chat(req: ChatRequest):
    try:
        resp = requests.post("http://localhost:11434/api/generate", json={
            "model": "qwen2.5:3b",
            "prompt": req.prompt,
            "stream": False
        }, timeout=30)
        return {"response": resp.json().get("response", "Lỗi AI")}
    except:
        return {"response": "Không kết nối được AI Ollama"}

if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("🚀 Wake & Learn API v3.0")
    print("="*50)
    print("📝 Demo: demo / demo123")
    print("🌐 http://localhost:8000")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
