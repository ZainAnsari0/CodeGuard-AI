# Contributing to CodeGuard AI

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (or SQLite for development)
- Redis 7+ (optional, for caching and task queue)
- Git

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend
cd backend && source venv/bin/activate
pytest tests/ -v

# Frontend
cd frontend
npm test

# E2E
cd frontend && npx playwright test
```

## Branch Naming
- `feature/` — New features (e.g., `feature/add-scan-history`)
- `fix/` — Bug fixes (e.g., `fix/auth-token-refresh`)
- `security/` — Security fixes (e.g., `security/rate-limiting`)

## Pull Request Process
1. Create a branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Submit a PR with a description of changes

## Code Style
- Backend: Follow PEP 8, use `black` for formatting
- Frontend: Follow existing TypeScript/React patterns, use `eslint`
- Commit messages: Use conventional commits format