"""Unit tests for Trust Engine (Story 11-5, Task 4).

Tests trust decay dynamics, refresh mechanisms, and contradiction penalties.
Coverage target: ≥90% per AC #4 requirements.
"""

import math
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.jarvis.knowledge.trust_engine import (
    DECAY_RATES,
    MIN_CONTRADICTION_PENALTY,
    MAX_CONTRADICTION_PENALTY,
    MIN_TRUST_THRESHOLD,
    TrustState,
    calculate_trust,
    calculate_trust_with_refresh,
    refresh_trust,
    apply_contradiction_penalty,
    should_archive,
    calculate_half_life,
    calculate_time_to_threshold,
    get_trust_cap_for_tier,
    enforce_trust_cap,
)
from src.jarvis.knowledge.tiers import KnowledgeTier


class TestTrustState:
    """Test TrustState validation."""

    def test_valid_trust_state(self):
        """Test valid trust state creation."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.85,
            initial_confidence=0.9,
            ingestion_time=datetime(2025, 1, 1, 0, 0, 0),
            last_refresh_time=datetime(2025, 1, 1, 0, 0, 0),
            tier=KnowledgeTier.K2,
            is_frozen=False,
            contradiction_count=0,
        )

        assert state.current_trust == 0.85
        assert state.initial_confidence == 0.9
        assert state.tier == KnowledgeTier.K2

    def test_invalid_current_trust_high(self):
        """Test that current_trust > 1.0 is rejected."""
        with pytest.raises(ValueError, match="current_trust must be in"):
            TrustState(
                knowledge_unit_id=uuid4(),
                current_trust=1.5,
                initial_confidence=0.9,
                ingestion_time=datetime.now(),
                last_refresh_time=datetime.now(),
                tier=KnowledgeTier.K2,
            )

    def test_invalid_current_trust_low(self):
        """Test that current_trust < 0.0 is rejected."""
        with pytest.raises(ValueError, match="current_trust must be in"):
            TrustState(
                knowledge_unit_id=uuid4(),
                current_trust=-0.1,
                initial_confidence=0.9,
                ingestion_time=datetime.now(),
                last_refresh_time=datetime.now(),
                tier=KnowledgeTier.K2,
            )

    def test_invalid_initial_confidence(self):
        """Test that invalid initial_confidence is rejected."""
        with pytest.raises(ValueError, match="initial_confidence must be in"):
            TrustState(
                knowledge_unit_id=uuid4(),
                current_trust=0.9,
                initial_confidence=1.5,
                ingestion_time=datetime.now(),
                last_refresh_time=datetime.now(),
                tier=KnowledgeTier.K2,
            )


class TestCalculateTrust:
    """Test trust calculation with exponential decay."""

    def test_k0_no_decay(self):
        """Test K0 (ground truth) has no decay (λ=0)."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 12, 31, 23, 59, 59)  # 1 year later

        trust = calculate_trust(
            initial_confidence=1.0,
            tier=KnowledgeTier.K0,
            ingestion_time=t0,
            current_time=t1,
        )

        # K0 should never decay
        assert trust == 1.0

    def test_k4_fast_decay(self):
        """Test K4 (noise) has fast decay (λ=10⁻²)."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 1, 1, 2, 0, 0)  # 2 hours later

        trust = calculate_trust(
            initial_confidence=1.0,
            tier=KnowledgeTier.K4,
            ingestion_time=t0,
            current_time=t1,
        )

        # After 2 hours with λ=10⁻² (7200 seconds)
        # T = 1.0 * e^(-0.01 * 7200) = e^(-72) ≈ 0 (very small)
        assert trust < 0.01

    def test_decay_formula_k2(self):
        """Test exact decay formula for K2 tier."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 1, 2, 0, 0, 0)  # 1 day = 86400 seconds

        trust = calculate_trust(
            initial_confidence=0.9,
            tier=KnowledgeTier.K2,
            ingestion_time=t0,
            current_time=t1,
        )

        # Expected: T = 0.9 * e^(-10⁻⁵ * 86400)
        lambda_k2 = DECAY_RATES[KnowledgeTier.K2]
        time_delta = 86400
        expected = 0.9 * math.exp(-lambda_k2 * time_delta)

        assert abs(trust - expected) < 1e-6

    def test_no_time_elapsed(self):
        """Test trust at t=t₀ equals initial confidence."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)

        trust = calculate_trust(
            initial_confidence=0.85,
            tier=KnowledgeTier.K3,
            ingestion_time=t0,
            current_time=t0,
        )

        assert trust == 0.85

    def test_invalid_confidence_bounds(self):
        """Test that invalid confidence is rejected."""
        t0 = datetime.now()
        t1 = t0 + timedelta(hours=1)

        with pytest.raises(ValueError, match="initial_confidence must be in"):
            calculate_trust(
                initial_confidence=1.5,
                tier=KnowledgeTier.K2,
                ingestion_time=t0,
                current_time=t1,
            )

    def test_invalid_time_order(self):
        """Test that current_time < ingestion_time is rejected."""
        t0 = datetime(2025, 1, 2, 0, 0, 0)
        t1 = datetime(2025, 1, 1, 0, 0, 0)  # Before t0

        with pytest.raises(ValueError, match="cannot be before ingestion_time"):
            calculate_trust(
                initial_confidence=0.9,
                tier=KnowledgeTier.K2,
                ingestion_time=t0,
                current_time=t1,
            )

    def test_clamping_to_zero(self):
        """Test that trust is clamped to [0, 1] bounds."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 12, 31, 23, 59, 59)  # Very long time

        trust = calculate_trust(
            initial_confidence=1.0,
            tier=KnowledgeTier.K4,  # Fast decay
            ingestion_time=t0,
            current_time=t1,
        )

        # Should be clamped to 0
        assert 0.0 <= trust <= 1.0


class TestCalculateTrustWithRefresh:
    """Test trust calculation with refresh events."""

    def test_refresh_resets_decay(self):
        """Test that refresh effectively resets decay clock."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t_refresh = datetime(2025, 1, 5, 0, 0, 0)  # 4 days later
        t_current = datetime(2025, 1, 6, 0, 0, 0)  # 5 days from t0, 1 day from refresh

        # Trust should be calculated from t_refresh, not t0
        trust = calculate_trust_with_refresh(
            initial_confidence=0.9,
            tier=KnowledgeTier.K2,
            ingestion_time=t0,
            last_refresh_time=t_refresh,
            current_time=t_current,
        )

        # Expected: decay from t_refresh (1 day)
        lambda_k2 = DECAY_RATES[KnowledgeTier.K2]
        time_delta = (t_current - t_refresh).total_seconds()
        expected = 0.9 * math.exp(-lambda_k2 * time_delta)

        assert abs(trust - expected) < 1e-6

    def test_no_refresh_equals_normal_decay(self):
        """Test that with no refresh, equals normal calculate_trust."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 1, 2, 0, 0, 0)

        trust_normal = calculate_trust(
            initial_confidence=0.8,
            tier=KnowledgeTier.K3,
            ingestion_time=t0,
            current_time=t1,
        )

        trust_with_refresh = calculate_trust_with_refresh(
            initial_confidence=0.8,
            tier=KnowledgeTier.K3,
            ingestion_time=t0,
            last_refresh_time=t0,  # Same as ingestion
            current_time=t1,
        )

        assert abs(trust_normal - trust_with_refresh) < 1e-9


class TestRefreshTrust:
    """Test trust refresh mechanism."""

    def test_refresh_updates_time(self):
        """Test that refresh updates last_refresh_time."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t_refresh = datetime(2025, 1, 5, 0, 0, 0)

        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=t0,
            last_refresh_time=t0,
            tier=KnowledgeTier.K2,
        )

        refreshed = refresh_trust(state, t_refresh)

        assert refreshed.last_refresh_time == t_refresh
        assert refreshed.knowledge_unit_id == state.knowledge_unit_id
        assert refreshed.initial_confidence == state.initial_confidence

    def test_refresh_calculates_current_trust(self):
        """Test that refresh calculates trust at refresh time."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t_refresh = datetime(2025, 1, 2, 0, 0, 0)  # 1 day later

        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.9,  # Initial
            initial_confidence=0.9,
            ingestion_time=t0,
            last_refresh_time=t0,
            tier=KnowledgeTier.K2,
        )

        refreshed = refresh_trust(state, t_refresh)

        # Trust should be calculated at t_refresh
        expected_trust = calculate_trust(
            initial_confidence=0.9,
            tier=KnowledgeTier.K2,
            ingestion_time=t0,
            current_time=t_refresh,
        )

        assert abs(refreshed.current_trust - expected_trust) < 1e-6

    def test_refresh_invalid_time_order(self):
        """Test that refresh time < last_refresh_time is rejected."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t_refresh = datetime(2025, 1, 5, 0, 0, 0)
        t_invalid = datetime(2025, 1, 3, 0, 0, 0)  # Before last refresh

        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=t0,
            last_refresh_time=t_refresh,
            tier=KnowledgeTier.K2,
        )

        with pytest.raises(ValueError, match="cannot be before last_refresh_time"):
            refresh_trust(state, t_invalid)


class TestApplyContradictionPenalty:
    """Test contradiction penalty logic."""

    def test_penalty_reduces_trust(self):
        """Test that penalty reduces trust by factor α."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K2,
        )

        penalty_factor = 0.5
        penalized = apply_contradiction_penalty(state, penalty_factor)

        expected_trust = 0.8 * 0.5
        assert abs(penalized.current_trust - expected_trust) < 1e-6
        assert penalized.contradiction_count == 1

    def test_penalty_invalid_factor(self):
        """Test that invalid penalty factor is rejected."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K2,
        )

        with pytest.raises(ValueError, match="penalty_factor must be in"):
            apply_contradiction_penalty(state, 0.05)  # Too low

        with pytest.raises(ValueError, match="penalty_factor must be in"):
            apply_contradiction_penalty(state, 0.8)  # Too high

    def test_same_tier_contradiction_freezes(self):
        """Test that same-tier contradiction freezes both units."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K2,
        )

        penalized = apply_contradiction_penalty(
            state,
            penalty_factor=0.3,
            contradicting_tier=KnowledgeTier.K2,  # Same tier
        )

        assert penalized.is_frozen is True

    def test_higher_tier_no_penalty(self):
        """Test that lower tier cannot contradict higher tier."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K1,  # High tier
        )

        penalized = apply_contradiction_penalty(
            state,
            penalty_factor=0.3,
            contradicting_tier=KnowledgeTier.K3,  # Lower tier
        )

        # No penalty should be applied
        assert penalized.current_trust == 0.8
        assert penalized.contradiction_count == 0

    def test_lower_tier_applies_penalty(self):
        """Test that higher tier can contradict lower tier."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.8,
            initial_confidence=0.9,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K3,  # Lower tier
        )

        penalized = apply_contradiction_penalty(
            state,
            penalty_factor=0.4,
            contradicting_tier=KnowledgeTier.K1,  # Higher tier
        )

        # Penalty should be applied
        expected_trust = 0.8 * 0.4
        assert abs(penalized.current_trust - expected_trust) < 1e-6
        assert penalized.contradiction_count == 1


class TestShouldArchive:
    """Test archival threshold logic."""

    def test_archive_when_below_threshold(self):
        """Test that knowledge is archived when trust < threshold."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 12, 31, 23, 59, 59)  # Long time

        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.02,  # Will decay below threshold
            initial_confidence=0.02,
            ingestion_time=t0,
            last_refresh_time=t0,
            tier=KnowledgeTier.K4,  # Fast decay
        )

        assert should_archive(state, t1) is True

    def test_no_archive_when_above_threshold(self):
        """Test that knowledge is not archived when trust > threshold."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2025, 1, 1, 1, 0, 0)  # 1 hour

        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.9,
            initial_confidence=0.9,
            ingestion_time=t0,
            last_refresh_time=t0,
            tier=KnowledgeTier.K2,  # Slow decay
        )

        assert should_archive(state, t1) is False

    def test_k0_never_archived(self):
        """Test that K0 (ground truth) is never archived due to no decay."""
        t0 = datetime(2025, 1, 1, 0, 0, 0)
        t1 = datetime(2030, 1, 1, 0, 0, 0)  # 5 years

        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=1.0,
            initial_confidence=1.0,
            ingestion_time=t0,
            last_refresh_time=t0,
            tier=KnowledgeTier.K0,  # No decay
        )

        assert should_archive(state, t1) is False


class TestCalculateHalfLife:
    """Test half-life calculations."""

    def test_k0_infinite_half_life(self):
        """Test that K0 has infinite half-life (no decay)."""
        half_life = calculate_half_life(KnowledgeTier.K0)
        assert half_life is None

    def test_k1_half_life(self):
        """Test K1 half-life calculation."""
        half_life = calculate_half_life(KnowledgeTier.K1)
        assert half_life is not None

        # Expected: t₁/₂ = ln(2) / 10⁻⁶ ≈ 693147 seconds ≈ 8 days
        expected_seconds = math.log(2) / DECAY_RATES[KnowledgeTier.K1]
        assert abs(half_life.total_seconds() - expected_seconds) < 1e-3

    def test_k4_short_half_life(self):
        """Test K4 has short half-life (fast decay)."""
        half_life = calculate_half_life(KnowledgeTier.K4)
        assert half_life is not None

        # Expected: t₁/₂ = ln(2) / 10⁻² ≈ 69 seconds ≈ 1 minute
        expected_seconds = math.log(2) / DECAY_RATES[KnowledgeTier.K4]
        assert abs(half_life.total_seconds() - expected_seconds) < 1e-3
        assert half_life.total_seconds() < 120  # Less than 2 minutes


class TestCalculateTimeToThreshold:
    """Test time-to-threshold calculations."""

    def test_k0_no_threshold_time(self):
        """Test that K0 never reaches threshold (no decay)."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=1.0,
            initial_confidence=1.0,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K0,
        )

        time_to_threshold = calculate_time_to_threshold(state, threshold=0.5)
        assert time_to_threshold is None

    def test_time_to_threshold_k2(self):
        """Test threshold time calculation for K2."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=1.0,
            initial_confidence=1.0,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K2,
        )

        threshold = 0.5
        time_to_threshold = calculate_time_to_threshold(state, threshold)
        assert time_to_threshold is not None

        # Expected: t = -ln(0.5 / 1.0) / 10⁻⁵ = ln(2) / 10⁻⁵
        expected_seconds = -math.log(threshold / 1.0) / DECAY_RATES[KnowledgeTier.K2]
        assert abs(time_to_threshold.total_seconds() - expected_seconds) < 1e-3

    def test_threshold_unreachable(self):
        """Test that threshold higher than initial confidence is unreachable."""
        state = TrustState(
            knowledge_unit_id=uuid4(),
            current_trust=0.5,
            initial_confidence=0.5,
            ingestion_time=datetime.now(),
            last_refresh_time=datetime.now(),
            tier=KnowledgeTier.K2,
        )

        time_to_threshold = calculate_time_to_threshold(state, threshold=0.8)
        assert time_to_threshold is None


class TestTrustCaps:
    """Test tier-specific trust caps."""

    def test_k0_k1_no_cap(self):
        """Test that K0 and K1 have full trust cap (1.0)."""
        assert get_trust_cap_for_tier(KnowledgeTier.K0) == 1.0
        assert get_trust_cap_for_tier(KnowledgeTier.K1) == 1.0

    def test_k2_high_cap(self):
        """Test that K2 has high cap (0.95)."""
        assert get_trust_cap_for_tier(KnowledgeTier.K2) == 0.95

    def test_k3_moderate_cap(self):
        """Test that K3 (narrative) has moderate cap (0.75)."""
        assert get_trust_cap_for_tier(KnowledgeTier.K3) == 0.75

    def test_k4_low_cap(self):
        """Test that K4 (noise) has low cap (0.5)."""
        assert get_trust_cap_for_tier(KnowledgeTier.K4) == 0.5

    def test_enforce_cap_below_limit(self):
        """Test that trust below cap is not modified."""
        trust = enforce_trust_cap(0.6, KnowledgeTier.K3)
        assert trust == 0.6

    def test_enforce_cap_above_limit(self):
        """Test that trust above cap is capped."""
        trust = enforce_trust_cap(0.9, KnowledgeTier.K3)
        assert trust == 0.75  # K3 cap

    def test_enforce_cap_k4(self):
        """Test cap enforcement for K4 (noise)."""
        trust = enforce_trust_cap(0.8, KnowledgeTier.K4)
        assert trust == 0.5  # K4 cap
