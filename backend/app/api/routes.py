"""
CodeGuard AI - API Routes Router
Main router for all API endpoints.
"""

from fastapi import APIRouter

from app.api.endpoints import auth, users, projects, code_files, analysis, ai, scanner, instructor, admin, kb, share, guest, rescan, health

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(code_files.router, prefix="/code-files", tags=["code-files"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(scanner.router, prefix="/scanner", tags=["scanner"])
api_router.include_router(instructor.router, prefix="/instructor", tags=["instructor"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(kb.router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(share.router, prefix="/share", tags=["sharing"])
api_router.include_router(guest.router, prefix="/guest", tags=["guest"])
api_router.include_router(rescan.router, prefix="/scanner", tags=["scanner"])