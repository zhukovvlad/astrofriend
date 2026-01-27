.PHONY: help install install-backend install-frontend venv backend frontend dev clean db-init test test-backend

# Detect Python executable from venv (absolute path from project root)
PROJECT_ROOT := $(shell pwd)
VENV_PYTHON := $(shell \
	if [ -f "$(PROJECT_ROOT)/astro_backend/.venv/bin/python" ]; then \
		echo "$(PROJECT_ROOT)/astro_backend/.venv/bin/python"; \
	elif [ -f "$(PROJECT_ROOT)/astro_backend/venv/bin/python" ]; then \
		echo "$(PROJECT_ROOT)/astro_backend/venv/bin/python"; \
	else \
		echo "python"; \
	fi)

# Default target
help:
	@echo "🌟 Astro-Soulmate Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make venv             - Create Python virtual environment"
	@echo "  make install          - Install all dependencies (backend + frontend)"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make db-init          - Initialize database"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Run both backend and frontend servers"
	@echo "  make backend          - Run backend server only"
	@echo "  make frontend         - Run frontend dev server only"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Clean build artifacts and caches"
	@echo ""
	@echo "Note: Virtual environment is used automatically if it exists"
	@echo "      (astro_backend/.venv or astro_backend/venv)"
	@echo ""

# ============================================
# INSTALLATION
# ============================================

venv:
	@echo "🐍 Creating Python virtual environment..."
	@cd astro_backend && python -m venv .venv
	@echo "✅ Virtual environment created!"
	@echo "Activate with: source astro_backend/.venv/bin/activate"

install: install-backend install-frontend
	@echo "✅ All dependencies installed!"

install-backend:
	@echo "📦 Installing backend dependencies..."
	@if [ ! -d "$(PROJECT_ROOT)/astro_backend/.venv" ] && [ ! -d "$(PROJECT_ROOT)/astro_backend/venv" ]; then \
		echo "⚠️  No virtual environment found. Create one with: make venv"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) -m pip install -r astro_backend/requirements.txt

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@cd astro_frontend && pnpm install

# ============================================
# DATABASE
# ============================================

db-init:
	@echo "🗄️  Initializing database..."
	@cd astro_backend && $(VENV_PYTHON) -c "from database import init_db; import asyncio; asyncio.run(init_db())"
	@echo "✅ Database initialized!"

db-reset:
	@echo "🗑️  Resetting database (drop + recreate + migrate)..."
	@docker exec astro_postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'astro_db' AND pid <> pg_backend_pid();" || true
	@docker exec astro_postgres psql -U postgres -c "DROP DATABASE IF EXISTS astro_db;"
	@docker exec astro_postgres psql -U postgres -c "CREATE DATABASE astro_db;"
	@cd astro_backend && $(VENV_PYTHON) -m alembic upgrade head
	@echo "✅ Database reset complete!"

db-migrate:
	@echo "📦 Running database migrations..."
	@cd astro_backend && $(VENV_PYTHON) -m alembic upgrade head
	@echo "✅ Migrations applied!"

db-rollback:
	@echo "⏪ Rolling back last migration..."
	@cd astro_backend && $(VENV_PYTHON) -m alembic downgrade -1
	@echo "✅ Rollback complete!"

# ============================================
# DEVELOPMENT SERVERS
# ============================================

backend:
	@echo "🚀 Starting backend server..."
	@cd astro_backend && $(VENV_PYTHON) main.py

frontend:
	@echo "🎨 Starting frontend dev server..."
	@cd astro_frontend && pnpm run dev

# Run both servers in parallel (requires GNU parallel or similar)
# For simple parallel execution without extra tools:
dev:
	@echo "🚀 Starting both backend and frontend servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo ""
	@echo "Press Ctrl+C to stop both servers"
	@echo ""
	@trap 'kill 0' EXIT; \
	(cd astro_backend && $(VENV_PYTHON) main.py) & \
	(cd astro_frontend && pnpm run dev) & \
	wait

# ============================================
# TESTING
# ============================================

test: test-backend
	@echo "✅ All tests complete!"

test-backend:
	@echo "🧪 Running backend tests..."
	@cd astro_backend && $(VENV_PYTHON) -m pytest

# ============================================
# CLEANUP
# ============================================

clean:
	@echo "🧹 Cleaning build artifacts and caches..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@cd astro_frontend && rm -rf dist dist-ssr 2>/dev/null || true
	@echo "✅ Cleanup complete!"
