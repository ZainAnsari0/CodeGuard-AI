"""
CodeGuard AI - Backend Main Application
FastAPI server with comprehensive middleware and configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import structlog

# Import settings first (needed for logging configuration)
from app.core.config import settings

# Configure structured logging
from app.core.logging import setup_logging
setup_logging(debug=False, log_level_name=settings.LOG_LEVEL)
logger = structlog.get_logger()

# Import database manager and models
from app.infrastructure.database import db_manager
from sqlmodel import SQLModel
from app.api.routes import api_router
from app.core.exceptions import (
    DomainError,
    # Backward-compatible aliases
    AppException,
    NotFoundException,
    ValidationError,
    UnauthorizedException,
    ForbiddenException,
    RateLimitException,
)

# Import all models so SQLModel.metadata picks them up
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.code_file import CodeFile  # noqa: F401
from app.models.analysis import Analysis, Finding, FixSuggestion  # noqa: F401
from app.models.share_token import ShareToken  # noqa: F401

# Create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown events."""
    logger.info("Starting up application...")

    # Validate JWT keys for RS256 mode
    from app.services.auth import validate_jwt_keys_on_startup
    if not validate_jwt_keys_on_startup():
        logger.warning("JWT key validation failed — RS256 may not work correctly")

    # Initialize database and ensure schema is up to date
    await db_manager.init()
    from app.infrastructure.database import engine
    from app.db.migrations import ensure_schema
    await ensure_schema(engine)

    # Run production readiness checks
    from app.core.startup_checks import run_startup_checks
    await run_startup_checks()

    logger.info("Application startup complete")
    yield
    logger.info("Shutting down application...")

    # Close database connections (draining happens automatically)
    await db_manager.close()

    # Close AI provider clients if they have open connections
    try:
        from app.ai.fallback_chain import ai_chain
        for provider in ai_chain.providers:
            if hasattr(provider, 'client') and hasattr(provider.client, 'close'):
                await provider.client.close()
    except Exception as e:
        logger.warning(f"Error closing AI provider clients: {e}")

    # Close Redis token revocation store
    try:
        from app.services.auth import close_revocation_store
        await close_revocation_store()
    except Exception as e:
        logger.warning(f"Error closing revocation store: {e}")

    logger.info("Shutdown complete")


# Initialize FastAPI application
# Disable API docs in production
_is_production = getattr(settings, "ENVIRONMENT", "development") == "production"
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/v1/openapi.json" if not _is_production else None,
    docs_url="/api/v1/docs" if not _is_production else None,
    redoc_url="/api/v1/redoc" if not _is_production else None,
    lifespan=lifespan
)

# Configure trusted hosts
ALLOWED_HOSTS = getattr(settings, "ALLOWED_HOSTS", ["*"])

if _is_production:
    # In production, TrustedHostMiddleware is ALWAYS active
    if "*" in ALLOWED_HOSTS:
        logger.warning(
            "ALLOWED_HOSTS contains '*' in production — "
            "this effectively disables host validation. "
            "Set ALLOWED_HOSTS to your actual domains."
        )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS,
    )
elif ALLOWED_HOSTS != ["*"]:
    # In development, only add middleware if hosts are explicitly configured
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS,
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Process-Time"]
)

# Rate limiting middleware
from app.core.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus metrics — restrict to internal networks in production
from prometheus_fastapi_instrumentator import Instrumentator
_metrics_endpoint = "/metrics" if not _is_production else None
_instrumentator = Instrumentator()
_instrumentator.instrument(app)
if _metrics_endpoint:
    _instrumentator.expose(app, endpoint=_metrics_endpoint)
elif _is_production:
    # In production, only expose via internal network (handled by nginx ACL)
    _instrumentator.expose(app, endpoint="/metrics", should_gzip=False)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses (dev only)."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    if not _is_production:
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    logger.debug(f"{request.method} {request.url.path} - {process_time:.4f}s")
    return response


# ─── New Enterprise Middleware ──────────────────────────────────────────
from app.api.middleware import (
    DomainExceptionMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    HTTPSEnforcementMiddleware,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSEnforcementMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(DomainExceptionMiddleware)


# Exception handlers — standardized error response format
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions with standardized format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": {"path": request.url.path},
            }
        },
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": {"errors": exc.errors},
            }
        },
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Handle unauthorized exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": {},
            }
        },
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """Handle forbidden exceptions."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": {},
            }
        },
    )


@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """Handle rate limit exceptions."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": {"retry_after": exc.retry_after},
            }
        },
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Generic exception handler — sanitize in production to avoid leaking stack traces
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions. Sanitize details in production."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    if _is_production:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred", "details": {}}},
        )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": str(exc), "details": {}}},
    )


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.PROJECT_VERSION,
        "docs": "/api/v1/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )