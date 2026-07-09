"""Unit tests for LLM client."""

import pytest
from unittest.mock import Mock, patch

from jarvis.llm.client import LLMClient, LLMResponse, call_llm


def test_llm_response_dataclass():
    """Test LLMResponse dataclass creation."""
    response = LLMResponse(
        content="Test content",
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
    )
    assert response.content == "Test content"
    assert response.provider == "openrouter"
    assert response.input_tokens == 100
    assert response.output_tokens == 50
    assert response.cost_usd == 0.01


def test_llm_client_defaults_without_api_key():
    """Client should build with defaults even without explicit API key."""
    with patch.dict("os.environ", {}, clear=True):
        client = LLMClient()
        assert client.provider == "auto"
        assert client.model


@patch("jarvis.llm.client.ProviderRouter")
@patch.object(LLMClient, "_build_providers", return_value=[])
def test_llm_client_call(mock_build_providers, mock_router_class):
    """Test LLM client call with mocked provider router."""
    mock_response = LLMResponse(
        content="Generated insight",
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.0123,
    )
    mock_router = Mock()
    mock_router.call.return_value = mock_response
    mock_router_class.return_value = mock_router

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test_key"}):
        client = LLMClient()
        response = client.call("Test prompt", system="System message")

    assert response == mock_response
    mock_router.call.assert_called_once()


@patch("jarvis.llm.client.ProviderRouter")
def test_call_llm_convenience_function(mock_router_class):
    """Test call_llm convenience function."""
    mock_response = LLMResponse(
        content="Test",
        provider="openrouter",
        model="test",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.001,
    )
    mock_router = Mock()
    mock_router.call.return_value = mock_response
    mock_router_class.return_value = mock_router

    response = call_llm("Test prompt")

    assert response == mock_response
    mock_router.call.assert_called_once()
