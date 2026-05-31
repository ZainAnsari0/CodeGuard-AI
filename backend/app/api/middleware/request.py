"""CodeGuard AI - Request Middleware

Adds request tracing, security headers, and HTTPS enforcement to every response.
"""

import uuid
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings

logger = structlog.get_logger()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adds a unique X-Request-ID to every request for distributed tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Adds X-Process-Time header and logs request timing."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}s"
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=f"{duration:.4f}s",
        )
        return response


class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforces HTTPS in production by checking the X-Forwarded-Proto header.

    In production, requests without X-Forwarded-Proto: https are rejected
    with a 403 response, except for health/ready endpoints needed by
    load balancers.
    """

    EXEMPT_PATHS = {"/health", "/ready"}

    async def dispatch(self, request: Request, call_next):
        # Only enforce in production
        if settings.ENVIRONMENT != "production":
            return await call_next(request)

        # Exempt health/ready paths for load balancers
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Check for HTTPS via reverse proxy header
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if forwarded_proto != "https":
            logger.warning(
                "https_enforcement_blocked",
                path=request.url.path,
                forwarded_proto=forwarded_proto,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "HTTPS_REQUIRED",
                        "message": "HTTPS is required. Please use HTTPS to access this resource.",
                        "details": {},
                    }
                },
            )

        return await call_next(request)