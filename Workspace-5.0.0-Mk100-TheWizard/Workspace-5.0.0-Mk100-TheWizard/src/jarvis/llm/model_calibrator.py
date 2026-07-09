"""Model Calibrator - Dynamic LLM Model Selection and Performance Tracking.

This module provides:
- Performance tracking per model per domain
- Dynamic model selection based on historical performance
- Hallucination and conflict rate tracking

Part of Phase 9: Epistemic Autonomy Layer.
Note: DORMANT until Epic 8 & 9 governance rules complete.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, update
from sqlalchemy.orm import Session

from jarvis.database.models import ModelPerformance
from jarvis.database.postgres import get_session


def record_model_call(
    session: Session,
    model_name: str,
    domain: str,
    latency_ms: float,
    is_hallucination: bool = False,
    generated_conflict: bool = False,
) -> None:
    """Record a model call and update performance metrics.
    
    Called after each LLM invocation to track performance.
    """
    # Find or create performance record
    perf = session.execute(
        select(ModelPerformance).where(
            and_(
                ModelPerformance.model_name == model_name,
                ModelPerformance.domain == domain
            )
        )
    ).scalar_one_or_none()
    
    if not perf:
        perf = ModelPerformance(
            model_name=model_name,
            domain=domain,
            total_calls=0,
            avg_latency_ms=Decimal("0.0"),
            hallucination_count=0,
            conflict_generation_rate=Decimal("0.0"),
        )
        session.add(perf)
    
    # Update metrics
    old_total = perf.total_calls
    perf.total_calls += 1
    
    # Rolling average for latency
    old_avg = float(perf.avg_latency_ms)
    perf.avg_latency_ms = Decimal(str(
        (old_avg * old_total + latency_ms) / perf.total_calls
    ))
    
    # Track hallucinations
    if is_hallucination:
        perf.hallucination_count += 1
    
    # Update conflict generation rate
    if generated_conflict:
        conflict_count = session.execute(
            select(func.count()).where(
                and_(
                    ModelPerformance.model_name == model_name,
                    ModelPerformance.domain == domain
                )
            )
        ).scalar() or 0
        perf.conflict_generation_rate = Decimal(str(
            conflict_count / max(perf.total_calls, 1)
        ))
    
    perf.last_used = datetime.now(timezone.utc)


def get_model_performance(
    session: Session,
    model_name: Optional[str] = None,
    domain: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get performance metrics for models, optionally filtered."""
    query = select(ModelPerformance)
    
    if model_name:
        query = query.where(ModelPerformance.model_name == model_name)
    if domain:
        query = query.where(ModelPerformance.domain == domain)
    
    query = query.order_by(
        ModelPerformance.domain,
        ModelPerformance.model_name
    )
    
    results = session.execute(query).scalars().all()
    
    return [
        {
            "id": str(r.id),
            "model_name": r.model_name,
            "domain": r.domain,
            "total_calls": r.total_calls,
            "avg_latency_ms": float(r.avg_latency_ms),
            "hallucination_count": r.hallucination_count,
            "hallucination_rate": r.hallucination_count / max(r.total_calls, 1),
            "conflict_generation_rate": float(r.conflict_generation_rate),
            "token_efficiency": float(r.token_efficiency),
            "last_used": r.last_used.isoformat() if r.last_used else None,
            "updated_at": r.updated_at.isoformat(),
        }
        for r in results
    ]


def select_best_model_for_domain(domain: str) -> str:
    """Select the best model for a domain based on historical performance.
    
    Ranking criteria (in order):
    1. Lowest hallucination rate
    2. Lowest conflict generation rate
    3. Lowest latency
    
    Returns default model if no performance data exists.
    
    Note: GOVERNANCE GATE - This function is dormant until Epic 9 approval.
    """
    with get_session() as session:
        performances = session.execute(
            select(ModelPerformance)
            .where(ModelPerformance.domain == domain)
            .order_by(
                ModelPerformance.hallucination_count.asc(),
                ModelPerformance.conflict_generation_rate.asc(),
                ModelPerformance.avg_latency_ms.asc()
            )
        ).scalars().all()
        
        if not performances:
            # Default model when no data
            return "gemini-2.5-flash"
        
        # Return the best performer
        return performances[0].model_name


def get_model_rankings() -> Dict[str, Any]:
    """Get model rankings across all domains.
    
    Returns summary of which models are best for which domains.
    """
    with get_session() as session:
        # Get all performance records
        all_perfs = session.execute(
            select(ModelPerformance)
        ).scalars().all()
        
        if not all_perfs:
            return {
                "message": "No performance data yet",
                "rankings": {},
                "recommendation": "Use default model: gemini-2.5-flash",
            }
        
        # Group by domain
        by_domain: Dict[str, List[ModelPerformance]] = {}
        for perf in all_perfs:
            if perf.domain not in by_domain:
                by_domain[perf.domain] = []
            by_domain[perf.domain].append(perf)
        
        # Rank within each domain
        rankings = {}
        for domain, perfs in by_domain.items():
            sorted_perfs = sorted(
                perfs,
                key=lambda p: (
                    p.hallucination_count / max(p.total_calls, 1),
                    float(p.conflict_generation_rate),
                    float(p.avg_latency_ms)
                )
            )
            
            rankings[domain] = {
                "best_model": sorted_perfs[0].model_name,
                "models": [
                    {
                        "model": p.model_name,
                        "calls": p.total_calls,
                        "hallucination_rate": round(
                            p.hallucination_count / max(p.total_calls, 1), 3
                        ),
                        "latency_ms": float(p.avg_latency_ms),
                    }
                    for p in sorted_perfs
                ]
            }
        
        return {
            "domains_tracked": len(rankings),
            "rankings": rankings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def mark_hallucination(
    session: Session,
    model_name: str,
    domain: str,
) -> None:
    """Mark a response as a hallucination (post-hoc correction).
    
    Called when a user or system identifies false information.
    """
    perf = session.execute(
        select(ModelPerformance).where(
            and_(
                ModelPerformance.model_name == model_name,
                ModelPerformance.domain == domain
            )
        )
    ).scalar_one_or_none()
    
    if perf:
        perf.hallucination_count += 1
        session.commit()
