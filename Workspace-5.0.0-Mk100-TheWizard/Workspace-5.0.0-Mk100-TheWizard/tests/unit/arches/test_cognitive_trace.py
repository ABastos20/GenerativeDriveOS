"""Unit tests for Cognitive Trace System (Story 4.5.6).

Tests:
- CognitiveTrace dataclass serialization
- to_dict/from_dict roundtrip
- Persistence functions (with mock session)
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from jarvis.arches.trace import (
    CognitiveTrace,
    RetrievedChunkTrace,
    AgentTrace,
    ResearchCallTrace,
)


class TestRetrievedChunkTrace:
    """Tests for RetrievedChunkTrace dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        chunk = RetrievedChunkTrace(
            chunk_id="chunk-123",
            doc_key="doc::test.pdf",
            version=2,
            domain="engineering",
            score_before_mmr=0.95,
            score_after_mmr=0.87,
            freshness_score=0.75,
        )
        
        d = chunk.to_dict()
        
        assert d["chunk_id"] == "chunk-123"
        assert d["doc_key"] == "doc::test.pdf"
        assert d["version"] == 2
        assert d["score_before_mmr"] == 0.95
        assert d["freshness_score"] == 0.75


class TestAgentTrace:
    """Tests for AgentTrace dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        agent = AgentTrace(
            name="Architect Rick",
            role="architect",
            input_summary="User asked about system design",
            output_summary="Suggested microservices approach",
            vote=0.85,
            latency_ms=150,
            model_name="gpt-4",
        )
        
        d = agent.to_dict()
        
        assert d["name"] == "Architect Rick"
        assert d["role"] == "architect"
        assert d["vote"] == 0.85
        assert d["latency_ms"] == 150


class TestResearchCallTrace:
    """Tests for ResearchCallTrace dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        call = ResearchCallTrace(
            query="best practices for API design",
            provider="web-search",
            success=True,
            duration_ms=350,
            results_count=10,
            meta={"engine": "bing"},
        )
        
        d = call.to_dict()
        
        assert d["query"] == "best practices for API design"
        assert d["provider"] == "web-search"
        assert d["success"] is True
        assert d["meta"]["engine"] == "bing"


class TestCognitiveTrace:
    """Tests for CognitiveTrace dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        trace = CognitiveTrace()
        
        assert trace.trace_id is not None
        assert trace.mode == "qa"
        assert trace.arches_version == "4.5.6"
        assert trace.trace_schema_version == 1
        assert trace.severity == "normal"
        assert trace.sampled is True
        assert trace.started_at is not None

    def test_to_dict(self):
        """Should convert to dictionary with all fields."""
        trace = CognitiveTrace(
            query="How does memory work?",
            mode="research",
            session_id="session-123",
        )
        
        d = trace.to_dict()
        
        assert "trace_id" in d
        assert d["query"] == "How does memory work?"
        assert d["mode"] == "research"
        assert d["session_id"] == "session-123"

    def test_to_json(self):
        """Should convert to JSON string."""
        trace = CognitiveTrace(query="test query")
        
        json_str = trace.to_json()
        
        assert isinstance(json_str, str)
        assert "test query" in json_str
        assert "trace_id" in json_str

    def test_from_dict_roundtrip(self):
        """Should roundtrip through to_dict/from_dict."""
        original = CognitiveTrace(
            query="What is ARCHES?",
            mode="qa",
            session_id="sess-456",
            diversity_mode="aggressive",
            k_initial=50,
            k_final=10,
        )
        original.add_phase_timing("retrieval_ms", 42)
        original.add_phase_timing("council_ms", 128)
        
        # Roundtrip
        d = original.to_dict()
        restored = CognitiveTrace.from_dict(d)
        
        assert str(restored.trace_id) == str(original.trace_id)
        assert restored.query == original.query
        assert restored.mode == original.mode
        assert restored.diversity_mode == original.diversity_mode
        assert restored.k_initial == 50
        assert restored.k_final == 10
        assert restored.phase_timings["retrieval_ms"] == 42
        assert restored.phase_timings["council_ms"] == 128

    def test_finalize_sets_timing(self):
        """finalize() should set completed_at and total_latency_ms."""
        trace = CognitiveTrace()
        
        # Simulate some processing time
        import time
        time.sleep(0.01)  # 10ms minimum
        
        trace.finalize()
        
        assert trace.completed_at is not None
        assert trace.total_latency_ms is not None
        assert trace.total_latency_ms >= 10

    def test_add_error_updates_severity(self):
        """add_error() should update severity to error."""
        trace = CognitiveTrace()
        assert trace.severity == "normal"
        
        trace.add_error("Something went wrong")
        
        assert trace.severity == "error"
        assert "Something went wrong" in trace.errors

    def test_with_nested_objects(self):
        """Should handle nested retrieval_events, agents, research_calls."""
        trace = CognitiveTrace(query="complex query")
        
        # Add retrieval events
        trace.retrieval_events.append(RetrievedChunkTrace(
            chunk_id="c1",
            doc_key="doc1",
            version=1,
            domain="eng",
            score_before_mmr=0.9,
            score_after_mmr=0.85,
        ))
        
        # Add agent
        trace.agents.append(AgentTrace(
            name="Rick",
            role="architect",
            input_summary="input",
            output_summary="output",
            vote=0.9,
            latency_ms=100,
            model_name="gpt-4",
        ))
        
        # Add research call
        trace.research_calls.append(ResearchCallTrace(
            query="search",
            provider="web",
            success=True,
            duration_ms=200,
            results_count=5,
        ))
        
        # Roundtrip
        d = trace.to_dict()
        restored = CognitiveTrace.from_dict(d)
        
        assert len(restored.retrieval_events) == 1
        assert restored.retrieval_events[0].chunk_id == "c1"
        assert len(restored.agents) == 1
        assert restored.agents[0].name == "Rick"
        assert len(restored.research_calls) == 1
        assert restored.research_calls[0].provider == "web"


class TestCognitiveTraceConstants:
    """Tests for module constants."""

    def test_arches_version(self):
        """ARCHES version should be 4.5.6."""
        trace = CognitiveTrace()
        assert trace.arches_version == "4.5.6"

    def test_schema_version(self):
        """Schema version should be 1."""
        trace = CognitiveTrace()
        assert trace.trace_schema_version == 1
