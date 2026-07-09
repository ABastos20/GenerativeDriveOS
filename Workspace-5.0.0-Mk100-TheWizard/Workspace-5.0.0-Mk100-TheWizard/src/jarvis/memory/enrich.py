"""Offline enrichment jobs for knowledge chunks.

This module provides an enrichment pipeline that:
- Iterates over Qdrant points in the knowledge collection
- Uses an LLM to generate a short summary, bullet-style facts, tags, and doc_type
- Writes those enrichment fields back into the Qdrant payload

The enricher is pluggable so tests can inject a deterministic implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

import structlog
from qdrant_client import QdrantClient

from jarvis.database import qdrant as qdrant_db
from jarvis.llm.client import LLMResponse, call_llm

logger = structlog.get_logger(__name__)


@dataclass
class ChunkEnrichment:
    """Enrichment result for a single knowledge chunk."""

    summary: str
    facts: List[str]
    tags: List[str]
    doc_type: str


EnricherFn = Callable[[str, Dict[str, Any]], ChunkEnrichment]


def _default_enricher(
    text: str,
    payload: Dict[str, Any],
    provider: str = "perplexity",
    model: Optional[str] = None,
) -> ChunkEnrichment:
    """LLM-based enricher used by the enrichment job.

    The prompt is intentionally strict and JSON-only to keep parsing robust.
    """
    source_file = str(payload.get("source_file") or "")
    section = str(payload.get("section") or "")
    doc_primary = str(payload.get("doc_primary_domain") or "").strip()
    doc_tags = [str(t).strip() for t in (payload.get("doc_tags") or []) if str(t).strip()]
    primary_domain = str(payload.get("primary_domain") or "").strip()
    domains = [str(d).strip() for d in (payload.get("domains") or []) if str(d).strip()]

    system = (
        "You are an enrichment engine for a knowledge base. "
        "Given a text chunk (and optional source path), you MUST return:\n"
        '- summary: 1–3 sentences, plain text\n'
        "- facts: 3–10 short bullet-style facts (strings)\n"
        "- tags: 3–10 short tags (snake_case or kebab-case)\n"
        "- doc_type: one of: note, spec, log, email, legal, financial, article, other\n\n"
        "Respond ONLY with a single JSON object, no markdown, no commentary."
    )

    # Lightweight metadata header to give the LLM document context without
    # blowing up the prompt size.
    meta_lines = []
    if doc_primary:
        meta_lines.append(f"- doc_primary_domain: {doc_primary}")
    if doc_tags:
        meta_lines.append(f"- doc_tags: {', '.join(doc_tags[:10])}")
    if primary_domain:
        meta_lines.append(f"- chunk_primary_domain: {primary_domain}")
    if domains:
        meta_lines.append(f"- chunk_domains: {', '.join(domains[:5])}")
    if source_file:
        meta_lines.append(f"- source_file: {source_file}")
    if section:
        meta_lines.append(f"- section: {section}")

    metadata_block = ""
    if meta_lines:
        metadata_block = "Metadata:\n" + "\n".join(meta_lines) + "\n\n"

    prompt = (
        "Enrich the following text chunk for downstream retrieval and analytics.\n\n"
        f"{metadata_block}"
        "Text chunk:\n"
        "----------------\n"
        f"{text[:4000]}\n"
        "----------------\n"
        "Return JSON with exactly these fields:\n"
        '{\n'
        '  "summary": "string",\n'
        '  "facts": ["string", ...],\n'
        '  "tags": ["string", ...],\n'
        '  "doc_type": "note|spec|log|email|legal|financial|article|other"\n'
        "}\n"
    )

    llm_response: LLMResponse = call_llm(
        prompt=prompt,
        system=system,
        provider=provider,
        model=model or "",
        max_tokens=512,
    )

    import json

    try:
        data = json.loads(llm_response.content)
    except json.JSONDecodeError:
        logger.warning(
            "chunk_enrichment_parse_failed",
            raw_response=llm_response.content[:200],
        )
        # Fallback: attach a trivial summary so retrieval still works.
        return ChunkEnrichment(
            summary=text[:280],
            facts=[],
            tags=[],
            doc_type="other",
        )

    summary = str(data.get("summary") or "").strip() or text[:280]
    facts = [str(f).strip() for f in data.get("facts") or [] if str(f).strip()]
    tags = [str(t).strip() for t in data.get("tags") or [] if str(t).strip()]
    doc_type = str(data.get("doc_type") or "other").strip() or "other"

    return ChunkEnrichment(
        summary=summary,
        facts=facts,
        tags=tags,
        doc_type=doc_type,
    )


@dataclass
class EnrichmentJobResult:
    """Summary of an enrichment job run."""

    collection_name: str
    points_processed: int
    points_enriched: int


def _should_process_point(
    payload: Dict[str, Any],
    domains: Optional[Sequence[str]],
    skip_if_present: bool,
) -> tuple[bool, Optional[str]]:
    """Check if point should be processed.
    
    Returns:
        (should_process, text) where text is None if should not process
    """
    text = str(payload.get("text") or "").strip()
    if not text:
        return False, None
    
    if domains is not None:
        domain_value = str(payload.get("domain") or "")
        if domain_value not in domains:
            return False, None
    
    if skip_if_present and payload.get("summary"):
        return False, None
    
    return True, text


def _update_point_payload(
    client: QdrantClient,
    collection_name: str,
    point_id: Any,
    enrichment: ChunkEnrichment,
) -> bool:
    """Update point payload with enrichment data.
    
    Returns:
        True if successful, False otherwise
    """
    update_fields: Dict[str, Any] = {
        "summary": enrichment.summary,
        "facts": enrichment.facts,
        "tags": enrichment.tags,
        "doc_type": enrichment.doc_type,
    }
    
    try:
        client.set_payload(
            collection_name=collection_name,
            payload=update_fields,
            points=[point_id],
        )
        return True
    except Exception as exc:  # pragma: no cover - network errors
        logger.warning(
            "enrichment_set_payload_failed",
            point_id=str(point_id),
            error=str(exc),
        )
        return False


def enrich_collection_chunks(
    collection_name: str = qdrant_db.DEFAULT_COLLECTION_NAME,
    *,
    provider: str = "perplexity",
    model: Optional[str] = None,
    limit: Optional[int] = None,
    batch_size: int = 32,
    dry_run: bool = False,
    skip_if_present: bool = True,
    enricher: Optional[EnricherFn] = None,
    client: Optional[QdrantClient] = None,
    domains: Optional[Sequence[str]] = None,
) -> EnrichmentJobResult:
    """Run an enrichment job over a Qdrant collection.

    Args:
        collection_name: Qdrant collection to process (default: "knowledge").
        provider: LLM provider for enrichment (default: perplexity).
        model: Optional model name for the provider.
        limit: Optional max number of points to process (None = all).
        batch_size: Number of points per scroll batch.
        dry_run: If True, do not write changes; just count.
        skip_if_present: Skip points that already have a 'summary' field.
        enricher: Optional custom enricher for tests.
        client: Optional Qdrant client instance.
        domains: Optional list of payload domains to restrict processing.

    Returns:
        EnrichmentJobResult with processed/enriched counts.
    """
    client = client or qdrant_db.get_qdrant_client()

    def _enrich(text: str, payload: Dict[str, Any]) -> ChunkEnrichment:
        if enricher is not None:
            return enricher(text, payload)
        return _default_enricher(text, payload, provider=provider, model=model)

    total_processed = 0
    total_enriched = 0
    cursor: Optional[str] = None

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

            payload: Dict[str, Any] = point.payload or {}
            
            # Check if point should be processed
            should_process, text = _should_process_point(payload, domains, skip_if_present)
            if not should_process:
                total_processed += 1
                continue

            if dry_run:
                total_processed += 1
                total_enriched += 1
                continue

            try:
                enrichment = _enrich(text, payload)
            except Exception as exc:  # pragma: no cover - network/LLM errors
                logger.warning(
                    "chunk_enrichment_failed",
                    point_id=str(point.id),
                    error=str(exc),
                )
                total_processed += 1
                continue

            # Update point payload
            if _update_point_payload(client, collection_name, point.id, enrichment):
                total_enriched += 1
            
            total_processed += 1

        if limit is not None and total_processed >= limit:
            break

        if cursor is None:
            break

    logger.info(
        "enrichment_job_completed",
        collection_name=collection_name,
        points_processed=total_processed,
        points_enriched=total_enriched,
    )

    return EnrichmentJobResult(
        collection_name=collection_name,
        points_processed=total_processed,
        points_enriched=total_enriched,
    )
