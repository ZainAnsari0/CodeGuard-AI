"""Tests for Pydantic schema validation: auth schemas, password rules, role validation."""

import pytest
from pydantic import ValidationError
from app.schemas.auth import (
    UserCreate, UserLogin, UserUpdate, PasswordResetRequest,
    PasswordResetConfirm, UserRole, _validate_password,
)


class TestPasswordValidation:
    """Tests for password strength validation."""

    def test_valid_password(self):
        result = _validate_password("Str0ng!Pass")
        assert result == "Str0ng!Pass"

    def test_password_too_short(self):
        with pytest.raises(ValueError, match="at least 8 characters"):
            _validate_password("Sh0rt!")

    def test_password_no_uppercase(self):
        with pytest.raises(ValueError, match="uppercase"):
            _validate_password("lowercase123!")

    def test_password_no_lowercase(self):
        with pytest.raises(ValueError, match="lowercase"):
            _validate_password("UPPERCASE123!")

    def test_password_no_digit(self):
        with pytest.raises(ValueError, match="digit"):
            _validate_password("NoDigitsHere!")

    def test_password_no_special_char(self):
        with pytest.raises(ValueError, match="special character"):
            _validate_password("NoSpecialChar123")


class TestUserCreate:
    """Tests for UserCreate schema validation."""

    def test_valid_developer(self):
        user = UserCreate(
            email="dev@example.com",
            password="Str0ng!Pass",
            full_name="Dev User",
            role="developer",
        )
        assert user.email == "dev@example.com"
        assert user.role == "developer"

    def test_valid_instructor(self):
        user = UserCreate(
            email="instr@example.com",
            password="Str0ng!Pass",
            full_name="Instructor User",
            role="instructor",
        )
        assert user.role == "instructor"

    def test_valid_admin(self):
        user = UserCreate(
            email="admin@example.com",
            password="Str0ng!Pass",
            full_name="Admin User",
            role="admin",
        )
        assert user.role == "admin"

    def test_invalid_role(self):
        with pytest.raises(ValidationError, match="Role must be one of"):
            UserCreate(
                email="user@example.com",
                password="Str0ng!Pass",
                full_name="Bad User",
                role="superadmin",
            )

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="Str0ng!Pass",
                full_name="Bad User",
                role="developer",
            )

    def test_weak_password_no_special_char(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="user@example.com",
                password="NoSpecialChar123",
                full_name="Weak User",
                role="developer",
            )

    def test_optional_full_name(self):
        user = UserCreate(
            email="user@example.com",
            password="Str0ng!Pass",
            role="developer",
        )
        assert user.full_name is None


class TestUserLogin:
    """Tests for UserLogin schema."""

    def test_valid_login(self):
        login = UserLogin(email="user@example.com", password="password123")
        assert login.email == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserLogin(email="not-an-email", password="password123")


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_partial_update_email_only(self):
        update = UserUpdate(email="new@example.com")
        assert update.email == "new@example.com"
        assert update.password is None

    def test_partial_update_password(self):
        update = UserUpdate(password="NewStr0ng!Pass")
        assert update.password == "NewStr0ng!Pass"

    def test_update_with_invalid_role(self):
        with pytest.raises(ValidationError, match="Role must be one of"):
            UserUpdate(role="superadmin")

    def test_update_with_weak_password(self):
        """Password validation runs all checks; 'weakpass' fails on uppercase first."""
        with pytest.raises(ValidationError):
            UserUpdate(password="weakpass")


class TestPasswordReset:
    """Tests for password reset schemas."""

    def test_reset_request_valid_email(self):
        req = PasswordResetRequest(email="user@example.com")
        assert req.email == "user@example.com"

    def test_reset_request_invalid_email(self):
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="not-an-email")

    def test_reset_confirm_valid(self):
        confirm = PasswordResetConfirm(
            token="some-reset-token",
            new_password="NewStr0ng!Pass",
        )
        assert confirm.token == "some-reset-token"

    def test_reset_confirm_weak_password(self):
        """'weak' is too short (min 8 chars), so it fails on length before special chars."""
        with pytest.raises(ValidationError):
            PasswordResetConfirm(
                token="some-reset-token",
                new_password="weak",
            )