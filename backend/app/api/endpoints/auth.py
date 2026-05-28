"""
CodeGuard AI - Authentication API Endpoints
User registration, login, token management, and password reset.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from app.core.config import settings
from app.core.exceptions import ValidationError, UnauthorizedException
from app.db.session import get_session
from app.db.base import ResponseSchema
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.auth import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    validate_token,
    is_account_locked,
    get_lockout_remaining_minutes,
    handle_failed_login,
    handle_successful_login,
    generate_password_reset_token,
    revoke_refresh_token,
    revoke_access_token,
    _revoke_token_hash,
)
from app.core.rate_limit import limiter

router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set httpOnly secure cookies for auth tokens."""
    secure = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=ResponseSchema)
@limiter.limit("5/minute")
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_session)
) -> Any:
    """Register a new user."""
    existing_result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_result.scalar_one_or_none():
        raise ValidationError(
            message="User with this email already exists",
            errors=[{"field": "email", "message": "Email already in use"}]
        )

    # Prevent self-assignment of admin/instructor roles during registration
    # Only admins can promote users via the admin endpoints
    role = user_data.role
    if role in ("admin", "instructor"):
        role = "developer"

    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=role,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id, extra_claims={"role": user.role})
    refresh_token = create_refresh_token(user.id)

    set_auth_cookies(response, access_token, refresh_token)

    return ResponseSchema(
        message="User registered successfully",
        data={
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "role": user.role,
            },
        }
    )


@router.post("/login", response_model=ResponseSchema)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
) -> Any:
    """Login and get access tokens."""
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Check account lockout
    if user and is_account_locked(user):
        remaining = get_lockout_remaining_minutes(user)
        raise UnauthorizedException(
            message=f"Account is temporarily locked. Try again in {remaining} minutes."
        )

    if not user or not verify_password(form_data.password, user.hashed_password):
        if user:
            lockout_info = handle_failed_login(user)
            await db.commit()

            if lockout_info["locked"]:
                raise UnauthorizedException(
                    message=f"Account locked due to too many failed attempts. Try again in {settings.LOCKOUT_DURATION_MINUTES} minutes."
                )

        raise UnauthorizedException(message="Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException(message="User account is deactivated")

    # Reset failed attempts on successful login
    handle_successful_login(user)
    access_token = create_access_token(user.id, extra_claims={"role": user.role})
    refresh_token = create_refresh_token(user.id)

    set_auth_cookies(response, access_token, refresh_token)

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return ResponseSchema(
        message="Login successful",
        data={
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "role": user.role,
            }
        }
    )


@router.post("/refresh", response_model=ResponseSchema)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_session)
) -> Any:
    """Refresh access token using refresh token from cookie or request body."""
    # Try cookie first, then request body
    rt = request.cookies.get("refresh_token")
    if not rt:
        # Fall back to JSON body for backward compatibility
        try:
            body = await request.json()
            rt = body.get("refresh_token")
        except Exception:
            pass

    if not rt:
        raise UnauthorizedException(message="Refresh token required")

    # Check if refresh token has been revoked
    from app.services.auth import is_refresh_token_revoked
    if await is_refresh_token_revoked(rt):
        raise UnauthorizedException(message="Refresh token has been revoked")

    payload = decode_access_token(rt)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException(message="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(message="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException(message="User not found or inactive")

    new_access_token = create_access_token(user.id, extra_claims={"role": user.role})
    new_refresh_token = create_refresh_token(user.id)

    # Revoke the old refresh token to prevent replay
    await revoke_refresh_token(rt)

    set_auth_cookies(response, new_access_token, new_refresh_token)

    return ResponseSchema(
        message="Token refreshed successfully",
        data=None
    )


@router.get("/me", response_model=ResponseSchema)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user profile."""
    return ResponseSchema(
        message="User profile retrieved successfully",
        data={"user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "role": current_user.role,
        }}
    )


@router.patch("/me", response_model=ResponseSchema)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> Any:
    """Update current user profile."""
    # Whitelist allowed fields to prevent privilege escalation
    # Note: email changes require verification, so only allow name/password here
    ALLOWED_PROFILE_FIELDS = {"full_name", "password"}
    update_data = {
        k: v for k, v in user_data.model_dump(exclude_unset=True).items()
        if k in ALLOWED_PROFILE_FIELDS
    }

    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return ResponseSchema(
        message="Profile updated successfully",
        data={"user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "role": current_user.role,
        }}
    )


@router.post("/logout", response_model=ResponseSchema)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Logout current user and clear auth cookies."""
    # Revoke the refresh token if available
    rt = request.cookies.get("refresh_token")
    if rt:
        await revoke_refresh_token(rt)

    # Revoke the access token if available
    at = request.cookies.get("access_token")
    if at:
        await revoke_access_token(at)

    # Clear httpOnly cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    return ResponseSchema(
        message="Logged out successfully",
        data=None
    )


@router.post("/forgot-password", response_model=ResponseSchema)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    forgot_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_session)
) -> Any:
    """Request a password reset email."""
    result = await db.execute(
        select(User).where(User.email == forgot_request.email)
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return ResponseSchema(
            message="If an account with that email exists, a reset link has been sent.",
            data=None
        )

    # Generate reset token and store only its hash
    reset_token = generate_password_reset_token()
    user.password_reset_token = _revoke_token_hash(reset_token)
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()

    # Send email (console backend for dev, SMTP for production)
    try:
        from app.services.email_service import email_service
        await email_service.send_password_reset_email(
            to_email=user.email,
            to_name=user.full_name or user.email,
            reset_token=reset_token,
        )
    except Exception as e:
        # Log error but don't expose to user
        import logging
        logging.getLogger(__name__).error("Failed to send password reset email: %s", e)

    return ResponseSchema(
        message="If an account with that email exists, a reset link has been sent.",
        data=None
    )


@router.post("/reset-password", response_model=ResponseSchema)
@limiter.limit("3/minute")
async def reset_password(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_session)
) -> Any:
    """Reset password using a valid reset token."""
    # Hash the submitted token to compare against stored hash
    token_hash = _revoke_token_hash(reset_data.token)
    result = await db.execute(
        select(User).where(User.password_reset_token == token_hash)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValidationError(
            message="Invalid or expired reset token",
            errors=[{"field": "token", "message": "Invalid reset token"}]
        )

    if user.password_reset_expires and user.password_reset_expires < datetime.now(timezone.utc):
        # Clear expired token
        user.password_reset_token = None
        user.password_reset_expires = None
        await db.commit()
        raise ValidationError(
            message="Reset token has expired. Please request a new one.",
            errors=[{"field": "token", "message": "Token expired"}]
        )

    # Update password and clear reset token
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()

    return ResponseSchema(
        message="Password has been reset successfully.",
        data=None
    )