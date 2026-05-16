#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "   Trạng thái Wake and Learn"
echo "========================================="

# Kiểm tra backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: Đang chạy (port 8000)${NC}"
else
    echo -e "${RED}❌ Backend: Không chạy${NC}"
fi

# Kiểm tra frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend: Đang chạy (port 3000)${NC}"
else
    echo -e "${RED}❌ Frontend: Không chạy${NC}"
fi

# Kiểm tra Ollama
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama: Đang chạy${NC}"
else
    echo -e "${RED}❌ Ollama: Không chạy (chạy 'ollama serve')${NC}"
fi

echo "========================================="
