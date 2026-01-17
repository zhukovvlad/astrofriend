.PHONY: help install install-backend install-frontend backend frontend dev clean db-init

# Default target
help:
	@echo "🌟 Astro-Soulmate Development Commands"
	@echo ""
	@echo "Setup:"
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
	@echo "Utilities:"
	@echo "  make clean            - Clean build artifacts and caches"
	@echo "  make test-backend     - Run backend tests"
	@echo ""

# ============================================
# INSTALLATION
# ============================================

install: install-backend install-frontend
	@echo "✅ All dependencies installed!"

install-backend:
	@echo "📦 Installing backend dependencies..."
	@cd astro_backend && python -m pip install -r requirements.txt

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@cd astro_frontend && pnpm install

# ============================================
# DATABASE
# ============================================

db-init:
	@echo "🗄️  Initializing database..."
	@cd astro_backend && python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
	@echo "✅ Database initialized!"

# ============================================
# DEVELOPMENT SERVERS
# ============================================

backend:
	@echo "🚀 Starting backend server..."
	@cd astro_backend && python main.py

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
	(cd astro_backend && python main.py) & \
	(cd astro_frontend && pnpm run dev) & \
	wait

# ============================================
# TESTING
# ============================================

test-backend:
	@echo "🧪 Running backend tests..."
	@cd astro_backend && pytest

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
