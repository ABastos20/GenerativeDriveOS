"""Ingestion helper functions - semantic phase extraction.

Extracted from ingest.py to reduce ingest_file LOC below 120.
"""
from typing import List, Optional, Any, Sequence, Callable
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import structlog
from qdrant_client import models as qmodels

from jarvis.database import qdrant

logger = structlog.get_logger(__name__)

EmbeddingFn = Callable[[Sequence[str]], Sequence[Sequence[float]]]


def validate_and_load_document(path: Path) -> tuple[str, list[str]]:
    """Phase 1: Validate file, detect format, convert to markdown, chunk.
    
    Returns:
        (markdown_text, chunks)
    """
    from jarvis.memory.ingest import detect_format, convert_to_markdown, chunk_text
    
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    file_format = detect_format(path)
    markdown_text = convert_to_markdown(path, file_format)
    chunks = chunk_text(markdown_text)
    
    return markdown_text, chunks


def generate_embeddings(
    chunks: list[str],
    embed_fn: Optional[EmbeddingFn],
) -> list:
    """Phase 2: Generate embeddings and validate.
    
    Returns:
        vectors (list of embeddings)
    """
    from jarvis.memory.ingest import default_embed
    
    embed = embed_fn or default_embed
    vectors = embed(chunks)

    if len(vectors) != len(chunks):
        raise ValueError("Number of vectors does not match chunks")

    for vec in vectors:
        if len(vec) != qdrant.VECTOR_SIZE:
            raise ValueError(
                f"Vector size {len(vec)} does not match expected {qdrant.VECTOR_SIZE}"
            )
    
    return vectors


def build_chunk_payloads(
    path: Path,
    chunks: list[str],
    domain: Optional[str],
    tags: Optional[List[str]],
    meta: Optional[dict],
) -> tuple[list[dict[str, Any]], str, set[str]]:
    """Phase 3: Build chunk payloads with domain heuristics.
    
    Returns:
        (payloads, doc_primary_domain, doc_tags)
    """
    from jarvis.memory.ingest import _hash_text
    from jarvis.memory.domain_catalog import _heuristic_metadata_from_payload
    
    ingested_at = datetime.now(timezone.utc).isoformat()
    doc_key = f"file::{path}"
    default_domain = domain or path.suffix.lower().lstrip(".")
    doc_primary_domain: Optional[str] = None
    doc_tags: set[str] = set()
    
    # Merge incoming meta with defaults
    effective_meta = {
        "is_latest": True,
        "is_system": False,
        "jarvis_core": False,
        "priority": 0.5,
        "semantic_family": "docs",
    }
    if meta:
        effective_meta.update(meta)
    
    payloads: List[dict[str, Any]] = []
    
    for i, chunk in enumerate(chunks):
        digest = _hash_text(chunk)
        payload = {
            "text": chunk,
            "source_file": str(path),
            "section": path.name,
            "domain": domain or path.suffix.lower().lstrip("."),
            "ingested_at": ingested_at,
            "hash": digest,
            "chunk_index": i,
            "doc_key": doc_key,
            "total_chunks": len(chunks),
            "is_system": effective_meta.get("is_system", False),
            "jarvis_core": effective_meta.get("jarvis_core", False),
            "priority": effective_meta.get("priority", 0.5),
            "semantic_family": effective_meta.get("semantic_family", "docs"),
        }
        
        if tags:
            payload["tags"] = list(tags)
            doc_tags.update(tags)

        # Apply domain heuristics
        heuristic_meta = _heuristic_metadata_from_payload(payload, chunk)
        if heuristic_meta:
            if heuristic_meta.primary_domain:
                payload["primary_domain"] = heuristic_meta.primary_domain
                if not doc_primary_domain or doc_primary_domain == default_domain:
                    doc_primary_domain = heuristic_meta.primary_domain
            if heuristic_meta.tags:
                payload["tags"] = list(set(payload.get("tags", []) + heuristic_meta.tags))
                doc_tags.update(payload["tags"])

        payloads.append(payload)
    
    doc_primary_domain = doc_primary_domain or default_domain
    return payloads, doc_primary_domain, doc_tags


def finalize_and_persist(
    path: Path,
    markdown_text: str,
    chunks: list[str],
    vectors: list,
    payloads: list[dict[str, Any]],
    doc_primary_domain: str,
    doc_tags: set[str],
    meta: Optional[dict],
    collection_name: str,
    client: Any,
) -> tuple[int, int]:
    """Phase 4: Finalize metadata, upsert document, create points.
    
    Returns:
        (chunks_count, points_written)
    """
    from jarvis.memory.ingest import _upsert_document
    
    doc_key = f"file::{path}"
    doc_metadata = {"total_chunks": len(chunks)}
    if doc_tags:
        doc_metadata["tags"] = sorted(doc_tags)

    # Upsert full document to Postgres
    # Ensure structural metadata (is_system, etc.) is persisted
    if meta:
        doc_metadata.update({
            k: v for k, v in meta.items() 
            if k in {"is_system", "jarvis_core", "priority", "semantic_family"}
        })

    _, doc_version = _upsert_document(
        doc_key=doc_key,
        content=markdown_text,
        source_file=str(path),
        domain=doc_primary_domain,
        metadata=doc_metadata,
    )

    # Merge meta defaults for is_latest
    effective_meta = {"is_latest": True}
    if meta:
        effective_meta.update(meta)

    # Finalize payloads and create points
    points: List[qmodels.PointStruct] = []
    for payload, vector in zip(payloads, vectors):
        payload["doc_primary_domain"] = doc_primary_domain
        payload["domain"] = payload.get("primary_domain") or payload.get("domain") or doc_primary_domain
        if doc_tags:
            payload["tags"] = sorted(set(payload.get("tags", []) + list(doc_tags)))
        
        payload["version"] = doc_version
        payload["is_latest"] = effective_meta.get("is_latest", True)

        points.append(
            qmodels.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload=payload,
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )

    logger.info(
        "ingest_completed",
        path=str(path),
        collection=collection_name,
        chunks=len(chunks),
        points=len(points),
        primary_domain=points[0].payload.get("primary_domain") if points else None,
    )

    return len(chunks), len(points)
