#!/usr/bin/env python
import subprocess
import sys
import os
from pathlib import Path

def setup_environment():
    Path("database").mkdir(exist_ok=True)
    Path("assets/images/cache").mkdir(parents=True, exist_ok=True)

def install_dependencies():
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                   cwd=".", check=True)
    print("✅ Dependencies installed")

def seed_database():
    print("🌱 Seeding database...")
    subprocess.run([sys.executable, "seed.py"], cwd=".", check=True)

if __name__ == "__main__":
    setup_environment()
    
    try:
        install_dependencies()
        seed_database()
        
        print("\n" + "="*50)
        print("🌟 Wake and Learn API")
        print("="*50)
        print("📍 API: http://localhost:8000")
        print("📚 Docs: http://localhost:8000/docs")
        print("="*50 + "\n")
        
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
