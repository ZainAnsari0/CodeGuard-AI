"""
CodeGuard AI - Instructor API Endpoints
Class CRUD, enrollment management, and metrics aggregation.
"""

import uuid
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.models.class_ import Class_, Enrollment
from app.models.analysis import Analysis, Finding
from app.schemas.instructor import (
    ClassCreate, ClassUpdate, ClassResponse,
    EnrollmentCreate, EnrollmentResponse,
    ClassMetricsResponse,
    JoinByCodeRequest, EnrolledClassResponse,
)
from app.api.dependencies import get_current_user, require_role
from app.schemas.auth import UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Class CRUD ---

@router.post("/classes", response_model=dict)
async def create_class(
    data: ClassCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Create a new class (instructor only)."""
    new_class = Class_(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        instructor_id=current_user.id,
    )
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)

    return {
        "success": True,
        "message": "Class created",
        "data": ClassResponse(
            id=new_class.id,
            name=new_class.name,
            description=new_class.description,
            instructor_id=new_class.instructor_id,
            join_code=new_class.join_code,
            is_active=new_class.is_active,
            created_at=new_class.created_at,
            updated_at=new_class.updated_at,
            student_count=0,
        ).model_dump(),
    }


@router.get("/classes", response_model=dict)
async def list_classes(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """List classes for the current instructor."""
    # Single query with subquery for student count — avoids N+1
    student_count_sq = (
        select(func.count().label("student_count"))
        .where(Enrollment.class_id == Class_.id, Enrollment.status == "active")
        .correlate(Class_)
        .scalar_subquery()
    )
    stmt = (
        select(Class_, student_count_sq.label("student_count"))
        .where(Class_.instructor_id == current_user.id, Class_.is_active == True)
    )
    result = await db.execute(stmt)
    rows = result.all()

    class_list = [
        ClassResponse(
            id=c.id, name=c.name, description=c.description,
            instructor_id=c.instructor_id, join_code=c.join_code,
            is_active=c.is_active, created_at=c.created_at,
            updated_at=c.updated_at, student_count=count or 0,
        ).model_dump()
        for c, count in rows
    ]

    return {"success": True, "data": class_list}


# --- Developer-facing class endpoints ---
# Must be defined BEFORE /classes/{class_id} routes
# to avoid path parameter conflicts with "join" and "mine".

@router.post("/classes/join", response_model=dict)
async def join_class_by_code(
    data: JoinByCodeRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Join a class using a join code (available to all authenticated users)."""
    # Look up the class by join code
    stmt = select(Class_).where(Class_.join_code == data.join_code, Class_.is_active == True)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Invalid join code. No active class found.")

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.class_id == cls.id,
            Enrollment.student_id == current_user.id,
        )
    )
    existing_enrollment = existing.scalar_one_or_none()
    if existing_enrollment:
        if existing_enrollment.status == "active":
            raise HTTPException(status_code=400, detail="You are already enrolled in this class.")
        # Re-activate dropped enrollment
        existing_enrollment.status = "active"
        await db.commit()
        await db.refresh(existing_enrollment)
        return {
            "success": True,
            "message": "Re-enrolled successfully",
            "data": {
                "class_id": cls.id,
                "class_name": cls.name,
                "status": "active",
                "enrolled_at": existing_enrollment.enrolled_at.isoformat() if existing_enrollment.enrolled_at else None,
            },
        }

    # Create new enrollment
    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        class_id=cls.id,
        student_id=current_user.id,
        status="active",
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return {
        "success": True,
        "message": "Joined class successfully",
        "data": {
            "class_id": cls.id,
            "class_name": cls.name,
            "status": "active",
            "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
        },
    }


@router.get("/classes/mine", response_model=dict)
async def list_my_classes(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List classes the current developer has joined."""
    # Subquery for student count per class
    student_count_sq = (
        select(func.count().label("student_count"))
        .where(Enrollment.class_id == Class_.id, Enrollment.status == "active")
        .correlate(Class_)
        .scalar_subquery()
    )

    # Query enrolled classes with class details and instructor info
    stmt = (
        select(Class_, Enrollment, User, student_count_sq.label("student_count"))
        .join(Enrollment, Enrollment.class_id == Class_.id)
        .join(User, Class_.instructor_id == User.id)
        .where(
            Enrollment.student_id == current_user.id,
            Enrollment.status == "active",
            Class_.is_active == True,
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    enrolled_classes = [
        EnrolledClassResponse(
            id=cls.id,
            name=cls.name,
            description=cls.description,
            join_code=cls.join_code,
            is_active=cls.is_active,
            instructor_name=instructor.full_name,
            instructor_email=instructor.email,
            enrolled_at=enrollment.enrolled_at,
            student_count=count or 0,
        ).model_dump()
        for cls, enrollment, instructor, count in rows
    ]

    return {"success": True, "data": enrolled_classes}


@router.delete("/classes/{class_id}/leave", response_model=dict)
async def leave_class(
    class_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Leave a class (developer self-service)."""
    stmt = select(Enrollment).where(
        Enrollment.class_id == class_id,
        Enrollment.student_id == current_user.id,
        Enrollment.status == "active",
    )
    result = await db.execute(stmt)
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="You are not enrolled in this class.")

    enrollment.status = "dropped"
    await db.commit()

    return {"success": True, "message": "Left class successfully"}


# --- Instructor-specific enrollment ---

@router.get("/classes/{class_id}", response_model=dict)
async def get_class(
    class_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Get a specific class by ID."""
    stmt = select(Class_).where(Class_.id == class_id)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not your class")

    count_stmt = select(func.count()).select_from(Enrollment).where(
        Enrollment.class_id == cls.id, Enrollment.status == "active"
    )
    count_result = await db.execute(count_stmt)
    student_count = count_result.scalar() or 0

    return {
        "success": True,
        "data": ClassResponse(
            id=cls.id, name=cls.name, description=cls.description,
            instructor_id=cls.instructor_id, join_code=cls.join_code,
            is_active=cls.is_active, created_at=cls.created_at,
            updated_at=cls.updated_at, student_count=student_count,
        ).model_dump(),
    }


@router.patch("/classes/{class_id}", response_model=dict)
async def update_class(
    class_id: str,
    data: ClassUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Update a class."""
    stmt = select(Class_).where(Class_.id == class_id)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not your class")

    if data.name is not None:
        cls.name = data.name
    if data.description is not None:
        cls.description = data.description
    if data.is_active is not None:
        cls.is_active = data.is_active

    await db.commit()
    await db.refresh(cls)

    return {
        "success": True,
        "message": "Class updated",
        "data": {"id": cls.id, "name": cls.name, "description": cls.description,
                 "is_active": cls.is_active, "join_code": cls.join_code},
    }


@router.delete("/classes/{class_id}", response_model=dict)
async def delete_class(
    class_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Deactivate a class (soft delete)."""
    stmt = select(Class_).where(Class_.id == class_id)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not your class")

    cls.is_active = False
    await db.commit()

    return {"success": True, "message": "Class deactivated"}


# --- Enrollment ----

@router.post("/classes/{class_id}/enroll", response_model=dict)
async def enroll_in_class(
    class_id: str,
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Enroll the current user in a class using a join code."""
    stmt = select(Class_).where(Class_.id == class_id, Class_.is_active == True)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls.join_code != data.join_code:
        raise HTTPException(status_code=400, detail="Invalid join code")

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already enrolled")

    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        class_id=class_id,
        student_id=current_user.id,
        status="active",
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return {
        "success": True,
        "message": "Enrolled successfully",
        "data": EnrollmentResponse(
            id=enrollment.id, class_id=enrollment.class_id,
            student_id=enrollment.student_id, status=enrollment.status,
            enrolled_at=enrollment.enrolled_at,
            student_name=current_user.full_name, student_email=current_user.email,
        ).model_dump(),
    }


@router.get("/classes/{class_id}/students", response_model=dict)
async def list_class_students(
    class_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """List students enrolled in a class."""
    stmt = select(Class_).where(Class_.id == class_id)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not your class")

    enrollments = await db.execute(
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.id)
        .where(Enrollment.class_id == class_id, Enrollment.status == "active")
    )
    rows = enrollments.all()

    students = []
    for enrollment, user in rows:
        students.append(EnrollmentResponse(
            id=enrollment.id, class_id=enrollment.class_id,
            student_id=enrollment.student_id, status=enrollment.status,
            enrolled_at=enrollment.enrolled_at,
            student_name=user.full_name, student_email=user.email,
        ).model_dump())

    return {"success": True, "data": students}


@router.delete("/classes/{class_id}/students/{student_id}", response_model=dict)
async def remove_student(
    class_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Remove a student from a class."""
    # Verify the instructor owns this class
    class_stmt = select(Class_).where(Class_.id == class_id)
    class_result = await db.execute(class_stmt)
    class_obj = class_result.scalar_one_or_none()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    if class_obj.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to manage this class")

    stmt = select(Enrollment).where(
        Enrollment.class_id == class_id, Enrollment.student_id == student_id,
        Enrollment.status == "active"
    )
    result = await db.execute(stmt)
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    enrollment.status = "dropped"
    await db.commit()

    return {"success": True, "message": "Student removed from class"}


# --- Metrics ---

@router.get("/classes/{class_id}/metrics", response_model=dict)
async def get_class_metrics(
    class_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
):
    """Get aggregated metrics for a class."""
    stmt = select(Class_).where(Class_.id == class_id)
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not your class")

    # Get student IDs in the class
    student_ids_subq = (
        select(Enrollment.student_id)
        .where(Enrollment.class_id == class_id, Enrollment.status == "active")
    )

    # Get analyses from enrolled students (limited to most recent 500)
    analyses_stmt = (
        select(Analysis)
        .where(Analysis.user_id.in_(student_ids_subq))
        .order_by(Analysis.created_at.desc())
        .limit(500)
    )
    analyses_result = await db.execute(analyses_stmt)
    analyses = analyses_result.scalars().all()

    total_scans = len(analyses)

    # Get findings for those analyses
    scan_ids = [a.id for a in analyses] if analyses else []
    findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    findings_by_type: dict = {}
    total_findings = 0

    if scan_ids:
        # Fetch severity counts using DB aggregation
        severity_stmt = (
            select(Finding.severity, func.count(Finding.id).label("count"))
            .where(Finding.analysis_id.in_(scan_ids))
            .group_by(Finding.severity)
        )
        severity_result = await db.execute(severity_stmt)
        for row in severity_result:
            sev = row.severity.value if hasattr(row.severity, "value") else str(row.severity)
            findings_by_severity[sev] = findings_by_severity.get(sev, 0) + row.count
            total_findings += row.count

        # Fetch vulnerability type counts using DB aggregation
        type_stmt = (
            select(Finding.vulnerability_type, func.count(Finding.id).label("count"))
            .where(Finding.analysis_id.in_(scan_ids))
            .group_by(Finding.vulnerability_type)
        )
        type_result = await db.execute(type_stmt)
        for row in type_result:
            findings_by_type[row.vulnerability_type] = findings_by_type.get(row.vulnerability_type, 0) + row.count

    # Count enrolled students
    count_stmt = select(func.count()).select_from(Enrollment).where(
        Enrollment.class_id == class_id, Enrollment.status == "active"
    )
    count_result = await db.execute(count_stmt)
    total_students = count_result.scalar() or 1

    # Top vulnerability types
    top_types = sorted(findings_by_type.items(), key=lambda x: x[1], reverse=True)[:5]
    top_vuln_types = [{"type": t, "count": c} for t, c in top_types]

    return {
        "success": True,
        "data": ClassMetricsResponse(
            class_id=cls.id, class_name=cls.name,
            total_students=total_students, total_scans=total_scans,
            total_findings=total_findings,
            findings_by_severity=findings_by_severity,
            findings_by_type=findings_by_type,
            avg_findings_per_student=round(total_findings / max(total_students, 1), 1),
            top_vulnerability_types=top_vuln_types,
        ).model_dump(),
    }