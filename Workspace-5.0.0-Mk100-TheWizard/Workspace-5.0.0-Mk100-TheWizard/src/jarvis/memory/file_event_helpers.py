"""File event handling helpers - Separated for complexity compliance.

Contains file validation and processing logic extracted from JarvisFileEventHandler.
"""
from pathlib import Path
from typing import Set

import structlog

from jarvis.memory.ingest import ingest_file
from jarvis.database import qdrant as qdrant_db
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

logger = structlog.get_logger(__name__)

# Supported file extensions for ingestion
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".json", ".ipynb", ".py", ".js", ".ts"}


def is_supported_file(file_path: str) -> bool:
    """Check if file type is supported for ingestion."""
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS


def remove_from_qdrant(file_path: str, collection_name: str) -> None:
    """Remove chunks associated with a file from Qdrant."""
    try:
        client: QdrantClient = qdrant_db.get_qdrant_client()
        file_path_normalized = str(Path(file_path))
        logger.info("removing_file_from_qdrant", path=file_path_normalized)

        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="source_file",
                        match=MatchValue(value=file_path_normalized),
                    )
                ]
            ),
        )
        logger.info("file_removed_from_qdrant", path=file_path_normalized)
    except Exception as e:
        logger.error("qdrant_removal_error", path=file_path, error=str(e))


def reingest_file(file_path: str, collection_name: str) -> None:
    """Re-ingest a modified file."""
    logger.info("reingesting_file", path=file_path)

    # First, remove old chunks
    remove_from_qdrant(file_path, collection_name)

    # Then, ingest new version
    path = Path(file_path)
    if path.exists():
        ingest_file(file_path=path, collection_name=collection_name, reprocess=True)
        logger.info("file_reingested", path=file_path)


def process_files_batch(files: list, collection_name: str) -> None:
    """Process a batch of pending files."""
    logger.info("processing_pending_files", count=len(files))
    for file_path in files:
        try:
            reingest_file(file_path, collection_name)
        except Exception as e:
            logger.error("reingest_error", path=file_path, error=str(e))
