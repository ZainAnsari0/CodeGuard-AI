"""
CodeGuard AI - Database Session Management
Handles database connections and session management.
Supports both SQLite (local dev) and PostgreSQL (production).

Uses lazy initialization to avoid crashes on bad DATABASE_URL at import time.
The engine and session factory are NOT created until first use, so importing
this module never fails. Call _init_engine() or use get_session() to trigger
initialization.
"""

import threading
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from app.core.config import settings

# Lazy-initialized module-level objects (backward compatibility)
_engine = None
_AsyncSessionLocal = None
_engine_lock = threading.Lock()

Base = declarative_base()


def _init_engine():
    """Initialize the database engine and session factory on first use.

    This avoids creating the engine at module import time, which would crash
    the entire application if DATABASE_URL is misconfigured. Thread-safe via
    double-checked locking.
    """
    global _engine, _AsyncSessionLocal

    if _engine is not None:
        return  # Already initialized

    with _engine_lock:
        if _engine is not None:
            return  # Double-check after acquiring lock

        try:
            is_sqlite = settings.DATABASE_URL.startswith("sqlite")

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
                    timeout_ms = settings.DATABASE_STATEMENT_TIMEOUT * 1000
                    if settings.DATABASE_URL.startswith("postgresql+asyncpg"):
                        # asyncpg uses server_settings, not libpq options
                        if "connect_args" not in engine_kwargs:
                            engine_kwargs["connect_args"] = {}
                        if "server_settings" not in engine_kwargs["connect_args"]:
                            engine_kwargs["connect_args"]["server_settings"] = {}
                        engine_kwargs["connect_args"]["server_settings"]["statement_timeout"] = str(timeout_ms)
                    else:
                        # psycopg2 / other drivers use libpq options
                        engine_kwargs["connect_args"] = {
                            "options": f"-c statement_timeout={timeout_ms}"
                        }

            db_url = settings.DATABASE_URL
            if not is_sqlite and "sslmode" in db_url:
                import urllib.parse
                parsed = urllib.parse.urlparse(db_url)
                query_params = urllib.parse.parse_qs(parsed.query)
                sslmode = query_params.pop("sslmode", [None])[0]
                new_query = urllib.parse.urlencode(query_params, doseq=True)
                parsed = parsed._replace(query=new_query)
                db_url = urllib.parse.urlunparse(parsed)
                
                # Configure SSL for asyncpg
                if "connect_args" not in engine_kwargs:
                    engine_kwargs["connect_args"] = {}
                if sslmode in ["require", "prefer", "allow", "verify-ca", "verify-full"]:
                    engine_kwargs["connect_args"]["ssl"] = True

            _engine = create_async_engine(db_url, **engine_kwargs)

            # Enable WAL mode and foreign keys for SQLite
            if is_sqlite:
                @event.listens_for(_engine.sync_engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            _AsyncSessionLocal = async_sessionmaker(
                _engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize database engine: {e}. "
                f"Check your DATABASE_URL setting."
            ) from e


# Backward-compatible module-level attributes.
# These lazily initialize on first access so existing code like
#   from app.db.session import engine
#   engine.begin()
# continues to work unchanged.
class _LazyEngine:
    """Lazy proxy that creates the real engine on first attribute access."""

    def __getattr__(self, name):
        _init_engine()
        return getattr(_engine, name)

    def __bool__(self):
        _init_engine()
        return bool(_engine)

    def __await__(self):
        # Allow `await engine.dispose()` etc. — delegate to real engine
        _init_engine()
        return _engine.__await__()

    @property
    def _actual(self):
        """Get the real engine object (for explicit access)."""
        _init_engine()
        return _engine


class _LazySessionFactory:
    """Lazy proxy that creates the real session factory on first call."""

    def __call__(self, **kwargs):
        _init_engine()
        return _AsyncSessionLocal(**kwargs)


# Module-level exports — backward compatible with all existing code:
#   from app.db.session import engine, AsyncSessionLocal, get_session, Base
engine = _LazyEngine()
AsyncSessionLocal = _LazySessionFactory()


async def get_session() -> AsyncSession:
    """Dependency for getting database sessions.

    Note: Endpoints must call `await db.commit()` explicitly.
    This dependency only handles rollback on unhandled exceptions.
    """
    _init_engine()
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Initialize database tables (development only — use alembic in production)."""
    _init_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables."""
    _init_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)