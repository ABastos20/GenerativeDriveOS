"""Unit tests for jarvis query CLI command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from jarvis.cli import query as query_cli
from jarvis.llm.client import LLMResponse
from jarvis.memory.search import SearchResult

runner = CliRunner()


@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return [
        SearchResult(
            text="Sample text from document 1",
            score=0.95,
            source_file="docs/example1.md",
            section="Introduction",
            domain="jarvis-core",
            metadata={"chunk_id": "chunk-1"},
        ),
        SearchResult(
            text="Sample text from document 2",
            score=0.87,
            source_file="docs/example2.md",
            section=None,
            domain="jarvis-conversations",
            metadata={"chunk_id": "chunk-2"},
        ),
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return LLMResponse(
        content="This is a test answer citing sources [1] and [2].",
        provider="openrouter",
        model="test-model",
        input_tokens=150,
        output_tokens=50,
        cost_usd=0.0,
    )


class TestQueryParameterValidation:
    """Test query parameter validation."""

    def test_k_parameter_too_low(self):
        """Test k parameter below valid range."""
        result = runner.invoke(query_cli.app, ["test query", "--k", "0"])
        assert result.exit_code == 1
        assert "k must be between 1 and 20" in result.output

    def test_k_parameter_too_high(self):
        """Test k parameter above valid range."""
        result = runner.invoke(query_cli.app, ["test query", "--k", "21"])
        assert result.exit_code == 1
        assert "k must be between 1 and 20" in result.output

    def test_k_parameter_valid_range(self):
        """Test k parameter within valid range."""
        # Should pass validation (will fail on search, but that's expected)
        with patch("jarvis.memory.search.search_memory", return_value=[]):
            result = runner.invoke(query_cli.app, ["test query", "--k", "10"])
            # Exits with 1 because no results, but k validation passed
            assert "k must be between" not in result.stdout


class TestContextBuilding:
    """Test context building and citation formatting."""

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_context_includes_all_results(
        self, mock_search, mock_llm, mock_dedup, mock_controller, mock_search_results, mock_llm_response
    ):
        """Test that context block includes all search results."""
        mock_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query"])

        # Verify call_llm was called with context from both results
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        prompt = call_args.kwargs["prompt"]

        assert "[Source 1]" in prompt
        assert "[Source 2]" in prompt
        assert "Sample text from document 1" in prompt
        assert "Sample text from document 2" in prompt

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_citations_formatted_correctly(
        self, mock_search, mock_llm, mock_dedup, mock_controller, mock_search_results, mock_llm_response
    ):
        """Test citation formatting in output."""
        mock_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query"])

        assert result.exit_code == 0
        assert "📚 SOURCES" in result.stdout
        assert "[1] score=0.950" in result.stdout
        assert "[2] score=0.870" in result.stdout
        assert "docs/example1.md" in result.stdout
        assert "docs/example2.md" in result.stdout


class TestJSONOutput:
    """Test JSON output format."""

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_json_output_structure(
        self, mock_search, mock_llm, mock_dedup, mock_controller, mock_search_results, mock_llm_response
    ):
        """Test JSON envelope structure matches PRD."""
        mock_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query", "--json-output"])

        assert result.exit_code == 0
        # Verify it's valid JSON
        import json

        data = json.loads(result.stdout)

        # Verify required fields
        assert "query" in data
        assert "response" in data
        assert "sources" in data
        assert "metadata" in data

        # Verify metadata structure
        assert "llm_provider" in data["metadata"]
        assert "model" in data["metadata"]
        assert "total_tokens" in data["metadata"]
        assert "cost_usd" in data["metadata"]

        # Verify sources structure
        assert len(data["sources"]) == 2
        assert "id" in data["sources"][0]
        assert "content" in data["sources"][0]
        assert "source_file" in data["sources"][0]
        assert "relevance_score" in data["sources"][0]
        assert "score" in data["sources"][0]


class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    @patch("jarvis.memory.search.search_memory")
    def test_no_search_results(self, mock_search):
        """Test graceful handling when no results found."""
        mock_search.return_value = []

        result = runner.invoke(query_cli.app, ["test query"])

        assert result.exit_code == 1
        assert "No relevant context found" in result.stdout
        assert "jarvis memory add" in result.stdout  # Helpful guidance

    @patch("jarvis.memory.search.search_memory")
    def test_no_search_results_json_output(self, mock_search):
        """Test JSON envelope when no results found."""
        mock_search.return_value = []

        result = runner.invoke(query_cli.app, ["test query", "--json-output"])

        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert data["query"] == "test query"
        assert data["response"] is None
        assert data["sources"] == []
        assert data["metadata"]["status"] == "insufficient_context"

    @patch("jarvis.memory.search.search_memory")
    def test_search_failure(self, mock_search):
        """Test handling of search failures."""
        mock_search.side_effect = Exception("Qdrant connection failed")

        result = runner.invoke(query_cli.app, ["test query"])

        assert result.exit_code == 1
        assert "Memory search failed" in result.output

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_llm_failure(self, mock_search, mock_llm, mock_dedup, mock_controller, mock_search_results):
        """Test handling of LLM call failures."""
        mock_search.return_value = mock_search_results
        mock_llm.side_effect = Exception("LLM provider unavailable")

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query"])

        assert result.exit_code == 1
        assert "LLM call failed" in result.output


class TestProviderRouting:
    """Test provider parameter handling."""

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_auto_provider_routing(
        self, mock_search, mock_llm, mock_dedup, mock_controller, mock_search_results, mock_llm_response
    ):
        """Test that auto provider routing is used by default."""
        mock_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query"])

        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        assert call_args.kwargs["provider"] == "auto"

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_explicit_provider(
        self, mock_search, mock_llm, mock_dedup, mock_controller, mock_search_results, mock_llm_response
    ):
        """Test explicit provider selection."""
        mock_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query", "--provider", "local-claude"])

        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        assert call_args.kwargs["provider"] == "local-claude"


class TestRetrieverModes:
    """Test retriever and weight parameter handling."""

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_default_retriever_uses_semantic(
        self,
        mock_search_memory: MagicMock,
        mock_llm: MagicMock,
        mock_dedup: MagicMock,
        mock_controller: MagicMock,
        mock_search_results,
        mock_llm_response,
    ):
        mock_search_memory.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query"])

        assert result.exit_code == 0
        mock_search_memory.assert_called_once()
        
    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.keyword_search")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_keyword_retriever_uses_keyword_search(
        self,
        mock_search_memory: MagicMock,
        mock_keyword_search: MagicMock,
        mock_llm: MagicMock,
        mock_dedup: MagicMock,
        mock_controller: MagicMock,
        mock_search_results,
        mock_llm_response,
    ):
        mock_keyword_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query", "--retriever", "keyword"])

        assert result.exit_code == 0
        mock_keyword_search.assert_called_once()
        mock_search_memory.assert_not_called()

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.hybrid_search")
    def test_hybrid_retriever_uses_hybrid_search(
        self,
        mock_hybrid_search: MagicMock,
        mock_llm: MagicMock,
        mock_dedup: MagicMock,
        mock_controller: MagicMock,
        mock_search_results,
        mock_llm_response,
    ):
        mock_hybrid_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(
            query_cli.app,
            ["test query", "--retriever", "hybrid", "--weight", "0.6"],
        )

        assert result.exit_code == 0
        mock_hybrid_search.assert_called_once()
        call_args = mock_hybrid_search.call_args
        assert call_args.kwargs["weight"] == 0.6

    def test_invalid_retriever_value(self):
        result = runner.invoke(query_cli.app, ["test query", "--retriever", "unknown"])
        assert result.exit_code == 1
        assert "Invalid retriever" in result.output

    def test_invalid_weight_for_hybrid(self):
        result = runner.invoke(
            query_cli.app,
            ["test query", "--retriever", "hybrid", "--weight", "1.5"],
        )
        assert result.exit_code == 1
        assert "weight must be between 0.0 and 1.0" in result.output


class TestStrictMode:
    """Test strict-mode behaviour wiring."""

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.search_memory")
    def test_strict_mode_appends_strict_instructions(
        self,
        mock_search_memory: MagicMock,
        mock_llm: MagicMock,
        mock_dedup: MagicMock,
        mock_controller: MagicMock,
        mock_search_results,
        mock_llm_response,
    ):
        mock_search_memory.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(query_cli.app, ["test query", "--strict-mode"])

        assert result.exit_code == 0
        mock_llm.assert_called_once()
        system_text = mock_llm.call_args.kwargs["system"]
        assert "GROUNDING LEVEL: STRICT" in system_text


class TestQueryExpansionCLI:
    """Tests for --expand query expansion wiring."""

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.expanded_search")
    def test_expand_flag_uses_expanded_search(
        self,
        mock_expanded_search: MagicMock,
        mock_llm: MagicMock,
        mock_dedup: MagicMock,
        mock_controller: MagicMock,
        mock_search_results,
        mock_llm_response,
    ):
        """--expand should route through expanded_search with given count."""
        mock_expanded_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(
            query_cli.app,
            ["test query", "--expand", "2"],
        )

        assert result.exit_code == 0
        mock_expanded_search.assert_called_once()
        call_args = mock_expanded_search.call_args
        # expansion_count comes from CLI --expand
        assert call_args.kwargs["expansion_count"] == 2
        # default retriever is semantic when not overridden
        assert call_args.kwargs["retriever"] == "semantic"

    @patch("jarvis.cli.query_phases.get_controller")
    @patch("jarvis.cli.query_phases.search.deduplicate_results", side_effect=lambda x: x)
    @patch("jarvis.cli.query_phases.call_llm")
    @patch("jarvis.cli.query_phases.search.expanded_search")
    def test_expand_flag_with_hybrid_retriever_and_weight(
        self,
        mock_expanded_search: MagicMock,
        mock_llm: MagicMock,
        mock_dedup: MagicMock,
        mock_controller: MagicMock,
        mock_search_results,
        mock_llm_response,
    ):
        """--expand should preserve retriever and weight parameters."""
        mock_expanded_search.return_value = mock_search_results
        mock_llm.return_value = mock_llm_response

        # Mock controller session
        mock_session = MagicMock()
        mock_controller.return_value.start_session.return_value = mock_session

        result = runner.invoke(
            query_cli.app,
            [
                "test query",
                "--retriever",
                "hybrid",
                "--weight",
                "0.6",
                "--expand",
                "3",
            ],
        )

        assert result.exit_code == 0
        mock_expanded_search.assert_called_once()
        call_args = mock_expanded_search.call_args
        assert call_args.kwargs["retriever"] == "hybrid"
        assert call_args.kwargs["weight"] == 0.6
        assert call_args.kwargs["expansion_count"] == 3

    def test_invalid_expand_value_too_low(self):
        """--expand below 0 should be rejected."""
        result = runner.invoke(query_cli.app, ["test query", "--expand", "-1"])
        assert result.exit_code == 1
        assert "--expand must be between 0 and 5" in result.output

    def test_invalid_expand_value_too_high(self):
        """--expand above 5 should be rejected."""
        result = runner.invoke(query_cli.app, ["test query", "--expand", "6"])
        assert result.exit_code == 1
        assert "--expand must be between 0 and 5" in result.output
