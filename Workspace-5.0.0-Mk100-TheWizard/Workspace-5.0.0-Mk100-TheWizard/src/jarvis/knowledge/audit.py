"""Epistemic Audit Log (Story 11-5, Lock 7).

This module implements comprehensive audit logging for all epistemic events:
- Tier promotions and demotions
- Trust decay and refresh events
- Contradiction detection and penalties
- Freeze events from dual-persona disagreement
- Usage policy violations

All events are immutably logged for forensic reconstruction and C-IDS integration.

Event Schema (AC #6):
{
    "event": "promotion | decay | contradiction | freeze | usage_violation",
    "knowledge_id": "...",
    "previous_tier": "K3",
    "new_tier": "K2",
    "reason": "dual_persona_pass",
    "timestamp": "utc"
}

References:
- [Story 11-5, AC #6: Epistemic Audit Log]
- [Lock 7: Epistemic Sovereignty]
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from src.jarvis.knowledge.tiers import KnowledgeTier

import structlog

logger = structlog.get_logger(__name__)


class EpistemicEventType(str, Enum):
    """Types of epistemic events that can be audited."""
    PROMOTION = "promotion"
    DEMOTION = "demotion"
    DECAY = "decay"
    REFRESH = "refresh"
    CONTRADICTION = "contradiction"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"
    USAGE_VIOLATION = "usage_violation"
    ARCHIVE = "archive"
    INITIAL_INGEST = "initial_ingest"


@dataclass
class EpistemicEvent:
    """Base epistemic event for audit trail.

    All epistemic transformations emit events for accountability
    and forensic reconstruction.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of epistemic event
        knowledge_unit_id: ID of affected knowledge unit
        timestamp: UTC timestamp of event
        reason: Human-readable reason for event
        metadata: Additional event-specific data
    """
    event_id: UUID
    event_type: EpistemicEventType
    knowledge_unit_id: UUID
    timestamp: datetime
    reason: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        data = asdict(self)
        # Convert enums and timestamps to strings
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        data["event_id"] = str(self.event_id)
        data["knowledge_unit_id"] = str(self.knowledge_unit_id)
        return data

    def to_json_schema(self) -> dict:
        """Convert to JSON schema matching AC #6 specification."""
        return {
            "event": self.event_type.value,
            "knowledge_id": str(self.knowledge_unit_id),
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            **self.metadata,
        }


@dataclass
class TierTransitionEvent(EpistemicEvent):
    """Event for tier promotions and demotions.

    Records transitions between knowledge tiers with full audit trail.
    """
    previous_tier: KnowledgeTier = field(default=KnowledgeTier.K4)
    new_tier: KnowledgeTier = field(default=KnowledgeTier.K4)
    analyst_verdict: Optional[bool] = None
    adversary_verdict: Optional[bool] = None
    authorized_by: Optional[str] = None

    def to_json_schema(self) -> dict:
        """Convert to JSON schema matching AC #6 specification."""
        base = super().to_json_schema()
        base.update({
            "previous_tier": self.previous_tier.value,
            "new_tier": self.new_tier.value,
        })
        if self.analyst_verdict is not None:
            base["analyst_verdict"] = self.analyst_verdict
        if self.adversary_verdict is not None:
            base["adversary_verdict"] = self.adversary_verdict
        if self.authorized_by:
            base["authorized_by"] = self.authorized_by
        return base


@dataclass
class TrustEvent(EpistemicEvent):
    """Event for trust decay, refresh, or penalty."""
    previous_trust: float = 0.0
    new_trust: float = 0.0
    decay_rate: Optional[float] = None
    tier: Optional[KnowledgeTier] = None

    def to_json_schema(self) -> dict:
        """Convert to JSON schema."""
        base = super().to_json_schema()
        base.update({
            "previous_trust": round(self.previous_trust, 3),
            "new_trust": round(self.new_trust, 3),
        })
        if self.decay_rate is not None:
            base["decay_rate"] = self.decay_rate
        if self.tier:
            base["tier"] = self.tier.value
        return base


@dataclass
class ContradictionEvent(EpistemicEvent):
    """Event for contradiction detection and resolution."""
    contradicting_unit_id: UUID = field(default_factory=lambda: UUID(int=0))
    tier: KnowledgeTier = KnowledgeTier.K4
    contradicting_tier: KnowledgeTier = KnowledgeTier.K4
    penalty_applied: bool = False
    penalty_factor: Optional[float] = None
    resolution: str = "pending"

    def to_json_schema(self) -> dict:
        """Convert to JSON schema."""
        base = super().to_json_schema()
        base.update({
            "contradicting_unit_id": str(self.contradicting_unit_id),
            "tier": self.tier.value,
            "contradicting_tier": self.contradicting_tier.value,
            "penalty_applied": self.penalty_applied,
            "resolution": self.resolution,
        })
        if self.penalty_factor is not None:
            base["penalty_factor"] = self.penalty_factor
        return base


@dataclass
class FreezeEvent(EpistemicEvent):
    """Event for dual-persona freeze/unfreeze."""
    tier: KnowledgeTier = KnowledgeTier.K4
    analyst_verdict: Optional[bool] = None
    adversary_verdict: Optional[bool] = None
    cids_alert_id: Optional[str] = None

    def to_json_schema(self) -> dict:
        """Convert to JSON schema."""
        base = super().to_json_schema()
        base.update({
            "tier": self.tier.value,
        })
        if self.analyst_verdict is not None:
            base["analyst_verdict"] = self.analyst_verdict
        if self.adversary_verdict is not None:
            base["adversary_verdict"] = self.adversary_verdict
        if self.cids_alert_id:
            base["cids_alert_id"] = self.cids_alert_id
        return base


@dataclass
class UsageViolationEvent(EpistemicEvent):
    """Event for usage policy violations."""
    tier: KnowledgeTier = KnowledgeTier.K4
    usage_class: str = "unknown"
    allowed_tiers: list[str] = field(default_factory=list)
    context: str = ""

    def to_json_schema(self) -> dict:
        """Convert to JSON schema."""
        base = super().to_json_schema()
        base.update({
            "tier": self.tier.value,
            "usage_class": self.usage_class,
            "allowed_tiers": self.allowed_tiers,
            "context": self.context,
        })
        return base


class EpistemicAuditLog:
    """Epistemic audit log for all knowledge sovereignty events.

    Implements AC #6: Comprehensive audit trail for epistemic events.

    The audit log provides:
    - Immutable event recording
    - Queryable audit trail
    - C-IDS integration hooks
    - Forensic reconstruction capability
    
    Story 11-5.2: Refactored to use pluggable sink architecture.
    Events fan-out to all configured sinks with error isolation.
    """

    def __init__(self, sinks: list | None = None):
        """Initialize audit log with optional sinks.
        
        Args:
            sinks: List of EpistemicAuditSink implementations.
                   If None, defaults to [InMemorySink()] for backward compatibility.
        """
        # Import here to avoid circular dependency
        from src.jarvis.knowledge.audit_sinks import InMemorySink
        
        if sinks is None:
            # Default: in-memory sink for backward compatibility
            self._memory_sink = InMemorySink()
            self._sinks = [self._memory_sink]
        else:
            self._sinks = list(sinks)
            # Find memory sink if present for query methods
            self._memory_sink = None
            for sink in self._sinks:
                if isinstance(sink, InMemorySink):
                    self._memory_sink = sink
                    break
            # If no memory sink, create one for queries
            if self._memory_sink is None:
                self._memory_sink = InMemorySink()
                self._sinks.insert(0, self._memory_sink)
        
        # Backward compatibility: expose events list from memory sink
        self.events = self._memory_sink.events
        self._event_index = self._memory_sink._event_index
        self._type_index = self._memory_sink._type_index

    def log_event(self, event: EpistemicEvent) -> None:
        """Log an epistemic event to all configured sinks.

        Args:
            event: Event to log
            
        Note:
            Fan-out to all sinks with error isolation per AC5.
            Sink failures are logged but don't crash the caller.
        """
        for sink in self._sinks:
            try:
                sink.handle_event(event)
            except Exception as e:
                # Error isolation: log but don't raise
                logger.warning(
                    "sink_write_failed",
                    sink=type(sink).__name__,
                    error=str(e),
                )

    def log_tier_transition(
        self,
        knowledge_unit_id: UUID,
        event_type: EpistemicEventType,
        previous_tier: KnowledgeTier,
        new_tier: KnowledgeTier,
        reason: str,
        analyst_verdict: Optional[bool] = None,
        adversary_verdict: Optional[bool] = None,
        authorized_by: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> TierTransitionEvent:
        """Log a tier transition event.

        Args:
            knowledge_unit_id: ID of knowledge unit
            event_type: PROMOTION or DEMOTION
            previous_tier: Original tier
            new_tier: New tier
            reason: Reason for transition
            analyst_verdict: Analyst approval (optional)
            adversary_verdict: Adversary approval (optional)
            authorized_by: Authorization identity (optional)
            metadata: Additional metadata (optional)

        Returns:
            Logged event
        """
        from uuid import uuid4

        event = TierTransitionEvent(
            event_id=uuid4(),
            event_type=event_type,
            knowledge_unit_id=knowledge_unit_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            metadata=metadata or {},
            previous_tier=previous_tier,
            new_tier=new_tier,
            analyst_verdict=analyst_verdict,
            adversary_verdict=adversary_verdict,
            authorized_by=authorized_by,
        )

        self.log_event(event)
        return event

    def log_trust_event(
        self,
        knowledge_unit_id: UUID,
        event_type: EpistemicEventType,
        previous_trust: float,
        new_trust: float,
        reason: str,
        decay_rate: Optional[float] = None,
        tier: Optional[KnowledgeTier] = None,
        metadata: Optional[dict] = None,
    ) -> TrustEvent:
        """Log a trust-related event.

        Args:
            knowledge_unit_id: ID of knowledge unit
            event_type: DECAY, REFRESH, or CONTRADICTION
            previous_trust: Trust before event
            new_trust: Trust after event
            reason: Reason for event
            decay_rate: Decay rate (optional)
            tier: Knowledge tier (optional)
            metadata: Additional metadata (optional)

        Returns:
            Logged event
        """
        from uuid import uuid4

        event = TrustEvent(
            event_id=uuid4(),
            event_type=event_type,
            knowledge_unit_id=knowledge_unit_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            metadata=metadata or {},
            previous_trust=previous_trust,
            new_trust=new_trust,
            decay_rate=decay_rate,
            tier=tier,
        )

        self.log_event(event)
        return event

    def log_contradiction(
        self,
        knowledge_unit_id: UUID,
        contradicting_unit_id: UUID,
        tier: KnowledgeTier,
        contradicting_tier: KnowledgeTier,
        reason: str,
        penalty_applied: bool = False,
        penalty_factor: Optional[float] = None,
        resolution: str = "pending",
        metadata: Optional[dict] = None,
    ) -> ContradictionEvent:
        """Log a contradiction event.

        Args:
            knowledge_unit_id: ID of knowledge unit
            contradicting_unit_id: ID of contradicting unit
            tier: Tier of knowledge unit
            contradicting_tier: Tier of contradicting unit
            reason: Description of contradiction
            penalty_applied: Whether penalty was applied
            penalty_factor: Penalty factor if applied
            resolution: Resolution status
            metadata: Additional metadata (optional)

        Returns:
            Logged event
        """
        from uuid import uuid4

        event = ContradictionEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.CONTRADICTION,
            knowledge_unit_id=knowledge_unit_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            metadata=metadata or {},
            contradicting_unit_id=contradicting_unit_id,
            tier=tier,
            contradicting_tier=contradicting_tier,
            penalty_applied=penalty_applied,
            penalty_factor=penalty_factor,
            resolution=resolution,
        )

        self.log_event(event)
        return event

    def log_freeze(
        self,
        knowledge_unit_id: UUID,
        tier: KnowledgeTier,
        reason: str,
        analyst_verdict: Optional[bool] = None,
        adversary_verdict: Optional[bool] = None,
        cids_alert_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> FreezeEvent:
        """Log a freeze event from dual-persona disagreement.

        Args:
            knowledge_unit_id: ID of knowledge unit
            tier: Knowledge tier
            reason: Reason for freeze
            analyst_verdict: Analyst verdict
            adversary_verdict: Adversary verdict
            cids_alert_id: C-IDS alert ID if escalated
            metadata: Additional metadata (optional)

        Returns:
            Logged event
        """
        from uuid import uuid4

        event = FreezeEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.FREEZE,
            knowledge_unit_id=knowledge_unit_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            metadata=metadata or {},
            tier=tier,
            analyst_verdict=analyst_verdict,
            adversary_verdict=adversary_verdict,
            cids_alert_id=cids_alert_id,
        )

        self.log_event(event)
        return event

    def log_usage_violation(
        self,
        knowledge_unit_id: UUID,
        tier: KnowledgeTier,
        usage_class: str,
        allowed_tiers: list[str],
        reason: str,
        context: str = "",
        metadata: Optional[dict] = None,
    ) -> UsageViolationEvent:
        """Log a usage policy violation.

        Args:
            knowledge_unit_id: ID of knowledge unit
            tier: Knowledge tier
            usage_class: Attempted usage class
            allowed_tiers: Tiers allowed for usage class
            reason: Violation description
            context: Additional context
            metadata: Additional metadata (optional)

        Returns:
            Logged event
        """
        from uuid import uuid4

        event = UsageViolationEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.USAGE_VIOLATION,
            knowledge_unit_id=knowledge_unit_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            metadata=metadata or {},
            tier=tier,
            usage_class=usage_class,
            allowed_tiers=allowed_tiers,
            context=context,
        )

        self.log_event(event)
        return event

    def query_by_knowledge_unit(self, knowledge_unit_id: UUID) -> list[EpistemicEvent]:
        """Query all events for a specific knowledge unit.

        Args:
            knowledge_unit_id: ID to query

        Returns:
            List of events for this knowledge unit
        """
        return self._event_index.get(knowledge_unit_id, []).copy()

    def query_by_type(self, event_type: EpistemicEventType) -> list[EpistemicEvent]:
        """Query all events of a specific type.

        Args:
            event_type: Event type to query

        Returns:
            List of events of this type
        """
        return self._type_index.get(event_type, []).copy()

    def query_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[EpistemicEvent]:
        """Query events within a time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            List of events in time range
        """
        return [
            event for event in self.events
            if start_time <= event.timestamp <= end_time
        ]

    def query_complex(
        self,
        knowledge_unit_id: Optional[UUID] = None,
        event_type: Optional[EpistemicEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[EpistemicEvent]:
        """Complex query with multiple filters.

        Args:
            knowledge_unit_id: Filter by knowledge unit (optional)
            event_type: Filter by event type (optional)
            start_time: Filter by start time (optional)
            end_time: Filter by end time (optional)

        Returns:
            List of events matching all filters
        """
        results = self.events

        if knowledge_unit_id is not None:
            results = [e for e in results if e.knowledge_unit_id == knowledge_unit_id]

        if event_type is not None:
            results = [e for e in results if e.event_type == event_type]

        if start_time is not None:
            results = [e for e in results if e.timestamp >= start_time]

        if end_time is not None:
            results = [e for e in results if e.timestamp <= end_time]

        return results

    def get_event_count(self) -> int:
        """Get total number of events logged.

        Returns:
            Event count
        """
        return len(self.events)

    def get_event_statistics(self) -> dict:
        """Get statistics on logged events.

        Returns:
            Dictionary with event statistics
        """
        if not self.events:
            return {
                "total_events": 0,
                "by_type": {},
                "by_knowledge_unit": {},
            }

        by_type = {}
        by_ku = {}

        for event in self.events:
            # Count by type
            type_name = event.event_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # Count by knowledge unit
            ku_id = str(event.knowledge_unit_id)
            by_ku[ku_id] = by_ku.get(ku_id, 0) + 1

        return {
            "total_events": len(self.events),
            "by_type": by_type,
            "by_knowledge_unit": by_ku,
        }

    def export_events_json(
        self,
        start_index: int = 0,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Export events to JSON format matching AC #6 schema.

        Args:
            start_index: Starting index (default: 0)
            limit: Maximum number of events (default: all)

        Returns:
            List of events in JSON schema format
        """
        end_index = start_index + limit if limit else len(self.events)
        events_slice = self.events[start_index:end_index]

        return [event.to_json_schema() for event in events_slice]

    def get_forensic_timeline(
        self,
        knowledge_unit_id: UUID
    ) -> list[dict]:
        """Get complete forensic timeline for a knowledge unit.

        Args:
            knowledge_unit_id: ID to reconstruct

        Returns:
            Chronologically ordered list of all events
        """
        events = self.query_by_knowledge_unit(knowledge_unit_id)
        events.sort(key=lambda e: e.timestamp)

        return [event.to_json_schema() for event in events]
