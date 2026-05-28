"""
CodeGuard AI - Knowledge Base API Endpoints
Article CRUD and search for security vulnerability education.
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.models.kb_article import KBArticle
from app.schemas.kb import (
    KBArticleCreate, KBArticleUpdate, KBArticleResponse,
    KBArticleSummary, KBSearchResponse,
)
from app.api.dependencies import get_current_user, require_role
from app.schemas.auth import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/articles", response_model=dict)
async def list_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List KB articles with optional category filter and search."""
    query = select(KBArticle).where(KBArticle.is_published == True)
    count_query = select(func.count()).select_from(KBArticle).where(KBArticle.is_published == True)

    if category:
        query = query.where(KBArticle.category == category)
        count_query = count_query.where(KBArticle.category == category)

    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_filter = (
            KBArticle.title.ilike(f"%{escaped}%", escape="\\")
            | KBArticle.content_markdown.ilike(f"%{escaped}%", escape="\\")
            | KBArticle.cwe_ids.ilike(f"%{escaped}%", escape="\\")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(KBArticle.created_at.desc()).offset(offset).limit(per_page)
    )
    articles = result.scalars().all()

    article_list = [
        KBArticleSummary(
            id=a.id, slug=a.slug, title=a.title,
            category=a.category, cwe_ids=a.cwe_ids,
            owasp_category=a.owasp_category,
            is_published=a.is_published, view_count=a.view_count,
            created_at=a.created_at,
        ).model_dump()
        for a in articles
    ]

    return {
        "success": True,
        "data": KBSearchResponse(articles=article_list, total=total).model_dump(),
    }


@router.get("/articles/{slug}", response_model=dict)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single KB article by slug."""
    stmt = select(KBArticle).where(KBArticle.slug == slug, KBArticle.is_published == True)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count atomically to avoid race conditions
    await db.execute(
        KBArticle.__table__.update()
        .where(KBArticle.id == article.id)
        .values(view_count=func.coalesce(KBArticle.view_count, 0) + 1)
    )
    await db.commit()
    await db.refresh(article)

    return {
        "success": True,
        "data": KBArticleResponse(
            id=article.id, slug=article.slug, title=article.title,
            category=article.category, cwe_ids=article.cwe_ids,
            owasp_category=article.owasp_category,
            content_markdown=article.content_markdown,
            vulnerable_example=article.vulnerable_example,
            safe_example=article.safe_example,
            is_published=article.is_published, view_count=article.view_count,
            created_at=article.created_at, updated_at=article.updated_at,
        ).model_dump(),
    }


@router.post("/articles", response_model=dict)
async def create_article(
    data: KBArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Create a new KB article (instructor/admin only)."""
    # Check slug uniqueness
    existing = await db.execute(select(KBArticle).where(KBArticle.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    article = KBArticle(
        id=str(uuid.uuid4()),
        slug=data.slug,
        title=data.title,
        category=data.category,
        cwe_ids=data.cwe_ids,
        owasp_category=data.owasp_category,
        content_markdown=data.content_markdown,
        vulnerable_example=data.vulnerable_example,
        safe_example=data.safe_example,
        is_published=data.is_published,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    return {
        "success": True,
        "message": "Article created",
        "data": KBArticleResponse(
            id=article.id, slug=article.slug, title=article.title,
            category=article.category, cwe_ids=article.cwe_ids,
            owasp_category=article.owasp_category,
            content_markdown=article.content_markdown,
            vulnerable_example=article.vulnerable_example,
            safe_example=article.safe_example,
            is_published=article.is_published, view_count=article.view_count,
            created_at=article.created_at, updated_at=article.updated_at,
        ).model_dump(),
    }


@router.patch("/articles/{slug}", response_model=dict)
async def update_article(
    slug: str,
    data: KBArticleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Update a KB article."""
    # Whitelist allowed update fields to prevent mass assignment
    ALLOWED_UPDATE_FIELDS = {"title", "category", "cwe_ids", "owasp_category",
                             "content_markdown", "vulnerable_example", "safe_example", "is_published"}

    stmt = select(KBArticle).where(KBArticle.slug == slug)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field in ALLOWED_UPDATE_FIELDS and hasattr(article, field):
            setattr(article, field, value)

    await db.commit()
    await db.refresh(article)

    return {
        "success": True,
        "message": "Article updated",
        "data": KBArticleResponse(
            id=article.id, slug=article.slug, title=article.title,
            category=article.category, cwe_ids=article.cwe_ids,
            owasp_category=article.owasp_category,
            content_markdown=article.content_markdown,
            vulnerable_example=article.vulnerable_example,
            safe_example=article.safe_example,
            is_published=article.is_published, view_count=article.view_count,
            created_at=article.created_at, updated_at=article.updated_at,
        ).model_dump(),
    }


@router.delete("/articles/{slug}", response_model=dict)
async def delete_article(
    slug: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Delete a KB article (admin only)."""
    stmt = select(KBArticle).where(KBArticle.slug == slug)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_published = False
    await db.commit()

    return {"success": True, "message": "Article unpublished"}


@router.get("/search", response_model=dict)
async def search_articles(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Search KB articles by title, content, or CWE IDs."""
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    search_filter = (
        KBArticle.title.ilike(f"%{escaped}%", escape="\\")
        | KBArticle.content_markdown.ilike(f"%{escaped}%", escape="\\")
        | KBArticle.cwe_ids.ilike(f"%{escaped}%", escape="\\")
    )
    stmt = select(KBArticle).where(KBArticle.is_published == True, search_filter)
    result = await db.execute(stmt.order_by(KBArticle.created_at.desc()).limit(20))
    articles = result.scalars().all()

    article_list = [
        KBArticleSummary(
            id=a.id, slug=a.slug, title=a.title,
            category=a.category, cwe_ids=a.cwe_ids,
            owasp_category=a.owasp_category,
            is_published=a.is_published, view_count=a.view_count,
            created_at=a.created_at,
        ).model_dump()
        for a in articles
    ]

    return {
        "success": True,
        "data": KBSearchResponse(articles=article_list, total=len(article_list)).model_dump(),
    }


@router.get("/categories", response_model=dict)
async def list_categories(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all KB article categories."""
    stmt = select(KBArticle.category).where(KBArticle.is_published == True).distinct()
    result = await db.execute(stmt)
    categories = [row[0] for row in result.all()]

    return {"success": True, "data": categories}