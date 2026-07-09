"""Unit tests for Epistemic Audit Log (Story 11-5, Task 6).

Tests audit event logging, querying, and forensic reconstruction.
Coverage target: ≥90% per AC #6 requirements.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

from src.jarvis.knowledge.audit import (
    EpistemicEventType,
    EpistemicEvent,
    TierTransitionEvent,
    TrustEvent,
    ContradictionEvent,
    FreezeEvent,
    UsageViolationEvent,
    EpistemicAuditLog,
)
from src.jarvis.knowledge.tiers import KnowledgeTier


class TestEpistemicEvent:
    """Test base EpistemicEvent."""

    def test_create_event(self):
        """Test creating basic epistemic event."""
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Trust decay applied",
            metadata={"decay_rate": 0.01},
        )

        assert event.event_type == EpistemicEventType.DECAY
        assert "decay_rate" in event.metadata

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event_id = uuid4()
        ku_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        event = EpistemicEvent(
            event_id=event_id,
            event_type=EpistemicEventType.PROMOTION,
            knowledge_unit_id=ku_id,
            timestamp=timestamp,
            reason="Test",
        )

        data = event.to_dict()

        assert data["event_type"] == "promotion"
        assert data["event_id"] == str(event_id)
        assert data["knowledge_unit_id"] == str(ku_id)
        assert isinstance(data["timestamp"], str)

    def test_to_json_schema(self):
        """Test AC #6 JSON schema format."""
        ku_id = uuid4()
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.FREEZE,
            knowledge_unit_id=ku_id,
            timestamp=datetime.now(timezone.utc),
            reason="Dual-persona disagreement",
        )

        json_data = event.to_json_schema()

        # Verify AC #6 schema fields
        assert "event" in json_data
        assert "knowledge_id" in json_data
        assert "reason" in json_data
        assert "timestamp" in json_data
        assert json_data["event"] == "freeze"


class TestTierTransitionEvent:
    """Test tier transition events."""

    def test_promotion_event(self):
        """Test tier promotion event."""
        event = TierTransitionEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Dual-persona approval",
            previous_tier=KnowledgeTier.K3,
            new_tier=KnowledgeTier.K2,
            analyst_verdict=True,
            adversary_verdict=True,
            authorized_by="governance",
        )

        assert event.previous_tier == KnowledgeTier.K3
        assert event.new_tier == KnowledgeTier.K2
        assert event.analyst_verdict is True
        assert event.adversary_verdict is True

    def test_json_schema_with_verdicts(self):
        """Test JSON schema includes verdicts."""
        event = TierTransitionEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
            previous_tier=KnowledgeTier.K3,
            new_tier=KnowledgeTier.K2,
            analyst_verdict=True,
            adversary_verdict=True,
        )

        json_data = event.to_json_schema()

        assert json_data["previous_tier"] == "narrative"
        assert json_data["new_tier"] == "trust_scored_external"
        assert json_data["analyst_verdict"] is True
        assert json_data["adversary_verdict"] is True


class TestTrustEvent:
    """Test trust events."""

    def test_decay_event(self):
        """Test trust decay event."""
        event = TrustEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Automatic decay",
            previous_trust=0.9,
            new_trust=0.85,
            decay_rate=0.01,
            tier=KnowledgeTier.K3,
        )

        assert event.previous_trust == 0.9
        assert event.new_trust == 0.85
        assert event.decay_rate == 0.01

    def test_refresh_event(self):
        """Test trust refresh event."""
        event = TrustEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.REFRESH,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Verified reuse",
            previous_trust=0.7,
            new_trust=0.9,
            tier=KnowledgeTier.K2,
        )

        assert event.event_type == EpistemicEventType.REFRESH
        assert event.new_trust > event.previous_trust


class TestContradictionEvent:
    """Test contradiction events."""

    def test_contradiction_with_penalty(self):
        """Test contradiction event with penalty applied."""
        ku_id = uuid4()
        contradicting_id = uuid4()

        event = ContradictionEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.CONTRADICTION,
            knowledge_unit_id=ku_id,
            timestamp=datetime.now(timezone.utc),
            reason="Higher tier contradicts lower",
            contradicting_unit_id=contradicting_id,
            tier=KnowledgeTier.K3,
            contradicting_tier=KnowledgeTier.K1,
            penalty_applied=True,
            penalty_factor=0.5,
            resolution="penalty_applied",
        )

        assert event.contradicting_unit_id == contradicting_id
        assert event.penalty_applied is True
        assert event.penalty_factor == 0.5

    def test_contradiction_json_schema(self):
        """Test contradiction JSON schema."""
        event = ContradictionEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.CONTRADICTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
            contradicting_unit_id=uuid4(),
            tier=KnowledgeTier.K2,
            contradicting_tier=KnowledgeTier.K1,
            penalty_applied=True,
            penalty_factor=0.3,
        )

        json_data = event.to_json_schema()

        assert "contradicting_unit_id" in json_data
        assert "tier" in json_data
        assert "contradicting_tier" in json_data
        assert "penalty_applied" in json_data
        assert json_data["penalty_factor"] == 0.3


class TestFreezeEvent:
    """Test freeze events."""

    def test_freeze_from_disagreement(self):
        """Test freeze event from dual-persona disagreement."""
        event = FreezeEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.FREEZE,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Persona disagreement",
            tier=KnowledgeTier.K3,
            analyst_verdict=True,
            adversary_verdict=False,
            cids_alert_id="CIDS-12345",
        )

        assert event.analyst_verdict is True
        assert event.adversary_verdict is False
        assert event.cids_alert_id == "CIDS-12345"

    def test_freeze_json_with_cids(self):
        """Test freeze JSON includes C-IDS alert."""
        event = FreezeEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.FREEZE,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
            tier=KnowledgeTier.K2,
            cids_alert_id="ALERT-001",
        )

        json_data = event.to_json_schema()

        assert "cids_alert_id" in json_data
        assert json_data["cids_alert_id"] == "ALERT-001"


class TestUsageViolationEvent:
    """Test usage violation events."""

    def test_usage_violation(self):
        """Test usage policy violation event."""
        event = UsageViolationEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.USAGE_VIOLATION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Narrative used for execution",
            tier=KnowledgeTier.K3,
            usage_class="execution_guidance",
            allowed_tiers=["ground_truth", "verified_derivation"],
            context="Attempted to use K3 for tool execution",
        )

        assert event.tier == KnowledgeTier.K3
        assert event.usage_class == "execution_guidance"
        assert len(event.allowed_tiers) == 2

    def test_violation_json_schema(self):
        """Test violation JSON schema."""
        event = UsageViolationEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.USAGE_VIOLATION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
            tier=KnowledgeTier.K4,
            usage_class="governance",
            allowed_tiers=["ground_truth", "verified_derivation", "trust_scored_external"],
            context="Test violation",
        )

        json_data = event.to_json_schema()

        assert "usage_class" in json_data
        assert "allowed_tiers" in json_data
        assert "context" in json_data
        assert json_data["tier"] == "noise"


class TestEpistemicAuditLog:
    """Test epistemic audit log."""

    @pytest.fixture
    def audit_log(self):
        """Create audit log instance."""
        return EpistemicAuditLog()

    def test_log_event(self, audit_log):
        """Test logging an event."""
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )

        audit_log.log_event(event)

        assert audit_log.get_event_count() == 1
        assert event in audit_log.events

    def test_log_tier_transition(self, audit_log):
        """Test logging tier transition."""
        ku_id = uuid4()

        event = audit_log.log_tier_transition(
            knowledge_unit_id=ku_id,
            event_type=EpistemicEventType.PROMOTION,
            previous_tier=KnowledgeTier.K3,
            new_tier=KnowledgeTier.K2,
            reason="Dual-persona approval",
            analyst_verdict=True,
            adversary_verdict=True,
            authorized_by="admin",
        )

        assert event.previous_tier == KnowledgeTier.K3
        assert event.new_tier == KnowledgeTier.K2
        assert audit_log.get_event_count() == 1

    def test_log_trust_event(self, audit_log):
        """Test logging trust event."""
        ku_id = uuid4()

        event = audit_log.log_trust_event(
            knowledge_unit_id=ku_id,
            event_type=EpistemicEventType.DECAY,
            previous_trust=0.9,
            new_trust=0.85,
            reason="Time-based decay",
            decay_rate=0.01,
            tier=KnowledgeTier.K3,
        )

        assert event.previous_trust == 0.9
        assert event.new_trust == 0.85
        assert audit_log.get_event_count() == 1

    def test_log_contradiction(self, audit_log):
        """Test logging contradiction."""
        ku_id = uuid4()
        contradicting_id = uuid4()

        event = audit_log.log_contradiction(
            knowledge_unit_id=ku_id,
            contradicting_unit_id=contradicting_id,
            tier=KnowledgeTier.K3,
            contradicting_tier=KnowledgeTier.K1,
            reason="Higher tier contradicts",
            penalty_applied=True,
            penalty_factor=0.5,
            resolution="penalty_applied",
        )

        assert event.contradicting_unit_id == contradicting_id
        assert event.penalty_applied is True
        assert audit_log.get_event_count() == 1

    def test_log_freeze(self, audit_log):
        """Test logging freeze event."""
        ku_id = uuid4()

        event = audit_log.log_freeze(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K2,
            reason="Persona disagreement",
            analyst_verdict=True,
            adversary_verdict=False,
            cids_alert_id="ALERT-001",
        )

        assert event.cids_alert_id == "ALERT-001"
        assert audit_log.get_event_count() == 1

    def test_log_usage_violation(self, audit_log):
        """Test logging usage violation."""
        ku_id = uuid4()

        event = audit_log.log_usage_violation(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K3,
            usage_class="execution_guidance",
            allowed_tiers=["ground_truth", "verified_derivation"],
            reason="Violation detected",
            context="Attempted execution",
        )

        assert event.usage_class == "execution_guidance"
        assert audit_log.get_event_count() == 1

    def test_query_by_knowledge_unit(self, audit_log):
        """Test querying events by knowledge unit."""
        ku_id1 = uuid4()
        ku_id2 = uuid4()

        # Log events for both units
        audit_log.log_trust_event(
            ku_id1, EpistemicEventType.DECAY, 0.9, 0.8, "Decay"
        )
        audit_log.log_trust_event(
            ku_id1, EpistemicEventType.REFRESH, 0.8, 0.9, "Refresh"
        )
        audit_log.log_trust_event(
            ku_id2, EpistemicEventType.DECAY, 0.7, 0.6, "Decay"
        )

        # Query ku_id1
        events = audit_log.query_by_knowledge_unit(ku_id1)
        assert len(events) == 2
        assert all(e.knowledge_unit_id == ku_id1 for e in events)

    def test_query_by_type(self, audit_log):
        """Test querying events by type."""
        ku_id = uuid4()

        # Log different event types
        audit_log.log_trust_event(
            ku_id, EpistemicEventType.DECAY, 0.9, 0.8, "Decay"
        )
        audit_log.log_trust_event(
            ku_id, EpistemicEventType.REFRESH, 0.8, 0.9, "Refresh"
        )
        audit_log.log_freeze(ku_id, KnowledgeTier.K2, "Freeze")

        # Query DECAY events
        decay_events = audit_log.query_by_type(EpistemicEventType.DECAY)
        assert len(decay_events) == 1
        assert decay_events[0].event_type == EpistemicEventType.DECAY

    def test_query_by_time_range(self, audit_log):
        """Test querying events by time range."""
        ku_id = uuid4()
        now = datetime.now(timezone.utc)

        # Log events at different times
        event1 = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=ku_id,
            timestamp=now - timedelta(hours=2),
            reason="Old event",
        )
        event2 = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=ku_id,
            timestamp=now,
            reason="Recent event",
        )

        audit_log.log_event(event1)
        audit_log.log_event(event2)

        # Query recent events only
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=1)
        events = audit_log.query_by_time_range(start_time, end_time)

        assert len(events) == 1
        assert events[0].reason == "Recent event"

    def test_query_complex(self, audit_log):
        """Test complex query with multiple filters."""
        ku_id = uuid4()
        now = datetime.now(timezone.utc)

        # Log various events
        audit_log.log_trust_event(
            ku_id, EpistemicEventType.DECAY, 0.9, 0.8, "Decay"
        )
        audit_log.log_trust_event(
            ku_id, EpistemicEventType.REFRESH, 0.8, 0.9, "Refresh"
        )
        audit_log.log_freeze(uuid4(), KnowledgeTier.K2, "Freeze")  # Different KU

        # Complex query: specific KU, DECAY type
        events = audit_log.query_complex(
            knowledge_unit_id=ku_id,
            event_type=EpistemicEventType.DECAY,
        )

        assert len(events) == 1
        assert events[0].event_type == EpistemicEventType.DECAY
        assert events[0].knowledge_unit_id == ku_id

    def test_get_event_statistics(self, audit_log):
        """Test event statistics."""
        ku_id1 = uuid4()
        ku_id2 = uuid4()

        # Log various events
        audit_log.log_trust_event(ku_id1, EpistemicEventType.DECAY, 0.9, 0.8, "Decay")
        audit_log.log_trust_event(ku_id1, EpistemicEventType.DECAY, 0.8, 0.7, "Decay")
        audit_log.log_freeze(ku_id2, KnowledgeTier.K2, "Freeze")

        stats = audit_log.get_event_statistics()

        assert stats["total_events"] == 3
        assert stats["by_type"]["decay"] == 2
        assert stats["by_type"]["freeze"] == 1
        assert str(ku_id1) in stats["by_knowledge_unit"]
        assert stats["by_knowledge_unit"][str(ku_id1)] == 2

    def test_export_events_json(self, audit_log):
        """Test exporting events to JSON (AC #6 format)."""
        ku_id = uuid4()

        # Log events
        audit_log.log_tier_transition(
            ku_id,
            EpistemicEventType.PROMOTION,
            KnowledgeTier.K3,
            KnowledgeTier.K2,
            "Test promotion",
        )

        # Export
        json_events = audit_log.export_events_json()

        assert len(json_events) == 1
        assert "event" in json_events[0]
        assert "knowledge_id" in json_events[0]
        assert "timestamp" in json_events[0]
        assert json_events[0]["event"] == "promotion"

    def test_export_events_with_pagination(self, audit_log):
        """Test exporting events with pagination."""
        ku_id = uuid4()

        # Log 5 events
        for i in range(5):
            audit_log.log_trust_event(
                ku_id, EpistemicEventType.DECAY, 0.9, 0.8, f"Event {i}"
            )

        # Export with pagination
        json_events = audit_log.export_events_json(start_index=1, limit=2)

        assert len(json_events) == 2

    def test_get_forensic_timeline(self, audit_log):
        """Test forensic timeline reconstruction."""
        ku_id = uuid4()

        # Log events in non-chronological order
        audit_log.log_trust_event(ku_id, EpistemicEventType.DECAY, 0.9, 0.85, "Decay 1")
        audit_log.log_trust_event(ku_id, EpistemicEventType.REFRESH, 0.85, 0.9, "Refresh")
        audit_log.log_trust_event(ku_id, EpistemicEventType.DECAY, 0.9, 0.8, "Decay 2")

        # Get forensic timeline (should be chronologically sorted)
        timeline = audit_log.get_forensic_timeline(ku_id)

        assert len(timeline) == 3
        # Verify JSON format
        assert all("event" in event for event in timeline)
        assert all("timestamp" in event for event in timeline)

    def test_event_indexing(self, audit_log):
        """Test that events are properly indexed."""
        ku_id1 = uuid4()
        ku_id2 = uuid4()

        # Log events
        audit_log.log_trust_event(ku_id1, EpistemicEventType.DECAY, 0.9, 0.8, "Test")
        audit_log.log_freeze(ku_id2, KnowledgeTier.K2, "Test")

        # Verify indexes are populated
        assert ku_id1 in audit_log._event_index
        assert ku_id2 in audit_log._event_index
        assert EpistemicEventType.DECAY in audit_log._type_index
        assert EpistemicEventType.FREEZE in audit_log._type_index

    def test_empty_query_results(self, audit_log):
        """Test queries on empty log."""
        non_existent_id = uuid4()

        events = audit_log.query_by_knowledge_unit(non_existent_id)
        assert len(events) == 0

        events = audit_log.query_by_type(EpistemicEventType.PROMOTION)
        assert len(events) == 0

    def test_statistics_empty_log(self, audit_log):
        """Test statistics on empty log."""
        stats = audit_log.get_event_statistics()

        assert stats["total_events"] == 0
        assert stats["by_type"] == {}
        assert stats["by_knowledge_unit"] == {}
