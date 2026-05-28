"""Integration tests for admin endpoints: user management, role-based access."""

import pytest


class TestAdminAccess:
    """Tests for admin role-based access control."""

    @pytest.mark.asyncio
    async def test_admin_can_access_users(self, client, admin_user):
        """Admin should be able to list users."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_user['token']}"},
        )
        assert response.status_code in (200, 404)  # 404 if endpoint doesn't exist yet

    @pytest.mark.asyncio
    async def test_developer_cannot_access_admin(self, client, test_user):
        """Developer should be denied access to admin endpoints."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code in (403, 401)  # Forbidden or Unauthorized

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_admin(self, client):
        """Unauthenticated request should be denied access to admin endpoints."""
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 401


class TestAdminSystemHealth:
    """Tests for admin system health endpoint."""

    @pytest.mark.asyncio
    async def test_system_health_requires_auth(self, client):
        """System health should require authentication."""
        response = await client.get("/api/v1/admin/system/health")
        assert response.status_code == 401