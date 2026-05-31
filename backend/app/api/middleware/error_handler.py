"""CodeGuard AI - Error Handler Middleware

Maps domain exceptions to consistent HTTP responses.
This is the single place where domain errors become HTTP errors.

Response envelope:
  { "success": false, "error": { "code": "...", "message": "...", "details": {} } }
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import DomainError

logger = logging.getLogger(__name__)

# Map domain exception codes to HTTP status codes
EXCEPTION_STATUS_MAP = {
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 400,
    "AUTH_FAILED": 401,
    "ACCESS_DENIED": 403,
    "ACCOUNT_LOCKED": 423,
    "RATE_LIMIT_EXCEEDED": 429,
    "DUPLICATE": 409,
    "BUSINESS_RULE_VIOLATION": 422,
    "FILE_REJECTED": 400,
    "AI_ERROR": 502,
    "EXTERNAL_SERVICE_ERROR": 502,
    "DOMAIN_ERROR": 500,
}


class DomainExceptionMiddleware(BaseHTTPMiddleware):
    """Catches DomainError exceptions and converts them to JSON responses.

    This middleware should be added AFTER CORS and BEFORE route handlers.
    It ensures that all error responses follow the same envelope format.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except DomainError as exc:
            status_code = EXCEPTION_STATUS_MAP.get(exc.code, 500)

            # Log at appropriate level
            if status_code >= 500:
                logger.error(f"Domain error [{exc.code}]: {exc.message}", exc_info=True)
            elif status_code >= 400:
                logger.info(f"Domain error [{exc.code}]: {exc.message}")

            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                },
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {},
                    },
                },
            )