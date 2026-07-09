"""Unit tests for Knowledge Tier System (Story 11-5, Task 1).

Tests tier assignment, promotion/demotion rules, and immutability enforcement.
Coverage target: ≥90% per AC #1 requirements.
"""

import pytest
from src.jarvis.knowledge.tiers import (
    KnowledgeTier,
    SourceType,
    CollectionMethod,
    TierAssignmentContext,
    assign_tier,
    can_promote,
    can_demote,
    validate_tier_transition,
    TierTransitionError,
)


class TestKnowledgeTier:
    """Test KnowledgeTier enum properties."""

    def test_tier_values(self):
        """Test that all tier values match specification."""
        assert KnowledgeTier.K0.value == "ground_truth"
        assert KnowledgeTier.K1.value == "verified_derivation"
        assert KnowledgeTier.K2.value == "trust_scored_external"
        assert KnowledgeTier.K3.value == "narrative"
        assert KnowledgeTier.K4.value == "noise"

    def test_tier_ordering(self):
        """Test tier partial order: K0 ≺ K1 ≺ K2 ≺ K3 ≺ K4."""
        assert KnowledgeTier.K0 < KnowledgeTier.K1
        assert KnowledgeTier.K1 < KnowledgeTier.K2
        assert KnowledgeTier.K2 < KnowledgeTier.K3
        assert KnowledgeTier.K3 < KnowledgeTier.K4

        # Transitivity
        assert KnowledgeTier.K0 < KnowledgeTier.K4

    def test_trust_rank(self):
        """Test trust rank mapping."""
        assert KnowledgeTier.K0.trust_rank == 0
        assert KnowledgeTier.K1.trust_rank == 1
        assert KnowledgeTier.K2.trust_rank == 2
        assert KnowledgeTier.K3.trust_rank == 3
        assert KnowledgeTier.K4.trust_rank == 4


class TestTierAssignmentContext:
    """Test TierAssignmentContext validation."""

    def test_valid_context(self):
        """Test valid context creation."""
        context = TierAssignmentContext(
            source_type=SourceType.TELEMETRY,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="sensor://device-001",
            initial_confidence=0.95
        )
        assert context.source_type == SourceType.TELEMETRY
        assert context.initial_confidence == 0.95

    def test_invalid_confidence_high(self):
        """Test that confidence > 1.0 is rejected."""
        with pytest.raises(ValueError, match="initial_confidence must be in"):
            TierAssignmentContext(
                source_type=SourceType.TELEMETRY,
                collection_method=CollectionMethod.DIRECT_CAPTURE,
                origin="sensor://test",
                initial_confidence=1.5
            )

    def test_invalid_confidence_low(self):
        """Test that confidence < 0.0 is rejected."""
        with pytest.raises(ValueError, match="initial_confidence must be in"):
            TierAssignmentContext(
                source_type=SourceType.TELEMETRY,
                collection_method=CollectionMethod.DIRECT_CAPTURE,
                origin="sensor://test",
                initial_confidence=-0.1
            )

    def test_boundary_confidence_values(self):
        """Test boundary values 0.0 and 1.0 are accepted."""
        context_min = TierAssignmentContext(
            source_type=SourceType.TELEMETRY,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="test",
            initial_confidence=0.0
        )
        assert context_min.initial_confidence == 0.0

        context_max = TierAssignmentContext(
            source_type=SourceType.TELEMETRY,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="test",
            initial_confidence=1.0
        )
        assert context_max.initial_confidence == 1.0


class TestAssignTier:
    """Test tier assignment function (AC #1: Tier Assignment Function)."""

    # K0: Ground Truth Tests
    def test_assign_k0_telemetry(self):
        """Test telemetry → K0."""
        context = TierAssignmentContext(
            source_type=SourceType.TELEMETRY,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="sensor://device-001"
        )
        assert assign_tier(context) == KnowledgeTier.K0

    def test_assign_k0_sensor(self):
        """Test sensor → K0."""
        context = TierAssignmentContext(
            source_type=SourceType.SENSOR,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="sensor://temp-probe-42"
        )
        assert assign_tier(context) == KnowledgeTier.K0

    def test_assign_k0_device_metrics(self):
        """Test on-device metrics → K0."""
        context = TierAssignmentContext(
            source_type=SourceType.ON_DEVICE_METRICS,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="metrics://cpu_usage"
        )
        assert assign_tier(context) == KnowledgeTier.K0

    def test_assign_k0_system_logs(self):
        """Test system logs → K0."""
        context = TierAssignmentContext(
            source_type=SourceType.SYSTEM_LOGS,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="file:///var/log/syslog"
        )
        assert assign_tier(context) == KnowledgeTier.K0

    # K1: Verified Derivation Tests
    def test_assign_k1_internal_analytics(self):
        """Test internal analytics → K1."""
        context = TierAssignmentContext(
            source_type=SourceType.INTERNAL_ANALYTICS,
            collection_method=CollectionMethod.API_FETCH,
            origin="analytics://user-engagement"
        )
        assert assign_tier(context) == KnowledgeTier.K1

    def test_assign_k1_derived_model(self):
        """Test derived model → K1."""
        context = TierAssignmentContext(
            source_type=SourceType.DERIVED_MODEL,
            collection_method=CollectionMethod.API_FETCH,
            origin="model://prediction-v1.2"
        )
        assert assign_tier(context) == KnowledgeTier.K1

    def test_assign_k1_processed_metrics(self):
        """Test processed metrics → K1."""
        context = TierAssignmentContext(
            source_type=SourceType.PROCESSED_METRICS,
            collection_method=CollectionMethod.API_FETCH,
            origin="metrics://aggregated_daily"
        )
        assert assign_tier(context) == KnowledgeTier.K1

    # K2: Trust-Scored External Tests
    def test_assign_k2_peer_reviewed_paper(self):
        """Test peer-reviewed paper → K2."""
        context = TierAssignmentContext(
            source_type=SourceType.PEER_REVIEWED_PAPER,
            collection_method=CollectionMethod.DOCUMENT_PARSE,
            origin="doi://10.1234/example.paper"
        )
        assert assign_tier(context) == KnowledgeTier.K2

    def test_assign_k2_academic_book(self):
        """Test academic book → K2."""
        context = TierAssignmentContext(
            source_type=SourceType.ACADEMIC_BOOK,
            collection_method=CollectionMethod.DOCUMENT_PARSE,
            origin="isbn://978-0-123456-78-9"
        )
        assert assign_tier(context) == KnowledgeTier.K2

    def test_assign_k2_technical_standard(self):
        """Test technical standard → K2."""
        context = TierAssignmentContext(
            source_type=SourceType.TECHNICAL_STANDARD,
            collection_method=CollectionMethod.DOCUMENT_PARSE,
            origin="standard://ISO-9001"
        )
        assert assign_tier(context) == KnowledgeTier.K2

    def test_assign_k2_official_docs(self):
        """Test official documentation → K2."""
        context = TierAssignmentContext(
            source_type=SourceType.OFFICIAL_DOCUMENTATION,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://docs.python.org/3/"
        )
        assert assign_tier(context) == KnowledgeTier.K2

    # K3: Narrative Tests
    def test_assign_k3_news_article(self):
        """Test news article → K3."""
        context = TierAssignmentContext(
            source_type=SourceType.NEWS_ARTICLE,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://news.example.com/article"
        )
        assert assign_tier(context) == KnowledgeTier.K3

    def test_assign_k3_blog_post(self):
        """Test blog post → K3."""
        context = TierAssignmentContext(
            source_type=SourceType.BLOG_POST,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://blog.example.com/post"
        )
        assert assign_tier(context) == KnowledgeTier.K3

    def test_assign_k3_expert_commentary(self):
        """Test expert commentary → K3."""
        context = TierAssignmentContext(
            source_type=SourceType.EXPERT_COMMENTARY,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://expert.opinion.com/article"
        )
        assert assign_tier(context) == KnowledgeTier.K3

    def test_assign_k3_interview(self):
        """Test interview → K3."""
        context = TierAssignmentContext(
            source_type=SourceType.INTERVIEW,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://interview.example.com"
        )
        assert assign_tier(context) == KnowledgeTier.K3

    # K4: Noise Tests
    def test_assign_k4_social_media(self):
        """Test social media → K4."""
        context = TierAssignmentContext(
            source_type=SourceType.SOCIAL_MEDIA,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://twitter.com/user/status/123"
        )
        assert assign_tier(context) == KnowledgeTier.K4

    def test_assign_k4_forum_post(self):
        """Test forum post → K4."""
        context = TierAssignmentContext(
            source_type=SourceType.FORUM_POST,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://forum.example.com/thread/456"
        )
        assert assign_tier(context) == KnowledgeTier.K4

    def test_assign_k4_web_scrape(self):
        """Test web scrape → K4."""
        context = TierAssignmentContext(
            source_type=SourceType.WEB_SCRAPE,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://random.site.com/page"
        )
        assert assign_tier(context) == KnowledgeTier.K4

    def test_assign_k4_unverified(self):
        """Test unverified source → K4."""
        context = TierAssignmentContext(
            source_type=SourceType.UNVERIFIED_SOURCE,
            collection_method=CollectionMethod.WEB_FETCH,
            origin="https://unknown.com"
        )
        assert assign_tier(context) == KnowledgeTier.K4

    # Synthetic/Agent-Generated Tests (Story 11-7 compatibility)
    def test_assign_k4_agent_generated(self):
        """Test agent-generated content → K4 (Story 11-7)."""
        context = TierAssignmentContext(
            source_type=SourceType.AGENT_GENERATED,
            collection_method=CollectionMethod.AGENT_SYNTHESIS,
            origin="agent://bmad-v1.0"
        )
        assert assign_tier(context) == KnowledgeTier.K4

    def test_assign_k4_simulation(self):
        """Test simulation output → K4 (Story 11-7)."""
        context = TierAssignmentContext(
            source_type=SourceType.SIMULATION,
            collection_method=CollectionMethod.SIMULATION_OUTPUT,
            origin="simulation://monte-carlo-001"
        )
        assert assign_tier(context) == KnowledgeTier.K4

    # Determinism Test
    def test_tier_assignment_determinism(self):
        """Test that same context always produces same tier (AC #1 invariant)."""
        context1 = TierAssignmentContext(
            source_type=SourceType.TELEMETRY,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="sensor://test",
            initial_confidence=0.95
        )
        context2 = TierAssignmentContext(
            source_type=SourceType.TELEMETRY,
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            origin="sensor://test",
            initial_confidence=0.95
        )

        tier1 = assign_tier(context1)
        tier2 = assign_tier(context2)

        assert tier1 == tier2 == KnowledgeTier.K0


class TestTierPromotionRules:
    """Test tier promotion validation (AC #1: Tier transitions)."""

    def test_valid_promotion_k4_to_k3(self):
        """Test valid promotion K4 → K3."""
        assert can_promote(KnowledgeTier.K4, KnowledgeTier.K3) is True

    def test_valid_promotion_k3_to_k2(self):
        """Test valid promotion K3 → K2."""
        assert can_promote(KnowledgeTier.K3, KnowledgeTier.K2) is True

    def test_valid_promotion_k2_to_k1(self):
        """Test valid promotion K2 → K1."""
        assert can_promote(KnowledgeTier.K2, KnowledgeTier.K1) is True

    def test_valid_promotion_k4_to_k1(self):
        """Test valid multi-tier promotion K4 → K1."""
        assert can_promote(KnowledgeTier.K4, KnowledgeTier.K1) is True

    def test_invalid_promotion_to_k0(self):
        """Test promotion to K0 is forbidden (only direct assignment)."""
        assert can_promote(KnowledgeTier.K1, KnowledgeTier.K0) is False
        assert can_promote(KnowledgeTier.K2, KnowledgeTier.K0) is False
        assert can_promote(KnowledgeTier.K4, KnowledgeTier.K0) is False

    def test_invalid_promotion_same_tier(self):
        """Test promotion to same tier is invalid."""
        assert can_promote(KnowledgeTier.K2, KnowledgeTier.K2) is False

    def test_invalid_promotion_wrong_direction(self):
        """Test promotion in wrong direction is invalid."""
        assert can_promote(KnowledgeTier.K1, KnowledgeTier.K2) is False
        assert can_promote(KnowledgeTier.K2, KnowledgeTier.K3) is False


class TestTierDemotionRules:
    """Test tier demotion validation (AC #1: Tier immutability)."""

    def test_valid_demotion_k1_to_k2(self):
        """Test valid demotion K1 → K2."""
        assert can_demote(KnowledgeTier.K1, KnowledgeTier.K2) is True

    def test_valid_demotion_k0_to_k1(self):
        """Test valid demotion K0 → K1."""
        assert can_demote(KnowledgeTier.K0, KnowledgeTier.K1) is True

    def test_valid_demotion_k0_to_k4(self):
        """Test valid multi-tier demotion K0 → K4."""
        assert can_demote(KnowledgeTier.K0, KnowledgeTier.K4) is True

    def test_invalid_demotion_same_tier(self):
        """Test demotion to same tier is invalid."""
        assert can_demote(KnowledgeTier.K3, KnowledgeTier.K3) is False

    def test_invalid_demotion_wrong_direction(self):
        """Test demotion in wrong direction is invalid."""
        assert can_demote(KnowledgeTier.K3, KnowledgeTier.K2) is False
        assert can_demote(KnowledgeTier.K4, KnowledgeTier.K3) is False


class TestValidateTierTransition:
    """Test tier transition validation and enforcement."""

    def test_valid_promotion_authorized(self):
        """Test valid promotion passes validation."""
        # Should not raise
        validate_tier_transition(
            KnowledgeTier.K4,
            KnowledgeTier.K3,
            "Dual-persona arbitration passed",
            authorized=True
        )

    def test_invalid_promotion_to_k0(self):
        """Test promotion to K0 raises error."""
        with pytest.raises(TierTransitionError) as exc_info:
            validate_tier_transition(
                KnowledgeTier.K1,
                KnowledgeTier.K0,
                "Attempting invalid promotion",
                authorized=True
            )
        assert "Cannot promote to K0" in str(exc_info.value)

    def test_valid_demotion_authorized(self):
        """Test valid demotion with authorization passes."""
        # Should not raise
        validate_tier_transition(
            KnowledgeTier.K1,
            KnowledgeTier.K2,
            "Contradiction detected",
            authorized=True
        )

    def test_demotion_without_authorization(self):
        """Test demotion without authorization raises error."""
        with pytest.raises(TierTransitionError) as exc_info:
            validate_tier_transition(
                KnowledgeTier.K1,
                KnowledgeTier.K2,
                "Attempting unauthorized demotion",
                authorized=False
            )
        assert "requires governance authorization" in str(exc_info.value)

    def test_same_tier_no_op(self):
        """Test same tier transition is no-op."""
        # Should not raise
        validate_tier_transition(
            KnowledgeTier.K2,
            KnowledgeTier.K2,
            "No-op transition",
            authorized=False
        )

    def test_transition_error_attributes(self):
        """Test TierTransitionError captures transition details."""
        try:
            validate_tier_transition(
                KnowledgeTier.K2,
                KnowledgeTier.K0,
                "Test error",
                authorized=True
            )
            pytest.fail("Should have raised TierTransitionError")
        except TierTransitionError as e:
            assert e.from_tier == KnowledgeTier.K2
            assert e.to_tier == KnowledgeTier.K0
            assert "Cannot promote to K0" in e.reason
            # Check for tier values in error message
            assert "trust_scored_external" in str(e)
            assert "ground_truth" in str(e)
