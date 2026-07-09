"""Memory retrieval execution."""
from typing import Optional, List
import typer

from jarvis.memory import search
from jarvis.arches.controller import ARCHESController, PlanStage


def execute_memory_retrieval(
    question: str,
    k: int,
    retriever: str,
    weight: float,
    expansion: int,
    source: Optional[str],
    allow_stale: bool,
    diversity: str,
    arches_controller: ARCHESController,
    arches_session: object,
    json_output: bool,
) -> List[search.SearchResult]:
    """Execute memory retrieval with proper ARCHES tracking.
    
    Returns:
        List of search results
        
    Raises:
        typer.Exit: If retrieval fails
    """
    if not json_output:
        expansion_info = f", expand={expansion}" if expansion > 0 else ""
        typer.echo(
            f"🔍 Searching memory for context (k={k}, retriever={retriever}{expansion_info})...",
            nl=False,
        )

    domains = [source] if source else None

    # Start HYBRID stage
    arches_controller.start_stage(arches_session, PlanStage.HYBRID)

    try:
        # Use expanded_search if query expansion is enabled
        if expansion > 0:
            results = search.expanded_search(
                question,
                k=k,
                expansion_count=expansion,
                domains=domains,
                retriever=retriever,
                weight=weight,
            )
        else:
            # Standard retrieval (no expansion)
            if retriever == "semantic":
                results = search.search_memory(question, k=k, domains=domains, allow_stale=allow_stale, diversity_mode=diversity)
            elif retriever == "keyword":
                results = search.keyword_search(question, k=k, domains=domains, allow_stale=allow_stale)
            else:
                results = search.hybrid_search(
                    question,
                    k=k,
                    weight=weight,
                    domains=domains,
                    allow_stale=allow_stale,
                    diversity_mode=diversity,
                )
    except Exception as exc:
        typer.echo(f"\\n❌ Memory search failed: {exc}", err=True)
        raise typer.Exit(code=1)

    raw_result_count = len(results)
    results = search.deduplicate_results(results)

    # Complete HYBRID stage and record memory usage
    arches_controller.complete_stage(arches_session, PlanStage.HYBRID)
    arches_controller.record_memory_usage(arches_session, results, domains=domains)

    if not json_output:
        dedup_note = ""
        if len(results) < raw_result_count:
            dedup_note = f" (deduped from {raw_result_count})"
        typer.echo(f" found {len(results)} chunk(s){dedup_note}")

    return results
