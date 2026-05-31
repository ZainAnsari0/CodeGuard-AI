"""CodeGuard AI - Configuration Module

Exports the composed Settings class for backward compatibility.
Domain-specific settings are available from their submodules.
"""

from app.core.config.base import (
    Settings,
    BaseAppSettings,
    DatabaseSettings,
    SecuritySettings,
    AISettings,
    ScannerSettings,
    EmailSettings,
    RedisSettings,
    settings,
)

__all__ = [
    "Settings",
    "BaseAppSettings",
    "DatabaseSettings",
    "SecuritySettings",
    "AISettings",
    "ScannerSettings",
    "EmailSettings",
    "RedisSettings",
    "settings",
]