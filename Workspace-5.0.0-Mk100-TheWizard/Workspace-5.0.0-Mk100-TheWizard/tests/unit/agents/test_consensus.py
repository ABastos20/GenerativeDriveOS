"""Unit tests for weighted chaos voting engine (Story 4.3)."""

import pytest

from jarvis.agents.consensus import VotingResult, weighted_chaos_vote, get_winner_response
from jarvis.agents.personas import PersonaConfig
from jarvis.agents.response import PersonaResponse


@pytest.fixture
def mock_personas():
    """Create mock personas with different weights."""
    return [
        PersonaConfig(name="Rickiest Rick", system_prompt="Analytical", weight=0.40, enabled=True),
        PersonaConfig(name="Balanced Rick", system_prompt="Balanced", weight=0.30, enabled=True),
        PersonaConfig(name="Supportive Rick", system_prompt="Supportive", weight=0.20, enabled=True),
        PersonaConfig(name="Chaotic Rick", system_prompt="Chaotic", weight=0.10, enabled=True),
    ]


def test_weighted_voting_clear_winner(mock_personas):
    """Test voting with clear winner (highest weight persona succeeds)."""
    responses = [
        PersonaResponse(mock_personas[0], "Rickiest response", ["src1"], None),
        PersonaResponse(mock_personas[1], "Balanced response", ["src2"], None),
        PersonaResponse(mock_personas[2], "Supportive response", ["src3"], None),
        PersonaResponse(mock_personas[3], "Chaotic response", ["src4"], None),
    ]

    result = weighted_chaos_vote(responses)

    assert isinstance(result, VotingResult)
    assert result.winner == "Rickiest Rick"
    assert result.scores["Rickiest Rick"] == 0.40
    assert result.scores["Balanced Rick"] == 0.30
    assert not result.has_tie
    assert result.total_personas == 4


def test_weighted_voting_with_tie(mock_personas):
    """Test voting when two personas have equal weights (tie scenario)."""
    # Create 2 personas with same weight
    tie_personas = [
        PersonaConfig(name="Rick A", system_prompt="A", weight=0.50, enabled=True),
        PersonaConfig(name="Rick B", system_prompt="B", weight=0.50, enabled=True),
    ]

    responses = [
        PersonaResponse(tie_personas[0], "Response A", [], None),
        PersonaResponse(tie_personas[1], "Response B", [], None),
    ]

    result = weighted_chaos_vote(responses, tie_threshold=0.05)

    # Both should be tied
    assert result.has_tie
    assert len(result.ties) == 2
    assert "Rick A" in result.ties
    assert "Rick B" in result.ties
    assert result.scores["Rick A"] == result.scores["Rick B"]


def test_weighted_voting_single_persona(mock_personas):
    """Test voting with single persona (100% weight Winner)."""
    responses = [
        PersonaResponse(mock_personas[0], "Only response", ["src1"], None),
    ]

    result = weighted_chaos_vote(responses)

    assert result.winner == "Rickiest Rick"
    assert result.scores["Rickiest Rick"] == 0.40
    assert not result.has_tie
    assert result.total_personas == 1


def test_weighted_voting_partial_failure(mock_personas):
    """Test voting when one persona fails (gets 0 score)."""
    responses = [
        PersonaResponse(mock_personas[0], "Success", ["src1"], None),  # 0.40 weight
        PersonaResponse(mock_personas[1], "", [], Exception("Failed")),  # 0 score (failed)
        PersonaResponse(mock_personas[2], "Success", ["src2"], None),  # 0.20 weight
    ]

    result = weighted_chaos_vote(responses)

    assert result.winner == "Rickiest Rick"  # Highest weight success
    assert result.scores["Rickiest Rick"] == 0.40
    assert result.scores["Balanced Rick"] == 0.0  # Failed persona gets 0
    assert result.scores["Supportive Rick"] == 0.20


def test_get_winner_response(mock_personas):
    """Test retrieving winner PersonaResponse object."""
    responses = [
        PersonaResponse(mock_personas[0], "Rickiest response", ["src1"], None),
        PersonaResponse(mock_personas[1], "Balanced response", ["src2"], None),
    ]

    result = weighted_chaos_vote(responses)
    winner_response = get_winner_response(responses, result)

    assert winner_response.persona.name == result.winner
    assert winner_response.response_text == "Rickiest response"
    assert winner_response.is_success


def test_get_winner_response_not_found(mock_personas):
    """Test error when winner not in responses."""
    responses = [
        PersonaResponse(mock_personas[0], "Response", [], None),
    ]

    # Create fake voting result with non-existent winner
    fake_result = VotingResult(
        winner="NonExistent Rick",
        scores={"NonExistent Rick": 1.0},
        ties=[],
        total_personas=1
    )

    with pytest.raises(ValueError, match="Winner persona .* not found"):
        get_winner_response(responses, fake_result)
