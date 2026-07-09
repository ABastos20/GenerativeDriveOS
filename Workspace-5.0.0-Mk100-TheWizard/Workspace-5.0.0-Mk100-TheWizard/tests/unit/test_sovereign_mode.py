"""Tests for Story 11-8 Sovereign Mode Configuration.

Tests AC2: Sovereign Mode Switch with fail-closed semantics.
"""

import pytest
import os
from unittest.mock import patch


class TestSovereignSettings:
    """Tests for SovereignSettings configuration."""

    def test_default_sovereign_mode_enabled(self):
        """Sovereign mode should default to True for production safety."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        assert settings.sovereign_mode is True

    def test_sovereign_mode_from_env_false(self):
        """Can disable sovereign mode via environment variable."""
        from config.sovereign_mode import SovereignSettings
        
        with patch.dict(os.environ, {"JARVIS_SOVEREIGN_MODE": "false"}):
            settings = SovereignSettings()
            assert settings.sovereign_mode is False

    def test_sovereign_mode_from_env_true(self):
        """Explicit true from environment."""
        from config.sovereign_mode import SovereignSettings
        
        with patch.dict(os.environ, {"JARVIS_SOVEREIGN_MODE": "true"}):
            settings = SovereignSettings()
            assert settings.sovereign_mode is True

    def test_mode_summary(self):
        """Mode summary should include all relevant state."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        summary = settings.get_mode_summary()
        
        assert "sovereign_mode" in summary
        assert "all_components_ready" in summary
        assert "fail_closed_active" in summary
        assert "components" in summary


class TestSovereignState:
    """Tests for SovereignState component tracking."""

    def test_initial_state_not_ready(self):
        """All components should start as not ready."""
        from config.sovereign_mode import SovereignState
        
        state = SovereignState()
        assert state.all_components_ready is False

    def test_register_all_components_ready(self):
        """All components ready when all registered."""
        from config.sovereign_mode import SovereignState
        
        state = SovereignState()
        state.register_component("arbitration", True)
        state.register_component("trust_engine", True)
        state.register_component("usage_policy", True)
        state.register_component("audit_sinks", True)
        state.register_component("provenance", True)
        
        assert state.all_components_ready is True

    def test_register_component_error(self):
        """Errors should be tracked."""
        from config.sovereign_mode import SovereignState
        
        state = SovereignState()
        state.register_component("arbitration", False, error="Failed to initialize")
        
        assert state.arbitration_ready is False
        assert "arbitration" in state.initialization_errors[0]


class TestFailClosedSemantics:
    """Tests for fail-closed behavior when sovereign mode is ON but components not ready."""

    def test_fail_closed_when_components_missing(self):
        """Fail-closed should be active when components not initialized."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        settings.sovereign_mode = True
        # Components not registered = fail_closed_active
        
        assert settings.fail_closed_active is True

    def test_not_fail_closed_when_all_ready(self):
        """Not fail-closed when all components ready."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        settings.sovereign_mode = True
        
        # Register all components
        settings.state.register_component("arbitration", True)
        settings.state.register_component("trust_engine", True)
        settings.state.register_component("usage_policy", True)
        settings.state.register_component("audit_sinks", True)
        settings.state.register_component("provenance", True)
        
        assert settings.fail_closed_active is False
        assert settings.is_operational is True

    def test_not_fail_closed_when_sovereign_off(self):
        """Not fail-closed when sovereign mode is off (lenient mode)."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        settings.sovereign_mode = False
        # Even with no components registered, not fail-closed
        
        assert settings.fail_closed_active is False
        assert settings.is_operational is True


class TestPromotionGating:
    """Tests for tier promotion gating under sovereign mode."""

    def test_promotion_blocked_fail_closed(self):
        """Promotions should be blocked when fail-closed is active."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        settings.sovereign_mode = True
        # Components not ready = fail_closed
        
        allowed, reason = settings.check_can_promote("test-knowledge-unit-id")
        
        assert allowed is False
        assert "fail-closed" in reason.lower()

    def test_promotion_allowed_when_operational(self):
        """Promotions allowed when fully operational."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        settings.sovereign_mode = True
        
        # Register all components
        settings.state.register_component("arbitration", True)
        settings.state.register_component("trust_engine", True)
        settings.state.register_component("usage_policy", True)
        settings.state.register_component("audit_sinks", True)
        settings.state.register_component("provenance", True)
        
        allowed, reason = settings.check_can_promote("test-knowledge-unit-id")
        
        assert allowed is True
        assert "operational" in reason.lower()

    def test_promotion_allowed_lenient_mode(self):
        """Promotions allowed in lenient mode (sovereign OFF)."""
        from config.sovereign_mode import SovereignSettings
        
        settings = SovereignSettings()
        settings.sovereign_mode = False
        
        allowed, reason = settings.check_can_promote("test-knowledge-unit-id")
        
        assert allowed is True
        assert "lenient" in reason.lower()


class TestSingletonPattern:
    """Tests for singleton access pattern."""

    def test_get_sovereign_settings_singleton(self):
        """Settings should be a singleton."""
        from config.sovereign_mode import get_sovereign_settings, reset_sovereign_settings
        
        reset_sovereign_settings()
        settings1 = get_sovereign_settings()
        settings2 = get_sovereign_settings()
        
        assert settings1 is settings2

    def test_reset_clears_singleton(self):
        """Reset should clear the singleton."""
        from config.sovereign_mode import get_sovereign_settings, reset_sovereign_settings
        
        settings1 = get_sovereign_settings()
        reset_sovereign_settings()
        settings2 = get_sovereign_settings()
        
        assert settings1 is not settings2
