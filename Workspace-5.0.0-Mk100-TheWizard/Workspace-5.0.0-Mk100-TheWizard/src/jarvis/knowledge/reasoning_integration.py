"""ReasoningEngine Integration for Knowledge Sovereignty (Story 11-5, Lock 7).

This module integrates epistemic sovereignty with the ReasoningEngine and BMAD.
It enforces the boundaries of what BMAD can and cannot do with knowledge.

BMAD Permissions (AC #7):
✅ BMAD may:
  - Read all knowledge classes
  - Propose hypotheses
  - Query knowledge tiers
  - Request tier information

❌ BMAD may NOT:
  - Promote hypotheses to evidence
  - Upgrade tier without authorization
  - Bypass knowledge usage policy
  - Directly modify trust weights

This is how autonomous reasoning is bounded by epistemic constraints.

References:
- [Story 11-5, AC #7: BMAD/Reasoning Binding]
- [Lock 7: Epistemic Sovereignty]
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID

from src.jarvis.knowledge.tiers import KnowledgeTier
from src.jarvis.knowledge.usage_policy import (
    UsageClass,
    KnowledgeUsagePolicy,
    ConstitutionalDenial,
)
from src.jarvis.knowledge.audit import EpistemicAuditLog, EpistemicEventType


class ReasoningContext(str, Enum):
    """Reasoning context types that map to usage classes."""
    EXECUTION = "execution"          # Tool execution, code generation
    GOVERNANCE = "governance"        # Governance decisions
    STRATEGY = "strategy"           # Strategic planning
    HYPOTHESIS = "hypothesis"        # Hypothesis generation
    EXPLORATION = "exploration"      # General exploration/ideation


# Mapping from reasoning context to usage class
REASONING_TO_USAGE_MAP: dict[ReasoningContext, UsageClass] = {
    ReasoningContext.EXECUTION: UsageClass.EXECUTION_GUIDANCE,
    ReasoningContext.GOVERNANCE: UsageClass.GOVERNANCE,
    ReasoningContext.STRATEGY: UsageClass.STRATEGY,
    ReasoningContext.HYPOTHESIS: UsageClass.IDEATION,
    ReasoningContext.EXPLORATION: UsageClass.IDEATION,
}


@dataclass
class KnowledgeAccessResult:
    """Result of knowledge access attempt.

    Attributes:
        allowed: Whether access was permitted
        knowledge_unit_id: ID of knowledge unit
        tier: Knowledge tier
        content: Knowledge content (if allowed)
        reason: Reason for decision
        trust: Current trust score (optional)
    """
    allowed: bool
    knowledge_unit_id: UUID
    tier: KnowledgeTier
    content: Optional[str]
    reason: str
    trust: Optional[float] = None


@dataclass
class HypothesisRecord:
    """Record of a hypothesis proposed by BMAD.

    Hypotheses are not promoted to evidence without authorization.
    They remain tracked but do not influence critical reasoning.

    Attributes:
        hypothesis_id: Unique hypothesis ID
        content: Hypothesis content
        proposed_by: Agent/system that proposed it
        tier: Proposed tier (always starts at K4)
        confidence: Confidence score
        supporting_evidence: IDs of supporting knowledge units
        status: pending | approved | rejected
    """
    hypothesis_id: UUID
    content: str
    proposed_by: str
    tier: KnowledgeTier = KnowledgeTier.K4  # Always starts as noise
    confidence: float = 0.0
    supporting_evidence: list[UUID] = None
    status: str = "pending"

    def __post_init__(self):
        if self.supporting_evidence is None:
            self.supporting_evidence = []


class KnowledgeSovereigntyEngine:
    """Integration layer between ReasoningEngine and epistemic sovereignty.

    Implements AC #7: Enforce BMAD boundaries and usage policy.

    This engine ensures that autonomous reasoning respects epistemic constraints:
    - Usage policy enforcement per reasoning context
    - Read-only access for BMAD
    - Hypothesis tracking without auto-promotion
    - Audit logging of all access attempts
    """

    def __init__(
        self,
        usage_policy: Optional[KnowledgeUsagePolicy] = None,
        audit_log: Optional[EpistemicAuditLog] = None,
        enable_strict_mode: bool = True,
    ):
        """Initialize knowledge sovereignty engine.

        Args:
            usage_policy: Usage policy engine (creates default if None)
            audit_log: Audit log (creates default if None)
            enable_strict_mode: Whether to raise exceptions on violations
        """
        self.usage_policy = usage_policy or KnowledgeUsagePolicy(
            enable_strict_mode=enable_strict_mode
        )
        self.audit_log = audit_log or EpistemicAuditLog()
        self.enable_strict_mode = enable_strict_mode
        self.hypotheses: dict[UUID, HypothesisRecord] = {}

    def access_knowledge(
        self,
        knowledge_unit_id: UUID,
        tier: KnowledgeTier,
        content: str,
        reasoning_context: ReasoningContext,
        requester: str = "reasoning_engine",
        trust: Optional[float] = None,
    ) -> KnowledgeAccessResult:
        """Access knowledge unit with usage policy enforcement.

        Args:
            knowledge_unit_id: ID of knowledge unit
            tier: Knowledge tier
            content: Knowledge content
            reasoning_context: Reasoning context
            requester: Identity of requester
            trust: Current trust score (optional)

        Returns:
            KnowledgeAccessResult with access decision

        Raises:
            ConstitutionalDenial: If strict mode enabled and access denied
        """
        # Map reasoning context to usage class
        usage_class = REASONING_TO_USAGE_MAP.get(
            reasoning_context,
            UsageClass.IDEATION,  # Default to most permissive
        )

        # Check usage policy
        policy_result = self.usage_policy.check_usage(
            knowledge_unit_id=knowledge_unit_id,
            tier=tier,
            usage_class=usage_class,
            context=f"ReasoningEngine access in {reasoning_context.value} context",
        )

        # Log access attempt (violation or success)
        if not policy_result.allowed:
            self.audit_log.log_usage_violation(
                knowledge_unit_id=knowledge_unit_id,
                tier=tier,
                usage_class=usage_class.value,
                allowed_tiers=[t.value for t in self.usage_policy.get_allowed_tiers(usage_class)],
                reason=policy_result.reason,
                context=f"Requester: {requester}, Context: {reasoning_context.value}",
            )

        # Return result
        if policy_result.allowed:
            return KnowledgeAccessResult(
                allowed=True,
                knowledge_unit_id=knowledge_unit_id,
                tier=tier,
                content=content,
                reason=policy_result.reason,
                trust=trust,
            )
        else:
            # Access denied
            if self.enable_strict_mode:
                raise ConstitutionalDenial(policy_result.violation)

            return KnowledgeAccessResult(
                allowed=False,
                knowledge_unit_id=knowledge_unit_id,
                tier=tier,
                content=None,  # No content returned
                reason=policy_result.reason,
                trust=trust,
            )

    def propose_hypothesis(
        self,
        content: str,
        proposed_by: str,
        confidence: float,
        supporting_evidence: Optional[list[UUID]] = None,
    ) -> HypothesisRecord:
        """Propose a hypothesis (BMAD is allowed to do this).

        Hypotheses start at K4 (noise) and require authorization for promotion.
        This allows BMAD to generate ideas without contaminating evidence.

        Args:
            content: Hypothesis content
            proposed_by: Agent/system proposing
            confidence: Confidence score [0, 1]
            supporting_evidence: IDs of supporting knowledge units

        Returns:
            HypothesisRecord

        Raises:
            ValueError: If confidence out of bounds
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {confidence}")

        from uuid import uuid4

        hypothesis = HypothesisRecord(
            hypothesis_id=uuid4(),
            content=content,
            proposed_by=proposed_by,
            tier=KnowledgeTier.K4,  # Always starts as noise
            confidence=confidence,
            supporting_evidence=supporting_evidence or [],
            status="pending",
        )

        # Store hypothesis
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis

        # Log hypothesis proposal (not a promotion)
        event = self._create_event(
            event_type=EpistemicEventType.INITIAL_INGEST,
            knowledge_unit_id=hypothesis.hypothesis_id,
            reason=f"Hypothesis proposed by {proposed_by}",
            metadata={
                "hypothesis": True,
                "confidence": confidence,
                "proposed_by": proposed_by,
            },
        )
        self.audit_log.log_event(event)

        return hypothesis

    def attempt_tier_promotion(
        self,
        knowledge_unit_id: UUID,
        current_tier: KnowledgeTier,
        target_tier: KnowledgeTier,
        requester: str,
    ) -> tuple[bool, str]:
        """Attempt tier promotion (requires authorization).

        BMAD is NOT allowed to promote tiers without authorization.
        Only governance or authorized systems can promote.

        Args:
            knowledge_unit_id: ID of knowledge unit
            current_tier: Current tier
            target_tier: Proposed target tier
            requester: Identity of requester

        Returns:
            Tuple of (success, reason)
        """
        # Check if requester is authorized
        authorized_requesters = {"governance", "human", "admin"}

        if requester.lower() not in authorized_requesters:
            reason = (
                f"Tier promotion denied: {requester} is not authorized. "
                f"Only {authorized_requesters} can promote tiers."
            )

            # Log unauthorized attempt
            self.audit_log.log_tier_transition(
                knowledge_unit_id=knowledge_unit_id,
                event_type=EpistemicEventType.PROMOTION,
                previous_tier=current_tier,
                new_tier=target_tier,
                reason=f"UNAUTHORIZED ATTEMPT by {requester}",
                authorized_by=requester,
            )

            return False, reason

        # Authorized promotion
        return True, f"Promotion authorized by {requester}"

    def get_hypothesis(self, hypothesis_id: UUID) -> Optional[HypothesisRecord]:
        """Retrieve hypothesis by ID.

        Args:
            hypothesis_id: Hypothesis ID

        Returns:
            HypothesisRecord or None if not found
        """
        return self.hypotheses.get(hypothesis_id)

    def list_hypotheses(
        self,
        proposed_by: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[HypothesisRecord]:
        """List hypotheses with optional filtering.

        Args:
            proposed_by: Filter by proposer (optional)
            status: Filter by status (optional)

        Returns:
            List of matching hypotheses
        """
        hypotheses = list(self.hypotheses.values())

        if proposed_by is not None:
            hypotheses = [h for h in hypotheses if h.proposed_by == proposed_by]

        if status is not None:
            hypotheses = [h for h in hypotheses if h.status == status]

        return hypotheses

    def approve_hypothesis(
        self,
        hypothesis_id: UUID,
        approved_by: str,
    ) -> tuple[bool, str]:
        """Approve hypothesis for potential promotion.

        Note: This only marks it approved - actual tier promotion
        requires dual-persona arbitration from AC #3.

        Args:
            hypothesis_id: Hypothesis ID
            approved_by: Identity of approver

        Returns:
            Tuple of (success, reason)
        """
        hypothesis = self.hypotheses.get(hypothesis_id)

        if hypothesis is None:
            return False, f"Hypothesis {hypothesis_id} not found"

        hypothesis.status = "approved"

        # Log approval
        self.audit_log.log_tier_transition(
            knowledge_unit_id=hypothesis_id,
            event_type=EpistemicEventType.PROMOTION,
            previous_tier=hypothesis.tier,
            new_tier=hypothesis.tier,  # Not promoted yet
            reason=f"Hypothesis approved by {approved_by}, pending arbitration",
            authorized_by=approved_by,
        )

        return True, f"Hypothesis approved by {approved_by}"

    def reject_hypothesis(
        self,
        hypothesis_id: UUID,
        rejected_by: str,
        reason: str,
    ) -> tuple[bool, str]:
        """Reject hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            rejected_by: Identity of rejector
            reason: Reason for rejection

        Returns:
            Tuple of (success, message)
        """
        hypothesis = self.hypotheses.get(hypothesis_id)

        if hypothesis is None:
            return False, f"Hypothesis {hypothesis_id} not found"

        hypothesis.status = "rejected"

        # Log rejection
        self.audit_log.log_tier_transition(
            knowledge_unit_id=hypothesis_id,
            event_type=EpistemicEventType.DEMOTION,
            previous_tier=hypothesis.tier,
            new_tier=hypothesis.tier,
            reason=f"Hypothesis rejected by {rejected_by}: {reason}",
            authorized_by=rejected_by,
        )

        return True, f"Hypothesis rejected: {reason}"

    def get_allowed_tiers_for_context(
        self,
        reasoning_context: ReasoningContext,
    ) -> set[KnowledgeTier]:
        """Get allowed knowledge tiers for a reasoning context.

        Args:
            reasoning_context: Reasoning context

        Returns:
            Set of allowed tiers
        """
        usage_class = REASONING_TO_USAGE_MAP.get(
            reasoning_context,
            UsageClass.IDEATION,
        )

        return self.usage_policy.get_allowed_tiers(usage_class)

    def filter_knowledge_by_context(
        self,
        knowledge_units: list[tuple[UUID, KnowledgeTier]],
        reasoning_context: ReasoningContext,
    ) -> list[UUID]:
        """Filter knowledge units to only those allowed for context.

        Args:
            knowledge_units: List of (id, tier) tuples
            reasoning_context: Reasoning context

        Returns:
            List of allowed knowledge unit IDs
        """
        usage_class = REASONING_TO_USAGE_MAP.get(
            reasoning_context,
            UsageClass.IDEATION,
        )

        return self.usage_policy.filter_allowed_knowledge(
            knowledge_units=knowledge_units,
            usage_class=usage_class,
        )

    def get_access_statistics(self) -> dict:
        """Get statistics on knowledge access and violations.

        Returns:
            Dictionary with access statistics
        """
        return {
            "total_hypotheses": len(self.hypotheses),
            "hypotheses_by_status": self._count_hypotheses_by_status(),
            "usage_violations": self.usage_policy.get_usage_statistics(),
            "audit_events": self.audit_log.get_event_statistics(),
        }

    def _count_hypotheses_by_status(self) -> dict[str, int]:
        """Count hypotheses by status."""
        counts = {}
        for hypothesis in self.hypotheses.values():
            counts[hypothesis.status] = counts.get(hypothesis.status, 0) + 1
        return counts

    def _create_event(
        self,
        event_type: EpistemicEventType,
        knowledge_unit_id: UUID,
        reason: str,
        metadata: Optional[dict] = None,
    ):
        """Helper to create epistemic event."""
        from uuid import uuid4
        from datetime import datetime, timezone
        from src.jarvis.knowledge.audit import EpistemicEvent

        return EpistemicEvent(
            event_id=uuid4(),
            event_type=event_type,
            knowledge_unit_id=knowledge_unit_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            metadata=metadata or {},
        )


# Convenience function for ReasoningEngine integration
def create_sovereignty_engine(
    enable_strict_mode: bool = True,
) -> KnowledgeSovereigntyEngine:
    """Create a knowledge sovereignty engine for ReasoningEngine.

    Args:
        enable_strict_mode: Whether to raise exceptions on violations

    Returns:
        KnowledgeSovereigntyEngine instance
    """
    return KnowledgeSovereigntyEngine(enable_strict_mode=enable_strict_mode)
