"""
CodeGuard AI - Database Session Management
Handles database connections and session management.
Supports both SQLite (local dev) and PostgreSQL (production).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
from app.core.config import settings

# Detect database type for engine configuration
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": False,
}

if is_sqlite:
    # SQLite-specific settings
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL-specific settings
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 3600

    # Statement timeout prevents runaway queries from hogging connections
    if settings.DATABASE_STATEMENT_TIMEOUT > 0:
        engine_kwargs["connect_args"] = {
            "options": f"-c statement_timeout={settings.DATABASE_STATEMENT_TIMEOUT * 1000}"
        }

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)


# Enable WAL mode and foreign keys for SQLite
if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_session() -> AsyncSession:
    """Dependency for getting database sessions.

    Note: Endpoints must call `await db.commit()` explicitly.
    This dependency only handles rollback on unhandled exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)