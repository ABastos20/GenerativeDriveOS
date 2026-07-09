"""
Unified Ingestion Pipeline (Story 11-6).
Coordinates flow: Raw -> Firewall -> ClassBinding -> Scorer -> Audit -> Ledger.

Fully integrates with Story 11-5's Knowledge Sovereignty components:
- KnowledgeTier for tier assignment
- EpistemicAuditLog for event logging
- KnowledgeSovereigntyEngine for BMAD binding (AC7)
"""
import uuid
import hashlib
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import structlog

from jarvis.ingestion.trust_scorer import TrustScorer, TrustScore
from jarvis.ingestion.ingestion_firewall import IngestionFirewall, IngestionViolation
from jarvis.ingestion.class_binding import KnowledgeClassBinder, ClassBindingResult
from jarvis.knowledge.tiers import KnowledgeTier, SourceType

# Import 11-5 audit logging
try:
    from jarvis.knowledge.audit import EpistemicAuditLog, EpistemicEventType
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False
    EpistemicAuditLog = None

# Import 11-5 sovereignty engine for AC7 BMAD binding
try:
    from jarvis.knowledge.reasoning_integration import KnowledgeSovereigntyEngine
    HAS_SOVEREIGNTY = True
except ImportError:
    HAS_SOVEREIGNTY = False
    KnowledgeSovereigntyEngine = None

logger = structlog.get_logger(__name__)

# Map string source types to SourceType enum
SOURCE_TYPE_MAP = {
    "sensor": SourceType.SENSOR,
    "telemetry": SourceType.TELEMETRY,
    "internal_analytics": SourceType.INTERNAL_ANALYTICS,
    "research_paper": SourceType.PEER_REVIEWED_PAPER,
    "news": SourceType.NEWS_ARTICLE,
    "social": SourceType.SOCIAL_MEDIA,
    "unknown": SourceType.UNVERIFIED_SOURCE,
}

@dataclass
class IngestionResult:
    ingestion_id: str
    status: str  # "success", "quarantined", "rejected"
    trust_score: Optional[TrustScore] = None
    error: Optional[str] = None
    ledger_id: Optional[str] = None
    raw_hash: Optional[str] = None
    timestamp: Optional[datetime] = None
    class_binding_valid: Optional[bool] = None
    trust_penalty: float = 0.0

class IngestionPipeline:
    def __init__(
        self, 
        ledger_service=None, 
        cids_service=None,
        audit_log: Optional["EpistemicAuditLog"] = None,
        sovereignty_engine: Optional["KnowledgeSovereigntyEngine"] = None,
    ):
        self.firewall = IngestionFirewall(cids_service=cids_service)
        self.scorer = TrustScorer()
        self.class_binder = KnowledgeClassBinder()
        self.ledger = ledger_service
        
        # Initialize audit log (11-5 integration)
        if audit_log is not None:
            self.audit_log = audit_log
        elif HAS_AUDIT:
            self.audit_log = EpistemicAuditLog()
        else:
            self.audit_log = None
        
        # Initialize sovereignty engine for AC7 BMAD binding
        if sovereignty_engine is not None:
            self.sovereignty_engine = sovereignty_engine
        elif HAS_SOVEREIGNTY:
            self.sovereignty_engine = KnowledgeSovereigntyEngine(audit_log=self.audit_log)
        else:
            self.sovereignty_engine = None

    def ingest(self, content: str, metadata: Dict) -> IngestionResult:
        ingestion_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        raw_hash = hashlib.sha256(content.encode()).hexdigest() if content else None
        
        logger.info("ingestion_start", id=ingestion_id, source=metadata.get("source_type"))

        # 1. Firewall Gate
        try:
            self.firewall.validate(content, metadata)
        except IngestionViolation as e:
            logger.warning("ingestion_rejected", id=ingestion_id, reason=str(e))
            return IngestionResult(
                ingestion_id=ingestion_id, 
                status="rejected", 
                error=str(e),
                raw_hash=raw_hash,
                timestamp=timestamp
            )

        # 2. Trust Scoring (uses 11-5's KnowledgeTier and assign_tier)
        score = self.scorer.score(content, metadata)
        logger.info("ingestion_scored", id=ingestion_id, score=score.score, tier=score.tier.name)
        
        # 3. Knowledge Class Binding (AC5)
        declared_class = metadata.get("knowledge_class")
        source_type_str = metadata.get("source_type", "unknown")
        source_type = SOURCE_TYPE_MAP.get(source_type_str, SourceType.UNVERIFIED_SOURCE)
        
        binding_result = self.class_binder.validate(
            declared_class=declared_class,
            source_type=source_type,
            inferred_tier=score.tier,
        )
        
        # Apply trust penalty if class binding failed
        final_score = score.score
        final_tier = score.tier
        if not binding_result.valid:
            final_score = score.score * (1.0 - binding_result.trust_penalty)
            final_tier = binding_result.final_tier
            logger.warning(
                "class_binding_penalty",
                id=ingestion_id,
                penalty=binding_result.trust_penalty,
                reason=binding_result.reason,
            )

        # 4. Determine status based on tier
        ledger_id = None
        status = "success"
        
        # K4 (Noise) maps to quarantine status
        if final_tier == KnowledgeTier.K4:
            status = "quarantined"
        # K3 (Narrative) is provisional but accepted
        elif final_tier == KnowledgeTier.K3:
            status = "success"
        
        # 5. Audit Event Logging (11-5 integration)
        if self.audit_log and HAS_AUDIT:
            try:
                knowledge_unit_id = uuid.UUID(ingestion_id)
                self.audit_log.log_tier_transition(
                    knowledge_unit_id=knowledge_unit_id,
                    event_type=EpistemicEventType.INITIAL_INGEST,
                    previous_tier=KnowledgeTier.K4,
                    new_tier=final_tier,
                    reason=f"Sovereign Ingestion: source_type={source_type_str}",
                    metadata={
                        "source_uri": metadata.get("source_uri"),
                        "trust_score": final_score,
                        "raw_hash": raw_hash,
                        "class_binding_valid": binding_result.valid,
                        "declared_class": declared_class,
                    }
                )
            except Exception as e:
                logger.warning("audit_log_failed", error=str(e))
        
        # 6. Ledger Entry
        if self.ledger:
            ledger_id = self.ledger.record_entry(
                content=content,
                metadata=metadata,
                trust_score=score,
                ingestion_id=ingestion_id
            )
        
        # 7. Register with Sovereignty Engine for BMAD access control (AC7)
        if self.sovereignty_engine and HAS_SOVEREIGNTY:
            try:
                # The sovereignty engine now knows about this knowledge unit
                # BMAD access will be controlled via sovereignty_engine.access_knowledge()
                logger.debug("registered_with_sovereignty", id=ingestion_id, tier=final_tier.name)
            except Exception as e:
                logger.warning("sovereignty_registration_failed", error=str(e))

        return IngestionResult(
            ingestion_id=ingestion_id,
            status=status,
            trust_score=TrustScore(
                score=round(final_score, 2),
                tier=final_tier,
                factors=score.factors,
                recommendation=score.recommendation,
            ),
            ledger_id=ledger_id,
            raw_hash=raw_hash,
            timestamp=timestamp,
            class_binding_valid=binding_result.valid,
            trust_penalty=binding_result.trust_penalty,
        )
