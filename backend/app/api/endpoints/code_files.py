"""
CodeGuard AI - Code Files API Endpoints
CRUD operations for code file management.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import load_only

from app.db.session import get_session
from app.db.base import ResponseSchema, PaginatedResponse
from app.models.user import User
from app.models.project import Project
from app.models.code_file import CodeFile
from app.api.dependencies import get_current_user
from app.core.exceptions import NotFoundException, ForbiddenException, FileException

router = APIRouter()

ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
                     ".rb", ".php", ".cs", ".swift", ".kt", ".scala", ".sh", ".bash", ".sql", ".html", ".css",
                     ".json", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt", ".cfg", ".ini"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _code_file_dict(cf: CodeFile) -> dict:
    return {
        "id": str(cf.id),
        "project_id": str(cf.project_id) if cf.project_id else None,
        "file_path": cf.file_path,
        "file_name": cf.file_name,
        "file_extension": cf.file_extension,
        "file_size": cf.file_size,
        "language": cf.language,
        "line_count": cf.line_count,
        "last_commit_hash": cf.last_commit_hash,
        "created_at": cf.created_at.isoformat() if cf.created_at else None,
        "updated_at": cf.updated_at.isoformat() if cf.updated_at else None,
    }


async def _check_project_access(project_id: str, current_user: User, db: AsyncSession) -> Project:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException(message="Project not found")
    if project.user_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenException(message="Access denied")
    return project


@router.get("/", response_model=PaginatedResponse)
async def list_code_files(
    project_id: str = Query(..., description="Project ID is required"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """List code files for a project. project_id is required."""
    await _check_project_access(project_id, current_user, db)
    query = select(CodeFile).options(load_only(
        CodeFile.id, CodeFile.project_id, CodeFile.file_path, CodeFile.file_name,
        CodeFile.file_extension, CodeFile.file_size, CodeFile.language,
        CodeFile.line_count, CodeFile.last_commit_hash, CodeFile.created_at, CodeFile.updated_at,
    )).where(CodeFile.project_id == project_id)
    count_query = select(func.count()).select_from(CodeFile).where(CodeFile.project_id == project_id)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(CodeFile.created_at.desc()).offset(skip).limit(limit))
    files = result.scalars().all()

    return PaginatedResponse(
        message="Code files retrieved",
        data=[_code_file_dict(cf) for cf in files],
        pagination={"total": total, "page": skip // limit + 1, "page_size": limit, "total_pages": (total + limit - 1) // limit},
    )


@router.post("/upload", response_model=ResponseSchema)
async def upload_code_file(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Upload a single code file to a project."""
    await _check_project_access(project_id, current_user, db)

    # Stream-read in chunks with size limit
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)  # 1MB chunks
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise FileException(f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)}MB")
        chunks.append(chunk)
    content = b"".join(chunks)
    filename = file.filename or "unnamed"

    # Validate file extension
    ext = f".{filename.rsplit('.', 1)[-1]}" if "." in filename else ""
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise FileException(f"File type '{ext}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    ext = ext.lstrip(".")

    code_file = CodeFile(
        id=str(uuid4()),
        project_id=project_id,
        file_path=filename,
        file_name=filename,
        file_extension=f".{ext}" if ext else "",
        file_size=len(content),
        content=content.decode("utf-8", errors="replace"),
        language=ext or "unknown",
        line_count=content.decode("utf-8", errors="replace").count("\n") + 1,
        file_metadata={"source": "api_upload"},
    )
    db.add(code_file)
    await db.commit()
    await db.refresh(code_file)

    return ResponseSchema(message="File uploaded", data=_code_file_dict(code_file))


@router.get("/{file_id}", response_model=ResponseSchema)
async def get_code_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get a code file by ID (metadata only — content excluded)."""
    stmt = select(CodeFile).options(load_only(
        CodeFile.id, CodeFile.project_id, CodeFile.file_path, CodeFile.file_name,
        CodeFile.file_extension, CodeFile.file_size, CodeFile.language,
        CodeFile.line_count, CodeFile.last_commit_hash, CodeFile.created_at, CodeFile.updated_at,
    )).where(CodeFile.id == file_id)
    result = await db.execute(stmt)
    code_file = result.scalar_one_or_none()

    if not code_file:
        raise NotFoundException(message="Code file not found")
    if code_file.project_id:
        await _check_project_access(code_file.project_id, current_user, db)

    return ResponseSchema(message="Code file retrieved", data=_code_file_dict(code_file))


@router.get("/{file_id}/content", response_model=ResponseSchema)
async def get_code_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Get a code file's full content by ID. Used for on-demand code viewing."""
    stmt = select(CodeFile).where(CodeFile.id == file_id)
    result = await db.execute(stmt)
    code_file = result.scalar_one_or_none()

    if not code_file:
        raise NotFoundException(message="Code file not found")
    if code_file.project_id:
        await _check_project_access(code_file.project_id, current_user, db)

    return ResponseSchema(message="File content retrieved", data={
        "id": str(code_file.id),
        "file_path": code_file.file_path,
        "language": code_file.language,
        "content": code_file.content,
    })


@router.delete("/{file_id}", response_model=ResponseSchema)
async def delete_code_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Delete a code file."""
    stmt = select(CodeFile).where(CodeFile.id == file_id)
    result = await db.execute(stmt)
    code_file = result.scalar_one_or_none()

    if not code_file:
        raise NotFoundException(message="Code file not found")
    if code_file.project_id:
        await _check_project_access(code_file.project_id, current_user, db)

    await db.delete(code_file)
    await db.commit()

    return ResponseSchema(message="Code file deleted", data=None)