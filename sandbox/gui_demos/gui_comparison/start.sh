#!/bin/bash

# Audio Comparison GUI Demo Startup Script

echo "🎵 Audio Comparison GUI Demo"
echo "=============================="
echo ""

# Check if dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing dependencies..."
    make install
    echo ""
fi

echo "🚀 Starting services..."
echo ""

# Start backend in background
echo "Starting backend server..."
nohup uv run python run_backend.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Check if backend started successfully
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend running at http://localhost:8000"
    echo "📚 API docs available at http://localhost:8000/docs"
else
    echo "❌ Backend failed to start"
    exit 1
fi

echo ""
echo "🌐 Starting frontend (this will open your browser)..."
echo "Press Ctrl+C to stop the frontend"
echo "Backend will continue running in background"
echo ""

# Start frontend
cd frontend && npm start

echo ""
echo "Frontend stopped. Backend is still running."
echo "Use 'make stop' or 'pkill -f uvicorn' to stop the backend."
