#!/usr/bin/env python3
"""Main entry point for AutoDAW application."""

import uvicorn
from pathlib import Path
import sys

# Add the autodaw package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from autodaw.backend.main import app

if __name__ == "__main__":
    print("Starting AutoDAW - GA+JSI+Audio Oracle Optimization")
    print("=" * 60)
    print("Backend API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Frontend should be started separately with: cd autodaw/frontend && npm start")
    print("=" * 60)

    uvicorn.run(
        "autodaw.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
