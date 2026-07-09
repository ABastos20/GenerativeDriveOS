"""Domain cataloging and classification for Jarvis memory.

This module implements an offline catalog job that:
- Iterates over Qdrant chunks in the knowledge collection
- Uses an LLM to classify each chunk into one or more domains
- Updates Qdrant payload metadata with domain tags
- Ensures discovered domains are recorded in PostgreSQL (knowledge_domains table)

The LLM classifier is pluggable so tests can inject a deterministic
classifier without making network calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from collections import Counter, defaultdict
import os

import structlog
from qdrant_client import QdrantClient

from jarvis.database import qdrant as qdrant_db
from jarvis.database.models import KnowledgeDomain
from jarvis.database.postgres import get_session
from jarvis.llm.client import LLMResponse, call_llm
from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP, DIRECT_DOMAIN_MAP, GD_KEYWORD_TAGS

logger = structlog.get_logger(__name__)


@dataclass
class ChunkDomainMetadata:
    """Classification result for a single knowledge chunk."""

    primary_domain: str
    secondary_domains: List[str]
    rick_personas: List[str]
    tags: List[str]
    confidence: float


ClassifierFn = Callable[[str], ChunkDomainMetadata]


def _normalize_window_text(text: str) -> str:
    """Normalize text before sending to the LLM.

    We strip leading/trailing whitespace, collapse all runs of whitespace
    (spaces, tabs, newlines) into single spaces, and return a single-line
    representation. This keeps content but makes prompts more compact and
    predictable for token counting.
    """
    if not text:
        return ""
    # split/join collapses all whitespace (including \n, \t) into single spaces.
    return " ".join(text.split())


def _classify_window(
    text: str,
    provider: str,
    model: Optional[str],
) -> ChunkDomainMetadata:
    """Classify a single text window into domains/personas."""
    # Log what we are sending to the LLM in a compact, privacy‑aware way.
    logger.info(
        "domain_classification_call",
        provider=provider,
        model=model,
        text_chars=len(text),
        text_preview=text[:160],
    )

    system = (
        "You are a domain classifier for the Jarvis knowledge base. "
        "Given a text chunk, you must assign:\n"
        "- primary_domain: a short stable key like 'architecture.core', 'memory.rag', "
        "'history.modern', 'philosophy.ethics', 'gdrive.product', 'gdrive.infra'\n"
        "- secondary_domains: up to 3 additional domain keys (can be empty)\n"
        "- rick_personas: names of personas that should own this content "
        "(e.g. 'Architect Rick', 'Dev Rick', 'Ops Rick', 'PM Rick'). Can be empty.\n"
        "- tags: 3-7 short keywords for filtering (snake_case or kebab-case)\n"
        "- confidence: float between 0.0 and 1.0 reflecting how confident you are\n\n"
        "Respond ONLY with a single JSON object, no markdown, no extra text."
    )

    prompt = (
        "Classify the following text chunk into knowledge domains and personas.\n\n"
        "Text chunk:\n"
        "----------------\n"
        f"{text}\n"
        "----------------\n"
        "Return JSON with exactly these fields:\n"
        '{\n'
        '  "primary_domain": "string",\n'
        '  "secondary_domains": ["string", ...],\n'
        '  "rick_personas": ["string", ...],\n'
        '  "tags": ["string", ...],\n'
        '  "confidence": 0.0\n'
        "}\n"
    )

    # Choose a sane default model when one is not provided.
    effective_model = model
    if provider == "google-ai" and not effective_model:
        # Align with GoogleAIProvider default.
        effective_model = "gemini-2.5"

    llm_response: LLMResponse = call_llm(
        prompt=prompt,
        system=system,
        provider=provider,
        model=effective_model or "",
        max_tokens=512,
    )

    import json

    try:
        data = json.loads(llm_response.content)
    except json.JSONDecodeError:
        logger.warning(
            "domain_classification_parse_failed",
            raw_response=llm_response.content[:200],
        )
        # Fallback: put everything in a generic bucket
        return ChunkDomainMetadata(
            primary_domain="generic.unknown",
            secondary_domains=[],
            rick_personas=[],
            tags=[],
            confidence=0.0,
        )

    primary = str(data.get("primary_domain") or "generic.unknown").strip() or "generic.unknown"
    secondary = [str(d).strip() for d in data.get("secondary_domains") or [] if str(d).strip()]
    personas = [str(p).strip() for p in data.get("rick_personas") or [] if str(p).strip()]
    tags = [str(t).strip() for t in data.get("tags") or [] if str(t).strip()]

    try:
        confidence = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0

    return ChunkDomainMetadata(
        primary_domain=primary,
        secondary_domains=secondary,
        rick_personas=personas,
        tags=tags,
        confidence=confidence,
    )


def _heuristic_metadata_from_payload(
    payload: Dict[str, Any],
    text: str,
) -> Optional[ChunkDomainMetadata]:
    """Best-effort, zero-LLM domain classification from existing payload fields.

    This is used as a fast baseline so that the LLM is only called for
    chunks where we truly lack structure.
    """
    from jarvis.memory.domain_classifiers import (
        classify_by_path,
        classify_by_title,
        classify_by_section,
        classify_by_text_content,
        get_extension_default,
    )
    
    domain = (payload.get("domain") or "").strip()
    source_file = (payload.get("source_file") or "").strip()
    section = (payload.get("section") or "").strip()
    title = (payload.get("title") or "").strip()
    chunk_index = payload.get("chunk_index")

    primary: Optional[str] = None
    tags: List[str] = []
    doc_type_hint: Optional[str] = None

    # Direct domain mappings
    mapped = DIRECT_DOMAIN_MAP.get(domain)
    if mapped:
        primary = mapped

    # Path-based classification
    if not primary and source_file:
        path_primary, path_tags = classify_by_path(source_file)
        if path_primary:
            primary = path_primary
        tags.extend(path_tags)
        
        # Extension fallback
        if not primary:
            doc_type_hint = get_extension_default(source_file)

    # Title-based classification
    if not primary and title:
        title_primary, title_tags = classify_by_title(title)
        if title_primary:
            primary = title_primary
        tags.extend(title_tags)

    # Section-based classification
    if not primary and section:
        primary = classify_by_section(section)

    # Text content analysis
    text_primary, text_tags = classify_by_text_content(source_file, section, title, text, primary)
    if text_primary:
        primary = text_primary
    tags.extend(text_tags)

    # Fallback to doc type hint
    if not primary and doc_type_hint:
        primary = doc_type_hint

    # Chunk position hint
    if chunk_index in (0, 1):
        tags.append("doc_header")

    if not primary:
        return None

    logger.info(
        "domain_classification_heuristic",
        primary_domain=primary,
        domain=domain,
        source_file=source_file,
        title=title,
    )

    return ChunkDomainMetadata(
        primary_domain=primary,
        secondary_domains=[],
        rick_personas=[],
        tags=tags,
        confidence=0.5,
    )


def _default_classifier(
    text: str,
    provider: str = "google-ai",
    model: Optional[str] = None,
) -> ChunkDomainMetadata:
    """LLM-based classifier used by the catalog job.

    For long chunks, this will classify multiple windows and aggregate
    the results so we don't overrun the model's effective context.
    """
    # Windowing parameters are configurable to allow tuning without code changes.
    # Default window is intentionally generous; callers can shrink it via env.
    window_chars = int(os.getenv("JARVIS_CATALOG_WINDOW_CHARS", "2000"))
    max_windows = int(os.getenv("JARVIS_CATALOG_MAX_WINDOWS", "3"))

    clean_text = _normalize_window_text(text or "")

    # Short chunks: classify directly (backwards compatible behaviour for tests).
    if len(clean_text) <= window_chars:
        return _classify_window(clean_text, provider=provider, model=model)

    # Long chunks: split into windows and classify each window separately.
    windows: List[str] = []
    max_len = window_chars * max_windows
    truncated = clean_text[:max_len]
    for start in range(0, len(truncated), window_chars):
        windows.append(truncated[start : start + window_chars])

    metas: List[ChunkDomainMetadata] = []
    for w in windows:
        meta = _classify_window(w, provider=provider, model=model)
        metas.append(meta)

    if not metas:
        return ChunkDomainMetadata(
            primary_domain="generic.unknown",
            secondary_domains=[],
            rick_personas=[],
            tags=[],
            confidence=0.0,
        )

    # Primary domain: majority vote over non-generic keys if possible.
    non_generic = [
        m.primary_domain
        for m in metas
        if m.primary_domain and m.primary_domain != "generic.unknown"
    ]
    if non_generic:
        primary = Counter(non_generic).most_common(1)[0][0]
    else:
        primary = metas[0].primary_domain or "generic.unknown"

    secondary_set = set()
    personas_set = set()
    tags_set = set()
    confidences: List[float] = []

    for m in metas:
        for d in m.secondary_domains:
            if d and d != primary:
                secondary_set.add(d)
        for p in m.rick_personas:
            if p:
                personas_set.add(p)
        for t in m.tags:
            if t:
                tags_set.add(t)
        confidences.append(float(m.confidence))

    # Trim to reasonable sizes to avoid unbounded growth.
    secondary_domains = list(secondary_set)[:5]
    rick_personas = list(personas_set)[:5]
    tags = list(tags_set)[:10]
    confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return ChunkDomainMetadata(
        primary_domain=primary,
        secondary_domains=secondary_domains,
        rick_personas=rick_personas,
        tags=tags,
        confidence=confidence,
    )


@dataclass
class DomainCatalogResult:
    """Summary of a catalog job run."""

    collection_name: str
    points_processed: int
    domains_created: int


@dataclass
class DocumentCatalogResult:
    """Summary of a document-level catalog run."""

    collection_name: str
    documents_processed: int
    points_updated: int


def _ensure_domains(domain_keys: Sequence[str], kind: str = "generic") -> int:
    """Ensure domain keys exist in the knowledge_domains table.

    Returns:
        Number of newly created domains.
    """
    unique_keys = {k for k in domain_keys if k}
    if not unique_keys:
        return 0

    created = 0
    with get_session() as session:
        existing = (
            session.query(KnowledgeDomain.key)
            .filter(KnowledgeDomain.key.in_(list(unique_keys)))
            .all()
        )
        existing_keys = {row[0] for row in existing}

        for key in unique_keys - existing_keys:
            domain = KnowledgeDomain(
                key=key,
                label=key.replace(".", " / "),
                kind=kind,
            )
            session.add(domain)
            created += 1

    return created


def _get_document_key(payload: Dict[str, Any]) -> Optional[str]:
    """Return a stable document key for a chunk payload.

    We prefer filesystem documents (source_file) but fall back to
    conversation_id for GPT exports. This key is stored in the payload
    as doc_key for easier debugging and analytics.
    """
    source_file = (payload.get("source_file") or "").strip()
    conversation_id = (payload.get("conversation_id") or "").strip()

    if source_file:
        return f"file::{source_file}"
    if conversation_id:
        return f"conv::{conversation_id}"
    return None


@dataclass
class _DocumentAggregation:
    """In-memory aggregation for a single logical document."""

    key: str
    source_file: Optional[str] = None
    conversation_id: Optional[str] = None
    domain_counts: Counter[str] = field(default_factory=Counter)
    tags: set[str] = field(default_factory=set)
    first_seen: Optional[float] = None
    last_seen: Optional[float] = None
    step_count: int = 0


def _derive_doc_primary_domain(domain_counts: Counter[str]) -> str:
    """Pick a primary domain for a document from chunk-level domains."""
    if not domain_counts:
        return "generic.unknown"

    # Prefer non-structural domains when available.
    non_structural: Dict[str, int] = {}
    for key, count in domain_counts.items():
        if not key:
            continue
        if key.startswith("docs.") or key == "generic.unknown":
            continue
        non_structural[key] = count

    candidates = non_structural or dict(domain_counts)
    return max(candidates.items(), key=lambda kv: kv[1])[0]


def catalog_documents(
    collection_name: str = qdrant_db.DEFAULT_COLLECTION_NAME,
    limit: Optional[int] = None,
    batch_size: int = 512,
    dry_run: bool = False,
    client: Optional[QdrantClient] = None,
) -> DocumentCatalogResult:
    """Build document-level profiles and propagate them to chunks.

    This job:
    - Groups chunks by document (source_file or conversation_id)
    - Computes a doc_primary_domain via majority vote over chunk domains
    - Aggregates chunk tags into doc_tags
    - Writes doc_key, doc_primary_domain, doc_tags into chunk payloads
    - Optionally fills missing primary_domain from the document profile

    No LLM calls are made; this is a lightweight, offline aggregation
    pass that refines the catalog created by catalog_collection_domains.
    """
    from jarvis.memory.catalog_helpers import (
        aggregate_document_chunks,
        derive_document_profiles,
        propagate_to_chunks,
    )
    
    client = client or qdrant_db.get_qdrant_client()

    # Phase 1: Aggregate per-document statistics
    docs = aggregate_document_chunks(client, collection_name, batch_size, limit)

    # Phase 2: Derive final document profiles
    doc_primary, doc_tags, doc_first_seen, doc_last_seen, doc_step_count = derive_document_profiles(docs)

    # Phase 3: Propagate document metadata back to chunks
    points_updated = propagate_to_chunks(
        client, collection_name, batch_size, limit,
        doc_primary, doc_tags, doc_first_seen, doc_last_seen, doc_step_count,
        dry_run
    )

    logger.info(
        "document_catalog_completed",
        collection_name=collection_name,
        documents_processed=len(docs),
        points_updated=points_updated,
    )

    return DocumentCatalogResult(
        collection_name=collection_name,
        documents_processed=len(docs),
        points_written=points_updated,
    )


def catalog_collection_domains(
    collection_name: str = qdrant_db.DEFAULT_COLLECTION_NAME,
    provider: str = "google-ai",
    model: Optional[str] = None,
    limit: Optional[int] = None,
    batch_size: int = 64,
    dry_run: bool = False,
    classifier: Optional[ClassifierFn] = None,
    client: Optional[QdrantClient] = None,
) -> DomainCatalogResult:
    """Run a catalog job over a Qdrant collection and classify chunk domains.

    Args:
        collection_name: Qdrant collection to process (default: "knowledge")
        provider: LLM provider to use for classification (default: google-ai)
        model: Optional model name (provider specific)
        limit: Optional max number of points to process (None = all)
        batch_size: Number of points per scroll batch
        dry_run: If True, do not write any changes (log only)
        classifier: Optional custom classifier for tests
        client: Optional Qdrant client

    Returns:
        DomainCatalogResult with processed count and newly created domains.
    """
    client = client or qdrant_db.get_qdrant_client()
    classify = classifier or (lambda text: _default_classifier(text, provider=provider, model=model))

    total_processed = 0
    total_created_domains = 0

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
            text = str(payload.get("text") or "").strip()
            if not text:
                continue

            # In dry-run mode we only count points; no LLM calls, no DB/Qdrant writes.
            if dry_run:
                total_processed += 1
                continue

            # First try cheap, deterministic heuristics based on existing metadata + text search.
            meta = _heuristic_metadata_from_payload(payload, text)
            # If heuristics can't decide, fall back to LLM classifier.
            if meta is None:
                meta = classify(text)

            # Update domains table
            all_domain_keys = [meta.primary_domain] + meta.secondary_domains
            total_created_domains += _ensure_domains(all_domain_keys)

            # Update Qdrant payload metadata
            new_fields: Dict[str, Any] = {
                "primary_domain": meta.primary_domain,
                "domains": all_domain_keys,
                "rick_personas": meta.rick_personas,
                "tags": meta.tags,
                "domain_confidence": meta.confidence,
            }
            try:
                client.set_payload(
                    collection_name=collection_name,
                    payload=new_fields,
                    points=[point.id],
                )
            except Exception as exc:  # pragma: no cover - network errors
                logger.warning(
                    "domain_catalog_set_payload_failed",
                    point_id=str(point.id),
                    error=str(exc),
                )

            total_processed += 1

        if limit is not None and total_processed >= limit:
            break

        if cursor is None:
            break

    logger.info(
        "domain_catalog_completed",
        collection_name=collection_name,
        points_processed=total_processed,
        new_domains=total_created_domains,
    )

    return DomainCatalogResult(
        collection_name=collection_name,
        points_processed=total_processed,
        domains_created=total_created_domains,
    )
