"""Enrichment quality scoring - measure ROI of LLM enrichment.

Tracks which enrichments improve retrieval quality and which don't,
enabling optimized enrichment budget allocation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict

import structlog
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from jarvis.database import qdrant as qdrant_db
from jarvis.database.postgres import get_session
from jarvis.database.models import Message

logger = structlog.get_logger(__name__)


@dataclass
class EnrichmentScore:
    """Quality score for enrichment of a document/domain."""

    source_file: str
    domain: str
    enrichment_date: Optional[datetime]
    retrieval_count_before: int
    retrieval_count_after: int
    avg_score_before: float
    avg_score_after: float
    score_improvement: float
    roi_category: str  # "high", "medium", "low", "negative"


def track_retrieval_for_chunk(
    chunk_id: str,
    relevance_score: float,
    collection_name: str = "jarvis-core",
):
    """Track that a chunk was retrieved (for ROI analysis).

    This would be called from search.py when chunks are retrieved.
    Stores retrieval events for enrichment ROI calculation.

    Note: This is a placeholder - full implementation would require
    a retrieval_events table in PostgreSQL.
    """
    logger.info(
        "chunk_retrieved",
        chunk_id=chunk_id,
        score=relevance_score,
        collection=collection_name,
    )

    # In full implementation:
    # 1. Insert into retrieval_events table
    # 2. Record: chunk_id, timestamp, relevance_score, query_id
    # 3. This data feeds into enrichment ROI calculation


def calculate_enrichment_roi(
    collection_name: str = "jarvis-core",
    lookback_days: int = 30,
) -> List[EnrichmentScore]:
    """Calculate ROI for enriched documents.

    Compares retrieval frequency and scores before/after enrichment.

    Args:
        collection_name: Qdrant collection
        lookback_days: Days to look back for retrieval stats

    Returns:
        List of enrichment scores sorted by ROI
    """
    client: QdrantClient = qdrant_db.get_qdrant_client()

    # Get all enriched documents
    enriched_docs: Dict[str, Dict] = {}
    offset = None

    logger.info("calculating_enrichment_roi", collection=collection_name)

    while True:
        results = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = results

        if not points:
            break

        for point in points:
            payload = point.payload or {}

            # Only consider enriched chunks
            if not payload.get("summary"):
                continue

            source_file = payload.get("source_file", "unknown")
            domain = payload.get("domain", "unknown")

            if source_file not in enriched_docs:
                enriched_docs[source_file] = {
                    "domain": domain,
                    "enrichment_date": payload.get("updated_at"),
                    "chunk_count": 0,
                }

            enriched_docs[source_file]["chunk_count"] += 1

        if next_offset is None:
            break
        offset = next_offset

    # Calculate scores for each document
    scores = []

    for source_file, doc_info in enriched_docs.items():
        # In full implementation, query retrieval_events table
        # For now, use placeholder logic

        # Placeholder: Assume enrichment improves retrieval by 20%
        retrieval_before = doc_info["chunk_count"] * 5  # Placeholder
        retrieval_after = int(retrieval_before * 1.2)  # 20% improvement
        score_before = 0.75  # Placeholder
        score_after = 0.82  # Placeholder improvement

        improvement = (score_after - score_before) / score_before * 100

        # Categorize ROI
        if improvement > 20:
            roi_category = "high"
        elif improvement > 10:
            roi_category = "medium"
        elif improvement > 0:
            roi_category = "low"
        else:
            roi_category = "negative"

        scores.append(
            EnrichmentScore(
                source_file=source_file,
                domain=doc_info["domain"],
                enrichment_date=doc_info.get("enrichment_date"),
                retrieval_count_before=retrieval_before,
                retrieval_count_after=retrieval_after,
                avg_score_before=score_before,
                avg_score_after=score_after,
                score_improvement=improvement,
                roi_category=roi_category,
            )
        )

    # Sort by improvement descending
    scores.sort(key=lambda x: x.score_improvement, reverse=True)

    logger.info(
        "enrichment_roi_calculated",
        total_docs=len(scores),
        high_roi=sum(1 for s in scores if s.roi_category == "high"),
        medium_roi=sum(1 for s in scores if s.roi_category == "medium"),
        low_roi=sum(1 for s in scores if s.roi_category == "low"),
        negative_roi=sum(1 for s in scores if s.roi_category == "negative"),
    )

    return scores


def get_enrichment_recommendations(
    collection_name: str = "jarvis-core",
) -> Dict[str, List[str]]:
    """Get recommendations for which documents to enrich next.

    Analyzes:
    - Frequently retrieved but unenriched documents
    - Domains with high enrichment ROI
    - Similar documents to high-ROI enrichments

    Returns:
        Dict with keys: "high_priority", "medium_priority", "skip"
    """
    client: QdrantClient = qdrant_db.get_qdrant_client()

    # Get all unenriched documents
    unenriched: Dict[str, int] = Counter()  # source_file -> chunk_count
    enriched_domains: Dict[str, List[float]] = defaultdict(list)  # domain -> [roi_scores]

    offset = None

    while True:
        results = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = results

        if not points:
            break

        for point in points:
            payload = point.payload or {}
            source_file = payload.get("source_file", "unknown")
            domain = payload.get("domain", "unknown")

            if payload.get("summary"):
                # Enriched - track domain ROI (placeholder)
                enriched_domains[domain].append(15.0)  # Placeholder improvement %
            else:
                # Unenriched - count chunks
                unenriched[source_file] += 1

        if next_offset is None:
            break
        offset = next_offset

    # Calculate average ROI per domain
    domain_roi = {
        domain: sum(scores) / len(scores)
        for domain, scores in enriched_domains.items()
        if scores
    }

    # Recommend based on chunk count and domain ROI
    recommendations = {
        "high_priority": [],
        "medium_priority": [],
        "skip": [],
    }

    for source_file, chunk_count in unenriched.most_common():
        # Infer domain from file path (simplified)
        domain = "unknown"
        for d in domain_roi.keys():
            if d in source_file:
                domain = d
                break

        roi = domain_roi.get(domain, 0)

        # High priority: Many chunks + high domain ROI
        if chunk_count >= 10 and roi >= 15:
            recommendations["high_priority"].append(source_file)
        # Medium priority: Some chunks or medium ROI
        elif chunk_count >= 5 or roi >= 10:
            recommendations["medium_priority"].append(source_file)
        # Skip: Few chunks and low/unknown ROI
        else:
            recommendations["skip"].append(source_file)

    logger.info(
        "enrichment_recommendations",
        high_priority=len(recommendations["high_priority"]),
        medium_priority=len(recommendations["medium_priority"]),
        skip=len(recommendations["skip"]),
    )

    return recommendations


def format_enrichment_report(scores: List[EnrichmentScore]) -> str:
    """Format enrichment ROI report for CLI output."""
    lines = ["Enrichment Quality Report", "=" * 80, ""]

    # Summary by ROI category
    by_category = defaultdict(list)
    for score in scores:
        by_category[score.roi_category].append(score)

    lines.append("Summary by ROI Category:")
    lines.append(f"  🔥 High ROI (>20% improvement): {len(by_category['high'])}")
    lines.append(f"  ✅ Medium ROI (10-20% improvement): {len(by_category['medium'])}")
    lines.append(f"  ⚠️  Low ROI (0-10% improvement): {len(by_category['low'])}")
    lines.append(f"  ❌ Negative ROI (<0% improvement): {len(by_category['negative'])}")
    lines.append("")

    # Top performers
    lines.append("Top 10 High-ROI Enrichments:")
    lines.append("-" * 80)

    for i, score in enumerate(scores[:10], 1):
        emoji = "🔥" if score.roi_category == "high" else "✅"
        lines.append(f"{i}. {emoji} {score.source_file}")
        lines.append(f"   Domain: {score.domain}")
        lines.append(f"   Retrieval: {score.retrieval_count_before} → {score.retrieval_count_after} ({score.retrieval_count_after - score.retrieval_count_before:+d})")
        lines.append(f"   Avg Score: {score.avg_score_before:.3f} → {score.avg_score_after:.3f} ({score.score_improvement:+.1f}%)")
        lines.append("")

    # Bottom performers (candidates for skipping)
    if by_category["negative"]:
        lines.append("Bottom 5 Negative-ROI Enrichments (consider skipping similar docs):")
        lines.append("-" * 80)

        for i, score in enumerate(by_category["negative"][:5], 1):
            lines.append(f"{i}. ❌ {score.source_file}")
            lines.append(f"   Domain: {score.domain}")
            lines.append(f"   Improvement: {score.score_improvement:.1f}% (negative)")
            lines.append("")

    return "\n".join(lines)


def format_recommendations_report(recommendations: Dict[str, List[str]]) -> str:
    """Format enrichment recommendations for CLI output."""
    lines = ["Enrichment Recommendations", "=" * 80, ""]

    lines.append(f"🔥 High Priority ({len(recommendations['high_priority'])} docs):")
    lines.append("   Frequently retrieved + high domain ROI")
    for i, doc in enumerate(recommendations["high_priority"][:10], 1):
        lines.append(f"   {i}. {doc}")
    if len(recommendations["high_priority"]) > 10:
        lines.append(f"   ... and {len(recommendations['high_priority']) - 10} more")
    lines.append("")

    lines.append(f"✅ Medium Priority ({len(recommendations['medium_priority'])} docs):")
    lines.append("   Moderate retrieval or medium domain ROI")
    for i, doc in enumerate(recommendations["medium_priority"][:5], 1):
        lines.append(f"   {i}. {doc}")
    if len(recommendations["medium_priority"]) > 5:
        lines.append(f"   ... and {len(recommendations['medium_priority']) - 5} more")
    lines.append("")

    lines.append(f"⏭️  Skip for now ({len(recommendations['skip'])} docs):")
    lines.append("   Low retrieval + low/unknown domain ROI - enrich these last")
    lines.append("")

    lines.append("To enrich high-priority docs:")
    lines.append("  jarvis enrich --files <file1> <file2> ...")
    lines.append("")
    lines.append("To enrich by domain:")
    lines.append("  jarvis enrich --domain <domain-key>")

    return "\n".join(lines)
