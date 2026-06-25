"""
CodeGuard AI - Celery Application Configuration
Async task queue for background processing.
"""

import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

if not settings.REDIS_ENABLED:
    logger.warning(
        "REDIS_ENABLED is False — Celery requires Redis as a broker. "
        "Set REDIS_ENABLED=True and configure REDIS_URL to enable background tasks."
    )

celery_app = Celery(
    "codeguard_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.scan_tasks",
        "app.tasks.auth_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute hard limit
    task_soft_time_limit=240,  # 4 minute soft limit
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
)