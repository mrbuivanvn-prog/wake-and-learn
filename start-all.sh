#!/bin/bash

# Màu sắc cho terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   🚀 Wake and Learn - Khởi động hệ thống${NC}"
echo -e "${BLUE}========================================${NC}"

# Đường dẫn
PROJECT_DIR="$HOME/new/wake-and-learn"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Chuyển đến thư mục dự án
cd $PROJECT_DIR

# 1. Dừng tất cả process cũ
echo -e "${YELLOW}📌 Dừng các process cũ...${NC}"
pkill -9 -f uvicorn 2>/dev/null
pkill -9 -f "http.server" 2>/dev/null
pkill -9 -f python3 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null
sleep 2
echo -e "${GREEN}✅ Đã dọn dẹp${NC}"

# 2. Kiểm tra virtual environment
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}📦 Tạo virtual environment...${NC}"
    python3 -m venv venv
fi

# 3. Kích hoạt venv và cài đặt dependencies
echo -e "${YELLOW}📦 Cài đặt dependencies...${NC}"
source venv/bin/activate
pip install -q fastapi uvicorn sqlalchemy ollama deep-translator requests

# 4. Tạo database mới nếu cần
if [ ! -f "$BACKEND_DIR/database/wakeandlearn.db" ]; then
    echo -e "${YELLOW}📦 Tạo database mới...${NC}"
    cd $BACKEND_DIR
    python3 -c "
from app.database import engine, Base
from app.models import User, Card, StudySession
Base.metadata.create_all(bind=engine)
print('✅ Database created')
"
    # Tạo user demo
    python3 -c "
from app.database import SessionLocal
from app.models import User
db = SessionLocal()
user = User(username='demo', email='demo@example.com')
db.add(user)
db.commit()
print('✅ Demo user created')
db.close()
"
fi

# 5. Khởi động backend
echo -e "${YELLOW}🚀 Khởi động Backend (port 8000)...${NC}"
cd $BACKEND_DIR
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend đã chạy (PID: $BACKEND_PID)${NC}"

# Đợi backend khởi động
sleep 3

# Kiểm tra backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend hoạt động tốt${NC}"
else
    echo -e "${RED}❌ Backend không khởi động được${NC}"
    exit 1
fi

# 6. Khởi động frontend
echo -e "${YELLOW}🚀 Khởi động Frontend (port 3000)...${NC}"
cd $FRONTEND_DIR
python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend đã chạy (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✨ HỆ THỐNG ĐÃ SẴN SÀNG!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}📍 Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "${YELLOW}📍 Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "${YELLOW}📍 API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}💡 Nhấn Ctrl+C để dừng tất cả${NC}"
echo ""

# Lưu PID để dừng sau
echo $BACKEND_PID > /tmp/wake_backend.pid
echo $FRONTEND_PID > /tmp/wake_frontend.pid

# Chờ và xử lý khi nhấn Ctrl+C
trap "echo ''; echo -e '${RED}🛑 Dừng hệ thống...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f /tmp/wake_backend.pid /tmp/wake_frontend.pid; exit" INT

wait
