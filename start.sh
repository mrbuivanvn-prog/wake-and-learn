#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Wake and Learn - Learning App${NC}"
echo -e "${BLUE}========================================${NC}"

# Kiểm tra virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Kích hoạt venv
source venv/bin/activate

# Cài đặt dependencies nếu chưa có
if [ ! -f "venv/installed" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install -q fastapi uvicorn sqlalchemy pydantic[email] python-multipart
    touch venv/installed
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Tạo database nếu chưa có
if [ ! -f "backend/database/wakeandlearn.db" ]; then
    echo -e "${YELLOW}🌱 Seeding database...${NC}"
    cd backend
    python3 -c "from app.database import engine, Base; from app.models import User, Card, StudySession; Base.metadata.create_all(bind=engine)"
    python3 seed.py
    cd ..
    echo -e "${GREEN}✅ Database ready${NC}"
fi

echo -e "${GREEN}✅ Starting services...${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}📍 Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}📍 API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}📍 Frontend App: http://localhost:3000${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Chạy backend trong background
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Chạy frontend
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

# Xử lý khi nhấn Ctrl+C
trap "echo -e '\n${RED}🛑 Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Giữ script chạy
wait
