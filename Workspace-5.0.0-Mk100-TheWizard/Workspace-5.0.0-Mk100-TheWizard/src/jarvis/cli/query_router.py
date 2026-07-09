"""Query CLI command router - Thin orchestrator pattern.

The main query() function is a thin router that dispatches to mode handlers.
All heavy lifting is delegated to query_phases.py and query_council_exec.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Any

import typer

from jarvis.config import load_settings
from jarvis.memory import search
from jarvis.memory.gap_analyzer import CoverageAnalyzer, RecencyAnalyzer, CoherenceAnalyzer, GapAnalysisConfig


@dataclass
class QueryContext:
    """Context object passed through the query pipeline."""
    question: str
    k: int
    provider: str
    max_tokens: int
    json_output: bool
    show_confidence: bool
    enable_research: bool
    allow_stale: bool
    diversity: str
    
    # Resolved parameters
    effective_retriever: str = "semantic"
    effective_weight: float = 0.7
    effective_expansion: int = 0
    effective_grounding_level: str = "balanced"
    
    # Council mode
    council_mode: bool = False
    selected_personas: Optional[List[Any]] = None
    select_override: Optional[str] = None
    show_all: bool = False
    
    # Results
    results: List[Any] = None
    arches_session: Any = None
    gap_analysis: dict = None
    research_summary: dict = None
    source: Optional[str] = None


def resolve_parameters(ctx: QueryContext, settings, retriever, weight, expand, grounding_level, strict_mode, auto_grounding) -> None:
    """Resolve effective parameters into context."""
    from jarvis.cli.query_validation import resolve_effective_params, validate_query_params
    from jarvis.memory.intent_analyzer import analyze_intent
    
    ctx.effective_retriever, ctx.effective_weight, ctx.effective_expansion, ctx.effective_grounding_level = resolve_effective_params(
        retriever, weight, expand, grounding_level, strict_mode, settings
    )
    validate_query_params(ctx.k, ctx.effective_expansion, ctx.effective_retriever, ctx.effective_weight, ctx.effective_grounding_level)
    
    if auto_grounding and grounding_level is None and not strict_mode:
        intent = analyze_intent(ctx.question)
        ctx.effective_grounding_level = intent.grounding_level
        if not ctx.json_output:
            typer.echo(f"🧠 Intent: {intent.intent_type} → grounding={ctx.effective_grounding_level} (confidence={intent.confidence:.2f})")


def execute_search(ctx: QueryContext) -> bool:
    """Execute memory search phase. Returns False if no results."""
    from jarvis.cli.query_phases import execute_search as do_search, handle_no_results
    
    if not ctx.json_output:
        expansion_info = f", expand={ctx.effective_expansion}" if ctx.effective_expansion > 0 else ""
        typer.echo(f"🔍 Searching memory for context (k={ctx.k}, retriever={ctx.effective_retriever}{expansion_info})...", nl=False)
    
    domains = [ctx.source] if ctx.source else None
    ctx.results, ctx.arches_session, raw_count = do_search(
        ctx.question, ctx.k, ctx.effective_retriever, ctx.effective_weight,
        ctx.effective_expansion, domains, ctx.allow_stale, ctx.diversity, ctx.json_output
    )
    
    if not ctx.results:
        handle_no_results(ctx.question, ctx.json_output)
        return False
    
    if not ctx.json_output:
        dedup_note = f" (deduped from {raw_count})" if len(ctx.results) < raw_count else ""
        typer.echo(f" found {len(ctx.results)} chunk(s){dedup_note}")
    return True


def analyze_gaps(ctx: QueryContext, gap_config: GapAnalysisConfig) -> None:
    """Analyze gaps in search results."""
    from jarvis.arches.controller import get_controller, PlanStage
    
    arches_controller = get_controller()
    arches_controller.start_stage(ctx.arches_session, PlanStage.ASSESS)
    
    coverage = CoverageAnalyzer(gap_config).analyze(ctx.question, ctx.results)
    recency = RecencyAnalyzer(gap_config).analyze(ctx.results)
    coherence = CoherenceAnalyzer(gap_config).analyze(ctx.results)
    
    ctx.gap_analysis = {
        "coverage_score": coverage.coverage_score, "coverage_gap": coverage.gap_detected,
        "recency_status": recency.status, "recency_gap": recency.gap_detected,
        "coherence_score": coherence.coherence_score, "contradictory": coherence.contradictory,
        "missing_terms": sorted(coverage.missing_terms),
    }
    
    arches_controller.complete_stage(ctx.arches_session, PlanStage.ASSESS)
    if ctx.gap_analysis["coverage_gap"] or ctx.gap_analysis["recency_gap"]:
        arches_controller.set_flag(ctx.arches_session, "gap_detected", True)
    
    if not ctx.json_output:
        typer.echo(f"\n🩺 Gap analysis: coverage={ctx.gap_analysis['coverage_score']:.2f} | recency={ctx.gap_analysis['recency_status']} | coherence={ctx.gap_analysis['coherence_score']:.2f}")


def handle_council_mode(ctx: QueryContext) -> None:
    """Handle Council of Ricks mode - exits after completion."""
    from jarvis.cli.query_council_exec import execute_council_mode
    execute_council_mode(ctx.question, ctx.results, ctx.selected_personas, ctx.select_override, ctx.show_all, ctx.json_output)


def handle_research_mode(ctx: QueryContext, research_config) -> None:
    """Execute research planner if gaps detected."""
    from jarvis.memory.research_planner import ResearchPlanner
    from jarvis.memory.research_executor import MCPResearchExecutor
    from jarvis.memory.critical_integrator import CriticalIntegrator
    from jarvis.memory.web_search import search_web, fetch_content_from_url
    
    def _stub_llm(prompt, system, provider, max_tokens):
        lines = ctx.gap_analysis.get("missing_terms") or [ctx.question]
        return type("Resp", (), {"content": "\n".join(lines[:research_config.max_queries])})
    
    planner = ResearchPlanner(config=research_config, llm_client=_stub_llm)
    plan = planner.plan(ctx.question, ctx.gap_analysis)
    executor = MCPResearchExecutor(
        fetch_tool=lambda url, prompt: {"content": fetch_content_from_url(url)},
        search_tool=search_web, max_sources_per_query=research_config.max_queries,
    )
    execution = executor.execute(plan)
    new_chunks = [src.content for res in execution for src in res.sources if src.content]
    integrator = CriticalIntegrator(base_confidence=ctx.gap_analysis["coverage_score"])
    integration = integrator.integrate(ctx.question, [res.text for res in ctx.results], new_chunks)
    
    ctx.research_summary = {
        "triggered": True, "planned_queries": [rq.query for rq in plan.queries],
        "executed_queries": len(execution), "sources_collected": len(new_chunks),
        "confidence_after": integration.confidence_after,
    }
    if not ctx.json_output:
        typer.echo(f"🔬 Research: {len(plan.queries)} queries, {len(new_chunks)} sources")


def handle_standard_query(ctx: QueryContext) -> None:
    """Handle standard RAG query path."""
    from jarvis.cli.query_phases import build_prompts, execute_llm_call, render_json_output, render_human_output
    
    system_prompt, user_prompt, citations = build_prompts(ctx.question, ctx.results, ctx.effective_grounding_level)
    llm_response = execute_llm_call(user_prompt, system_prompt, ctx.provider, ctx.max_tokens, ctx.json_output)
    
    if ctx.json_output:
        render_json_output(ctx.question, llm_response, ctx.results, ctx.effective_grounding_level, ctx.gap_analysis, ctx.enable_research, ctx.research_summary)
    else:
        render_human_output(llm_response, citations, ctx.results, ctx.show_confidence, ctx.effective_grounding_level)
