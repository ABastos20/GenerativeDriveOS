"""Qdrant vector database connection and collection management.

This module provides:
- Qdrant client with lazy initialization
- Collection creation and management
- Custom exception classes
- Environment-based configuration

Collection is configured per architecture.md:
- Vector size: 384 dimensions (all-MiniLM-L6-v2)
- Distance metric: Cosine
- HNSW config: m=16, ef_construct=200, full_scan_threshold=10000
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

# Use structlog for structured logging
logger = structlog.get_logger(__name__)


# --- Custom Exceptions -----------------------------------------------------------


class QdrantError(Exception):
    """Base exception for Qdrant operations."""


class QdrantConnectionError(QdrantError):
    """Qdrant connection failed."""


class CollectionError(QdrantError):
    """Collection operation failed."""


# --- Configuration ---------------------------------------------------------------


def get_qdrant_config() -> tuple[str, int]:
    """Get Qdrant configuration from environment variables.

    Environment variables:
        QDRANT_HOST: Qdrant host (default: qdrant)
        QDRANT_PORT: Qdrant port (default: 6333)

    Returns:
        Tuple of (host, port)
    """
    host = os.environ.get("QDRANT_HOST", "qdrant")
    port = int(os.environ.get("QDRANT_PORT", "6333"))

    return host, port


# --- Client Initialization -------------------------------------------------------


_client: Optional[QdrantClient] = None


def get_qdrant_client(timeout: float = 5.0) -> QdrantClient:
    """Get or create Qdrant client with lazy initialization.

    Args:
        timeout: Connection timeout in seconds (default: 5.0)

    Returns:
        QdrantClient instance

    Raises:
        QdrantConnectionError: If client creation fails
    """
    global _client

    if _client is not None:
        return _client

    try:
        host, port = get_qdrant_config()

        _client = QdrantClient(
            host=host,
            port=port,
            timeout=timeout,
        )

        logger.info(
            "qdrant_client_created",
            host=host,
            port=port,
            timeout=timeout,
        )

        return _client

    except Exception as e:
        logger.error(
            "qdrant_connection_failed",
            error=str(e),
            host=host,
            port=port,
        )
        raise QdrantConnectionError(f"Failed to connect to Qdrant: {e}") from e


def close_qdrant_client() -> None:
    """Close Qdrant client and clean up resources.

    Use this for graceful shutdown in tests or application teardown.
    """
    global _client

    if _client is not None:
        _client.close()
        _client = None
        logger.info("qdrant_client_closed")


# --- Collection Management -------------------------------------------------------


# Collection defaults from architecture.md
DEFAULT_COLLECTION_NAME = "knowledge"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 embedding dimension
DISTANCE_METRIC = models.Distance.COSINE
HNSW_M = 16
HNSW_EF_CONSTRUCT = 200
HNSW_FULL_SCAN_THRESHOLD = 10000


def init_collection(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    vector_size: int = VECTOR_SIZE,
    distance: models.Distance = DISTANCE_METRIC,
    hnsw_m: int = HNSW_M,
    hnsw_ef_construct: int = HNSW_EF_CONSTRUCT,
    hnsw_full_scan_threshold: int = HNSW_FULL_SCAN_THRESHOLD,
    client: Optional[QdrantClient] = None,
) -> bool:
    """Initialize Qdrant collection idempotently.

    Creates collection if it doesn't exist. If collection already exists,
    logs and returns success without modification.

    Args:
        collection_name: Name of collection to create (default: "knowledge")
        vector_size: Dimension of vectors (default: 384 for all-MiniLM-L6-v2)
        distance: Distance metric (default: Cosine)
        hnsw_m: HNSW m parameter (default: 16)
        hnsw_ef_construct: HNSW ef_construct parameter (default: 200)
        hnsw_full_scan_threshold: HNSW full scan threshold (default: 10000)
        client: Optional QdrantClient instance (uses global if None)

    Returns:
        True if collection was created or already exists

    Raises:
        CollectionError: If collection creation fails
    """
    if client is None:
        client = get_qdrant_client()

    try:
        # Check if collection already exists (idempotency)
        if collection_exists(collection_name, client=client):
            logger.info(
                "collection_already_exists",
                collection_name=collection_name,
            )
            return True

        # Create collection with architecture-specified parameters
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=distance,
            ),
            hnsw_config=models.HnswConfigDiff(
                m=hnsw_m,
                ef_construct=hnsw_ef_construct,
                full_scan_threshold=hnsw_full_scan_threshold,
            ),
        )

        logger.info(
            "collection_created",
            collection_name=collection_name,
            vector_size=vector_size,
            distance=distance.value,
            hnsw_m=hnsw_m,
            hnsw_ef_construct=hnsw_ef_construct,
        )

        return True

    except (ResponseHandlingException, UnexpectedResponse) as e:
        logger.error(
            "collection_creation_failed",
            collection_name=collection_name,
            error=str(e),
        )
        raise CollectionError(f"Failed to create collection '{collection_name}': {e}") from e


def collection_exists(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    client: Optional[QdrantClient] = None,
) -> bool:
    """Check if collection exists in Qdrant.

    Args:
        collection_name: Name of collection to check
        client: Optional QdrantClient instance (uses global if None)

    Returns:
        True if collection exists, False otherwise

    Raises:
        QdrantConnectionError: If unable to check collection existence
    """
    if client is None:
        client = get_qdrant_client()

    try:
        return client.collection_exists(collection_name=collection_name)
    except Exception as e:
        logger.error(
            "collection_exists_check_failed",
            collection_name=collection_name,
            error=str(e),
        )
        raise QdrantConnectionError(
            f"Failed to check if collection '{collection_name}' exists: {e}"
        ) from e


def get_collection_info(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    client: Optional[QdrantClient] = None,
) -> models.CollectionInfo:
    """Get collection information including configuration and stats.

    Args:
        collection_name: Name of collection
        client: Optional QdrantClient instance (uses global if None)

    Returns:
        CollectionInfo with configuration and statistics

    Raises:
        CollectionError: If collection doesn't exist or retrieval fails
    """
    if client is None:
        client = get_qdrant_client()

    try:
        return client.get_collection(collection_name=collection_name)
    except Exception as e:
        logger.error(
            "get_collection_info_failed",
            collection_name=collection_name,
            error=str(e),
        )
        raise CollectionError(
            f"Failed to get info for collection '{collection_name}': {e}"
        ) from e
