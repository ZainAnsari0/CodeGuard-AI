"""Database migration utilities.

In production: run alembic migrations (refuse to start if they fail).
In development: use create_all as convenience, with a warning.
"""
import logging
import subprocess
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_alembic_config_path() -> Path:
    """Find the alembic.ini file."""
    # Look relative to the app root
    for candidate in [Path("alembic.ini"), Path(__file__).parent.parent.parent / "alembic.ini"]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("alembic.ini not found")


def run_alembic_upgrade() -> bool:
    """Run alembic upgrade head synchronously.
    
    Returns True if migrations succeeded, False otherwise.
    """
    try:
        alembic_ini = get_alembic_config_path()
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(alembic_ini.parent),
        )
        if result.returncode == 0:
            logger.info("Alembic migrations applied successfully")
            return True
        else:
            logger.error("Alembic migration failed:\nstdout: %s\nstderr: %s", result.stdout, result.stderr)
            return False
    except Exception as e:
        logger.error("Failed to run alembic migrations: %s", e)
        return False


async def ensure_schema(engine: AsyncEngine) -> None:
    """Ensure database schema is up to date.
    
    In production: Run alembic migrations. Refuse to start if they fail.
    In development: Use create_all for convenience (with a warning).
    """
    if settings.ENVIRONMENT == "production":
        logger.info("Production mode: running alembic migrations...")
        
        # Check if database has existing tables from create_all but no alembic_version
        try:
            async with engine.connect() as conn:
                from sqlalchemy import text
                has_users = await conn.scalar(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users')")
                )
                has_alembic = await conn.scalar(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')")
                )
                
                if has_users and not has_alembic:
                    logger.warning("Database has existing tables but no alembic_version. Stamping to head...")
                    alembic_ini = get_alembic_config_path()
                    stamp_result = subprocess.run(
                        [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "stamp", "head"],
                        capture_output=True,
                        text=True,
                        cwd=str(alembic_ini.parent),
                    )
                    if stamp_result.returncode == 0:
                        logger.info("Alembic stamped database to head successfully")
                    else:
                        logger.error("Failed to stamp database: %s", stamp_result.stderr)
        except Exception as e:
            logger.warning("Failed to check database tables for bootstrapping: %s", e)

        if not run_alembic_upgrade():
            raise RuntimeError(
                "Database migrations failed — refusing to start in production. "
                "Run 'alembic upgrade head' manually to diagnose."
            )
    else:
        logger.warning(
            "Development mode: using create_all instead of alembic migrations. "
            "This is fine for dev but migrations should be used for schema changes."
        )
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)