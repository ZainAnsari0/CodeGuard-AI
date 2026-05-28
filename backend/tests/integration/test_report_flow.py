"""Integration tests for report/share flow: listing, share token creation, access, revocation."""

import pytest


def unwrap(response_data):
    """Unwrap API response that may be nested under 'data' key."""
    if "data" in response_data and isinstance(response_data["data"], dict):
        return response_data["data"]
    return response_data


class TestShareTokenCreation:
    """Tests for creating share tokens."""

    @pytest.mark.asyncio
    async def test_create_share_requires_auth(self, client):
        """Creating a share token without auth should return 401."""
        response = await client.post(
            "/api/v1/share",
            json={"analysis_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_share_nonexistent_analysis(self, client, test_user):
        """Creating a share token for a nonexistent analysis should return 404."""
        response = await client.post(
            "/api/v1/share",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"analysis_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 404


class TestShareTokenAccess:
    """Tests for accessing shared reports."""

    @pytest.mark.asyncio
    async def test_access_invalid_token(self, client):
        """Accessing a share with an invalid token should return 404."""
        response = await client.get("/api/v1/share/invalid-token-12345")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_access_nonexistent_token(self, client):
        """Accessing a share with a nonexistent token should return 404."""
        response = await client.get("/api/v1/share/abc123def456")
        assert response.status_code == 404


class TestShareTokenList:
    """Tests for listing user share tokens."""

    @pytest.mark.asyncio
    async def test_list_shares_requires_auth(self, client):
        """Listing shares without auth should return 401."""
        response = await client.get("/api/v1/share")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_shares_authenticated(self, client, test_user):
        """Authenticated user should be able to list their shares."""
        response = await client.get(
            "/api/v1/share",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code == 200
        data = unwrap(response.json())
        assert "shares" in data or isinstance(data, list)


class TestShareTokenRevocation:
    """Tests for revoking share tokens."""

    @pytest.mark.asyncio
    async def test_revoke_invalid_token(self, client, test_user):
        """Revoking a nonexistent token should return 404."""
        response = await client.delete(
            "/api/v1/share/nonexistent-token",
            headers={"Authorization": f"Bearer {test_user['token']}"},
        )
        assert response.status_code == 404