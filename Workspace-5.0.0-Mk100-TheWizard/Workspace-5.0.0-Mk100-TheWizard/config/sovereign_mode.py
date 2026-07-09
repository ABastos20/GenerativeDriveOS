"""Sovereign Mode Configuration for Epic 11 (Mk100 "The Wizard").

Story 11-8: This module implements the Sovereign Mode switch that
enforces all 7 Locks as mandatory when enabled.

Fail-Closed Semantics:
    If sovereign_mode = True and any required sub-component fails to
    initialise, the system MUST fail-closed:
    - No tier promotions allowed
    - Logs a critical event
    - Serves only low-risk advisory responses
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, List

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SovereignState:
    """Runtime state tracking for Sovereign Mode."""
    
    # Core component availability
    arbitration_ready: bool = False
    trust_engine_ready: bool = False
    usage_policy_ready: bool = False
    audit_sinks_ready: bool = False
    provenance_ready: bool = False
    
    # Failure tracking
    initialization_errors: List[str] = field(default_factory=list)
    
    @property
    def all_components_ready(self) -> bool:
        """Check if all required components are initialized."""
        return all([
            self.arbitration_ready,
            self.trust_engine_ready,
            self.usage_policy_ready,
            self.audit_sinks_ready,
            self.provenance_ready,
        ])
    
    def register_component(self, name: str, ready: bool, error: Optional[str] = None) -> None:
        """Register a component's readiness state."""
        if name == "arbitration":
            self.arbitration_ready = ready
        elif name == "trust_engine":
            self.trust_engine_ready = ready
        elif name == "usage_policy":
            self.usage_policy_ready = ready
        elif name == "audit_sinks":
            self.audit_sinks_ready = ready
        elif name == "provenance":
            self.provenance_ready = ready
        
        if error:
            self.initialization_errors.append(f"{name}: {error}")
            logger.critical(
                "sovereign_component_initialization_failed",
                component=name,
                error=error
            )


class SovereignSettings:
    """
    Sovereign Mode settings for Epic 11.
    
    When sovereign_mode is True, all Epic 11 invariants become mandatory:
    - Persona arbitration required for tier promotions
    - Usage policy enforced at runtime
    - Contradiction penalties active
    - All audit sinks receive events
    - Provenance freeze rules active
    - BMAD memory strictness enabled
    
    Fail-Closed: If sovereign_mode=True but components aren't ready,
    the system operates in fail-safe mode (no promotions, advisory only).
    """
    
    def __init__(self):
        # Read from environment or default to True for production safety
        self._sovereign_mode = os.environ.get("JARVIS_SOVEREIGN_MODE", "true").lower() == "true"
        self._state = SovereignState()
        self._fail_closed_active = False
    
    @property
    def sovereign_mode(self) -> bool:
        """Whether Sovereign Mode is enabled."""
        return self._sovereign_mode
    
    @sovereign_mode.setter
    def sovereign_mode(self, value: bool) -> None:
        """Set Sovereign Mode (for testing)."""
        self._sovereign_mode = value
        logger.info("sovereign_mode_changed", enabled=value)
    
    @property
    def state(self) -> SovereignState:
        """Get the current runtime state."""
        return self._state
    
    @property
    def is_operational(self) -> bool:
        """
        Check if system is fully operational.
        
        Returns True if either:
        - Sovereign mode is OFF (lenient mode)
        - Sovereign mode is ON AND all components are ready
        """
        if not self._sovereign_mode:
            return True
        return self._state.all_components_ready
    
    @property
    def fail_closed_active(self) -> bool:
        """
        Check if fail-closed mode is active.
        
        Fail-closed is active when:
        - Sovereign mode is ON
        - But not all components are ready
        """
        return self._sovereign_mode and not self._state.all_components_ready
    
    def check_can_promote(self, knowledge_unit_id: str) -> tuple[bool, str]:
        """
        Check if a tier promotion is allowed under current mode.
        
        Returns:
            (allowed, reason) tuple
        """
        if not self._sovereign_mode:
            return True, "Sovereign mode disabled - lenient promotion"
        
        if not self._state.all_components_ready:
            logger.warning(
                "sovereign_promotion_blocked_fail_closed",
                knowledge_unit_id=knowledge_unit_id,
                missing_components=[
                    c for c, ready in [
                        ("arbitration", self._state.arbitration_ready),
                        ("trust_engine", self._state.trust_engine_ready),
                        ("usage_policy", self._state.usage_policy_ready),
                        ("audit_sinks", self._state.audit_sinks_ready),
                        ("provenance", self._state.provenance_ready),
                    ] if not ready
                ]
            )
            return False, "Fail-closed: Required components not initialized"
        
        return True, "Sovereign mode operational - promotion allowed"
    
    def get_mode_summary(self) -> dict:
        """Get a summary of the current mode state."""
        return {
            "sovereign_mode": self._sovereign_mode,
            "all_components_ready": self._state.all_components_ready,
            "fail_closed_active": self.fail_closed_active,
            "components": {
                "arbitration": self._state.arbitration_ready,
                "trust_engine": self._state.trust_engine_ready,
                "usage_policy": self._state.usage_policy_ready,
                "audit_sinks": self._state.audit_sinks_ready,
                "provenance": self._state.provenance_ready,
            },
            "initialization_errors": self._state.initialization_errors,
        }


# Module-level singleton
_settings: Optional[SovereignSettings] = None


def get_sovereign_settings() -> SovereignSettings:
    """Get the singleton SovereignSettings instance."""
    global _settings
    if _settings is None:
        _settings = SovereignSettings()
    return _settings


def reset_sovereign_settings() -> None:
    """Reset settings (for testing)."""
    global _settings
    _settings = None


# Convenience accessor
settings = get_sovereign_settings()
