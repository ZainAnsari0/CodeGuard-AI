"""Integration tests for container lifecycle: spawn, teardown, resource limits."""

import pytest
from unittest.mock import MagicMock, patch


class TestContainerSecurityHardening:
    """Tests for container security hardening options."""

    @pytest.mark.asyncio
    async def test_spawn_container_has_read_only_filesystem(self):
        """Containers should run with read-only filesystem."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"output"
        mock_container.short_id = "test123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_container(image="test:latest", command="echo hello")

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs.get("read_only") is True

    @pytest.mark.asyncio
    async def test_spawn_container_drops_all_capabilities(self):
        """Containers should drop all Linux capabilities."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"output"
        mock_container.short_id = "test123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_container(image="test:latest", command="echo hello")

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs.get("cap_drop") == ["ALL"]

    @pytest.mark.asyncio
    async def test_spawn_container_has_no_new_privileges(self):
        """Containers should have no-new-privileges security option."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"output"
        mock_container.short_id = "test123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_container(image="test:latest", command="echo hello")

        call_kwargs = mock_client.containers.run.call_args[1]
        assert "no-new-privileges:true" in call_kwargs.get("security_opt", [])

    @pytest.mark.asyncio
    async def test_spawn_container_has_pid_limit(self):
        """Containers should have a PID limit to prevent fork bombs."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"output"
        mock_container.short_id = "test123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_container(image="test:latest", command="echo hello")

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs.get("pids_limit") == 64

    @pytest.mark.asyncio
    async def test_spawn_container_has_tmpfs(self):
        """Containers should have a tmpfs mount for temporary writes."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"output"
        mock_container.short_id = "test123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_container(image="test:latest", command="echo hello")

        call_kwargs = mock_client.containers.run.call_args[1]
        assert "/tmp" in call_kwargs.get("tmpfs", {})

    @pytest.mark.asyncio
    async def test_spawn_container_network_disabled_by_default(self):
        """Containers should have network disabled by default."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"output"
        mock_container.short_id = "test123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_container(image="test:latest", command="echo hello")

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs.get("network_mode") == "none"