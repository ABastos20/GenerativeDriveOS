"""Unit tests for ARCHES Runtime Controller.

Tests cover:
- Session creation with unique IDs (AC #1)
- Plan state stage transitions (AC #2)
- Memory state recording (AC #3)
- State flag toggling (AC #4)
- should_trigger_research logic (AC #5)
- Freshness computation (AC #7)
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from jarvis.arches.controller import (
    ARCHESController,
    ARCHESSession,
    PlanStage,
    get_controller,
)
from jarvis.arches.state import (
    MemoryState,
    SessionFlags,
    StageStatus,
)


class TestARCHESSession:
    """Tests for ARCHESSession dataclass."""

    def test_session_creation_with_unique_id(self):
        """AC#1: Session created with unique session_id."""
        session1 = ARCHESSession(
            session_id="test-session-1",
            query="What is Jarvis?",
        )
        session2 = ARCHESSession(
            session_id="test-session-2",
            query="How does memory work?",
        )
        
        assert session1.session_id != session2.session_id
        assert session1.session_id == "test-session-1"
        assert session2.session_id == "test-session-2"

    def test_session_initializes_plan_state_with_all_stages(self):
        """AC#2: Plan state tracks all ARCHES stages."""
        session = ARCHESSession(
            session_id="test",
            query="test query",
        )
        
        expected_stages = {"assess", "research", "critical", "hybrid", "execute", "store"}
        actual_stages = set(session.plan_state.keys())
        
        assert expected_stages == actual_stages
        
        # All stages should be pending initially
        for stage_status in session.plan_state.values():
            assert stage_status.status == "pending"

    def test_session_has_memory_state(self):
        """AC#3: Session has memory_state for tracking chunks, domains, freshness."""
        session = ARCHESSession(
            session_id="test",
            query="test",
        )
        
        assert isinstance(session.memory_state, MemoryState)
        assert session.memory_state.chunks_used == []
        assert session.memory_state.domains == []
        assert session.memory_state.freshness_scores == {}

    def test_session_has_flags(self):
        """AC#4: Session maintains state flags."""
        session = ARCHESSession(
            session_id="test",
            query="test",
        )
        
        assert isinstance(session.flags, SessionFlags)
        assert session.flags.is_research_triggered is False
        assert session.flags.fallback_needed is False
        assert session.flags.rerun_detected is False

    def test_session_touch_updates_timestamp(self):
        """Session touch() updates updated_at."""
        session = ARCHESSession(
            session_id="test",
            query="test",
        )
        original_time = session.updated_at
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        
        session.touch()
        
        assert session.updated_at > original_time

    def test_session_timestamps(self):
        """Session has created_at and updated_at timestamps."""
        before = datetime.now(timezone.utc)
        session = ARCHESSession(
            session_id="test",
            query="test",
        )
        after = datetime.now(timezone.utc)
        
        assert before <= session.created_at <= after
        assert before <= session.updated_at <= after


class TestStageStatus:
    """Tests for StageStatus transitions."""

    def test_stage_start(self):
        """Stage can be started."""
        status = StageStatus(stage=PlanStage.ASSESS, status="pending")
        
        status.start()
        
        assert status.status == "running"
        assert status.started_at is not None
        assert status.completed_at is None

    def test_stage_complete(self):
        """Stage can be completed."""
        status = StageStatus(stage=PlanStage.ASSESS, status="running")
        status.started_at = datetime.now(timezone.utc)
        
        status.complete()
        
        assert status.status == "complete"
        assert status.completed_at is not None

    def test_stage_skip(self):
        """Stage can be skipped."""
        status = StageStatus(stage=PlanStage.RESEARCH, status="pending")
        
        status.skip()
        
        assert status.status == "skipped"
        assert status.completed_at is not None


class TestARCHESController:
    """Tests for ARCHESController class."""

    @pytest.fixture
    def controller(self):
        """Create a fresh controller for each test."""
        return ARCHESController()

    def test_start_session_creates_unique_id(self, controller):
        """AC#1: Controller creates sessions with unique IDs."""
        session1 = controller.start_session("Query 1")
        session2 = controller.start_session("Query 2")
        
        assert session1.session_id != session2.session_id
        assert len(session1.session_id) == 32  # UUID hex length

    def test_start_session_stores_query(self, controller):
        """Session stores the original query."""
        query = "What is the meaning of life?"
        session = controller.start_session(query)
        
        assert session.query == query

    def test_start_session_stores_conversation_id(self, controller):
        """Session stores conversation_id if provided."""
        session = controller.start_session(
            "Test query",
            conversation_id="conv-123",
        )
        
        assert session.conversation_id == "conv-123"

    def test_get_session_returns_stored_session(self, controller):
        """Controller can retrieve stored sessions."""
        session = controller.start_session("Test")
        
        retrieved = controller.get_session(session.session_id)
        
        assert retrieved is session

    def test_get_session_returns_none_for_unknown(self, controller):
        """Controller returns None for unknown session IDs."""
        assert controller.get_session("nonexistent") is None

    def test_start_stage(self, controller):
        """AC#2: Controller can start ARCHES stages."""
        session = controller.start_session("Test")
        
        controller.start_stage(session, PlanStage.ASSESS)
        
        assert session.plan_state["assess"].status == "running"
        assert session.plan_state["assess"].started_at is not None

    def test_complete_stage(self, controller):
        """AC#2: Controller can complete ARCHES stages."""
        session = controller.start_session("Test")
        controller.start_stage(session, PlanStage.ASSESS)
        
        controller.complete_stage(session, PlanStage.ASSESS)
        
        assert session.plan_state["assess"].status == "complete"
        assert session.plan_state["assess"].completed_at is not None

    def test_skip_stage(self, controller):
        """AC#2: Controller can skip ARCHES stages."""
        session = controller.start_session("Test")
        
        controller.skip_stage(session, PlanStage.RESEARCH)
        
        assert session.plan_state["research"].status == "skipped"

    def test_record_memory_usage_basic(self, controller):
        """AC#3: Controller records memory usage with chunks and domains."""
        session = controller.start_session("Test")
        
        # Mock chunks with IDs
        chunks = [
            MagicMock(id="chunk-1", created_at=datetime.now(timezone.utc)),
            MagicMock(id="chunk-2", created_at=datetime.now(timezone.utc)),
        ]
        domains = ["jarvis-core", "jarvis-memory"]
        
        controller.record_memory_usage(session, chunks, domains=domains)
        
        assert session.memory_state.chunks_used == ["chunk-1", "chunk-2"]
        assert session.memory_state.domains == domains
        assert session.memory_state.total_chunks_retrieved == 2

    def test_record_memory_usage_with_point_id(self, controller):
        """Controller handles chunks with point_id attribute."""
        session = controller.start_session("Test")
        
        chunks = [
            MagicMock(point_id="point-1", spec=["point_id"]),
        ]
        
        controller.record_memory_usage(session, chunks)
        
        assert session.memory_state.chunks_used == ["point-1"]

    def test_record_memory_usage_with_dict_chunks(self, controller):
        """Controller handles chunks as dictionaries."""
        session = controller.start_session("Test")
        
        chunks = [
            {"id": "dict-chunk-1"},
            {"id": "dict-chunk-2"},
        ]
        
        controller.record_memory_usage(session, chunks)
        
        assert session.memory_state.chunks_used == ["dict-chunk-1", "dict-chunk-2"]

    def test_set_flag(self, controller):
        """AC#4: Controller can set session flags."""
        session = controller.start_session("Test")
        
        controller.set_flag(session, "is_research_triggered", True)
        controller.set_flag(session, "fallback_needed", True)
        
        assert session.flags.is_research_triggered is True
        assert session.flags.fallback_needed is True

    def test_set_flag_updates_timestamp(self, controller):
        """Setting flag updates session timestamp."""
        session = controller.start_session("Test")
        original = session.updated_at
        
        import time
        time.sleep(0.01)
        
        controller.set_flag(session, "gap_detected", True)
        
        assert session.updated_at > original


class TestShouldTriggerResearch:
    """Tests for should_trigger_research logic (AC#5)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    def test_returns_false_if_already_triggered(self, controller):
        """AC#5: Don't re-trigger if already triggered."""
        session = controller.start_session("Test")
        session.flags.is_research_triggered = True
        
        gap_analysis = {"coverage_gap": True, "coverage_score": 0.3}
        
        assert controller.should_trigger_research(session, gap_analysis) is False

    def test_returns_false_if_sufficient_memory(self, controller):
        """AC#5: Don't trigger if sufficient memory available."""
        session = controller.start_session("Test")
        session.flags.has_sufficient_memory = True
        
        gap_analysis = {"coverage_gap": True, "coverage_score": 0.3}
        
        assert controller.should_trigger_research(session, gap_analysis) is False

    def test_returns_true_on_coverage_gap(self, controller):
        """AC#5: Trigger on low coverage score."""
        session = controller.start_session("Test")
        
        gap_analysis = {
            "coverage_gap": True,
            "coverage_score": 0.4,  # Below 0.6 threshold
        }
        
        assert controller.should_trigger_research(session, gap_analysis) is True

    def test_returns_false_on_good_coverage(self, controller):
        """AC#5: Don't trigger on good coverage."""
        session = controller.start_session("Test")
        
        gap_analysis = {
            "coverage_gap": False,
            "coverage_score": 0.8,
        }
        
        assert controller.should_trigger_research(session, gap_analysis) is False

    def test_returns_true_on_recency_gap(self, controller):
        """AC#5: Trigger on recency gap."""
        session = controller.start_session("Test")
        
        gap_analysis = {
            "coverage_gap": False,
            "coverage_score": 0.8,
            "recency_gap": True,
        }
        
        assert controller.should_trigger_research(session, gap_analysis) is True

    def test_returns_false_with_no_gap_analysis(self, controller):
        """AC#5: Don't trigger without gap analysis."""
        session = controller.start_session("Test")
        
        assert controller.should_trigger_research(session, None) is False
        assert controller.should_trigger_research(session, {}) is False


class TestFreshnessComputation:
    """Tests for freshness score computation (AC#7)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    def test_fresh_chunk_has_score_near_one(self, controller):
        """AC#7: Fresh chunks (0 days) have score ~1.0."""
        now = datetime.now(timezone.utc)
        chunks = [MagicMock(id="fresh", created_at=now)]
        
        scores = controller._compute_freshness(chunks)
        
        assert scores["fresh"] > 0.99

    def test_30_day_old_chunk_has_half_score(self, controller):
        """AC#7: 30-day half-life decay."""
        now = datetime.now(timezone.utc)
        old_date = now - timedelta(days=30)
        chunks = [MagicMock(id="old", created_at=old_date)]
        
        scores = controller._compute_freshness(chunks)
        
        # At 30 days: score = 1/(1+30/30) = 0.5
        assert abs(scores["old"] - 0.5) < 0.01

    def test_60_day_old_chunk_has_third_score(self, controller):
        """AC#7: 60-day old chunk has score ~0.33."""
        now = datetime.now(timezone.utc)
        old_date = now - timedelta(days=60)
        chunks = [MagicMock(id="older", created_at=old_date)]
        
        scores = controller._compute_freshness(chunks)
        
        # At 60 days: score = 1/(1+60/30) = 1/3 ≈ 0.33
        assert abs(scores["older"] - 0.333) < 0.02

    def test_freshness_with_string_timestamp(self, controller):
        """AC#7: Handles ISO string timestamps."""
        now = datetime.now(timezone.utc)
        chunks = [{"id": "str-ts", "created_at": now.isoformat()}]
        
        scores = controller._compute_freshness(chunks)
        
        assert "str-ts" in scores
        assert scores["str-ts"] > 0.99

    def test_freshness_from_metadata(self, controller):
        """AC#7: Extracts timestamp from metadata dict."""
        now = datetime.now(timezone.utc)
        chunks = [
            MagicMock(
                id="meta-chunk",
                metadata={"created_at": now.isoformat()},
                spec=["id", "metadata"],
            )
        ]
        
        scores = controller._compute_freshness(chunks)
        
        assert "meta-chunk" in scores

    def test_average_freshness_computed(self, controller):
        """AC#7: Average freshness is computed on record."""
        session = controller.start_session("Test")
        now = datetime.now(timezone.utc)
        
        chunks = [
            MagicMock(id="fresh", created_at=now),
            MagicMock(id="old", created_at=now - timedelta(days=30)),
        ]
        
        controller.record_memory_usage(session, chunks)
        
        # Average of ~1.0 and ~0.5 = ~0.75
        assert 0.7 < session.memory_state.average_freshness < 0.8


class TestSessionSummary:
    """Tests for session summary generation."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    def test_get_session_summary(self, controller):
        """Summary includes all key metrics."""
        session = controller.start_session("What is Jarvis?")
        controller.start_stage(session, PlanStage.ASSESS)
        controller.complete_stage(session, PlanStage.ASSESS)
        controller.set_flag(session, "is_research_triggered", True)
        
        summary = controller.get_session_summary(session)
        
        assert summary["session_id"] == session.session_id
        assert "assess" in summary["completed_stages"]
        assert summary["research_triggered"] is True
        assert "flags" in summary


class TestEndSession:
    """Tests for session cleanup."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    def test_end_session_marks_running_stages_complete(self, controller):
        """Ending session completes running stages."""
        session = controller.start_session("Test")
        controller.start_stage(session, PlanStage.ASSESS)
        
        controller.end_session(session)
        
        assert session.plan_state["assess"].status == "complete"


class TestGlobalController:
    """Tests for global controller singleton."""

    def test_get_controller_returns_singleton(self):
        """get_controller returns same instance."""
        controller1 = get_controller()
        controller2 = get_controller()
        
        assert controller1 is controller2

    def test_controller_is_thread_safe(self):
        """Controller handles concurrent session creation."""
        controller = ARCHESController()
        sessions = []
        
        def create_session():
            s = controller.start_session("Concurrent test")
            sessions.append(s)
        
        threads = [threading.Thread(target=create_session) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All sessions should be unique
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 10


class TestAgentResults:
    """Tests for agent result recording."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    def test_record_agent_result(self, controller):
        """Controller can record agent results."""
        session = controller.start_session("Test")
        result1 = MagicMock(persona_name="Rick", content="Answer 1")
        result2 = MagicMock(persona_name="Morty", content="Answer 2")
        
        controller.record_agent_result(session, result1)
        controller.record_agent_result(session, result2)
        
        assert len(session.agent_results) == 2
        assert session.agent_results[0].persona_name == "Rick"
        assert session.agent_results[1].persona_name == "Morty"
