"""RAG query command - Epic 3 Story 3.1.

THIN ROUTER PATTERN: This file contains only:
1. Typer CLI arguments and decorators
2. Router logic that delegates to query_router.py handlers

All heavy lifting is in query_router.py, query_phases.py, query_council_exec.py.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import typer

from jarvis.config import load_settings
from jarvis.memory import search
from jarvis.memory.gap_analyzer import (
    CoherenceAnalyzer,
    CoverageAnalyzer,
    GapAnalysisConfig,
    RecencyAnalyzer,
)
from jarvis.memory.intent_analyzer import analyze_intent
from jarvis.llm.client import call_llm  # Re-exported for test mock compatibility
from jarvis.memory.research_planner import ResearchPlanner
from jarvis.memory.research_executor import MCPResearchExecutor

app = typer.Typer(help="RAG query commands with LLM-powered answers.")


def _load_gap_config(settings: object) -> GapAnalysisConfig:
    gap_cfg = getattr(settings, "gap_analysis", None)
    return GapAnalysisConfig(
        coverage_threshold=getattr(gap_cfg, "coverage_threshold", 0.6),
        recency_stale_days=getattr(gap_cfg, "recency_stale_days", 90),
        recency_sparse_days=getattr(gap_cfg, "recency_sparse_days", 30),
        min_recency_results=getattr(gap_cfg, "min_recency_results", 1),
        coherence_threshold=getattr(gap_cfg, "coherence_threshold", 0.35),
    )


def _load_research_config(settings: object):
    from jarvis.memory.research_planner import ResearchPlanConfig
    research_cfg = getattr(settings, "research", None)
    return ResearchPlanConfig(
        max_queries=getattr(research_cfg, "max_queries", 3),
        min_queries=getattr(research_cfg, "min_queries", 2),
        provider=getattr(research_cfg, "provider", "auto"),
    )


@app.command()
def query(
    question: str,
    provider: str = "auto",
    source: Optional[str] = None,
    k: int = 5,
    grounding_level: str = typer.Option(None, "--grounding-level", case_sensitive=False, help="soft | balanced | strict."),
    auto_grounding: bool = typer.Option(True, "--auto-grounding/--no-auto-grounding", help="Auto grounding level."),
    show_confidence: bool = typer.Option(False, "--show-confidence", help="Show confidence tags."),
    max_tokens: int = 2000,
    json_output: bool = typer.Option(False, "--json-output", "--json", help="JSON output."),
    retriever: Optional[str] = None,
    weight: Optional[float] = None,
    strict_mode: bool = False,
    expand: Optional[int] = None,
    enable_research: bool = typer.Option(False, "--enable-research", help="Enable research mode."),
    agents: Optional[str] = typer.Option(None, "--agents", help="Council of Ricks personas."),
    show_all: bool = typer.Option(False, "--show-all", help="Show all persona responses."),
    select: Optional[str] = typer.Option(None, "--select", help="Select specific persona."),
    allow_stale: bool = typer.Option(False, "--allow-stale", help="Include stale documents."),
    diversity: str = typer.Option("balanced", "--diversity", help="Diversity mode."),
) -> None:
    """Ask JARVIS a question and get an LLM-powered answer with citations."""
    # === THIN ROUTER - All logic delegated to query_router.py ===
    from jarvis.cli.query_router import (
        QueryContext, resolve_parameters, execute_search,
        analyze_gaps, handle_council_mode, handle_research_mode, handle_standard_query,
    )
    from jarvis.cli.query_council import parse_and_validate_personas
    
    settings = load_settings()
    gap_config = _load_gap_config(settings)
    research_config = _load_research_config(settings)
    
    # Build context
    ctx = QueryContext(
        question=question, k=k, provider=provider, max_tokens=max_tokens,
        json_output=json_output, show_confidence=show_confidence,
        enable_research=enable_research, allow_stale=allow_stale, diversity=diversity,
        source=source,
    )
    
    # Phase 1: Parameters
    resolve_parameters(ctx, settings, retriever, weight, expand, grounding_level, strict_mode, auto_grounding)
    
    # Phase 2: Council check
    ctx.selected_personas = parse_and_validate_personas(agents, select, json_output)
    ctx.council_mode = ctx.selected_personas is not None
    ctx.select_override = select
    ctx.show_all = show_all
    if ctx.council_mode and not json_output:
        typer.echo("🎭 Council of Ricks mode activated")
    
    # Phase 3: Search
    if not execute_search(ctx):
        return
    
    # Phase 4: Gap analysis
    analyze_gaps(ctx, gap_config)
    
    # Phase 5: Route to handler
    if ctx.council_mode and ctx.selected_personas:
        handle_council_mode(ctx)
    
    if ctx.enable_research and (ctx.gap_analysis["coverage_gap"] or ctx.gap_analysis["recency_gap"]):
        handle_research_mode(ctx, research_config)
    
    # Phase 6: Standard query
    handle_standard_query(ctx)


if __name__ == "__main__":
    app()
