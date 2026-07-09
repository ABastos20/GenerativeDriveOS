"""Unit tests for Qdrant database module.

These tests mock the Qdrant client to avoid requiring a running Qdrant instance.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from jarvis.database.qdrant import (
    QdrantConnectionError,
    CollectionError,
    get_qdrant_config,
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
    HNSW_FULL_SCAN_THRESHOLD,
)


class TestQdrantConfig:
    """Test Qdrant configuration functions."""

    def test_get_qdrant_config_defaults(self) -> None:
        """Test default configuration values."""
        # Clear environment
        os.environ.pop("QDRANT_HOST", None)
        os.environ.pop("QDRANT_PORT", None)

        host, port = get_qdrant_config()

        assert host == "qdrant"
        assert port == 6333

    def test_get_qdrant_config_from_env(self) -> None:
        """Test configuration from environment variables."""
        os.environ["QDRANT_HOST"] = "custom-qdrant"
        os.environ["QDRANT_PORT"] = "9333"

        try:
            host, port = get_qdrant_config()

            assert host == "custom-qdrant"
            assert port == 9333
        finally:
            os.environ.pop("QDRANT_HOST", None)
            os.environ.pop("QDRANT_PORT", None)


class TestQdrantClient:
    """Test Qdrant client initialization."""

    def teardown_method(self) -> None:
        """Clean up client after each test."""
        close_qdrant_client()

    @patch("jarvis.database.qdrant.QdrantClient")
    def test_get_qdrant_client_success(self, mock_client_class: MagicMock) -> None:
        """Test successful client creation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = get_qdrant_client()

        assert client == mock_client
        mock_client_class.assert_called_once()

    @patch("jarvis.database.qdrant.QdrantClient")
    def test_get_qdrant_client_singleton(self, mock_client_class: MagicMock) -> None:
        """Test client singleton pattern."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client1 = get_qdrant_client()
        client2 = get_qdrant_client()

        assert client1 == client2
        assert mock_client_class.call_count == 1  # Only called once

    @patch("jarvis.database.qdrant.QdrantClient")
    def test_get_qdrant_client_connection_error(self, mock_client_class: MagicMock) -> None:
        """Test client connection failure."""
        mock_client_class.side_effect = Exception("Connection refused")

        with pytest.raises(QdrantConnectionError) as exc_info:
            get_qdrant_client()

        assert "Failed to connect to Qdrant" in str(exc_info.value)

    @patch("jarvis.database.qdrant.QdrantClient")
    def test_close_qdrant_client(self, mock_client_class: MagicMock) -> None:
        """Test client cleanup."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = get_qdrant_client()
        close_qdrant_client()

        mock_client.close.assert_called_once()

        # Verify new client created after close
        client2 = get_qdrant_client()
        assert mock_client_class.call_count == 2


class TestCollectionOperations:
    """Test collection management operations."""

    def teardown_method(self) -> None:
        """Clean up client after each test."""
        close_qdrant_client()

    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_collection_exists_true(self, mock_get_client: MagicMock) -> None:
        """Test collection_exists returns True when collection exists."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_get_client.return_value = mock_client

        result = collection_exists("knowledge")

        assert result is True
        mock_client.collection_exists.assert_called_once_with(collection_name="knowledge")

    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_collection_exists_false(self, mock_get_client: MagicMock) -> None:
        """Test collection_exists returns False when collection doesn't exist."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False
        mock_get_client.return_value = mock_client

        result = collection_exists("knowledge")

        assert result is False

    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_collection_exists_error(self, mock_get_client: MagicMock) -> None:
        """Test collection_exists handles errors."""
        mock_client = MagicMock()
        mock_client.collection_exists.side_effect = Exception("Connection lost")
        mock_get_client.return_value = mock_client

        with pytest.raises(QdrantConnectionError) as exc_info:
            collection_exists("knowledge")

        assert "Failed to check if collection" in str(exc_info.value)

    @patch("jarvis.database.qdrant.collection_exists")
    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_init_collection_creates_new(
        self, mock_get_client: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test init_collection creates collection when it doesn't exist."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_exists.return_value = False

        result = init_collection()

        assert result is True
        mock_client.create_collection.assert_called_once()

        # Verify correct parameters
        call_args = mock_client.create_collection.call_args
        assert call_args.kwargs["collection_name"] == DEFAULT_COLLECTION_NAME
        assert call_args.kwargs["vectors_config"].size == VECTOR_SIZE
        assert call_args.kwargs["vectors_config"].distance == DISTANCE_METRIC
        assert call_args.kwargs["hnsw_config"].m == HNSW_M
        assert call_args.kwargs["hnsw_config"].ef_construct == HNSW_EF_CONSTRUCT

    @patch("jarvis.database.qdrant.collection_exists")
    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_init_collection_idempotent(
        self, mock_get_client: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test init_collection is idempotent when collection exists."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_exists.return_value = True

        result = init_collection()

        assert result is True
        mock_client.create_collection.assert_not_called()  # Should not create

    @patch("jarvis.database.qdrant.collection_exists")
    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_init_collection_error(
        self, mock_get_client: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test init_collection handles creation errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_exists.return_value = False
        mock_client.create_collection.side_effect = UnexpectedResponse(
            status_code=500,
            reason_phrase="server error",
            content=b"error",
            headers={},
        )

        with pytest.raises(CollectionError) as exc_info:
            init_collection()

        assert "Failed to create collection" in str(exc_info.value)

    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_get_collection_info_success(self, mock_get_client: MagicMock) -> None:
        """Test get_collection_info returns collection info."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_info = MagicMock(spec=models.CollectionInfo)
        mock_client.get_collection.return_value = mock_info

        result = get_collection_info("knowledge")

        assert result == mock_info
        mock_client.get_collection.assert_called_once_with(collection_name="knowledge")

    @patch("jarvis.database.qdrant.get_qdrant_client")
    def test_get_collection_info_error(self, mock_get_client: MagicMock) -> None:
        """Test get_collection_info handles errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_collection.side_effect = Exception("Collection not found")

        with pytest.raises(CollectionError) as exc_info:
            get_collection_info("knowledge")

        assert "Failed to get info for collection" in str(exc_info.value)


class TestCollectionParameters:
    """Test collection configuration parameters."""

    def test_default_parameters(self) -> None:
        """Test default collection parameters match architecture spec."""
        assert DEFAULT_COLLECTION_NAME == "knowledge"
        assert VECTOR_SIZE == 384
        assert DISTANCE_METRIC == models.Distance.COSINE
        assert HNSW_M == 16
        assert HNSW_EF_CONSTRUCT == 200
        assert HNSW_FULL_SCAN_THRESHOLD == 10000
