"""
CodeGuard AI - Authentication Service
JWT token management, password hashing, token validation, and account lockout.
Supports HS256 (local dev) and RS256 (production).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid
import os
import logging
import secrets
import hashlib

from jose import jwt, JWTError
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


# ── Token Revocation Store ──────────────────────────────────────
# Redis-backed with in-memory fallback for single-worker dev mode.
# Uses TTL-based expiry so revoked tokens auto-expire without cleanup.

_revoked_tokens: Dict[str, float] = {}  # token_hash -> expiry timestamp (fallback)
_redis_client = None


def _revoke_token_hash(token: str) -> str:
    """Hash token before storing to avoid exposing raw tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


async def _get_redis():
    """Lazy-initialize async Redis client for token revocation."""
    global _redis_client
    if _redis_client is None and settings.REDIS_ENABLED:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.warning("Token revocation: Redis unavailable, using in-memory fallback: %s", e)
            _redis_client = None
    return _redis_client


async def revoke_refresh_token(token: str) -> None:
    """Mark a refresh token as revoked."""
    token_hash = _revoke_token_hash(token)
    ttl_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
    r = await _get_redis()
    if r:
        try:
            await r.setex(f"revoked:{token_hash}", ttl_seconds, "1")
            return
        except Exception as e:
            logger.warning("Redis revocation failed, using in-memory fallback: %s", e)
    # In-memory fallback
    _revoked_tokens[token_hash] = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).timestamp()


async def is_refresh_token_revoked(token: str) -> bool:
    """Check if a refresh token has been revoked."""
    token_hash = _revoke_token_hash(token)
    r = await _get_redis()
    if r:
        try:
            return bool(await r.exists(f"revoked:{token_hash}"))
        except Exception:
            pass  # Fall through to in-memory check
    # In-memory fallback
    expiry = _revoked_tokens.get(token_hash)
    if expiry is None:
        return False
    if expiry <= datetime.now(timezone.utc).timestamp():
        del _revoked_tokens[token_hash]
        return False
    return True


async def revoke_access_token(token: str) -> None:
    """Mark an access token as revoked (used on logout)."""
    token_hash = _revoke_token_hash(token)
    ttl_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    r = await _get_redis()
    if r:
        try:
            await r.setex(f"revoked:{token_hash}", ttl_seconds, "1")
            return
        except Exception as e:
            logger.warning("Redis revocation failed, using in-memory fallback: %s", e)
    # In-memory fallback
    _revoked_tokens[token_hash] = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).timestamp()


async def is_access_token_revoked(token: str) -> bool:
    """Check if an access token has been revoked."""
    token_hash = _revoke_token_hash(token)
    r = await _get_redis()
    if r:
        try:
            return bool(await r.exists(f"revoked:{token_hash}"))
        except Exception:
            pass  # Fall through to in-memory check
    # In-memory fallback
    expiry = _revoked_tokens.get(token_hash)
    if expiry is None:
        return False
    if expiry <= datetime.now(timezone.utc).timestamp():
        del _revoked_tokens[token_hash]
        return False
    return True

# Password hashing — use bcrypt directly to avoid passlib 1.7.4 / bcrypt 4.x compat issue
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password,
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


_signing_key_cache: Optional[str] = None
_verification_key_cache: Optional[str] = None


def _get_signing_key() -> str:
    """Get the signing key based on algorithm (cached after first read)."""
    global _signing_key_cache
    if settings.JWT_ALGORITHM == "RS256":
        if _signing_key_cache is None:
            key_path = settings.JWT_PRIVATE_KEY_PATH
            if key_path and os.path.exists(key_path):
                with open(key_path, "r") as f:
                    _signing_key_cache = f.read()
            else:
                raise RuntimeError("RS256 configured but private key not found — refusing to fall back to HS256")
        return _signing_key_cache
    return settings.JWT_SECRET_KEY


def _get_verification_key() -> str:
    """Get the verification key based on algorithm (cached after first read)."""
    global _verification_key_cache
    if settings.JWT_ALGORITHM == "RS256":
        if _verification_key_cache is None:
            key_path = settings.JWT_PUBLIC_KEY_PATH
            if key_path and os.path.exists(key_path):
                with open(key_path, "r") as f:
                    _verification_key_cache = f.read()
            else:
                raise RuntimeError("RS256 configured but public key not found — refusing to fall back to HS256")
        return _verification_key_cache
    return settings.JWT_SECRET_KEY


def validate_jwt_keys_on_startup() -> bool:
    """Validate that JWT keys are available for the configured algorithm.

    Call this during application startup. Returns True if keys are valid,
    raises an error if RS256 is configured but keys are missing.
    """
    if settings.JWT_ALGORITHM == "RS256":
        private_path = settings.JWT_PRIVATE_KEY_PATH
        public_path = settings.JWT_PUBLIC_KEY_PATH

        if not private_path or not public_path:
            logger.error("RS256 requires JWT_PRIVATE_KEY_PATH and JWT_PUBLIC_KEY_PATH to be set")
            return False

        if not os.path.exists(private_path):
            logger.error("JWT private key not found at: %s", private_path)
            return False

        if not os.path.exists(public_path):
            logger.error("JWT public key not found at: %s", public_path)
            return False

        logger.info("RS256 JWT keys validated: private=%s, public=%s", private_path, public_path)
    else:
        logger.info("Using HS256 JWT algorithm with secret key")

    return True


def create_access_token(user_id: uuid.UUID, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Create a JWT access token."""
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": now,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, _get_signing_key(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a JWT refresh token."""
    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, _get_signing_key(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, _get_verification_key(), algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def validate_token(token: str, db: AsyncSession):
    """Validate a token and return the user."""
    from app.models.user import User

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException(message="Invalid or expired token")

    # Check if access token has been revoked (e.g., on logout)
    if await is_access_token_revoked(token):
        raise UnauthorizedException(message="Token has been revoked")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(message="Invalid token payload")

    if payload.get("type") != "access":
        raise UnauthorizedException(message="Invalid token type")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException(message="User not found")

    if not user.is_active:
        raise UnauthorizedException(message="User account is inactive")

    return user


def generate_password_reset_token() -> str:
    """Generate a secure token for password reset."""
    return secrets.token_urlsafe(32)


def is_account_locked(user) -> bool:
    """Check if a user account is currently locked."""
    if user.locked_until is None:
        return False
    if user.locked_until <= datetime.now(timezone.utc):
        return False
    return True


def get_lockout_remaining_minutes(user) -> int:
    """Get the remaining lockout time in minutes."""
    if user.locked_until is None:
        return 0
    remaining = user.locked_until - datetime.now(timezone.utc)
    if remaining.total_seconds() <= 0:
        return 0
    return max(1, int(remaining.total_seconds() / 60))


def handle_failed_login(user) -> Dict[str, Any]:
    """Increment failed login attempts and lock account if threshold reached.

    Returns dict with lockout info.
    """
    user.failed_login_attempts += 1
    lockout_info = {
        "locked": False,
        "failed_attempts": user.failed_login_attempts,
        "lockout_duration_minutes": settings.LOCKOUT_DURATION_MINUTES,
    }

    if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        lockout_info["locked"] = True
        lockout_info["unlock_time"] = user.locked_until.isoformat()

    return lockout_info


def handle_successful_login(user):
    """Reset failed login attempts on successful authentication."""
    user.failed_login_attempts = 0
    user.locked_until = None