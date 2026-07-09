"""Epistemic Engine - Contradiction Detection and Truth Maintenance.

This module provides the core epistemic self-regulation capabilities:
- Contradiction detection across time, sources, and domains
- Conflict severity assessment
- Resolution tracking

Part of Phase 9: Epistemic Autonomy Layer.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from jarvis.database.models import (
    Entity,
    Relationship,
    DocumentEntity,
    EpistemicConflict,
    BeliefSnapshot,
    Document,
)
from jarvis.database.postgres import get_session


def detect_source_conflicts(session: Session) -> List[Dict[str, Any]]:
    """Detect conflicts where the same entity has different claims from different sources.
    
    Returns list of detected conflicts (not yet persisted).
    """
    conflicts = []
    
    # Get entities with multiple document sources
    subq = (
        select(DocumentEntity.entity_id)
        .group_by(DocumentEntity.entity_id)
        .having(func.count(DocumentEntity.document_id) > 1)
    )
    
    entities_with_multiple_sources = session.execute(
        select(Entity).where(Entity.id.in_(subq))
    ).scalars().all()
    
    for entity in entities_with_multiple_sources:
        # Get all relationships where this entity is source or target
        relationships = session.execute(
            select(Relationship).where(
                or_(
                    Relationship.source_id == entity.id,
                    Relationship.target_id == entity.id
                )
            )
        ).scalars().all()
        
        # Group relationships by type to find potential conflicts
        by_type: Dict[str, List[Relationship]] = {}
        for rel in relationships:
            if rel.relation_type not in by_type:
                by_type[rel.relation_type] = []
            by_type[rel.relation_type].append(rel)
        
        # For now, we detect if same relation_type has different targets
        # This is a simplified heuristic
        for rel_type, rels in by_type.items():
            if len(rels) > 1:
                targets = set(str(r.target_id) for r in rels)
                if len(targets) > 1:
                    # Potential conflict: same entity, same relation type, different targets
                    conflicts.append({
                        "entity_id": entity.id,
                        "fact_1": f"{entity.name} {rel_type} {rels[0].target_id}",
                        "fact_2": f"{entity.name} {rel_type} {rels[1].target_id}",
                        "contradiction_type": "source",
                        "severity": "low",  # Multiple targets might be valid
                    })
    
    return conflicts


def detect_temporal_conflicts(session: Session) -> List[Dict[str, Any]]:
    """Detect conflicts where beliefs about an entity changed over time.
    
    Uses BeliefSnapshot history to find significant changes.
    """
    conflicts = []
    
    # Find entities with belief snapshots that have been superseded
    superseded_beliefs = session.execute(
        select(BeliefSnapshot).where(
            and_(
                BeliefSnapshot.superseded_by.isnot(None),
                BeliefSnapshot.is_current == False
            )
        )
    ).scalars().all()
    
    for old_belief in superseded_beliefs:
        # Get the new belief
        new_belief = session.execute(
            select(BeliefSnapshot).where(BeliefSnapshot.id == old_belief.superseded_by)
        ).scalar_one_or_none()
        
        if new_belief and old_belief.claim != new_belief.claim:
            confidence_delta = abs(float(old_belief.confidence) - float(new_belief.confidence))
            
            conflicts.append({
                "entity_id": old_belief.entity_id,
                "fact_1": old_belief.claim,
                "fact_2": new_belief.claim,
                "contradiction_type": "temporal",
                "confidence_delta": Decimal(str(confidence_delta)),
                "severity": "medium" if confidence_delta > 0.3 else "low",
            })
    
    return conflicts


def run_conflict_detection() -> Dict[str, Any]:
    """Run all conflict detection algorithms and persist new conflicts.
    
    Returns summary of detection run.
    """
    with get_session() as session:
        new_conflicts = 0
        
        # Detect source conflicts
        source_conflicts = detect_source_conflicts(session)
        for conflict_data in source_conflicts:
            # Check if conflict already exists
            existing = session.execute(
                select(EpistemicConflict).where(
                    and_(
                        EpistemicConflict.entity_id == conflict_data["entity_id"],
                        EpistemicConflict.fact_1 == conflict_data["fact_1"],
                        EpistemicConflict.fact_2 == conflict_data["fact_2"],
                        EpistemicConflict.status == "active"
                    )
                )
            ).scalar_one_or_none()
            
            if not existing:
                conflict = EpistemicConflict(
                    entity_id=conflict_data["entity_id"],
                    fact_1=conflict_data["fact_1"],
                    fact_2=conflict_data["fact_2"],
                    contradiction_type=conflict_data["contradiction_type"],
                    severity=conflict_data.get("severity", "medium"),
                    confidence_delta=conflict_data.get("confidence_delta", Decimal("0.0")),
                )
                session.add(conflict)
                new_conflicts += 1
        
        # Detect temporal conflicts
        temporal_conflicts = detect_temporal_conflicts(session)
        for conflict_data in temporal_conflicts:
            existing = session.execute(
                select(EpistemicConflict).where(
                    and_(
                        EpistemicConflict.entity_id == conflict_data["entity_id"],
                        EpistemicConflict.fact_1 == conflict_data["fact_1"],
                        EpistemicConflict.fact_2 == conflict_data["fact_2"],
                        EpistemicConflict.status == "active"
                    )
                )
            ).scalar_one_or_none()
            
            if not existing:
                conflict = EpistemicConflict(
                    entity_id=conflict_data["entity_id"],
                    fact_1=conflict_data["fact_1"],
                    fact_2=conflict_data["fact_2"],
                    contradiction_type=conflict_data["contradiction_type"],
                    severity=conflict_data.get("severity", "medium"),
                    confidence_delta=conflict_data.get("confidence_delta", Decimal("0.0")),
                )
                session.add(conflict)
                new_conflicts += 1
        
        session.commit()
        
        # Get total active conflicts
        total_active = session.execute(
            select(func.count(EpistemicConflict.id)).where(
                EpistemicConflict.status == "active"
            )
        ).scalar() or 0
        
        return {
            "new_conflicts": new_conflicts,
            "total_active": total_active,
            "source_conflicts_checked": len(source_conflicts),
            "temporal_conflicts_checked": len(temporal_conflicts),
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }


def get_active_conflicts(
    session: Session,
    entity_id: Optional[UUID] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get active conflicts, optionally filtered by entity.
    
    Returns list of conflict details with entity info.
    """
    query = (
        select(EpistemicConflict, Entity)
        .join(Entity, EpistemicConflict.entity_id == Entity.id)
        .where(EpistemicConflict.status == "active")
        .order_by(
            EpistemicConflict.severity.desc(),
            EpistemicConflict.detected_at.desc()
        )
        .limit(limit)
    )
    
    if entity_id:
        query = query.where(EpistemicConflict.entity_id == entity_id)
    
    results = session.execute(query).all()
    
    conflicts = []
    for conflict, entity in results:
        conflicts.append({
            "id": str(conflict.id),
            "entity": {
                "id": str(entity.id),
                "name": entity.name,
                "kind": entity.kind,
            },
            "fact_1": conflict.fact_1,
            "fact_2": conflict.fact_2,
            "contradiction_type": conflict.contradiction_type,
            "severity": conflict.severity,
            "confidence_delta": float(conflict.confidence_delta),
            "detected_at": conflict.detected_at.isoformat(),
            "status": conflict.status,
        })
    
    return conflicts


def resolve_conflict(
    session: Session,
    conflict_id: UUID,
    resolution: str,
    resolved_by: str = "human"
) -> Dict[str, Any]:
    """Resolve a conflict with human or system decision.
    
    resolution: human_override | auto_reconciled | fact_1_wins | fact_2_wins
    """
    conflict = session.execute(
        select(EpistemicConflict).where(EpistemicConflict.id == conflict_id)
    ).scalar_one_or_none()
    
    if not conflict:
        return {"error": "Conflict not found"}
    
    conflict.status = "resolved"
    conflict.resolution = resolution
    conflict.resolved_by = resolved_by
    conflict.resolved_at = datetime.now(timezone.utc)
    
    session.commit()
    
    return {
        "id": str(conflict.id),
        "status": "resolved",
        "resolution": resolution,
        "resolved_by": resolved_by,
        "resolved_at": conflict.resolved_at.isoformat(),
    }


def get_conflict_stats(session: Session) -> Dict[str, Any]:
    """Get statistics about epistemic conflicts."""
    # Count by status
    status_counts = session.execute(
        select(
            EpistemicConflict.status,
            func.count(EpistemicConflict.id)
        ).group_by(EpistemicConflict.status)
    ).all()
    
    # Count by type
    type_counts = session.execute(
        select(
            EpistemicConflict.contradiction_type,
            func.count(EpistemicConflict.id)
        ).group_by(EpistemicConflict.contradiction_type)
    ).all()
    
    # Count by severity (active only)
    severity_counts = session.execute(
        select(
            EpistemicConflict.severity,
            func.count(EpistemicConflict.id)
        ).where(EpistemicConflict.status == "active")
        .group_by(EpistemicConflict.severity)
    ).all()
    
    return {
        "by_status": {status: count for status, count in status_counts},
        "by_type": {ctype: count for ctype, count in type_counts},
        "by_severity": {sev: count for sev, count in severity_counts},
    }
