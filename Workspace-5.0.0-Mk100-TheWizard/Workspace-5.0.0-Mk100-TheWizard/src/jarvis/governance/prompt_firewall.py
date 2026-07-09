"""
Prompt Firewall - Lock 5: Semantic Command Firewall & Tool Sovereignty (Story 11-3)

The Fifth Lock: Prevents LLM from self-escalating into developer mode.

This is the last line of defense before prompts reach external LLM tools.
Even if a prompt passes capability checks, it must not contain patterns
that could trick the downstream LLM into coding/execution behaviors.

Philosophy: "The bypass is not the action layer. It's the prompt layer."

Enforcement Chain:
1. CapabilityIndex.is_allowed() - Lock 4
2. PromptFirewall.evaluate() - Lock 5 (this module)
3. Workflow ceiling check
4. CLI safe-mode invocation
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PromptDecision:
    """Result of prompt safety evaluation."""
    verdict: str  # "allow", "deny", "rewrite"
    reason: str
    matched_rules: List[str] = field(default_factory=list)
    severity: str = "info"  # "info", "warning", "critical"
    
    @property
    def is_allowed(self) -> bool:
        return self.verdict == "allow"
    
    @property  
    def is_denied(self) -> bool:
        return self.verdict == "deny"


class PromptFirewall:
    """
    Lock 5: Semantic Command Firewall.
    
    Evaluates prompts for developer-mode patterns before they reach
    external LLM tools (codex, claude, etc.).
    
    Three-Layer Defense:
    1. Global forbidden patterns (apply to all prompts)
    2. Per-capability patterns (context-specific restrictions)
    3. Shell meta-character detection (prevent command injection)
    """
    
    # Global forbidden patterns (Lock 5 core)
    # NOTE: Uses word boundaries (\b) to avoid false positives
    DEFAULT_FORBIDDEN_PATTERNS = [
        # Developer mode triggers
        r"\bdeveloper mode\b",
        r"\bwrite\s+code\b",
        r"\bmodify\s+file\b",
        r"\brun\s+command\b",
        r"\bexecute\s+shell\b",
        r"\bapply\s+changes\b",
        r"\bgit\s+commit\b",
        r"\brm\s+-rf\b",
        r"\bimplement\s+",
        r"\brefactor\s+",
        r"\bfix\s+bug\b",
        r"\bupdate\s+code\b",
        r"\bcreate\s+file\b",
        r"\bdelete\s+file\b",
        r"\bedit\s+source\b",
    ]
    
    # Shell meta-characters (prevent implicit command chaining)
    SHELL_METACHAR_PATTERNS = [
        r"[;&|`$()]",
        r">\s*/",
        r"<\s*/",
    ]
    
    # Per-capability forbidden patterns
    CAPABILITY_PATTERNS: Dict[str, List[str]] = {
        "write_story": [
            r"\bimplement\b",
            r"\brefactor\b",
            r"\bfix\s+bug\b",
            r"\bupdate\s+code\b",
        ],
        "create_context": [
            r"\bgenerate\s+implementation\b",
            r"\bdatabase\s+migration\b",
        ],
        "governance_reason": [
            # More permissive - governance can discuss implementation abstractly
        ],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PromptFirewall.
        
        Args:
            config: Optional config dict with custom patterns.
                    If None, loads from CapabilityIndex config.
        """
        if config:
            self.global_patterns = config.get(
                "global_forbidden_patterns", 
                self.DEFAULT_FORBIDDEN_PATTERNS
            )
            self.capability_patterns = config.get(
                "per_capability", 
                self.CAPABILITY_PATTERNS
            )
        else:
            # Try to load from CapabilityIndex
            try:
                from jarvis.governance.capabilities import get_capability_index
                cap_index = get_capability_index()
                self.global_patterns = cap_index.capabilities.get(
                    "global_forbidden_patterns",
                    self.DEFAULT_FORBIDDEN_PATTERNS
                )
                self.capability_patterns = cap_index.capabilities.get(
                    "per_capability",
                    self.CAPABILITY_PATTERNS
                )
            except (ImportError, Exception):
                self.global_patterns = self.DEFAULT_FORBIDDEN_PATTERNS
                self.capability_patterns = self.CAPABILITY_PATTERNS
        
        self._denial_count = 0
        self._last_denial_reason = None
    
    def evaluate(
        self, 
        prompt: str,
        capability: Optional[str] = None,
        agent_role: Optional[str] = None
    ) -> PromptDecision:
        """
        Evaluate prompt for safety.
        
        Args:
            prompt: The prompt text to evaluate
            capability: Optional capability context (e.g., "write_story")
            agent_role: Optional agent role for logging
            
        Returns:
            PromptDecision with verdict, reason, and matched rules
        """
        matched_rules: List[str] = []
        
        # Check global forbidden patterns
        for pattern in self.global_patterns:
            if re.search(pattern, prompt, flags=re.IGNORECASE):
                matched_rules.append(f"global:{pattern}")
        
        # Check shell meta-characters
        for pattern in self.SHELL_METACHAR_PATTERNS:
            if re.search(pattern, prompt):
                matched_rules.append(f"shell:{pattern}")
        
        # Check per-capability patterns
        if capability:
            cap_patterns = self.capability_patterns.get(capability, [])
            if isinstance(cap_patterns, dict):
                cap_patterns = cap_patterns.get("forbidden_patterns", [])
            for pattern in cap_patterns:
                if re.search(pattern, prompt, flags=re.IGNORECASE):
                    matched_rules.append(f"capability:{pattern}")
        
        # Determine verdict
        if matched_rules:
            self._denial_count += 1
            
            # Determine severity based on pattern type
            has_shell = any("shell:" in r for r in matched_rules)
            has_developer = any("developer mode" in r.lower() for r in matched_rules)
            
            if has_shell or has_developer:
                severity = "critical"
            elif len(matched_rules) > 2:
                severity = "warning"
            else:
                severity = "info"
            
            reason = f"Blocked by {len(matched_rules)} rule(s): {matched_rules[:3]}"
            self._last_denial_reason = reason
            
            # Log denial
            logger.warning(
                "prompt_firewall_denied",
                capability=capability,
                agent_role=agent_role,
                matched_rules=matched_rules,
                severity=severity,
                prompt_preview=prompt[:100] + "..." if len(prompt) > 100 else prompt
            )
            
            return PromptDecision(
                verdict="deny",
                reason=reason,
                matched_rules=matched_rules,
                severity=severity
            )
        
        # Prompt is safe
        logger.debug(
            "prompt_firewall_allowed",
            capability=capability,
            agent_role=agent_role
        )
        
        return PromptDecision(
            verdict="allow",
            reason="No forbidden patterns detected",
            matched_rules=[],
            severity="info"
        )
    
    def get_stats(self) -> dict:
        """Get firewall statistics."""
        return {
            "total_denials": self._denial_count,
            "last_denial_reason": self._last_denial_reason
        }
    
    def can_proceed(
        self,
        prompt: str,
        capability: Optional[str] = None,
        agent_role: Optional[str] = None
    ) -> bool:
        """Convenience method - returns True if prompt is allowed."""
        decision = self.evaluate(prompt, capability, agent_role)
        return decision.is_allowed


# Singleton instance
_firewall: Optional[PromptFirewall] = None


def get_prompt_firewall() -> PromptFirewall:
    """Get the singleton PromptFirewall instance."""
    global _firewall
    if _firewall is None:
        _firewall = PromptFirewall()
    return _firewall


def reset_prompt_firewall() -> None:
    """Reset the singleton (for testing)."""
    global _firewall
    _firewall = None
