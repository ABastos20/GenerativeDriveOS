"""Belief Tracker - Temporal Belief History and Drift Detection.

This module provides:
- Belief snapshot creation and versioning
- Temporal belief queries
- Drift detection (significant belief changes)

Part of Phase 9: Epistemic Autonomy Layer.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, update
from sqlalchemy.orm import Session

from jarvis.database.models import (
    Entity,
    BeliefSnapshot,
    Document,
)
from jarvis.database.postgres import get_session


def create_belief_snapshot(
    session: Session,
    entity_id: UUID,
    claim: str,
    claim_type: str = "property",
    confidence: float = 1.0,
    source_doc_id: Optional[UUID] = None,
) -> BeliefSnapshot:
    """Create a new belief snapshot for an entity.
    
    Automatically supersedes existing beliefs of the same type.
    """
    # Find current belief of same type to supersede
    current = session.execute(
        select(BeliefSnapshot).where(
            and_(
                BeliefSnapshot.entity_id == entity_id,
                BeliefSnapshot.claim_type == claim_type,
                BeliefSnapshot.is_current == True
            )
        )
    ).scalar_one_or_none()
    
    # Create new snapshot
    new_snapshot = BeliefSnapshot(
        entity_id=entity_id,
        claim=claim,
        claim_type=claim_type,
        confidence=Decimal(str(confidence)),
        source_doc_id=source_doc_id,
        is_current=True,
    )
    session.add(new_snapshot)
    session.flush()  # Get the ID
    
    # Supersede old belief if exists
    if current:
        current.is_current = False
        current.superseded_by = new_snapshot.id
    
    return new_snapshot


def get_belief_timeline(
    session: Session,
    entity_id: UUID,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get temporal belief history for an entity.
    
    Returns beliefs ordered by time (newest first).
    """
    beliefs = session.execute(
        select(BeliefSnapshot)
        .where(BeliefSnapshot.entity_id == entity_id)
        .order_by(BeliefSnapshot.created_at.desc())
        .limit(limit)
    ).scalars().all()
    
    result = []
    for belief in beliefs:
        result.append({
            "id": str(belief.id),
            "claim": belief.claim,
            "claim_type": belief.claim_type,
            "confidence": float(belief.confidence),
            "is_current": belief.is_current,
            "source_doc_id": str(belief.source_doc_id) if belief.source_doc_id else None,
            "superseded_by": str(belief.superseded_by) if belief.superseded_by else None,
            "created_at": belief.created_at.isoformat(),
        })
    
    return result


def detect_belief_drift(
    session: Session,
    entity_id: Optional[UUID] = None,
    threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """Detect entities with significant belief drift.
    
    Drift = significant change in confidence or claim over time.
    """
    drifts = []
    
    # Query for superseded beliefs with significant confidence change
    query = (
        select(BeliefSnapshot)
        .where(
            and_(
                BeliefSnapshot.superseded_by.isnot(None),
                BeliefSnapshot.is_current == False
            )
        )
    )
    
    if entity_id:
        query = query.where(BeliefSnapshot.entity_id == entity_id)
    
    old_beliefs = session.execute(query).scalars().all()
    
    for old_belief in old_beliefs:
        # Get the new belief
        new_belief = session.execute(
            select(BeliefSnapshot).where(BeliefSnapshot.id == old_belief.superseded_by)
        ).scalar_one_or_none()
        
        if not new_belief:
            continue
        
        confidence_change = abs(float(old_belief.confidence) - float(new_belief.confidence))
        claim_changed = old_belief.claim != new_belief.claim
        
        if confidence_change >= threshold or claim_changed:
            # Get entity info
            entity = session.execute(
                select(Entity).where(Entity.id == old_belief.entity_id)
            ).scalar_one_or_none()
            
            drifts.append({
                "entity_id": str(old_belief.entity_id),
                "entity_name": entity.name if entity else "Unknown",
                "claim_type": old_belief.claim_type,
                "old_claim": old_belief.claim,
                "new_claim": new_belief.claim,
                "old_confidence": float(old_belief.confidence),
                "new_confidence": float(new_belief.confidence),
                "confidence_change": confidence_change,
                "claim_changed": claim_changed,
                "old_timestamp": old_belief.created_at.isoformat(),
                "new_timestamp": new_belief.created_at.isoformat(),
            })
    
    return drifts


def get_current_beliefs(
    session: Session,
    entity_id: UUID
) -> List[Dict[str, Any]]:
    """Get all current (not superseded) beliefs for an entity."""
    beliefs = session.execute(
        select(BeliefSnapshot)
        .where(
            and_(
                BeliefSnapshot.entity_id == entity_id,
                BeliefSnapshot.is_current == True
            )
        )
        .order_by(BeliefSnapshot.claim_type)
    ).scalars().all()
    
    return [
        {
            "id": str(b.id),
            "claim": b.claim,
            "claim_type": b.claim_type,
            "confidence": float(b.confidence),
            "created_at": b.created_at.isoformat(),
        }
        for b in beliefs
    ]


def get_belief_volatility(
    session: Session,
    entity_id: UUID,
    days: int = 90
) -> Dict[str, Any]:
    """Calculate belief volatility for an entity over a time period.
    
    Volatility = number of belief changes / time period
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Count superseded beliefs in period
    changes = session.execute(
        select(func.count(BeliefSnapshot.id)).where(
            and_(
                BeliefSnapshot.entity_id == entity_id,
                BeliefSnapshot.superseded_by.isnot(None),
                BeliefSnapshot.created_at >= since
            )
        )
    ).scalar() or 0
    
    # Count total current beliefs
    total = session.execute(
        select(func.count(BeliefSnapshot.id)).where(
            and_(
                BeliefSnapshot.entity_id == entity_id,
                BeliefSnapshot.is_current == True
            )
        )
    ).scalar() or 1
    
    volatility = changes / max(total, 1)
    
    return {
        "entity_id": str(entity_id),
        "period_days": days,
        "changes": changes,
        "current_beliefs": total,
        "volatility": round(volatility, 3),
        "stability": "stable" if volatility < 0.2 else "moderate" if volatility < 0.5 else "volatile",
    }
