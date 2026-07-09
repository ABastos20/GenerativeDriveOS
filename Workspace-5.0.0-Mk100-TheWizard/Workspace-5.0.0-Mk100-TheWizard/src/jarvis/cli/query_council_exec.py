"""Council of Ricks execution - Separated for LOC compliance.

Contains the entire Council mode execution block extracted from query command.
"""
from __future__ import annotations

import asyncio
import json
from typing import List, Optional, Any

import typer

from jarvis.agents.personas import PersonaConfig
from jarvis.agents.parallel_invoker import invoke_personas_parallel
from jarvis.agents.voting import weighted_chaos_vote, get_winner_response
from jarvis.agents.aggregator import aggregate_responses, select_persona_response


def execute_council_mode(
    question: str,
    results: List[Any],
    selected_personas: List[PersonaConfig],
    select_override: Optional[str],
    show_all: bool,
    json_output: bool,
) -> None:
    """Execute Council of Ricks mode - parallel personas, voting, and persistence."""
    # Build context for personas
    context_parts = [f"[Source]\n{res.text.strip()}" for res in results]
    context_for_personas = "\n\n".join(context_parts)

    if not json_output:
        typer.echo(f"\n🌀 Invoking {len(selected_personas)} personas in parallel...")

    # Step 1: Parallel invocation
    persona_responses = asyncio.run(
        invoke_personas_parallel(selected_personas, context_for_personas, question)
    )

    # Step 2: Weighted voting
    voting_result = weighted_chaos_vote(persona_responses)

    # Step 3: Manual override or consensus
    if select_override:
        final_response = select_persona_response(persona_responses, select_override)
        if not json_output:
            typer.echo(f"\n👤 Manual override: using '{select_override}' response")
    else:
        final_response = get_winner_response(persona_responses, voting_result)
        if not json_output:
            typer.echo(f"\n🏆 Consensus winner: '{voting_result.winner}' (score: {voting_result.scores[voting_result.winner]:.2f})")

    # Step 4: Display aggregated response
    aggregated_view = aggregate_responses(persona_responses, voting_result, show_all=show_all)

    if json_output:
        _output_council_json(question, final_response, voting_result, persona_responses, select_override)
    else:
        typer.echo("\n" + "=" * 80)
        typer.echo(aggregated_view)
        typer.echo("=" * 80)

    # Step 5: Persist to database
    _persist_council_conversation(question, final_response, voting_result, persona_responses, select_override, json_output)

    raise typer.Exit(code=0)


def _output_council_json(question, final_response, voting_result, persona_responses, select_override):
    """Output JSON for council mode."""
    payload = {
        "query": question,
        "response": final_response.response_text,
        "council_mode": True,
        "winner": final_response.persona.name,
        "voting_metadata": {
            "winner": voting_result.winner,
            "scores": voting_result.scores,
            "total_personas": voting_result.total_personas,
            "manual_override": select_override,
        },
        "metadata": {
            "status": "success",
            "personas_invoked": len(persona_responses),
            "successful_responses": sum(1 for r in persona_responses if r.is_success),
        },
    }
    typer.echo(json.dumps(payload, indent=2))


def _persist_council_conversation(question, final_response, voting_result, persona_responses, select_override, json_output):
    """Persist council conversation to database."""
    if not json_output:
        typer.echo("\n💾 Saving conversation...")

    try:
        from jarvis.database.models import Message, Conversation
        from jarvis.database.postgres import get_session

        with get_session() as session:
            conversation = Conversation()
            session.add(conversation)
            session.flush()

            user_message = Message(
                conversation_id=conversation.id, role="user", content=question, agent_persona=None,
            )
            session.add(user_message)

            voting_metadata = {
                "winner": voting_result.winner,
                "scores": {k: float(v) for k, v in voting_result.scores.items()},
                "total_personas": voting_result.total_personas,
                "personas_invoked": [p.persona.name for p in persona_responses],
                "successful_responses": sum(1 for r in persona_responses if r.is_success),
                "failed_responses": sum(1 for r in persona_responses if not r.is_success),
            }

            if select_override:
                voting_metadata["manual_override"] = select_override
                voting_metadata["override_reason"] = "user_selected"

            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=final_response.response_text,
                agent_persona=final_response.persona.name,
                voting_metadata=voting_metadata,
            )
            session.add(assistant_message)
            session.flush()

            if not json_output:
                typer.echo(f"✅ Conversation saved (ID: {conversation.id})")

    except Exception as exc:
        typer.echo(f"\n⚠️  Warning: Failed to save conversation: {exc}", err=True)
