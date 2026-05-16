from app.database import init_db, SessionLocal
from app.models import User, UserSettings, VocabularyGroup, Vocabulary, UserLearning
from datetime import date, datetime

def seed():
    init_db()
    db = SessionLocal()
    
    # Xóa dữ liệu cũ
    db.query(UserLearning).delete()
    db.query(Vocabulary).delete()
    db.query(VocabularyGroup).delete()
    db.query(UserSettings).delete()
    db.query(User).delete()
    
    from app.main import get_password_hash
    # Tạo user demo
    demo = User(username="demo", password=get_password_hash("demo123"), created_at=datetime.now())
    db.add(demo)
    db.flush()
    
    settings = UserSettings(user_id=demo.id, daily_goal=5)
    db.add(settings)
    
    # Tạo nhóm
    group = VocabularyGroup(name="IT Helpdesk", language="en", profession="IT", created_by_user=False)
    db.add(group)
    db.flush()
    
    # Từ mẫu
    samples = [
        ("restart", "khởi động lại", "/riːbuːt/", "Please restart your computer.", "Vui lòng khởi động lại máy tính."),
        ("printer", "máy in", "/prɪntər/", "The printer is out of paper.", "Máy in đã hết giấy."),
        ("permissions", "quyền truy cập", "/pərmɪʃənz/", "You need admin permissions.", "Bạn cần quyền quản trị.")
    ]
    for w in samples:
        vocab = Vocabulary(
            group_id=group.id, word=w[0], meaning=w[1], pronunciation=w[2],
            example=w[3], example_vi=w[4], level="A1"
        )
        db.add(vocab)
        db.flush()
        learning = UserLearning(vocab_id=vocab.id, user_id=demo.id, next_review=date.today())
        db.add(learning)
    
    db.commit()
    print("✅ Seeded database with demo user: demo/demo123")
    db.close()

if __name__ == "__main__":
    seed()
