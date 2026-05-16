#!/bin/bash
echo "🧹 Cleaning ports..."

# Kill processes
pkill -9 -f uvicorn 2>/dev/null
pkill -9 -f "http.server" 2>/dev/null
pkill -9 -f "python3 -m http.server" 2>/dev/null

# Kill by port
fuser -k 8000/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null

# Đợi 1 giây
sleep 1

# Kiểm tra
echo "✅ Ports cleaned"
echo "Port 8000: $(sudo lsof -i :8000 | wc -l) processes"
echo "Port 3000: $(sudo lsof -i :3000 | wc -l) processes"

# Chạy lại
echo "🚀 Starting application..."
./start.sh
