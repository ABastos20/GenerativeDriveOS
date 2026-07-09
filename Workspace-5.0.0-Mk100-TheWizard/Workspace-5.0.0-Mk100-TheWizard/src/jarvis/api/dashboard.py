"""Interactive memory dashboard for JARVIS brain visibility.

Provides real-time visualizations of:
- Domain distribution
- Ingestion timeline
- Retrieval heatmap
- Enrichment coverage
- Cost tracking
- Heuristic hit rates
"""

from __future__ import annotations

import os
from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone
from collections import Counter

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from qdrant_client import QdrantClient
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from jarvis.database import qdrant as qdrant_db
from jarvis.database.postgres import get_session
from jarvis.database.models import Message, Conversation, LLMUsageLog, ResearchLog
from jarvis.database.models import Message, Conversation, LLMUsageLog, ResearchLog
from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP
from jarvis.api.dependencies import require_platform_role
from fastapi import Depends

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/dashboard", 
    tags=["dashboard"],
    dependencies=[Depends(require_platform_role(["observer", "user"]))]
)

# Sensible defaults to drive UI health bars when limits are not explicitly configured.
DEFAULT_RESEARCH_HOURLY_LIMIT = int(os.environ.get("JARVIS_RESEARCH_HOURLY_LIMIT", "10"))
DEFAULT_RESEARCH_COST_CAP_USD = float(os.environ.get("JARVIS_RESEARCH_COST_CAP_USD", "5.0"))


def get_domain_distribution(collection_name: str = "knowledge") -> Dict[str, int]:
    """Get domain distribution across Qdrant collection."""
    client: QdrantClient = qdrant_db.get_qdrant_client()

    try:
        # Scroll all points and count domains
        domain_counts: Counter = Counter()
        offset = None

        while True:
            results = client.scroll(
                collection_name=collection_name,
                limit=1000,
                offset=offset,
                with_payload=["domain"],
                with_vectors=False,
            )

            points, next_offset = results

            if not points:
                break

            for point in points:
                payload = point.payload or {}
                domain = payload.get("domain", "unknown")
                domain_counts[domain] += 1

            if next_offset is None:
                break
            offset = next_offset

        return dict(domain_counts.most_common(30))  # Top 30 domains

    except Exception as e:
        logger.error("domain_distribution_error", error=str(e))
        return {}


def get_ingestion_timeline(
    collection_name: str = "knowledge",
    days: int = 30,
) -> Dict[str, int]:
    """Get ingestion timeline (points added per day)."""
    client: QdrantClient = qdrant_db.get_qdrant_client()

    try:
        # Scroll points with timestamps
        daily_counts: Counter = Counter()
        offset = None

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        while True:
            results = client.scroll(
                collection_name=collection_name,
                limit=1000,
                offset=offset,
                with_payload=["created_at", "ingested_at"],
                with_vectors=False,
            )

            points, next_offset = results

            if not points:
                break

            for point in points:
                payload = point.payload or {}
                timestamp_str = payload.get("created_at") or payload.get("ingested_at")

                if timestamp_str:
                    try:
                        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        # Normalize to aware UTC; if ts is naive, assume UTC.
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        else:
                            ts = ts.astimezone(timezone.utc)

                        if ts >= cutoff:
                            day_key = ts.strftime("%Y-%m-%d")
                            daily_counts[day_key] += 1
                    except (ValueError, AttributeError):
                        pass

            if next_offset is None:
                break
            offset = next_offset

        # Fill in missing days with 0
        result = {}
        current = cutoff.date()
        end = datetime.now(timezone.utc).date()

        while current <= end:
            day_key = current.strftime("%Y-%m-%d")
            result[day_key] = daily_counts.get(day_key, 0)
            current += timedelta(days=1)

        return result

    except Exception as e:
        logger.error("ingestion_timeline_error", error=str(e))
        return {}


def get_retrieval_heatmap(days: int = 7) -> Dict[str, int]:
    """Get retrieval heatmap (domains queried most often)."""
    with get_session() as session:
        try:
            # Query messages with citation_provenance
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            messages = session.query(Message).filter(
                Message.role == "assistant",
                Message.citation_provenance.isnot(None),
                Message.created_at >= cutoff,
            ).all()

            domain_counts: Counter = Counter()

            for msg in messages:
                if msg.citation_provenance and isinstance(msg.citation_provenance, list):
                    for citation in msg.citation_provenance:
                        if isinstance(citation, dict):
                            domain = citation.get("domain")
                            if domain:
                                domain_counts[domain] += 1

            return dict(domain_counts.most_common(20))

        except Exception as e:
            logger.error("retrieval_heatmap_error", error=str(e))
            return {}


def get_enrichment_coverage(collection_name: str = "knowledge") -> Dict[str, Any]:
    """Get enrichment coverage statistics."""
    client: QdrantClient = qdrant_db.get_qdrant_client()

    try:
        total_points = 0
        enriched_points = 0
        enrichment_fields = {"summary": 0, "facts": 0, "tags": 0, "doc_type": 0}

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
                total_points += 1
                payload = point.payload or {}

                has_enrichment = False
                for field in enrichment_fields.keys():
                    if payload.get(field):
                        enrichment_fields[field] += 1
                        has_enrichment = True

                if has_enrichment:
                    enriched_points += 1

            if next_offset is None:
                break
            offset = next_offset

        coverage_pct = (enriched_points / total_points * 100) if total_points > 0 else 0

        return {
            "total_points": total_points,
            "enriched_points": enriched_points,
            "coverage_percent": round(coverage_pct, 1),
            "field_coverage": {
                field: round((count / total_points * 100), 1) if total_points > 0 else 0
                for field, count in enrichment_fields.items()
            },
        }

    except Exception as e:
        logger.error("enrichment_coverage_error", error=str(e))
        return {}


def get_cost_tracking(days: int = 30) -> Dict[str, Any]:
    """Get LLM cost tracking statistics."""
    with get_session() as session:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            messages = session.query(Message).filter(
                Message.role == "assistant",
                Message.created_at >= cutoff,
            ).all()

            total_cost = 0.0
            total_tokens = 0
            provider_costs: Counter = Counter()
            model_costs: Counter = Counter()

            for msg in messages:
                # Normalize to float to avoid mixing Decimal and float
                cost_raw = msg.cost_usd or 0.0
                try:
                    cost = float(cost_raw)
                except (TypeError, ValueError):
                    cost = 0.0
                tokens = msg.token_count or 0
                provider = msg.provider or "unknown"
                model = msg.model or "unknown"

                total_cost += cost
                total_tokens += tokens
                provider_costs[provider] += cost
                model_costs[model] += cost

            return {
                "total_cost_usd": round(total_cost, 4),
                "total_tokens": total_tokens,
                "avg_cost_per_query": round(total_cost / len(messages), 6) if messages else 0.0,
                "by_provider": dict(provider_costs),
                "by_model": dict(model_costs.most_common(5)),
            }

        except Exception as e:
            logger.error("cost_tracking_error", error=str(e))
            return {}


def get_heuristic_hit_rate(collection_name: str = "knowledge") -> Dict[str, Any]:
    """Get heuristic classification hit rate."""
    client: QdrantClient = qdrant_db.get_qdrant_client()

    try:
        total_classified = 0
        heuristic_count = 0
        llm_count = 0
        direct_count = 0

        offset = None

        while True:
            results = client.scroll(
                collection_name=collection_name,
                limit=1000,
                offset=offset,
                with_payload=["domain_source"],
                with_vectors=False,
            )

            points, next_offset = results

            if not points:
                break

            for point in points:
                payload = point.payload or {}
                source = payload.get("domain_source", "unknown")

                if source != "unknown":
                    total_classified += 1

                    if source == "heuristic":
                        heuristic_count += 1
                    elif source == "llm":
                        llm_count += 1
                    elif source == "direct":
                        direct_count += 1

            if next_offset is None:
                break
            offset = next_offset

        heuristic_rate = (heuristic_count / total_classified * 100) if total_classified > 0 else 0
        llm_rate = (llm_count / total_classified * 100) if total_classified > 0 else 0

        return {
            "total_classified": total_classified,
            "heuristic_count": heuristic_count,
            "llm_count": llm_count,
            "direct_count": direct_count,
            "heuristic_rate_percent": round(heuristic_rate, 1),
            "llm_rate_percent": round(llm_rate, 1),
            "total_heuristic_keywords": len(CHAVAO_DOMAIN_MAP),
        }

    except Exception as e:
        logger.error("heuristic_hit_rate_error", error=str(e))
        return {}


def get_research_stats(days: int = 30) -> Dict[str, Any]:
    """Aggregate research log stats over recent window."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        with get_session() as session:
            logs: List[ResearchLog] = (
                session.query(ResearchLog)
                .filter(ResearchLog.created_at >= since)
                .order_by(ResearchLog.created_at.desc())
                .all()
            )
            last_hour_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
            last_day_cutoff = datetime.now(timezone.utc) - timedelta(days=1)
            total = len(logs)
            executed = sum(log.executed_queries or 0 for log in logs)
            sources = sum(log.sources_collected or 0 for log in logs)
            avg_cost = float(
                (sum(float(log.cost_usd or 0.0) for log in logs) / total) if total else 0.0
            )
            gap_counter: Counter[str] = Counter()
            daily_counter: Counter[str] = Counter()
            daily_costs: Counter[str] = Counter()
            confidence_deltas: list[float] = []
            queries_last_hour = 0
            cost_last_24h = 0.0
            for log in logs:
                gaps = (log.gap_types or {}) if isinstance(log.gap_types, dict) else {}
                for key, val in gaps.items():
                    if val:
                        gap_counter[key] += 1
                if log.created_at and log.created_at >= last_hour_cutoff:
                    queries_last_hour += log.executed_queries or 0
                if log.created_at and log.created_at >= last_day_cutoff:
                    try:
                        cost_last_24h += float(log.cost_usd or 0.0)
                    except (TypeError, ValueError):
                        pass
                if log.created_at:
                    day_key = log.created_at.date().isoformat()
                    daily_counter[day_key] += 1
                    try:
                        daily_costs[day_key] += float(log.cost_usd or 0.0)
                    except (TypeError, ValueError):
                        pass
                if log.confidence_before is not None and log.confidence_after is not None:
                    confidence_deltas.append(float(log.confidence_after - log.confidence_before))

            trend: list[dict[str, Any]] = []
            if logs:
                start = since.date()
                end = datetime.now(timezone.utc).date()
                current = start
                while current <= end:
                    key = current.isoformat()
                    trend.append(
                        {
                            "date": key,
                            "sessions": daily_counter.get(key, 0),
                            "cost_usd": round(float(daily_costs.get(key, 0.0)), 4),
                        }
                    )
                    current += timedelta(days=1)

            return {
                "since": since.isoformat(),
                "sessions": total,
                "executed_queries": executed,
                "sources_collected": sources,
                "avg_cost_usd": round(avg_cost, 4),
                "gap_counts": gap_counter.most_common(),
                "trend": trend,
                "confidence_deltas": confidence_deltas,
                "queries_last_hour": queries_last_hour,
                "cost_last_24h": round(cost_last_24h, 4),
                "hourly_limit": DEFAULT_RESEARCH_HOURLY_LIMIT,
                "cost_cap_usd": DEFAULT_RESEARCH_COST_CAP_USD,
            }
    except Exception as e:
        logger.error("research_stats_error", error=str(e))
        return {
            "since": since.isoformat(),
            "sessions": 0,
            "executed_queries": 0,
            "sources_collected": 0,
            "avg_cost_usd": 0.0,
            "gap_counts": [],
            "trend": [],
            "confidence_deltas": [],
            "queries_last_hour": 0,
            "cost_last_24h": 0.0,
            "hourly_limit": DEFAULT_RESEARCH_HOURLY_LIMIT,
            "cost_cap_usd": DEFAULT_RESEARCH_COST_CAP_USD,
        }


@router.get("/api/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(collection: str = "knowledge"):
    """Get all dashboard statistics."""
    try:
        return {
            "domain_distribution": get_domain_distribution(collection),
            "ingestion_timeline": get_ingestion_timeline(collection),
            "retrieval_heatmap": get_retrieval_heatmap(),
            "enrichment_coverage": get_enrichment_coverage(collection),
            "cost_tracking": get_cost_tracking(),
            "heuristic_hit_rate": get_heuristic_hit_rate(collection),
            "research_stats": get_research_stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("dashboard_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/research-stats", response_model=Dict[str, Any])
async def get_research_stats_api(days: int = 30):
    """Expose research mode analytics."""
    try:
        return get_research_stats(days=days)
    except Exception as e:
        logger.error("research_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_class=HTMLResponse)
async def dashboard_ui():
    """Serve interactive memory dashboard UI.
    
    The dashboard is now served from a separate template file with
    CSS and JS in their own static files for better maintainability.
    """
    from pathlib import Path
    
    dashboard_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "memory_dashboard.html"
    if dashboard_html.exists():
        return HTMLResponse(content=dashboard_html.read_text(encoding="utf-8"))
    
    # Fallback: Return error message if template not found
    return HTMLResponse(
        content="<h1>Memory Dashboard not found</h1><p>Template file missing at: memory_dashboard.html</p>",
        status_code=404
    )
