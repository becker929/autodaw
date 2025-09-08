.PHONY: help install start start-backend start-frontend stop clean dev-setup test

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "AutoDAW - GA+JSI+Audio Oracle Optimization"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "$(YELLOW)Installing backend dependencies...$(NC)"
	uv sync
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	cd autodaw/frontend && npm install
	@echo "$(GREEN)All dependencies installed successfully!$(NC)"

dev-setup: install ## Complete development environment setup
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "Run 'make start' to launch both backend and frontend"

start: ## Start both backend and frontend servers
	@echo "$(YELLOW)Starting AutoDAW application...$(NC)"
	@echo "Backend will be at http://localhost:8000"
	@echo "Frontend will be at http://localhost:3000"
	@echo "Use Ctrl+C to stop both servers"
	@trap 'make stop' INT; \
	make start-backend & \
	sleep 3 && make start-frontend & \
	wait

start-backend: ## Start only the FastAPI backend server
	@echo "$(YELLOW)Starting backend server...$(NC)"
	uv run python main.py

start-frontend: ## Start only the React frontend server
	@echo "$(YELLOW)Starting frontend server...$(NC)"
	cd autodaw/frontend && npm start

stop: ## Stop all running servers
	@echo "$(RED)Stopping servers...$(NC)"
	@pkill -f "uvicorn.*autodaw.backend.main:app" || true
	@pkill -f "react-scripts start" || true
	@echo "$(GREEN)Servers stopped$(NC)"

status: ## Check if services are running
	@echo "$(YELLOW)Checking service status...$(NC)"
	@if pgrep -f "uvicorn.*autodaw.backend.main:app" > /dev/null; then \
		echo "$(GREEN)Backend: Running$(NC)"; \
	else \
		echo "$(RED)Backend: Not running$(NC)"; \
	fi
	@if pgrep -f "react-scripts start" > /dev/null; then \
		echo "$(GREEN)Frontend: Running$(NC)"; \
	else \
		echo "$(RED)Frontend: Not running$(NC)"; \
	fi

test: ## Run complete test suite
	@echo "$(YELLOW)Installing test dependencies...$(NC)"
	uv sync --extra test
	@echo "$(YELLOW)Running comprehensive test suite...$(NC)"
	@echo "  - Basic functionality tests"
	@echo "  - API integration tests"
	@echo "  - Edge case tests"
	@echo "  - Performance tests"
	@echo "  - End-to-end workflow tests"
	uv run pytest tests/ -v --tb=short
	@echo "$(YELLOW)Running standalone basic tests...$(NC)"
	uv run python tests/test_basic.py
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	cd autodaw/frontend && npm test -- --watchAll=false --verbose
	@echo "$(GREEN)All tests completed successfully!$(NC)"
	@echo "$(GREEN)Test coverage includes:$(NC)"
	@echo "  ✓ Database operations and consistency"
	@echo "  ✓ API endpoints and error handling"
	@echo "  ✓ Complete user workflows"
	@echo "  ✓ Edge cases and boundary conditions"
	@echo "  ✓ Performance and load testing"
	@echo "  ✓ Concurrent operations"
	@echo "  ✓ Data integrity and recovery"

test-quick: ## Run quick subset of tests
	@echo "$(YELLOW)Running quick test subset...$(NC)"
	uv sync --extra test
	uv run pytest tests/test_basic.py tests/test_api.py -v
	@echo "$(GREEN)Quick tests completed!$(NC)"

test-integration: ## Run integration tests only
	@echo "$(YELLOW)Running integration tests...$(NC)"
	uv sync --extra test
	uv run pytest tests/test_integration.py tests/test_end_to_end.py -v
	@echo "$(GREEN)Integration tests completed!$(NC)"

test-performance: ## Run performance tests only
	@echo "$(YELLOW)Running performance tests...$(NC)"
	uv sync --extra test
	uv run pytest tests/test_performance.py -v
	@echo "$(GREEN)Performance tests completed!$(NC)"

clean: ## Clean build artifacts and dependencies
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf autodaw/frontend/node_modules
	rm -rf autodaw/frontend/build
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f autodaw.db
	@echo "$(GREEN)Cleanup complete$(NC)"

# Development shortcuts
backend: start-backend ## Alias for start-backend
frontend: start-frontend ## Alias for start-frontend
