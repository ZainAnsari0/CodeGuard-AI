"""Tests for container service: Docker container spawning with mocked Docker client."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestContainerServiceHealthCheck:
    """Tests for Docker availability checking."""

    def test_check_docker_available(self):
        """When Docker is reachable, health check should return available=True."""
        from app.services.container import ContainerService

        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "24.0.0"}

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            result = service.check_docker_available()
        assert result["available"] is True
        assert result["version"] == "24.0.0"

    def test_check_docker_unavailable(self):
        """When Docker is not reachable, health check should return available=False."""
        from app.services.container import ContainerService

        service = ContainerService()

        with patch.object(service, '_get_client', side_effect=Exception("Docker not running")):
            result = service.check_docker_available()
        assert result["available"] is False


class TestContainerSpawning:
    """Tests for container spawning and cleanup with mocked Docker."""

    @pytest.mark.asyncio
    async def test_spawn_container_success(self):
        """Successful container spawn should return output and clean up."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Hello from container"
        mock_container.short_id = "abc123"
        mock_container.remove = MagicMock()

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            result = await service.spawn_container(
                image="hello-world",
                command="echo hello",
                timeout=30,
            )

        assert result["status"] == "completed"
        assert result["exit_code"] == 0
        mock_container.remove.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_spawn_container_timeout(self):
        """Container timeout should be handled gracefully."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("Timeout")
        mock_container.kill = MagicMock()
        mock_container.remove = MagicMock()
        mock_container.short_id = "timeout123"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            result = await service.spawn_container(
                image="slow-image",
                command="sleep 999",
                timeout=1,
            )

        # Container cleanup should still happen
        mock_container.remove.assert_called()

    @pytest.mark.asyncio
    async def test_spawn_container_cleanup_on_error(self):
        """Container should be removed even when an error occurs."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("Unexpected error")
        mock_container.remove = MagicMock()
        mock_container.short_id = "error123"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            result = await service.spawn_container(
                image="test-image",
                command="echo test",
                timeout=30,
            )

        # Container cleanup should still happen
        mock_container.remove.assert_called()

    @pytest.mark.asyncio
    async def test_spawn_scan_container_read_only_volume(self):
        """Scan containers should mount code as read-only."""
        from app.services.container import ContainerService

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'{"findings": []}'
        mock_container.remove = MagicMock()
        mock_container.short_id = "scan123"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container

        service = ContainerService()
        service._client = mock_client

        with patch.object(service, '_get_client', return_value=mock_client):
            await service.spawn_scan_container(
                code_volume_path="/tmp/test_code",
                scanner_image="codeguard-scanner:latest",
                scan_config={"scan_id": "test-123"},
            )

        call_kwargs = mock_client.containers.run.call_args[1]
        # Verify volumes are mounted as read-only
        volumes = call_kwargs.get("volumes", {})
        assert "/tmp/test_code" in volumes
        assert volumes["/tmp/test_code"]["mode"] == "ro"