from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from time import monotonic
from typing import Dict, List, Optional, Sequence

import structlog
from sqlalchemy.orm import Session

from jarvis.database import qdrant as qdrant_db
from jarvis.memory.query_expander import expand_query
from jarvis.memory.retrieval.types import SearchResult
from jarvis.memory.retrieval import core

logger = structlog.get_logger(__name__)

def _reciprocal_rank_fusion(
    query_results: List[List[SearchResult]],
    k_constant: int = 60,
) -> Dict[str, float]:
    rrf_scores: Dict[str, float] = {}

    for result_set in query_results:
        for rank, result in enumerate(result_set, start=1):
            key = core._make_result_key(result)
            rrf_score = 1.0 / (k_constant + rank)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + rrf_score

    return rrf_scores

def expanded_search(
    query: str,
    *,
    k: int = 10,
    expansion_count: int = 2,
    domains: Optional[Sequence[str]] = None,
    retriever: str = "semantic",
    weight: float = 0.7,
    client: Optional["qdrant_db.QdrantClient"] = None,
    session: Optional[Session] = None,
) -> List[SearchResult]:
    if expansion_count < 0 or expansion_count > 5:
        raise ValueError("expansion_count must be between 0 and 5")

    valid_retrievers = {"semantic", "keyword", "hybrid"}
    if retriever not in valid_retrievers:
        raise ValueError(f"Invalid retriever: {retriever}")

    if retriever == "hybrid" and (weight < 0.0 or weight > 1.0):
        # hybrid_search will also validate this, but good to catch early
        raise ValueError(f"weight must be between 0.0 and 1.0, got {weight}")

    start = monotonic()
    logger.info(
        "expanded_search_started",
        query=query,
        k=k,
        expansion_count=expansion_count,
        retriever=retriever,
    )

    if expansion_count == 0:
        if retriever == "semantic":
            return core.search_memory(query, k=k, domains=domains, client=client)
        elif retriever == "keyword":
            return core.keyword_search(query, k=k, domains=domains, session=session)
        elif retriever == "hybrid":
            return core.hybrid_search(query, k=k, weight=weight, domains=domains, client=client, session=session)
        else:
            raise ValueError(f"Unknown retriever: {retriever}")

    queries = [query] + expand_query(query, count=expansion_count)
    queries = list(dict.fromkeys(queries))  # Deduplicate

    all_results: List[List[SearchResult]] = []

    def _run_single_query(q: str) -> List[SearchResult]:
        if retriever == "semantic":
            return core.search_memory(q, k=k, domains=domains, client=client)
        elif retriever == "keyword":
            return core.keyword_search(q, k=k, domains=domains, session=session)
        elif retriever == "hybrid":
            return core.hybrid_search(q, k=k, weight=weight, domains=domains, client=client, session=session)
        return []

    with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
        all_results = list(executor.map(_run_single_query, queries))

    logger.info("expanded_search_retrieval_completed", result_sets=len(all_results))

    rrf_map = _reciprocal_rank_fusion(all_results)
    
    # Flatten and deduplicate by key, assigning RRF score
    merged: Dict[str, SearchResult] = {}
    for res_list in all_results:
        for res in res_list:
            key = core._make_result_key(res)
            if key not in merged:
                merged[key] = res
    
    final_results = []
    for key, score in rrf_map.items():
        if key in merged:
            res = merged[key]
            res.score = score
            res.metadata = res.metadata or {}
            res.metadata["rrf_score"] = score
            res.metadata["fusion_strategy"] = "reciprocal_rank_fusion"
            res.metadata["expansion_count"] = expansion_count
            final_results.append(res)
            
    final_results.sort(key=lambda r: r.score, reverse=True)
    results = final_results[:k]

    duration_ms = (monotonic() - start) * 1000.0
    logger.info(
        "expanded_search_completed",
        k=k,
        expansion_count=expansion_count,
        retriever=retriever,
        fusion_strategy="reciprocal_rank_fusion",
        result_count=len(results),
        total_latency_ms=round(duration_ms, 2),
    )
    return results
