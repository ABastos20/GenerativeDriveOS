"""Safe mode configuration and enforcement for JARVIS.

Provides read-only mode to prevent agent invocation and database writes
during maintenance, testing, or debugging scenarios.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SafeConfig:
    """Configuration for safe mode operation.
    
    Safe mode enforces read-only operation:
    - No agent invocation
    - No database writes
    - Query/retrieval operations still allowed
    """
    
    enabled: bool = False
    allow_agent_invocation: bool = False
    allow_writes: bool = False
    
    @classmethod
    def from_env(cls) -> SafeConfig:
        """Load safe mode config from environment variables.
        
        Checks JARVIS_SAFE_MODE environment variable.
        When enabled, blocks agent invocation and writes.
        """
        enabled = os.environ.get("JARVIS_SAFE_MODE", "false").lower() == "true"
        return cls(
            enabled=enabled,
            allow_agent_invocation=not enabled,
            allow_writes=not enabled,
        )
    
    def enforce_safety(self, operation: str) -> None:
        """Raise exception if operation not allowed in safe mode.
        
        Args:
            operation: Operation type ("agent_invocation" or "write")
            
        Raises:
            PermissionError: If operation blocked by safe mode
        """
        if not self.enabled:
            return
            
        if operation == "agent_invocation" and not self.allow_agent_invocation:
            logger.warning("safe_mode_block", operation=operation)
            raise PermissionError("Agent invocation blocked in safe mode")
        
        if operation == "write" and not self.allow_writes:
            logger.warning("safe_mode_block", operation=operation)
            raise PermissionError("Write operations blocked in safe mode")
        
        logger.debug("safe_mode_allow", operation=operation)
