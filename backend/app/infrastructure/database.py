"""CodeGuard AI - Infrastructure Database Module

Enhanced session management with DatabaseManager pattern.
Supports both SQLite (dev) and PostgreSQL (production).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Detect database type for engine configuration
is_sqlite = settings.DATABASE_URL.startswith("sqlite")


class DatabaseManager:
    """Manages database engine and session lifecycle.

    Usage:
        db_manager = DatabaseManager()
        # In app lifespan:
        await db_manager.init()
        # In endpoints:
        async for session in db_manager.get_session():
            ...
        # In shutdown:
        await db_manager.close()
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None

    async def init(self):
        """Initialize engine and session factory. Call once at startup."""
        engine_kwargs = {"echo": False}

        if is_sqlite:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs.update({
                "pool_pre_ping": True,
                "pool_size": 10,
                "max_overflow": 20,
                "pool_recycle": 3600,
            })
            if settings.DATABASE_STATEMENT_TIMEOUT > 0:
                engine_kwargs["connect_args"] = {
                    "options": f"-c statement_timeout={settings.DATABASE_STATEMENT_TIMEOUT * 1000}"
                }

        self._engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

        # Enable WAL mode and foreign keys for SQLite
        if is_sqlite:
            @event.listens_for(self._engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def get_session(self):
        """Async generator dependency for getting database sessions.

        Note: Endpoints must call `await db.commit()` explicitly.
        This dependency only handles rollback on unhandled exceptions.
        """
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def close(self):
        """Dispose of the engine. Call once at shutdown."""
        if self._engine:
            await self._engine.dispose()


# Backward-compatible module-level objects
# These are initialized from settings at import time for backward compatibility.
_engine_kwargs = {"echo": False}
if is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
    })
    if settings.DATABASE_STATEMENT_TIMEOUT > 0:
        _engine_kwargs["connect_args"] = {
            "options": f"-c statement_timeout={settings.DATABASE_STATEMENT_TIMEOUT * 1000}"
        }

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# Enable WAL mode and foreign keys for SQLite
if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_session():
    """Legacy async generator dependency for getting database sessions."""
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