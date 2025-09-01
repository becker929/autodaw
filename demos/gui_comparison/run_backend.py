#!/usr/bin/env python3
"""
Launch script for the audio comparison backend server.
"""

import uvicorn
from backend.main import app

if __name__ == "__main__":
    print("Starting Audio Comparison API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
