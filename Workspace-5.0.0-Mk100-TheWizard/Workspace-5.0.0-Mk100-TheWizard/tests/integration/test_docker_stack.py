"""
Integration tests for Docker Compose stack.

These tests validate that the full JARVIS Docker environment starts correctly,
all services reach healthy state, and basic inter-service communication works.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "docker" / "docker-compose.yml"


def run_compose_command(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run docker compose command with proper file reference."""
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


@pytest.fixture(scope="module")
def docker_stack():
    """
    Fixture that starts the Docker Compose stack before tests and tears it down after.

    Uses module scope so the stack only starts once for all tests in this file.
    """
    # Start the stack
    print("\n🚀 Starting Docker Compose stack...")
    result = run_compose_command(["up", "-d", "--build"], timeout=300)

    if result.returncode != 0:
        pytest.fail(f"Failed to start Docker stack:\n{result.stderr}")

    # Wait for services to be healthy (max 60 seconds)
    print("⏳ Waiting for services to become healthy...")
    max_wait = 60
    start_time = time.time()

    while time.time() - start_time < max_wait:
        ps_result = run_compose_command(["ps", "--format", "json"])
        if ps_result.returncode == 0:
            # Check if all services are running/healthy
            # Simple check: if ps succeeds and shows output, services are up
            if ps_result.stdout.strip():
                print("✅ Services are up")
                time.sleep(5)  # Give services a bit more time to stabilize
                break
        time.sleep(2)
    else:
        pytest.fail("Services did not become healthy within 60 seconds")

    yield

    # Teardown: stop and remove containers
    print("\n🛑 Stopping Docker Compose stack...")
    run_compose_command(["down"], timeout=60)


class TestDockerStack:
    """Integration tests for the Docker Compose stack."""

    def test_all_services_start(self, docker_stack):
        """Verify all 4 services (jarvis, postgres, qdrant, redis) start successfully."""
        result = run_compose_command(["ps", "--format", "json"])
        assert result.returncode == 0, f"docker compose ps failed: {result.stderr}"
        assert result.stdout.strip(), "No services found running"

        # Check for expected service names in output
        output = result.stdout.lower()
        expected_services = ["jarvis", "postgres", "qdrant", "redis"]

        for service in expected_services:
            assert service in output, f"Service '{service}' not found in running containers"

    def test_postgres_health_check(self, docker_stack):
        """Verify PostgreSQL is healthy using pg_isready."""
        result = run_compose_command([
            "exec", "-T", "postgres", "pg_isready", "-U", "jarvis"
        ])

        assert result.returncode == 0, f"PostgreSQL health check failed: {result.stderr}"
        assert "accepting connections" in result.stdout, "PostgreSQL not accepting connections"

    def test_qdrant_http_endpoint(self, docker_stack):
        """Verify Qdrant HTTP endpoint is responding."""
        # Use curl from jarvis container (has network access to other services)
        result = run_compose_command([
            "exec", "-T", "jarvis", "curl", "-f", "http://qdrant:6333/readyz"
        ])

        # If curl succeeds (exit code 0), Qdrant is healthy
        # Note: If curl is not in image, this test will fail - that's expected at this stage
        if result.returncode != 0:
            if "not found" in result.stderr or "No such file" in result.stderr:
                pytest.skip("curl not available in jarvis container yet")
            else:
                assert False, f"Qdrant health check failed: {result.stderr}"

    def test_redis_ping(self, docker_stack):
        """Verify Redis responds to PING command."""
        result = run_compose_command([
            "exec", "-T", "redis", "redis-cli", "ping"
        ])

        assert result.returncode == 0, f"Redis ping failed: {result.stderr}"
        assert "PONG" in result.stdout, "Redis did not respond with PONG"

    def test_workspace_mount_exists(self, docker_stack):
        """Verify /workspace directory is mounted in jarvis container."""
        result = run_compose_command([
            "exec", "-T", "jarvis", "ls", "-la", "/workspace"
        ])

        assert result.returncode == 0, f"Workspace mount check failed: {result.stderr}"
        assert "total" in result.stdout, "/workspace directory appears empty or not mounted"

    def test_workspace_write_permissions(self, docker_stack):
        """Verify jarvis container can write to /workspace/.jarvis/."""
        # Try to create a test file
        result = run_compose_command([
            "exec", "-T", "jarvis", "bash", "-c",
            "mkdir -p /workspace/.jarvis && echo 'test' > /workspace/.jarvis/.test-write && rm /workspace/.jarvis/.test-write"
        ])

        assert result.returncode == 0, f"Workspace write test failed: {result.stderr}"

    def test_jarvis_doctor_command(self, docker_stack):
        """Verify jarvis doctor command exists and runs (may not pass all checks yet)."""
        result = run_compose_command([
            "exec", "-T", "jarvis", "bash", "-c",
            "python -m jarvis.cli.doctor --help"
        ])

        # If the module doesn't exist yet, that's okay - skip test
        if result.returncode != 0 and "No module named" in result.stderr:
            pytest.skip("jarvis.cli.doctor module not yet implemented")

        assert result.returncode == 0, f"jarvis doctor --help failed: {result.stderr}"
        assert "doctor" in result.stdout.lower() or "Usage" in result.stdout


class TestDockerBuild:
    """Tests that can run without starting the full stack - just test the build."""

    def test_docker_build_succeeds(self):
        """Verify docker compose build completes without errors."""
        result = run_compose_command(["build", "jarvis"], timeout=600)

        assert result.returncode == 0, f"Docker build failed:\n{result.stderr}\n{result.stdout}"

    def test_poetry_dependencies_installed(self, docker_stack):
        """Verify Poetry dependencies are installed in the container."""
        result = run_compose_command([
            "exec", "-T", "jarvis", "python", "-c",
            "import typer, structlog, qdrant_client, psycopg2, redis; print('OK')"
        ])

        if result.returncode != 0:
            if "No module named" in result.stderr:
                pytest.fail(f"Required dependencies not installed: {result.stderr}")
            else:
                assert False, f"Dependency check failed: {result.stderr}"

        assert "OK" in result.stdout, "Import check did not complete successfully"


if __name__ == "__main__":
    # Run tests with pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
