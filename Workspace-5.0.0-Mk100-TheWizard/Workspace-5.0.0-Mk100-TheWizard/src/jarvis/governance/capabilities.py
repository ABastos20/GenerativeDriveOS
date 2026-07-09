"""
Capability Index & Command Sovereignty (Story 11-2)

The Fourth Lock: Constitutional permission gate that validates
which actions Mk100 "The Wizard" is allowed to execute.

Philosophy: "Mk100 is a myth engine + epistemic narrator, not a developer."
"""

import json
import re
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class Decision(Enum):
    """Capability decision outcomes."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_HUMAN = "require_human"


@dataclass
class PromptDecision:
    """Result of prompt safety evaluation."""
    verdict: str  # allow | deny | rewrite
    reason: str
    matched_rules: List[str]


class CapabilityIndex:
    """
    Sovereign capability registry enforcing constitutional permissions.
    
    The Fourth Lock in the Five Locks architecture:
    1. LLM Sandboxing (11-1b) - LLM only suggests
    2. Math Sovereignty (11-1b) - Goals from argmax(Belief * Value)
    3. Audit Logs (11-1b) - All suggestions logged
    4. Capability Index (11-2) - This class
    5. Prompt & Tool Sovereignty (11-3) - validate_prompt()
    """
    
    # Default forbidden patterns for prompt filtering (Lock 5)
    # NOTE: Uses word boundaries (\b) to avoid false positives (architect refinement)
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
        # Shell meta-characters (prevent implicit shell chaining)
        r"[;&|`$()]",
        r">\s*/",
        r"<\s*/",
    ]
    
    # Per-capability forbidden patterns
    CAPABILITY_PATTERNS = {
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
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize capability index.
        
        Args:
            config_path: Path to capability_index.json. If None, uses defaults.
        """
        self.config_path = config_path or Path("config/capability_index.json")
        self.capabilities = self._load_capabilities()
        self.version = self.capabilities.get("version", "11.2.0")
        self.default_policy = self.capabilities.get("default_policy", "deny")
        
        # Load prompt safety patterns
        self.forbidden_patterns = self.capabilities.get(
            "global_forbidden_patterns", 
            self.DEFAULT_FORBIDDEN_PATTERNS
        )
        self.per_capability_patterns = self.capabilities.get(
            "per_capability", 
            self.CAPABILITY_PATTERNS
        )

    def _load_capabilities(self) -> dict:
        """Load capability registry from JSON or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("capability_load_failed", error=str(e))
        
        # Default Mk100 "The Wizard" capability profile
        return {
            "version": "11.2.0",
            "default_policy": "deny",
            "philosophy": "Mk100 is a myth engine + epistemic narrator, not a developer.",
            "capabilities": {
                "write_story": {
                    "allowed": True,
                    "tier": "public",
                    "description": "Generate narrative content",
                    "agent_roles": ["storyteller", "all"],
                    "requires": []
                },
                "create_context": {
                    "allowed": True,
                    "tier": "public",
                    "description": "Synthesize project context",
                    "agent_roles": ["analyst", "architect", "all"],
                    "requires": []
                },
                "world_building": {
                    "allowed": True,
                    "tier": "public",
                    "description": "Create coherent worlds",
                    "agent_roles": ["storyteller", "all"],
                    "requires": []
                },
                "governance_reason": {
                    "allowed": True,
                    "tier": "public",
                    "description": "Reason about governance",
                    "agent_roles": ["all"],
                    "requires": []
                },
                "run_cli_tool": {
                    "allowed": True,
                    "tier": "restricted",
                    "description": "Execute codex/claude CLI",
                    "agent_roles": ["developer"],
                    "requires": ["human_approval"]
                },
                "modify_code": {
                    "allowed": False,
                    "tier": "forbidden",
                    "description": "Direct code modification",
                    "agent_roles": [],
                    "requires": []
                },
                "run_shell": {
                    "allowed": False,
                    "tier": "forbidden",
                    "description": "Shell command execution",
                    "agent_roles": [],
                    "requires": []
                },
                "mutate_infra": {
                    "allowed": False,
                    "tier": "forbidden",
                    "description": "Infrastructure changes",
                    "agent_roles": [],
                    "requires": []
                },
                "override_budget": {
                    "allowed": False,
                    "tier": "forbidden",
                    "description": "Budget constraint bypass",
                    "agent_roles": [],
                    "requires": []
                },
                "amend_constitution": {
                    "allowed": False,
                    "tier": "forbidden",
                    "description": "Constitutional changes",
                    "agent_roles": [],
                    "requires": []
                }
            }
        }

    def is_allowed(self, action_type: str, agent_role: str = "all") -> Decision:
        """
        Check if action is constitutionally permitted (Lock 4).
        
        Args:
            action_type: Action to validate (e.g., 'write_story')
            agent_role: Role of requesting agent (e.g., 'storyteller')
            
        Returns:
            Decision: ALLOW, DENY, or REQUIRE_HUMAN
        """
        # Default deny policy for unlisted capabilities
        caps = self.capabilities.get("capabilities", {})
        if action_type not in caps:
            logger.warning(
                "capability_denied_unknown",
                action_type=action_type,
                agent_role=agent_role,
                reason="unlisted_capability"
            )
            return Decision.DENY
        
        cap = caps[action_type]
        
        # Check if capability is allowed at all
        if not cap.get("allowed", False):
            logger.info(
                "capability_denied_forbidden",
                action_type=action_type,
                agent_role=agent_role,
                tier=cap.get("tier", "unknown")
            )
            return Decision.DENY
        
        # Check if agent role is permitted
        allowed_roles = cap.get("agent_roles", [])
        if allowed_roles and "all" not in allowed_roles and agent_role not in allowed_roles:
            logger.info(
                "capability_denied_role",
                action_type=action_type,
                agent_role=agent_role,
                allowed_roles=allowed_roles
            )
            return Decision.DENY
        
        # Check if human approval required
        if "human_approval" in cap.get("requires", []):
            logger.info(
                "capability_requires_human",
                action_type=action_type,
                agent_role=agent_role
            )
            return Decision.REQUIRE_HUMAN
        
        logger.debug(
            "capability_allowed",
            action_type=action_type,
            agent_role=agent_role
        )
        return Decision.ALLOW

    def validate_prompt(
        self, 
        prompt: str, 
        capability: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate prompt content doesn't trigger developer mode (Lock 5).
        
        This is the Semantic Command Firewall that prevents prompts from
        activating execution semantics in external LLM tools like codex/claude.
        
        Args:
            prompt: The prompt text to validate
            capability: The capability context (for specific filtering)
            
        Returns:
            Tuple of (is_safe: bool, reason: str)
        """
        matched_rules = []
        
        # Check global forbidden patterns
        # NOTE: Uses re.IGNORECASE instead of inline (?i) for simpler dynamic rule loading
        for pattern in self.forbidden_patterns:
            if re.search(pattern, prompt, flags=re.IGNORECASE):
                matched_rules.append(pattern)
        
        # Check per-capability patterns if applicable
        if capability:
            cap_patterns = self.per_capability_patterns.get(capability, {})
            if isinstance(cap_patterns, dict):
                cap_patterns = cap_patterns.get("forbidden_patterns", [])
            for pattern in cap_patterns:
                if re.search(pattern, prompt, flags=re.IGNORECASE):
                    matched_rules.append(pattern)
        
        if matched_rules:
            logger.warning(
                "prompt_denied",
                capability=capability,
                matched_rules=matched_rules,
                prompt_preview=prompt[:100] + "..." if len(prompt) > 100 else prompt
            )
            return False, f"Prompt matched forbidden patterns: {matched_rules}"
        
        return True, "OK"

    def evaluate_prompt(
        self,
        prompt: str,
        capability: Optional[str] = None,
        agent_role: Optional[str] = None
    ) -> PromptDecision:
        """
        Full prompt evaluation returning structured decision.
        
        Args:
            prompt: The prompt text to evaluate
            capability: The capability context
            agent_role: The agent role (for audit)
            
        Returns:
            PromptDecision with verdict, reason, and matched_rules
        """
        is_safe, reason = self.validate_prompt(prompt, capability)
        
        if is_safe:
            return PromptDecision(
                verdict="allow",
                reason="OK",
                matched_rules=[]
            )
        
        # Extract matched rules from reason string
        matched = []
        if "matched forbidden patterns:" in reason:
            try:
                # Parse the list from the reason string
                import ast
                rules_str = reason.split("matched forbidden patterns:")[1].strip()
                matched = ast.literal_eval(rules_str)
            except:
                matched = [reason]
        
        return PromptDecision(
            verdict="deny",
            reason=reason,
            matched_rules=matched
        )

    def get_capability_info(self, action_type: str) -> Optional[dict]:
        """Get detailed info about a capability."""
        return self.capabilities.get("capabilities", {}).get(action_type)
    
    def list_allowed_capabilities(self, agent_role: str = "all") -> List[str]:
        """List all capabilities allowed for an agent role."""
        allowed = []
        for cap_name, cap_info in self.capabilities.get("capabilities", {}).items():
            if self.is_allowed(cap_name, agent_role) == Decision.ALLOW:
                allowed.append(cap_name)
        return allowed

    # --- Governance Binding (Story 11-2 Task 3) ---
    
    def get_governance_config(self) -> dict:
        """Get governance configuration for capability updates."""
        return self.capabilities.get("governance", {
            "update_requires": ["CONFIGURE", "OWNER"],
            "proposal_type": "capability_update",
            "version_archive_enabled": True
        })
    
    def can_update_capability(self, permission_level: str) -> bool:
        """
        Check if a permission level can update capabilities.
        
        Governance binding: Only CONFIGURE or OWNER can modify capabilities.
        Changes require proposal + vote (handled by governance system).
        """
        gov_config = self.get_governance_config()
        allowed_permissions = gov_config.get("update_requires", ["CONFIGURE", "OWNER"])
        return permission_level in allowed_permissions
    
    def create_capability_update_proposal(
        self,
        capability: str,
        action: str,  # "enable", "disable", "modify"
        changes: dict,
        justification: str,
        proposer_id: str
    ) -> dict:
        """
        Create a capability update proposal for governance voting.
        
        Returns proposal dict that should be submitted to governance system.
        Actual update only happens after governance approval.
        """
        from datetime import datetime, timezone
        
        proposal = {
            "type": "capability_update",
            "capability": capability,
            "action": action,
            "current_state": self.get_capability_info(capability),
            "proposed_changes": changes,
            "justification": justification,
            "proposer_id": proposer_id,
            "current_version": self.version,
            "proposed_version": self._increment_version(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "requires_permission": self.get_governance_config().get("update_requires", ["CONFIGURE", "OWNER"])
        }
        
        logger.info(
            "capability_update_proposal_created",
            capability=capability,
            action=action,
            proposer=proposer_id
        )
        
        return proposal
    
    def _increment_version(self) -> str:
        """Increment the patch version for capability updates."""
        parts = self.version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts)

    # --- Capability Usage Tracking (Story 11-2 Task 4) ---
    
    def track_usage(self, capability: str, agent_id: str, agent_role: str, decision: Decision) -> None:
        """Track capability usage for telemetry and observability."""
        # Get or initialize usage tracker
        if not hasattr(self, '_usage_stats'):
            self._usage_stats = {
                "total_checks": 0,
                "allowed": 0,
                "denied": 0,
                "require_human": 0,
                "by_capability": {},
                "by_agent_role": {}
            }
        
        self._usage_stats["total_checks"] += 1
        
        if decision == Decision.ALLOW:
            self._usage_stats["allowed"] += 1
        elif decision == Decision.DENY:
            self._usage_stats["denied"] += 1
        elif decision == Decision.REQUIRE_HUMAN:
            self._usage_stats["require_human"] += 1
        
        # Track by capability
        if capability not in self._usage_stats["by_capability"]:
            self._usage_stats["by_capability"][capability] = {"allowed": 0, "denied": 0}
        if decision == Decision.ALLOW:
            self._usage_stats["by_capability"][capability]["allowed"] += 1
        else:
            self._usage_stats["by_capability"][capability]["denied"] += 1
        
        # Track by role
        if agent_role not in self._usage_stats["by_agent_role"]:
            self._usage_stats["by_agent_role"][agent_role] = {"allowed": 0, "denied": 0}
        if decision == Decision.ALLOW:
            self._usage_stats["by_agent_role"][agent_role]["allowed"] += 1
        else:
            self._usage_stats["by_agent_role"][agent_role]["denied"] += 1
    
    def get_usage_stats(self) -> dict:
        """Get capability usage statistics."""
        if not hasattr(self, '_usage_stats'):
            return {"total_checks": 0, "allowed": 0, "denied": 0, "require_human": 0}
        return self._usage_stats.copy()
    
    def get_top_capabilities(self, limit: int = 5) -> List[tuple]:
        """Get most frequently checked capabilities."""
        if not hasattr(self, '_usage_stats'):
            return []
        by_cap = self._usage_stats.get("by_capability", {})
        sorted_caps = sorted(
            by_cap.items(), 
            key=lambda x: x[1]["allowed"] + x[1]["denied"], 
            reverse=True
        )
        return sorted_caps[:limit]


# --- Intent Drift Detection (Story 11-1b Task 4) ---

@dataclass
class DenialEvent:
    """Record of a denied prompt/capability for drift detection."""
    timestamp: str
    agent_id: str
    agent_role: str
    capability: str
    action_type: str
    matched_rules: List[str]
    prompt_preview: str


class PromptDriftDetector:
    """
    Telemetry for blocked prompts and intent drift detection.
    
    Detects potential Ultron behavior by tracking repeated denial patterns.
    If an agent hits N denied prompts in a time window, raises an alert.
    """
    
    # Alert threshold: N denials in WINDOW_SECONDS
    DENIAL_THRESHOLD = 3
    WINDOW_SECONDS = 600  # 10 minutes
    
    def __init__(self):
        self.denials: List[DenialEvent] = []
        self._alerts: List[dict] = []
    
    def record_denial(
        self,
        agent_id: str,
        agent_role: str,
        capability: str,
        action_type: str,
        matched_rules: List[str],
        prompt: str
    ) -> None:
        """Record a prompt/capability denial for drift tracking."""
        from datetime import datetime, timezone
        
        event = DenialEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            agent_role=agent_role,
            capability=capability,
            action_type=action_type,
            matched_rules=matched_rules,
            prompt_preview=prompt[:100] + "..." if len(prompt) > 100 else prompt
        )
        self.denials.append(event)
        
        # Log telemetry event
        logger.warning(
            "prompt_denial_recorded",
            agent_id=agent_id,
            agent_role=agent_role,
            capability=capability,
            action_type=action_type,
            matched_rules=matched_rules
        )
        
        # Check for intent drift
        self._check_drift(agent_id)
    
    def _check_drift(self, agent_id: str) -> None:
        """Check if agent is exhibiting potential Ultron behavior."""
        from datetime import datetime, timezone, timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.WINDOW_SECONDS)
        cutoff_str = cutoff.isoformat()
        
        # Count recent denials for this agent
        recent_count = sum(
            1 for d in self.denials 
            if d.agent_id == agent_id and d.timestamp >= cutoff_str
        )
        
        if recent_count >= self.DENIAL_THRESHOLD:
            alert = {
                "severity": "WARNING",
                "pattern": "potential_ultron_behavior",
                "agent_id": agent_id,
                "denial_count": recent_count,
                "window_seconds": self.WINDOW_SECONDS,
                "message": f"Agent {agent_id} hit {recent_count} denials in {self.WINDOW_SECONDS}s",
                "action": "requires_investigation"
            }
            self._alerts.append(alert)
            
            logger.error(
                "intent_drift_detected",
                **alert
            )
    
    def get_alerts(self) -> List[dict]:
        """Get all intent drift alerts."""
        return self._alerts.copy()
    
    def get_denial_count(self, agent_id: str = None) -> int:
        """Get total denial count, optionally filtered by agent."""
        if agent_id:
            return sum(1 for d in self.denials if d.agent_id == agent_id)
        return len(self.denials)
    
    def get_top_denied_patterns(self, limit: int = 5) -> List[tuple]:
        """Get most frequently matched forbidden patterns."""
        from collections import Counter
        all_rules = []
        for d in self.denials:
            all_rules.extend(d.matched_rules)
        return Counter(all_rules).most_common(limit)


# Singleton instances for global access
_capability_index: Optional[CapabilityIndex] = None
_drift_detector: Optional[PromptDriftDetector] = None


def get_capability_index() -> CapabilityIndex:
    """Get or create the global capability index instance."""
    global _capability_index
    if _capability_index is None:
        _capability_index = CapabilityIndex()
    return _capability_index


def get_drift_detector() -> PromptDriftDetector:
    """Get or create the global drift detector instance."""
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = PromptDriftDetector()
    return _drift_detector

