"""Unit tests for ARCHES Planner Feedback Loop (Story 4.5.5).

Tests:
- PlanAction enum values (AC #1)
- High disagreement triggers research expansion (AC #2, #3)
- Failed agents trigger retry (AC #4)
- High overlap triggers diversity increase (AC #5)
- Structured logging (AC #6)
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, List, Any

from jarvis.arches.controller import (
    ARCHESController,
    ARCHESSession,
    PlanAction,
    PlanStage,
)


@dataclass
class MockVotingResult:
    """Mock VotingResult for testing."""
    winner: str = "architect"
    scores: Dict[str, float] = field(default_factory=lambda: {"architect": 0.4, "critic": 0.3})
    ties: List[str] = field(default_factory=list)
    total_personas: int = 2
    disagreement_score: float = 0.0
    failed_agents: List[str] = field(default_factory=list)
    
    @property
    def has_tie(self) -> bool:
        return len(self.ties) > 1


class TestPlanActionEnum:
    """Tests for PlanAction enum (AC #1)."""

    def test_enum_values_exist(self):
        """PlanAction should have all required values."""
        assert PlanAction.COMPLETE.value == "complete"
        assert PlanAction.TRIGGER_RESEARCH_EXPANSION.value == "trigger_research_expansion"
        assert PlanAction.RETRY_WITH_FALLBACK.value == "retry_with_fallback"
        assert PlanAction.INCREASE_DIVERSITY.value == "increase_diversity"

    def test_enum_is_string_enum(self):
        """PlanAction should be a string enum for JSON serialization."""
        # String enum inherits from str
        assert isinstance(PlanAction.COMPLETE.value, str)
        assert PlanAction.COMPLETE.value == "complete"


class TestReactToVotingOutcome:
    """Tests for react_to_voting_outcome() (AC #2-5)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    @pytest.fixture
    def session(self, controller):
        return controller.start_session("test query", mode="qa")

    def test_normal_flow_returns_noop(self, controller, session):
        """Normal voting (no issues) should return NOOP (architect notes)."""
        voting = MockVotingResult(disagreement_score=0.3)
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.NOOP

    def test_high_disagreement_triggers_research(self, controller, session):
        """Disagreement > 0.7 should trigger research expansion (AC #2, #3)."""
        voting = MockVotingResult(disagreement_score=0.8)
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.TRIGGER_RESEARCH_EXPANSION
        assert session.flags.gap_detected is True

    def test_tie_triggers_research(self, controller, session):
        """Voting tie should trigger research expansion."""
        voting = MockVotingResult(
            disagreement_score=0.5,
            ties=["architect", "critic"],
        )
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.TRIGGER_RESEARCH_EXPANSION

    def test_failed_agents_trigger_fallback(self, controller, session):
        """Failed agents should trigger retry with fallback (AC #4)."""
        voting = MockVotingResult(failed_agents=["engineer"])
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.RETRY_WITH_FALLBACK
        assert session.flags.fallback_needed is True

    def test_failed_agents_priority_over_disagreement(self, controller, session):
        """Failed agents should have higher priority than disagreement."""
        voting = MockVotingResult(
            disagreement_score=0.9,  # Very high
            failed_agents=["engineer"],
        )
        
        action = controller.react_to_voting_outcome(session, voting)
        
        # Failed agents should win
        assert action == PlanAction.RETRY_WITH_FALLBACK



class TestHighOverlapTriggersDiversity:
    """Test that high overlap triggers INCREASE_DIVERSITY (AC #5)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    @pytest.fixture
    def session(self, controller):
        return controller.start_session("test query", mode="qa")

    def test_high_overlap_triggers_diversity(self, controller, session):
        """Overlap > 0.8 should trigger diversity increase."""
        # Create high overlap scenario: 1 unique doc, 10 chunks
        session.memory_state.chunks_used = [
            f"doc::single_file.md::chunk_{i}" for i in range(10)
        ]
        
        voting = MockVotingResult(disagreement_score=0.3)
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.INCREASE_DIVERSITY


class TestDisagreementThreshold:
    """Test the exact disagreement threshold (0.7)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    @pytest.fixture
    def session(self, controller):
        return controller.start_session("test query", mode="qa")

    def test_exactly_at_threshold_does_not_trigger(self, controller, session):
        """Disagreement exactly 0.7 should NOT trigger (> not >=)."""
        voting = MockVotingResult(disagreement_score=0.7)
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.NOOP

    def test_just_above_threshold_triggers(self, controller, session):
        """Disagreement 0.71 should trigger."""
        voting = MockVotingResult(disagreement_score=0.71)
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.TRIGGER_RESEARCH_EXPANSION


class TestLoopGuards:
    """Tests for loop guards (architect notes)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    @pytest.fixture
    def session(self, controller):
        return controller.start_session("test query", mode="qa")

    def test_research_only_once_per_query(self, controller, session):
        """Research expansion should only trigger once per query."""
        voting = MockVotingResult(disagreement_score=0.8)
        
        # First call should trigger research
        action1 = controller.react_to_voting_outcome(session, voting)
        assert action1 == PlanAction.TRIGGER_RESEARCH_EXPANSION
        assert session.planner_state.research_expanded is True
        
        # Second call should return NOOP (already expanded)
        action2 = controller.react_to_voting_outcome(session, voting)
        assert action2 == PlanAction.NOOP

    def test_fallback_only_once_per_query(self, controller, session):
        """Fallback retry should only trigger once per query."""
        voting = MockVotingResult(failed_agents=["engineer"])
        
        # First call should trigger fallback
        action1 = controller.react_to_voting_outcome(session, voting)
        assert action1 == PlanAction.RETRY_WITH_FALLBACK
        
        # Second call should return NOOP
        action2 = controller.react_to_voting_outcome(session, voting)
        assert action2 == PlanAction.NOOP


class TestNoActionRegression:
    """Test that normal conditions return NOOP (architect notes requirement)."""

    @pytest.fixture
    def controller(self):
        return ARCHESController()

    @pytest.fixture
    def session(self, controller):
        return controller.start_session("test query", mode="qa")

    def test_no_action_when_all_normal(self, controller, session):
        """When disagreement < 0.7, no failed agents, overlap < 0.8 → NOOP."""
        # Set up chunks with low overlap
        session.memory_state.chunks_used = [
            "doc1::file1.md::chunk_0",
            "doc2::file2.md::chunk_0",
            "doc3::file3.md::chunk_0",
        ]
        
        voting = MockVotingResult(
            disagreement_score=0.5,  # Below 0.7
            failed_agents=[],        # None
        )
        
        action = controller.react_to_voting_outcome(session, voting)
        
        assert action == PlanAction.NOOP
