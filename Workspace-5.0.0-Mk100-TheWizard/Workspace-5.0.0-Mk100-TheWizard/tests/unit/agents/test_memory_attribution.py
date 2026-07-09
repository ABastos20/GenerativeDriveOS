"""Unit tests for memory attribution in Council of Ricks (Story 4.5.2)."""

import pytest
from unittest.mock import MagicMock

from jarvis.agents.response import MemoryAttribution, PersonaResponse
from jarvis.agents.personas import PersonaConfig
from jarvis.agents.parallel_invocation import (
    _build_attributed_context,
    _extract_used_chunks,
)
from jarvis.agents.consensus import weighted_chaos_vote, VotingResult


# === Test MemoryAttribution Dataclass (AC#1) ===


class TestMemoryAttribution:
    """Tests for MemoryAttribution dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        attr = MemoryAttribution()
        assert attr.chunks_used == []
        assert attr.domains_accessed == []
        assert attr.sources == []
        assert attr.memory_freshness == 0.0
        assert attr.total_chunks_available == 0

    def test_to_dict(self):
        """Test JSON serialization."""
        attr = MemoryAttribution(
            chunks_used=["chunk1", "chunk2"],
            domains_accessed=["domain-a"],
            sources=["doc1.md"],
            memory_freshness=0.85,
            total_chunks_available=5,
        )
        result = attr.to_dict()
        assert result["chunks_used"] == ["chunk1", "chunk2"]
        assert result["domains_accessed"] == ["domain-a"]
        assert result["sources"] == ["doc1.md"]
        assert result["memory_freshness"] == 0.85
        assert result["total_chunks_available"] == 5
        assert result["citation_rate"] == 0.4  # 2/5

    def test_citation_rate_zero_chunks(self):
        """Test citation rate with zero available chunks."""
        attr = MemoryAttribution(
            chunks_used=["chunk1"],
            total_chunks_available=0,
        )
        result = attr.to_dict()
        assert result["citation_rate"] == 1.0  # 1/max(0,1)


class TestPersonaResponseAttribution:
    """Tests for PersonaResponse with memory attribution."""

    def _make_persona(self, name: str = "Test Persona") -> PersonaConfig:
        return PersonaConfig(
            name=name,
            system_prompt="Test prompt",
            weight=1.0,
            enabled=True,
        )

    def test_response_with_attribution(self):
        """Test PersonaResponse includes memory attribution."""
        attr = MemoryAttribution(
            chunks_used=["chunk1"],
            domains_accessed=["domain-a"],
            sources=["source.md"],
            memory_freshness=0.9,
        )
        response = PersonaResponse(
            persona=self._make_persona(),
            response_text="Test response",
            sources=[],
            memory_attribution=attr,
        )
        assert response.chunks_used == ["chunk1"]
        assert response.domains_accessed == ["domain-a"]
        assert response.memory_freshness == 0.9

    def test_response_without_attribution(self):
        """Test PersonaResponse gracefully handles null attribution."""
        response = PersonaResponse(
            persona=self._make_persona(),
            response_text="Test response",
            sources=[],
            memory_attribution=None,
        )
        assert response.chunks_used == []
        assert response.domains_accessed == []
        assert response.memory_freshness == 0.0


# === Test Context Building (AC#2, #3) ===


class TestBuildAttributedContext:
    """Tests for _build_attributed_context function."""

    def test_no_chunks_returns_original(self):
        """Test with no chunks returns original context."""
        context = "Some context"
        result, chunk_map = _build_attributed_context(context, None)
        assert result == context
        assert chunk_map == {}

    def test_empty_chunks_returns_original(self):
        """Test with empty chunks list returns original context."""
        context = "Some context"
        result, chunk_map = _build_attributed_context(context, [])
        assert result == context
        assert chunk_map == {}

    def test_chunks_with_id_attribute(self):
        """Test chunks with 'id' attribute are properly mapped."""
        chunk = MagicMock()
        chunk.id = "abc123"
        chunk.text = "Chunk content"
        chunk.metadata = {"primary_domain": "test-domain", "doc_key": "doc1.md"}

        attributed, chunk_map = _build_attributed_context("", [chunk])

        assert "[Source 1 | Chunk ID: abc123]" in attributed
        assert "Chunk content" in attributed
        assert "1" in chunk_map
        assert chunk_map["1"]["chunk_id"] == "abc123"
        assert chunk_map["1"]["domain"] == "test-domain"
        assert chunk_map["1"]["source"] == "doc1.md"

    def test_chunks_with_point_id_attribute(self):
        """Test chunks with 'point_id' attribute (Qdrant)."""
        chunk = MagicMock()
        chunk.id = None
        chunk.point_id = "qdrant-point-456"
        chunk.text = "Qdrant chunk"
        chunk.metadata = {}
        # Remove 'id' attribute to trigger point_id fallback
        del chunk.id

        attributed, chunk_map = _build_attributed_context("", [chunk])

        assert "[Source 1 | Chunk ID: qdrant-point-456]" in attributed

    def test_dict_chunks(self):
        """Test dict-based chunks."""
        chunk = {
            "id": "dict-chunk-1",
            "text": "Dict chunk content",
            "metadata": {"domain": "dict-domain"},
        }

        attributed, chunk_map = _build_attributed_context("", [chunk])

        assert "[Source 1 | Chunk ID: dict-chunk-1]" in attributed
        assert chunk_map["1"]["domain"] == "dict-domain"


# === Test Citation Extraction (AC#4) ===


class TestExtractUsedChunks:
    """Tests for _extract_used_chunks function."""

    def test_empty_chunk_map(self):
        """Test with empty chunk map returns empty attribution."""
        result = _extract_used_chunks("Some response", {})
        assert result.chunks_used == []
        assert result.total_chunks_available == 0

    def test_numeric_citations(self):
        """Test extraction of [1], [2] style citations."""
        chunk_map = {
            "1": {"chunk_id": "chunk-a", "domain": "domain-a", "source": "doc1.md", "freshness": 0.9},
            "2": {"chunk_id": "chunk-b", "domain": "domain-b", "source": "doc2.md", "freshness": 0.8},
            "3": {"chunk_id": "chunk-c", "domain": "domain-c", "source": "doc3.md", "freshness": 0.7},
        }
        content = "Based on [1] and [2], the answer is..."

        result = _extract_used_chunks(content, chunk_map)

        assert set(result.chunks_used) == {"chunk-a", "chunk-b"}
        assert set(result.domains_accessed) == {"domain-a", "domain-b"}
        assert len(result.sources) == 2
        assert result.total_chunks_available == 3

    def test_source_prefix_citations(self):
        """Test extraction of [Source 1] style citations."""
        chunk_map = {
            "1": {"chunk_id": "chunk-1", "domain": "d1", "source": "s1", "freshness": 1.0},
        }
        content = "According to [Source 1], we can see..."

        result = _extract_used_chunks(content, chunk_map)

        assert result.chunks_used == ["chunk-1"]

    def test_freshness_averaging(self):
        """Test that memory_freshness is averaged correctly."""
        chunk_map = {
            "1": {"chunk_id": "c1", "domain": "d1", "source": "s1", "freshness": 0.8},
            "2": {"chunk_id": "c2", "domain": "d2", "source": "s2", "freshness": 0.6},
        }
        content = "Using [1] and [2]..."

        result = _extract_used_chunks(content, chunk_map)

        assert result.memory_freshness == 0.7  # (0.8 + 0.6) / 2

    def test_no_citations_found(self):
        """Test response with no citations."""
        chunk_map = {
            "1": {"chunk_id": "c1", "domain": "d1", "source": "s1", "freshness": 1.0},
        }
        content = "This response doesn't cite anything specific."

        result = _extract_used_chunks(content, chunk_map)

        assert result.chunks_used == []
        assert result.memory_freshness == 0.0


# === Test Voting with Attribution (AC#5) ===


class TestVotingAttribution:
    """Tests for voting result with memory attribution."""

    def _make_persona(self, name: str, weight: float = 1.0) -> PersonaConfig:
        return PersonaConfig(
            name=name,
            system_prompt=f"Prompt for {name}",
            weight=weight,
            enabled=True,
        )

    def test_voting_includes_attribution(self):
        """Test that voting result includes per-agent attribution."""
        attr1 = MemoryAttribution(chunks_used=["c1"], domains_accessed=["d1"])
        attr2 = MemoryAttribution(chunks_used=["c1", "c2"], domains_accessed=["d1", "d2"])

        responses = [
            PersonaResponse(
                persona=self._make_persona("Persona A", 0.8),
                response_text="Response A",
                sources=[],
                memory_attribution=attr1,
            ),
            PersonaResponse(
                persona=self._make_persona("Persona B", 1.0),
                response_text="Response B",
                sources=[],
                memory_attribution=attr2,
            ),
        ]

        result = weighted_chaos_vote(responses)

        assert "Persona A" in result.attribution
        assert "Persona B" in result.attribution
        assert result.attribution["Persona A"]["chunks_used"] == ["c1"]
        assert result.attribution["Persona B"]["chunks_used"] == ["c1", "c2"]

    def test_voting_handles_null_attribution(self):
        """Test voting handles responses without attribution."""
        responses = [
            PersonaResponse(
                persona=self._make_persona("Persona A"),
                response_text="Response A",
                sources=[],
                memory_attribution=None,
            ),
        ]

        result = weighted_chaos_vote(responses)

        assert "Persona A" in result.attribution
        assert result.attribution["Persona A"]["chunks_used"] == []
