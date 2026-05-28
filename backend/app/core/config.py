"""
CodeGuard AI - Configuration Management
Pydantic-based settings management with environment variable support.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project Information
    PROJECT_NAME: str = "CodeGuard AI"
    PROJECT_DESCRIPTION: str = "AI-powered code analysis and threat detection platform"
    PROJECT_VERSION: str = "1.0.0"

    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = ""  # Must be set via env var; empty string triggers production validation

    # JWT Settings
    JWT_SECRET_KEY: str = ""  # Must be set via env var; empty string triggers production validation
    JWT_ALGORITHM: str = "HS256"  # Use HS256 for local dev; switch to RS256 for production
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None

    # Trusted Hosts
    ALLOWED_HOSTS: List[str] = ["*"]

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "Accept", "X-Requested-With"]

    # Database Settings
    # Default to SQLite for local dev; production must override via env var
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeguard.db"
    DATABASE_STATEMENT_TIMEOUT: int = 30  # seconds; 0 to disable

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # AI/ML Settings
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"  # Override with http://host.docker.internal:11434 in Docker
    DEFAULT_MODEL: str = "llama3:8b"

    # Frontend URL (for password reset links etc.)
    FRONTEND_URL: str = "http://localhost:3000"

    # Environment
    ENVIRONMENT: str = "development"

    # Security Settings
    DEBUG: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Account Lockout Settings
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # File Settings
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".swift"]
    UPLOAD_DIR: str = "/tmp/codeguard_uploads"
    MAX_ZIP_ENTRIES: int = 1000
    MAX_ZIP_DEPTH: int = 3
    MAX_ZIP_RATIO: float = 10.0

    # Scanner Settings
    SCANNER_IMAGE: str = "codeguard-scanner:latest"
    SCANNER_TIMEOUT: int = 600  # 10 minutes
    SCANNER_MEM_LIMIT: str = "1g"
    MAX_CONCURRENT_SCANS: int = 5

    # Prompt Cache Settings
    PROMPT_CACHE_ENABLED: bool = True
    PROMPT_CACHE_TTL: int = 3600  # 1 hour

    # SMTP Settings (for password reset emails)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@codeguard.ai"
    SMTP_FROM_NAME: str = "CodeGuard AI"
    SMTP_USE_TLS: bool = True
    EMAIL_BACKEND: str = "console"  # "console" for dev, "smtp" for production

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: str | List[str]) -> List[str]:
        """Parse allowed hosts from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str):
            return v.strip('"[]').split(",")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str):
            return v.strip('"[]').split(",")
        return v

    @model_validator(mode='after')
    def validate_production_secrets(self):
        """Fail fast if default/placeholder secrets are used in production."""
        if self.ENVIRONMENT == "production":
            insecure_keys = [
                "change-me-in-production", "changeme", "secret", "password",
                "your-secret-key", "your-jwt-secret",
            ]
            if self.SECRET_KEY.lower() in insecure_keys or len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be set to a strong value (32+ chars) in production")
            if self.JWT_ALGORITHM == "HS256" and (self.JWT_SECRET_KEY.lower() in insecure_keys or len(self.JWT_SECRET_KEY) < 32):
                raise ValueError("JWT_SECRET_KEY must be set to a strong value (32+ chars) in production")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS must not contain '*' in production — specify explicit origins")
            if "codeguard_password" in self.DATABASE_URL or "codeguard_redis_pass" in self.REDIS_URL:
                raise ValueError("Default database/redis credentials detected in production — set proper POSTGRES_PASSWORD and REDIS_PASSWORD")
        return self

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


# Create settings instance
settings = Settings()