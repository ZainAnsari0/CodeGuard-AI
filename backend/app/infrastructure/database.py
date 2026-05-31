"""CodeGuard AI - Infrastructure Database Module

Enhanced session management with DatabaseManager pattern.
Supports both SQLite (dev) and PostgreSQL (production).

The DatabaseManager provides explicit lifecycle control (init/close)
and should be used in the app lifespan. The module also re-exports
lazy-initialized engine, AsyncSessionLocal, and get_session from
app.db.session for backward compatibility.
"""

from app.db.session import (
    _init_engine,
    get_session,
    engine,
    AsyncSessionLocal,
    Base,
    init_db,
    drop_db,
)


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
        self._initialized = False

    async def init(self):
        """Initialize engine and session factory. Call once at startup."""
        _init_engine()
        self._initialized = True

    async def get_session(self):
        """Async generator dependency for getting database sessions."""
        async for session in get_session():
            yield session

    async def close(self):
        """Dispose of the engine. Call once at shutdown."""
        from app.db.session import _engine
        if _engine is not None:
            await _engine.dispose()


# Module-level singleton for use in lifespan
db_manager = DatabaseManager()

__all__ = [
    "DatabaseManager",
    "db_manager",
    "get_session",
    "engine",
    "Base",
]