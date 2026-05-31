"""CodeGuard AI - Base Application Settings

Shared configuration settings used across all environments.
Domain-specific settings are in separate modules:
  - security.py: Auth, CORS, rate limiting
  - ai.py: AI/LLM provider settings
  - scanner.py: Scanner and container settings
  - email.py: SMTP and notification settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator


class BaseAppSettings(BaseSettings):
    """Base settings shared across all environments."""

    PROJECT_NAME: str = "CodeGuard AI"
    PROJECT_DESCRIPTION: str = "AI-powered code analysis and threat detection platform"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"
    UPLOAD_DIR: str = "/tmp/codeguard_uploads"

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}")
        return v.upper()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeguard.db"
    DATABASE_STATEMENT_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class SecuritySettings(BaseSettings):
    """Security-related configuration."""
    SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "Accept", "X-Requested-With"]
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str):
            return v.strip('"[]').split(",")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str):
            return v.strip('"[]').split(",")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class AISettings(BaseSettings):
    """AI/ML provider configuration."""
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "llama3:8b"
    PROMPT_CACHE_ENABLED: bool = True
    PROMPT_CACHE_TTL: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class ScannerSettings(BaseSettings):
    """Scanner and container configuration."""
    SCANNER_IMAGE: str = "codeguard-scanner:latest"
    SCANNER_TIMEOUT: int = 600
    SCANNER_MEM_LIMIT: str = "1g"
    MAX_CONCURRENT_SCANS: int = 5
    MAX_FILE_SIZE: int = 10485760
    ALLOWED_EXTENSIONS: List[str] = [".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".swift"]
    MAX_ZIP_ENTRIES: int = 1000
    MAX_ZIP_DEPTH: int = 3
    MAX_ZIP_RATIO: float = 10.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class EmailSettings(BaseSettings):
    """SMTP and notification configuration."""
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@codeguard.ai"
    SMTP_FROM_NAME: str = "CodeGuard AI"
    SMTP_USE_TLS: bool = True
    EMAIL_BACKEND: str = "console"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class Settings(
    BaseAppSettings,
    DatabaseSettings,
    SecuritySettings,
    AISettings,
    ScannerSettings,
    EmailSettings,
    RedisSettings,
):
    """Composed application settings from all domain configs."""

    @model_validator(mode="after")
    def validate_production_secrets(self):
        """Fail fast if default/placeholder secrets are used in production."""
        if self.ENVIRONMENT == "production":
            insecure_keys = [
                "change-me-in-production", "changeme", "secret", "password",
                "your-secret-key", "your-jwt-secret",
            ]
            if not self.SECRET_KEY or self.SECRET_KEY.lower() in insecure_keys:
                raise ValueError("SECRET_KEY must be set to a secure value in production")
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY.lower() in insecure_keys:
                raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("SQLite must not be used in production — set DATABASE_URL to PostgreSQL")
            if self.EMAIL_BACKEND == "console":
                import warnings
                warnings.warn("EMAIL_BACKEND=console in production — emails will only be logged")
        return self


# Backward-compatible singleton
settings = Settings()