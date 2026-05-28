# CodeGuard AI - Backend

FastAPI backend for CodeGuard AI security analysis platform.

## Project Structure

```
backend/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core functionality (config, exceptions, security)
│   ├── db/           # Database connections
│   ├── models/       # SQLModel database models
│   ├── schemas/      # Pydantic schemas
│   └── services/     # Business logic services
├── alembic/          # Database migrations
├── main.py           # FastAPI application entry point
└── requirements.txt  # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Development Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd CodeGuard_AI/backend
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/codeguard
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

4. Run database migrations:

```bash
alembic upgrade head
```

5. Start the development server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

1. Start Docker services:

```bash
docker-compose up -d
```

2. Run migrations:

```bash
docker-compose exec backend alembic upgrade head
```

3. View logs:

```bash
docker-compose logs -f backend
```

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Features

- **User Authentication**: JWT-based authentication with fastapi-users
- **Project Management**: CRUD operations for projects
- **Security Analysis**: REST API for security scan triggers and results
- **Git Integration**: Support for GitHub and GitLab repositories
- **Celery Workers**: Asynchronous task processing

## Database Schema

### Main Tables

- **users**: User accounts
- **projects**: Code projects to be scanned
- **code_files**: Stored code file contents
- **analyses**: Security analysis records
- **findings**: Security findings from analysis
- **fix_suggestions**: Automated fix suggestions

## Tech Stack

- **FastAPI**: Web framework
- **SQLModel**: SQL database ORM
- **Pydantic**: Data validation
- **PostgreSQL**: Primary database
- **Redis**: Caching and task queue
- **Celery**: Asynchronous task processing
- **Alembic**: Database migrations