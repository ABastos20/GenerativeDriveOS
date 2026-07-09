"""ARCHES session management module.

Extracted from controller.py for better modularity.
Handles session lifecycle operations.
"""
from typing import Optional
import uuid
import threading
from datetime import datetime

import structlog

from jarvis.arches.state import ARCHESSession
from jarvis.arches.trace import CognitiveTrace
from jarvis.memory.search import RetrievalMode, detect_retrieval_mode

logger = structlog.get_logger(__name__)


class SessionManager:
    """Manages ARCHES session lifecycle."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: dict[str, ARCHESSession] = {}
        self._lock = threading.Lock()
        self.logger = logger

    def create_session(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        mode: str = "qa",
        explicit_retrieval_mode: Optional[RetrievalMode] = None,
    ) -> ARCHESSession:
        """Create a new ARCHES session with cognitive trace.
        
        Returns:
            Newly created ARCHESSession
        """
        session_id = uuid.uuid4().hex

        # Detect retrieval mode
        if explicit_retrieval_mode is not None:
            retrieval_mode = explicit_retrieval_mode
            detected_date = None
        else:
            retrieval_mode, detected_date = detect_retrieval_mode(query)

        # Create cognitive trace
        cognitive_trace = CognitiveTrace(
            session_id=session_id,
            query=query,
            mode=mode,
            retrieval_mode=retrieval_mode.value,
        )

        # Create session
        session = ARCHESSession(
            session_id=session_id,
            query=query,
            conversation_id=conversation_id,
            cognitive_trace=cognitive_trace,
        )

        session.retrieval_mode = retrieval_mode
        session.time_slice_date = detected_date

        with self._lock:
            self.sessions[session.session_id] = session

        self.logger.info(
            "arches_session_started",
            session_id=session.session_id,
            trace_id=str(cognitive_trace.trace_id),
            query_length=len(query),
            conversation_id=conversation_id,
            mode=mode,
            retrieval_mode=retrieval_mode.value,
            time_slice_date=detected_date.isoformat() if detected_date else None,
        )

        return session

    def get_session(self, session_id: str) -> Optional[ARCHESSession]:
        """Retrieve a session by ID."""
        with self._lock:
            return self.sessions.get(session_id)

    def end_session(
        self,
        session: ARCHESSession,
        db_session: Optional[object] = None,
    ) -> Optional[str]:
        """End session and persist cognitive trace.
        
        Returns:
            trace_id if persisted, None otherwise
        """
        from jarvis.arches.trace import log_cognitive_trace
        from jarvis.arches.trace_helpers import populate_trace_from_session

        session.touch()

        # Mark all incomplete stages as complete
        for stage_status in session.plan_state.values():
            if stage_status.status == "running":
                stage_status.complete()

        trace_id = None

        # Finalize and persist cognitive trace
        if session.cognitive_trace:
            trace = session.cognitive_trace

            #Populate trace from session state
            populate_trace_from_session(session, trace)

            # Finalize timing
            trace.finalize()

            # Persist if DB session provided
            if db_session:
                try:
                    log_cognitive_trace(trace, db_session)
                    trace_id = str(trace.trace_id)
                except Exception as e:
                    self.logger.error(
                        "cognitive_trace_persist_failed",
                        session_id=session.session_id,
                        error=str(e),
                    )
                    trace.add_error(f"Trace persist failed: {e}")
            else:
                trace_id = str(trace.trace_id)

        self.logger.info(
            "arches_session_ended",
            session_id=session.session_id,
            trace_id=trace_id,
            duration_ms=int(
                (session.updated_at - session.created_at).total_seconds() * 1000
            ),
            research_triggered=session.flags.is_research_triggered,
            chunks_used=len(session.memory_state.chunks_used),
        )

        return trace_id
