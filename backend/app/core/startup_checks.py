"""CodeGuard AI - Production Readiness Startup Checks

Validates that all required configuration is in place before the application
starts serving requests. Called from the lifespan handler in main.py.
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)


async def run_startup_checks() -> bool:
    """Run all startup validation checks and log findings.

    Returns True if all checks pass (warnings are acceptable).
    Raises RuntimeError if critical checks fail in production.
    """
    from app.core.config import settings

    checks = _collect_checks(settings)
    _log_findings(checks)

    critical_failures = [c for c in checks if c["level"] == "critical" and not c["passed"]]
    if critical_failures and settings.ENVIRONMENT == "production":
        failures = ", ".join(c["name"] for c in critical_failures)
        raise RuntimeError(f"Critical startup checks failed: {failures}")

    return len(critical_failures) == 0


def _collect_checks(settings) -> List[dict]:
    """Gather results of all startup checks."""
    checks = []
    is_prod = settings.ENVIRONMENT == "production"

    # ── Required environment variables ─────────────────────────────
    required_vars = {
        "SECRET_KEY": settings.SECRET_KEY,
        "JWT_SECRET_KEY": settings.JWT_SECRET_KEY,
    }

    for var_name, var_value in required_vars.items():
        checks.append({
            "name": f"env:{var_name}",
            "level": "critical" if is_prod else "warning",
            "passed": bool(var_value) and var_value.lower() not in {
                "change-me-in-production", "changeme", "secret", "password",
                "your-secret-key", "your-jwt-secret",
            },
            "message": f"{var_name} is {'set' if var_value else 'empty'}",
        })

    # ── DATABASE_URL must not be sqlite in production ──────────────
    checks.append({
        "name": "database:not-sqlite",
        "level": "critical" if is_prod else "warning",
        "passed": not settings.DATABASE_URL.startswith("sqlite"),
        "message": f"Database driver: {settings.DATABASE_URL.split('://')[0].split('+')[0]}",
    })

    # ── Redis reachability check (when enabled) ────────────────────
    if settings.REDIS_ENABLED:
        redis_ok = _check_redis_reachable(settings)
        checks.append({
            "name": "redis:reachable",
            "level": "critical" if is_prod else "warning",
            "passed": redis_ok,
            "message": f"Redis at {settings.REDIS_URL} is {'reachable' if redis_ok else 'unreachable'}",
        })

    # ── JWT keys exist when RS256 is configured ─────────────────────
    if settings.JWT_ALGORITHM == "RS256":
        private_exists = bool(settings.JWT_PRIVATE_KEY_PATH) and os.path.exists(settings.JWT_PRIVATE_KEY_PATH)
        public_exists = bool(settings.JWT_PUBLIC_KEY_PATH) and os.path.exists(settings.JWT_PUBLIC_KEY_PATH)
        checks.append({
            "name": "jwt:private-key",
            "level": "critical",
            "passed": private_exists,
            "message": f"JWT private key at {settings.JWT_PRIVATE_KEY_PATH}: {'found' if private_exists else 'missing'}",
        })
        checks.append({
            "name": "jwt:public-key",
            "level": "critical",
            "passed": public_exists,
            "message": f"JWT public key at {settings.JWT_PUBLIC_KEY_PATH}: {'found' if public_exists else 'missing'}",
        })

    return checks


def _check_redis_reachable(settings) -> bool:
    """Try to connect to Redis and return whether it's reachable."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        r.ping()
        r.close()
        return True
    except Exception as e:
        logger.warning(f"Redis reachability check failed: {e}")
        return False


def _log_findings(checks: List[dict]) -> None:
    """Log all check findings at the appropriate level."""
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        level = check["level"]
        name = check["name"]
        message = check["message"]

        if check["passed"]:
            logger.info(f"Startup check [{status}] {name}: {message}")
        elif level == "critical":
            logger.error(f"Startup check [{status}] {name}: {message}")
        else:
            logger.warning(f"Startup check [{status}] {name}: {message}")