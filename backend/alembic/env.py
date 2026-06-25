import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from sqlmodel import SQLModel
from app.db.session import Base

# Import all models so Alembic can detect them
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.code_file import CodeFile  # noqa: F401
from app.models.analysis import Analysis, Finding, FixSuggestion  # noqa: F401
from app.models.class_ import Class_, Enrollment  # noqa: F401
from app.models.kb_article import KBArticle  # noqa: F401
from app.models.system_event import SystemEvent  # noqa: F401
from app.models.share_token import ShareToken  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use async-compatible URL, convert for alembic sync usage
sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()