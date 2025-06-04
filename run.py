#!/usr/bin/env python3


import uvicorn
import os
import sys
from pathlib import Path

def check_requirements():
    try:
        import fastapi
        import pydantic
        import pytz
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_environment():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("API_HOST", "0.0.0.0")
    os.environ.setdefault("API_PORT", "8000")
    
    print("✅ Environment setup complete")

def main():
    print("🧘‍♀️ Fitness Studio Booking API")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    setup_environment()
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print(f"🚀 Starting server on http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"📖 ReDoc: http://{host}:{port}/redoc")
    print(f"🔍 Log Level: {log_level.upper()}")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=True,  
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()