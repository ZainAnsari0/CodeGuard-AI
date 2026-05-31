"""CodeGuard AI - Repositories

Data access layer following the Repository pattern.
Each repository encapsulates all database queries for its domain.
"""

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
]