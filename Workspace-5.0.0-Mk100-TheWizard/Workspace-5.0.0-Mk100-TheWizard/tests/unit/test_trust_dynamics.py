"""Unit tests for Story 9-3 AC 8-10: Trust Dynamics Update.

Tests:
- TrustUpdater.update_on_outcome (aligned/dissent/abuse)
- TrustUpdater.apply_inactivity_decay
- TrustUpdater.recenter_to_mean
"""
import pytest
from unittest.mock import MagicMock

from jarvis.governance.trust import TrustUpdater


class TestTrustDynamicsUpdate:
    """Tests for AC 8: Trust Update Equation."""
    
    @pytest.fixture
    def mock_trust_score(self):
        """Create mock TrustScore with default governance_consistency."""
        score = MagicMock()
        score.governance_consistency = 0.5
        return score
    
    def test_update_on_outcome_aligned(self, mock_trust_score):
        """Test +0.01 reward for voting with consensus."""
        new_value = TrustUpdater.update_on_outcome(
            trust_score=mock_trust_score,
            vote_aligned_with_outcome=True,
            process_abuse=False
        )
        
        assert new_value == pytest.approx(0.51)
        assert mock_trust_score.governance_consistency == pytest.approx(0.51)
    
    def test_update_on_outcome_dissent(self, mock_trust_score):
        """Test -0.01 penalty for voting against consensus."""
        new_value = TrustUpdater.update_on_outcome(
            trust_score=mock_trust_score,
            vote_aligned_with_outcome=False,
            process_abuse=False
        )
        
        assert new_value == pytest.approx(0.49)
        assert mock_trust_score.governance_consistency == pytest.approx(0.49)
    
    def test_update_on_outcome_process_abuse(self, mock_trust_score):
        """Test -0.05 penalty for process abuse (overrides alignment)."""
        new_value = TrustUpdater.update_on_outcome(
            trust_score=mock_trust_score,
            vote_aligned_with_outcome=True,  # Would be +0.01 normally
            process_abuse=True  # But abuse overrides
        )
        
        assert new_value == pytest.approx(0.45)
        assert mock_trust_score.governance_consistency == pytest.approx(0.45)
    
    def test_update_clamped_at_max(self):
        """Test that trust score is clamped at 1.0."""
        score = MagicMock()
        score.governance_consistency = 0.99
        
        new_value = TrustUpdater.update_on_outcome(
            trust_score=score,
            vote_aligned_with_outcome=True,
            process_abuse=False
        )
        
        assert new_value == 1.0
    
    def test_update_clamped_at_min(self):
        """Test that trust score is clamped at 0.0."""
        score = MagicMock()
        score.governance_consistency = 0.01
        
        new_value = TrustUpdater.update_on_outcome(
            trust_score=score,
            vote_aligned_with_outcome=True,
            process_abuse=True  # -0.05
        )
        
        assert new_value == 0.0


class TestInactivityDecay:
    """Tests for AC 9: Drift/decay for inactivity."""
    
    @pytest.fixture
    def mock_trust_score(self):
        score = MagicMock()
        score.governance_consistency = 0.6
        return score
    
    def test_single_epoch_decay(self, mock_trust_score):
        """Test -0.01 decay for 1 epoch."""
        new_value = TrustUpdater.apply_inactivity_decay(
            trust_score=mock_trust_score,
            epochs_inactive=1
        )
        
        assert new_value == pytest.approx(0.59)
    
    def test_multiple_epoch_decay(self, mock_trust_score):
        """Test cumulative decay for multiple epochs."""
        new_value = TrustUpdater.apply_inactivity_decay(
            trust_score=mock_trust_score,
            epochs_inactive=5
        )
        
        assert new_value == pytest.approx(0.55)
    
    def test_decay_clamped_at_zero(self):
        """Test decay doesn't go below 0."""
        score = MagicMock()
        score.governance_consistency = 0.02
        
        new_value = TrustUpdater.apply_inactivity_decay(
            trust_score=score,
            epochs_inactive=10
        )
        
        assert new_value == 0.0


class TestRecenterToMean:
    """Tests for AC 9: Periodic re-centering."""
    
    def test_recenter_above_mean(self):
        """Test high trust moves toward mean."""
        score = MagicMock()
        score.governance_consistency = 0.9
        
        # 10% toward 0.5: 0.9 + 0.1*(0.5-0.9) = 0.9 - 0.04 = 0.86
        new_value = TrustUpdater.recenter_to_mean(score, population_mean=0.5)
        
        assert new_value == pytest.approx(0.86)
    
    def test_recenter_below_mean(self):
        """Test low trust moves toward mean."""
        score = MagicMock()
        score.governance_consistency = 0.2
        
        # 10% toward 0.5: 0.2 + 0.1*(0.5-0.2) = 0.2 + 0.03 = 0.23
        new_value = TrustUpdater.recenter_to_mean(score, population_mean=0.5)
        
        assert new_value == pytest.approx(0.23)
    
    def test_recenter_at_mean(self):
        """Test at-mean trust stays same."""
        score = MagicMock()
        score.governance_consistency = 0.5
        
        new_value = TrustUpdater.recenter_to_mean(score, population_mean=0.5)
        
        assert new_value == pytest.approx(0.5)
