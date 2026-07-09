"""Epistemic Audit Sinks (Story 11-5.2).

This module defines the sink architecture for routing epistemic audit events
to multiple backends (memory, stdout, database) without changing the semantic core.

Architecture:
    EpistemicAuditLog (semantic core)
             │
             ▼
        ┌────┴────┐
        │  Sinks  │ ← fan-out
        └────┬────┘
             │
        ┌────┼────┬────────────┐
        ▼    ▼    ▼            ▼
    InMemory Stdout PostgreSQL ...future

References:
- [Story 11-5.2: Epistemic Audit Sink Architecture]
- [Lock 7: Epistemic Sovereignty]
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

import structlog

# Import event types from audit module
from src.jarvis.knowledge.audit import EpistemicEvent, EpistemicEventType

logger = structlog.get_logger(__name__)


@runtime_checkable
class EpistemicAuditSink(Protocol):
    """Protocol for epistemic audit event sinks.
    
    Sinks receive events and handle storage/transmission to backends.
    Each sink must implement `handle_event` to receive events.
    
    The Protocol is @runtime_checkable for duck-typing validation.
    
    Example:
        class MySink:
            def handle_event(self, event: EpistemicEvent) -> None:
                # Store/transmit event
                pass
        
        # Validate at runtime
        sink = MySink()
        assert isinstance(sink, EpistemicAuditSink)
    """
    
    def handle_event(self, event: EpistemicEvent) -> None:
        """Handle an epistemic event.
        
        Args:
            event: The epistemic event to process
            
        Note:
            Implementations should not raise exceptions to callers.
            Internal errors should be logged and swallowed.
        """
        ...


class InMemorySink:
    """In-memory audit event sink.
    
    Stores events in memory with indexes for fast querying.
    This is the default sink providing backward-compatible behavior.
    
    Attributes:
        events: Chronologically ordered list of all events
    """
    
    def __init__(self) -> None:
        """Initialize in-memory sink with empty storage."""
        self.events: list[EpistemicEvent] = []
        self._event_index: dict[UUID, list[EpistemicEvent]] = {}
        self._type_index: dict[EpistemicEventType, list[EpistemicEvent]] = {}
    
    def handle_event(self, event: EpistemicEvent) -> None:
        """Store event in memory with indexing.
        
        Args:
            event: Event to store
        """
        # Append to main log
        self.events.append(event)
        
        # Update knowledge unit index
        if event.knowledge_unit_id not in self._event_index:
            self._event_index[event.knowledge_unit_id] = []
        self._event_index[event.knowledge_unit_id].append(event)
        
        # Update type index
        if event.event_type not in self._type_index:
            self._type_index[event.event_type] = []
        self._type_index[event.event_type].append(event)
    
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
    
    def get_event_count(self) -> int:
        """Get total number of events stored.
        
        Returns:
            Event count
        """
        return len(self.events)
    
    def clear(self) -> None:
        """Clear all stored events. Use for testing only."""
        self.events.clear()
        self._event_index.clear()
        self._type_index.clear()


# Fields that are SAFE to log to external observability systems
SAFE_LOG_FIELDS = frozenset({
    "event", "event_id", "event_type", "timestamp",
    "knowledge_id", "knowledge_unit_id", "tier", "trust_score",
    "previous_tier", "new_tier", "previous_trust", "new_trust",
    "reason", "authorized_by", "requester",
    "analyst_verdict", "adversary_verdict",
    "usage_class", "penalty_applied", "resolution",
})

# Fields that must NEVER be logged to external systems
UNSAFE_LOG_FIELDS = frozenset({
    "raw_prompt", "document_text", "context", "content",
    "llm_response", "metadata", "raw_content", "user_data",
})


class StdoutJsonSink:
    """Structured logging sink for observability integration (Story 11-5.3).
    
    Outputs epistemic events as single-line JSON to stdout via structlog,
    suitable for ingestion by Graylog, ELK, Kinesis, or other log aggregators.
    
    Security:
        By default, content is redacted to prevent PII/sensitive data leakage.
        Only safe telemetry fields are included in output.
    
    Example:
        sink = StdoutJsonSink(redact_content=True)
        audit_log = EpistemicAuditLog(sinks=[InMemorySink(), sink])
    """
    
    def __init__(self, redact_content: bool = True) -> None:
        """Initialize stdout sink.
        
        Args:
            redact_content: If True (default), strip sensitive fields from output.
        """
        self.redact_content = redact_content
        self._logger = structlog.get_logger("jarvis.epistemic")
    
    def handle_event(self, event: EpistemicEvent) -> None:
        """Output event as structured JSON log line.
        
        Args:
            event: Event to log
        """
        try:
            data = event.to_json_schema()
            if self.redact_content:
                data = self._redact(data)
            data = self._flatten(data)
            self._logger.info("epistemic_event", **data)
        except Exception as e:
            # Never raise to caller - log error internally
            logger.warning("stdout_sink_error", error=str(e))
    
    def _redact(self, data: dict) -> dict:
        """Remove sensitive fields from event data.
        
        Args:
            data: Raw event data dict
            
        Returns:
            Sanitized dict with only safe fields
        """
        # Remove known unsafe fields
        for field in UNSAFE_LOG_FIELDS:
            data.pop(field, None)
        
        # Only keep safe fields (whitelist approach)
        return {k: v for k, v in data.items() if k in SAFE_LOG_FIELDS}
    
    def _flatten(self, data: dict) -> dict:
        """Flatten and serialize data for JSON output.
        
        Ensures all values are JSON-serializable primitives:
        - datetime -> ISO8601 string
        - UUID -> string
        - enum -> .value
        - nested dicts -> flattened with _ prefix
        
        Args:
            data: Event data dict
            
        Returns:
            Flat, JSON-serializable dict
        """
        from datetime import datetime
        from uuid import UUID
        from enum import Enum
        
        flat = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                flat[key] = value.isoformat()
            elif isinstance(value, UUID):
                flat[key] = str(value)
            elif isinstance(value, Enum):
                flat[key] = value.value
            elif isinstance(value, dict):
                # Flatten nested dict with prefix
                for k, v in value.items():
                    flat[f"{key}_{k}"] = v
            elif isinstance(value, list):
                # Convert list to comma-separated string
                flat[key] = ",".join(str(v) for v in value)
            else:
                flat[key] = value
        
        return flat


def create_audit_log_from_env() -> "EpistemicAuditLog":
    """Factory to create EpistemicAuditLog from environment config.
    
    Uses EPISTEMIC_AUDIT_SINKS environment variable to configure sinks.
    
    Environment Variables:
        EPISTEMIC_AUDIT_SINKS: Comma-separated list of sink names.
            - "memory" (default): InMemorySink for queries
            - "stdout": StdoutJsonSink for log aggregation
            - "postgres": PostgresSink for database persistence
            
    Example:
        export EPISTEMIC_AUDIT_SINKS=memory,stdout
        
    Returns:
        Configured EpistemicAuditLog instance
    """
    import os
    # Import here to avoid circular dependency
    from src.jarvis.knowledge.audit import EpistemicAuditLog
    
    config = os.getenv("EPISTEMIC_AUDIT_SINKS", "memory")
    sink_names = [s.strip().lower() for s in config.split(",")]
    
    sinks: list[EpistemicAuditSink] = []
    
    if "memory" in sink_names:
        sinks.append(InMemorySink())
    
    if "stdout" in sink_names:
        sinks.append(StdoutJsonSink(redact_content=True))
    
    if "postgres" in sink_names:
        # PostgresSink requires a session factory - must be provided externally
        # This is a placeholder; in production, inject get_db_session_factory()
        logger.warning("postgres_sink_requires_session_factory", 
                      hint="Use create_audit_log_from_factory() with session_factory")
    
    # Ensure at least memory sink for queries
    if not sinks:
        sinks.append(InMemorySink())
    
    return EpistemicAuditLog(sinks=sinks)


class PostgresSink:
    """PostgreSQL persistence sink for epistemic audit events (Story 11-5.4).
    
    Writes events to PostgreSQL for long-term storage and SQL querying.
    
    Features:
        - Graceful degradation: DB failures don't crash the pipeline
        - JSONB payload for flexible event storage
        - Session factory injection for testability
    
    Example:
        sink = PostgresSink(session_factory=get_db_session)
        audit_log = EpistemicAuditLog(sinks=[InMemorySink(), sink])
    """
    
    def __init__(self, session_factory) -> None:
        """Initialize PostgreSQL sink.
        
        Args:
            session_factory: Callable that returns a SQLAlchemy session.
        """
        self._session_factory = session_factory
    
    def handle_event(self, event: EpistemicEvent) -> None:
        """Persist event to PostgreSQL.
        
        Args:
            event: Event to persist
            
        Note:
            Graceful degradation per AC3: DB errors are logged, not raised.
        """
        try:
            # Import here to avoid circular dependency
            from src.jarvis.database.models import EpistemicEventModel
            
            session = self._session_factory()
            try:
                model = EpistemicEventModel(
                    id=event.event_id,
                    event_type=event.event_type.value,
                    knowledge_unit_id=event.knowledge_unit_id,
                    timestamp=event.timestamp,
                    payload=event.to_json_schema(),
                )
                session.add(model)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.warning("postgres_sink_write_failed", error=str(e))
            finally:
                session.close()
        except Exception as e:
            # Even session factory can fail - never raise
            logger.warning("postgres_sink_session_failed", error=str(e))


def create_audit_log_with_postgres(session_factory) -> "EpistemicAuditLog":
    """Create EpistemicAuditLog with PostgreSQL persistence.
    
    Factory function for production use with database.
    
    Args:
        session_factory: Callable that returns a SQLAlchemy session.
        
    Returns:
        EpistemicAuditLog configured with memory, stdout, and postgres sinks.
    """
    from src.jarvis.knowledge.audit import EpistemicAuditLog
    
    return EpistemicAuditLog(sinks=[
        InMemorySink(),
        StdoutJsonSink(redact_content=True),
        PostgresSink(session_factory),
    ])


# Type alias for convenience
AuditSinkList = list[EpistemicAuditSink]
