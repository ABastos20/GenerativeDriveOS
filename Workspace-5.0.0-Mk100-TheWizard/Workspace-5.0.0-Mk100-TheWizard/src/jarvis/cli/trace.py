"""CLI commands for cognitive trace inspection and export (Story 4.5.6).

Commands:
- jarvis trace list - List recent traces
- jarvis trace show <id> - Pretty-print trace (inspect-only, no LLM calls)
- jarvis trace export <id> - Export trace as JSON/YAML
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import typer
import structlog

from jarvis.database import postgres as pg

app = typer.Typer(
    name="trace",
    help="🧠 Inspect and export cognitive traces from ARCHES query processing.",
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════


@app.command("list")
def list_traces(
    session_id: Optional[str] = typer.Option(
        None,
        "--session-id",
        "-s",
        help="Filter by session ID",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Maximum number of traces to show",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        help="Filter by severity: normal | error | low_confidence | debug",
    ),
) -> None:
    """List recent cognitive traces.
    
    Shows trace_id, created_at, session_id, severity, mode, latency.
    """
    from jarvis.arches.trace import list_cognitive_traces
    
    typer.echo("\n🧠 Cognitive Traces\n")
    typer.echo("=" * 80)
    
    with pg.get_session() as session:
        traces = list_cognitive_traces(
            session,
            session_id=session_id,
            severity=severity,
            limit=limit,
        )
    
    if not traces:
        typer.echo("  No traces found.\n")
        return
    
    # Header
    typer.echo(f"{'TRACE ID':<38} {'MODE':<10} {'SEVERITY':<12} {'LATENCY':<10} {'CREATED'}")
    typer.echo("-" * 80)
    
    for trace in traces:
        trace_id = trace["trace_id"][:36]
        mode = trace.get("mode", "qa")
        severity = trace.get("severity", "normal")
        latency = f"{trace.get('total_latency_ms', '-')}ms" if trace.get("total_latency_ms") else "-"
        created = trace.get("created_at", "-")[:19] if trace.get("created_at") else "-"
        
        # Color-code severity
        if severity == "error":
            severity_display = typer.style(severity, fg=typer.colors.RED)
        elif severity == "low_confidence":
            severity_display = typer.style(severity, fg=typer.colors.YELLOW)
        else:
            severity_display = severity
        
        typer.echo(f"{trace_id:<38} {mode:<10} {severity_display:<12} {latency:<10} {created}")
    
    typer.echo("-" * 80)
    typer.echo(f"Total: {len(traces)} traces\n")


@app.command("show")
def show_trace(
    trace_id: str = typer.Argument(..., help="Trace ID (UUID)"),
) -> None:
    """Pretty-print a cognitive trace (inspect-only, no LLM calls).
    
    Alias: `jarvis trace replay <id>` (same behavior).
    """
    from jarvis.arches.trace import get_cognitive_trace
    
    try:
        uuid_id = UUID(trace_id)
    except ValueError:
        typer.echo(f"❌ Invalid trace ID: {trace_id}", err=True)
        raise typer.Exit(code=1)
    
    with pg.get_session() as session:
        trace = get_cognitive_trace(uuid_id, session)
    
    if trace is None:
        typer.echo(f"❌ Trace not found: {trace_id}", err=True)
        raise typer.Exit(code=1)
    
    # Pretty-print the trace
    typer.echo("\n" + "=" * 80)
    typer.echo("🧠 COGNITIVE TRACE")
    typer.echo("=" * 80)
    
    # Core info
    typer.echo(f"\n📌 Core Identifiers")
    typer.echo(f"   Trace ID:     {trace.trace_id}")
    typer.echo(f"   Session ID:   {trace.session_id or '-'}")
    typer.echo(f"   Mode:         {trace.mode}")
    typer.echo(f"   Severity:     {trace.severity}")
    typer.echo(f"   Query:        {trace.query[:100]}{'...' if len(trace.query) > 100 else ''}")
    
    # Timing
    typer.echo(f"\n⏱️  Timing")
    typer.echo(f"   Started:      {trace.started_at}")
    typer.echo(f"   Completed:    {trace.completed_at or '-'}")
    typer.echo(f"   Total:        {trace.total_latency_ms}ms" if trace.total_latency_ms else "   Total:        -")
    
    if trace.phase_timings:
        typer.echo(f"   Phases:")
        for phase, ms in trace.phase_timings.items():
            typer.echo(f"      {phase}: {ms}ms")
    
    # Retrieval
    typer.echo(f"\n🔍 Retrieval Phase")
    typer.echo(f"   Retrievers:   {', '.join(trace.retrievers_used) or '-'}")
    typer.echo(f"   Diversity:    {trace.diversity_mode}")
    typer.echo(f"   K initial:    {trace.k_initial}")
    typer.echo(f"   K final:      {trace.k_final}")
    
    if trace.retrieval_events:
        typer.echo(f"   Top chunks ({len(trace.retrieval_events)}):")
        for i, chunk in enumerate(trace.retrieval_events[:5]):
            typer.echo(f"      {i+1}. {chunk.doc_key} (score: {chunk.score_after_mmr:.3f}, fresh: {chunk.freshness_score or '-'})")
    
    # Agents
    if trace.agents:
        typer.echo(f"\n🎭 Council of Ricks ({len(trace.agents)} agents)")
        for agent in trace.agents:
            vote_str = f"vote={agent.vote:.2f}" if agent.vote else "no vote"
            typer.echo(f"   • {agent.name} ({agent.role}): {agent.latency_ms}ms, {vote_str}")
    
    # Research
    if trace.research_calls:
        typer.echo(f"\n🌐 Research Calls ({len(trace.research_calls)})")
        for call in trace.research_calls:
            status = "✓" if call.success else "✗"
            typer.echo(f"   • [{status}] {call.provider}: {call.query[:50]}... ({call.duration_ms}ms, {call.results_count} results)")
    
    # Output
    typer.echo(f"\n📤 Output")
    typer.echo(f"   Confidence:   {trace.confidence_estimate or '-'}")
    typer.echo(f"   Sources:      {len(trace.sources)} chunks")
    typer.echo(f"   Domains:      {', '.join(trace.domains) or '-'}")
    
    if trace.final_answer_summary:
        typer.echo(f"   Summary:      {trace.final_answer_summary[:150]}...")
    
    # Meta
    if trace.errors:
        typer.echo(f"\n⚠️  Errors ({len(trace.errors)})")
        for error in trace.errors:
            typer.echo(f"   • {error}")
    
    if trace.tags:
        typer.echo(f"\n🏷️  Tags: {', '.join(trace.tags)}")
    
    typer.echo("\n" + "=" * 80 + "\n")


@app.command("replay")
def replay_trace(
    trace_id: str = typer.Argument(..., help="Trace ID (UUID)"),
) -> None:
    """Replay a cognitive trace (alias for show - inspect-only, no LLM calls)."""
    show_trace(trace_id)


@app.command("export")
def export_trace(
    trace_id: str = typer.Argument(..., help="Trace ID (UUID)"),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json | yaml",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
) -> None:
    """Export a cognitive trace as JSON or YAML."""
    from jarvis.arches.trace import get_cognitive_trace
    
    try:
        uuid_id = UUID(trace_id)
    except ValueError:
        typer.echo(f"❌ Invalid trace ID: {trace_id}", err=True)
        raise typer.Exit(code=1)
    
    with pg.get_session() as session:
        trace = get_cognitive_trace(uuid_id, session)
    
    if trace is None:
        typer.echo(f"❌ Trace not found: {trace_id}", err=True)
        raise typer.Exit(code=1)
    
    # Convert to dict
    data = trace.to_dict()
    
    # Format output
    if format.lower() == "yaml":
        try:
            import yaml
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        except ImportError:
            typer.echo("❌ PyYAML not installed. Install with: pip install pyyaml", err=True)
            raise typer.Exit(code=1)
    else:
        import json
        content = json.dumps(data, indent=2, default=str)
    
    # Output
    if output:
        with open(output, "w") as f:
            f.write(content)
        typer.echo(f"✅ Trace exported to: {output}")
    else:
        typer.echo(content)
