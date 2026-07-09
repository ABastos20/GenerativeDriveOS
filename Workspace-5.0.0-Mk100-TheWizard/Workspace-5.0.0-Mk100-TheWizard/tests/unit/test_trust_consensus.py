"""Verification Tests for Story 9-3: Trust-Weighted Consensus.

Verifies:
1. Trust Formula Correctness
2. Safety Constraints (Sybil, Elite Cap, Minority Floor)
3. Voting Integration
"""
import pytest
from unittest.mock import MagicMock
from jarvis.governance.models import TrustScore, Constitution
from jarvis.governance.trust import TrustCalculator

class TestTrustCalculator:
    
    @pytest.fixture
    def mock_constitution(self):
        """Standard constitution for testing default behavior."""
        c = MagicMock(spec=Constitution)
        c.weight_epistemic = 0.4
        c.weight_consistency = 0.3
        c.weight_integrity = 0.2
        c.weight_reputation = 0.1
        c.sybil_threshold = 0.2
        c.minority_floor = 0.05
        c.anti_elite_multiplier = 5.0
        return c

    def test_raw_trust_calculation_perfect(self, mock_constitution):
        """Verify T = 1.0 for perfect score."""
        class MockScore:
            def __init__(self, e, c, h, r):
                self.epistemic_reliability = e
                self.governance_consistency = c
                self.historical_integrity = h
                self.reputation = r
                
        ts = MockScore(1.0, 1.0, 1.0, 1.0)
        val = TrustCalculator.calculate_raw_trust(ts, mock_constitution)
        assert val == pytest.approx(1.0), f"Expected 1.0, got {val}"
        
    def test_raw_trust_calculation_mixed(self, mock_constitution):
        """Verify T = 0.4 for mixed score."""
        class MockScore:
            def __init__(self, e, c, h, r):
                self.epistemic_reliability = e
                self.governance_consistency = c
                self.historical_integrity = h
                self.reputation = r

        ts2 = MockScore(0.5, 0.0, 1.0, 0.0)
        val = TrustCalculator.calculate_raw_trust(ts2, mock_constitution)
        assert val == 0.4, f"Expected 0.4, got {val}"
        
    def test_sybil_resistance(self, mock_constitution):
        """Verify Sybil Resistance (Quadratic Penalty for T < Tau)."""
        tau = 0.2
        
        # Case 1: T > Tau (Linear)
        t_high = 0.5
        w_high = TrustCalculator.calculate_effective_weight(t_high, [0.5], mock_constitution, apply_constraints=True)
        # Should be linear (subject to min floor/cap, but here median=0.5 -> cap=2.5)
        # 0.5 is > floor(0.05).
        assert w_high == 0.5
        
        # Case 2: T < Tau (Quadratic Penalty)
        # Formula: w = t^2 / tau
        # t=0.15, tau=0.2 -> 0.1125
        
        t_test = 0.15
        w_low = TrustCalculator.calculate_effective_weight(t_test, [0.5], mock_constitution, apply_constraints=True)
        
        # Expected: 0.15^2 / 0.2 = 0.1125
        assert pytest.approx(w_low) == 0.1125
        
        # Verify it IS penalized vs linear
        assert w_low < t_test # 0.1125 < 0.15
        
    def test_minority_floor(self, mock_constitution):
        """Verify epsilon floor protects silenced voices."""
        t_zero = 0.0
        w = TrustCalculator.calculate_effective_weight(t_zero, [0.5], mock_constitution, apply_constraints=True)
        assert w == 0.05 # MINORITY_FLOOR in mock
        
    def test_anti_elite_cap(self, mock_constitution):
        """Verify 5x Median Cap."""
        # Population: Median = 0.1
        # Cap = 0.5
        population = [0.1, 0.1, 0.1] # Median 0.1
        
        user_trust = 1.0 # Super user
        w = TrustCalculator.calculate_effective_weight(user_trust, population, mock_constitution, apply_constraints=True)
        
        # Should be capped at 0.5
        assert w == 0.5
        assert w < user_trust

    def test_anti_elite_soft_failover(self, mock_constitution):
        """Verify constraints when median is tiny."""
        # Population of newbs (Median < epsilon)
        population = [0.01, 0.01, 0.01] # Median 0.01
        
        # Logic says: if median < FLOOR (0.05), use FLOOR as base for cap.
        # Cap = max(median, FLOOR) * 5 = 0.05 * 5 = 0.25
        
        user_trust = 1.0
        w = TrustCalculator.calculate_effective_weight(user_trust, population, mock_constitution, apply_constraints=True)
        
        assert w == 0.25 # 5x0.05
