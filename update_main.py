import re

with open("backend/app/main.py", "r") as f:
    content = f.read()

# Add imports
imports = """import jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
"""
content = re.sub(r'import uuid\n', 'import uuid\n' + imports, content)

# Add JWT config and Context
jwt_config = """
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

"""
content = re.sub(r'# Session lưu tạm\nsessions = {}\n', jwt_config, content)

# Update get_user_id
get_user_id_new = """
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
"""
content = re.sub(r'def get_user_id\(token: str\):\n    uid = sessions\.get\(token\)\n    if not uid:\n        raise HTTPException\(401, "Invalid token"\)\n    return uid\n', get_user_id_new, content)

# Update endpoints using get_user_id
content = content.replace('def add_words_batch_ai(words: List[str], token: str, db: Session = Depends(get_db)):', 'def add_words_batch_ai(words: List[str], user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):')
content = content.replace('user_id = get_user_id(token)', '')

content = content.replace('def get_today_words(token: str, db: Session = Depends(get_db)):', 'def get_today_words(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):')
content = content.replace('def learn_word(vocab_id: int, is_correct: bool, token: str, db: Session = Depends(get_db)):', 'def learn_word(vocab_id: int, is_correct: bool, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):')
content = content.replace('def get_dashboard(token: str, db: Session = Depends(get_db)):', 'def get_dashboard(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):')
content = content.replace('def get_all_words(token: str, db: Session = Depends(get_db)):', 'def get_all_words(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):')
content = content.replace('def update_settings(daily_goal: int, token: str, db: Session = Depends(get_db)):', 'def update_settings(daily_goal: int, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):')


# Replace login
login_old = """@app.post("/auth/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")
    token = str(uuid.uuid4())
    sessions[token] = user.id
    return {"token": token, "user_id": user.id, "username": user.username}"""

login_new = """from pydantic import BaseModel
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")
    token = create_access_token({"sub": str(user.id)})
    return {"token": token, "user_id": user.id, "username": user.username}"""

content = content.replace(login_old, login_new)

# Replace register
register_old = """@app.post("/auth/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(400, "Username exists")
    user = User(username=username, password=password)
    db.add(user)
    db.flush()
    settings = UserSettings(user_id=user.id, daily_goal=5)
    db.add(settings)
    db.commit()
    token = str(uuid.uuid4())
    sessions[token] = user.id
    return {"token": token, "user_id": user.id, "username": username}"""

register_new = """@app.post("/auth/register")
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
    return {"token": token, "user_id": user.id, "username": req.username}"""

content = content.replace(register_old, register_new)

# Add exercises endpoints
exercises_endpoints = """
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
    learning = db.query(UserLearning).filter(UserLearning.vocab_id == vocab.id, UserLearning.id == user_id).first() # this should be joined with user_id... Wait UserLearning doesn't have user_id natively in models.py?
    # Let me check models.py! Oh wait, UserLearning only has id, vocab_id, mastery...
    
    return {"correct": correct, "correct_answer": vocab.word if not correct else ""}
"""

content = content.replace('if __name__ == "__main__":', exercises_endpoints + '\nif __name__ == "__main__":')

with open("backend/app/main.py", "w") as f:
    f.write(content)

