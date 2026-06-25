# CodeGuard AI

**AI-Powered Code Vulnerability Scanner with Explainable Feedback**

CodeGuard AI is a privacy-first, AI-augmented static application security testing (SAST) platform designed for educational and junior-developer contexts. It transforms deterministic AST-based vulnerability detection into human-readable, educational experiences through a multi-tier LLM pipeline with deterministic fallbacks.

## Features

- **AST-based scanning** for Python and JavaScript code (in-process, no containers)
- **AI-powered explanations** with LLM fallback chain (OpenAI → Anthropic → Groq → OpenRouter → Ollama → Rule-based)
- **Validated remediation** — every AI-generated fix passes syntactic validation
- **Ephemeral temporary workspaces** — zero source code persistence after scan
- **Static Analysis Safety Model** — code is parsed, never executed
- **Role-based access** — Developer, Instructor, Admin roles
- **Shared reports** — generate shareable links for scan findings
- **Knowledge base** — CWE-based educational content
- **Dark/light theme** with responsive design

## Tech Stack

| Layer      | Technology                                           |
|------------|------------------------------------------------------|
| Frontend   | React 19, Vite 8, TanStack Query, Zustand, Tailwind |
| Backend    | FastAPI, SQLModel, PostgreSQL, Redis, Celery         |
| AI         | Multi-provider fallback chain with local LLM support |
| Scanning   | Python AST, JS Acorn parser (in-process)            |
| Infra      | Render (PaaS), Nginx, Prometheus, Grafana             |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for JavaScript scanning)
- PostgreSQL 16+ (or SQLite for development)
- Redis 7+ (optional, for caching and task queue)

### Development Setup

```bash
# Clone and configure
git clone https://github.com/ZainAnsari0/CodeGuard-AI.git && cd CodeGuard-AI
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, GROQ_API_KEY, etc.)

# Generate JWT keys
bash backend/scripts/setup-tls.sh self-signed

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Frontend setup (separate terminal)
cd frontend
npm install
npm run dev    # http://localhost:5173
```

### Production Deployment (Render)

This project is configured for deployment on [Render](https://render.com) using the included `render.yaml` Blueprint.

1. Push code to GitHub
2. Connect your GitHub repo to Render
3. Configure environment variables in the Render dashboard (see `.env.example`)
4. Render auto-deploys backend (FastAPI) and frontend (static site) services

See [render.yaml](render.yaml) for service definitions and [docs/deployment.md](docs/deployment.md) for full documentation.

## Testing

```bash
# Backend tests (112+ tests)
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend tests (41+ tests)
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
│   │   ├── ai/            # AI pipeline (multi-provider fallback chain)
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Config, JWT, rate limiting
│   │   ├── db/            # Database session
│   │   ├── models/        # SQLModel models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   │   ├── auth.py              # JWT, bcrypt, lockout
│   │   │   ├── scan_orchestrator.py # Full scan pipeline
│   │   │   ├── temp_workspace.py    # Ephemeral workspace management
│   │   │   └── ...
│   │   └── tasks/         # Celery tasks
│   ├── alembic/           # Database migrations
│   ├── scanner/           # AST scanners (in-process)
│   ├── scripts/           # Utility scripts
│   └── tests/             # Test suite
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components
│   │   ├── store/         # Zustand stores
│   │   ├── hooks/         # Custom hooks
│   │   └── types/         # TypeScript types
│   └── nginx configs
├── monitoring/            # Prometheus + Grafana
├── certs/                 # JWT keys (gitignored)
├── deploy/                # Deployment scripts
├── docs/                  # Documentation
└── Makefile               # Common development commands
```

## Security Model

CodeGuard AI performs **static analysis only**. User code is:

- **Parsed** — AST analysis reads the syntax tree
- **Analyzed** — Pattern matching detects vulnerability patterns
- **Tokenized** — AI models process code as text tokens

User code is **never** executed, interpreted, or compiled. Temporary workspaces (`/tmp/codeguard_uploads/{scan_id}/`) are automatically deleted after scan completion. Only vulnerability metadata is persisted in the database.

## Team

- **Zain Ansari** — AI/ML Engineer (AI pipeline, scanning engine, benchmarking)
- **Burhan** — Backend Engineer (API, auth, database, deployment)
- **Saad** — Frontend Engineer (UI, state management, E2E testing)

## License

This project is developed for the Final Year Project at the University of Central Punjab, Faculty of Information Technology & Computer Science.