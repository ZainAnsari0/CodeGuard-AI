"""
CodeGuard AI - Docker Container Service
Manages ephemeral Docker containers for code scanning.
Spawn → Run Analysis → Destroy lifecycle.
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum concurrent scan containers (configurable via settings)
# NOTE: This semaphore is per-process. In multi-worker deployments (e.g., uvicorn --workers N),
# the effective concurrency limit is MAX_CONCURRENT_SCANS * workers. For global coordination
# across workers, use a Redis-based distributed semaphore.
_MAX_CONCURRENT_SCANS = getattr(settings, "MAX_CONCURRENT_SCANS", 5)

# Module-level semaphore singleton — shared across all calls within this process
_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    """Return the shared concurrency semaphore, creating it once.

    This semaphore limits concurrent scans *within a single process*. In a multi-worker
    deployment, each worker has its own semaphore, so the effective cluster-wide limit
    is MAX_CONCURRENT_SCANS multiplied by the number of workers.
    """
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(_MAX_CONCURRENT_SCANS)
    return _semaphore


class ContainerService:
    """Service for managing ephemeral Docker containers for code scanning."""

    def __init__(self):
        self._client = None
        self._lock = threading.Lock()

    def _get_client(self):
        """Lazy-initialize Docker client (thread-safe)."""
        if self._client is None:
            with self._lock:
                # Double-check after acquiring lock
                if self._client is None:
                    try:
                        import docker
                        self._client = docker.from_env()
                        logger.info("Docker client initialized successfully")
                    except ImportError:
                        logger.error("docker package not installed. Install with: pip install docker")
                        raise
                    except Exception as e:
                        logger.error(f"Failed to initialize Docker client: {e}")
                        raise
        return self._client

    def close(self):
        """Close the Docker client to release resources."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    async def _wait_container(self, container, timeout: int) -> Dict[str, Any]:
        """Wait for container completion without blocking the event loop."""
        return await asyncio.to_thread(container.wait, timeout=timeout)

    def _run_container_sync(self, client, **kwargs):
        """Synchronous container run — called via to_thread."""
        return client.containers.run(**kwargs)

    def _get_logs_sync(self, container):
        """Synchronous log retrieval — called via to_thread."""
        return container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

    async def spawn_container(
        self,
        image: str,
        command: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        timeout: int = 300,
        mem_limit: str = "512m",
        cpu_period: int = 100000,
        cpu_quota: int = 50000,
        network_disabled: bool = True,
    ) -> Dict[str, Any]:
        """Spawn an ephemeral container, run a command, and collect results."""
        container = None
        semaphore = _get_semaphore()
        async with semaphore:
            try:
                logger.info(f"Spawning container from image: {image}")
                client = self._get_client()

                container = await asyncio.to_thread(
                    self._run_container_sync, client,
                    image=image,
                    command=command,
                    environment=environment or {},
                    volumes=volumes or {},
                    mem_limit=mem_limit,
                    memswap_limit=mem_limit,
                    cpu_period=cpu_period,
                    cpu_quota=cpu_quota,
                    network_mode="none" if network_disabled else "bridge",
                    detach=True,
                    remove=False,
                    stdout=True,
                    stderr=True,
                    read_only=True,
                    pids_limit=64,
                    cap_drop=["ALL"],
                    security_opt=["no-new-privileges:true"],
                    tmpfs={"/tmp": "size=100m"},
                    labels={"codeguard": "true"},
                )

                logger.info(f"Container {container.short_id} spawned, waiting for completion (timeout={timeout}s)")

                result = await self._wait_container(container, timeout=timeout)
                exit_code = result.get("StatusCode", -1)

                logs = await asyncio.to_thread(self._get_logs_sync, container)

                logger.info(f"Container {container.short_id} completed with exit code {exit_code}")

                return {
                    "container_id": container.short_id,
                    "exit_code": exit_code,
                    "output": logs,
                    "status": "completed" if exit_code == 0 else "failed",
                }

            except Exception as e:
                logger.error(f"Container execution error: {e}")
                return {
                    "container_id": container.short_id if container else None,
                    "exit_code": -1,
                    "output": str(e),
                    "status": "error",
                }

            finally:
                if container:
                    try:
                        await asyncio.to_thread(container.remove, force=True)
                        logger.info(f"Container {container.short_id} removed")
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to remove container: {cleanup_err}")

    async def spawn_scan_container(
        self,
        code_volume_path: str,
        scanner_image: str = "codeguard-scanner:latest",
        scan_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Spawn a container specifically for code scanning."""
        volumes = {
            code_volume_path: {"bind": "/code", "mode": "ro"},
        }

        environment = {}
        if scan_config:
            import json
            environment["SCAN_CONFIG"] = json.dumps(scan_config)

        command = "python scanner.py /code"

        return await self.spawn_container(
            image=scanner_image,
            command=command,
            environment=environment,
            volumes=volumes,
            timeout=600,
            mem_limit="1g",
            network_disabled=True,
        )

    def check_docker_available(self) -> Dict[str, Any]:
        """Verify Docker daemon is accessible and can spawn containers."""
        try:
            client = self._get_client()
            version_info = client.version()
            logger.info(f"Docker daemon available: {version_info.get('Version', 'unknown')}")

            return {
                "available": True,
                "version": version_info.get("Version", "unknown"),
                "error": None,
            }
        except Exception as e:
            logger.error(f"Docker daemon not available: {e}")
            return {
                "available": False,
                "version": None,
                "error": str(e),
            }


# Singleton instance
container_service = ContainerService()