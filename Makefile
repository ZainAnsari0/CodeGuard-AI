# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Production Operations Makefile
# ═══════════════════════════════════════════════════════════════════
#
# Usage:
#   make <target>        Run a single target
#   make help             Show all available targets
#   ENV=staging           Override environment (default: production)
#
# Prerequisites:
#   - Docker + Docker Compose v2
#   - OpenSSL (for key generation)
#   - jq (for JSON parsing in health checks)
# ═══════════════════════════════════════════════════════════════════

# ── Configuration ─────────────────────────────────────────────────
ENV              ?= production
COMPOSE_DEV      = docker compose -f docker-compose.yml
COMPOSE_STAGING  = docker compose -f docker-compose.yml -f docker-compose.staging.yml
COMPOSE_PROD     = docker compose -f docker-compose.yml -f docker-compose.prod.yml
COMPOSE          = $(if $(filter staging,$(ENV)),$(COMPOSE_STAGING),$(COMPOSE_PROD))

DOCKER_REGISTRY  ?= ghcr.io/codeguard-ai
IMAGE_TAG        ?= latest
GIT_SHA          := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

BACKEND_IMG      = $(DOCKER_REGISTRY)/api:$(IMAGE_TAG)
FRONTEND_IMG     = $(DOCKER_REGISTRY)/frontend:$(IMAGE_TAG)
CELERY_IMG       = $(DOCKER_REGISTRY)/celery:$(IMAGE_TAG)
SCANNER_IMG      = $(DOCKER_REGISTRY)/scanner:$(IMAGE_TAG)

.PHONY: help \
        dev up down restart logs ps \
        build build-push \
        deploy deploy-rollback deploy-status \
        db-migrate db-migrate-down db-seed db-backup db-restore \
        certs-generate certs-renew \
        health health-verbose \
        test test-backend test-frontend test-e2e \
        lint lint-backend lint-frontend \
        security-audit \
        logs-follow logs-api logs-celery logs-frontend \
        clean clean-volumes clean-images \
        staging staging-down \
        docker-prune

# ── Help ──────────────────────────────────────────────────────────
help: ## Show this help
	@echo "CodeGuard AI — Available Commands"
	@echo "═════════════════════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment overrides: ENV=staging|production (default: production)"

# ── Development ───────────────────────────────────────────────────
dev: ## Start development stack with hot-reload
	$(COMPOSE_DEV) up --build -d
	@echo "✅ Development stack running at http://localhost:3000"

up: ## Start the $(ENV) stack
	$(COMPOSE) up -d
	@echo "✅ $(ENV) stack started"

down: ## Stop the $(ENV) stack
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

ps: ## Show running containers
	$(COMPOSE) ps

# ── Build ──────────────────────────────────────────────────────────
build: ## Build all images locally
	docker build -t codeguard-api:$(GIT_SHA) -t codeguard-api:latest ./backend
	docker build --build-arg NGINX_ENV=prod -t codeguard-frontend:$(GIT_SHA) -t codeguard-frontend:latest ./frontend
	docker build -f ./backend/Dockerfile.celery -t codeguard-celery:$(GIT_SHA) -t codeguard-celery:latest ./backend
	docker build -f ./backend/Dockerfile.scanner -t codeguard-scanner:$(GIT_SHA) -t codeguard-scanner:latest ./backend

build-push: ## Build, tag, and push images to registry
	docker buildx build --platform linux/amd64 \
		-t $(BACKEND_IMG)-$(GIT_SHA) -t $(BACKEND_IMG) \
		--push ./backend
	docker buildx build --platform linux/amd64 \
		--build-arg NGINX_ENV=prod \
		-t $(FRONTEND_IMG)-$(GIT_SHA) -t $(FRONTEND_IMG) \
		--push ./frontend
	docker buildx build --platform linux/amd64 \
		-f ./backend/Dockerfile.celery \
		-t $(CELERY_IMG)-$(GIT_SHA) -t $(CELERY_IMG) \
		--push ./backend

# ── Deploy ────────────────────────────────────────────────────────
deploy: ## Full production deploy: build → push → migrate → rollout
	@echo "🚀 Deploying to $(ENV) (sha: $(GIT_SHA))..."
	make build-push IMAGE_TAG=$(GIT_SHA)
	make db-migrate
	$(COMPOSE) up -d --no-deps --build api celery celery-beat frontend
	@echo "⏳ Waiting for health check..."
	@sleep 15
	make health
	@echo "✅ Deployment complete"

deploy-rollback: ## Rollback to previous image tag
	@read -p "Enter tag to rollback to: " tag; \
	$(COMPOSE) up -d --no-deps \
		-e API_IMAGE=$(DOCKER_REGISTRY)/api:$$tag \
		-e FRONTEND_IMAGE=$(DOCKER_REGISTRY)/frontend:$$tag

deploy-status: ## Show deployment status and versions
	$(COMPOSE) ps
	@echo ""
	@echo "Health check:"
	@curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool 2>/dev/null || echo "❌ API unreachable"
	@curl -sf http://localhost/health | python3 -m json.tool 2>/dev/null || echo "❌ Frontend unreachable"

# ── Staging ───────────────────────────────────────────────────────
staging: ## Start staging environment
	ENV=staging $(COMPOSE_STAGING) up -d --build
	@echo "✅ Staging environment running at http://localhost:3000"

staging-down: ## Stop staging environment
	ENV=staging $(COMPOSE_STAGING) down

# ── Database ──────────────────────────────────────────────────────
db-migrate: ## Run database migrations
	$(COMPOSE) exec api alembic upgrade head
	@echo "✅ Migrations applied"

db-migrate-down: ## Rollback last migration (DANGEROUS — use with caution)
	@read -p "⚠️  Rollback last migration? [y/N]: " confirm; \
	[ "$$confirm" = "y" ] && $(COMPOSE) exec api alembic downgrade -1 || echo "Cancelled"

db-seed: ## Seed database with development data
	$(COMPOSE) exec api python -m app.scripts.seed_db

db-backup: ## Create a PostgreSQL backup
	@mkdir -p backups
	@BACKUP_FILE="codeguard_$$(date +%Y%m%d_%H%M%S).sql.gz"; \
	$(COMPOSE) exec -T postgres pg_dump -U codeguard_user codeguard | gzip > "backups/$$BACKUP_FILE"; \
	echo "✅ Backup saved: backups/$$BACKUP_FILE"

db-restore: ## Restore PostgreSQL from backup file
	@read -p "Enter backup file path (relative to backups/): " file; \
	$(COMPOSE) exec -T postgres psql -U codeguard_user codeguard < <(gunzip -c "backups/$$file"); \
	echo "✅ Database restored from: $$file"

# ── Certificates ──────────────────────────────────────────────────
certs-generate: ## Generate JWT and TLS certificates
	@mkdir -p certs
	@echo "🔐 Generating RS256 JWT keys..."
	cd backend && bash generate_keys.sh ../certs
	@echo "🔐 Generating self-signed TLS certificate (for dev/staging)..."
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout certs/tls_private.key -out certs/fullchain.pem \
		-subj "/CN=codeguard.local/O=CodeGuard AI/C=US" \
		-addext "subjectAltName=DNS:localhost,DNS:codeguard.local" 2>/dev/null
	@chmod 600 certs/tls_private.key certs/jwt_private.pem
	@echo "✅ Certificates generated in certs/"

certs-renew: ## Renew Let's Encrypt certificates
	docker compose -f docker-compose.yml -f docker-compose.prod.yml \
		run --rm certbot certonly \
		--webroot --webroot-path /var/www/certbot \
		-d $${DOMAIN:-codeguard.example.com} \
		-d $${DOMAIN_WWW:-www.codeguard.example.com}
	$(COMPOSE) exec frontend nginx -s reload
	@echo "✅ Certificates renewed"

# ── Health Checks ─────────────────────────────────────────────────
health: ## Quick health check
	@echo "API:    $$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("status","unknown"))' || echo '❌ unreachable')"
	@echo "Frontend: $$(curl -sf -o /dev/null -w '%{http_code}' http://localhost/health 2>/dev/null || echo '❌ unreachable')"

health-verbose: ## Detailed health check with all subsystems
	@echo "═══ API Health ═══"
	@curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool 2>/dev/null || echo "❌ API unreachable"
	@echo ""
	@echo "═══ API Readiness ═══"
	@curl -sf http://localhost:8000/api/v1/ready | python3 -m json.tool 2>/dev/null || echo "❌ API not ready"
	@echo ""
	@echo "═══ Frontend ═══"
	@curl -sf -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" http://localhost/health 2>/dev/null || echo "❌ Frontend unreachable"
	@echo ""
	@echo "═══ Docker Services ═══"
	@$(COMPOSE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# ── Testing ───────────────────────────────────────────────────────
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests with coverage
	cd backend && python -m pytest tests/ -v --tb=short \
		--cov=app --cov-report=term-missing --cov-fail-under=40

test-frontend: ## Run frontend tests
	cd frontend && npm test -- --coverage

test-e2e: ## Run end-to-end tests
	cd frontend && npx playwright test

# ── Linting ───────────────────────────────────────────────────────
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend Python code
	cd backend && ruff check app/ main.py

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

# ── Logs ──────────────────────────────────────────────────────────
logs: ## Show recent logs from all services
	$(COMPOSE) logs --tail=50

logs-follow: ## Follow all logs in real-time
	$(COMPOSE) logs -f

logs-api: ## Follow API logs
	$(COMPOSE) logs -f api

logs-celery: ## Follow Celery worker logs
	$(COMPOSE) logs -f celery celery-beat

logs-frontend: ## Follow nginx/frontend logs
	$(COMPOSE) logs -f frontend

# ── Cleanup ───────────────────────────────────────────────────────
clean: ## Remove stopped containers and dangling images
	$(COMPOSE) down --remove-orphans
	docker image prune -f

clean-volumes: ## Remove all project volumes (DESTRUCTIVE — loses data)
	@read -p "⚠️  This will delete all database and cache data. Continue? [y/N]: " confirm; \
	[ "$$confirm" = "y" ] && $(COMPOSE) down -v || echo "Cancelled"

clean-images: ## Remove all project images
	$(COMPOSE) down --rmi all

docker-prune: ## Full Docker system prune (global)
	docker system prune -a --volumes -f