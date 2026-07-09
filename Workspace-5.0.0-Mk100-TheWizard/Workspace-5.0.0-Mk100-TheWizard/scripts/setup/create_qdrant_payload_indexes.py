"""Create Qdrant payload indexes for high-performance filtering.

Architect-recommended payload indexes for massive speedup (120ms → 8-15ms).
Run this after collection is created and has data.
"""
from __future__ import annotations

import structlog
from qdrant_client.models import PayloadSchemaType

from jarvis.database.qdrant import get_qdrant_client, DEFAULT_COLLECTION_NAME

logger = structlog.get_logger(__name__)


def create_payload_indexes(collection_name: str = DEFAULT_COLLECTION_NAME) -> None:
    """Create payload indexes for domain, doc_step, and created_at filters.
    
    These indexes provide massive performance improvements for filtered searches:
    - domain filter: Fast filtering by knowledge domain
    - doc_step filter: Fast filtering by document structure
    - created_at filter: Fast temporal filtering
    
    Expected speedup: 120ms → 8-15ms (per Architect)
    """
    client = get_qdrant_client()
    
    indexes = [
        ("domain", PayloadSchemaType.KEYWORD, "Domain classification filter"),
        ("doc_step", PayloadSchemaType.INTEGER, "Document step/section filter"),
        ("created_at", PayloadSchemaType.DATETIME, "Temporal recency filter"),
    ]
    
    logger.info("creating_qdrant_payload_indexes", collection=collection_name, count=len(indexes))
    
    for field_name, field_schema, description in indexes:
        try:
            logger.info(
                "creating_payload_index",
                field=field_name,
                schema=field_schema,
                description=description
            )
            
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema,
                wait=True,
            )
            
            logger.info("payload_index_created", field=field_name)
            
        except Exception as e:
            # Index might already exist
            logger.warning(
                "payload_index_creation_failed",
                field=field_name,
                error=str(e),
                note="Index may already exist"
            )
    
    logger.info("payload_indexes_complete", collection=collection_name)


if __name__ == "__main__":
    import sys
    
    collection = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COLLECTION_NAME
    
    logger.info("starting_payload_index_creation", collection=collection)
    create_payload_indexes(collection)
    logger.info("payload_index_creation_complete")
