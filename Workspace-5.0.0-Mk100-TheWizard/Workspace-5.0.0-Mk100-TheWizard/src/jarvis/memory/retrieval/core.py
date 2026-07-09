from __future__ import annotations

import hashlib
import os
import threading
from time import monotonic
from typing import Callable, Dict, List, Optional, Sequence, Union, Tuple

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

from jarvis.database import models as db_models
from jarvis.database.models import Document
from jarvis.database import postgres as pg_db
from jarvis.database import qdrant as qdrant_db
from jarvis.memory.diversity import apply_diversity_filter

from jarvis.memory.retrieval.types import RetrievalMode, SearchResult
from jarvis.memory.retrieval import filters
from jarvis.observability.metrics import memory_search_latency

logger = structlog.get_logger(__name__)

# Constants
DEFAULT_DIVERSITY_MODE = "balanced"

def deduplicate_results(results: Sequence[SearchResult]) -> List[SearchResult]:
    seen: set[str] = set()
    unique: List[SearchResult] = []

    for res in results:
        meta = res.metadata or {}
        key = None

        for candidate in (meta.get("chunk_id"), meta.get("hash"), meta.get("message_id")):
            if candidate:
                key = f"{res.domain or '-'}:{candidate}"
                break

        if key is None:
            text = (res.text or "").strip()
            if not text:
                continue
            digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
            key = f"{res.domain or '-'}:{digest}"

        if key in seen:
            continue

        seen.add(key)
        unique.append(res)

    return unique

def _embed_query(query: str) -> List[float]:
    if not hasattr(_embed_query, "_model"):
        _embed_query._model = None
        _embed_query._lock = threading.Lock()

    if _embed_query._model is None:
        with _embed_query._lock:
            if _embed_query._model is None:
                model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                model = model.eval()
                _embed_query._model = model

    model = _embed_query._model
    vec = model.encode([query], normalize_embeddings=True)[0]
    return vec.tolist()

_RERANKER = None

def _load_reranker():
    global _RERANKER
    if _RERANKER is None:
        from sentence_transformers import CrossEncoder
        _RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")
    return _RERANKER

def _should_rerank() -> bool:
    value = os.getenv("JARVIS_RERANK_ENABLED", "")
    return value.lower() in {"1", "true", "yes"}

def _rerank_results(query: str, results: List[SearchResult], top_k: int = 20) -> List[SearchResult]:
    if not results or not _should_rerank():
        return results

    top_k = max(1, min(top_k, len(results)))

    try:
        reranker = _load_reranker()
    except Exception:
        return results

    pairs = [[query, r.text] for r in results[:top_k]]

    try:
        scores = reranker.predict(pairs)
    except Exception:
        return results

    for res, score in zip(results[:top_k], scores):
        meta = dict(res.metadata or {})
        meta["rerank_score"] = float(score)
        meta.setdefault("original_score", float(res.score))
        res.metadata = meta

    reranked_segment = sorted(results[:top_k], key=lambda r: r.metadata["rerank_score"], reverse=True)
    return reranked_segment + results[top_k:]

def _make_result_key(result: SearchResult) -> str:
    metadata = result.metadata or {}
    chunk_id = metadata.get("chunk_id") or metadata.get("hash") or metadata.get("message_id")
    domain = result.domain or "-"
    if chunk_id:
        return f"{domain}:{chunk_id}"
    return f"{domain}:{hash(result.text)}"

def _normalize_score_map(
    results: Sequence[SearchResult],
    make_key: Callable[[SearchResult], str],
) -> Dict[str, float]:
    if not results:
        return {}

    scores = [res.score for res in results]
    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return {make_key(res): 1.0 for res in results}

    span = max_score - min_score
    return {make_key(res): (res.score - min_score) / span for res in results}

def search_memory(
    query: str,
    *,
    k: int = 10,
    domains: Optional[Sequence[str]] = None,
    tags: Optional[Sequence[str]] = None,
    min_freshness: float = filters.DEFAULT_MIN_FRESHNESS,
    allow_stale: bool = False,
    diversity_mode: str = DEFAULT_DIVERSITY_MODE,
    retrieval_mode: Optional[RetrievalMode] = None,
    include_system_docs: Optional[bool] = None,
    time_slice: Optional[Union[str, Tuple[str, str]]] = None,
    client: Optional["qdrant_db.QdrantClient"] = None,
) -> List[SearchResult]:
    stripped_query = query.strip()
    if not stripped_query:
        raise ValueError("Query cannot be empty")

    if k < 1 or k > 50:
        raise ValueError(f"k must be between 1 and 50, got {k}")

    start = monotonic()
    k = max(1, min(k, 50))
    client = client or qdrant_db.get_qdrant_client()
    vector = _embed_query(stripped_query)

    detected_mode = retrieval_mode
    detected_date = None
    if detected_mode is None:
        detected_mode, detected_date = filters.detect_retrieval_mode(stripped_query)
    
    effective_time_slice = time_slice
    if effective_time_slice is None and detected_date is not None:
        effective_time_slice = detected_date.strftime("%Y-%m-%d")
    
    effective_include_system = include_system_docs
    if effective_include_system is None:
        effective_include_system = (detected_mode == RetrievalMode.META)
    
    effective_allow_stale = allow_stale
    if not allow_stale and detected_mode in (RetrievalMode.HISTORICAL, RetrievalMode.TIME_SLICE):
        effective_allow_stale = True
    
    logger.info(
        "search_memory_mode_detected",
        retrieval_mode=detected_mode.value,
        include_system=effective_include_system,
        allow_stale=effective_allow_stale,
        time_slice=effective_time_slice,
    )

    normalized_domains = filters.normalize_domains_for_search(domains)
    effective_domains = (
        list(normalized_domains) if normalized_domains else filters.infer_query_domains(stripped_query)
    )

    def _run_query(domains_for_filter: Optional[Sequence[str]]) -> List[SearchResult]:
        q_filter = filters.build_filter_for_mode(
            mode=detected_mode,
            domains=domains_for_filter,
            tags=tags,
            include_system_docs=effective_include_system,
            allow_stale=effective_allow_stale,
            time_slice=effective_time_slice,
        )

        search_result = client.query_points(
            collection_name=qdrant_db.DEFAULT_COLLECTION_NAME,
            query=vector,
            query_filter=q_filter,
            search_params=None,
            limit=k,
            with_payload=True,
            with_vectors=False,
        )

        out: List[SearchResult] = []
        for point in search_result.points:
            payload = point.payload or {}
            text = payload.get("text") or ""
            if not text:
                continue
            out.append(
                SearchResult(
                    text=text,
                    score=float(point.score),
                    source_file=payload.get("source_file"),
                    section=payload.get("section"),
                    domain=payload.get("primary_domain") or payload.get("domain"),
                    metadata=payload,
                    doc_id=payload.get("doc_id"),
                    doc_key=payload.get("doc_key"),
                )
            )
        return out

    results = _run_query(effective_domains)

    if domains is None and not results:
        results = _run_query(None)

    results = filters.filter_results_by_domains(results, normalized_domains)
    results = filters.apply_time_weight(results)
    results = filters.apply_source_boost(results)
    results = _rerank_results(stripped_query, results)
    results = filters.apply_freshness_filter(results, min_freshness, allow_stale)
    results = filters.resolve_version_conflicts(results)

    inferred_for_prior = list(effective_domains) if effective_domains else []
    results = filters.apply_domain_prior(results, inferred_for_prior, detected_mode)
    results = apply_diversity_filter(results, max_results=k, diversity_mode=diversity_mode)

    duration_ms = (monotonic() - start) * 1000.0
    try:
        memory_search_latency.record(duration_ms)
    except Exception:
        pass

    logger.info(
        "memory_search_completed",
        k=k,
        result_count=len(results),
        duration_ms=round(duration_ms, 2),
    )

    return results

def keyword_search(
    query: str,
    *,
    k: int = 10,
    domains: Optional[Sequence[str]] = None,
    allow_stale: bool = False,
    session: Optional[Session] = None,
) -> List[SearchResult]:
    stripped_query = query.strip()
    if not stripped_query:
        raise ValueError("Query cannot be empty")

    if k < 1 or k > 50:
        raise ValueError(f"k must be between 1 and 50, got {k}")

    keyword_domain = "jarvis-conversations"
    if domains is not None and keyword_domain not in {d.replace(".", "-") for d in domains} and keyword_domain not in {d.replace("-", ".") for d in domains}:
        return []

    start = monotonic()
    k = max(1, min(k, 50))

    def _run_keyword_search(db_session: Session) -> List[SearchResult]:
        vector = func.to_tsvector("english", db_models.Message.content)
        ts_query = func.plainto_tsquery("english", stripped_query)
        rank = func.ts_rank_cd(vector, ts_query).label("rank")

        stmt = (
            select(db_models.Message.id, db_models.Message.content, rank)
            .where(vector.op("@@")(ts_query))
            .order_by(rank.desc())
            .limit(k)
        )

        rows = db_session.execute(stmt).all()
        results: List[SearchResult] = []
        for row in rows:
            score = float(row.rank or 0.0)
            if score <= 0.0:
                continue
            metadata = {
                "message_id": str(row.id),
                "chunk_id": str(row.id),
                "source": "postgres-messages",
            }
            results.append(
                SearchResult(
                    text=row.content,
                    score=score,
                    source_file=None,
                    section=None,
                    domain=keyword_domain,
                    metadata=metadata,
                )
            )
        return results

    if session is not None:
        results = _run_keyword_search(session)
    else:
        with pg_db.get_session() as db_session:
            results = _run_keyword_search(db_session)

    duration_ms = (monotonic() - start) * 1000.0
    logger.info("keyword_search_completed", result_count=len(results), duration_ms=round(duration_ms, 2))
    return results

def document_keyword_search(
    query: str,
    *,
    k: int = 10,
    domains: Optional[Sequence[str]] = None,
    session: Optional[Session] = None,
) -> List[SearchResult]:
    stripped_query = query.strip()
    if not stripped_query:
        return []

    k = max(1, min(k, 50))
    start = monotonic()

    def _run_search(db_session: Session) -> List[SearchResult]:
        vector = func.to_tsvector("english", Document.content)
        ts_query = func.plainto_tsquery("english", stripped_query)
        rank = func.ts_rank_cd(vector, ts_query).label("rank")
        headline = func.ts_headline(
            "english", Document.content, ts_query, "StartSel=**,StopSel=**,MaxWords=50,MinWords=20"
        ).label("headline")

        stmt = (
            select(
                Document.id,
                Document.doc_key,
                headline,
                Document.source_file,
                Document.domain,
                Document.metadata_,
                rank,
            )
            .where(vector.op("@@")(ts_query))
        )

        if domains:
            stmt = stmt.where(Document.domain.in_(domains))

        stmt = stmt.order_by(rank.desc()).limit(k)

        rows = db_session.execute(stmt).all()
        results: List[SearchResult] = []
        for row in rows:
            score = float(row.rank or 0.0)
            if score <= 0.0:
                continue

            meta = dict(row.metadata_ or {})
            meta.update({
                "doc_key": row.doc_key,
                "source": "postgres-documents",
                "is_snippet": True,
            })

            results.append(
                SearchResult(
                    text=row.headline,
                    score=score,
                    source_file=row.source_file,
                    section=None,
                    domain=row.domain,
                    metadata=meta,
                    doc_id=str(row.id) if getattr(row, "id", None) else None,
                    doc_key=row.doc_key,
                )
            )
        return filters.filter_results_by_domains(results, domains)

    if session is not None:
        results = _run_search(session)
    else:
        with pg_db.get_session() as db_session:
            results = _run_search(db_session)

    duration_ms = (monotonic() - start) * 1000.0
    logger.info("document_search_completed", result_count=len(results), duration_ms=round(duration_ms, 2))
    return results

def hybrid_search(
    query: str,
    *,
    k: int = 10,
    weight: float = 0.7,
    domains: Optional[Sequence[str]] = None,
    allow_stale: bool = False,
    diversity_mode: str = DEFAULT_DIVERSITY_MODE,
    client: Optional["qdrant_db.QdrantClient"] = None,
    session: Optional[Session] = None,
) -> List[SearchResult]:
    if weight < 0.0 or weight > 1.0:
        raise ValueError(f"weight must be between 0.0 and 1.0, got {weight}")

    start = monotonic()

    semantic_results = search_memory(query, k=k, domains=domains, allow_stale=allow_stale, diversity_mode=diversity_mode, client=client)
    keyword_results = keyword_search(query, k=k, domains=domains, allow_stale=allow_stale, session=session)
    document_results = document_keyword_search(query, k=k, domains=domains, session=session)

    semantic_norm = _normalize_score_map(semantic_results, _make_result_key)
    keyword_norm = _normalize_score_map(keyword_results, _make_result_key)
    document_norm = _normalize_score_map(document_results, _make_result_key)

    combined: Dict[str, SearchResult] = {}
    for res in semantic_results:
        combined.setdefault(_make_result_key(res), res)
    for res in keyword_results:
        combined.setdefault(_make_result_key(res), res)
    for res in document_results:
        combined.setdefault(_make_result_key(res), res)

    merged: List[SearchResult] = []
    for key, res in combined.items():
        semantic_score = semantic_norm.get(key)
        keyword_score = keyword_norm.get(key)
        document_score = document_norm.get(key)

        raw_keyword_score = max(keyword_score or 0.0, document_score or 0.0)
        
        if semantic_score is None and raw_keyword_score <= 0.0:
            continue

        if semantic_score is None:
            final_score = (1.0 - weight) * raw_keyword_score
        elif raw_keyword_score <= 0.0:
            final_score = weight * semantic_score
        else:
            final_score = weight * semantic_score + (1.0 - weight) * raw_keyword_score

        metadata = dict(res.metadata or {})
        metadata["semantic_score_norm"] = semantic_score
        metadata["keyword_score_norm"] = keyword_score
        metadata["hybrid_weight"] = weight

        merged.append(
            SearchResult(
                text=res.text,
                score=float(final_score),
                source_file=res.source_file,
                section=res.section,
                domain=res.domain,
                metadata=metadata,
                doc_id=res.doc_id,
                doc_key=res.doc_key,
            )
        )

    merged.sort(key=lambda r: r.score, reverse=True)
    merged = filters.filter_results_by_domains(merged, domains)
    merged = merged[: max(1, min(k, 50))]

    duration_ms = (monotonic() - start) * 1000.0
    logger.info("hybrid_search_completed", result_count=len(merged), duration_ms=round(duration_ms, 2))
    return merged
