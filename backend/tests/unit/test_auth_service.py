"""Tests for authentication service: password hashing, JWT, and account lockout."""

import uuid
import time
from datetime import datetime, timedelta

import pytest
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    validate_jwt_keys_on_startup,
)


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_bcrypt_string(self):
        hashed = get_password_hash("MySecretP@ss123")
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_hash_password_different_each_time(self):
        """Bcrypt uses random salt, so hashes differ each time."""
        h1 = get_password_hash("MySecretP@ss123")
        h2 = get_password_hash("MySecretP@ss123")
        assert h1 != h2

    def test_verify_password_correct(self):
        hashed = get_password_hash("MySecretP@ss123")
        assert verify_password("MySecretP@ss123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = get_password_hash("MySecretP@ss123")
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_empty_password(self):
        hashed = get_password_hash("MySecretP@ss123")
        assert verify_password("", hashed) is False

    def test_verify_password_none_password(self):
        hashed = get_password_hash("MySecretP@ss123")
        with pytest.raises((TypeError, AttributeError)):
            verify_password(None, hashed)


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token_contains_sub(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id)
        assert isinstance(token, str)
        assert len(token) > 20
        # Decode and verify sub claim
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)

    def test_create_access_token_with_extra_claims(self):
        user_id = uuid.uuid4()
        token = create_access_token(
            user_id=user_id,
            extra_claims={"email": "test@example.com", "role": "developer"},
        )
        payload = decode_access_token(token)
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "developer"

    def test_create_access_token_different_users_produce_different_tokens(self):
        t1 = create_access_token(user_id=uuid.uuid4())
        t2 = create_access_token(user_id=uuid.uuid4())
        assert t1 != t2


class TestJWTKeyValidation:
    """Tests for JWT key validation on startup."""

    def test_validate_jwt_keys_hs256_returns_true(self):
        """HS256 mode should always return True (uses secret key)."""
        result = validate_jwt_keys_on_startup()
        assert result is True