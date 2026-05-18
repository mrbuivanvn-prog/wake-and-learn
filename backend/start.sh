#!/bin/bash
cd /home/k3/new/wake-and-learn/backend
export PYTHONPATH=/home/k3/new/wake-and-learn/backend
exec python3 -m uvicorn app.main:app --port 8000 --host 0.0.0.0