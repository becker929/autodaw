#!/bin/bash

# AutoDAW Startup Script
# Starts both backend and frontend servers

set -e

echo "🎵 AutoDAW - GA+JSI+Audio Oracle Optimization"
echo "=============================================="

# Check if required tools are installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    pkill -f "uvicorn.*autodaw.backend.main:app" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Check if dependencies are installed
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the autodaw root directory"
    exit 1
fi

echo "📦 Installing dependencies..."
uv sync --quiet
cd autodaw/frontend && npm install --silent
cd ../..

echo ""
echo "🚀 Starting servers..."
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start backend in background
echo "⚡ Starting backend server..."
uv run python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "⚡ Starting frontend server..."
cd autodaw/frontend
npm start &
FRONTEND_PID=$!
cd ../..

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
