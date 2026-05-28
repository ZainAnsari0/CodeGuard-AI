"""
CodeGuard AI - Custom Exception Classes
Define custom exceptions for the application.
"""

from fastapi import HTTPException
from typing import Optional, List, Dict, Any


class AppException(HTTPException):
    """Base exception for all custom application exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "APP_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            details=details
        )


class ValidationError(AppException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[List[Dict[str, Any]]] = None,
        error_code: str = "VALIDATION_ERROR"
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details={"errors": errors or []}
        )
        self.errors = errors or []


class UnauthorizedException(AppException):
    """Exception raised for authentication/authorization failures."""

    def __init__(
        self,
        message: str = "Unauthorized",
        error_code: str = "UNAUTHORIZED"
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code
        )


class ForbiddenException(AppException):
    """Exception raised when user lacks required role/permission."""

    def __init__(
        self,
        message: str = "Forbidden",
        error_code: str = "FORBIDDEN"
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code
        )


class RateLimitException(AppException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        error_code: str = "RATE_LIMIT_EXCEEDED"
    ):
        super().__init__(
            message=message,
            status_code=429,
            error_code=error_code,
            details={"retry_after": retry_after}
        )
        self.retry_after = retry_after


class DatabaseException(AppException):
    """Exception raised for database operations."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        error_code: str = "DATABASE_ERROR"
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code=error_code
        )


class AIException(AppException):
    """Exception raised for AI/ML operations."""
    
    def __init__(
        self,
        message: str = "AI service error",
        error_code: str = "AI_ERROR"
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code=error_code
        )


class FileException(AppException):
    """Exception raised for file operations."""
    
    def __init__(
        self,
        message: str = "File operation failed",
        error_code: str = "FILE_ERROR"
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code
        )