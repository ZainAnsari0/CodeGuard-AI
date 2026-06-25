# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Development & Operations Makefile
# ═══════════════════════════════════════════════════════════════════
#
# Usage:
#   make <target>        Run a single target
#   make help             Show all available targets
#
# Prerequisites:
#   - Python 3.11+ with venv
#   - Node.js 18+ with npm
#   - PostgreSQL 16+
#   - Redis 7+
#   - OpenSSL (for key generation)
# ═══════════════════════════════════════════════════════════════════

# ── Configuration ─────────────────────────────────────────────────
PYTHON          ?= python3
VENV            ?= backend/venv
PIP             ?= $(VENV)/bin/pip
PYTHON_CMD      ?= $(VENV)/bin/python
CELERY          ?= $(VENV)/bin/celery
ALEMBIC         ?= $(VENV)/bin/alembic

.PHONY: help \
        dev dev-api dev-celery dev-frontend \
        db-migrate db-migrate-down db-seed db-backup db-restore \
        certs-generate \
        health health-verbose \
        test test-backend test-frontend test-e2e \
        lint lint-backend lint-frontend \
        security-audit \
        logs clean \
        install install-backend install-frontend

# ── Help ──────────────────────────────────────────────────────────
help: ## Show this help
	@echo "CodeGuard AI — Available Commands"
	@echo "═════════════════════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Services: API (port 8000), Frontend (port 5173), Celery worker"

# ── Install ───────────────────────────────────────────────────────
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend Python dependencies
	cd backend && $(PYTHON) -m venv venv && \
		$(PIP) install -r requirements.txt
	@echo "✅ Backend dependencies installed"

install-frontend: ## Install frontend Node.js dependencies
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

# ── Development ───────────────────────────────────────────────────
dev: ## Start all development services (API + Celery + Frontend)
	@echo "Starting CodeGuard AI development environment..."
	@make dev-api &
	@make dev-celery &
	@make dev-frontend &
	@echo "✅ Development stack running"
	@echo "   API:       http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/api/v1/docs"
	@echo "   Frontend:  http://localhost:5173"

dev-api: ## Start the FastAPI development server
	cd backend && $(PYTHON_CMD) -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-celery: ## Start the Celery worker
	cd backend && $(CELERY) -A app.tasks.celery_app worker --loglevel=info

dev-celery-beat: ## Start the Celery beat scheduler
	cd backend && $(CELERY) -A app.tasks.celery_app beat --loglevel=info

dev-frontend: ## Start the Vite frontend dev server
	cd frontend && npm run dev

# ── Production ───────────────────────────────────────────────────
prod-api: ## Start API in production mode (4 workers)
	cd backend && $(PYTHON_CMD) -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

prod-celery: ## Start Celery worker in production mode
	cd backend && $(CELERY) -A app.tasks.celery_app worker --loglevel=info --concurrency=4

prod-frontend-build: ## Build frontend for production
	cd frontend && npm run build
	@echo "✅ Frontend built to frontend/dist/"

# ── Database ──────────────────────────────────────────────────────
db-migrate: ## Run database migrations
	cd backend && $(ALEMBIC) upgrade head
	@echo "✅ Migrations applied"

db-migrate-down: ## Rollback last migration (DANGEROUS — use with caution)
	@read -p "⚠️  Rollback last migration? [y/N]: " confirm; \
	[ "$$confirm" = "y" ] && cd backend && $(ALEMBIC) downgrade -1 || echo "Cancelled"

db-seed: ## Seed database with development data
	cd backend && $(PYTHON_CMD) -m app.scripts.seed_db

db-backup: ## Create a PostgreSQL backup
	@mkdir -p backups
	@BACKUP_FILE="codeguard_$$(date +%Y%m%d_%H%M%S).sql.gz"; \
	pg_dump -U codeguard_user codeguard | gzip > "backups/$$BACKUP_FILE"; \
	echo "✅ Backup saved: backups/$$BACKUP_FILE"

db-restore: ## Restore PostgreSQL from backup file
	@read -p "Enter backup file path (relative to backups/): " file; \
	gunzip -c "backups/$$file" | psql -U codeguard_user codeguard; \
	echo "✅ Database restored from: $$file"

# ── Certificates ──────────────────────────────────────────────────
certs-generate: ## Generate JWT keys for RS256 authentication
	@mkdir -p certs
	@echo "🔐 Generating RS256 JWT keys..."
	cd backend && bash generate_keys.sh ../certs
	@chmod 600 certs/jwt_private.pem
	@echo "✅ JWT keys generated in certs/"

# ── Health Checks ─────────────────────────────────────────────────
health: ## Quick health check
	@echo "API:    $$(curl -sf http://localhost:8000/health 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("status","unknown"))' || echo '❌ unreachable')"
	@echo "Redis:  $$(redis-cli ping 2>/dev/null || echo '❌ unreachable')"

health-verbose: ## Detailed health check with all subsystems
	@echo "═══ API Health ═══"
	@curl -sf http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ API unreachable"
	@echo ""
	@echo "═══ API Readiness ═══"
	@curl -sf http://localhost:8000/ready | python3 -m json.tool 2>/dev/null || echo "❌ API not ready"
	@echo ""
	@echo "═══ Workspace Health ═══"
	@curl -sf http://localhost:8000/api/v1/scanner/workspace-health | python3 -m json.tool 2>/dev/null || echo "❌ Workspace check failed"
	@echo ""
	@echo "═══ Redis ═══"
	@redis-cli info server 2>/dev/null | grep redis_version || echo "❌ Redis unreachable"

# ── Testing ───────────────────────────────────────────────────────
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests with coverage
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v --tb=short \
		--cov=app --cov-report=term-missing --cov-fail-under=40

test-frontend: ## Run frontend tests
	cd frontend && npm test -- --coverage

test-e2e: ## Run end-to-end tests
	cd frontend && npx playwright test

# ── Linting ───────────────────────────────────────────────────────
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend Python code
	cd backend && $(PYTHON_CMD) -m ruff check app/ main.py

lint-frontend: ## Lint frontend TypeScript/React code
	cd frontend && npm run lint

# ── Security ──────────────────────────────────────────────────────
security-audit: ## Run full security audit
	cd backend && bash scripts/security_audit.sh
	cd frontend && bash scripts/security_audit.sh
	@echo ""
	@echo "🔍 Checking for exposed secrets..."
	@git diff --cached --name-only | xargs grep -l "BEGIN RSA PRIVATE" 2>/dev/null && echo "❌ PRIVATE KEY FOUND IN STAGED FILES" || echo "✅ No private keys in staged files"
	@grep -rE "(?<!\w)(password|secret|api_key|token)\s*=\s*['\"][^'\"]{8,}['\"]" \
		--include="*.py" --include="*.ts" --include="*.tsx" --include="*.env" \
		backend/app frontend/src .env .env.production 2>/dev/null | \
		grep -v "change_me\|CHANGE_ME\|test-secret\|$$" || echo "✅ No hardcoded secrets detected"

# ── Cleanup ───────────────────────────────────────────────────────
clean: ## Remove temporary files and caches
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist frontend/.next 2>/dev/null || true
	rm -rf /tmp/codeguard_uploads/* 2>/dev/null || true
	@echo "✅ Cleaned temporary files and caches"

clean-workspaces: ## Remove stale scan workspaces
	rm -rf /tmp/codeguard_uploads/* 2>/dev/null || true
	rm -rf /tmp/codeguard_uploads_fallback/* 2>/dev/null || true
	@echo "✅ Cleaned scan workspaces"