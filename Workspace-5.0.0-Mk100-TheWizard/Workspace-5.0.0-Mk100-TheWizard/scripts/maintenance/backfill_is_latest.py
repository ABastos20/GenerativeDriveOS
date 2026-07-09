#!/usr/bin/env python3
"""Backfill is_latest flag for existing Qdrant corpus (Story 4.5.3b).

This script:
1. Scans all chunks in Qdrant grouped by doc_key
2. Identifies the freshest version per doc_key (by ingested_at or version)
3. Sets is_latest=true for freshest, false for others
4. Updates corresponding DB Document rows

Idempotent: safe to re-run.

Usage:
    python scripts/backfill_is_latest.py [--dry-run] [--collection knowledge]
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

import structlog

# Add src to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jarvis.database import qdrant
from jarvis.database.models import Document
from jarvis.database.postgres import get_session

logger = structlog.get_logger(__name__)


def parse_ingested_at(val: Any) -> Optional[datetime]:
    """Parse ingested_at from payload (ISO format string)."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def backfill_is_latest(
    collection_name: str = qdrant.DEFAULT_COLLECTION_NAME,
    dry_run: bool = False,
    batch_size: int = 100,
) -> dict[str, int]:
    """Backfill is_latest flag for existing corpus.
    
    Returns:
        Dict with counts: {"scanned", "updated_latest", "updated_stale", "docs_updated"}
    """
    client = qdrant.get_qdrant_client()
    
    # Group chunks by doc_key
    doc_chunks: dict[str, list[dict]] = defaultdict(list)
    
    logger.info("backfill_scanning_chunks", collection=collection_name)
    
    # Scroll through all points
    offset = None
    total_scanned = 0
    
    while True:
        result = client.scroll(
            collection_name=collection_name,
            scroll_filter=None,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        points, next_offset = result
        
        if not points:
            break
            
        for point in points:
            payload = point.payload or {}
            doc_key = payload.get("doc_key")
            if not doc_key:
                continue
                
            doc_chunks[doc_key].append({
                "id": point.id,
                "version": payload.get("version", 1),
                "ingested_at": parse_ingested_at(payload.get("ingested_at")),
                "is_latest": payload.get("is_latest"),
            })
        
        total_scanned += len(points)
        offset = next_offset
        
        if next_offset is None:
            break
    
    logger.info(
        "backfill_scan_complete",
        total_chunks=total_scanned,
        unique_docs=len(doc_chunks),
    )
    
    # Determine freshest per doc_key and update
    updated_latest = 0
    updated_stale = 0
    docs_in_progress = 0
    
    for doc_key, chunks in doc_chunks.items():
        # Sort by version (desc), then ingested_at (desc)
        sorted_chunks = sorted(
            chunks,
            key=lambda c: (c["version"], c["ingested_at"] or datetime.min),
            reverse=True,
        )
        
        freshest_version = sorted_chunks[0]["version"]
        
        # Prepare updates
        latest_ids = []
        stale_ids = []
        
        for chunk in sorted_chunks:
            current_is_latest = chunk.get("is_latest")
            should_be_latest = chunk["version"] == freshest_version
            
            if should_be_latest and current_is_latest is not True:
                latest_ids.append(chunk["id"])
            elif not should_be_latest and current_is_latest is not False:
                stale_ids.append(chunk["id"])
        
        if latest_ids or stale_ids:
            docs_in_progress += 1
            
            if not dry_run:
                # Update Qdrant payloads
                if latest_ids:
                    client.set_payload(
                        collection_name=collection_name,
                        payload={"is_latest": True, "version": freshest_version},
                        points=latest_ids,
                    )
                    updated_latest += len(latest_ids)
                
                if stale_ids:
                    client.set_payload(
                        collection_name=collection_name,
                        payload={"is_latest": False},
                        points=stale_ids,
                    )
                    updated_stale += len(stale_ids)
            else:
                updated_latest += len(latest_ids)
                updated_stale += len(stale_ids)
                
            logger.debug(
                "backfill_doc_processed",
                doc_key=doc_key,
                latest_count=len(latest_ids),
                stale_count=len(stale_ids),
            )
    
    # Update DB Document rows
    docs_updated = 0
    if not dry_run:
        with get_session() as session:
            # Set all documents to is_latest=True (since we only keep latest versions in DB)
            docs_updated = session.query(Document).filter(
                Document.is_latest == False  # noqa: E712
            ).update({"is_latest": True})
            session.commit()
    
    result = {
        "scanned": total_scanned,
        "updated_latest": updated_latest,
        "updated_stale": updated_stale,
        "docs_updated": docs_updated,
    }
    
    logger.info(
        "backfill_complete",
        dry_run=dry_run,
        **result,
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Backfill is_latest for existing corpus")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--collection", default=qdrant.DEFAULT_COLLECTION_NAME, help="Qdrant collection name")
    args = parser.parse_args()
    
    print(f"🔄 Backfilling is_latest flag for collection: {args.collection}")
    if args.dry_run:
        print("   (DRY RUN - no changes will be made)")
    
    result = backfill_is_latest(
        collection_name=args.collection,
        dry_run=args.dry_run,
    )
    
    print(f"\n✅ Backfill complete:")
    print(f"   - Chunks scanned: {result['scanned']}")
    print(f"   - Marked as latest: {result['updated_latest']}")
    print(f"   - Marked as stale: {result['updated_stale']}")
    print(f"   - DB docs updated: {result['docs_updated']}")


if __name__ == "__main__":
    main()
