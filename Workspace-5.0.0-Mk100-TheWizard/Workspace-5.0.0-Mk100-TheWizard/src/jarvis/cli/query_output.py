"""Output formatting for query results."""
import json
from typing import List
import typer

from jarvis.memory import search
from jarvis.memory.confidence_scorer import score_response_confidence, format_confidence_legend


def format_json_output(
    question: str,
    response: object,
    results: List[search.SearchResult],
    grounding_level: str,
    gap_analysis: dict,
    enable_research: bool,
    research_summary: dict,
) -> None:
    """Format and output JSON response."""
    sources = []
    for idx, res in enumerate(results, start=1):
        source_entry = {
            "id": idx,
            "content": res.text,
            "source_file": res.source_file,
            "section": res.section,
            "domain": (res.domain or None).replace(".", "-") if res.domain else None,
            "relevance_score": res.score,
            "score": res.score,
        }
        chunk_id = res.metadata.get("chunk_id") if res.metadata else None
        if chunk_id is not None:
            source_entry["chunk_id"] = chunk_id
        hash_value = res.metadata.get("hash") if res.metadata else None
        if hash_value is not None:
            source_entry["hash"] = hash_value
        sources.append(source_entry)

    total_tokens = response.input_tokens + response.output_tokens

    payload = {
        "query": question,
        "response": response.content,
        "sources": sources,
        "metadata": {
            "llm_provider": response.provider,
            "model": response.model,
            "total_tokens": total_tokens,
            "cost_usd": response.cost_usd,
            "grounding_level": grounding_level,
            "gap_analysis": gap_analysis,
            "research_enabled": enable_research,
            "research_summary": research_summary,
        },
    }

    typer.echo(json.dumps(payload, indent=2))


def format_text_output(
    response: object,
    results: List[search.SearchResult],
    citations: list,
    show_confidence: bool,
    grounding_level: str,
) -> None:
    """Format and output human-readable response."""
    typer.echo("\\n" + "=" * 80)
    typer.echo("📝 ANSWER")
    typer.echo("=" * 80)

    # Add in-line confidence scoring if requested
    response_text = response.content
    if show_confidence:
        response_text = score_response_confidence(
            response_text,
            results,
            grounding_level,
        )

    typer.echo(response_text)

    if show_confidence:
        typer.echo("\\n" + format_confidence_legend())

    typer.echo("\\n" + "-" * 80)
    typer.echo("📚 SOURCES")
    typer.echo("-" * 80)
    for cite in citations:
        typer.echo(f"[{cite['id']}] score={cite['score']:.3f}")
        if cite["source_file"]:
            typer.echo(f"    {cite['source_file']}", nl=False)
            if cite["section"]:
                typer.echo(f" (section: {cite['section']})")
            else:
                typer.echo()
        elif cite["domain"]:
            typer.echo(f"    domain: {cite['domain']}")
        typer.echo()

    typer.echo("-" * 80)
    typer.echo(
        f"🔧 {response.provider} ({response.model}) | "
        f"{response.input_tokens + response.output_tokens} tokens | "
        f"${response.cost_usd:.4f}"
    )
