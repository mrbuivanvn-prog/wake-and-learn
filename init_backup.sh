#!/bin/bash
TARGET="/home/k3/new/learn-E-ZH"
cd $TARGET
git init
git add .
git commit -m "Initial commit for Trilingual Edition (learn E-ZH)"
echo "✅ Backup and Git initialization complete at $TARGET"
