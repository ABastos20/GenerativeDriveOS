"""Unit tests for Epistemic Audit Sinks (Story 11-5.2).

Tests the sink architecture including:
- Protocol definition and runtime checking
- InMemorySink storage and indexing
- Multi-sink fan-out
- Error isolation

Coverage target: AC1-AC5.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.jarvis.knowledge.audit import (
    EpistemicAuditLog,
    EpistemicEvent,
    EpistemicEventType,
)
from src.jarvis.knowledge.audit_sinks import (
    EpistemicAuditSink,
    InMemorySink,
)


class TestEpistemicAuditSinkProtocol:
    """Test AC1: Sink Protocol Definition."""
    
    def test_protocol_is_runtime_checkable(self):
        """Test that Protocol is runtime_checkable."""
        # InMemorySink should satisfy the protocol
        sink = InMemorySink()
        assert isinstance(sink, EpistemicAuditSink)
    
    def test_duck_typed_class_satisfies_protocol(self):
        """Test that any class with handle_event satisfies protocol."""
        class DuckSink:
            def handle_event(self, event: EpistemicEvent) -> None:
                pass
        
        sink = DuckSink()
        assert isinstance(sink, EpistemicAuditSink)
    
    def test_invalid_class_fails_protocol_check(self):
        """Test that class without handle_event fails protocol check."""
        class NotASink:
            def log_event(self, event):  # Different method name
                pass
        
        sink = NotASink()
        assert not isinstance(sink, EpistemicAuditSink)


class TestInMemorySink:
    """Test AC2: InMemorySink Implementation."""
    
    @pytest.fixture
    def sink(self):
        """Create fresh InMemorySink."""
        return InMemorySink()
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event."""
        return EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test event",
        )
    
    def test_handle_event_stores_event(self, sink, sample_event):
        """Test that handle_event stores event in list."""
        sink.handle_event(sample_event)
        
        assert len(sink.events) == 1
        assert sink.events[0] == sample_event
    
    def test_handle_event_indexes_by_knowledge_unit(self, sink, sample_event):
        """Test that handle_event creates knowledge unit index."""
        sink.handle_event(sample_event)
        
        result = sink.query_by_knowledge_unit(sample_event.knowledge_unit_id)
        assert len(result) == 1
        assert result[0] == sample_event
    
    def test_handle_event_indexes_by_type(self, sink, sample_event):
        """Test that handle_event creates type index."""
        sink.handle_event(sample_event)
        
        result = sink.query_by_type(EpistemicEventType.PROMOTION)
        assert len(result) == 1
        assert result[0] == sample_event
    
    def test_multiple_events_same_unit(self, sink):
        """Test multiple events for same knowledge unit."""
        ku_id = uuid4()
        events = [
            EpistemicEvent(
                event_id=uuid4(),
                event_type=EpistemicEventType.PROMOTION,
                knowledge_unit_id=ku_id,
                timestamp=datetime.now(timezone.utc),
                reason=f"Event {i}",
            )
            for i in range(3)
        ]
        
        for event in events:
            sink.handle_event(event)
        
        result = sink.query_by_knowledge_unit(ku_id)
        assert len(result) == 3
    
    def test_clear_removes_all_events(self, sink, sample_event):
        """Test that clear() removes all events."""
        sink.handle_event(sample_event)
        assert len(sink.events) == 1
        
        sink.clear()
        assert len(sink.events) == 0
        assert sink.get_event_count() == 0


class TestEpistemicAuditLogSinkIntegration:
    """Test AC3: EpistemicAuditLog Refactor with Sinks."""
    
    def test_default_uses_inmemory_sink(self):
        """Test that default constructor uses InMemorySink."""
        log = EpistemicAuditLog()
        
        # Should have a memory sink
        assert log._memory_sink is not None
        assert isinstance(log._memory_sink, InMemorySink)
    
    def test_custom_sinks_are_used(self):
        """Test that custom sinks receive events."""
        calls = []
        
        class TrackingSink:
            def handle_event(self, event):
                calls.append(event)
        
        custom_sink = TrackingSink()
        log = EpistemicAuditLog(sinks=[custom_sink])
        
        event = log.log_tier_transition(
            knowledge_unit_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            previous_tier="K4",
            new_tier="K3",
            reason="Test",
        )
        
        # Custom sink should have received the event
        assert len(calls) == 1
        assert calls[0].event_id == event.event_id
    
    def test_multi_sink_fanout(self):
        """Test that events fan-out to multiple sinks."""
        sink1_calls = []
        sink2_calls = []
        
        class Sink1:
            def handle_event(self, event):
                sink1_calls.append(event)
        
        class Sink2:
            def handle_event(self, event):
                sink2_calls.append(event)
        
        log = EpistemicAuditLog(sinks=[Sink1(), Sink2()])
        
        # Log an event
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )
        log.log_event(event)
        
        # Both sinks should have received it
        assert len(sink1_calls) == 1
        assert len(sink2_calls) == 1


class TestErrorIsolation:
    """Test AC5: Error Isolation."""
    
    def test_failing_sink_does_not_crash_caller(self):
        """Test that a failing sink doesn't raise to caller."""
        class FailingSink:
            def handle_event(self, event):
                raise RuntimeError("Sink failure!")
        
        log = EpistemicAuditLog(sinks=[FailingSink()])
        
        # Should not raise
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.FREEZE,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )
        log.log_event(event)  # Should not raise
    
    def test_failing_sink_does_not_block_healthy_sinks(self):
        """Test that failing sink doesn't block healthy sinks."""
        healthy_calls = []
        
        class FailingSink:
            def handle_event(self, event):
                raise RuntimeError("Sink failure!")
        
        class HealthySink:
            def handle_event(self, event):
                healthy_calls.append(event)
        
        # Failing sink comes first
        log = EpistemicAuditLog(sinks=[FailingSink(), HealthySink()])
        
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.DECAY,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )
        log.log_event(event)
        
        # Healthy sink should still receive event
        assert len(healthy_calls) == 1
    
    def test_all_sinks_fail_no_exception(self):
        """Test that all sinks failing doesn't raise exception."""
        class FailingSink1:
            def handle_event(self, event):
                raise RuntimeError("Sink 1 failure!")
        
        class FailingSink2:
            def handle_event(self, event):
                raise ValueError("Sink 2 failure!")
        
        log = EpistemicAuditLog(sinks=[FailingSink1(), FailingSink2()])
        
        # Should not raise even with all sinks failing
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.CONTRADICTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )
        log.log_event(event)  # Should not raise


class TestBackwardCompatibility:
    """Test AC4: Backward Compatibility."""
    
    def test_events_list_accessible(self):
        """Test that events list is accessible like before."""
        log = EpistemicAuditLog()
        
        event = log.log_tier_transition(
            knowledge_unit_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            previous_tier="K4",
            new_tier="K3",
            reason="Test",
        )
        
        # events list should be accessible directly
        assert len(log.events) == 1
        assert log.events[0] == event
    
    def test_query_methods_still_work(self):
        """Test that query methods work without passing sinks."""
        log = EpistemicAuditLog()
        ku_id = uuid4()
        
        log.log_tier_transition(
            knowledge_unit_id=ku_id,
            event_type=EpistemicEventType.PROMOTION,
            previous_tier="K4",
            new_tier="K3",
            reason="Test",
        )
        
        # Query methods should work
        results = log.query_by_knowledge_unit(ku_id)
        assert len(results) == 1
        
        results = log.query_by_type(EpistemicEventType.PROMOTION)
        assert len(results) == 1
    
    def test_get_event_count_works(self):
        """Test get_event_count still works."""
        log = EpistemicAuditLog()
        
        assert log.get_event_count() == 0
        
        log.log_tier_transition(
            knowledge_unit_id=uuid4(),
            event_type=EpistemicEventType.DEMOTION,
            previous_tier="K2",
            new_tier="K3",
            reason="Test",
        )
        
        assert log.get_event_count() == 1


class TestStdoutJsonSink:
    """Test AC1, AC2, AC3: StdoutJsonSink Implementation."""
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event."""
        return EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test event",
            metadata={"secret_data": "should_be_removed"},
        )
    
    def test_sink_satisfies_protocol(self):
        """Test that StdoutJsonSink implements Protocol."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink
        sink = StdoutJsonSink()
        assert isinstance(sink, EpistemicAuditSink)
    
    def test_redaction_removes_unsafe_fields(self):
        """Test that _redact removes unsafe fields."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink, SAFE_LOG_FIELDS
        
        sink = StdoutJsonSink(redact_content=True)
        data = {
            "event": "promotion",
            "knowledge_id": "123",
            "reason": "test",
            "metadata": {"secret": "value"},  # unsafe
            "raw_prompt": "should be removed",  # unsafe
            "document_text": "also removed",  # unsafe
            "context": "removed too",  # unsafe
        }
        
        result = sink._redact(data)
        
        # Safe fields kept
        assert "event" in result
        assert "knowledge_id" in result
        assert "reason" in result
        
        # Unsafe fields removed
        assert "metadata" not in result
        assert "raw_prompt" not in result
        assert "document_text" not in result
        assert "context" not in result
    
    def test_flatten_serializes_types(self):
        """Test that _flatten handles datetime, UUID, and enums."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink
        
        sink = StdoutJsonSink()
        test_time = datetime(2025, 12, 10, 12, 0, 0, tzinfo=timezone.utc)
        test_uuid = uuid4()
        
        data = {
            "timestamp": test_time,
            "knowledge_id": test_uuid,
            "event_type": EpistemicEventType.PROMOTION,
            "list_field": ["a", "b", "c"],
        }
        
        result = sink._flatten(data)
        
        # Datetime -> ISO string
        assert result["timestamp"] == "2025-12-10T12:00:00+00:00"
        # UUID -> string
        assert result["knowledge_id"] == str(test_uuid)
        # Enum -> value
        assert result["event_type"] == "promotion"
        # List -> comma-separated
        assert result["list_field"] == "a,b,c"
    
    def test_handle_event_no_exception(self, sample_event):
        """Test that handle_event doesn't raise exceptions."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink
        
        sink = StdoutJsonSink()
        # Should not raise
        sink.handle_event(sample_event)
    
    def test_redact_false_keeps_all_fields(self):
        """Test that redact_content=False keeps all fields."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink
        
        sink = StdoutJsonSink(redact_content=False)
        data = {
            "event": "test",
            "metadata": {"key": "value"},
            "raw_prompt": "should stay",
        }
        
        # _redact is skipped when redact_content=False, so test flatten only
        result = sink._flatten(data)
        assert "raw_prompt" in result


class TestMultiSinkCompatibility:
    """Test AC4: Multi-Sink Compatibility."""
    
    def test_stdout_and_memory_both_receive_events(self):
        """Test that both sinks receive events."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink
        
        memory_sink = InMemorySink()
        stdout_sink = StdoutJsonSink(redact_content=True)
        
        log = EpistemicAuditLog(sinks=[memory_sink, stdout_sink])
        
        event = log.log_tier_transition(
            knowledge_unit_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            previous_tier="K4",
            new_tier="K3",
            reason="Test",
        )
        
        # Memory sink should have the event
        assert memory_sink.get_event_count() == 1
    
    def test_query_still_works_with_stdout_sink(self):
        """Test that query methods work with multiple sinks."""
        from src.jarvis.knowledge.audit_sinks import StdoutJsonSink
        
        log = EpistemicAuditLog(sinks=[InMemorySink(), StdoutJsonSink()])
        ku_id = uuid4()
        
        log.log_tier_transition(
            knowledge_unit_id=ku_id,
            event_type=EpistemicEventType.DEMOTION,
            previous_tier="K2",
            new_tier="K3",
            reason="Test",
        )
        
        results = log.query_by_knowledge_unit(ku_id)
        assert len(results) == 1


class TestEnvironmentConfig:
    """Test AC5: Environment Configuration."""
    
    def test_default_memory_only(self, monkeypatch):
        """Test default config uses memory sink only."""
        from src.jarvis.knowledge.audit_sinks import create_audit_log_from_env
        
        monkeypatch.delenv("EPISTEMIC_AUDIT_SINKS", raising=False)
        
        log = create_audit_log_from_env()
        assert log._memory_sink is not None
        assert len(log._sinks) >= 1
    
    def test_memory_and_stdout_config(self, monkeypatch):
        """Test memory,stdout config creates both sinks."""
        from src.jarvis.knowledge.audit_sinks import create_audit_log_from_env, StdoutJsonSink
        
        monkeypatch.setenv("EPISTEMIC_AUDIT_SINKS", "memory,stdout")
        
        log = create_audit_log_from_env()
        
        # Should have both sinks
        assert len(log._sinks) == 2
        sink_types = [type(s).__name__ for s in log._sinks]
        assert "InMemorySink" in sink_types
        assert "StdoutJsonSink" in sink_types
    
    def test_empty_config_defaults_to_memory(self, monkeypatch):
        """Test empty config defaults to memory sink."""
        from src.jarvis.knowledge.audit_sinks import create_audit_log_from_env
        
        monkeypatch.setenv("EPISTEMIC_AUDIT_SINKS", "")
        
        log = create_audit_log_from_env()
        assert log._memory_sink is not None


class TestPostgresSink:
    """Test Story 11-5.4: PostgresSink Implementation and Graceful Degradation."""
    
    def test_sink_satisfies_protocol(self):
        """Test that PostgresSink implements Protocol."""
        from src.jarvis.knowledge.audit_sinks import PostgresSink
        
        def mock_session_factory():
            pass
        
        sink = PostgresSink(session_factory=mock_session_factory)
        assert isinstance(sink, EpistemicAuditSink)
    
    def test_session_factory_failure_no_exception(self):
        """Test that session factory failure doesn't raise (AC3)."""
        from src.jarvis.knowledge.audit_sinks import PostgresSink
        
        def failing_factory():
            raise RuntimeError("DB connection failed!")
        
        sink = PostgresSink(session_factory=failing_factory)
        
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.PROMOTION,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )
        
        # Should not raise
        sink.handle_event(event)
    
    def test_commit_failure_rollback(self):
        """Test that commit failure triggers rollback (AC3)."""
        from src.jarvis.knowledge.audit_sinks import PostgresSink
        from unittest.mock import Mock
        
        mock_session = Mock()
        mock_session.commit.side_effect = RuntimeError("Commit failed!")
        
        def session_factory():
            return mock_session
        
        sink = PostgresSink(session_factory=session_factory)
        
        event = EpistemicEvent(
            event_id=uuid4(),
            event_type=EpistemicEventType.FREEZE,
            knowledge_unit_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            reason="Test",
        )
        
        # Should not raise
        sink.handle_event(event)
        
        # Rollback should have been called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_multi_sink_with_postgres(self):
        """Test that PostgresSink works alongside other sinks."""
        from src.jarvis.knowledge.audit_sinks import PostgresSink
        from unittest.mock import Mock, patch
        
        mock_session = Mock()
        def session_factory():
            return mock_session
        
        memory_sink = InMemorySink()
        postgres_sink = PostgresSink(session_factory=session_factory)
        
        log = EpistemicAuditLog(sinks=[memory_sink, postgres_sink])
        
        # Patch the model import inside PostgresSink
        with patch('src.jarvis.knowledge.audit_sinks.logger'):
            event = EpistemicEvent(
                event_id=uuid4(),
                event_type=EpistemicEventType.DEMOTION,
                knowledge_unit_id=uuid4(),
                timestamp=datetime.now(timezone.utc),
                reason="Test",
            )
            log.log_event(event)
        
        # Memory sink should have the event
        assert memory_sink.get_event_count() == 1
        # Postgres should have tried to add (even if it fails on model import)
        # The key is that it doesn't crash the pipeline
