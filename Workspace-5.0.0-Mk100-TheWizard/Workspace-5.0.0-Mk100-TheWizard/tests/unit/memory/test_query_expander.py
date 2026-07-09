"""Unit tests for query expansion logic."""

from __future__ import annotations

import pytest

from jarvis.memory.query_expander import expand_query


class TestExpandQuery:
    """Test suite for expand_query function."""

    def test_expand_query_generates_correct_count(self):
        """Verify expansion_count parameter is respected."""
        result = expand_query("How do I optimize PostgreSQL?", count=2)
        # Should return original + 2 expansions = 3 total
        assert len(result) == 3, f"Expected 3 results, got {len(result)}"
        assert result[0] == "How do I optimize PostgreSQL?"

    def test_expand_query_includes_original(self):
        """Original query must always be first in expansion list."""
        original = "What is RAG?"
        result = expand_query(original, count=3)
        assert result[0] == original
        assert len(result) >= 1

    def test_expand_query_zero_count_returns_original_only(self):
        """expansion_count=0 should return only original query."""
        result = expand_query("Test query", count=0)
        assert len(result) == 1
        assert result[0] == "Test query"

    def test_expand_query_synonym_replacement(self):
        """Test synonym replacement for common technical terms."""
        result = expand_query("How to optimize the system", count=3)
        # Should contain original
        assert "How to optimize the system" in result
        # Should generate some variants (exact content depends on implementation)
        assert len(result) > 1

    def test_expand_query_question_reformulation(self):
        """Test question reformulation patterns."""
        # "How do I X?" should generate "Steps to X", "X tutorial", etc.
        result = expand_query("How do I configure Qdrant?", count=3)
        assert "How do I configure Qdrant?" in result
        # Check that at least one expansion was generated
        assert len(result) > 1

    def test_expand_query_validates_count_range(self):
        """Raise ValueError for count outside valid range [0, 5]."""
        with pytest.raises(ValueError, match="count must be between 0 and 5"):
            expand_query("Test", count=-1)

        with pytest.raises(ValueError, match="count must be between 0 and 5"):
            expand_query("Test", count=10)

    def test_expand_query_empty_input_returns_original(self):
        """Empty or whitespace-only input should return original."""
        result = expand_query("", count=2)
        assert len(result) == 1
        assert result[0] == ""

        result = expand_query("   ", count=2)
        assert len(result) == 1
        assert result[0] == "   "

    def test_expand_query_what_is_pattern(self):
        """Test 'What is X?' question pattern reformulation."""
        result = expand_query("What is Docker?", count=3)
        assert "What is Docker?" in result
        # Implementation should generate variants like "Docker definition", "about Docker"
        assert len(result) > 1

    def test_expand_query_max_count_five(self):
        """Test that count=5 generates up to 5 expansions."""
        result = expand_query("How to debug Python?", count=5)
        # Should return original + up to 5 expansions
        assert len(result) >= 1
        assert len(result) <= 6  # Original + 5 expansions max

    def test_expand_query_deduplication(self):
        """Ensure no duplicate expansions in result list."""
        result = expand_query("How to test APIs?", count=5)
        # All entries should be unique
        assert len(result) == len(set(result))

    def test_expand_query_preserves_case_in_original(self):
        """Original query case should be preserved."""
        original = "How Do I OPTIMIZE PostgreSQL?"
        result = expand_query(original, count=2)
        assert result[0] == original

    def test_expand_query_no_expansions_for_short_query(self):
        """Very short queries should still return original + attempts."""
        result = expand_query("RAG", count=2)
        assert result[0] == "RAG"
        # Implementation may or may not generate expansions for single-word query
        assert len(result) >= 1
