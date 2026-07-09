"""Unit tests for ReasoningEngine Integration (Story 11-5, Task 7).

Tests BMAD boundaries, hypothesis tracking, and usage policy enforcement.
Coverage target: ≥90% per AC #7 requirements.
"""

import pytest
from uuid import uuid4

from src.jarvis.knowledge.reasoning_integration import (
    ReasoningContext,
    REASONING_TO_USAGE_MAP,
    KnowledgeAccessResult,
    HypothesisRecord,
    KnowledgeSovereigntyEngine,
    create_sovereignty_engine,
)
from src.jarvis.knowledge.tiers import KnowledgeTier
from src.jarvis.knowledge.usage_policy import UsageClass, ConstitutionalDenial


class TestReasoningContextMapping:
    """Test reasoning context to usage class mapping."""

    def test_execution_maps_to_execution_guidance(self):
        """Test execution context maps to execution guidance."""
        assert REASONING_TO_USAGE_MAP[ReasoningContext.EXECUTION] == UsageClass.EXECUTION_GUIDANCE

    def test_governance_maps_to_governance(self):
        """Test governance context maps to governance usage."""
        assert REASONING_TO_USAGE_MAP[ReasoningContext.GOVERNANCE] == UsageClass.GOVERNANCE

    def test_hypothesis_maps_to_ideation(self):
        """Test hypothesis context maps to ideation."""
        assert REASONING_TO_USAGE_MAP[ReasoningContext.HYPOTHESIS] == UsageClass.IDEATION

    def test_exploration_maps_to_ideation(self):
        """Test exploration context maps to ideation."""
        assert REASONING_TO_USAGE_MAP[ReasoningContext.EXPLORATION] == UsageClass.IDEATION


class TestHypothesisRecord:
    """Test hypothesis record."""

    def test_create_hypothesis(self):
        """Test creating hypothesis record."""
        hypothesis = HypothesisRecord(
            hypothesis_id=uuid4(),
            content="Test hypothesis",
            proposed_by="bmad",
            confidence=0.7,
        )

        assert hypothesis.tier == KnowledgeTier.K4  # Always starts as noise
        assert hypothesis.status == "pending"
        assert hypothesis.supporting_evidence == []

    def test_hypothesis_with_evidence(self):
        """Test hypothesis with supporting evidence."""
        evidence_ids = [uuid4(), uuid4()]

        hypothesis = HypothesisRecord(
            hypothesis_id=uuid4(),
            content="Test",
            proposed_by="bmad",
            confidence=0.8,
            supporting_evidence=evidence_ids,
        )

        assert len(hypothesis.supporting_evidence) == 2


class TestKnowledgeSovereigntyEngine:
    """Test knowledge sovereignty engine."""

    @pytest.fixture
    def engine(self):
        """Create sovereignty engine."""
        return KnowledgeSovereigntyEngine(enable_strict_mode=False)

    @pytest.fixture
    def strict_engine(self):
        """Create strict mode engine."""
        return KnowledgeSovereigntyEngine(enable_strict_mode=True)

    def test_access_knowledge_allowed(self, engine):
        """Test accessing knowledge when tier is allowed (AC #7: BMAD may read all classes)."""
        ku_id = uuid4()

        result = engine.access_knowledge(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K0,
            content="Ground truth data",
            reasoning_context=ReasoningContext.EXECUTION,
            requester="reasoning_engine",
            trust=1.0,
        )

        assert result.allowed is True
        assert result.content == "Ground truth data"
        assert result.tier == KnowledgeTier.K0
        assert result.trust == 1.0

    def test_access_knowledge_denied(self, engine):
        """Test accessing knowledge when tier is not allowed."""
        ku_id = uuid4()

        result = engine.access_knowledge(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K3,  # Narrative
            content="News article",
            reasoning_context=ReasoningContext.EXECUTION,  # Only allows K0, K1
            requester="reasoning_engine",
        )

        assert result.allowed is False
        assert result.content is None  # No content returned
        assert result.tier == KnowledgeTier.K3

    def test_access_knowledge_strict_mode_raises(self, strict_engine):
        """Test that strict mode raises ConstitutionalDenial on violation."""
        ku_id = uuid4()

        with pytest.raises(ConstitutionalDenial):
            strict_engine.access_knowledge(
                knowledge_unit_id=ku_id,
                tier=KnowledgeTier.K3,
                content="Test",
                reasoning_context=ReasoningContext.EXECUTION,
            )

    def test_access_logs_violation(self, engine):
        """Test that violations are logged to audit."""
        ku_id = uuid4()

        engine.access_knowledge(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K4,
            content="Noise",
            reasoning_context=ReasoningContext.GOVERNANCE,  # K4 not allowed
        )

        # Check audit log
        from src.jarvis.knowledge.audit import EpistemicEventType
        violations = engine.audit_log.query_by_type(EpistemicEventType.USAGE_VIOLATION)
        # Should have logged violation
        assert len(violations) > 0

    def test_propose_hypothesis(self, engine):
        """Test proposing hypothesis (AC #7: BMAD may propose hypotheses)."""
        hypothesis = engine.propose_hypothesis(
            content="System performance will improve",
            proposed_by="bmad",
            confidence=0.75,
            supporting_evidence=[uuid4()],
        )

        assert hypothesis.tier == KnowledgeTier.K4  # Always starts as noise
        assert hypothesis.status == "pending"
        assert hypothesis.confidence == 0.75
        assert len(hypothesis.supporting_evidence) == 1

    def test_propose_hypothesis_invalid_confidence(self, engine):
        """Test that invalid confidence is rejected."""
        with pytest.raises(ValueError, match="confidence must be in"):
            engine.propose_hypothesis(
                content="Test",
                proposed_by="bmad",
                confidence=1.5,  # Out of bounds
            )

    def test_attempt_tier_promotion_unauthorized(self, engine):
        """Test tier promotion by unauthorized requester (AC #7: BMAD may NOT upgrade)."""
        ku_id = uuid4()

        success, reason = engine.attempt_tier_promotion(
            knowledge_unit_id=ku_id,
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
            requester="bmad",  # Not authorized
        )

        assert success is False
        assert "not authorized" in reason.lower()

    def test_attempt_tier_promotion_authorized(self, engine):
        """Test tier promotion by authorized requester."""
        ku_id = uuid4()

        success, reason = engine.attempt_tier_promotion(
            knowledge_unit_id=ku_id,
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
            requester="governance",  # Authorized
        )

        assert success is True
        assert "authorized" in reason.lower()

    def test_attempt_tier_promotion_human_authorized(self, engine):
        """Test that human is authorized for promotion."""
        ku_id = uuid4()

        success, _ = engine.attempt_tier_promotion(
            knowledge_unit_id=ku_id,
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
            requester="human",
        )

        assert success is True

    def test_get_hypothesis(self, engine):
        """Test retrieving hypothesis by ID."""
        hypothesis = engine.propose_hypothesis(
            content="Test hypothesis",
            proposed_by="bmad",
            confidence=0.7,
        )

        retrieved = engine.get_hypothesis(hypothesis.hypothesis_id)

        assert retrieved is not None
        assert retrieved.hypothesis_id == hypothesis.hypothesis_id
        assert retrieved.content == "Test hypothesis"

    def test_get_hypothesis_not_found(self, engine):
        """Test retrieving non-existent hypothesis."""
        non_existent_id = uuid4()
        result = engine.get_hypothesis(non_existent_id)
        assert result is None

    def test_list_hypotheses(self, engine):
        """Test listing hypotheses."""
        engine.propose_hypothesis("Hyp 1", "bmad", 0.7)
        engine.propose_hypothesis("Hyp 2", "reasoner", 0.8)
        engine.propose_hypothesis("Hyp 3", "bmad", 0.6)

        all_hypotheses = engine.list_hypotheses()
        assert len(all_hypotheses) == 3

    def test_list_hypotheses_filter_by_proposer(self, engine):
        """Test filtering hypotheses by proposer."""
        engine.propose_hypothesis("Hyp 1", "bmad", 0.7)
        engine.propose_hypothesis("Hyp 2", "reasoner", 0.8)
        engine.propose_hypothesis("Hyp 3", "bmad", 0.6)

        bmad_hypotheses = engine.list_hypotheses(proposed_by="bmad")
        assert len(bmad_hypotheses) == 2
        assert all(h.proposed_by == "bmad" for h in bmad_hypotheses)

    def test_list_hypotheses_filter_by_status(self, engine):
        """Test filtering hypotheses by status."""
        hyp1 = engine.propose_hypothesis("Hyp 1", "bmad", 0.7)
        hyp2 = engine.propose_hypothesis("Hyp 2", "bmad", 0.8)

        # Approve one
        engine.approve_hypothesis(hyp1.hypothesis_id, "human")

        approved = engine.list_hypotheses(status="approved")
        pending = engine.list_hypotheses(status="pending")

        assert len(approved) == 1
        assert len(pending) == 1

    def test_approve_hypothesis(self, engine):
        """Test approving hypothesis."""
        hypothesis = engine.propose_hypothesis("Test", "bmad", 0.7)

        success, reason = engine.approve_hypothesis(
            hypothesis.hypothesis_id,
            approved_by="human",
        )

        assert success is True
        assert hypothesis.status == "approved"

    def test_approve_hypothesis_not_found(self, engine):
        """Test approving non-existent hypothesis."""
        non_existent_id = uuid4()

        success, reason = engine.approve_hypothesis(non_existent_id, "human")

        assert success is False
        assert "not found" in reason.lower()

    def test_reject_hypothesis(self, engine):
        """Test rejecting hypothesis."""
        hypothesis = engine.propose_hypothesis("Test", "bmad", 0.7)

        success, reason = engine.reject_hypothesis(
            hypothesis.hypothesis_id,
            rejected_by="human",
            reason="Insufficient evidence",
        )

        assert success is True
        assert hypothesis.status == "rejected"

    def test_reject_hypothesis_not_found(self, engine):
        """Test rejecting non-existent hypothesis."""
        non_existent_id = uuid4()

        success, reason = engine.reject_hypothesis(
            non_existent_id,
            rejected_by="human",
            reason="Test",
        )

        assert success is False
        assert "not found" in reason.lower()

    def test_get_allowed_tiers_for_context(self, engine):
        """Test getting allowed tiers for reasoning context."""
        exec_tiers = engine.get_allowed_tiers_for_context(ReasoningContext.EXECUTION)
        assert exec_tiers == {KnowledgeTier.K0, KnowledgeTier.K1}

        gov_tiers = engine.get_allowed_tiers_for_context(ReasoningContext.GOVERNANCE)
        assert KnowledgeTier.K2 in gov_tiers
        assert KnowledgeTier.K4 not in gov_tiers

        hyp_tiers = engine.get_allowed_tiers_for_context(ReasoningContext.HYPOTHESIS)
        assert len(hyp_tiers) == 5  # All tiers allowed

    def test_filter_knowledge_by_context(self, engine):
        """Test filtering knowledge units by context."""
        knowledge_units = [
            (uuid4(), KnowledgeTier.K0),
            (uuid4(), KnowledgeTier.K1),
            (uuid4(), KnowledgeTier.K3),
            (uuid4(), KnowledgeTier.K4),
        ]

        # Filter for execution (only K0, K1 allowed)
        allowed_ids = engine.filter_knowledge_by_context(
            knowledge_units=knowledge_units,
            reasoning_context=ReasoningContext.EXECUTION,
        )

        assert len(allowed_ids) == 2  # Only K0 and K1

    def test_get_access_statistics(self, engine):
        """Test getting access statistics."""
        # Generate some activity
        engine.propose_hypothesis("Hyp 1", "bmad", 0.7)
        engine.propose_hypothesis("Hyp 2", "bmad", 0.8)
        engine.access_knowledge(
            uuid4(), KnowledgeTier.K3, "Test", ReasoningContext.EXECUTION
        )  # Violation

        stats = engine.get_access_statistics()

        assert "total_hypotheses" in stats
        assert "hypotheses_by_status" in stats
        assert "usage_violations" in stats
        assert "audit_events" in stats
        assert stats["total_hypotheses"] == 2

    def test_hypotheses_start_as_noise(self, engine):
        """Test that all hypotheses start at K4 (AC #7: cannot promote without auth)."""
        hyp1 = engine.propose_hypothesis("Test 1", "bmad", 0.9)
        hyp2 = engine.propose_hypothesis("Test 2", "reasoner", 0.95)

        assert hyp1.tier == KnowledgeTier.K4
        assert hyp2.tier == KnowledgeTier.K4

    def test_context_mapping_execution(self, engine):
        """Test that execution context enforces strict tier policy."""
        ku_id = uuid4()

        # K0 allowed
        result = engine.access_knowledge(
            ku_id, KnowledgeTier.K0, "Test", ReasoningContext.EXECUTION
        )
        assert result.allowed is True

        # K3 not allowed
        result = engine.access_knowledge(
            ku_id, KnowledgeTier.K3, "Test", ReasoningContext.EXECUTION
        )
        assert result.allowed is False

    def test_context_mapping_hypothesis(self, engine):
        """Test that hypothesis context allows all tiers."""
        ku_id = uuid4()

        # All tiers should be allowed for hypothesis generation
        for tier in KnowledgeTier:
            result = engine.access_knowledge(
                ku_id, tier, "Test", ReasoningContext.HYPOTHESIS
            )
            assert result.allowed is True, f"{tier} should be allowed for hypothesis"

    def test_audit_trail_created(self, engine):
        """Test that operations create audit trail."""
        initial_count = engine.audit_log.get_event_count()

        # Propose hypothesis
        engine.propose_hypothesis("Test", "bmad", 0.7)

        # Access knowledge (violation)
        engine.access_knowledge(
            uuid4(), KnowledgeTier.K3, "Test", ReasoningContext.EXECUTION
        )

        final_count = engine.audit_log.get_event_count()
        assert final_count > initial_count


class TestCreateSovereigntyEngine:
    """Test convenience function."""

    def test_create_default_engine(self):
        """Test creating engine with defaults."""
        engine = create_sovereignty_engine()

        assert engine is not None
        assert engine.enable_strict_mode is True
        assert engine.usage_policy is not None
        assert engine.audit_log is not None

    def test_create_non_strict_engine(self):
        """Test creating non-strict engine."""
        engine = create_sovereignty_engine(enable_strict_mode=False)

        assert engine.enable_strict_mode is False


class TestBMADBoundaries:
    """Test enforcement of BMAD boundaries (AC #7)."""

    @pytest.fixture
    def engine(self):
        """Create engine."""
        return KnowledgeSovereigntyEngine(enable_strict_mode=False)

    def test_bmad_can_read_all_tiers(self, engine):
        """Test AC #7: BMAD may read all knowledge classes."""
        # BMAD can read any tier in appropriate context
        for tier in KnowledgeTier:
            result = engine.access_knowledge(
                uuid4(),
                tier,
                "Test content",
                ReasoningContext.HYPOTHESIS,  # Permissive context
                requester="bmad",
            )
            assert result.allowed is True

    def test_bmad_can_propose_hypotheses(self, engine):
        """Test AC #7: BMAD may propose hypotheses."""
        hypothesis = engine.propose_hypothesis(
            content="Test hypothesis",
            proposed_by="bmad",
            confidence=0.8,
        )

        assert hypothesis is not None
        assert hypothesis.proposed_by == "bmad"

    def test_bmad_cannot_promote_tiers(self, engine):
        """Test AC #7: BMAD may NOT upgrade tier without authorization."""
        success, reason = engine.attempt_tier_promotion(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
            requester="bmad",
        )

        assert success is False
        assert "not authorized" in reason.lower()

    def test_bmad_cannot_bypass_usage_policy(self, engine):
        """Test AC #7: BMAD may NOT bypass knowledge usage policy."""
        # Attempt to use K3 for execution (not allowed)
        result = engine.access_knowledge(
            knowledge_unit_id=uuid4(),
            tier=KnowledgeTier.K3,
            content="Narrative",
            reasoning_context=ReasoningContext.EXECUTION,
            requester="bmad",
        )

        assert result.allowed is False

    def test_governance_can_promote_tiers(self, engine):
        """Test that governance IS authorized for promotion."""
        success, _ = engine.attempt_tier_promotion(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
            requester="governance",
        )

        assert success is True
