"""Stability Index - Cognitive Stability Index (CSI) Computation.

This module computes the CSI formula:
CSI = belief_coherence × evidence_freshness × domain_agreement

Part of Phase 9: Epistemic Autonomy Layer.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import select, func, and_
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


def compute_belief_coherence(session: Session, entity_id: UUID) -> float:
    """Compute coherence: 1 - (conflicts / total_beliefs).
    
    Higher = more coherent beliefs.
    """
    # Count active conflicts for this entity
    conflict_count = session.execute(
        select(func.count(EpistemicConflict.id)).where(
            and_(
                EpistemicConflict.entity_id == entity_id,
                EpistemicConflict.status == "active"
            )
        )
    ).scalar() or 0
    
    # Count total relationships (as proxy for beliefs)
    belief_count = session.execute(
        select(func.count(Relationship.id)).where(
            (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id)
        )
    ).scalar() or 1  # Avoid division by zero
    
    coherence = 1.0 - (conflict_count / max(belief_count, 1))
    return max(0.0, min(1.0, coherence))


def compute_evidence_freshness(session: Session, entity_id: UUID) -> float:
    """Compute freshness: based on how recently evidence was updated.
    
    Higher = more recent evidence.
    """
    # Get the most recent document linked to this entity
    result = session.execute(
        select(func.max(Document.updated_at)).where(
            Document.id.in_(
                select(DocumentEntity.document_id).where(
                    DocumentEntity.entity_id == entity_id
                )
            )
        )
    ).scalar()
    
    if not result:
        return 0.5  # Default for no linked documents
    
    # Calculate freshness based on days since update
    days_since = (datetime.now(timezone.utc) - result).days
    
    # Exponential decay: fresh = 1.0 at 0 days, ~0.5 at 30 days, ~0.1 at 90 days
    freshness = 1.0 / (1.0 + days_since / 30.0)
    return max(0.0, min(1.0, freshness))


def compute_domain_agreement(session: Session, entity_id: UUID) -> float:
    """Compute domain agreement: consistency across domains.
    
    Higher = consistent across domains.
    """
    # Get all domains this entity appears in (via linked documents)
    domains = session.execute(
        select(Document.domain).where(
            Document.id.in_(
                select(DocumentEntity.document_id).where(
                    DocumentEntity.entity_id == entity_id
                )
            )
        ).distinct()
    ).scalars().all()
    
    if len(domains) <= 1:
        return 1.0  # Single domain = no disagreement
    
    # Check for conflicts from different domains
    domain_conflicts = session.execute(
        select(func.count(EpistemicConflict.id)).where(
            and_(
                EpistemicConflict.entity_id == entity_id,
                EpistemicConflict.contradiction_type == "domain",
                EpistemicConflict.status == "active"
            )
        )
    ).scalar() or 0
    
    # Agreement decreases with domain conflicts
    agreement = 1.0 - (domain_conflicts / len(domains))
    return max(0.0, min(1.0, agreement))


def compute_entity_csi(session: Session, entity_id: UUID) -> Dict[str, Any]:
    """Compute CSI for a single entity.
    
    CSI = coherence(0.4) × freshness(0.3) × agreement(0.3)
    """
    coherence = compute_belief_coherence(session, entity_id)
    freshness = compute_evidence_freshness(session, entity_id)
    agreement = compute_domain_agreement(session, entity_id)
    
    # Weighted average
    csi = (coherence * 0.4) + (freshness * 0.3) + (agreement * 0.3)
    
    return {
        "csi": round(csi, 3),
        "components": {
            "coherence": round(coherence, 3),
            "freshness": round(freshness, 3),
            "domain_agreement": round(agreement, 3),
        }
    }


def compute_system_csi() -> Dict[str, Any]:
    """Compute system-wide CSI metrics."""
    with get_session() as session:
        # Get all entities
        entities = session.execute(
            select(Entity.id, Entity.name, Entity.kind)
        ).all()
        
        if not entities:
            return {
                "system_csi": 0.0,
                "entity_count": 0,
                "by_severity": {},
                "top_unstable": [],
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
        
        # Compute CSI for each entity
        csi_scores = []
        unstable = []
        
        for entity_id, name, kind in entities:
            csi_data = compute_entity_csi(session, entity_id)
            csi_scores.append(csi_data["csi"])
            
            if csi_data["csi"] < 0.5:  # Unstable threshold
                unstable.append({
                    "id": str(entity_id),
                    "name": name,
                    "kind": kind,
                    **csi_data,
                })
        
        # System average
        system_csi = sum(csi_scores) / len(csi_scores)
        
        # Categorize by stability
        by_severity = {
            "stable": len([s for s in csi_scores if s >= 0.7]),
            "moderate": len([s for s in csi_scores if 0.5 <= s < 0.7]),
            "unstable": len([s for s in csi_scores if s < 0.5]),
        }
        
        return {
            "system_csi": round(system_csi, 3),
            "entity_count": len(entities),
            "by_severity": by_severity,
            "top_unstable": sorted(unstable, key=lambda x: x["csi"])[:10],
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }


def update_entity_csi() -> int:
    """Recompute and persist CSI for all entities."""
    with get_session() as session:
        entities = session.execute(select(Entity)).scalars().all()
        updated = 0
        
        for entity in entities:
            csi_data = compute_entity_csi(session, entity.id)
            
            # Store in entity properties
            props = entity.properties or {}
            props["csi"] = csi_data["csi"]
            props["csi_components"] = csi_data["components"]
            props["csi_updated_at"] = datetime.now(timezone.utc).isoformat()
            entity.properties = props
            updated += 1
        
        session.commit()
        return updated
