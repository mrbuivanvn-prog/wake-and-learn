#!/bin/bash
echo "🛑 Stopping Wake and Learn..."
pkill -f "uvicorn app.main:app"
pkill -f "http.server 3000"
echo "✅ All services stopped"
