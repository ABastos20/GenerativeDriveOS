"""Catalog helpers for document-level aggregation.

Extracted from domain_catalog.py to reduce catalog_documents LOC.
"""
from typing import Any, Dict, List, Optional
from collections import Counter
from dataclasses import dataclass, field

import structlog
from qdrant_client import QdrantClient

logger = structlog.get_logger(__name__)


@dataclass
class DocumentAggregation:
    """In-memory aggregation for a single logical document."""
    
    key: str
    source_file: Optional[str] = None
    conversation_id: Optional[str] = None
    domain_counts: Counter[str] = field(default_factory=Counter)
    tags: set[str] = field(default_factory=set)
    first_seen: Optional[float] = None
    last_seen: Optional[float] = None
    step_count: int = 0


def aggregate_document_chunks(
    client: QdrantClient,
    collection_name: str,
    batch_size: int,
    limit: Optional[int],
) -> Dict[str, DocumentAggregation]:
    """Phase 1: Aggregate per-document statistics from chunks.
    
    Returns:
        Dict mapping doc_key to DocumentAggregation
    """
    from jarvis.memory.domain_catalog import _get_document_key
    from datetime import datetime
    
    docs: Dict[str, DocumentAggregation] = {}
    total_points_seen = 0
    cursor: Optional[str] = None
    
    def _to_ts(value: Any) -> Optional[float]:
        """Convert value to timestamp."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except Exception:
                return None
        return None
    
    while True:
        points, cursor = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            with_payload=True,
            with_vectors=False,
            offset=cursor,
        )
        if not points:
            break

        for point in points:
            if limit is not None and total_points_seen >= limit:
                break

            payload: Dict[str, Any] = point.payload or {}
            doc_key = _get_document_key(payload)
            if not doc_key:
                total_points_seen += 1
                continue

            # Extract timestamps
            create_ts = _to_ts(payload.get("create_time"))
            ingest_ts = _to_ts(payload.get("ingested_at"))
            candidates: List[float] = [t for t in [create_ts, ingest_ts] if t is not None]

            # Get or create aggregation
            agg = docs.get(doc_key)
            if agg is None:
                agg = DocumentAggregation(
                    key=doc_key,
                    source_file=(payload.get("source_file") or "").strip() or None,
                    conversation_id=(payload.get("conversation_id") or "").strip() or None,
                )
                docs[doc_key] = agg

            # Update timestamps
            if candidates:
                ts_min, ts_max = min(candidates), max(candidates)
                if agg.first_seen is None or ts_min < agg.first_seen:
                    agg.first_seen = ts_min
                if agg.last_seen is None or ts_max > agg.last_seen:
                    agg.last_seen = ts_max

            # Aggregate domain and tags
            domain_key = str(
                payload.get("primary_domain") or payload.get("domain") or "generic.unknown"
            ).strip()
            if domain_key:
                agg.domain_counts[domain_key] += 1

            for tag in payload.get("tags") or []:
                if tag:
                    agg.tags.add(str(tag))

            agg.step_count += 1
            total_points_seen += 1

        if limit is not None and total_points_seen >= limit:
            break
        if cursor is None:
            break
    
    return docs


def derive_document_profiles(
    docs: Dict[str, DocumentAggregation]
) -> tuple[Dict[str, str], Dict[str, List[str]], Dict[str, Optional[float]], Dict[str, Optional[float]], Dict[str, int]]:
    """Phase 2: Derive final document profiles from aggregations.
    
    Returns:
        (doc_primary, doc_tags, doc_first_seen, doc_last_seen, doc_step_count)
    """
    from jarvis.memory.domain_catalog import _derive_doc_primary_domain
    
    doc_primary: Dict[str, str] = {}
    doc_tags: Dict[str, List[str]] = {}
    doc_first_seen: Dict[str, Optional[float]] = {}
    doc_last_seen: Dict[str, Optional[float]] = {}
    doc_step_count: Dict[str, int] = {}

    for key, agg in docs.items():
        primary = _derive_doc_primary_domain(agg.domain_counts)
        doc_primary[key] = primary
        doc_tags[key] = list(agg.tags)[:20] if agg.tags else []
        doc_first_seen[key] = agg.first_seen
        doc_last_seen[key] = agg.last_seen
        doc_step_count[key] = agg.step_count
    
    return doc_primary, doc_tags, doc_first_seen, doc_last_seen, doc_step_count


def propagate_to_chunks(
    client: QdrantClient,
    collection_name: str,
    batch_size: int,
    limit: Optional[int],
    doc_primary: Dict[str, str],
    doc_tags: Dict[str, List[str]],
    doc_first_seen: Dict[str, Optional[float]],
    doc_last_seen: Dict[str, Optional[float]],
    doc_step_count: Dict[str, int],
    dry_run: bool,
) -> int:
    """Phase 3: Propagate document metadata back to chunks.
    
    Returns:
        Number of points updated
    """
    from jarvis.memory.domain_catalog import _get_document_key
    
    points_updated = 0
    cursor = None
    total_processed = 0

    while True:
        points, cursor = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            with_payload=True,
            with_vectors=False,
            offset=cursor,
        )
        if not points:
            break

        for point in points:
            if limit is not None and total_processed >= limit:
                break

            payload = point.payload or {}
            doc_key = _get_document_key(payload)
            if not doc_key or doc_key not in doc_primary:
                total_processed += 1
                continue

            primary = payload.get("primary_domain")
            domains = list(payload.get("domains") or [])
            chunk_tags = list(payload.get("tags") or [])

            doc_primary_domain = doc_primary[doc_key]
            doc_tag_list = doc_tags.get(doc_key, [])
            doc_first = doc_first_seen.get(doc_key)
            doc_last = doc_last_seen.get(doc_key)
            doc_steps = doc_step_count.get(doc_key, 0)

            # Inherit from document if no meaningful primary
            if not primary or str(primary).strip() == "generic.unknown":
                primary = doc_primary_domain

            if primary and primary not in domains:
                domains = [primary] + [d for d in domains if d != primary]

            # Merge tags
            merged_tags = list({*chunk_tags, *doc_tag_list})
            if len(merged_tags) > 25:
                merged_tags = merged_tags[:25]

            new_fields: Dict[str, Any] = {
                "doc_key": doc_key,
                "doc_primary_domain": doc_primary_domain,
                "doc_tags": doc_tag_list,
                "doc_first_seen": doc_first,
                "doc_last_seen": doc_last,
                "doc_step_count": doc_steps,
                "primary_domain": primary,
                "domains": domains,
                "tags": merged_tags,
            }

            if dry_run:
                total_processed += 1
                continue

            try:
                client.set_payload(
                    collection_name=collection_name,
                    payload=new_fields,
                    points=[point.id],
                )
                points_updated += 1
            except Exception as exc:
                logger.warning(
                    "document_catalog_set_payload_failed",
                    point_id=str(point.id),
                    error=str(exc),
                )

            total_processed += 1

        if limit is not None and total_processed >= limit:
            break
        if cursor is None:
            break
    
    return points_updated
