# CodeGuard AI

**AI-Powered Code Vulnerability Scanner with Explainable Feedback**

CodeGuard AI is a privacy-first, AI-augmented static application security testing (SAST) platform designed for educational and junior-developer contexts. It transforms deterministic AST-based vulnerability detection into human-readable, educational experiences through a multi-tier LLM pipeline with deterministic fallbacks.

## Features

- **AST-based scanning** for Python and JavaScript code
- **AI-powered explanations** with LLM fallback chain (Ollama → Groq → OpenAI)
- **Validated remediation** — every AI-generated fix passes syntactic validation
- **Ephemeral Docker containers** — zero code persistence after scan
- **Role-based access** — Student, Instructor, Admin roles
- **Shared reports** — generate shareable links for scan findings
- **Knowledge base** — CWE-based educational content
- **Dark/light theme** with responsive design

## Tech Stack

| Layer      | Technology                                        |
|------------|---------------------------------------------------|
| Frontend   | React 19, Vite 8, TanStack Query, Zustand, Tailwind |
| Backend    | FastAPI, SQLModel, PostgreSQL, Redis, Celery       |
| AI         | Ollama (local), Groq (fast), OpenAI (fallback)     |
| Scanning   | Docker containers, Python AST, JS Acorn parser     |
| Infra      | Docker Compose, Nginx, Prometheus, Grafana          |

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2+
- 4GB+ RAM, 2+ CPU cores

### Development Setup

```bash
# Clone and configure
git clone <repo-url> && cd FYP
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, GROQ_API_KEY)

# Generate JWT keys
bash backend/scripts/setup-tls.sh self-signed

# Start services
docker compose up -d

# Run database migrations
docker exec codeguard_api alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# API Docs:  http://localhost:8000/api/v1/docs
# Health:    http://localhost:8000/health
```

### Production Deployment

```bash
# Configure production environment
cp .env.production .env.production.local
# Edit ALL CHANGE_ME placeholders

# Generate TLS certificates
bash backend/scripts/setup-tls.sh production

# Deploy
bash backend/scripts/deploy.sh production
```

See [docs/deployment.md](docs/deployment.md) for full deployment documentation.

## Testing

```bash
# Backend tests (112 tests)
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend tests (41 tests)
cd frontend
npm test -- --coverage

# E2E tests
cd frontend
npx playwright test

# Security audit
cd backend && bash scripts/security_audit.sh
cd frontend && bash scripts/security_audit.sh
```

## Project Structure

```
FYP/
├── backend/               # FastAPI backend
│   ├── app/               # Application code
│   │   ├── ai/            # AI pipeline (Ollama, Groq, OpenAI)
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Config, JWT, rate limiting
│   │   ├── db/            # Database session
│   │   ├── models/        # SQLModel models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── tasks/         # Celery tasks
│   ├── alembic/           # Database migrations
│   ├── scripts/           # Utility scripts
│   ├── tests/             # Test suite
│   └── Dockerfile
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components
│   │   ├── store/         # Zustand stores
│   │   ├── hooks/         # Custom hooks
│   │   └── types/         # TypeScript types
│   ├── e2e/               # Playwright E2E tests
│   ├── nginx.conf         # Dev nginx config
│   ├── nginx.prod.conf    # Production nginx config
│   └── Dockerfile
├── monitoring/            # Prometheus + Grafana
│   ├── prometheus.yml
│   ├── alerts.yml
│   └── grafana/           # Dashboards & provisioning
├── certs/                 # TLS & JWT keys (gitignored)
├── docker-compose.yml     # Development compose
├── docker-compose.prod.yml # Production overlay
└── docs/                  # Documentation
```

## Team

- **Zain Ansari** — AI/ML Engineer (AI pipeline, scanning engine, benchmarking)
- **Burhan** — Backend Engineer (API, auth, database, deployment)
- **Saad** — Frontend Engineer (UI, state management, E2E testing)

## License

This project is developed for the Final Year Project at the University of Central Punjab, Faculty of Information Technology & Computer Science.