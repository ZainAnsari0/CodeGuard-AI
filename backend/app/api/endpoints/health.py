"""CodeGuard AI - Health Check Endpoints

System health, readiness, and liveness probes for monitoring and orchestration.
"""

import time as time_module
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session

router = APIRouter()

_start_time = time_module.time()


@router.get("/health", tags=["health"])
async def health_check():
    """Basic liveness probe — always returns 200 if the process is up."""
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time_module.time() - _start_time, 1),
    }


@router.get("/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_session)):
    """Readiness probe — checks database connectivity."""
    checks = {"database": "unknown", "redis": "unknown"}
    overall = "healthy"

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        overall = "unhealthy"

    # Redis check
    if settings.REDIS_ENABLED:
        try:
            import redis.asyncio as aioredis
            r = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"degraded: {str(e)[:100]}"
            if overall == "healthy":
                overall = "degraded"
    else:
        checks["redis"] = "disabled"

    return {
        "status": overall,
        "version": settings.PROJECT_VERSION,
        "checks": checks,
    }