"""
Evidence Promotion Workflow (Story 11-6, AC3).
Enables post-ingestion tier promotion with audit trails.

Promotion Rules:
- K4 → K3: Automatic if score >= 0.3
- K3 → K2: Requires dual-persona arbitration (11-5)
- K2 → K1: Requires human reviewer OR governance auto-policy
- K1 → K0: Never (K0 is only direct telemetry)
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID
import structlog

from jarvis.knowledge.tiers import (
    KnowledgeTier,
    can_promote,
    validate_tier_transition,
    TierTransitionError,
)

# Try to import 11-5 arbitration
try:
    from jarvis.knowledge.arbitration import DualPersonaArbitrator, ArbitrationResult
    HAS_ARBITRATION = True
except ImportError:
    HAS_ARBITRATION = False
    DualPersonaArbitrator = None

# Try to import 11-5 audit log
try:
    from jarvis.knowledge.audit import EpistemicAuditLog, EpistemicEventType
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False

logger = structlog.get_logger(__name__)

@dataclass
class PromotionRequest:
    knowledge_unit_id: UUID
    current_tier: KnowledgeTier
    target_tier: KnowledgeTier
    requester: str
    trust_score: float
    content: Optional[str] = None
    metadata: Optional[dict] = None

@dataclass
class PromotionResult:
    approved: bool
    new_tier: KnowledgeTier
    reason: str
    audit_event_id: Optional[str] = None
    arbitration_required: bool = False

class EvidencePromotionWorkflow:
    """
    Implements AC3: Evidence Promotion Workflow.
    
    Promotion Rules:
    - Tier 0 → Tier 1: automatic if score >= 0.5 (Note: K4→K3 in new model)
    - Tier 1 → Tier 2: requires human reviewer OR governance auto-policy
    """
    
    def __init__(
        self, 
        audit_log: Optional["EpistemicAuditLog"] = None,
        arbitrator: Optional["DualPersonaArbitrator"] = None,
    ):
        self.audit_log = audit_log
        self.arbitrator = arbitrator
        
    def can_auto_promote(self, request: PromotionRequest) -> Tuple[bool, str]:
        """Check if automatic promotion is allowed."""
        current = request.current_tier
        target = request.target_tier
        score = request.trust_score
        
        # Validate basic promotion rules
        if not can_promote(current, target):
            return False, f"Invalid promotion path: {current.name} → {target.name}"
        
        # K4 → K3: Auto if score >= 0.3
        if current == KnowledgeTier.K4 and target == KnowledgeTier.K3:
            if score >= 0.3:
                return True, "Auto-promotion: K4→K3, score threshold met"
            return False, f"Score {score} below threshold 0.3"
        
        # K3 → K2: Requires arbitration
        if current == KnowledgeTier.K3 and target == KnowledgeTier.K2:
            return False, "Requires dual-persona arbitration"
        
        # K2 → K1: Requires human/governance
        if current == KnowledgeTier.K2 and target == KnowledgeTier.K1:
            return False, "Requires human reviewer or governance policy"
        
        # K1 → K0: Never allowed via promotion
        if target == KnowledgeTier.K0:
            return False, "K0 can only be assigned at initial ingestion (direct telemetry)"
        
        return False, "Promotion path not recognized"
    
    def request_promotion(self, request: PromotionRequest) -> PromotionResult:
        """
        Process a promotion request through the workflow.
        Returns PromotionResult with approval status.
        """
        logger.info(
            "promotion_request", 
            id=str(request.knowledge_unit_id),
            from_tier=request.current_tier.name,
            to_tier=request.target_tier.name,
            requester=request.requester,
        )
        
        # 1. Check auto-promotion eligibility
        can_auto, reason = self.can_auto_promote(request)
        
        if can_auto:
            # Perform auto-promotion
            return self._execute_promotion(request, reason, authorized_by="auto")
        
        # 2. Check if arbitration is needed (K3 → K2)
        if (request.current_tier == KnowledgeTier.K3 and 
            request.target_tier == KnowledgeTier.K2):
            
            if self.arbitrator and HAS_ARBITRATION and request.content:
                # Run dual-persona arbitration
                arb_result = self.arbitrator.arbitrate(
                    content=request.content,
                    source_type=request.metadata.get("source_type", "unknown"),
                    declared_tier=request.target_tier,
                )
                
                if arb_result.approved:
                    return self._execute_promotion(
                        request, 
                        f"Dual-persona approved: {arb_result.summary}",
                        authorized_by="dual_persona_arbitration"
                    )
                else:
                    return PromotionResult(
                        approved=False,
                        new_tier=request.current_tier,
                        reason=f"Arbitration denied: {arb_result.summary}",
                        arbitration_required=True,
                    )
            else:
                return PromotionResult(
                    approved=False,
                    new_tier=request.current_tier,
                    reason="Arbitration required but arbitrator not available",
                    arbitration_required=True,
                )
        
        # 3. For K2 → K1: Require explicit human authorization
        if (request.current_tier == KnowledgeTier.K2 and 
            request.target_tier == KnowledgeTier.K1):
            return PromotionResult(
                approved=False,
                new_tier=request.current_tier,
                reason="Requires human reviewer or governance policy approval",
            )
        
        # Default: deny
        return PromotionResult(
            approved=False,
            new_tier=request.current_tier,
            reason=reason,
        )
    
    def approve_with_authorization(
        self, 
        request: PromotionRequest, 
        authorized_by: str
    ) -> PromotionResult:
        """
        Approve a promotion with explicit authorization (human/governance).
        For K2 → K1 promotions that require human review.
        """
        if not can_promote(request.current_tier, request.target_tier):
            return PromotionResult(
                approved=False,
                new_tier=request.current_tier,
                reason=f"Invalid promotion: {request.current_tier.name} → {request.target_tier.name}",
            )
        
        return self._execute_promotion(
            request,
            f"Authorized promotion by {authorized_by}",
            authorized_by=authorized_by,
        )
    
    def _execute_promotion(
        self, 
        request: PromotionRequest, 
        reason: str,
        authorized_by: str,
    ) -> PromotionResult:
        """Execute the promotion and log to audit trail."""
        audit_event_id = None
        
        # Log to epistemic audit trail
        if self.audit_log and HAS_AUDIT:
            try:
                event = self.audit_log.log_tier_transition(
                    knowledge_unit_id=request.knowledge_unit_id,
                    event_type=EpistemicEventType.PROMOTION,
                    previous_tier=request.current_tier,
                    new_tier=request.target_tier,
                    reason=reason,
                    authorized_by=authorized_by,
                    metadata={
                        "requester": request.requester,
                        "trust_score": request.trust_score,
                    }
                )
                audit_event_id = str(event.event_id)
            except Exception as e:
                logger.warning("audit_log_failed", error=str(e))
        
        logger.info(
            "promotion_approved",
            id=str(request.knowledge_unit_id),
            new_tier=request.target_tier.name,
            authorized_by=authorized_by,
        )
        
        return PromotionResult(
            approved=True,
            new_tier=request.target_tier,
            reason=reason,
            audit_event_id=audit_event_id,
        )
