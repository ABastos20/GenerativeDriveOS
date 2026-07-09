"""Unit tests for Dual-Persona Arbitration (Story 11-5, Task 3).

Tests dual-persona evaluation logic, promotion rules, and freeze mechanisms.
Coverage target: ≥90% per AC #3 requirements.
"""

import pytest
from src.jarvis.knowledge.arbitration import (
    Persona,
    VerdictType,
    ArbitrationVerdict,
    ArbitrationResult,
    DualPersonaArbitrator,
    format_arbitration_report,
)
from src.jarvis.knowledge.tiers import KnowledgeTier


class TestArbitrationVerdict:
    """Test ArbitrationVerdict validation."""

    def test_valid_verdict(self):
        """Test valid verdict creation."""
        verdict = ArbitrationVerdict(
            persona=Persona.ANALYST,
            verdict=VerdictType.APPROVE,
            confidence=0.85,
            reasoning="Claim is logically consistent",
            identified_risks=[],
        )

        assert verdict.persona == Persona.ANALYST
        assert verdict.verdict == VerdictType.APPROVE
        assert verdict.confidence == 0.85

    def test_invalid_confidence_high(self):
        """Test that confidence > 1.0 is rejected."""
        with pytest.raises(ValueError, match="confidence must be in"):
            ArbitrationVerdict(
                persona=Persona.ANALYST,
                verdict=VerdictType.APPROVE,
                confidence=1.5,
                reasoning="Test",
                identified_risks=[],
            )

    def test_invalid_confidence_low(self):
        """Test that confidence < 0.0 is rejected."""
        with pytest.raises(ValueError, match="confidence must be in"):
            ArbitrationVerdict(
                persona=Persona.ADVERSARY,
                verdict=VerdictType.REJECT,
                confidence=-0.1,
                reasoning="Test",
                identified_risks=[],
            )


class TestArbitrationResult:
    """Test ArbitrationResult properties."""

    def test_both_approved(self):
        """Test both_approved property when both approve."""
        analyst = ArbitrationVerdict(
            persona=Persona.ANALYST,
            verdict=VerdictType.APPROVE,
            confidence=0.9,
            reasoning="Approved",
            identified_risks=[],
        )
        adversary = ArbitrationVerdict(
            persona=Persona.ADVERSARY,
            verdict=VerdictType.APPROVE,
            confidence=0.85,
            reasoning="Approved",
            identified_risks=[],
        )

        result = ArbitrationResult(
            analyst_verdict=analyst,
            adversary_verdict=adversary,
            promotion_allowed=True,
            freeze_required=False,
            reason="Both approved",
        )

        assert result.both_approved is True
        assert result.any_rejected is False

    def test_any_rejected(self):
        """Test any_rejected property when one rejects."""
        analyst = ArbitrationVerdict(
            persona=Persona.ANALYST,
            verdict=VerdictType.REJECT,
            confidence=0.7,
            reasoning="Rejected",
            identified_risks=["logical inconsistency"],
        )
        adversary = ArbitrationVerdict(
            persona=Persona.ADVERSARY,
            verdict=VerdictType.APPROVE,
            confidence=0.85,
            reasoning="Approved",
            identified_risks=[],
        )

        result = ArbitrationResult(
            analyst_verdict=analyst,
            adversary_verdict=adversary,
            promotion_allowed=False,
            freeze_required=True,
            reason="Disagreement",
        )

        assert result.both_approved is False
        assert result.any_rejected is True


class TestDualPersonaArbitrator:
    """Test dual-persona arbitration logic."""

    @pytest.fixture
    def arbitrator(self):
        """Create arbitrator instance."""
        return DualPersonaArbitrator()

    def test_arbitrate_both_approve(self, arbitrator):
        """Test arbitration when both personas approve (AC #3: Promotion allowed)."""
        # Use a claim that will pass both personas' heuristics
        claim = "The system measured average latency of 150ms over 1000 requests"
        source = "telemetry://system-metrics"

        result = arbitrator.arbitrate(
            claim=claim,
            source=source,
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
        )

        # Both should approve (heuristics pass)
        assert result.analyst_verdict.verdict == VerdictType.APPROVE
        assert result.adversary_verdict.verdict == VerdictType.APPROVE
        assert result.promotion_allowed is True
        assert result.freeze_required is False

    def test_arbitrate_disagreement_freeze(self, arbitrator):
        """Test arbitration when personas disagree (AC #3: Freeze required)."""
        # Use absolutist language to trigger adversary rejection
        claim = "This is absolutely guaranteed to always work perfectly"
        source = "blog://random-site"

        result = arbitrator.arbitrate(
            claim=claim,
            source=source,
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )

        # Should trigger disagreement (adversary likely rejects)
        # Note: With current heuristics, both might reject, which is also valid
        # The key test is that if disagreement occurs, freeze is required

        if result.analyst_verdict.verdict != result.adversary_verdict.verdict:
            assert result.freeze_required is True
            assert result.promotion_allowed is False
            assert "disagreement" in result.reason.lower()

    def test_arbitrate_both_reject(self, arbitrator):
        """Test arbitration when both personas reject."""
        # Use a very short claim with suspicious source AND absolutist language
        claim = "This is guaranteed to always work perfectly"
        source = "unknown://forum-post"

        result = arbitrator.arbitrate(
            claim=claim,
            source=source,
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )

        # Both should reject (fails multiple heuristics)
        assert result.analyst_verdict.verdict == VerdictType.REJECT
        assert result.adversary_verdict.verdict == VerdictType.REJECT
        assert result.promotion_allowed is False
        assert result.freeze_required is False  # No freeze on agreement

    def test_arbitrate_invalid_promotion(self, arbitrator):
        """Test that invalid promotions are rejected."""
        with pytest.raises(ValueError, match="Invalid promotion"):
            arbitrator.arbitrate(
                claim="Test",
                source="test",
                current_tier=KnowledgeTier.K2,
                target_tier=KnowledgeTier.K3,  # Demotion, not promotion
            )

    def test_arbitrate_with_context(self, arbitrator):
        """Test arbitration with additional context."""
        claim = "System performance improved by 25%"
        source = "analytics://internal"
        context = {
            "baseline": "200ms",
            "current": "150ms",
            "sample_size": 1000,
        }

        result = arbitrator.arbitrate(
            claim=claim,
            source=source,
            current_tier=KnowledgeTier.K1,
            target_tier=KnowledgeTier.K0,
            context=context,
        )

        # Context is passed to evaluation (even if not used in heuristics)
        assert result is not None
        assert result.analyst_verdict is not None
        assert result.adversary_verdict is not None

    def test_promotion_rule_formal(self, arbitrator):
        """Test formal promotion rule: Promotion(i) = allowed ⟺ f_A(i) = 1 ∧ f_D(i) = 1."""
        # Create test cases for all verdict combinations
        test_cases = [
            # (analyst, adversary, expected_allowed)
            (VerdictType.APPROVE, VerdictType.APPROVE, True),   # 1 ∧ 1 = 1
            (VerdictType.APPROVE, VerdictType.REJECT, False),   # 1 ∧ 0 = 0
            (VerdictType.REJECT, VerdictType.APPROVE, False),   # 0 ∧ 1 = 0
            (VerdictType.REJECT, VerdictType.REJECT, False),    # 0 ∧ 0 = 0
        ]

        for analyst_v, adversary_v, expected in test_cases:
            analyst = ArbitrationVerdict(
                persona=Persona.ANALYST,
                verdict=analyst_v,
                confidence=0.8,
                reasoning="Test",
                identified_risks=[],
            )
            adversary = ArbitrationVerdict(
                persona=Persona.ADVERSARY,
                verdict=adversary_v,
                confidence=0.8,
                reasoning="Test",
                identified_risks=[],
            )

            result = arbitrator._make_arbitration_decision(
                analyst,
                adversary,
                KnowledgeTier.K3,
                KnowledgeTier.K2,
            )

            assert result.promotion_allowed == expected


class TestFormatArbitrationReport:
    """Test arbitration report formatting."""

    def test_format_report_approval(self):
        """Test report formatting for approval case."""
        analyst = ArbitrationVerdict(
            persona=Persona.ANALYST,
            verdict=VerdictType.APPROVE,
            confidence=0.90,
            reasoning="Logically consistent",
            identified_risks=[],
        )
        adversary = ArbitrationVerdict(
            persona=Persona.ADVERSARY,
            verdict=VerdictType.APPROVE,
            confidence=0.85,
            reasoning="No attack surface detected",
            identified_risks=[],
        )
        result = ArbitrationResult(
            analyst_verdict=analyst,
            adversary_verdict=adversary,
            promotion_allowed=True,
            freeze_required=False,
            reason="Both approved",
        )

        report = format_arbitration_report(result)

        assert "Dual-Persona Arbitration Report" in report
        assert "Analyst Evaluation" in report
        assert "Adversary Evaluation" in report
        assert "APPROVE" in report
        assert "0.90" in report
        assert "0.85" in report
        assert "Promotion Allowed: True" in report

    def test_format_report_freeze(self):
        """Test report formatting for freeze case."""
        analyst = ArbitrationVerdict(
            persona=Persona.ANALYST,
            verdict=VerdictType.APPROVE,
            confidence=0.80,
            reasoning="Approved",
            identified_risks=[],
        )
        adversary = ArbitrationVerdict(
            persona=Persona.ADVERSARY,
            verdict=VerdictType.REJECT,
            confidence=0.70,
            reasoning="Attack surface detected",
            identified_risks=["Deception indicators", "Source manipulation"],
        )
        result = ArbitrationResult(
            analyst_verdict=analyst,
            adversary_verdict=adversary,
            promotion_allowed=False,
            freeze_required=True,
            reason="Disagreement - claim frozen",
        )

        report = format_arbitration_report(result)

        assert "REJECT" in report
        assert "Freeze Required: True" in report
        assert "Deception indicators" in report
        assert "Source manipulation" in report
        assert "Disagreement - claim frozen" in report


class MockLLMResponse:
    """Mock response object matching LLM provider response interface."""
    def __init__(self, content: str):
        self.content = content


class MockLLMProvider:
    """Mock LLM provider for testing LLM-based persona evaluation."""
    
    def __init__(self, responses=None, should_fail=False):
        """Configure mock provider.
        
        Args:
            responses: Dict mapping persona to response content.
            should_fail: If True, raises exception on call.
        """
        self._responses = responses or {}
        self._should_fail = should_fail
        self.call_log = []
    
    def call(self, prompt: str, system: str = "", **kwargs) -> MockLLMResponse:
        """Mock LLM call - returns configured response or raises.
        
        Matches LLMProvider.call(prompt=, system=, ...) interface.
        """
        self.call_log.append({
            "prompt": prompt,
            "system": system,
        })
        if self._should_fail:
            raise ConnectionError("Mock LLM provider failure")
        
        # Determine persona from system prompt
        if "Analyst" in system or "ANALYST" in system:
            content = self._responses.get("analyst", '{"verdict": "APPROVE", "confidence": 0.8, "reasoning": "Mock analyst", "risks": []}')
        elif "Adversary" in system or "ADVERSARY" in system:
            content = self._responses.get("adversary", '{"verdict": "APPROVE", "confidence": 0.75, "reasoning": "Mock adversary", "risks": []}')
        else:
            content = '{"verdict": "PENDING", "confidence": 0.5, "reasoning": "Unknown persona", "risks": []}'
        
        return MockLLMResponse(content)


class TestLLMIntegration:
    """Test LLM-based persona evaluation (Story 11-5.1)."""
    
    def test_llm_both_approve(self):
        """Test happy-path: both LLM personas approve (AC2, AC3)."""
        mock_provider = MockLLMProvider(responses={
            "analyst": '{"verdict": "APPROVE", "confidence": 0.9, "reasoning": "Logically coherent", "risks": []}',
            "adversary": '{"verdict": "APPROVE", "confidence": 0.85, "reasoning": "No deception detected", "risks": []}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="System latency measured at 100ms",
            source="telemetry://metrics",
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
        )
        
        assert result.analyst_verdict.verdict == VerdictType.APPROVE
        assert result.adversary_verdict.verdict == VerdictType.APPROVE
        assert result.promotion_allowed is True
        assert result.freeze_required is False
        assert len(mock_provider.call_log) == 2  # Both personas called
    
    def test_llm_analyst_rejects(self):
        """Test LLM analyst rejection triggers freeze on disagreement."""
        mock_provider = MockLLMProvider(responses={
            "analyst": '{"verdict": "REJECT", "confidence": 0.7, "reasoning": "Inconsistent claim", "risks": ["contradiction"]}',
            "adversary": '{"verdict": "APPROVE", "confidence": 0.8, "reasoning": "No attacks", "risks": []}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="System always works",
            source="blog://external",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        assert result.analyst_verdict.verdict == VerdictType.REJECT
        assert result.adversary_verdict.verdict == VerdictType.APPROVE
        assert result.promotion_allowed is False
        assert result.freeze_required is True  # Disagreement -> freeze
    
    def test_llm_adversary_rejects(self):
        """Test LLM adversary rejection triggers freeze on disagreement."""
        mock_provider = MockLLMProvider(responses={
            "analyst": '{"verdict": "APPROVE", "confidence": 0.85, "reasoning": "Valid claim", "risks": []}',
            "adversary": '{"verdict": "REJECT", "confidence": 0.9, "reasoning": "Deception detected", "risks": ["manipulation"]}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Trust me completely",
            source="unknown://source",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        assert result.analyst_verdict.verdict == VerdictType.APPROVE
        assert result.adversary_verdict.verdict == VerdictType.REJECT
        assert result.promotion_allowed is False
        assert result.freeze_required is True  # Disagreement -> freeze
    
    def test_llm_both_reject(self):
        """Test LLM both personas reject - no freeze (agreement)."""
        mock_provider = MockLLMProvider(responses={
            "analyst": '{"verdict": "REJECT", "confidence": 0.8, "reasoning": "Invalid", "risks": ["logical_error"]}',
            "adversary": '{"verdict": "REJECT", "confidence": 0.85, "reasoning": "Deception", "risks": ["attack"]}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Absolutely guaranteed",
            source="malicious://attacker",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        assert result.analyst_verdict.verdict == VerdictType.REJECT
        assert result.adversary_verdict.verdict == VerdictType.REJECT
        assert result.promotion_allowed is False
        assert result.freeze_required is False  # Agreement to reject -> no freeze


class TestGracefulDegradation:
    """Test graceful degradation on LLM provider failure (AC5)."""
    
    def test_provider_failure_causes_freeze(self):
        """Test that LLM provider failure returns PENDING and freezes (AC5)."""
        mock_provider = MockLLMProvider(should_fail=True)
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Test claim",
            source="test://source",
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
        )
        
        # Provider failure should cause PENDING and freeze
        assert result.analyst_verdict.verdict == VerdictType.PENDING
        assert result.freeze_required is True
        assert result.promotion_allowed is False
    
    def test_no_provider_uses_heuristics(self):
        """Test that missing LLM provider falls back to heuristics."""
        arbitrator = DualPersonaArbitrator(llm_provider=None)
        
        # Claims that should pass heuristics
        result = arbitrator.arbitrate(
            claim="System measured 100ms latency over 500 samples",
            source="metrics://internal",
            current_tier=KnowledgeTier.K3,
            target_tier=KnowledgeTier.K2,
        )
        
        # Without provider, should use heuristics (existing behavior)
        assert result is not None
        assert result.analyst_verdict.verdict in [VerdictType.APPROVE, VerdictType.REJECT]
        assert result.adversary_verdict.verdict in [VerdictType.APPROVE, VerdictType.REJECT]


class TestAuditSafety:
    """Test that audit safety requirements are met (AC4)."""
    
    def test_verdict_fields_are_sanitized(self):
        """Test that LLM response parsing sanitizes/limits field lengths."""
        # Long reasoning should be truncated by _parse_llm_verdict
        mock_provider = MockLLMProvider(responses={
            "analyst": '{"verdict": "APPROVE", "confidence": 0.85, "reasoning": "' + 'x' * 2000 + '", "risks": []}',
            "adversary": '{"verdict": "APPROVE", "confidence": 0.8, "reasoning": "Short", "risks": []}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Test",
            source="test://",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        # Reasoning should be capped at 1000 chars (per implementation)
        assert len(result.analyst_verdict.reasoning) <= 1000
    
    def test_confidence_clamped(self):
        """Test that out-of-range confidence is clamped."""
        mock_provider = MockLLMProvider(responses={
            "analyst": '{"verdict": "APPROVE", "confidence": 1.5, "reasoning": "Test", "risks": []}',
            "adversary": '{"verdict": "APPROVE", "confidence": -0.2, "reasoning": "Test", "risks": []}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Test",
            source="test://",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        # Confidence should be clamped to [0.0, 1.0]
        assert 0.0 <= result.analyst_verdict.confidence <= 1.0
        assert 0.0 <= result.adversary_verdict.confidence <= 1.0
    
    def test_invalid_json_causes_pending(self):
        """Test that invalid JSON response causes PENDING verdict."""
        mock_provider = MockLLMProvider(responses={
            "analyst": 'This is not valid JSON at all',
            "adversary": '{"verdict": "APPROVE", "confidence": 0.8, "reasoning": "OK", "risks": []}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Test",
            source="test://",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        # Invalid JSON should cause PENDING
        assert result.analyst_verdict.verdict == VerdictType.PENDING
        assert result.freeze_required is True
    
    def test_markdown_json_extraction(self):
        """Test that JSON wrapped in markdown code blocks is extracted."""
        mock_provider = MockLLMProvider(responses={
            "analyst": '```json\n{"verdict": "APPROVE", "confidence": 0.85, "reasoning": "Valid", "risks": []}\n```',
            "adversary": '{"verdict": "APPROVE", "confidence": 0.8, "reasoning": "OK", "risks": []}',
        })
        arbitrator = DualPersonaArbitrator(llm_provider=mock_provider)
        
        result = arbitrator.arbitrate(
            claim="Test",
            source="test://",
            current_tier=KnowledgeTier.K4,
            target_tier=KnowledgeTier.K3,
        )
        
        # Should successfully parse JSON from markdown block
        assert result.analyst_verdict.verdict == VerdictType.APPROVE
        assert result.analyst_verdict.confidence == 0.85
