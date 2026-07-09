"""Tests for Story 11-6 AC3 (Promotion) and AC5 (Class Binding)."""
import pytest
from uuid import uuid4

from jarvis.knowledge.tiers import KnowledgeTier, SourceType
from jarvis.ingestion.promotion import (
    EvidencePromotionWorkflow,
    PromotionRequest,
    PromotionResult,
)
from jarvis.ingestion.class_binding import (
    KnowledgeClassBinder,
    DeclaredKnowledgeClass,
)


class TestEvidencePromotionWorkflow:
    """Tests for AC3: Evidence Promotion Workflow."""
    
    def test_auto_promote_k4_to_k3_high_score(self):
        """K4 → K3 auto-promotes if score >= 0.3."""
        workflow = EvidencePromotionWorkflow()
        request = PromotionRequest(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
            requester="test",
            trust_score=0.5,
        )
        result = workflow.request_promotion(request)
        assert result.approved is True
        assert result.new_tier == KnowledgeTier.K3
        assert "auto-promotion" in result.reason.lower()
    
    def test_auto_promote_k4_to_k3_low_score_denied(self):
        """K4 → K3 denied if score < 0.3."""
        workflow = EvidencePromotionWorkflow()
        request = PromotionRequest(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
            requester="test",
            trust_score=0.2,
        )
        result = workflow.request_promotion(request)
        assert result.approved is False
        assert result.new_tier == KnowledgeTier.K4
    
    def test_k3_to_k2_requires_arbitration(self):
        """K3 → K2 requires dual-persona arbitration."""
        workflow = EvidencePromotionWorkflow()
        request = PromotionRequest(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
            requester="test",
            trust_score=0.8,
        )
        result = workflow.request_promotion(request)
        assert result.approved is False
        assert result.arbitration_required is True
    
    def test_k2_to_k1_requires_human(self):
        """K2 → K1 requires human reviewer."""
        workflow = EvidencePromotionWorkflow()
        request = PromotionRequest(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K2,
            target_tier=KnowledgeTier.K1,
            requester="test",
            trust_score=0.95,
        )
        result = workflow.request_promotion(request)
        assert result.approved is False
        assert "human" in result.reason.lower() or "governance" in result.reason.lower()
    
    def test_k1_to_k0_never_allowed(self):
        """K1 → K0 never allowed via promotion."""
        workflow = EvidencePromotionWorkflow()
        request = PromotionRequest(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K1,
            target_tier=KnowledgeTier.K0,
            requester="test",
            trust_score=1.0,
        )
        result = workflow.request_promotion(request)
        assert result.approved is False
        assert "k0" in result.reason.lower()
    
    def test_approve_with_authorization(self):
        """Manual authorization allows K2 → K1."""
        workflow = EvidencePromotionWorkflow()
        request = PromotionRequest(
            knowledge_unit_id=uuid4(),
            current_tier=KnowledgeTier.K2,
            target_tier=KnowledgeTier.K1,
            requester="test",
            trust_score=0.95,
        )
        result = workflow.approve_with_authorization(request, authorized_by="human_reviewer")
        assert result.approved is True
        assert result.new_tier == KnowledgeTier.K1


class TestKnowledgeClassBinder:
    """Tests for AC5: Knowledge Class Binding."""
    
    def test_no_declared_class_passes(self):
        """No declared class = no validation needed."""
        binder = KnowledgeClassBinder()
        result = binder.validate(
            declared_class=None,
            source_type=SourceType.SENSOR,
            inferred_tier=KnowledgeTier.K0,
        )
        assert result.valid is True
        assert result.trust_penalty == 0.0
    
    def test_valid_binding_sensor_primary(self):
        """Sensor claiming primary_evidence is valid."""
        binder = KnowledgeClassBinder()
        result = binder.validate(
            declared_class="primary_evidence",
            source_type=SourceType.SENSOR,
            inferred_tier=KnowledgeTier.K0,
        )
        assert result.valid is True
        assert result.trust_penalty == 0.0
    
    def test_news_claiming_primary_evidence_blocked(self):
        """News cannot claim primary_evidence - gets penalized."""
        binder = KnowledgeClassBinder()
        result = binder.validate(
            declared_class="primary_evidence",
            source_type=SourceType.NEWS_ARTICLE,
            inferred_tier=KnowledgeTier.K3,
        )
        assert result.valid is False
        assert result.trust_penalty >= 0.5
        assert result.final_tier == KnowledgeTier.K4
    
    def test_social_claiming_expert_opinion_blocked(self):
        """Social media cannot claim expert_opinion."""
        binder = KnowledgeClassBinder()
        result = binder.validate(
            declared_class="expert_opinion",
            source_type=SourceType.SOCIAL_MEDIA,
            inferred_tier=KnowledgeTier.K4,
        )
        assert result.valid is False
        assert result.trust_penalty >= 0.5
    
    def test_unknown_class_downgrades(self):
        """Unknown knowledge class gets downgraded."""
        binder = KnowledgeClassBinder()
        result = binder.validate(
            declared_class="fake_class",
            source_type=SourceType.SENSOR,
            inferred_tier=KnowledgeTier.K0,
        )
        assert result.valid is False
        assert result.final_tier == KnowledgeTier.K4
    
    def test_overclaiming_penalty(self):
        """Source claiming higher class than tier supports gets penalized."""
        binder = KnowledgeClassBinder()
        result = binder.validate(
            declared_class="verified_analysis",
            source_type=SourceType.PEER_REVIEWED_PAPER,  # This is K2
            inferred_tier=KnowledgeTier.K2,  # K2 doesn't support verified_analysis
        )
        assert result.valid is False
        assert result.trust_penalty > 0
