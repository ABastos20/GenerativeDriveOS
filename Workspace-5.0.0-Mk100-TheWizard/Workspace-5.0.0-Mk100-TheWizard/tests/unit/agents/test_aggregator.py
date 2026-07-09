"""Unit tests for response aggregation and override UX (Story 4.4)."""

import pytest

from jarvis.agents.aggregator import aggregate_responses, select_persona_response
from jarvis.agents.consensus import VotingResult
from jarvis.agents.personas import PersonaConfig
from jarvis.agents.response import PersonaResponse


@pytest.fixture
def mock_responses():
    """Create mock persona responses for testing."""
    personas = [
        PersonaConfig(name="Rickiest Rick", system_prompt="Analytical", weight=0.40, enabled=True),
        PersonaConfig(name="Supportive Rick", system_prompt="Supportive", weight=0.30, enabled=True),
        PersonaConfig(name="Chaotic Rick", system_prompt="Chaotic", weight=0.30, enabled=True),
    ]

    return [
        PersonaResponse(personas[0], "Rickiest response about quantum computing", ["source1"], None),
        PersonaResponse(personas[1], "Supportive response about quantum computing", ["source2"], None),
        PersonaResponse(personas[2], "Chaotic response about quantum computing", ["source3"], None),
    ]


@pytest.fixture
def mock_voting_result():
    """Create mock voting result."""
    return VotingResult(
        winner="Rickiest Rick",
        scores={"Rickiest Rick": 0.40, "Supportive Rick": 0.30, "Chaotic Rick": 0.30},
        ties=[],
        total_personas=3
    )


def test_aggregate_responses_show_winner_only(mock_responses, mock_voting_result):
    """Test aggregation with show_all=False (winner only)."""
    output = aggregate_responses(mock_responses, mock_voting_result, show_all=False)

    assert "COUNCIL OF RICKS RESPONSE" in output
    assert "Rickiest Rick" in output
    assert "40%" in output  # Winner weight
    assert "Rickiest response about quantum computing" in output
    assert "source1" in output

    # Should NOT show other personas
    assert "Supportive Rick" not in output
    assert "Chaotic Rick" not in output

    # Should have hint to show all
    assert "--show-all" in output


def test_aggregate_responses_show_all(mock_responses, mock_voting_result):
    """Test aggregation with show_all=True (all personas)."""
    output = aggregate_responses(mock_responses, mock_voting_result, show_all=True)

    assert "COUNCIL OF RICKS RESPONSE" in output

    # All personas should be shown
    assert "Rickiest Rick" in output
    assert "Supportive Rick" in output
    assert "Chaotic Rick" in output

    # All responses
    assert "Rickiest response" in output
    assert "Supportive response" in output
    assert "Chaotic response" in output

    # Voting breakdown
    assert "Voting Results:" in output
    assert "0.40" in output  # Rickiest score
    assert "0.30" in output  # Other scores

    # Override hint
    assert "--select" in output


def test_aggregate_responses_with_failure(mock_voting_result):
    """Test aggregation handles failed persona gracefully."""
    personas = [
        PersonaConfig(name="Good Rick", system_prompt="Works", weight=0.60, enabled=True),
        PersonaConfig(name="Bad Rick", system_prompt="Fails", weight=0.40, enabled=True),
    ]

    responses = [
        PersonaResponse(personas[0], "Success response", ["src1"], None),
        PersonaResponse(personas[1], "", [], Exception("API failed")),
    ]

    # Update voting result to reflect failure
    voting_result = VotingResult(
        winner="Good Rick",
        scores={"Good Rick": 0.60, "Bad Rick": 0.0},
        ties=[],
        total_personas=2
    )

    output = aggregate_responses(responses, voting_result, show_all=True)

    assert "Good Rick" in output
    assert "Bad Rick" in output
    assert "❌ Failed" in output or "API failed" in output


def test_select_persona_response_success(mock_responses):
    """Test successful persona selection."""
    selected = select_persona_response(mock_responses, "Supportive Rick")

    assert selected.persona.name == "Supportive Rick"
    assert selected.response_text == "Supportive response about quantum computing"
    assert selected.is_success


def test_select_persona_response_not_found(mock_responses):
    """Test error when selecting non-existent persona."""
    with pytest.raises(ValueError, match="Persona .* not found"):
        select_persona_response(mock_responses, "NonExistent Rick")


def test_select_persona_response_failed_persona():
    """Test error when selecting a failed persona."""
    personas = [
        PersonaConfig(name="Failed Rick", system_prompt="Fails", weight=1.0, enabled=True),
    ]

    responses = [
        PersonaResponse(personas[0], "", [], Exception("Failed")),
    ]

    with pytest.raises(ValueError, match="persona invocation failed"):
        select_persona_response(responses, "Failed Rick")
