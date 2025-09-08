# Audio Comparison GUI Demo - Makefile
# Manages backend and frontend services

.PHONY: help install start start-backend start-frontend stop test clean dev-setup status

# Default target
help:
	@echo "Audio Comparison GUI Demo - Available Commands:"
	@echo ""
	@echo "  make install      - Install all dependencies (backend + frontend)"
	@echo "  make start        - Start both backend and frontend servers"
	@echo "  make start-backend- Start only the FastAPI backend server"
	@echo "  make start-frontend- Start only the React frontend server"
	@echo "  make stop         - Stop all running servers"
	@echo "  make status       - Check if services are running"
	@echo "  make test         - Run test suite"
	@echo "  make clean        - Clean build artifacts and dependencies"
	@echo "  make dev-setup    - Complete development environment setup"
	@echo ""

# Install all dependencies
install:
	@echo "Installing Python dependencies..."
	uv sync
	@echo "Installing Node.js dependencies..."
	cd frontend && npm install
	@echo "Installation complete"

# Complete development setup
dev-setup: install
	@echo "Development environment ready"
	@echo "Run 'make start' to launch the application"

# Start both services
start:
	@echo "Starting Audio Comparison GUI Demo..."
	@echo "Backend will be available at: http://localhost:8000"
	@echo "Frontend will be available at: http://localhost:3000"
	@echo "API docs available at: http://localhost:8000/docs"
	@echo ""
	@echo "Starting backend server in background..."
	@nohup uv run python run_backend.py > backend.log 2>&1 &
	@echo "Waiting for backend to start..."
	@sleep 5
	@echo "Starting frontend (this will open your browser)..."
	@echo "Press Ctrl+C to stop the frontend (backend will keep running)"
	@echo "Use 'make stop' to stop both services"
	@cd frontend && npm start

# Start backend only
start-backend:
	@echo "Starting FastAPI backend server..."
	@echo "API available at: http://localhost:8000"
	@echo "API docs available at: http://localhost:8000/docs"
	uv run python run_backend.py

# Start frontend only (requires backend to be running)
start-frontend:
	@echo "Starting React frontend server..."
	@echo "Frontend available at: http://localhost:3000"
	cd frontend && npm start

# Stop all services
stop:
	@echo "Stopping all services..."
	@pkill -f "uvicorn" || true
	@pkill -f "react-scripts" || true
	@pkill -f "node.*react-scripts" || true
	@echo "Services stopped"

# Check service status
status:
	@echo "Checking service status..."
	@echo "Backend (uvicorn):"
	@curl -s http://localhost:8000/ > /dev/null && echo "  ✓ Running at http://localhost:8000" || echo "  ✗ Not running"
	@echo "Frontend (React):"
	@curl -s http://localhost:3000/ > /dev/null && echo "  ✓ Running at http://localhost:3000" || echo "  ✗ Not running"

# Run tests
test:
	@echo "Running backend tests..."
	uv run pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test -- --coverage --watchAll=false

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf __pycache__/
	rm -rf backend/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -rf frontend/node_modules/
	rm -rf frontend/build/
	rm -rf .uv/
	@echo "Clean complete"

# Development workflow targets
dev: dev-setup start

# Quick restart
restart: stop start
