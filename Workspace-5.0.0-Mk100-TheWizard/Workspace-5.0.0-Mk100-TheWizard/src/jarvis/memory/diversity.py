"""Diversity filtering for memory retrieval results (Story 4.5.4).

Implements Maximal Marginal Relevance (MMR) to prevent redundant chunks
from dominating retrieval results, ensuring agents receive topically 
diverse context.

MMR Formula:
    Score = λ * relevance - (1-λ) * max_sim(doc, selected)

Modes:
    - balanced (λ=0.5): Equal relevance + diversity
    - aggressive (λ=0.3): More diversity, stronger penalty
    - minimal (λ=1.0): No diversity penalty, preserve ordering
"""

from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

import numpy as np
import structlog

if TYPE_CHECKING:
    from jarvis.memory.retrieval.types import SearchResult

# ═══════════════════════════════════════════════════════════════════════════════
# ✨ MMR DIVERSITY FILTER (Story 4.5.4)
# ═══════════════════════════════════════════════════════════════════════════════
# "Not all those who wander are lost, but those who cluster are redundant."
# ═══════════════════════════════════════════════════════════════════════════════

# Lambda values for each diversity mode
DIVERSITY_LAMBDAS: Dict[str, float] = {
    "balanced": 0.5,    # Equal relevance + diversity
    "aggressive": 0.3,  # Stronger diversity penalty
    "minimal": 1.0,     # No diversity (preserve current ordering)
}

# Same-document similarity floor (prevents same-doc chunks from clustering)
SAME_DOC_SIM_FLOOR = 0.85


def apply_diversity_filter(
    results: "List[SearchResult]",
    max_results: int,
    diversity_mode: str = "balanced",
) -> "List[SearchResult]":
    """Apply MMR-based diversity to pre-ranked results.
    
    Runs AFTER:
      1) Hybrid retrieval
      2) Cross-encoder rerank
      3) Freshness scoring
      4) Version conflict resolution
    
    And BEFORE:
      - Final truncation to k
      - Handing results to Council of Ricks
    
    Args:
        results: Pre-ranked SearchResults (already scored)
        max_results: Maximum results to return
        diversity_mode: "balanced" | "aggressive" | "minimal"
        
    Returns:
        MMR-reranked results with redundancy reduced
    """
    logger = structlog.get_logger("jarvis.memory.diversity")
    
    if not results:
        return results
    
    # Minimal mode = no diversity filtering, preserve current ordering
    if diversity_mode == "minimal":
        logger.debug("diversity_filter_skipped", mode="minimal")
        return results[:max_results]
    
    # Get lambda for this mode
    lambda_val = DIVERSITY_LAMBDAS.get(diversity_mode, 0.5)
    
    # Compute pairwise similarity matrix
    similarity_matrix = _compute_pairwise_similarity(results)
    
    # Apply MMR selection
    selected_indices = _select_mmr(
        results=results,
        similarity_matrix=similarity_matrix,
        lambda_val=lambda_val,
        k=max_results,
    )
    
    # Build selected results
    selected_results = [results[i] for i in selected_indices]
    
    # Log diversity metrics
    overlap_before = _compute_overlap_metric(results[:max_results])
    overlap_after = _compute_overlap_metric(selected_results)
    
    logger.info(
        "diversity_filter_applied",
        mode=diversity_mode,
        lambda_val=lambda_val,
        input_count=len(results),
        output_count=len(selected_results),
        overlap_before=round(overlap_before, 3),
        overlap_after=round(overlap_after, 3),
        diversity_gain=round(overlap_before - overlap_after, 3),
    )
    
    return selected_results


def _compute_pairwise_similarity(
    results: "List[SearchResult]",
) -> np.ndarray:
    """Compute cosine similarity matrix between all result pairs.
    
    Uses embeddings from metadata if available, otherwise falls back
    to text-based similarity estimation.
    
    Same doc_key pairs get a similarity floor to prevent clustering.
    """
    n = len(results)
    similarity = np.zeros((n, n))
    
    # Try to extract embeddings from metadata
    embeddings = []
    for r in results:
        meta = r.metadata or {}
        emb = meta.get("embedding") or meta.get("vector")
        if emb is not None and hasattr(emb, "__len__"):
            embeddings.append(np.array(emb, dtype=np.float32))
        else:
            embeddings.append(None)
    
    # Check if we have embeddings
    has_embeddings = all(e is not None for e in embeddings)
    
    if has_embeddings:
        # Compute cosine similarity from embeddings
        emb_matrix = np.vstack(embeddings)
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        normalized = emb_matrix / norms
        similarity = normalized @ normalized.T
    else:
        # Fallback: estimate similarity from text overlap
        # Less accurate but works when embeddings not stored
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    similarity[i, j] = 1.0
                else:
                    sim = _estimate_text_similarity(results[i].text, results[j].text)
                    similarity[i, j] = sim
                    similarity[j, i] = sim
    
    # Apply same-doc similarity floor
    for i in range(n):
        for j in range(i + 1, n):
            doc_key_i = results[i].doc_key or results[i].source_file or ""
            doc_key_j = results[j].doc_key or results[j].source_file or ""
            
            if doc_key_i and doc_key_j and doc_key_i == doc_key_j:
                # Same document - apply floor to cluster them together less
                floor = SAME_DOC_SIM_FLOOR
                similarity[i, j] = max(similarity[i, j], floor)
                similarity[j, i] = max(similarity[j, i], floor)
    
    return similarity


def _estimate_text_similarity(text1: str, text2: str) -> float:
    """Estimate text similarity using word overlap (Jaccard-like).
    
    Used as fallback when embeddings not available.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def _select_mmr(
    results: "List[SearchResult]",
    similarity_matrix: np.ndarray,
    lambda_val: float,
    k: int,
) -> List[int]:
    """Select k results using Maximal Marginal Relevance.
    
    MMR Formula:
        Score = λ * relevance - (1-λ) * max_sim(doc, selected)
    
    Args:
        results: All candidate results
        similarity_matrix: Pairwise similarity matrix
        lambda_val: Balance between relevance (1.0) and diversity (0.0)
        k: Number of results to select
        
    Returns:
        Indices of selected results in MMR order
    """
    n = len(results)
    k = min(k, n)
    
    if k == 0:
        return []
    
    # Normalize relevance scores to [0, 1]
    scores = np.array([r.score for r in results])
    max_score = scores.max() if scores.max() > 0 else 1.0
    relevance = scores / max_score
    
    # Track selected and remaining indices
    selected: List[int] = []
    remaining = list(range(n))
    
    # Start with highest relevance (first item after prior reranking)
    first_idx = 0  # Already sorted by relevance
    selected.append(first_idx)
    remaining.remove(first_idx)
    
    # Iteratively select using MMR
    while len(selected) < k and remaining:
        best_mmr = -float("inf")
        best_idx = remaining[0]
        
        for idx in remaining:
            # Relevance term
            rel = relevance[idx]
            
            # Diversity term: max similarity to any selected
            max_sim = max(similarity_matrix[idx, s] for s in selected)
            
            # MMR score
            mmr_score = lambda_val * rel - (1 - lambda_val) * max_sim
            
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = idx
        
        selected.append(best_idx)
        remaining.remove(best_idx)
    
    return selected


def _compute_overlap_metric(results: "List[SearchResult]") -> float:
    """Compute overlap metric: fraction of results sharing a doc_key.
    
    1.0 = all results from same document (high redundancy)
    0.0 = all results from unique documents (high diversity)
    """
    if len(results) <= 1:
        return 0.0
    
    doc_keys = [r.doc_key or r.source_file or f"unique_{i}" for i, r in enumerate(results)]
    unique_docs = len(set(doc_keys))
    
    # Overlap = 1 - (unique_docs / total_docs)
    overlap = 1.0 - (unique_docs / len(results))
    
    return overlap
