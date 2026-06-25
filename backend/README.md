# CodeGuard AI - Backend

FastAPI backend for CodeGuard AI security analysis platform.

## Project Structure

```
backend/
├── app/
│   ├── ai/           # AI pipeline (multi-provider fallback chain)
│   ├── api/          # API endpoints
│   ├── core/         # Core functionality (config, exceptions, security)
│   ├── db/           # Database connections
│   ├── models/       # SQLModel database models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic services
│   │   ├── auth.py              # JWT, bcrypt, lockout
│   │   ├── scan_orchestrator.py # Full scan pipeline
│   │   ├── temp_workspace.py    # Ephemeral workspace management
│   │   └── ...
│   └── tasks/        # Celery tasks (async scan execution)
├── scanner/          # AST scanners (run in-process)
├── alembic/          # Database migrations
├── scripts/          # Operational scripts
├── main.py           # FastAPI application entry point
└── requirements.txt  # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (or SQLite for development)
- Redis 7+ (optional, for caching and task queue)
- Node.js 18+ (for JavaScript scanning)

### Development Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd CodeGuard_AI/backend
```

2. Create virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set up environment variables:

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/codeguard
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=your-jwt-secret-key
```

4. Generate JWT keys (for RS256):

```bash
bash scripts/setup-tls.sh self-signed
```

5. Run database migrations:

```bash
alembic upgrade head
```

6. Start the development server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

7. Start Celery worker (separate terminal):

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Key Features

- **User Authentication**: JWT-based auth (RS256 production / HS256 dev) with refresh tokens
- **Project Management**: CRUD operations for projects
- **Security Analysis**: AST-based static analysis with AI enrichment
- **AI Fallback Chain**: OpenAI → Anthropic → Groq → OpenRouter → Ollama → Rule-based
- **Temporary Workspaces**: Ephemeral isolated directories per scan, auto-deleted after completion
- **Celery Workers**: Asynchronous scan execution

## Database Schema

### Main Tables

- **users**: User accounts with lockout and role-based access
- **projects**: Code projects to be scanned
- **code_files**: Stored code file contents
- **analyses**: Security analysis records
- **findings**: Security findings from analysis
- **fix_suggestions**: AI-generated, AST-validated fix suggestions
- **classes**: Instructor class management
- **share_tokens**: Time-limited report sharing

## Tech Stack

- **FastAPI**: Web framework
- **SQLModel**: SQL database ORM
- **Pydantic**: Data validation
- **PostgreSQL**: Primary database
- **Redis**: Caching, task queue, token revocation
- **Celery**: Asynchronous task processing
- **Alembic**: Database migrations