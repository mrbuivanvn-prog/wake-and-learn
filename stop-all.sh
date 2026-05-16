#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Dừng hệ thống Wake and Learn...${NC}"

# Dừng theo PID đã lưu
if [ -f /tmp/wake_backend.pid ]; then
    kill -9 $(cat /tmp/wake_backend.pid) 2>/dev/null
    rm -f /tmp/wake_backend.pid
fi

if [ -f /tmp/wake_frontend.pid ]; then
    kill -9 $(cat /tmp/wake_frontend.pid) 2>/dev/null
    rm -f /tmp/wake_frontend.pid
fi

# Dừng tất cả process liên quan
pkill -9 -f uvicorn 2>/dev/null
pkill -9 -f "http.server" 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null

echo -e "${GREEN}✅ Đã dừng tất cả services${NC}"
