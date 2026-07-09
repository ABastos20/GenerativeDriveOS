"""Response aggregation and display formatting for Council of Ricks (Story 4.4).

Enhanced with memory attribution for Story 4.5.2:
- Display per-agent chunk/domain usage in --show-all mode
"""

from typing import List

from jarvis.agents.consensus import VotingResult
from jarvis.agents.response import PersonaResponse


def aggregate_responses(
    responses: List[PersonaResponse],
    voting_result: VotingResult,
    show_all: bool = False
) -> str:
    """Aggregate persona responses into formatted display string.

    Args:
        responses: List of all PersonaResponse objects from parallel invocation
        voting_result: Result from weighted_chaos_vote()
        show_all: If True, display all persona responses. If False, show only winner.

    Returns:
        Formatted string with response aggregation
    """
    output = []

    # Header
    output.append("=" * 80)
    output.append("🎭 COUNCIL OF RICKS RESPONSE")
    output.append("=" * 80)

    if show_all:
        # Display voting results summary
        output.append("")
        output.append(f"🏆 Selected Winner: {voting_result.winner} (weight: {voting_result.scores[voting_result.winner]:.0%})")

        if voting_result.has_tie:
            output.append(f"⚠️  Tie detected: {', '.join(voting_result.ties)}")

        output.append("")
        output.append("-" * 80)

        # Display all persona responses
        for response in responses:
            persona_name = response.persona.name
            weight = response.persona.weight
            score = voting_result.scores.get(persona_name, 0.0)

            # Mark winner
            winner_marker = "👑 " if persona_name == voting_result.winner else "   "

            output.append("")
            output.append(f"{winner_marker}[{persona_name} - Weight: {weight:.0%} | Score: {score:.2f}]")

            if response.is_success:
                output.append(response.response_text)
                if response.sources:
                    output.append(f"Sources: {', '.join(response.sources)}")
                
                # Memory Attribution (Story 4.5.2)
                if response.memory_attribution:
                    attr = response.memory_attribution
                    output.append("")
                    output.append(f"📚 Memory Attribution:")
                    output.append(f"   Chunks cited: {len(attr.chunks_used)}/{attr.total_chunks_available}")
                    if attr.domains_accessed:
                        output.append(f"   Domains: {', '.join(attr.domains_accessed)}")
                    if attr.sources:
                        output.append(f"   Sources: {', '.join(attr.sources[:3])}{'...' if len(attr.sources) > 3 else ''}")
                    output.append(f"   Freshness: {attr.memory_freshness:.0%}")
            else:
                output.append(f"❌ Failed: {response.error}")

            output.append("-" * 40)

        # Voting breakdown with attribution summary (Story 4.5.2)
        output.append("")
        output.append("📊 Voting Results:")
        sorted_personas = sorted(voting_result.scores.items(), key=lambda x: x[1], reverse=True)
        for persona_name, score in sorted_personas:
            # Add attribution summary if available
            attr_info = ""
            if persona_name in voting_result.attribution:
                attr = voting_result.attribution[persona_name]
                chunks_cited = len(attr.get("chunks_used", []))
                total_chunks = attr.get("total_chunks_available", 0)
                if total_chunks > 0:
                    attr_info = f" [cited {chunks_cited}/{total_chunks} chunks]"
            output.append(f"  {persona_name}: {score:.2f}{attr_info}")

        # Override hint
        output.append("")
        output.append("💡 To select a different response: jarvis query \"<query>\" --select \"<persona_name>\"")

    else:
        # Show winner only
        winner_response = next(r for r in responses if r.persona.name == voting_result.winner)

        output.append("")
        output.append(f"Selected Persona: {voting_result.winner} (weight: {voting_result.scores[voting_result.winner]:.0%})")
        output.append("")
        output.append(winner_response.response_text)

        if winner_response.sources:
            output.append("")
            output.append(f"Sources: {', '.join(winner_response.sources)}")

        # Hint to show all
        output.append("")
        output.append("💡 To see all persona responses: add --show-all flag")

    output.append("")
    output.append("=" * 80)

    return "\\n".join(output)


def select_persona_response(
    responses: List[PersonaResponse],
    selected_persona_name: str
) -> PersonaResponse:
    """Select a specific persona's response by name (manual override).

    Args:
        responses: List of all PersonaResponse objects
        selected_persona_name: Name of persona to select

    Returns:
        PersonaResponse for the selected persona

    Raises:
        ValueError: If persona name not found or persona failed
    """
    # Find matching persona
    for response in responses:
        if response.persona.name == selected_persona_name:
            if not response.is_success:
                raise ValueError(
                    f"Cannot select '{selected_persona_name}': persona invocation failed. "
                    f"Error: {response.error}"
                )
            return response

    # Persona not found - provide helpful error
    available_names = [r.persona.name for r in responses]
    raise ValueError(
        f"Persona '{selected_persona_name}' not found. "
        f"Available personas: {', '.join(available_names)}"
    )
