"""Integration tests for Qdrant database module.

These tests require Docker Compose with Qdrant running.
Run with: pytest tests/integration/database/test_qdrant_integration.py
"""

from __future__ import annotations

import subprocess
import time
from uuid import uuid4

import pytest
from qdrant_client.http import models

from jarvis.database.qdrant import (
    get_qdrant_client,
    close_qdrant_client,
    init_collection,
    collection_exists,
    get_collection_info,
    DEFAULT_COLLECTION_NAME,
    VECTOR_SIZE,
    DISTANCE_METRIC,
    HNSW_M,
    HNSW_EF_CONSTRUCT,
)


@pytest.fixture(scope="module")
def qdrant_running() -> None:
    """Verify Qdrant service is running before tests."""
    try:
        client = get_qdrant_client()
        # Test connection by listing collections
        client.get_collections()
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")


@pytest.fixture(scope="function")
def test_collection_name() -> str:
    """Generate unique collection name for each test."""
    return f"test_collection_{uuid4().hex[:8]}"


@pytest.fixture(scope="function", autouse=True)
def cleanup_client() -> None:
    """Clean up client after each test."""
    yield
    close_qdrant_client()


class TestCollectionInitialization:
    """Test collection initialization with real Qdrant instance."""

    def test_init_collection_creates_collection(
        self, qdrant_running: None, test_collection_name: str
    ) -> None:
        """Test that init_collection creates a new collection."""
        client = get_qdrant_client()

        # Verify collection doesn't exist initially
        assert not collection_exists(test_collection_name, client=client)

        # Initialize collection
        result = init_collection(collection_name=test_collection_name, client=client)
        assert result is True

        # Verify collection now exists
        assert collection_exists(test_collection_name, client=client)

        # Cleanup
        client.delete_collection(test_collection_name)

    def test_init_collection_validates_config(
        self, qdrant_running: None, test_collection_name: str
    ) -> None:
        """Test that collection is created with correct configuration."""
        client = get_qdrant_client()

        # Initialize collection
        init_collection(collection_name=test_collection_name, client=client)

        # Get collection info and validate
        info = get_collection_info(test_collection_name, client=client)

        assert info.config.params.vectors.size == VECTOR_SIZE
        assert info.config.params.vectors.distance == DISTANCE_METRIC
        assert info.config.hnsw_config.m == HNSW_M
        assert info.config.hnsw_config.ef_construct == HNSW_EF_CONSTRUCT

        # Cleanup
        client.delete_collection(test_collection_name)

    def test_init_collection_idempotency(
        self, qdrant_running: None, test_collection_name: str
    ) -> None:
        """Test that init_collection can be called multiple times without errors."""
        client = get_qdrant_client()

        # Initialize collection twice
        result1 = init_collection(collection_name=test_collection_name, client=client)
        result2 = init_collection(collection_name=test_collection_name, client=client)

        assert result1 is True
        assert result2 is True

        # Verify collection still exists with correct config
        info = get_collection_info(test_collection_name, client=client)
        assert info.config.params.vectors.size == VECTOR_SIZE

        # Cleanup
        client.delete_collection(test_collection_name)


class TestCollectionPersistence:
    """Test collection persistence across restarts."""

    @pytest.mark.slow
    def test_collection_persists_after_restart(
        self, qdrant_running: None, test_collection_name: str
    ) -> None:
        """Test that collection and data persist after Qdrant restart.

        This test requires docker compose to be available.
        """
        client = get_qdrant_client()

        # Create collection and add test points
        init_collection(collection_name=test_collection_name, client=client)

        # Insert test points
        test_points = [
            models.PointStruct(
                id=str(uuid4()),
                vector=[0.1] * VECTOR_SIZE,
                payload={"text": "test document 1"},
            ),
            models.PointStruct(
                id=str(uuid4()),
                vector=[0.2] * VECTOR_SIZE,
                payload={"text": "test document 2"},
            ),
        ]

        client.upsert(collection_name=test_collection_name, points=test_points)

        # Give Qdrant time to persist
        time.sleep(1)

        # Get point count before restart
        info_before = get_collection_info(test_collection_name, client=client)
        points_before = info_before.points_count

        # Restart Qdrant container
        try:
            subprocess.run(
                ["docker", "compose", "-f", "docker/docker-compose.yml", "restart", "qdrant"],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            pytest.skip(f"Cannot restart Qdrant container: {e}")

        # Wait for Qdrant to come back up
        max_retries = 10
        for _ in range(max_retries):
            try:
                close_qdrant_client()  # Reset client
                client = get_qdrant_client()
                client.get_collections()  # Test connection
                break
            except Exception:
                time.sleep(1)
        else:
            pytest.fail("Qdrant did not come back up after restart")

        # Verify collection still exists
        assert collection_exists(test_collection_name, client=client)

        # Verify point count is preserved
        info_after = get_collection_info(test_collection_name, client=client)
        assert info_after.points_count == points_before
        assert info_after.points_count == 2

        # Cleanup
        client.delete_collection(test_collection_name)


class TestHealthChecks:
    """Test health check integration."""

    def test_doctor_check_qdrant_collection_exists(
        self, qdrant_running: None, test_collection_name: str
    ) -> None:
        """Test that doctor check validates existing collection."""
        from jarvis.cli.doctor_checks import check_qdrant_collection

        client = get_qdrant_client()

        # Create test collection
        init_collection(collection_name=test_collection_name, client=client)

        # Run health check
        result = check_qdrant_collection(collection_name=test_collection_name)

        assert result.passed is True
        assert "configured correctly" in result.message

        # Cleanup
        client.delete_collection(test_collection_name)

    def test_doctor_check_qdrant_collection_missing(self, qdrant_running: None) -> None:
        """Test that doctor check detects missing collection."""
        from jarvis.cli.doctor_checks import check_qdrant_collection

        # Use non-existent collection name
        result = check_qdrant_collection(collection_name="nonexistent_collection")

        assert result.passed is False
        assert "does not exist" in result.message


class TestDefaultCollection:
    """Test initialization of default 'knowledge' collection."""

    def test_init_default_collection(self, qdrant_running: None) -> None:
        """Test initialization of default knowledge collection.

        This test creates the actual 'knowledge' collection that the system uses.
        """
        client = get_qdrant_client()

        # Check if collection already exists
        if collection_exists(DEFAULT_COLLECTION_NAME, client=client):
            # Skip if already initialized
            pytest.skip(f"Collection '{DEFAULT_COLLECTION_NAME}' already exists")

        # Initialize default collection
        result = init_collection(client=client)
        assert result is True

        # Verify configuration
        info = get_collection_info(client=client)
        assert info.config.params.vectors.size == VECTOR_SIZE
        assert info.config.params.vectors.distance == DISTANCE_METRIC

        # Note: We intentionally don't delete the default collection
        # as it's used by the actual system
