"""
CodeGuard AI - Test Configuration and Fixtures
Shared fixtures for all tests: in-memory SQLite database, authenticated client, mocked AI.
"""

import asyncio
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.services.auth import get_password_hash, create_access_token


# ─── Test Database ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Import all models so create_all picks them up
    from app.models.user import User  # noqa: F401
    from app.models.project import Project  # noqa: F401
    from app.models.code_file import CodeFile  # noqa: F401
    from app.models.analysis import Analysis, Finding, FixSuggestion  # noqa: F401
    from app.models.share_token import ShareToken  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


# ─── Test Client ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(test_db: AsyncSession):
    """Create an HTTP test client with dependency overrides."""
    from main import app
    from app.db.session import get_session

    async def override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ─── Test Users ───────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession):
    """Create a test developer user and return (user_dict, token)."""
    from app.models.user import User

    user_id = str(uuid.uuid4())
    hashed_pw = get_password_hash("TestP@ss123")
    user = User(
        id=user_id,
        email="testuser@codeguard.test",
        full_name="Test User",
        hashed_password=hashed_pw,
        role="developer",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(
        user_id=uuid.UUID(user_id),
        extra_claims={"email": user.email, "role": user.role},
    )

    return {
        "user": user,
        "id": user_id,
        "email": user.email,
        "token": token,
        "password": "TestP@ss123",
    }


@pytest_asyncio.fixture
async def admin_user(test_db: AsyncSession):
    """Create an admin user and return (user_dict, token)."""
    from app.models.user import User

    user_id = str(uuid.uuid4())
    hashed_pw = get_password_hash("AdminP@ss123")
    user = User(
        id=user_id,
        email="admin@codeguard.test",
        full_name="Admin User",
        hashed_password=hashed_pw,
        role="admin",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(
        user_id=uuid.UUID(user_id),
        extra_claims={"email": user.email, "role": user.role},
    )

    return {
        "user": user,
        "id": user_id,
        "email": user.email,
        "token": token,
        "password": "AdminP@ss123",
    }


@pytest.fixture
def auth_headers(test_user):
    """Return authorization headers for the test user."""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
def admin_headers(admin_user):
    """Return authorization headers for the admin user."""
    return {"Authorization": f"Bearer {admin_user['token']}"}


# ─── Mock AI ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ai_chain():
    """Mock the AI fallback chain to avoid real LLM calls."""
    from unittest.mock import AsyncMock, MagicMock

    mock_chain = MagicMock()
    mock_chain.generate = AsyncMock(return_value={
        "response": '{"findings": [{"vulnerability_type": "SQL Injection", "severity": "high", "cwe_id": "CWE-89", "file_path": "test.py", "line_number": 5, "code_snippet": "query = \\"SELECT * FROM users WHERE id = \\" + user_id", "explanation": "String concatenation in SQL query", "remediation": "Use parameterized queries", "confidence": 0.9}], "summary": "1 finding", "language": "python", "total_findings": 1}',
        "provider": "mock",
        "model": "test-model",
    })
    return mock_chain


@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama client to avoid real server calls."""
    from unittest.mock import AsyncMock, MagicMock

    mock_client = MagicMock()
    mock_client.generate = AsyncMock(return_value={"response": "mock response"})
    mock_client.chat = AsyncMock(return_value={"response": "mock response"})
    mock_client.check_health = AsyncMock(return_value={"available": True, "models": []})
    return mock_client