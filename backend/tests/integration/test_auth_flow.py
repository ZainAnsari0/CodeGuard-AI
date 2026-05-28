"""Integration tests for authentication flow: register, login, me, lockout, password reset."""

import pytest
from httpx import ASGITransport, AsyncClient


def unwrap(response_data):
    """Unwrap API response that may be nested under 'data' key."""
    if "data" in response_data and isinstance(response_data["data"], dict):
        return response_data["data"]
    return response_data


class TestRegisterFlow:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client):
        """Registering a new user should return success with user data."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "NewUser!Pass1",
            "full_name": "New User",
            "role": "developer",
        })
        assert response.status_code in (200, 201)
        data = unwrap(response.json())
        assert "user" in data or "email" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        """Registering with an existing email should return an error."""
        response = await client.post("/api/v1/auth/register", json={
            "email": test_user["email"],
            "password": "Another!Pass1",
            "full_name": "Duplicate User",
            "role": "developer",
        })
        assert response.status_code in (400, 409, 422)

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Registering with a weak password should fail validation."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "weak@test.com",
            "password": "weak",
            "full_name": "Weak Pass",
            "role": "developer",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client):
        """Registering with an invalid role should fail validation."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "badrole@test.com",
            "password": "Valid!Pass123",
            "full_name": "Bad Role",
            "role": "superadmin",
        })
        assert response.status_code == 422


class TestLoginFlow:
    """Tests for login and token retrieval."""

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Login with correct credentials should return a token."""
        response = await client.post("/api/v1/auth/login", data={
            "username": test_user["email"],
            "password": test_user["password"],
        })
        assert response.status_code == 200
        data = unwrap(response.json())
        assert "user" in data or "email" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        """Login with wrong password should return 401."""
        response = await client.post("/api/v1/auth/login", data={
            "username": test_user["email"],
            "password": "WrongPassword!1",
        })
        assert response.status_code in (401, 400)

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Login with a nonexistent email should return 401."""
        response = await client.post("/api/v1/auth/login", data={
            "username": "nonexistent@test.com",
            "password": "SomePassword!1",
        })
        assert response.status_code in (401, 400)


class TestGetMe:
    """Tests for the /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client, test_user):
        """Authenticated user should get their profile."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code == 200
        data = unwrap(response.json())
        # The response may have 'user' nested under data
        user_data = data.get("user", data)
        assert user_data.get("email") == test_user["email"]

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client):
        """Unauthenticated request should return 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client):
        """Request with invalid token should return 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401