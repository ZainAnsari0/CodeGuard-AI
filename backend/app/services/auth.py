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
# Production: Redis-backed (required for multi-worker deployments)
# Development: In-memory (acceptable for single-worker dev mode)

class TokenRevocationStore:
    """Manages token revocation with Redis backend and safe fallback.

    Production mode (REDIS_ENABLED=True):
        - Uses Redis for shared state across workers
        - If Redis is unavailable, FAILS CLOSED (treats tokens as revoked)
          to prevent security bypass
        - Uses connection pool for efficiency

    Development mode (REDIS_ENABLED=False):
        - Uses in-memory dict (single worker only)
        - Appropriate for local development
    """

    def __init__(self):
        self._redis_pool = None
        self._memory_store: Dict[str, float] = {}  # token_hash -> expiry timestamp
        self._redis_available: bool = False

    async def _get_redis(self):
        """Get Redis connection pool. Initializes pool on first call."""
        if self._redis_pool is not None:
            return self._redis_pool

        if settings.REDIS_ENABLED:
            try:
                import redis.asyncio as aioredis
                self._redis_pool = aioredis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    max_connections=10,
                )
                # Test the connection
                conn = aioredis.Redis(connection_pool=self._redis_pool)
                await conn.ping()
                await conn.aclose()
                self._redis_available = True
                logger.info("Token revocation: Redis connection pool initialized")
                return self._redis_pool
            except Exception as e:
                self._redis_available = False
                if settings.ENVIRONMENT == "production":
                    logger.error(
                        "Token revocation: Redis unavailable in production mode! "
                        "FAILING CLOSED — all revocation checks will return True (revoked). "
                        "Error: %s", e
                    )
                else:
                    logger.warning(
                        "Token revocation: Redis unavailable, using in-memory fallback (dev mode): %s", e
                    )
                return None
        return None

    async def _redis_set(self, key: str, ttl_seconds: int, value: str = "1") -> bool:
        """Set a key in Redis. Returns True if successful."""
        pool = await self._get_redis()
        if pool is None:
            return False
        import redis.asyncio as aioredis
        conn = aioredis.Redis(connection_pool=pool)
        try:
            await conn.setex(key, ttl_seconds, value)
            return True
        except Exception as e:
            logger.warning("Redis setex failed: %s", e)
            self._redis_available = False
            return False
        finally:
            await conn.aclose()

    async def _redis_exists(self, key: str) -> Optional[bool]:
        """Check if key exists in Redis. Returns True/False/None (None=Redis unavailable)."""
        pool = await self._get_redis()
        if pool is None:
            return None
        import redis.asyncio as aioredis
        conn = aioredis.Redis(connection_pool=pool)
        try:
            result = await conn.exists(key)
            self._redis_available = True
            return bool(result)
        except Exception as e:
            logger.warning("Redis exists check failed: %s", e)
            self._redis_available = False
            return None
        finally:
            await conn.aclose()

    async def _memory_set(self, key: str, ttl_seconds: int) -> None:
        """Set a key in in-memory store."""
        self._memory_store[key] = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).timestamp()

    def _memory_exists(self, key: str) -> bool:
        """Check if key exists in in-memory store and hasn't expired."""
        expiry = self._memory_store.get(key)
        if expiry is None:
            return False
        if expiry <= datetime.now(timezone.utc).timestamp():
            del self._memory_store[key]
            return False
        return True

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Mark a token as revoked."""
        token_hash = _revoke_token_hash(token)
        redis_ok = await self._redis_set(f"revoked:{token_hash}", ttl_seconds)
        if not redis_ok:
            if settings.ENVIRONMENT == "production":
                logger.error(
                    "Token revocation FAILED in production — Redis unavailable! "
                    "Token may not be properly revoked across workers."
                )
            await self._memory_set(token_hash, ttl_seconds)

    async def is_revoked(self, token: str, ttl_seconds: int) -> bool:
        """Check if a token has been revoked.

        In production mode with Redis unavailable: FAILS CLOSED (returns True).
        In development mode: Falls back to in-memory check.
        """
        token_hash = _revoke_token_hash(token)

        # Try Redis first
        redis_result = await self._redis_exists(f"revoked:{token_hash}")
        if redis_result is True:
            return True
        if redis_result is False:
            return False

        # Redis unavailable
        if settings.ENVIRONMENT == "production":
            # FAIL CLOSED: if we can't check Redis in production, treat as revoked
            logger.error(
                "Cannot verify token revocation status — Redis unavailable in production. "
                "Failing closed (treating token as revoked) for security."
            )
            return True

        # Development mode: use in-memory fallback
        return self._memory_exists(token_hash)

    async def is_refresh_revoked(self, token: str) -> bool:
        """Check if a refresh token is revoked."""
        return await self.is_revoked(token, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    async def is_access_revoked(self, token: str) -> bool:
        """Check if an access token is revoked."""
        return await self.is_revoked(token, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    async def revoke_refresh(self, token: str) -> None:
        """Revoke a refresh token."""
        await self.revoke(token, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    async def revoke_access(self, token: str) -> None:
        """Revoke an access token."""
        await self.revoke(token, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    async def close(self):
        """Close Redis connection pool. Call at application shutdown."""
        if self._redis_pool is not None:
            import redis.asyncio as aioredis
            await self._redis_pool.disconnect()
            self._redis_pool = None


# Singleton instance
_revocation_store = TokenRevocationStore()


def _revoke_token_hash(token: str) -> str:
    """Hash token before storing to avoid exposing raw tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Public API (backward compatible function signatures) ────────

async def revoke_refresh_token(token: str) -> None:
    """Mark a refresh token as revoked."""
    await _revocation_store.revoke_refresh(token)


async def is_refresh_token_revoked(token: str) -> bool:
    """Check if a refresh token has been revoked."""
    return await _revocation_store.is_refresh_revoked(token)


async def revoke_access_token(token: str) -> None:
    """Mark an access token as revoked (used on logout)."""
    await _revocation_store.revoke_access(token)


async def is_access_token_revoked(token: str) -> bool:
    """Check if an access token has been revoked."""
    return await _revocation_store.is_access_revoked(token)


async def close_revocation_store() -> None:
    """Close the revocation store (call during application shutdown)."""
    await _revocation_store.close()


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