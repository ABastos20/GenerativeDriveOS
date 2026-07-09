"""Unit tests for memory compilation service."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from jarvis.memory.compile import (
    CompilationResult,
    compile_memories,
    _format_date_range,
    _build_compilation_prompt,
)
from jarvis.llm.client import LLMResponse


def test_format_date_range():
    """Test date range formatting."""
    since = datetime(2025, 11, 1, tzinfo=timezone.utc)
    until = datetime(2025, 11, 30, tzinfo=timezone.utc)
    result = _format_date_range(since, until)
    assert result == "2025-11-01 to 2025-11-30"


def test_build_compilation_prompt_empty():
    """Test prompt building with no conversations."""
    prompt = _build_compilation_prompt([])
    assert "No conversations to analyze" in prompt


def test_build_compilation_prompt_with_conversations():
    """Test prompt building with mock conversations."""
    mock_conv = Mock()
    mock_conv.id = "test-id"
    mock_conv.created_at = datetime(2025, 11, 1, tzinfo=timezone.utc)

    mock_msg = Mock()
    mock_msg.role = "user"
    mock_msg.content = "Test message"
    mock_conv.messages = [mock_msg]

    prompt = _build_compilation_prompt([mock_conv])

    assert "Conversation test-id" in prompt
    assert "Test message" in prompt
    assert "Key Themes" in prompt


@patch("jarvis.memory.compile.get_session_factory")
@patch("jarvis.memory.compile.call_llm")
@patch("jarvis.memory.compile.ingest_file")
def test_compile_memories_no_conversations(mock_ingest, mock_call_llm, mock_session_factory):
    """Test compile_memories with no conversations in date range."""
    # Mock database session with no conversations
    mock_session = Mock()
    mock_session.query.return_value.filter.return_value.all.return_value = []
    mock_session.query.return_value.join.return_value.filter.return_value.count.return_value = 0
    mock_session_factory.return_value = Mock(return_value=mock_session)

    since = datetime(2025, 11, 1, tzinfo=timezone.utc)
    until = datetime(2025, 11, 30, tzinfo=timezone.utc)

    result = compile_memories(since, until, output_dir=Path("/tmp/test"), auto_ingest=False)

    assert result.conversation_count == 0
    assert result.message_count == 0
    assert result.output_file.exists()
    mock_call_llm.assert_not_called()
    mock_ingest.assert_not_called()


@patch("jarvis.memory.compile.get_session_factory")
@patch("jarvis.memory.compile.call_llm")
@patch("jarvis.memory.compile.ingest_file")
def test_compile_memories_with_conversations(mock_ingest, mock_call_llm, mock_session_factory):
    """Test compile_memories with mock conversations and LLM response."""
    # Mock database session with conversations
    mock_conv = Mock()
    mock_conv.id = "test-id"
    mock_conv.created_at = datetime(2025, 11, 1, tzinfo=timezone.utc)
    mock_msg = Mock()
    mock_msg.role = "user"
    mock_msg.content = "Test message"
    mock_conv.messages = [mock_msg]

    mock_session = Mock()
    mock_session.query.return_value.filter.return_value.all.return_value = [mock_conv]
    mock_session.query.return_value.join.return_value.filter.return_value.count.return_value = 1
    mock_session_factory.return_value = Mock(return_value=mock_session)

    # Mock LLM response
    mock_llm_response = LLMResponse(
        content="# Key Themes\n\nTest insights",
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
    )
    mock_call_llm.return_value = mock_llm_response

    # Mock ingestion
    mock_ingest_result = Mock()
    mock_ingest_result.chunks = 5
    mock_ingest_result.points_written = 5
    mock_ingest.return_value = mock_ingest_result

    since = datetime(2025, 11, 1, tzinfo=timezone.utc)
    until = datetime(2025, 11, 30, tzinfo=timezone.utc)

    result = compile_memories(since, until, output_dir=Path("/tmp/test"), auto_ingest=True)

    assert result.conversation_count == 1
    assert result.message_count == 1
    assert result.llm_response == mock_llm_response
    assert result.ingestion_result == mock_ingest_result
    assert result.output_file.exists()

    # Verify LLM was called
    mock_call_llm.assert_called_once()

    # Verify ingestion was triggered
    mock_ingest.assert_called_once()
    call_kwargs = mock_ingest.call_args[1]
    assert call_kwargs["domain"] == "jarvis-insights"
