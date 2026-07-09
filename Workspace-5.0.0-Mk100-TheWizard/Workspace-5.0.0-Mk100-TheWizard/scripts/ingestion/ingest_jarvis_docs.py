#!/usr/bin/env python3
"""Ingest Jarvis core documents into memory.

Usage:
    python scripts/ingest_jarvis_docs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog

from jarvis.memory.ingest import ingest_file

logger = structlog.get_logger(__name__)


def main() -> int:
    """Ingest Jarvis core documents."""
    docs_dir = Path("docs/jarvis")

    core_docs = [
        ("persona.md", "jarvis-core"),
        ("operating-manual.md", "jarvis-core"),
    ]

    total_chunks = 0

    for doc_name, domain in core_docs:
        doc_path = docs_dir / doc_name

        if not doc_path.exists():
            logger.warning("document_not_found", path=str(doc_path))
            continue

        logger.info("ingesting_document", path=str(doc_path), domain=domain)

        try:
            result = ingest_file(doc_path, domain=domain)
            total_chunks += result.chunks
            logger.info("document_ingested", path=str(doc_path), chunks=result.chunks)
        except Exception as e:
            logger.error("ingestion_failed", path=str(doc_path), error=str(e), exc_info=True)
            continue

    logger.info("jarvis_docs_ingestion_complete", total_chunks=total_chunks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
