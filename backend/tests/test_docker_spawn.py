"""
Sprint 1 Deliverable (S1.9): Docker Socket Mount Test
Verifies that the backend can spawn ephemeral containers from the API.

Usage:
    python -m tests.test_docker_spawn
    # or: python tests/test_docker_spawn.py
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _is_docker_available():
    """Check if Docker daemon is accessible."""
    try:
        import docker
        client = docker.from_env()
        client.version()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _is_docker_available(), reason="Docker daemon not available")
def test_docker_availability():
    """Test that the Docker daemon is accessible and can list containers."""
    import docker

    client = docker.from_env()
    version_info = client.version()

    assert version_info is not None, "Docker version info should not be None"
    assert "Version" in version_info, "Docker version info should contain 'Version'"

    # List running containers (should not raise)
    containers = client.containers.list()
    assert isinstance(containers, list), "containers.list() should return a list"


@pytest.mark.skipif(not _is_docker_available(), reason="Docker daemon not available")
def test_container_spawn():
    """Test spawning an ephemeral container and collecting output."""
    import docker

    client = docker.from_env()

    # Run hello-world container (lightweight, exits immediately)
    try:
        output = client.containers.run(
            "hello-world",
            detach=False,
            remove=True,
        )
        output_text = output.decode("utf-8", errors="replace").strip()
        assert len(output_text) > 0, "Container should produce output"
    except docker.errors.ImageNotFound:
        # Pull the image if not available locally
        client.images.pull("hello-world")
        output = client.containers.run(
            "hello-world",
            detach=False,
            remove=True,
        )
        output_text = output.decode("utf-8", errors="replace").strip()
        assert len(output_text) > 0, "Container should produce output after pulling image"


@pytest.mark.skipif(not _is_docker_available(), reason="Docker daemon not available")
def test_container_service():
    """Test the ContainerService wrapper class."""
    from app.services.container import container_service

    # Test health check
    health = container_service.check_docker_available()
    assert health["available"], f"Docker should be available but got: {health['error']}"

    # Test spawn via service
    result = container_service.spawn_container(
        image="hello-world",
        timeout=30,
        mem_limit="64m",
        network_disabled=False,
    )

    assert result["status"] == "completed", f"Container spawn failed: {result}"
    assert result["exit_code"] == 0, f"Container exited with code: {result['exit_code']}"
    assert len(result["output"]) > 0, "Container should produce output"


def main():
    """Standalone runner for manual testing outside of pytest."""
    print("\n" + "=" * 60)
    print("  CodeGuard AI — Sprint 1 Task S1.9")
    print("  Docker Socket Mount & Container Spawn Test")
    print("=" * 60 + "\n")

    results = []

    # Docker availability
    try:
        import docker
        client = docker.from_env()
        version_info = client.version()
        print(f"  [PASS] Docker daemon is accessible")
        print(f"  Docker version: {version_info.get('Version', 'unknown')}")
        containers = client.containers.list()
        print(f"  Running containers: {len(containers)}")
        results.append(("Docker availability", True))
    except docker.errors.DockerException as e:
        print(f"  [FAIL] Cannot connect to Docker daemon: {e}")
        print("  To fix:")
        print("    1. Install Docker: https://docs.docker.com/get-docker/")
        print("    2. Add user to docker group: sudo usermod -aG docker $USER")
        print("    3. Start Docker: sudo systemctl start docker")
        results.append(("Docker availability", False))
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        results.append(("Docker availability", False))

    if results[0][1]:
        # Container spawn test
        try:
            client = docker.from_env()
            try:
                output = client.containers.run("hello-world", detach=False, remove=True)
                print(f"  [PASS] Container spawned and completed successfully")
                results.append(("Container spawn", True))
            except docker.errors.ImageNotFound:
                client.images.pull("hello-world")
                output = client.containers.run("hello-world", detach=False, remove=True)
                print(f"  [PASS] Container spawned after pulling image")
                results.append(("Container spawn", True))
        except Exception as e:
            print(f"  [FAIL] Container spawn error: {e}")
            results.append(("Container spawn", False))

        # ContainerService test
        try:
            from app.services.container import container_service
            health = container_service.check_docker_available()
            if health["available"]:
                print(f"  [PASS] ContainerService reports Docker available")
                result = container_service.spawn_container(
                    image="hello-world", timeout=30, mem_limit="64m", network_disabled=False,
                )
                if result["status"] == "completed":
                    print(f"  [PASS] ContainerService.spawn_container works")
                    results.append(("ContainerService", True))
                else:
                    print(f"  [FAIL] Container spawn failed: {result}")
                    results.append(("ContainerService", False))
            else:
                print(f"  [FAIL] Docker unavailable: {health['error']}")
                results.append(("ContainerService", False))
        except Exception as e:
            print(f"  [FAIL] ContainerService error: {e}")
            results.append(("ContainerService", False))
    else:
        print("\n  [SKIP] Skipping container tests — Docker not available.")

    print("\n" + "=" * 60)
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("  RESULT: ALL TESTS PASSED — S1.9 COMPLETE")
    else:
        print("  RESULT: SOME TESTS FAILED — Review errors above")
        for name, passed in results:
            print(f"    {name}: {'PASS' if passed else 'FAIL'}")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()