"""Unit tests for Knowledge Usage Policy (Story 11-5, Task 5).

Tests usage policy enforcement, constitutional denials, and governance configuration.
Coverage target: ≥90% per AC #5 requirements.
"""

import pytest
from uuid import uuid4

from src.jarvis.knowledge.usage_policy import (
    UsageClass,
    DEFAULT_USAGE_POLICY,
    UsagePolicyViolation,
    PolicyCheckResult,
    KnowledgeUsagePolicy,
    ConstitutionalDenial,
    enforce_usage_policy,
    get_most_restrictive_usage_for_tier,
    validate_policy_configuration,
)
from src.jarvis.knowledge.tiers import KnowledgeTier


class TestUsagePolicyViolation:
    """Test UsagePolicyViolation dataclass."""

    def test_violation_summary(self):
        """Test human-readable violation summary."""
        violation = UsagePolicyViolation(
            knowledge_unit_id=uuid4(),
            tier=KnowledgeTier.K3,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
            allowed_tiers={KnowledgeTier.K0, KnowledgeTier.K1},
            context="Attempted to use narrative for execution",
        )

        summary = violation.violation_summary
        assert "narrative" in summary
        assert "execution_guidance" in summary
        assert "ground_truth" in summary or "verified_derivation" in summary


class TestDefaultUsagePolicy:
    """Test default usage policy configuration."""

    def test_execution_guidance_restrictive(self):
        """Test that execution guidance only allows K0 and K1."""
        allowed = DEFAULT_USAGE_POLICY[UsageClass.EXECUTION_GUIDANCE]
        assert allowed == {KnowledgeTier.K0, KnowledgeTier.K1}

    def test_governance_no_noise(self):
        """Test that governance doesn't allow K4 (noise)."""
        allowed = DEFAULT_USAGE_POLICY[UsageClass.GOVERNANCE]
        assert KnowledgeTier.K4 not in allowed
        assert KnowledgeTier.K0 in allowed
        assert KnowledgeTier.K1 in allowed
        assert KnowledgeTier.K2 in allowed

    def test_strategy_allows_narrative(self):
        """Test that strategy allows K3 (narrative)."""
        allowed = DEFAULT_USAGE_POLICY[UsageClass.STRATEGY]
        assert KnowledgeTier.K3 in allowed

    def test_ideation_allows_all(self):
        """Test that ideation allows all tiers."""
        allowed = DEFAULT_USAGE_POLICY[UsageClass.IDEATION]
        assert len(allowed) == 5
        assert all(tier in allowed for tier in KnowledgeTier)

    def test_policy_monotonicity(self):
        """Test that policy is monotonic (permissive ⊇ restrictive)."""
        exec_tiers = DEFAULT_USAGE_POLICY[UsageClass.EXECUTION_GUIDANCE]
        gov_tiers = DEFAULT_USAGE_POLICY[UsageClass.GOVERNANCE]
        strat_tiers = DEFAULT_USAGE_POLICY[UsageClass.STRATEGY]
        idea_tiers = DEFAULT_USAGE_POLICY[UsageClass.IDEATION]

        # Each level should include all tiers from more restrictive levels
        assert exec_tiers.issubset(gov_tiers)
        assert gov_tiers.issubset(strat_tiers)
        assert strat_tiers.issubset(idea_tiers)


class TestKnowledgeUsagePolicy:
    """Test knowledge usage policy enforcement."""

    @pytest.fixture
    def policy(self):
        """Create policy instance."""
        return KnowledgeUsagePolicy()

    def test_check_usage_allowed(self, policy):
        """Test usage check when tier is allowed (AC #5: Allowed(i, U) ⟺ Tier(i) ∈ U)."""
        ku_id = uuid4()
        result = policy.check_usage(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K0,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
            context="Test execution",
        )

        assert result.allowed is True
        assert result.tier == KnowledgeTier.K0
        assert result.usage_class == UsageClass.EXECUTION_GUIDANCE
        assert result.violation is None

    def test_check_usage_denied(self, policy):
        """Test usage check when tier is not allowed."""
        ku_id = uuid4()
        result = policy.check_usage(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K3,  # Narrative
            usage_class=UsageClass.EXECUTION_GUIDANCE,  # Only allows K0, K1
            context="Attempted narrative execution",
        )

        assert result.allowed is False
        assert result.violation is not None
        assert result.violation.tier == KnowledgeTier.K3
        assert len(policy.violations) == 1

    def test_check_usage_k4_execution_denied(self, policy):
        """Test that K4 (noise) cannot be used for execution."""
        ku_id = uuid4()
        result = policy.check_usage(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K4,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
        )

        assert result.allowed is False
        assert result.violation.tier == KnowledgeTier.K4

    def test_check_usage_k3_governance_denied(self, policy):
        """Test that K3 (narrative) cannot be used for governance."""
        ku_id = uuid4()
        result = policy.check_usage(
            knowledge_unit_id=ku_id,
            tier=KnowledgeTier.K3,
            usage_class=UsageClass.GOVERNANCE,
        )

        assert result.allowed is False

    def test_check_usage_batch(self, policy):
        """Test batch usage checking."""
        knowledge_units = [
            (uuid4(), KnowledgeTier.K0),
            (uuid4(), KnowledgeTier.K1),
            (uuid4(), KnowledgeTier.K3),  # This should fail
        ]

        results = policy.check_usage_batch(
            knowledge_units=knowledge_units,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
        )

        assert len(results) == 3
        assert results[0].allowed is True
        assert results[1].allowed is True
        assert results[2].allowed is False

    def test_filter_allowed_knowledge(self, policy):
        """Test filtering knowledge units by policy."""
        knowledge_units = [
            (uuid4(), KnowledgeTier.K0),
            (uuid4(), KnowledgeTier.K1),
            (uuid4(), KnowledgeTier.K3),  # Should be filtered out
            (uuid4(), KnowledgeTier.K4),  # Should be filtered out
        ]

        allowed_ids = policy.filter_allowed_knowledge(
            knowledge_units=knowledge_units,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
        )

        assert len(allowed_ids) == 2  # Only K0 and K1

    def test_get_allowed_tiers(self, policy):
        """Test getting allowed tiers for usage class."""
        exec_tiers = policy.get_allowed_tiers(UsageClass.EXECUTION_GUIDANCE)
        assert exec_tiers == {KnowledgeTier.K0, KnowledgeTier.K1}

        gov_tiers = policy.get_allowed_tiers(UsageClass.GOVERNANCE)
        assert KnowledgeTier.K2 in gov_tiers

    def test_update_policy_valid(self, policy):
        """Test updating policy with valid configuration."""
        # Allow K2 for execution guidance
        policy.update_policy(
            usage_class=UsageClass.EXECUTION_GUIDANCE,
            allowed_tiers={KnowledgeTier.K0, KnowledgeTier.K1, KnowledgeTier.K2},
            authorized_by="admin",
        )

        allowed = policy.get_allowed_tiers(UsageClass.EXECUTION_GUIDANCE)
        assert KnowledgeTier.K2 in allowed

    def test_update_policy_invalid_execution(self, policy):
        """Test that execution guidance cannot allow K3+ (security constraint)."""
        with pytest.raises(ValueError, match="cannot allow tiers beyond K2"):
            policy.update_policy(
                usage_class=UsageClass.EXECUTION_GUIDANCE,
                allowed_tiers={KnowledgeTier.K0, KnowledgeTier.K1, KnowledgeTier.K3},
                authorized_by="admin",
            )

    def test_update_policy_invalid_governance(self, policy):
        """Test that governance cannot allow K4 (security constraint)."""
        with pytest.raises(ValueError, match="cannot allow K4"):
            policy.update_policy(
                usage_class=UsageClass.GOVERNANCE,
                allowed_tiers={KnowledgeTier.K0, KnowledgeTier.K1, KnowledgeTier.K4},
                authorized_by="admin",
            )

    def test_get_violations_unfiltered(self, policy):
        """Test getting all violations."""
        # Generate some violations
        policy.check_usage(uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE)
        policy.check_usage(uuid4(), KnowledgeTier.K4, UsageClass.EXECUTION_GUIDANCE)

        violations = policy.get_violations()
        assert len(violations) == 2

    def test_get_violations_filtered_by_usage(self, policy):
        """Test getting violations filtered by usage class."""
        policy.check_usage(uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE)
        policy.check_usage(uuid4(), KnowledgeTier.K4, UsageClass.GOVERNANCE)

        exec_violations = policy.get_violations(usage_class=UsageClass.EXECUTION_GUIDANCE)
        assert len(exec_violations) == 1
        assert exec_violations[0].tier == KnowledgeTier.K3

    def test_get_violations_filtered_by_tier(self, policy):
        """Test getting violations filtered by tier."""
        policy.check_usage(uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE)
        policy.check_usage(uuid4(), KnowledgeTier.K4, UsageClass.EXECUTION_GUIDANCE)

        k3_violations = policy.get_violations(tier=KnowledgeTier.K3)
        assert len(k3_violations) == 1
        assert k3_violations[0].tier == KnowledgeTier.K3

    def test_clear_violations(self, policy):
        """Test clearing violation history."""
        policy.check_usage(uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE)
        policy.check_usage(uuid4(), KnowledgeTier.K4, UsageClass.EXECUTION_GUIDANCE)

        count = policy.clear_violations()
        assert count == 2
        assert len(policy.violations) == 0

    def test_get_usage_statistics(self, policy):
        """Test getting violation statistics."""
        # Generate violations
        policy.check_usage(uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE)
        policy.check_usage(uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE)
        policy.check_usage(uuid4(), KnowledgeTier.K4, UsageClass.GOVERNANCE)

        stats = policy.get_usage_statistics()
        assert stats["total_violations"] == 3
        assert stats["by_usage_class"]["execution_guidance"] == 2
        assert stats["by_usage_class"]["governance"] == 1
        assert stats["by_tier"]["narrative"] == 2
        assert stats["by_tier"]["noise"] == 1

    def test_get_usage_statistics_empty(self, policy):
        """Test statistics when no violations."""
        stats = policy.get_usage_statistics()
        assert stats["total_violations"] == 0
        assert stats["by_usage_class"] == {}
        assert stats["by_tier"] == {}


class TestConstitutionalDenial:
    """Test constitutional denial exception."""

    def test_strict_mode_raises_exception(self):
        """Test that strict mode raises ConstitutionalDenial on violation."""
        policy = KnowledgeUsagePolicy(enable_strict_mode=True)

        with pytest.raises(ConstitutionalDenial) as exc_info:
            result = policy.check_usage(
                knowledge_unit_id=uuid4(),
                tier=KnowledgeTier.K3,
                usage_class=UsageClass.EXECUTION_GUIDANCE,
            )

            # Manually check and raise if violation (simulating enforcement)
            if not result.allowed:
                raise ConstitutionalDenial(result.violation)

        assert "narrative" in str(exc_info.value)

    def test_non_strict_mode_no_exception(self):
        """Test that non-strict mode doesn't raise exception."""
        policy = KnowledgeUsagePolicy(enable_strict_mode=False)

        result = policy.check_usage(
            knowledge_unit_id=uuid4(),
            tier=KnowledgeTier.K3,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
        )

        # Should not raise, just return denial
        assert result.allowed is False


class TestEnforceUsagePolicy:
    """Test enforce_usage_policy helper function."""

    def test_enforce_with_default_policy(self):
        """Test enforcement with default policy."""
        result = enforce_usage_policy(
            knowledge_unit_id=uuid4(),
            tier=KnowledgeTier.K0,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
            policy=None,  # Use default
        )

        assert result.allowed is True

    def test_enforce_raises_on_violation(self):
        """Test that enforcement raises exception on violation."""
        with pytest.raises(ConstitutionalDenial):
            enforce_usage_policy(
                knowledge_unit_id=uuid4(),
                tier=KnowledgeTier.K3,
                usage_class=UsageClass.EXECUTION_GUIDANCE,
                policy=None,
            )

    def test_enforce_with_custom_policy(self):
        """Test enforcement with custom policy."""
        custom_policy = KnowledgeUsagePolicy(enable_strict_mode=False)

        result = enforce_usage_policy(
            knowledge_unit_id=uuid4(),
            tier=KnowledgeTier.K3,
            usage_class=UsageClass.EXECUTION_GUIDANCE,
            policy=custom_policy,
        )

        # Should not raise with strict mode disabled
        assert result.allowed is False


class TestGetMostRestrictiveUsage:
    """Test most restrictive usage determination."""

    def test_k0_allows_execution(self):
        """Test that K0 can be used for execution."""
        usage = get_most_restrictive_usage_for_tier(KnowledgeTier.K0)
        assert usage == UsageClass.EXECUTION_GUIDANCE

    def test_k1_allows_execution(self):
        """Test that K1 can be used for execution."""
        usage = get_most_restrictive_usage_for_tier(KnowledgeTier.K1)
        assert usage == UsageClass.EXECUTION_GUIDANCE

    def test_k2_allows_governance(self):
        """Test that K2 requires governance or less restrictive."""
        usage = get_most_restrictive_usage_for_tier(KnowledgeTier.K2)
        assert usage == UsageClass.GOVERNANCE

    def test_k3_allows_strategy(self):
        """Test that K3 (narrative) requires strategy or less restrictive."""
        usage = get_most_restrictive_usage_for_tier(KnowledgeTier.K3)
        assert usage == UsageClass.STRATEGY

    def test_k4_allows_ideation_only(self):
        """Test that K4 (noise) only allowed for ideation."""
        usage = get_most_restrictive_usage_for_tier(KnowledgeTier.K4)
        assert usage == UsageClass.IDEATION


class TestValidatePolicyConfiguration:
    """Test policy configuration validation."""

    def test_valid_policy(self):
        """Test validation of valid policy."""
        is_valid, errors = validate_policy_configuration(DEFAULT_USAGE_POLICY)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_execution_allows_k3(self):
        """Test that execution allowing K3 is invalid."""
        invalid_policy = DEFAULT_USAGE_POLICY.copy()
        invalid_policy[UsageClass.EXECUTION_GUIDANCE] = {
            KnowledgeTier.K0,
            KnowledgeTier.K1,
            KnowledgeTier.K3,
        }

        is_valid, errors = validate_policy_configuration(invalid_policy)
        assert is_valid is False
        assert any("EXECUTION_GUIDANCE" in err and "K2" in err for err in errors)

    def test_invalid_governance_allows_k4(self):
        """Test that governance allowing K4 is invalid."""
        invalid_policy = DEFAULT_USAGE_POLICY.copy()
        invalid_policy[UsageClass.GOVERNANCE] = {
            KnowledgeTier.K0,
            KnowledgeTier.K1,
            KnowledgeTier.K4,
        }

        is_valid, errors = validate_policy_configuration(invalid_policy)
        assert is_valid is False
        assert any("GOVERNANCE" in err and "K4" in err for err in errors)

    def test_invalid_monotonicity_violation(self):
        """Test detection of monotonicity violation."""
        invalid_policy = DEFAULT_USAGE_POLICY.copy()
        # Make governance less permissive than execution (violation)
        invalid_policy[UsageClass.GOVERNANCE] = {KnowledgeTier.K0}
        invalid_policy[UsageClass.EXECUTION_GUIDANCE] = {
            KnowledgeTier.K0,
            KnowledgeTier.K1,
        }

        is_valid, errors = validate_policy_configuration(invalid_policy)
        assert is_valid is False
        assert any("monotonicity" in err.lower() for err in errors)

    def test_missing_usage_class(self):
        """Test detection of missing usage class."""
        incomplete_policy = DEFAULT_USAGE_POLICY.copy()
        del incomplete_policy[UsageClass.EXECUTION_GUIDANCE]

        is_valid, errors = validate_policy_configuration(incomplete_policy)
        assert is_valid is False
        assert any("Missing policy" in err for err in errors)


class TestFormalRule:
    """Test formal rule: Allowed(i, U) ⟺ Tier(i) ∈ U."""

    def test_formal_rule_k0_execution(self):
        """Test: K0 ∈ U_execution ⟹ Allowed."""
        policy = KnowledgeUsagePolicy()
        result = policy.check_usage(
            uuid4(), KnowledgeTier.K0, UsageClass.EXECUTION_GUIDANCE
        )
        assert result.allowed is True

    def test_formal_rule_k3_execution(self):
        """Test: K3 ∉ U_execution ⟹ ¬Allowed."""
        policy = KnowledgeUsagePolicy()
        result = policy.check_usage(
            uuid4(), KnowledgeTier.K3, UsageClass.EXECUTION_GUIDANCE
        )
        assert result.allowed is False

    def test_formal_rule_k2_governance(self):
        """Test: K2 ∈ U_governance ⟹ Allowed."""
        policy = KnowledgeUsagePolicy()
        result = policy.check_usage(
            uuid4(), KnowledgeTier.K2, UsageClass.GOVERNANCE
        )
        assert result.allowed is True

    def test_formal_rule_k4_governance(self):
        """Test: K4 ∉ U_governance ⟹ ¬Allowed."""
        policy = KnowledgeUsagePolicy()
        result = policy.check_usage(
            uuid4(), KnowledgeTier.K4, UsageClass.GOVERNANCE
        )
        assert result.allowed is False

    def test_formal_rule_all_tiers_ideation(self):
        """Test: ∀ tier ∈ {K0..K4}, tier ∈ U_ideation ⟹ Allowed."""
        policy = KnowledgeUsagePolicy()

        for tier in KnowledgeTier:
            result = policy.check_usage(
                uuid4(), tier, UsageClass.IDEATION
            )
            assert result.allowed is True, f"{tier} should be allowed for ideation"
