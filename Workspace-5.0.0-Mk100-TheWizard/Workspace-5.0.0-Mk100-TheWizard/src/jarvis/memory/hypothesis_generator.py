"""Hypothesis Generator - Autonomous Hypothesis Creation.

This module generates testable hypotheses when the system detects:
- High contradiction regions (>3 conflicts in cluster)
- Sparse graph regions (<5 relationships for important entity)
- High uncertainty clusters (avg confidence < 0.5)

Part of Phase 9: Epistemic Autonomy Layer.
Note: DORMANT until Epic 8 & 9 governance rules complete.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from jarvis.database.models import (
    Entity,
    Relationship,
    EpistemicConflict,
    Hypothesis,
)
from jarvis.database.postgres import get_session


# Trigger thresholds (configurable via governance)
CONFLICT_THRESHOLD = 3  # Conflicts per cluster for trigger
SPARSE_THRESHOLD = 5    # Min relationships for important entity
UNCERTAINTY_THRESHOLD = 0.5  # Max avg confidence for uncertain cluster


def detect_high_conflict_regions(session: Session) -> List[Dict[str, Any]]:
    """Find entities/regions with high contradiction density.
    
    Returns regions that could benefit from hypothesis testing.
    """
    # Group conflicts by entity
    conflict_counts = session.execute(
        select(
            EpistemicConflict.entity_id,
            func.count(EpistemicConflict.id).label("conflict_count")
        )
        .where(EpistemicConflict.status == "active")
        .group_by(EpistemicConflict.entity_id)
        .having(func.count(EpistemicConflict.id) >= CONFLICT_THRESHOLD)
    ).all()
    
    regions = []
    for entity_id, count in conflict_counts:
        entity = session.execute(
            select(Entity).where(Entity.id == entity_id)
        ).scalar_one_or_none()
        
        if entity:
            regions.append({
                "entity_id": str(entity_id),
                "entity_name": entity.name,
                "entity_kind": entity.kind,
                "conflict_count": count,
                "trigger_type": "high_conflict",
            })
    
    return regions


def detect_sparse_regions(session: Session) -> List[Dict[str, Any]]:
    """Find important entities with sparse relationship coverage.
    
    Important = has PageRank or is frequently referenced.
    """
    # Get entities with PageRank (important) but few relationships
    entities = session.execute(select(Entity)).scalars().all()
    
    sparse = []
    for entity in entities:
        # Check if entity has PageRank (is important)
        pagerank = entity.properties.get("pagerank", 0) if entity.properties else 0
        if pagerank < 1.0:  # Not important enough
            continue
        
        # Count relationships
        rel_count = session.execute(
            select(func.count(Relationship.id)).where(
                or_(
                    Relationship.source_id == entity.id,
                    Relationship.target_id == entity.id
                )
            )
        ).scalar() or 0
        
        if rel_count < SPARSE_THRESHOLD:
            sparse.append({
                "entity_id": str(entity.id),
                "entity_name": entity.name,
                "entity_kind": entity.kind,
                "pagerank": pagerank,
                "relationship_count": rel_count,
                "trigger_type": "sparse_region",
            })
    
    return sparse


def generate_hypothesis_from_conflict(
    session: Session,
    entity_id: UUID,
    conflicts: List[EpistemicConflict],
) -> Optional[Hypothesis]:
    """Generate a hypothesis to resolve conflicting beliefs.
    
    Returns hypothesis for investigation.
    """
    if not conflicts:
        return None
    
    entity = session.execute(
        select(Entity).where(Entity.id == entity_id)
    ).scalar_one_or_none()
    
    if not entity:
        return None
    
    # Construct hypothesis statement
    conflict_summary = f"{len(conflicts)} conflicting beliefs about {entity.name}"
    statement = f"The contradictions about '{entity.name}' may be resolved by examining temporal context or source reliability."
    
    # Construct validation plan
    validation_plan = [
        f"search:latest research on {entity.name}",
        "verify:check source document dates",
        "ask_user:request clarification on conflicting facts",
    ]
    
    hypothesis = Hypothesis(
        statement=statement,
        confidence=Decimal("0.3"),  # Low initial confidence
        trigger_type="contradiction",
        supporting_entities=[str(entity_id)],
        contradicting_entities=[str(c.entity_id) for c in conflicts],
        validation_plan=validation_plan,
        status="pending",
    )
    
    return hypothesis


def generate_hypothesis_from_sparse(
    session: Session,
    entity_id: UUID,
    pagerank: float,
) -> Optional[Hypothesis]:
    """Generate a hypothesis for sparse graph regions.
    
    Suggests expanding knowledge about important but under-documented entities.
    """
    entity = session.execute(
        select(Entity).where(Entity.id == entity_id)
    ).scalar_one_or_none()
    
    if not entity:
        return None
    
    statement = f"'{entity.name}' has high importance (PageRank={pagerank:.2f}) but sparse documentation. Additional research may reveal important relationships."
    
    validation_plan = [
        f"search:comprehensive overview of {entity.name}",
        "ingest:related documents about this topic",
        "expand:find related entities and relationships",
    ]
    
    hypothesis = Hypothesis(
        statement=statement,
        confidence=Decimal("0.4"),
        trigger_type="sparse_region",
        supporting_entities=[str(entity_id)],
        contradicting_entities=[],
        validation_plan=validation_plan,
        status="pending",
    )
    
    return hypothesis


def run_hypothesis_generation() -> Dict[str, Any]:
    """Run hypothesis generation algorithms.
    
    Returns summary of generated hypotheses.
    
    Note: GOVERNANCE GATE - Hypotheses are generated but NOT acted upon
    until Epic 9 governance is complete.
    """
    with get_session() as session:
        generated = 0
        
        # 1. Generate from conflict regions
        conflict_regions = detect_high_conflict_regions(session)
        for region in conflict_regions:
            entity_id = UUID(region["entity_id"])
            
            # Check if hypothesis already exists for this entity
            existing = session.execute(
                select(Hypothesis).where(
                    and_(
                        Hypothesis.supporting_entities.contains([str(entity_id)]),
                        Hypothesis.status == "pending"
                    )
                )
            ).scalar_one_or_none()
            
            if existing:
                continue
            
            # Get conflicts for this entity
            conflicts = session.execute(
                select(EpistemicConflict).where(
                    and_(
                        EpistemicConflict.entity_id == entity_id,
                        EpistemicConflict.status == "active"
                    )
                )
            ).scalars().all()
            
            hyp = generate_hypothesis_from_conflict(session, entity_id, conflicts)
            if hyp:
                session.add(hyp)
                generated += 1
        
        # 2. Generate from sparse regions
        sparse_regions = detect_sparse_regions(session)
        for region in sparse_regions[:10]:  # Limit to top 10
            entity_id = UUID(region["entity_id"])
            
            existing = session.execute(
                select(Hypothesis).where(
                    and_(
                        Hypothesis.supporting_entities.contains([str(entity_id)]),
                        Hypothesis.status == "pending"
                    )
                )
            ).scalar_one_or_none()
            
            if existing:
                continue
            
            hyp = generate_hypothesis_from_sparse(
                session, entity_id, region["pagerank"]
            )
            if hyp:
                session.add(hyp)
                generated += 1
        
        session.commit()
        
        # Get total pending
        total_pending = session.execute(
            select(func.count(Hypothesis.id)).where(
                Hypothesis.status == "pending"
            )
        ).scalar() or 0
        
        return {
            "status": "dormant",  # GOVERNANCE: Not activated
            "message": "Hypotheses generated but NOT acted upon (awaiting governance)",
            "generated": generated,
            "total_pending": total_pending,
            "conflict_regions_scanned": len(conflict_regions),
            "sparse_regions_scanned": len(sparse_regions),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def get_pending_hypotheses(
    session: Session,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get pending hypotheses awaiting validation."""
    hypotheses = session.execute(
        select(Hypothesis)
        .where(Hypothesis.status == "pending")
        .order_by(Hypothesis.created_at.desc())
        .limit(limit)
    ).scalars().all()
    
    return [
        {
            "id": str(h.id),
            "statement": h.statement,
            "confidence": float(h.confidence),
            "trigger_type": h.trigger_type,
            "supporting_entities": h.supporting_entities,
            "validation_plan": h.validation_plan,
            "status": h.status,
            "created_at": h.created_at.isoformat(),
        }
        for h in hypotheses
    ]


def update_hypothesis_status(
    session: Session,
    hypothesis_id: UUID,
    new_status: str,
    validated_by: str = "system",
) -> Dict[str, Any]:
    """Update hypothesis status.
    
    new_status: pending | validating | validated | rejected | escalated
    """
    hypothesis = session.execute(
        select(Hypothesis).where(Hypothesis.id == hypothesis_id)
    ).scalar_one_or_none()
    
    if not hypothesis:
        return {"error": "Hypothesis not found"}
    
    hypothesis.status = new_status
    if new_status in ("validated", "rejected"):
        hypothesis.validated_at = datetime.now(timezone.utc)
    
    session.commit()
    
    return {
        "id": str(hypothesis.id),
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
