"""Unit Tests for Story 9-4: Constitutional Framework.

Verifies:
1. ConstitutionalGuard.get_active_constitution() 
2. ConstitutionalGuard.check_legitimacy_conservation()
3. ConstitutionalGuard.validate_parameter_safety()
4. Integration with Trust Calculator
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from jarvis.governance.models import Constitution
from jarvis.governance.constitution import ConstitutionalGuard, ConstitutionalViolation


class TestConstitutionalGuard:
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def default_constitution(self):
        """Standard constitution for testing."""
        c = Constitution(
            active=True,
            weight_epistemic=0.4,
            weight_consistency=0.3,
            weight_integrity=0.2,
            weight_reputation=0.1,
            sybil_threshold=0.2,
            minority_floor=0.05,
            anti_elite_multiplier=5.0,
            max_legitimacy_drift=0.1
        )
        return c
    
    def test_get_active_constitution_exists(self, mock_session, default_constitution):
        """Verify fetching active constitution when it exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = default_constitution
        mock_session.execute.return_value = mock_result
        
        result = ConstitutionalGuard.get_active_constitution(mock_session)
        
        assert result == default_constitution
        assert result.active is True
        
    def test_get_active_constitution_auto_bootstrap(self, mock_session):
        """Verify auto-creation of constitution if none exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = ConstitutionalGuard.get_active_constitution(mock_session)
        
        # Should have created a new constitution
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert isinstance(result, Constitution)
        assert result.active is True
        
    def test_legitimacy_conservation_within_bounds(self):
        """Verify no exception when drift is within limits."""
        prev = 100.0
        new = 108.0  # 8% increase
        max_drift = 0.1  # 10% max
        
        # Should not raise
        ConstitutionalGuard.check_legitimacy_conservation(prev, new, max_drift)
        
    def test_legitimacy_conservation_violation(self):
        """Verify exception when drift exceeds limits."""
        prev = 100.0
        new = 120.0  # 20% increase
        max_drift = 0.1  # 10% max
        
        with pytest.raises(ConstitutionalViolation) as exc_info:
            ConstitutionalGuard.check_legitimacy_conservation(prev, new, max_drift)
            
        assert "Legitimacy Conservation Violation" in str(exc_info.value)
        assert "20.00%" in str(exc_info.value)
        
    def test_legitimacy_conservation_decrease(self):
        """Verify bidirectional drift detection (decrease)."""
        prev = 100.0
        new = 80.0  # 20% decrease
        max_drift = 0.1  # 10% max
        
        with pytest.raises(ConstitutionalViolation):
            ConstitutionalGuard.check_legitimacy_conservation(prev, new, max_drift)
            
    def test_legitimacy_conservation_zero_edge_case(self):
        """Verify handling of zero previous weight (bootstrap case)."""
        prev = 0.0
        new = 10.0
        max_drift = 0.1
        
        # Should not raise for bootstrap (from zero is always allowed)
        ConstitutionalGuard.check_legitimacy_conservation(prev, new, max_drift)
        
    def test_validate_parameter_safety_valid(self):
        """Verify validation of safe parameter changes."""
        # Weights sum to 1.0
        params = {
            'weight_epistemic': 0.35,
            'weight_consistency': 0.35,
            'weight_integrity': 0.2,
            'weight_reputation': 0.1
        }
        
        # Should not raise
        ConstitutionalGuard.validate_parameter_safety(params)
        
    def test_validate_parameter_safety_invalid_sum(self):
        """Verify rejection of weights that don't sum to 1.0."""
        params = {
            'weight_epistemic': 0.5,
            'weight_consistency': 0.3,
            'weight_integrity': 0.2,
            'weight_reputation': 0.1  # Sum = 1.1
        }
        
        with pytest.raises(ConstitutionalViolation) as exc_info:
            ConstitutionalGuard.validate_parameter_safety(params)
            
        assert "must sum to 1.0" in str(exc_info.value)
        
    def test_validate_parameter_safety_negative_weight(self):
        """Verify rejection of negative weights."""
        params = {
            'weight_epistemic': 0.5,
            'weight_consistency': -0.1,  # Invalid
            'weight_integrity': 0.4,
            'weight_reputation': 0.2
        }
        
        with pytest.raises(ConstitutionalViolation) as exc_info:
            ConstitutionalGuard.validate_parameter_safety(params)
            
        assert "Weights must be non-negative" in str(exc_info.value)
        
    def test_validate_parameter_safety_invalid_threshold(self):
        """Verify bounds checking for thresholds."""
        params = {'sybil_threshold': 1.5}  # > 1.0
        
        with pytest.raises(ConstitutionalViolation) as exc_info:
            ConstitutionalGuard.validate_parameter_safety(params)
            
        assert "must be between 0.0 and 1.0" in str(exc_info.value)
        
    def test_validate_parameter_safety_partial_update(self):
        """Verify validation works for partial parameter updates."""
        # Only updating some weights (valid scenario for amendment)
        params = {
            'sybil_threshold': 0.25,
            'minority_floor': 0.03
        }
        
        # Should not raise (partial updates are allowed)
        ConstitutionalGuard.validate_parameter_safety(params)
