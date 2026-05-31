"""CodeGuard AI - Domain Services

Service layer following the Service pattern. Each domain service
encapsulates business logic and orchestrates repository calls.
Dependencies are injected via constructor (db session).

Usage in endpoints:
    async def my_endpoint(db: AsyncSession = Depends(get_session)):
        service = ProjectService(db)
        project = await service.create_project(current_user, data)
"""

from app.services.domain.auth_service import AuthService
from app.services.domain.project_service import ProjectService

__all__ = [
    "AuthService",
    "ProjectService",
]