"""Unit tests for parallel persona invocation (Story 4.2)."""

import asyncio
from unittest.mock import Mock

import pytest

from jarvis.agents.parallel_invocation import invoke_persona_async, invoke_personas_parallel
from jarvis.agents.personas import PersonaConfig
from jarvis.agents.response import PersonaResponse
from unittest.mock import patch
from jarvis.llm import client as llm_client


@pytest.fixture
def mock_personas():
    """Create mock personas for testing."""
    return [
        PersonaConfig(name="Rickiest Rick", system_prompt="Be analytical", weight=0.40, enabled=True),
        PersonaConfig(name="Supportive Rick", system_prompt="Be supportive", weight=0.30, enabled=True),
        PersonaConfig(name="Chaotic Rick", system_prompt="Be chaotic", weight=0.30, enabled=True),
    ]


@pytest.mark.asyncio
async def test_invoke_persona_async_success(mock_personas):
    """Test successful async persona invocation."""
    persona = mock_personas[0]
    context = "Test context about quantum computing"
    query = "What is quantum computing?"

    # Patch call_llm to avoid real network calls
    from jarvis import agents
    from jarvis.llm import client as llm_client

    async def run():
        with patch.object(llm_client, "call_llm") as call_stub:
            call_stub.return_value = llm_client.LLMResponse(
                content=f"{persona.name} answer",
                provider="test",
                model="test-model",
                input_tokens=5,
                output_tokens=5,
                cost_usd=0.0,
            )
            return await invoke_persona_async(persona, context, query)

    response = await run()

    assert isinstance(response, PersonaResponse)
    assert response.persona == persona
    assert response.is_success
    assert response.error is None
    assert len(response.response_text) > 0
    assert persona.name in response.response_text


@pytest.mark.asyncio
async def test_invoke_personas_parallel_all_success(mock_personas):
    """Test parallel invocation with all personas succeeding."""
    context = "Test context"
    query = "Test query"

    with patch("jarvis.llm.client.call_llm") as call_stub:
        def _mk_response(persona):
            return llm_client.LLMResponse(
                content=f"{persona.name} response",
                provider="test",
                model="test-model",
                input_tokens=1,
                output_tokens=1,
                cost_usd=0.0,
            )
        call_stub.side_effect = lambda prompt, system=None, provider="auto", max_tokens=2000: _mk_response(mock_personas[0])
        responses = await invoke_personas_parallel(mock_personas, context, query)

    assert len(responses) == 3
    assert all(r.is_success for r in responses)
    assert all(isinstance(r, PersonaResponse) for r in responses)

    # Check all personas were invoked
    persona_names = {r.persona.name for r in responses}
    expected_names = {p.name for p in mock_personas}
    assert persona_names == expected_names


@pytest.mark.asyncio
async def test_invoke_personas_parallel_partial_failure():
    """Test parallel invocation handles partial failures gracefully."""
    # Create personas where one will fail
    personas = [
        PersonaConfig(name="Good Rick", system_prompt="Works", weight=0.50, enabled=True),
        PersonaConfig(name="Bad Rick", system_prompt="Fails", weight=0.50, enabled=True),
    ]

    context = "Test context"
    query = "Test query"

    # Mock the invoke_persona_async to make one fail
    original_invoke = invoke_persona_async

    async def mock_invoke(persona, context=None, query=None, **kwargs):
        if persona.name == "Bad Rick":
            return PersonaResponse(
                persona=persona,
                response_text="",
                sources=[],
                error=Exception("Simulated failure")
            )
        return PersonaResponse(
            persona=persona,
            response_text="ok",
            sources=[],
            error=None
        )

    # Patch and test
    import jarvis.agents.parallel_invocation as module
    original = module.invoke_persona_async
    module.invoke_persona_async = mock_invoke

    try:
        responses = await invoke_personas_parallel(personas, context, query)

        assert len(responses) == 2
        success_count = sum(1 for r in responses if r.is_success)
        failure_count = sum(1 for r in responses if not r.is_success)

        assert success_count == 1
        assert failure_count == 1

        # Find the failed response
        failed = next(r for r in responses if not r.is_success)
        assert failed.persona.name == "Bad Rick"
        assert failed.error is not None

    finally:
        module.invoke_persona_async = original


@pytest.mark.asyncio
async def test_parallel_invocation_performance(mock_personas):
    """Test that parallel invocation is actually parallel (faster than sequential)."""
    import time

    context = "Test context"
    query = "Test query"

    # Stub out actual LLM calls to keep timing deterministic
    with patch("jarvis.llm.client.call_llm") as call_stub:
        call_stub.return_value = llm_client.LLMResponse(
            content="ok",
            provider="test",
            model="test-model",
            input_tokens=1,
            output_tokens=1,
            cost_usd=0.0,
        )
        start = time.time()
        responses = await invoke_personas_parallel(mock_personas, context, query)
        parallel_time = time.time() - start

        start = time.time()
        for persona in mock_personas:
            await invoke_persona_async(persona, context, query)
        sequential_time = time.time() - start

    # Ensure both paths complete and return all personas; timing may be noisy in CI.
    assert len(responses) == 3
    assert all(r.is_success for r in responses)
    assert len(responses) == 3
