"""CodeGuard AI - Domain Exception Hierarchy

Domain exceptions are decoupled from HTTP status codes.
The exception-to-HTTP mapping lives in app/api/middleware/error_handler.py.

Architecture principle:
  - Domain layer raises domain exceptions (e.g., EntityNotFound, BusinessRuleViolation)
  - API layer catches and maps to HTTP responses
  - Domain exceptions have NO knowledge of HTTP
"""

from typing import Optional, List, Dict, Any


# ─── Base ────────────────────────────────────────────────────────

class DomainError(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self,
        message: str = "An error occurred",
        code: str = "DOMAIN_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


# ─── Not Found ───────────────────────────────────────────────────

class EntityNotFound(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity: str = "Resource", entity_id: str = "", code: str = "NOT_FOUND"):
        message = f"{entity} not found" if not entity_id else f"{entity} with id '{entity_id}' not found"
        super().__init__(message=message, code=code)
        self.entity = entity
        self.entity_id = entity_id


# ─── Validation ─────────────────────────────────────────────────

class ValidationFailed(DomainError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[List[Dict[str, Any]]] = None,
        code: str = "VALIDATION_ERROR",
    ):
        super().__init__(message=message, code=code, details={"errors": errors or []})
        self.errors = errors or []


# ─── Authentication & Authorization ─────────────────────────────

class AuthenticationFailed(DomainError):
    """Raised when authentication credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials", code: str = "AUTH_FAILED"):
        super().__init__(message=message, code=code)


class AccessDenied(DomainError):
    """Raised when a user lacks the required role or permission."""

    def __init__(
        self,
        message: str = "Access denied",
        required_role: str = "",
        code: str = "ACCESS_DENIED",
    ):
        super().__init__(message=message, code=code)
        self.required_role = required_role


class AccountLocked(DomainError):
    """Raised when an account is locked due to too many failed attempts."""

    def __init__(
        self,
        message: str = "Account is temporarily locked",
        retry_after_minutes: int = 15,
        code: str = "ACCOUNT_LOCKED",
    ):
        super().__init__(message=message, code=code, details={"retry_after_minutes": retry_after_minutes})
        self.retry_after_minutes = retry_after_minutes


# ─── Rate Limiting ───────────────────────────────────────────────

class RateLimitExceeded(DomainError):
    """Raised when a rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        code: str = "RATE_LIMIT_EXCEEDED",
    ):
        super().__init__(message=message, code=code, details={"retry_after": retry_after})
        self.retry_after = retry_after


# ─── Business Logic ─────────────────────────────────────────────

class BusinessRuleViolation(DomainError):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(message=message, code=code)


class DuplicateEntity(DomainError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity: str = "Resource", field: str = "", code: str = "DUPLICATE"):
        message = f"{entity} already exists" if not field else f"{entity} with this {field} already exists"
        super().__init__(message=message, code=code)
        self.entity = entity
        self.field = field


# ─── External Services ───────────────────────────────────────────

class ExternalServiceError(DomainError):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service: str = "",
        message: str = "External service error",
        code: str = "EXTERNAL_SERVICE_ERROR",
    ):
        message = f"{service} error: {message}" if service else message
        super().__init__(message=message, code=code)


class AIServiceError(ExternalServiceError):
    """Raised when the AI/LLM service fails."""

    def __init__(self, message: str = "AI service error", code: str = "AI_ERROR"):
        super().__init__(service="AI", message=message, code=code)


# ─── File / Upload ───────────────────────────────────────────────

class FileRejected(DomainError):
    """Raised when an uploaded file fails validation."""

    def __init__(
        self,
        message: str = "File validation failed",
        errors: Optional[List[str]] = None,
        code: str = "FILE_REJECTED",
    ):
        super().__init__(message=message, code=code, details={"errors": errors or []})
        self.errors = errors or []


# ─── Backward-Compatible Aliases ─────────────────────────────────
# These map the old names to the new hierarchy so existing code
# continues to work during the migration period.

AppException = DomainError  # Will be deprecated
NotFoundException = EntityNotFound
ValidationError = ValidationFailed
UnauthorizedException = AuthenticationFailed
ForbiddenException = AccessDenied
RateLimitException = RateLimitExceeded
DatabaseException = ExternalServiceError
AIException = AIServiceError
FileException = FileRejected