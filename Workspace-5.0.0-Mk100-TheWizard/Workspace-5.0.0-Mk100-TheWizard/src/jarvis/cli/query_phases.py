"""Query CLI execution phases - Separated for LOC compliance.

Contains major execution blocks extracted from the query command.
"""
from __future__ import annotations

import json
from typing import Optional, List, Any
from pathlib import Path

import typer

from jarvis.memory import search
from jarvis.llm.client import call_llm
from jarvis.arches.controller import get_controller, PlanStage


def execute_search(
    question: str,
    k: int,
    effective_retriever: str,
    effective_weight: float,
    effective_expansion: int,
    domains: Optional[List[str]],
    allow_stale: bool,
    diversity: str,
    json_output: bool,
) -> tuple[List[Any], Any, int]:
    """Execute memory search phase. Returns (results, arches_session, raw_count)."""
    arches_controller = get_controller()
    arches_session = arches_controller.start_session(query=question)
    arches_controller.start_stage(arches_session, PlanStage.HYBRID)

    try:
        if effective_expansion > 0:
            results = search.expanded_search(
                question, k=k, expansion_count=effective_expansion,
                domains=domains, retriever=effective_retriever, weight=effective_weight,
            )
        elif effective_retriever == "semantic":
            results = search.search_memory(question, k=k, domains=domains, allow_stale=allow_stale, diversity_mode=diversity)
        elif effective_retriever == "keyword":
            results = search.keyword_search(question, k=k, domains=domains, allow_stale=allow_stale)
        else:
            results = search.hybrid_search(question, k=k, weight=effective_weight, domains=domains, allow_stale=allow_stale, diversity_mode=diversity)
    except Exception as exc:
        typer.echo(f"\n❌ Memory search failed: {exc}", err=True)
        raise typer.Exit(code=1)

    raw_count = len(results)
    results = search.deduplicate_results(results)
    arches_controller.complete_stage(arches_session, PlanStage.HYBRID)
    arches_controller.record_memory_usage(arches_session, results, domains=domains)

    return results, arches_session, raw_count


def handle_no_results(question: str, json_output: bool) -> None:
    """Handle case when no results found."""
    if json_output:
        payload = {
            "query": question, "response": None, "sources": [],
            "metadata": {"status": "insufficient_context", "llm_provider": None, "model": None, "total_tokens": 0, "cost_usd": 0.0},
        }
        typer.echo(json.dumps(payload, indent=2))
        raise typer.Exit(code=0)
    typer.echo("\n⚠️  No relevant context found in memory.")
    typer.echo("Tip: Ingest more documents with 'jarvis memory add <path>'")
    raise typer.Exit(code=1)


def build_prompts(
    question: str,
    results: List[Any],
    effective_grounding_level: str,
) -> tuple[str, str, List[dict]]:
    """Build system prompt, user prompt, and citations list."""
    context_parts = []
    citations = []

    for idx, res in enumerate(results, start=1):
        source_ref = f"[{idx}]"
        if res.source_file:
            source_info = f"{res.source_file}"
            if res.section:
                source_info += f" (section: {res.section})"
            source_ref += f" {source_info}"
        elif res.domain:
            source_ref += f" domain:{res.domain.replace('.', '-')}"

        citations.append({
            "id": idx, "source_file": res.source_file, "section": res.section,
            "domain": (res.domain or "").replace(".", "-") if res.domain else None, "score": round(res.score, 3),
        })
        context_parts.append(f"[Source {idx}]\n{res.text.strip()}")

    context_block = "\n\n".join(context_parts)

    system_prompt = """You are JARVIS, an AI advisor with access to a curated knowledge base.
Answer the user's question based ONLY on the provided context sources.
- Cite sources using [1], [2], etc. when referencing specific information.
- If the context doesn't contain enough information, say so clearly.
"""
    if effective_grounding_level == "soft":
        system_prompt += "\nGROUNDING LEVEL: SOFT - Be creative, tie claims to sources."
    elif effective_grounding_level == "balanced":
        system_prompt += "\nGROUNDING LEVEL: BALANCED - Cite sources for claims."
    elif effective_grounding_level == "strict":
        system_prompt += "\nGROUNDING LEVEL: STRICT - Do NOT invent facts. If insufficient, say so."

    user_prompt = f"""Context from knowledge base:

{context_block}

---

Question: {question}

Answer the question based on the context above, citing sources where appropriate:"""

    return system_prompt, user_prompt, citations


def execute_llm_call(
    user_prompt: str,
    system_prompt: str,
    provider: str,
    max_tokens: int,
    json_output: bool,
) -> Any:
    """Execute LLM call phase."""
    if not json_output:
        typer.echo(f"🤖 Generating answer (provider={provider})...", nl=False)

    try:
        llm_response = call_llm(prompt=user_prompt, system=system_prompt, provider=provider, max_tokens=max_tokens)
    except Exception as exc:
        typer.echo(f"\n❌ LLM call failed: {exc}", err=True)
        raise typer.Exit(code=1)

    if not json_output:
        typer.echo(" done")

    return llm_response


def render_json_output(
    question: str,
    llm_response: Any,
    results: List[Any],
    effective_grounding_level: str,
    gap_analysis: dict,
    enable_research: bool,
    research_summary: Optional[dict],
) -> None:
    """Render JSON output."""
    sources = []
    for idx, res in enumerate(results, start=1):
        source_entry = {
            "id": idx, "content": res.text, "source_file": res.source_file,
            "section": res.section, "domain": (res.domain or "").replace(".", "-") if res.domain else None,
            "relevance_score": res.score, "score": res.score,
        }
        chunk_id = res.metadata.get("chunk_id") if res.metadata else None
        if chunk_id is not None:
            source_entry["chunk_id"] = chunk_id
        hash_value = res.metadata.get("hash") if res.metadata else None
        if hash_value is not None:
            source_entry["hash"] = hash_value
        sources.append(source_entry)

    total_tokens = llm_response.input_tokens + llm_response.output_tokens
    payload = {
        "query": question, "response": llm_response.content, "sources": sources,
        "metadata": {
            "llm_provider": llm_response.provider, "model": llm_response.model,
            "total_tokens": total_tokens, "cost_usd": llm_response.cost_usd,
            "grounding_level": effective_grounding_level, "gap_analysis": gap_analysis,
            "research_enabled": enable_research, "research_summary": research_summary,
        },
    }
    typer.echo(json.dumps(payload, indent=2))
    raise typer.Exit(code=0)


def render_human_output(
    llm_response: Any,
    citations: List[dict],
    results: List[Any],
    show_confidence: bool,
    effective_grounding_level: str,
) -> None:
    """Render human-readable output."""
    from jarvis.agents.confidence_scorer import score_response_confidence, format_confidence_legend

    typer.echo("\n" + "=" * 80)
    typer.echo("📝 ANSWER")
    typer.echo("=" * 80)

    response_text = llm_response.content
    if show_confidence:
        response_text = score_response_confidence(response_text, results, effective_grounding_level)

    typer.echo(response_text)

    if show_confidence:
        typer.echo("\n" + format_confidence_legend())

    typer.echo("\n" + "-" * 80)
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
        f"🔧 {llm_response.provider} ({llm_response.model}) | "
        f"{llm_response.input_tokens + llm_response.output_tokens} tokens | "
        f"${llm_response.cost_usd:.4f}"
    )
    raise typer.Exit(code=0)
