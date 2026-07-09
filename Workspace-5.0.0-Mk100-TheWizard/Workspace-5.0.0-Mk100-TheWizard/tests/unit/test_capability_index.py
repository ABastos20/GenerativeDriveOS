"""Unit tests for Story 11-2 Capability Index & Command Sovereignty.

Tests the Fourth Lock - Constitutional permission gate that validates
which actions Mk100 "The Wizard" is allowed to execute.

Tests cover:
- AC1: Capability Registry (default deny, versioning)
- AC2: Capability Service (is_allowed, roles, tiers)
- AC3: ReasoningEngine Enforcement  
- AC4: Governance Binding
- AC5: Telemetry & Observability
- AC6: Prompt Sovereignty (covered in 11-1b tests)
"""
import pytest
from pathlib import Path
import json


class TestCapabilityRegistry:
    """AC1: Tests for capability registry file and loading."""
    
    @pytest.fixture
    def capability_index(self):
        """Load CapabilityIndex from config file."""
        from jarvis.governance.capabilities import CapabilityIndex
        config_path = Path("config/capability_index.json")
        return CapabilityIndex(config_path=config_path)
    
    def test_registry_file_exists(self):
        """Verify config/capability_index.json exists."""
        config_path = Path("config/capability_index.json")
        assert config_path.exists(), "Capability registry file missing"
    
    def test_registry_has_version(self, capability_index):
        """Verify registry is versioned."""
        assert capability_index.version is not None
        assert capability_index.version.count(".") == 2, "Version should be semver"
    
    def test_default_deny_policy(self, capability_index):
        """Verify unlisted capabilities are denied."""
        from jarvis.governance.capabilities import Decision
        
        # Unknown capability should be denied
        decision = capability_index.is_allowed("unknown_capability_xyz", "any_role")
        assert decision == Decision.DENY
    
    def test_registry_has_capabilities(self, capability_index):
        """Verify registry has expected capabilities."""
        info = capability_index.get_capability_info("write_story")
        assert info is not None
        assert "allowed" in info
        assert "tier" in info


class TestCapabilityService:
    """AC2: Tests for CapabilityIndex service."""
    
    @pytest.fixture  
    def capability_index(self):
        """Load CapabilityIndex."""
        from jarvis.governance.capabilities import CapabilityIndex
        return CapabilityIndex()
    
    def test_decision_enum_values(self):
        """Verify Decision enum has expected values."""
        from jarvis.governance.capabilities import Decision
        assert Decision.ALLOW.value == "allow"
        assert Decision.DENY.value == "deny"
        assert Decision.REQUIRE_HUMAN.value == "require_human"
    
    def test_allowed_capability_returns_allow(self, capability_index):
        """Test is_allowed returns ALLOW for permitted capabilities."""
        from jarvis.governance.capabilities import Decision
        
        decision = capability_index.is_allowed("write_story", "storyteller")
        assert decision == Decision.ALLOW
    
    def test_forbidden_capability_returns_deny(self, capability_index):
        """Test is_allowed returns DENY for forbidden capabilities."""
        from jarvis.governance.capabilities import Decision
        
        decision = capability_index.is_allowed("modify_code", "any_role")
        assert decision == Decision.DENY
    
    def test_restricted_capability_requires_human(self, capability_index):
        """Test restricted capabilities return REQUIRE_HUMAN."""
        from jarvis.governance.capabilities import Decision
        
        decision = capability_index.is_allowed("run_cli_tool", "developer")
        assert decision == Decision.REQUIRE_HUMAN
    
    def test_role_filtering(self, capability_index):
        """Test role-based filtering works."""
        from jarvis.governance.capabilities import Decision
        
        # storyteller can write_story
        assert capability_index.is_allowed("write_story", "storyteller") == Decision.ALLOW
        
        # wrong role should be denied (if roles are enforced)
        # Note: depends on registry configuration
    
    def test_all_role_grants_access(self, capability_index):
        """Test 'all' role grants access."""
        from jarvis.governance.capabilities import Decision
        
        decision = capability_index.is_allowed("governance_reason", "any_random_role")
        assert decision == Decision.ALLOW


class TestPromptFiltering:
    """Tests for prompt sovereignty (Lock 5 partial)."""
    
    @pytest.fixture
    def capability_index(self):
        """Load CapabilityIndex."""
        from jarvis.governance.capabilities import CapabilityIndex
        return CapabilityIndex()
    
    def test_forbidden_pattern_blocked(self, capability_index):
        """Test forbidden patterns are detected."""
        prompt = "Please write code to implement the feature"
        allowed, reason = capability_index.validate_prompt(prompt)
        assert not allowed
        assert "forbidden" in reason.lower() or "blocked" in reason.lower()
    
    def test_safe_prompt_allowed(self, capability_index):
        """Test safe prompts are allowed."""
        prompt = "Analyze the governance structure of this institution"
        allowed, reason = capability_index.validate_prompt(prompt)
        assert allowed
    
    def test_shell_metachar_blocked(self, capability_index):
        """Test shell meta-characters are blocked."""
        prompt = "Can you help me; rm -rf /"
        allowed, reason = capability_index.validate_prompt(prompt)
        assert not allowed


class TestGovernanceBinding:
    """AC4: Tests for governance binding."""
    
    @pytest.fixture
    def capability_index(self):
        """Load CapabilityIndex."""
        from jarvis.governance.capabilities import CapabilityIndex
        return CapabilityIndex()
    
    def test_governance_config_exists(self, capability_index):
        """Test governance configuration is present."""
        gov_config = capability_index.get_governance_config()
        assert "update_requires" in gov_config
    
    def test_configure_permission_can_update(self, capability_index):
        """Test CONFIGURE permission allows updates."""
        assert capability_index.can_update_capability("CONFIGURE")
        assert capability_index.can_update_capability("OWNER")
    
    def test_normal_role_cannot_update(self, capability_index):
        """Test normal roles cannot update capabilities."""
        assert not capability_index.can_update_capability("storyteller")
        assert not capability_index.can_update_capability("developer")
    
    def test_create_update_proposal(self, capability_index):
        """Test capability update proposal creation."""
        proposal = capability_index.create_capability_update_proposal(
            capability="write_story",
            action="modify",
            changes={"tier": "restricted"},
            justification="Testing governance binding",
            proposer_id="test-user"
        )
        
        assert proposal["type"] == "capability_update"
        assert proposal["capability"] == "write_story"
        assert proposal["status"] == "pending"
        assert "proposed_version" in proposal


class TestUsageTracking:
    """AC5: Tests for telemetry and observability."""
    
    @pytest.fixture
    def capability_index(self):
        """Load CapabilityIndex."""
        from jarvis.governance.capabilities import CapabilityIndex
        return CapabilityIndex()
    
    def test_usage_tracking_records(self, capability_index):
        """Test usage tracking records decisions."""
        from jarvis.governance.capabilities import Decision
        
        # Track some usage
        capability_index.track_usage("write_story", "agent-1", "storyteller", Decision.ALLOW)
        capability_index.track_usage("modify_code", "agent-1", "storyteller", Decision.DENY)
        
        stats = capability_index.get_usage_stats()
        assert stats["total_checks"] >= 2
        assert stats["allowed"] >= 1
        assert stats["denied"] >= 1
    
    def test_top_capabilities_returns_list(self, capability_index):
        """Test top capabilities returns sorted list."""
        from jarvis.governance.capabilities import Decision
        
        # Track some usage
        capability_index.track_usage("write_story", "agent-1", "storyteller", Decision.ALLOW)
        capability_index.track_usage("write_story", "agent-2", "storyteller", Decision.ALLOW)
        
        top = capability_index.get_top_capabilities(limit=5)
        assert isinstance(top, list)


class TestDriftDetection:
    """Tests for intent drift detection (Ultron behavior)."""
    
    def test_drift_detector_records_denial(self):
        """Test drift detector records denial events."""
        from jarvis.governance.capabilities import get_drift_detector
        
        detector = get_drift_detector()
        detector.record_denial(
            agent_id="test-agent",
            agent_role="storyteller",
            capability="modify_code",
            action_type="modify_code",
            matched_rules=["capability_denied"],
            prompt="test prompt"
        )
        
        assert len(detector.denials) >= 1
    
    def test_multiple_denials_triggers_alert(self):
        """Test repeated denials trigger Ultron alert."""
        from jarvis.governance.capabilities import PromptDriftDetector
        
        detector = PromptDriftDetector()
        
        # Record 3+ denials (threshold)
        for i in range(4):
            detector.record_denial(
                agent_id="suspicious-agent",
                agent_role="storyteller",
                capability="modify_code",
                action_type="modify_code",
                matched_rules=["capability_denied"],
                prompt=f"test prompt {i}"
            )
        
        # Should have generated alert
        alerts = detector.get_alerts()
        assert len(alerts) >= 1
        assert "potential_ultron_behavior" in alerts[0].get("pattern", "")
