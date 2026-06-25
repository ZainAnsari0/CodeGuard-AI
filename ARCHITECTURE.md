# CodeGuard AI — Enterprise Architecture Refactoring Plan

> Authored by: Principal Software Architect  
> Date: 2026-05-31  
> Status: Awaiting Implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Architecture Audit](#2-current-architecture-audit)
3. [Target Architecture Design](#3-target-architecture-design)
4. [Refactored Folder Structure](#4-refactored-folder-structure)
5. [Production-Grade Patterns](#5-production-grade-patterns)
6. [Long-Term Maintainability](#6-long-term-maintainability)
7. [Enterprise Best Practices](#7-enterprise-best-practices)
8. [Migration Strategy](#8-migration-strategy)

---

## 1. Executive Summary

CodeGuard AI is a full-stack security analysis platform (FastAPI + React/TypeScript) with AI-powered vulnerability scanning, ephemeral temporary workspaces for static analysis, Celery task queues, and an instructor/class management subsystem. The codebase is functional but exhibits architectural debt that will impede scaling.

### Key Findings

| Area | Current State | Risk |
|------|---------------|------|
| **Separation of Concerns** | Business logic in endpoint handlers | High — untestable, duplicated logic |
| **Data Access** | Raw SQLAlchemy queries in routes | High — no abstraction, impossible to swap DB |
| **Service Layer** | Ad-hoc singletons, no DI | Medium — hard to mock, circular imports |
| **Schemas/Models** | Mixed in model files | Medium — violates SRP, DTOs coupled to ORM |
| **Configuration** | Single monolithic Settings | Low-Medium — growing config in one class |
| **Error Handling** | Inconsistent AppException vs HTTPException | Medium — leaking HTTP concerns into domain |
| **API Contracts** | Mixed `dict` and `ResponseSchema` returns | Medium — no consistent envelope |
| **State Management (FE)** | Stores call raw `fetch` | Medium — no API layer, hard to mock |
| **Type Safety (FE)** | Monolithic `types/index.ts` | Low — grows unbounded |
| **Testing** | Mixed unit/integration at top level | Medium — unclear test boundaries |

---

## 2. Current Architecture Audit

### 2.1 Backend Issues

```
app/
├── api/
│   ├── dependencies.py       # Auth + ownership checks (good, but thin)
│   ├── routes.py              # Flat router registration
│   └── endpoints/             # 13 endpoint files — most 100-300 lines
│       ├── scanner.py         # 280+ lines: file I/O + DB + task queue
│       ├── auth.py            # 200+ lines: registration, login, refresh, password reset
│       ├── admin.py           # 300+ lines: user CRUD + health + events
│       └── ...
├── core/
│   ├── config.py              # Single 130-line Settings class (all domains)
│   ├── exceptions.py          # Good hierarchy but HTTPException coupling
│   ├── logging.py             # Structured logging (good)
│   └── rate_limit.py          # Cookie-based rate limiting
├── models/                    # ORM models WITH schemas mixed in (ProjectCreate, etc.)
├── schemas/                   # Separate schemas exist but models still have their own
├── services/
│   ├── auth.py                 # 350+ lines: tokens, hashing, revocation, Redis
│   ├── cache.py                # Sync Redis + LRU fallback (should be fully async)
│   ├── temp_workspace.py           # Ephemeral scan workspace management
│   ├── scan_orchestrator.py    # Good separation but imports ai_chain singleton
│   └── file_validator.py       # File validation
├── ai/                         # AI provider chain (good structure)
│   ├── providers/              # Strategy pattern for AI providers
│   ├── prompts/                # Jinja2 template management
│   ├── fallback_chain.py       # Circuit breaker + fallback
│   ├── ollama_client.py        # Direct client (duplicates provider)
│   └── parser.py                # LLM output parser
└── tasks/                      # Celery tasks
    ├── celery_app.py
    ├── scan_tasks.py            # Uses sync engine, does direct DB writes
    └── auth_tasks.py
```

#### Critical Anti-Patterns

**A. Fat Endpoints** — `scanner.py` handles upload, validation, DB writes, file I/O, task dispatch. This should be 3-4 separate service methods.

**B. No Repository Layer** — Every endpoint directly writes `select(User).where(...)` queries. Changes to the data model require touching every endpoint.

**C. Singleton Globals** — `ollama_client`, `prompt_cache`, `ai_chain`, `email_service`, `workspace_service`, `ast_validator` are module-level singletons. This prevents DI-based testing and causes import-time side effects.

**D. Schema Duplication** — `ProjectCreate`, `ProjectUpdate`, `ProjectResponse` appear in both `models/project.py` and `schemas/project.py`. Same for `CodeFile*` schemas.

**E. Inconsistent Response Envelope** — Some endpoints return `ResponseSchema(data=...)`, others return `{"success": True, "data": ...}` as raw dicts, some use `PaginatedResponse`. No single standard.

### 2.2 Frontend Issues

```
src/
├── components/          # Flat per-category, no feature grouping
├── hooks/               # Data-fetching hooks with inline fetch calls
├── lib/                 # Two files (api.ts, validation.ts)
├── pages/               # 17 flat page components
├── store/               # Zustand stores with inline API calls
├── types/               # Single 200-line index.ts
└── utils/               # One file (severity.ts)
```

**A. No API Service Layer** — `authStore.ts` has 150+ lines of raw `fetch()` calls with URL construction, error parsing, and cookie handling repeated everywhere.

**B. No Feature-Based Organization** — Dashboard, scanning, admin, and knowledge base pages are all flat alongside components from different domains.

**C. Monolithic Types** — All TypeScript types in one file with no domain separation.

---

## 3. Target Architecture Design

### 3.1 Architectural Principles

```mermaid
graph TB
    subgraph "Presentation Layer"
        A[API Endpoints<br/>Thin Controllers]
        FE[Frontend Pages<br/>UI Only]
    end
    
    subgraph "Application Layer"
        B[Service Layer<br/>Business Logic]
        API_FE[API Client<br/>Type-Safe]
    end
    
    subgraph "Domain Layer"
        C[Domain Models<br/>Pure Business Objects]
        D[Schemas / DTOs<br/>Validation & Serialization]
    end
    
    subgraph "Infrastructure Layer"
        E[Repository Layer<br/>Data Access]
        F[AI Providers<br/>External Services]
        G[Task Queue<br/>Celery Workers]
        H[Cache / Redis<br/>Infrastructure]
    end
    
    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    B --> H
    FE --> API_FE
    API_FE --> A
```

### 3.2 Clean Architecture Layers

```mermaid
graph LR
    subgraph "Dependency Direction →"
        EP[Endpoints] --> SVC[Services]
        SVC --> REPO[Repositories]
        REPO --> MODELS[ORM Models]
        SVC --> SCHEMAS[Schemas/DTOs]
        SVC r,
    public code: string,
    public message: string,
    public details?: Record<string, unknown>,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | undefined>
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
    const url = new URL(path.startsWith('http') ? path : `${this.baseUrl}${path}`)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) url.searchParams.set(key, String(value))
      })
    }
    return url.toString()
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(path, params)

    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    }
    if (options.body && typeof options.body === 'string') {
      headers['Content-Type'] = 'application/json'
    }

    const response = await fetch(url, { ...fetchOptions, headers, credentials: 'include' })

    if (!response.ok) {
      let detail = `API error: ${response.status}`
      let code = 'UNKNOWN_ERROR'
      try {
        const body = await response.json()
        if (body.error) {
          // New envelope format
          throw new ApiError(response.status, body.error.code, body.error.message, body.error.details)
        }
        detail = body.detail || body.message || detail
        code = body.code || code
      } catch (e) {
        if (e instanceof ApiError) throw e
      }
      throw new ApiError(response.status, code, detail)
    }

    const text = await response.text()
    if (!text) return undefined as T
    const json = JSON.parse(text)
    // Unwrap envelope: { success: true, data: T }
    return json.data ?? json
  }

  async get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
    return this.request<T>(path, { method: 'GET', params })
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type — browser sets it with boundary
    })
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' })
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
```

```typescript
// frontend/src/features/auth/api/authApi.ts

import { apiClient } from '../../../shared/api/client'
import type { User, AuthStore } from '../types/auth'

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.postForm<{ user: User }>('/api/v1/auth/login', 
      new URLSearchParams({ username: email, password })),
  
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    apiClient.post<{ user: User }>('/api/v1/auth/register', data),
  
  logout: () =>
    apiClient.post<void>('/api/v1/auth/logout', {}),
  
  refresh: () =>
    apiClient.post<{ access_token: string }>('/api/v1/auth/refresh', {}),
  
  me: () =>
    apiClient.get<User>('/api/v1/auth/me'),
  
  forgotPassword: (email: string) =>
    apiClient.post<{ message: string }>('/api/v1/auth/forgot-password', { email }),
  
  resetPassword: (token: string, newPassword: string) =>
    apiClient.post<{ message: string }>('/api/v1/auth/reset-password', { token, new_password: newPassword }),
}
```

### 5.7 Repository Pattern for Frontend Data

```typescript
// frontend/src/features/scanning/api/scanApi.ts

import { apiClient } from '../../../shared/api/client'
import type { ScanResult, ScanStatus } from '../types/scan'

export const scanApi = {
  upload: (files: File[], language: string) => {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    formData.append('language', language)
    return apiClient.postForm<{ scan_id: string; file_count: number }>('/api/v1/scanner/upload', formData)
  },

  getStatus: (scanId: string) =>
    apiClient.get<ScanStatus>(`/api/v1/scanner/${scanId}/status`),

  getResults: (scanId: string) =>
    apiClient.get<ScanResult>(`/api/v1/scanner/${scanId}/results`),

  getHistory: (params?: { skip?: number; limit?: number }) =>
    apiClient.get<{ items: ScanResult[]; total: number }>('/api/v1/scanner/history', params),
}
```

---

## 6. Long-Term Maintainability

### 6.1 Split Configuration

```python
# app/core/config/base.py
from pydantic_settings import BaseSettings

class BaseAppSettings(BaseSettings):
    """Base settings shared across all environments."""
    PROJECT_NAME: str = "CodeGuard AI"
    PROJECT_DESCRIPTION: str = "AI-powered code analysis platform"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# app/core/config/database.py
from .base import BaseAppSettings

class DatabaseSettings(BaseAppSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeguard.db"
    DATABASE_STATEMENT_TIMEOUT: int = 30

# app/core/config/security.py
from .base import BaseAppSettings
from typing import List, Optional

class SecuritySettings(BaseAppSettings):
    SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "Accept"]
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

# app/core/config/__init__.py — compose settings
from .base import BaseAppSettings
from .database import DatabaseSettings
from .security import SecuritySettings
from .ai import AISettings
from .scanner import ScannerSettings
from .email import EmailSettings

class Settings(
    BaseAppSettings,
    DatabaseSettings,
    SecuritySettings,
    AISettings,
    ScannerSettings,
    EmailSettings,
):
    """Composed application settings."""
    
    @model_validator(mode='after')
    def validate_production_secrets(self):
        # Existing production validation
        ...
        return self

settings = Settings()
```

### 6.2 Database Session as Repository Dependency

```python
# app/infrastructure/database.py — enhanced session management

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager

from app.core.config import settings

class DatabaseManager:
    """Manages database engine and session lifecycle."""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
    
    async def init(self):
        """Initialize engine and session factory."""
        engine_kwargs = {"echo": False}
        if settings.DATABASE_URL.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs.update({
                "pool_pre_ping": True,
                "pool_size": 10,
                "max_overflow": 20,
                "pool_recycle": 3600,
            })
        
        self._engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        """Get a database session for dependency injection."""
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    
    async def close(self):
        """Dispose of the engine."""
        if self._engine:
            await self._engine.dispose()

db_manager = DatabaseManager()
```

### 6.3 Async-First Cache Layer

```python
# app/infrastructure/cache.py — fully async, no blocking calls

import json
import hashlib
import logging
import asyncio
from collections import OrderedDict
from typing import Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

class LRUCache:
    """Thread-safe in-memory LRU cache."""
    # ... (same as current, but documented)

class AsyncPromptCache:
    """Async cache with Redis primary + LRU fallback."""
    
    def __init__(self, redis_url: Optional[str] = None, ttl: int = 3600, enabled: bool = True):
        self.redis_url = redis_url
        self.ttl = ttl
        self.enabled = enabled
        self._redis: Optional[aioredis.Redis] = None
        self._fallback = LRUCache(max_size=256)
        self._lock = asyncio.Lock()
    
    async def _get_redis(self) -> Optional[aioredis.Redis]:
        """Get or create async Redis client."""
        if self._redis is not None:
            try:
                await self._redis.ping()
                return self._redis
            except Exception:
                await self._redis.aclose()
                self._redis = None
        
        if aioredis and self.redis_url:
            try:
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
                return self._redis
            except Exception as e:
                logger.warning("AsyncPromptCache: Redis unavailable: %s", e)
                self._redis = None
        return None
    
    async def get(self, template_name: str, rendered_prompt: str, model: str) -> Optional[dict]:
        # ... (async version using await redis.get)
    
    async def set(self, template_name: str, rendered_prompt: str, model: str, response: dict, ttl: Optional[int] = None) -> bool:
        # ... (async version using await redis.setex)
```

### 6.4 Testing Strategy

```python
# tests/unit/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.auth_service import AuthService
from app.services.scan_service import ScanService
from app.repositories.user import UserRepository

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def user_repo(mock_db):
    return UserRepository(mock_db)

@pytest.fixture
def auth_service(mock_db):
    return AuthService(mock_db)

@pytest.fixture
def mock_file_validator():
    validator = MagicMock(spec=FileSecurityValidator)
    validator.validate_file.return_value = MagicMock(is_valid=True, sanitized_filename="test.py", errors=[], warnings=[])
    return validator

# tests/unit/test_services/test_scan_service.py
import pytest
from app.services.scan_service import ScanService

@pytest.mark.asyncio
async def test_upload_valid_file(mock_db, mock_file_validator):
    service = ScanService(db=mock_db, file_validator=mock_file_validator, ...)
    result = await service.upload_and_queue_scan(files=[...], user=mock_user)
    assert result.status == "pending"
```

---

## 7. Enterprise Best Practices

### 7.1 Configuration Profiles

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./codeguard.db
REDIS_ENABLED=false
EMAIL_BACKEND=console

# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://codeguard:${DB_PASSWORD}@staging-db:5432/codeguard
REDIS_ENABLED=true
EMAIL_BACKEND=smtp

# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://codeguard:${DB_PASSWORD}@prod-db:5432/codeguard
REDIS_ENABLED=true
EMAIL_BACKEND=smtp
```

### 7.2 Health Checks & Observability

```python
# app/api/endpoints/health.py — NEW: dedicated health endpoint

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.infrastructure.database import db_manager

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    """Comprehensive health check."""
    checks = {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
    }
    return checks

@router.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_session)):
    """Readiness probe — checks DB and Redis."""
    checks = {"database": "unknown", "redis": "unknown"}
    
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        checks["status"] = "unhealthy"
    
    # Redis check
    cache = AsyncPromptCache(redis_url=settings.REDIS_URL, enabled=settings.REDIS_ENABLED)
    r = await cache._get_redis()
    checks["redis"] = "ok" if r else "degraded"
    
    return checks
```

### 7.3 Request ID Tracing

```python
# app/api/middleware.py — request correlation

import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### 7.4 Security Headers

```python
# app/api/middleware.py

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # Adjust for your needs
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'"
        )
        return response
```

### 7.5 Graceful Shutdown

```python
# app/main.py — enhanced lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    
    # Validate configuration
    if not validate_jwt_keys():
        logger.error("JWT key validation failed")
        raise RuntimeError("Invalid JWT configuration")
    
    # Initialize database
    await db_manager.init()
    async with db_manager._engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Initialize services
    await initialize_services()
    
    logger.info("Application startup complete")
    yield
    
    logger.info("Shutting down application...")
    
    # Graceful shutdown
    await shutdown_services()
    await db_manager.close()
    
    logger.info("Shutdown complete")
```

### 7.6 Model-Schema Separation

Every ORM model should only contain database mapping. Schemas should be pure Pydantic models:

```python
# app/models/user.py — ORM model ONLY
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Boolean, DateTime, Integer
from datetime import datetime, timezone
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), sa_column=Column(String(36), primary_key=True))
    email: str = Field(sa_column=Column(String, nullable=False, unique=True, index=True))
    hashed_password: str = Field(sa_column=Column(String, nullable=False))
    # ... other DB fields only

# app/schemas/user.py — Pydantic DTOs ONLY
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    role: str = Field(default="developer")

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)  # ORM mode
```

---

## 8. Migration Strategy

### Phase 1: Foundation (Week 1-2)
- [ ] Split `Settings` into domain configs (database, security, AI, scanner, email)
- [ ] Create `app/core/http_exceptions.py` with domain→HTTP mapping
- [ ] Create `app/schemas/base.py` with `ApiResponse[T]`, `PaginatedResponse[T]`
- [ ] Create `app/repositories/base.py` with `BaseRepository`
- [ ] Create `app/infrastructure/database.py` with `DatabaseManager`
- [ ] Add `RequestIdMiddleware` and `SecurityHeadersMiddleware`
- [ ] Refactor `exceptions.py` to remove HTTPException inheritance

### Phase 2: Repositories (Week 2-3)
- [ ] Create `UserRepository`
- [ ] Create `AnalysisRepository`
- [ ] Create `ProjectRepository`, `CodeFileRepository`, `ShareTokenRepository`, `KBArticleRepository`
- [ ] Move all raw SQL queries from endpoints into repositories
- [ ] Write unit tests for each repository

### Phase 3: Services (Week 3-4)
- [ ] Extract `AuthService` from `app/services/auth.py` (separate token revocation into `TokenRevocationService`)
- [ ] Create `ScanService` from `endpoints/scanner.py` business logic
- [ ] Create `AnalysisService` from `endpoints/analysis.py`
- [ ] Create `ProjectService`, `UserService`, `ShareService`, `KBService`, `AdminService`, `InstructorService`
- [ ] Wire DI in `dependencies.py`
- [ ] Make all endpoints thin — only call service methods + return responses

### Phase 4: Frontend Refactor (Week 4-5)
- [ ] Create `shared/api/client.ts` (ApiClient class)
- [ ] Create per-feature `api/` subdirectories (`authApi.ts`, `scanApi.ts`, etc.)
- [ ] Move fetch logic from Zustand stores into API modules
- [ ] Restructure into `features/` directory
- [ ] Split `types/index.ts` into per-feature type files
- [ ] Simplify stores to be pure state managers (no fetch calls)

### Phase 5: Model Cleanup & Testing (Week 5-6)
- [ ] Remove schemas from model files (`ProjectCreate`, `ProjectUpdate`, etc. → move to `schemas/`)
- [ ] Remove schema imports from model files
- [ ] Update all endpoints to use new schema imports
- [ ] Add integration test fixtures using repositories
- [ ] Add health check endpoints
- [ ] Document API using OpenAPI extensions

### Phase 6: Polish & Hardening (Week 6-7)
- [ ] Add OpenAPI schema examples for all endpoints
- [ ] Add request/response validation middleware
- [ ] Create `Makefile` with common commands (test, lint, migrate, etc.)
- [ ] Add pre-commit hooks (ruff, mypy, bandit)
- [ ] Create health check endpoints for all services
- [ ] Add structured error responses to all endpoints
- [ ] Performance test and add database indexes from Sprint 5-6 migrations

---

## Summary of Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Repository Pattern** | Decouples data access from business logic; enables testing with mock repos |
| **Service Layer** | Single place for business rules; endpoints become thin controllers |
| **Dependency Injection** | Eliminates module-level singletons; enables easy testing |
| **Domain Exceptions** | Decouples error handling from HTTP; single mapping point |
| **Unified Response Envelope** | Consistent API contract for frontend; easier error handling |
| **Split Configuration** | Per-domain config files; easier to reason about and test |
| **Feature-Based Frontend** | Co-locates pages, hooks, API, types per feature; reduces navigation distance |
| **API Client Class** | Centralized error handling, auth, and response unwrapping |
| **Async-First Infrastructure** | Eliminates blocking Redis calls; proper async cache |
| **Model-Schema Separation** | Clean DTO pattern; ORM models don't leak into API contracts |

This refactoring plan transforms CodeGuard AI from a functional prototype into an enterprise-grade, maintainable, and testable codebase. Each phase is incremental and can be deployed independently.