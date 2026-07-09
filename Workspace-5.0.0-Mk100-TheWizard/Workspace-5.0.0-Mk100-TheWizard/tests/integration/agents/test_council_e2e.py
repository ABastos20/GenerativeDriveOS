"""Integration test for Council of Ricks E2E flow (Stories 4.2-4.4).

This test validates the complete flow:
query → parallel invocation → voting → display → override
"""

import asyncio

import pytest

from jarvis.agents.aggregator import aggregate_responses, select_persona_response
from jarvis.agents.consensus import weighted_chaos_vote, get_winner_response
from jarvis.agents.parallel_invocation import invoke_personas_parallel
from jarvis.agents.personas import PersonaConfig


@pytest.fixture
def test_personas():
    """Create test personas for E2E flow."""
    return [
        PersonaConfig(name="Rickiest Rick", system_prompt="Analytical", weight=0.40, enabled=True),
        PersonaConfig(name="Supportive Rick", system_prompt="Supportive", weight=0.30, enabled=True),
        PersonaConfig(name="Chaotic Rick", system_prompt="Chaotic", weight=0.30, enabled=True),
    ]


@pytest.mark.asyncio
async def test_council_of_ricks_e2e_flow(test_personas):
    """Test complete Council of Ricks flow from query to final response."""
    query = "What is quantum computing?"
    context = "Quantum computing is a type of computing that uses quantum mechanics..."

    # Step 1: Parallel invocation
    persona_responses = await invoke_personas_parallel(test_personas, context, query)

    assert len(persona_responses) == 3
    assert all(r.is_success for r in persona_responses)

    # Step 2: Voting
    voting_result = weighted_chaos_vote(persona_responses)

    assert voting_result.winner == "Rickiest Rick"  # Highest weight
    assert voting_result.total_personas == 3

    # Step 3: Get winner response
    winner_response = get_winner_response(persona_responses, voting_result)

    assert winner_response.persona.name == "Rickiest Rick"
    assert winner_response.is_success

    # Step 4: Aggregation display (winner only)
    aggregated_winner = aggregate_responses(persona_responses, voting_result, show_all=False)

    assert "Rickiest Rick" in aggregated_winner
    assert "COUNCIL OF RICKS" in aggregated_winner
    assert "--show-all" in aggregated_winner  # Hint to show all

    # Step 5: Aggregation display (show all)
    aggregated_all = aggregate_responses(persona_responses, voting_result, show_all=True)

    assert "Rickiest Rick" in aggregated_all
    assert "Supportive Rick" in aggregated_all
    assert "Chaotic Rick" in aggregated_all
    assert "Voting Results:" in aggregated_all
    assert "--select" in aggregated_all  # Override hint


@pytest.mark.asyncio
async def test_council_override_flow(test_personas):
    """Test manual override flow (--select flag)."""
    query = "Test query"
    context = "Test context"

    # Step 1-2: Invocation and voting
    persona_responses = await invoke_personas_parallel(test_personas, context, query)
    voting_result = weighted_chaos_vote(persona_responses)

    # Winner should be Rickiest Rick (highest weight)
    assert voting_result.winner == "Rickiest Rick"

    # Step 3: Override with manual selection
    overridden = select_persona_response(persona_responses, "Supportive Rick")

    assert overridden.persona.name == "Supportive Rick"
    assert overridden != get_winner_response(persona_responses, voting_result)


@pytest.mark.asyncio
async def test_council_partial_failure_flow(test_personas):
    """Test Council of Ricks handles partial failures gracefully."""
    from jarvis.agents.response import PersonaResponse

    query = "Test query"
    context = "Test context"

    # Simulate partial failure: second persona fails
    persona_responses = await invoke_personas_parallel(test_personas, context, query)
    
    # Override second response with failure
    persona_responses[1] = PersonaResponse(
        persona=test_personas[1],
        response_text="",
        sources=[],
        error=Exception("Simulated failure")
    )

    # Voting should still work
    voting_result = weighted_chaos_vote(persona_responses)

    # Winner should be Rickiest Rick (only successful with highest weight)
    assert voting_result.winner == "Rickiest Rick"
    assert voting_result.scores["Supportive Rick"] == 0.0  # Failed persona gets 0

    # Aggregation should display failure
    aggregated = aggregate_responses(persona_responses, voting_result, show_all=True)

    assert "❌ Failed" in aggregated or "Simulated failure" in aggregated
