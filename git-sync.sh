#!/bin/bash

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   📤 Đồng bộ lên GitHub${NC}"
echo -e "${BLUE}========================================${NC}"

# Kiểm tra git đã được khởi tạo chưa
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📌 Khởi tạo git repository...${NC}"
    git init
    git remote add origin https://github.com/k3-vmware/wake-and-learn.git
fi

# Kiểm tra thay đổi
echo -e "${YELLOW}📌 Kiểm tra thay đổi...${NC}"
git status

# Hỏi message commit
echo ""
read -p "📝 Nhập message commit (mặc định: Update code): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update code - $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Thêm tất cả file
echo -e "${YELLOW}📌 Thêm file vào git...${NC}"
git add .

# Commit
echo -e "${YELLOW}📌 Commit thay đổi...${NC}"
git commit -m "$commit_msg"

# Push lên GitHub
echo -e "${YELLOW}📌 Push lên GitHub...${NC}"
git push -u origin main

echo -e "${GREEN}✅ Đã đồng bộ lên GitHub thành công!${NC}"
echo -e "${BLUE}========================================${NC}"
