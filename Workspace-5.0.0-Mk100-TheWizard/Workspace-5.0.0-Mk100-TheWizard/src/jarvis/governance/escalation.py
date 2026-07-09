"""Escalation Engine - Automatic escalation to higher authority.

Story 9-1: Multi-Human Governance Model
Implements AC9-14: Escalation rules, triggers, chain, and integration

This module provides:
- EscalationTrigger: Evaluates conditions for escalation
- EscalationEngine: Creates and manages escalations
- Integration with CSI thresholds from Story 8-8
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from jarvis.governance.models import (
    Role,
    EscalationRule,
    Escalation,
    EscalationStatus,
    EscalationTriggerType,
    GovernanceUser,
    AuditLog,
)


class EscalationTrigger:
    """Evaluates conditions that trigger escalation.
    
    Implements AC10: Escalation Triggers
    - Tie votes
    - Quorum not met
    - Constitutional conflict
    - CSI below threshold
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._rules_cache: Optional[List[EscalationRule]] = None
    
    def get_active_rules(self) -> List[EscalationRule]:
        """Get all active escalation rules, ordered by priority."""
        if self._rules_cache is not None:
            return self._rules_cache
        
        result = self.session.execute(
            select(EscalationRule)
            .where(EscalationRule.is_active == True)
            .order_by(EscalationRule.priority)
        )
        self._rules_cache = list(result.scalars().all())
        return self._rules_cache
    
    def check_tie_vote(self, proposal_id: UUID, for_votes: float, against_votes: float) -> Optional[EscalationRule]:
        """Check if a tie vote should trigger escalation.
        
        Args:
            proposal_id: The proposal being voted on
            for_votes: Weighted sum of "for" votes
            against_votes: Weighted sum of "against" votes
            
        Returns:
            EscalationRule if tie detected, None otherwise
        """
        if abs(for_votes - against_votes) < 0.01:  # Effectively tied
            for rule in self.get_active_rules():
                if rule.trigger_type == EscalationTriggerType.TIE_VOTE:
                    return rule
        return None
    
    def check_quorum_failed(self, participation_rate: float) -> Optional[EscalationRule]:
        """Check if failed quorum should trigger escalation.
        
        Args:
            participation_rate: Fraction of eligible voters who voted (0-1)
            
        Returns:
            EscalationRule if quorum failed, None otherwise
        """
        for rule in self.get_active_rules():
            if rule.trigger_type == EscalationTriggerType.QUORUM_FAILED:
                threshold = rule.threshold_value or 0.5
                if participation_rate < threshold:
                    return rule
        return None
    
    def check_csi_threshold(self) -> Optional[EscalationRule]:
        """Check if CSI is below critical threshold.
        
        Implements AC13: Governance Gate - Connect to CSI thresholds from Story 8-8
        Implements AC14: Auto-Escalate when stability drops
        
        Returns:
            EscalationRule if CSI is critical, None otherwise
        """
        # Import here to avoid circular dependency
        from jarvis.memory.governance_node import GovernanceGate
        
        gate = GovernanceGate(self.session)
        governance_level = gate.evaluate_governance_level()
        
        if governance_level in ("critical", "lockdown"):
            for rule in self.get_active_rules():
                if rule.trigger_type == EscalationTriggerType.CSI_BELOW_THRESHOLD:
                    return rule
        
        return None
    
    def check_constitutional_conflict(self, proposal_id: UUID, violation_type: str) -> Optional[EscalationRule]:
        """Check if proposal conflicts with constitution.
        
        Args:
            proposal_id: The proposal being checked
            violation_type: Type of constitutional violation
            
        Returns:
            EscalationRule if conflict detected, None otherwise
        """
        for rule in self.get_active_rules():
            if rule.trigger_type == EscalationTriggerType.CONSTITUTIONAL_CONFLICT:
                return rule
        return None
    
    def check_timeout(self, deadline: datetime) -> Optional[EscalationRule]:
        """Check if decision deadline has passed.
        
        Args:
            deadline: When the decision was due
            
        Returns:
            EscalationRule if timed out, None otherwise
        """
        if datetime.now(timezone.utc) > deadline:
            for rule in self.get_active_rules():
                if rule.trigger_type == EscalationTriggerType.TIMEOUT:
                    return rule
        return None


class EscalationEngine:
    """Creates and manages escalations.
    
    Implements AC11: Escalation Chain - Contributor → Admin → Owner
    
    Usage:
        engine = EscalationEngine(session)
        escalation = engine.create_escalation(
            rule=rule,
            target_type="proposal",
            target_id=proposal_id
        )
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.trigger = EscalationTrigger(session)
    
    def create_escalation(
        self,
        rule: EscalationRule,
        target_type: str,
        target_id: UUID,
        trigger_context: Optional[Dict[str, Any]] = None,
    ) -> Escalation:
        """Create a new escalation.
        
        Args:
            rule: The rule that triggered this escalation
            target_type: Type of target (proposal, conflict, hypothesis)
            target_id: ID of the target
            trigger_context: Additional context about the trigger
            
        Returns:
            The created Escalation
        """
        # Calculate deadline
        deadline = datetime.now(timezone.utc) + timedelta(hours=rule.timeout_hours)
        
        escalation = Escalation(
            rule_id=rule.id,
            trigger_type=rule.trigger_type,
            trigger_context=trigger_context or {},
            target_type=target_type,
            target_id=target_id,
            current_role=rule.escalate_to_role,
            status=EscalationStatus.PENDING,
            deadline=deadline,
            escalation_chain=[rule.escalate_to_role.value if isinstance(rule.escalate_to_role, Role) else rule.escalate_to_role],
        )
        
        self.session.add(escalation)
        self.session.flush()
        
        # Log the escalation creation
        self._log_escalation(escalation, "created")
        
        return escalation
    
    def escalate_further(self, escalation: Escalation) -> Escalation:
        """Escalate to the next level in the chain.
        
        Implements AC11: Escalation Chain - Contributor → Admin → Owner
        
        Args:
            escalation: The escalation to escalate further
            
        Returns:
            Updated escalation
        """
        current_role = escalation.current_role
        if isinstance(current_role, str):
            current_role = Role(current_role)
        
        next_role = current_role.can_escalate_to()
        
        if next_role is None:
            # Already at highest level (Owner)
            return escalation
        
        # Update escalation
        escalation.current_role = next_role
        chain = escalation.escalation_chain or []
        chain.append(next_role.value)
        escalation.escalation_chain = chain
        
        # Reset deadline for next level
        # Get timeout from rule
        result = self.session.execute(
            select(EscalationRule).where(EscalationRule.id == escalation.rule_id)
        )
        rule = result.scalar_one_or_none()
        timeout_hours = rule.timeout_hours if rule else 24
        
        escalation.deadline = datetime.now(timezone.utc) + timedelta(hours=timeout_hours)
        
        self.session.flush()
        self._log_escalation(escalation, "escalated_further")
        
        return escalation
    
    def resolve_escalation(
        self,
        escalation: Escalation,
        resolution: str,
        resolved_by: GovernanceUser,
    ) -> Escalation:
        """Resolve an escalation.
        
        Args:
            escalation: The escalation to resolve
            resolution: How it was resolved
            resolved_by: User who resolved it
            
        Returns:
            Updated escalation
        """
        escalation.status = EscalationStatus.RESOLVED
        escalation.resolution = resolution
        escalation.resolved_by = resolved_by.id
        escalation.resolved_at = datetime.now(timezone.utc)
        
        self.session.flush()
        self._log_escalation(escalation, "resolved", resolved_by.id)
        
        return escalation
    
    def get_pending_escalations(
        self,
        role: Optional[Role] = None,
        user_id: Optional[UUID] = None,
    ) -> List[Escalation]:
        """Get pending escalations.
        
        Args:
            role: Filter by current role level
            user_id: Filter by assigned user
            
        Returns:
            List of pending escalations
        """
        query = select(Escalation).where(
            Escalation.status == EscalationStatus.PENDING
        )
        
        if role is not None:
            query = query.where(Escalation.current_role == role)
        
        if user_id is not None:
            query = query.where(Escalation.assigned_to == user_id)
        
        query = query.order_by(Escalation.created_at)
        
        result = self.session.execute(query)
        return list(result.scalars().all())
    
    def check_expired_escalations(self) -> List[Escalation]:
        """Find and handle expired escalations.
        
        Called by background job to auto-escalate timed out escalations.
        
        Returns:
            List of escalations that were escalated further
        """
        now = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(Escalation).where(
                and_(
                    Escalation.status == EscalationStatus.PENDING,
                    Escalation.deadline < now,
                )
            )
        )
        expired = list(result.scalars().all())
        
        escalated = []
        for escalation in expired:
            # Check if we can escalate further
            current_role = escalation.current_role
            if isinstance(current_role, str):
                current_role = Role(current_role)
            
            if current_role.can_escalate_to() is not None:
                self.escalate_further(escalation)
                escalated.append(escalation)
            else:
                # At highest level, mark as expired
                escalation.status = EscalationStatus.EXPIRED
                self._log_escalation(escalation, "expired")
        
        self.session.flush()
        return escalated
    
    def assign_escalation(
        self,
        escalation: Escalation,
        user: GovernanceUser,
    ) -> Escalation:
        """Assign an escalation to a specific user.
        
        Args:
            escalation: The escalation to assign
            user: User to assign to
            
        Returns:
            Updated escalation
        """
        escalation.assigned_to = user.id
        escalation.status = EscalationStatus.IN_PROGRESS
        
        self.session.flush()
        self._log_escalation(escalation, "assigned", user.id)
        
        return escalation
    
    def _log_escalation(
        self,
        escalation: Escalation,
        action: str,
        actor_id: Optional[UUID] = None,
    ) -> None:
        """Log an escalation action to audit trail.
        
        Implements AC15: Audit Trail
        """
        log = AuditLog(
            action_type=f"escalation_{action}",
            entity_type="escalation",
            entity_id=escalation.id,
            new_value={
                "status": escalation.status.value if isinstance(escalation.status, EscalationStatus) else escalation.status,
                "current_role": escalation.current_role.value if isinstance(escalation.current_role, Role) else escalation.current_role,
                "resolution": escalation.resolution,
            },
            actor_id=actor_id,
            actor_type="user" if actor_id else "system",
        )
        self.session.add(log)


# Convenience functions
def should_escalate(
    session: Session,
    trigger_type: EscalationTriggerType,
    **kwargs,
) -> Optional[EscalationRule]:
    """Check if a condition should trigger escalation.
    
    Args:
        session: Database session
        trigger_type: Type of trigger to check
        **kwargs: Additional arguments for specific trigger types
        
    Returns:
        EscalationRule if should escalate, None otherwise
    """
    trigger = EscalationTrigger(session)
    
    if trigger_type == EscalationTriggerType.TIE_VOTE:
        return trigger.check_tie_vote(
            proposal_id=kwargs.get("proposal_id"),
            for_votes=kwargs.get("for_votes", 0),
            against_votes=kwargs.get("against_votes", 0),
        )
    elif trigger_type == EscalationTriggerType.QUORUM_FAILED:
        return trigger.check_quorum_failed(
            participation_rate=kwargs.get("participation_rate", 0),
        )
    elif trigger_type == EscalationTriggerType.CSI_BELOW_THRESHOLD:
        return trigger.check_csi_threshold()
    elif trigger_type == EscalationTriggerType.CONSTITUTIONAL_CONFLICT:
        return trigger.check_constitutional_conflict(
            proposal_id=kwargs.get("proposal_id"),
            violation_type=kwargs.get("violation_type", ""),
        )
    elif trigger_type == EscalationTriggerType.TIMEOUT:
        return trigger.check_timeout(deadline=kwargs.get("deadline"))
    
    return None


def create_default_escalation_rules(session: Session) -> List[EscalationRule]:
    """Create default escalation rules for the system.
    
    Call this once during system initialization.
    """
    rules = [
        EscalationRule(
            name="Tie Vote Escalation",
            trigger_type=EscalationTriggerType.TIE_VOTE,
            escalate_to_role=Role.ADMIN,
            timeout_hours=48,
            priority=10,
            description="Escalate tied votes to admin for tie-breaking",
        ),
        EscalationRule(
            name="Quorum Failed Escalation",
            trigger_type=EscalationTriggerType.QUORUM_FAILED,
            threshold_value=0.5,
            threshold_operator="<",
            escalate_to_role=Role.ADMIN,
            timeout_hours=72,
            priority=20,
            description="Escalate when less than 50% participation",
        ),
        EscalationRule(
            name="CSI Critical Escalation",
            trigger_type=EscalationTriggerType.CSI_BELOW_THRESHOLD,
            threshold_value=0.3,
            threshold_operator="<",
            escalate_to_role=Role.OWNER,
            timeout_hours=24,
            priority=5,
            description="Escalate directly to owner when system stability critical",
        ),
        EscalationRule(
            name="Constitutional Conflict Escalation",
            trigger_type=EscalationTriggerType.CONSTITUTIONAL_CONFLICT,
            escalate_to_role=Role.OWNER,
            timeout_hours=24,
            priority=1,
            description="Constitutional conflicts always go to owner",
        ),
        EscalationRule(
            name="Timeout Escalation",
            trigger_type=EscalationTriggerType.TIMEOUT,
            escalate_to_role=Role.ADMIN,
            timeout_hours=24,
            auto_escalate_further=True,
            priority=30,
            description="Escalate stale decisions",
        ),
    ]
    
    for rule in rules:
        session.add(rule)
    
    session.flush()
    return rules
