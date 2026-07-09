#!/usr/bin/env python3
"""Initialize Qdrant collection for JARVIS knowledge base.

This script creates the 'knowledge' collection idempotently with the correct
configuration from architecture.md:
- 384-d vectors (all-MiniLM-L6-v2 embeddings)
- Cosine distance metric
- HNSW parameters: m=16, ef_construct=200, full_scan_threshold=10000

Usage:
    python scripts/init_qdrant.py
    python scripts/init_qdrant.py --collection custom_name
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog

from jarvis.database.qdrant import (
    init_collection,
    get_qdrant_client,
    collection_exists,
    get_collection_info,
    DEFAULT_COLLECTION_NAME,
)

logger = structlog.get_logger(__name__)


def main() -> int:
    """Initialize Qdrant collection."""
    parser = argparse.ArgumentParser(
        description="Initialize Qdrant collection for JARVIS knowledge base"
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Collection name (default: {DEFAULT_COLLECTION_NAME})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Connection timeout in seconds (default: 10.0)",
    )

    args = parser.parse_args()

    try:
        logger.info(
            "initializing_qdrant_collection",
            collection=args.collection,
            timeout=args.timeout,
        )

        # Get client
        client = get_qdrant_client(timeout=args.timeout)

        # Check if collection already exists
        if collection_exists(args.collection, client=client):
            logger.info(
                "collection_already_exists",
                collection=args.collection,
            )

            # Validate configuration
            info = get_collection_info(args.collection, client=client)
            logger.info(
                "collection_info",
                collection=args.collection,
                points_count=info.points_count,
                vectors_count=info.vectors_count if hasattr(info, "vectors_count") else "N/A",
                vector_size=info.config.params.vectors.size,
                distance=info.config.params.vectors.distance.value,
            )

            return 0

        # Initialize collection
        success = init_collection(collection_name=args.collection, client=client)

        if success:
            logger.info(
                "collection_initialized_successfully",
                collection=args.collection,
            )
            return 0
        else:
            logger.error(
                "collection_initialization_failed",
                collection=args.collection,
            )
            return 1

    except Exception as e:
        logger.error(
            "qdrant_initialization_error",
            collection=args.collection,
            error=str(e),
            exc_info=True,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
