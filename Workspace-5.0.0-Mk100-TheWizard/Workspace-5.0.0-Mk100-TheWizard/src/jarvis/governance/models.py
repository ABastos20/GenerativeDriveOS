"""Governance Models - SQLAlchemy models for multi-human governance.

Story 9-1: Multi-Human Governance Model
Implements AC1-4: GovernanceUser, Role enum, Permissions

This module defines:
- GovernanceUser: Extends user concept with governance fields
- Role: Enum for Owner, Admin, Contributor, Observer
- Permission: Model for action → role mapping
- EscalationRule: Escalation triggers and targets
- Escalation: Active escalation instances
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Text, DateTime, Float, Boolean, Integer,
    ForeignKey, Index, UniqueConstraint, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from jarvis.database.models import Base


class Role(str, Enum):
    """User roles in the governance system.
    
    Implements AC2: Role Enum - Owner, Admin, Contributor, Observer
    
    Role hierarchy:
    - OWNER: Full control, constitutional authority
    - ADMIN: Manage users, moderate votes, config changes
    - CONTRIBUTOR: Vote and propose
    - OBSERVER: Read-only access
    """
    OWNER = "owner"
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    OBSERVER = "observer"
    
    @classmethod
    def escalation_chain(cls) -> List["Role"]:
        """Return roles in escalation order (lowest to highest)."""
        return [cls.OBSERVER, cls.CONTRIBUTOR, cls.ADMIN, cls.OWNER]
    
    def can_escalate_to(self) -> Optional["Role"]:
        """Get the next role in escalation chain."""
        chain = self.escalation_chain()
        idx = chain.index(self)
        if idx < len(chain) - 1:
            return chain[idx + 1]
        return None  # Owner is highest, cannot escalate further


class PermissionAction(str, Enum):
    """Permission actions available in the system.
    
    Implements AC6: Permission Categories - vote, propose, amend, override, view
    """
    VIEW = "view"                      # Read access
    VOTE = "vote"                      # Cast votes on proposals
    PROPOSE = "propose"                # Create proposals
    AMEND = "amend"                    # Propose constitutional amendments
    OVERRIDE = "override"              # Override system decisions
    MANAGE_USERS = "manage_users"      # Add/remove users, change roles
    MODERATE = "moderate"              # Moderate proposals and votes
    CONFIGURE = "configure"            # Change system configuration
    ALL = "*"                          # Wildcard for all permissions

    
class PlatformRole(str, Enum):
    """Platform access level (technical/admin).
    
    Distinct from Governance Role.
    - ADMIN: Full system access (logs, config, debug)
    - USER: Standard features
    - OBSERVER: Read-only dashboard
    """
    ADMIN = "admin"
    USER = "user"
    OBSERVER = "observer"


class Persona(str, Enum):
    """AI persona for chat interactions.
    
    Scoped to user preference.
    - IRON_MAN: Sarcastic, technical, confident
    - COPILOT: Minimalist, code-focused, obedient
    - ADVISOR: Socratic, cautious, strategic
    """
    IRON_MAN = "iron_man"
    COPILOT = "copilot"
    ADVISOR = "advisor"


class GovernanceUser(Base):
    """User model for governance participation.
    
    Implements AC1: GovernanceUser Model - Extends base User with governance fields
    
    Each governance user has:
    - Name and email for identification
    - Role determining permissions
    - Trust scores per domain (filled by Story 9-3)
    - Activity tracking
    - Audit fields
    """
    __tablename__ = "governance_users"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Basic identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Optional unmapped field for legacy API compatibility (not persisted)
    email: Optional[str] = None
    
    # OIDC Linkage
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False, default="https://jarvis.sovereign.idp")
    
    # Governance Role (Political Power)
    role: Mapped[str] = mapped_column(
        SQLEnum(Role, name="governance_role", create_type=True),
        default=Role.OBSERVER,
        nullable=False
    )
    
    # Platform Role (Technical Access)
    platform_role: Mapped[str] = mapped_column(
        SQLEnum(PlatformRole, name="platform_role", create_type=True),
        default=PlatformRole.USER,
        nullable=False
    )
    
    # Persona Preference (UX Style)
    preferred_persona: Mapped[str] = mapped_column(
        SQLEnum(Persona, name="user_persona", create_type=True),
        default=Persona.COPILOT,
        nullable=False
    )
    
    # Trust scores per domain (populated by Story 9-3)
    # Format: {"security": 0.8, "architecture": 0.6, ...}
    trust_scores: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSON,
        default=dict,
        nullable=True
    )

    # Trust Metrics (Story 9-3)
    trust_metrics: Mapped["GovernanceTrustScore"] = relationship(
        "GovernanceTrustScore",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Cached permissions (denormalized for performance)
    permissions: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        default=list,
        nullable=True
    )
    
    # Activity tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    last_active: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Audit fields
    invited_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_governance_users_subject_id", "subject_id", "issuer"),
        Index("ix_governance_users_role", "role"),
        Index("ix_governance_users_platform_role", "platform_role"),
        Index("ix_governance_users_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<GovernanceUser {self.name} sub={self.subject_id} role={self.role}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "subject_id": self.subject_id,
            "issuer": self.issuer,
            "role": self.role.value if isinstance(self.role, Role) else self.role,
            "trust_scores": self.trust_scores or {},
            "trust_metrics": self.trust_metrics.to_dict() if self.trust_metrics else None,
            "permissions": self.permissions or [],
            "is_active": self.is_active,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }


class GovernanceTrustScore(Base):
    """Trust score components for a user.
    
    Implements Story 9-3 Trust Model.
    Provides the raw components (E, C, H, R) for the trust calculation.
    """
    __tablename__ = "governance_user_trust_scores"
    __allow_unmapped__ = True
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        unique=True,
        nullable=False
    )
    
    # Trust components (0.0 to 1.0)
    # Epistemic Reliability (Accuracy of beliefs) - 40%
    epistemic_reliability: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Governance Consistency (Alignment stability) - 30%
    governance_consistency: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Historical Integrity (Audit violations) - 20%
    historical_integrity: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Reputation (Web-of-trust) - 10%
    reputation: Mapped[float] = mapped_column(Float, default=0.5)
    
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationship
    user: Mapped["GovernanceUser"] = relationship("GovernanceUser", back_populates="trust_metrics")
    
    def __repr__(self) -> str:
        return f"<GovernanceTrustScore user={self.user_id} E={self.epistemic_reliability}>"
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "epistemic_reliability": self.epistemic_reliability,
            "governance_consistency": self.governance_consistency,
            "historical_integrity": self.historical_integrity,
            "reputation": self.reputation,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

# Back-compat alias for legacy code/tests
TrustScore = GovernanceTrustScore

class Constitution(Base):
    """The Supreme Law.
    
    Implements Story 9-4: Constitutional Framework.
    Stores the immutable constants that govern the system.
    Only one Constitution can be active at a time.
    """
    __tablename__ = "constitutions"
    __allow_unmapped__ = True
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Trust Components Weights (Must sum to 1.0)
    weight_epistemic: Mapped[float] = mapped_column(Float, default=0.4, nullable=False)
    weight_consistency: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    weight_integrity: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    weight_reputation: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    
    # Safety Constraints
    sybil_threshold: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    minority_floor: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)
    anti_elite_multiplier: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    
    # Legitimacy Conservation (Story 9-4)
    # Maximum allowed change in total system weight per epoch (e.g., 0.1 = 10%)
    max_legitimacy_drift: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Constitution active={self.active} created={self.created_at}>"
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "active": self.active,
            "weights": {
                "epistemic": self.weight_epistemic,
                "consistency": self.weight_consistency,
                "integrity": self.weight_integrity,
                "reputation": self.weight_reputation
            },
            "constraints": {
                "sybil_threshold": self.sybil_threshold,
                "minority_floor": self.minority_floor,
                "anti_elite_multiplier": self.anti_elite_multiplier,
                "max_legitimacy_drift": self.max_legitimacy_drift
            }
        }


class Permission(Base):
    """Permission definition for action → role mapping.
    
    Implements AC5: Permission Model - Action → Role mapping
    
    Maps which roles can perform which actions.
    """
    __tablename__ = "permissions"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Permission definition
    action: Mapped[str] = mapped_column(
        SQLEnum(PermissionAction, name="permission_action", create_type=True),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        SQLEnum(Role, name="permission_role", create_type=True),
        nullable=False
    )
    
    # Additional constraints
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    __table_args__ = (
        UniqueConstraint("action", "role", "resource_type", name="uq_permission_action_role"),
        Index("ix_permissions_role", "role"),
        Index("ix_permissions_action", "action"),
    )
    
    def __repr__(self) -> str:
        return f"<Permission {self.role}:{self.action}>"


class EscalationTriggerType(str, Enum):
    """Types of events that trigger escalation.
    
    Implements AC10: Escalation Triggers
    """
    TIE_VOTE = "tie_vote"                    # Proposal vote is tied
    QUORUM_FAILED = "quorum_failed"          # Not enough participation
    CSI_BELOW_THRESHOLD = "csi_below_threshold"  # System stability low
    CONFLICT_THRESHOLD = "conflict_threshold"    # Too many conflicts
    CONSTITUTIONAL_CONFLICT = "constitutional"   # Proposal vs constitution
    MANUAL = "manual"                        # User-requested escalation
    TIMEOUT = "timeout"                      # Decision deadline passed


class EscalationRule(Base):
    """Rule defining when to escalate to higher authority.
    
    Implements AC9: EscalationRule Model - Condition → escalate to higher authority
    
    Rules define triggers and which role handles escalation.
    """
    __tablename__ = "escalation_rules"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Rule definition
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    trigger_type: Mapped[str] = mapped_column(
        SQLEnum(EscalationTriggerType, name="escalation_trigger", create_type=True),
        nullable=False
    )
    
    # Thresholds
    threshold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold_operator: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # <, >, ==, etc.
    
    # Escalation target
    escalate_to_role: Mapped[str] = mapped_column(
        SQLEnum(Role, name="escalate_role", create_type=True),
        default=Role.ADMIN,
        nullable=False
    )
    
    # Timing
    timeout_hours: Mapped[int] = mapped_column(Integer, default=24)
    auto_escalate_further: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Rule metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)  # Lower = higher priority
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    __table_args__ = (
        Index("ix_escalation_rules_trigger", "trigger_type"),
        Index("ix_escalation_rules_active", "is_active"),
        Index("ix_escalation_rules_priority", "priority"),
    )
    
    def __repr__(self) -> str:
        return f"<EscalationRule {self.name} -> {self.escalate_to_role}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "trigger_type": self.trigger_type.value if isinstance(self.trigger_type, EscalationTriggerType) else self.trigger_type,
            "threshold_value": self.threshold_value,
            "escalate_to_role": self.escalate_to_role.value if isinstance(self.escalate_to_role, Role) else self.escalate_to_role,
            "timeout_hours": self.timeout_hours,
            "is_active": self.is_active,
            "priority": self.priority,
        }


class EscalationStatus(str, Enum):
    """Status of an escalation instance."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    ESCALATED_FURTHER = "escalated_further"


class Escalation(Base):
    """Active escalation instance.
    
    Implements AC11: Escalation Chain - Contributor → Admin → Owner
    
    Tracks pending and resolved escalations.
    """
    __tablename__ = "escalations"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # What triggered this escalation
    rule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("escalation_rules.id"),
        nullable=False
    )
    trigger_type: Mapped[str] = mapped_column(
        SQLEnum(EscalationTriggerType, name="esc_trigger", create_type=True),
        nullable=False
    )
    trigger_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Target (what needs resolution)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)  # proposal, conflict, hypothesis
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    
    # Current authority level
    current_role: Mapped[str] = mapped_column(
        SQLEnum(Role, name="current_esc_role", create_type=True),
        nullable=False
    )
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=True
    )
    
    # Status and resolution
    status: Mapped[str] = mapped_column(
        SQLEnum(EscalationStatus, name="escalation_status", create_type=True),
        default=EscalationStatus.PENDING,
        nullable=False
    )
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=True
    )
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Audit
    escalation_chain: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        default=list,
        nullable=True
    )  # History of role escalations
    
    __table_args__ = (
        Index("ix_escalations_status", "status"),
        Index("ix_escalations_target", "target_type", "target_id"),
        Index("ix_escalations_current_role", "current_role"),
        Index("ix_escalations_deadline", "deadline"),
    )
    
    def __repr__(self) -> str:
        return f"<Escalation {self.target_type}:{self.target_id} -> {self.current_role}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "rule_id": str(self.rule_id),
            "trigger_type": self.trigger_type.value if isinstance(self.trigger_type, EscalationTriggerType) else self.trigger_type,
            "trigger_context": self.trigger_context,
            "target_type": self.target_type,
            "target_id": str(self.target_id),
            "current_role": self.current_role.value if isinstance(self.current_role, Role) else self.current_role,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "status": self.status.value if isinstance(self.status, EscalationStatus) else self.status,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "escalation_chain": self.escalation_chain or [],
        }


class AuditLog(Base):
    """Audit trail for governance actions.
    
    Implements AC15: Audit Trail - All role assignments and permission changes logged
    """
    __tablename__ = "governance_audit_log"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # What happened
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    
    # Details
    old_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Renamed from 'metadata' (reserved)
    
    # Who did it
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=True
    )
    actor_type: Mapped[str] = mapped_column(String(50), default="user")  # user, system, api
    
    # When
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    __table_args__ = (
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
        Index("ix_audit_log_action", "action_type"),
        Index("ix_audit_log_actor", "actor_id"),
        Index("ix_audit_log_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action_type} on {self.entity_type}:{self.entity_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "old_value": self.old_value,
            "new_value": self.new_value,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_type": self.actor_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProposalType(str, Enum):
    """Type of proposal.
    
    Implements AC2: Proposal Types
    """
    DECISION = "decision"                      # Normal decision
    CONFIG_CHANGE = "config_change"            # System configuration change
    CONSTITUTIONAL_AMENDMENT = "constitutional_amendment"  # Changing core rules


class ProposalStatus(str, Enum):
    """Lifecycle status of a proposal.
    
    Implements AC3: Proposal Lifecycle
    """
    DRAFT = "draft"
    OPEN = "open"          # Active voting
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Proposal(Base):
    """Governance proposal for decision making.
    
    Implements AC1: Proposal Model
    """
    __tablename__ = "proposals"
    __allow_unmapped__ = True
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Creator
    proposer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=False
    )
    
    # Type and Status
    proposal_type: Mapped[str] = mapped_column(
        SQLEnum(ProposalType, name="proposal_type", create_type=True),
        default=ProposalType.DECISION,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(ProposalStatus, name="proposal_status", create_type=True),
        default=ProposalStatus.DRAFT,
        nullable=False
    )
    
    # Rules
    quorum_required: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0
    approval_threshold: Mapped[float] = mapped_column(Float, default=0.5)  # > 0.5 to pass
    
    # Metadata
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., "jarvis.core"
    
    # Pre-computed results (for cheap reads)
    total_for: Mapped[float] = mapped_column(Float, default=0.0)
    total_against: Mapped[float] = mapped_column(Float, default=0.0)
    total_abstain: Mapped[float] = mapped_column(Float, default=0.0)
    total_weight: Mapped[float] = mapped_column(Float, default=0.0)
    result_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Story 9-5: Governance Locks (Trust Freezing + Legitimacy Snapshot)
    # Frozen trust snapshot at proposal open - prevents mid-vote trust manipulation
    # Format: {"user_id": {"raw_trust": 0.7, "effective_weight": 0.5}, ...}
    frozen_trust_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Total system weight at open - for legitimacy conservation check at resolve
    total_weight_at_open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_proposals_status", "status"),
        Index("ix_proposals_type", "proposal_type"),
        Index("ix_proposals_proposer", "proposer_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Proposal {self.title} status={self.status}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "proposer_id": str(self.proposer_id),
            "proposal_type": self.proposal_type.value if isinstance(self.proposal_type, ProposalType) else self.proposal_type,
            "status": self.status.value if isinstance(self.status, ProposalStatus) else self.status,
            "quorum_required": self.quorum_required,
            "approval_threshold": self.approval_threshold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_reason": self.resolution_reason,
        }


class VoteChoice(str, Enum):
    """Vote choices."""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


class Vote(Base):
    """Vote cast on a proposal.
    
    Implements AC5: Vote Model
    """
    __tablename__ = "votes"
    __allow_unmapped__ = True
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    proposal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("proposals.id"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=False
    )
    
    choice: Mapped[str] = mapped_column(
        SQLEnum(VoteChoice, name="vote_choice", create_type=True),
        nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delegated_from_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_users.id"),
        nullable=True
    )
    
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    
    # One vote per user per proposal
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_vote_proposal_user"),
        Index("ix_votes_proposal", "proposal_id"),
        Index("ix_votes_user", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Vote {self.choice} on {self.proposal_id} by {self.user_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "proposal_id": str(self.proposal_id),
            "user_id": str(self.user_id),
            "choice": self.choice.value if isinstance(self.choice, VoteChoice) else self.choice,
            "weight": self.weight,
            "justification": self.justification,
            "voted_at": self.voted_at.isoformat() if self.voted_at else None,
        }
