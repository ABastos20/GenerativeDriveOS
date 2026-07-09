"""Document ingestion pipeline for JARVIS memory.

Responsibilities:
- Format detection and Markdown normalization (via pypandoc when needed)
- Hybrid chunking for embeddings
- Embedding generation (default SentenceTransformer; pluggable for tests)
- Qdrant upsert with structured payload metadata
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Sequence
from uuid import uuid4

import structlog
from qdrant_client.http import models as qmodels
from sqlalchemy.dialects.postgresql import insert

from jarvis.database import qdrant
from jarvis.database.models import Base, Document
from jarvis.database.postgres import get_engine, get_session

logger = structlog.get_logger(__name__)

EmbeddingFn = Callable[[Sequence[str]], Sequence[Sequence[float]]]

_MODEL = None


def _load_model():
    """Lazy-load the embedding model."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def detect_format(path: Path) -> str:
    """Detect file format from extension."""
    ext = path.suffix.lower()
    if ext in {".md", ".markdown", ".txt"}:
        return "markdown"
    if ext == ".pdf":
        return "pdf"
    if ext in {".htm", ".html"}:
        return "html"
    raise ValueError(f"Unsupported file type: {ext}")


def convert_to_markdown(path: Path, file_format: str) -> str:
    """Convert a document to Markdown text."""
    if file_format == "markdown":
        return path.read_text(encoding="utf-8")

    if file_format == "pdf":
        # Pandoc cannot read PDFs directly; use a lightweight PDF text extractor instead.
        try:
            from PyPDF2 import PdfReader  # type: ignore[import]
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("PyPDF2 is required to convert PDF files") from exc

        try:
            reader = PdfReader(str(path))
        except Exception as exc:  # pragma: no cover - PDF parser/runtime errors
            raise RuntimeError(f"Failed to read PDF {path}: {exc}") from exc

        pages: list[str] = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                # Sanitize text
                text = text.replace("\x00", "")
                if text.strip():
                    pages.append(text.strip())
            except Exception as exc:
                logger.warning("pdf_page_extraction_failed", path=str(path), page=i, error=str(exc))
                # Add placeholder to maintain page count/context if needed, or just skip
                pages.append(f"[Page {i+1} extraction failed]")

        return "\n\n".join(pages)

    try:
        import pypandoc
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("pypandoc is required to convert non-Markdown files") from exc

    try:
        return pypandoc.convert_file(str(path), "md")
    except OSError as exc:  # pragma: no cover - pandoc runtime errors
        raise RuntimeError(f"Failed to convert {path} to markdown: {exc}") from exc


def chunk_text(markdown_text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    """Chunk markdown text using a simple paragraph-based strategy with optional overlap.
    
    Increased default max_chars to 2000 to keep more context per chunk.
    """
    paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
    if not paragraphs:
        # Fallback for texts without double newlines (e.g. some PDF extractions)
        if markdown_text.strip():
            paragraphs = [markdown_text.strip()]
        else:
            return []

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) <= max_chars:
            current.append(para)
            current_len += len(para)
        else:
            if current:
                chunks.append("\n\n".join(current))
                overlap_text = current[-1][-overlap:] if overlap and current[-1] else ""
                current = [overlap_text] if overlap_text else []
                current_len = len(overlap_text)
            
            # If a single paragraph is huge, we must split it
            if len(para) > max_chars:
                # Simple split by length for huge paragraphs
                for i in range(0, len(para), max_chars - overlap):
                    chunk_part = para[i : i + max_chars]
                    chunks.append(chunk_part)
                # Don't add to current, we just consumed it
                current = []
                current_len = 0
            else:
                current.append(para)
                current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    return [c for c in chunks if c.strip()]


def default_embed(texts: Sequence[str]) -> List[List[float]]:
    """Generate embeddings using the default SentenceTransformer model."""
    model = _load_model()
    vectors = model.encode(list(texts), normalize_embeddings=True)
    return [vec.tolist() for vec in vectors]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class IngestionResult:
    collection_name: str
    chunks: int
    points_written: int
    vector_size: int


def _upsert_document(
    doc_key: str, content: str, source_file: str, domain: str, metadata: dict
) -> tuple[None, int]:
    """Upsert full document text into Postgres for hybrid retrieval.
    
    Story 4.5.3b: Implements version tracking for is_latest Qdrant filter.
    On ingest:
    1. Look up existing doc by doc_key
    2. If exists: version = existing.version + 1, mark old as is_latest=False
    3. Insert/update new row with is_latest=True
    
    Returns:
        Tuple of (None, version) where version is the new document version number.
    """
    version = 1
    try:
        # Ensure table exists (idempotent)
        Base.metadata.create_all(get_engine())

        with get_session() as session:
            # Look up existing document to get current version
            existing = session.query(Document).filter(Document.doc_key == doc_key).first()
            
            if existing:
                # Increment version and mark old as not latest
                version = existing.version + 1
                existing.is_latest = False
                session.flush()  # Apply is_latest=False before insert
                
                # For documents table we use upsert, but since doc_key has unique constraint,
                # we update the existing row with new version
                existing.content = content
                existing.domain = domain
                existing.metadata_ = metadata
                existing.version = version
                existing.is_latest = True
                existing.updated_at = datetime.now(timezone.utc)
                
                logger.info(
                    "document_version_updated",
                    doc_key=doc_key,
                    old_version=version - 1,
                    new_version=version,
                )
            else:
                # New document - version 1
                new_doc = Document(
                    doc_key=doc_key,
                    content=content,
                    source_file=source_file,
                    domain=domain,
                    metadata_=metadata,
                    version=1,
                    is_latest=True,
                )
                session.add(new_doc)
                logger.info("document_created", doc_key=doc_key, version=1)
            
            session.commit()
            
    except Exception as e:
        logger.error("document_upsert_failed", doc_key=doc_key, error=str(e))
        
    return None, version



def ingest_file(
    path: Path,
    collection_name: str = qdrant.DEFAULT_COLLECTION_NAME,
    embed_fn: Optional[EmbeddingFn] = None,
    client: Optional["qdrant.QdrantClient"] = None,
    domain: Optional[str] = None,
    tags: Optional[List[str]] = None,
    meta: Optional[dict] = None,
) -> IngestionResult:
    """Ingest a document into Qdrant with embeddings and metadata payload.

    Args:
        path: Path to document file
        collection_name: Qdrant collection name (default: "knowledge")
        embed_fn: Optional custom embedding function
        client: Optional Qdrant client (creates new if None)
        domain: Optional domain tag for payload (defaults to file extension)
        tags: Optional list of tags for semantic classification
        meta: Optional metadata dict with keys like:
            - is_latest: bool (default True)
            - is_system: bool (default False) - System plane vs corpus plane
            - jarvis_core: bool (default False)
            - priority: float 0.0-1.0 (default 0.5)
            - semantic_family: str (e.g. 'core-memory', 'session-log', 'story')

    Returns:
        IngestionResult with collection name, chunk count, points written, vector size
    """
    from jarvis.memory.ingest_helpers import (
        validate_and_load_document,
        generate_embeddings,
        build_chunk_payloads,
        finalize_and_persist,
    )

    # Phase 1: Validate and load
    markdown_text, chunks = validate_and_load_document(path)

    # Phase 0: Apply Ingestion Policy (Self-Discovery)
    # If explicit metadata/domain not provided, try to discover from policy
    if not domain or not meta:
        try:
            from jarvis.memory.domain_classifiers import classify_from_ingestion_policy
            p_domain, p_tags, p_meta = classify_from_ingestion_policy(path)
            
            # Use policy values if not explicitly overridden
            domain = domain or p_domain
            
            # Merge tags
            current_tags = set(tags or [])
            current_tags.update(p_tags)
            tags = list(current_tags)
            
            # Merge meta (policy provides defaults, explicit meta overrides)
            if meta is None:
                meta = p_meta
            else:
                # User meta overrides policy meta
                combined = p_meta.copy()
                combined.update(meta)
                meta = combined
                
        except ImportError:
            # Fallback if policy module issues
            logger.warning("ingestion_policy_import_failed")
        except Exception as e:
            logger.warning("ingestion_policy_failed", error=str(e))


    if not chunks:
        logger.info("ingest_no_chunks", path=str(path))
        return IngestionResult(collection_name, 0, 0, qdrant.VECTOR_SIZE)

    # Phase 2: Generate embeddings
    vectors = generate_embeddings(chunks, embed_fn)

    # Initialize Qdrant client and collection
    client = client or qdrant.get_qdrant_client()
    qdrant.init_collection(collection_name=collection_name, client=client)

    # Phase 3: Build chunk payloads with domain heuristics
    payloads, doc_primary_domain, doc_tags = build_chunk_payloads(
        path, chunks, domain, tags, meta
    )

    # Phase 4: Finalize and persist
    chunks_count, points_written = finalize_and_persist(
        path, markdown_text, chunks, vectors, payloads,
        doc_primary_domain, doc_tags, meta, collection_name, client
    )

    return IngestionResult(
        collection_name=collection_name,
        chunks=chunks_count,
        points_written=points_written,
        vector_size=qdrant.VECTOR_SIZE,
    )
