from __future__ import annotations

from collections import Counter
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import typer
from sqlalchemy import func

from jarvis.database.models import LLMUsageLog, Message, ResearchLog
from jarvis.database.postgres import get_session
from jarvis.memory.domain_catalog import catalog_collection_domains, catalog_documents
from jarvis.memory.enrich import enrich_collection_chunks
from jarvis.analytics import (
    create_snapshot_tables,
    capture_domain_snapshot,
    capture_system_snapshot,
    get_domain_growth,
    get_top_growing_domains,
    format_domain_growth_report,
)
from jarvis.memory.keyword_miner import (
    mine_llm_classified_keywords,
    format_keyword_suggestions,
    generate_heuristic_code,
)
from jarvis.memory.enrichment_scorer import (
    calculate_enrichment_roi,
    get_enrichment_recommendations,
    format_enrichment_report,
    format_recommendations_report,
)

app = typer.Typer(help="Analytics and reporting commands.")


def _iter_citations(value: Any) -> Iterable[Dict[str, Any]]:
    """Yield individual citation dicts from a stored provenance value."""
    if value is None:
        return

    # Canonical shape: list[dict]
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield item
        return

    # Fallback: envelope-style {"sources": [...]}
    if isinstance(value, dict):
        sources = value.get("sources")
        if isinstance(sources, list):
            for item in sources:
                if isinstance(item, dict):
                    yield item


def aggregate_citation_stats(
    provenance_values: List[Any],
    group_by: str,
) -> Dict[str, Any]:
    """Aggregate citation statistics by source_file or domain."""
    if group_by not in {"source_file", "domain"}:
        raise ValueError("group_by must be 'source_file' or 'domain'")

    counter: Counter[str] = Counter()
    total_citations = 0

    for value in provenance_values:
        for citation in _iter_citations(value):
            key_value = citation.get(group_by) or "<unknown>"
            counter[str(key_value)] += 1
            total_citations += 1

    top_entries = [
        {"value": name, "count": count} for name, count in counter.most_common()
    ]

    return {
        "total_citations": total_citations,
        "unique_values": len(counter),
        "top": top_entries,
    }


@app.command("citations")
def citations(
    days: int = typer.Option(
        30,
        "--days",
        min=1,
        help="Look back this many days from now (UTC).",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        min=1,
        help="Maximum number of top entries to return.",
    ),
    group_by: str = typer.Option(
        "source_file",
        "--group-by",
        help="Aggregation dimension: 'source_file' or 'domain'.",
    ),
) -> None:
    """Show basic citation usage statistics over recent conversations."""
    group_by_normalized = group_by.strip().lower()
    if group_by_normalized not in {"source_file", "domain"}:
        typer.echo("Error: --group-by must be 'source_file' or 'domain'", err=True)
        raise typer.Exit(code=1)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    with get_session() as session:
        messages: List[Message] = (
            session.query(Message)
            .filter(
                Message.citation_provenance.isnot(None),
                Message.created_at >= since,
            )
            .order_by(Message.created_at.asc())
            .all()
        )

    provenance_values: List[Any] = [m.citation_provenance for m in messages]
    stats = aggregate_citation_stats(
        provenance_values=provenance_values,
        group_by=group_by_normalized,
    )

    # Truncate top entries to the requested limit
    top_limited = stats["top"][:limit]

    payload = {
        "since": since.isoformat(),
        "group_by": group_by_normalized,
        "total_messages_with_provenance": len(messages),
        "total_citations": stats["total_citations"],
        "unique_values": stats["unique_values"],
        "top": top_limited,
    }

    import json

    typer.echo(json.dumps(payload, indent=2))


@app.command("usage")
def usage(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Filter to a single provider (e.g., google-ai, perplexity, openrouter).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json-output",
        help="Return aggregated usage as JSON instead of human-readable lines.",
    ),
) -> None:
    """Show aggregated LLM usage by provider (tokens and cost)."""
    with get_session() as session:
        query = (
            session.query(
                LLMUsageLog.provider,
                func.sum(LLMUsageLog.tokens_input),
                func.sum(LLMUsageLog.tokens_output),
                func.sum(LLMUsageLog.cost_usd),
            )
            .group_by(LLMUsageLog.provider)
            .order_by(LLMUsageLog.provider.asc())
        )

        if provider:
            query = query.filter(LLMUsageLog.provider == provider)

        rows = query.all()

    if json_output:
        payload: List[Dict[str, Any]] = []
        for row_provider, tokens_in, tokens_out, cost in rows:
            payload.append(
                {
                    "provider": row_provider,
                    "tokens_in": int(tokens_in or 0),
                    "tokens_out": int(tokens_out or 0),
                    "cost_usd": float(Decimal(cost or 0).quantize(Decimal("0.000001"))),
                }
            )

        import json

        typer.echo(json.dumps(payload, indent=2))
        return

    if not rows:
        typer.echo("No LLM usage rows found.")
        return


@app.command("research-summary")
def research_summary(
    days: int = typer.Option(
        30,
        "--days",
        min=1,
        help="Look back this many days from now (UTC).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json-output",
        help="Return aggregated research stats as JSON.",
    ),
) -> None:
    """Summarize research mode activity from ResearchLog."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    with get_session() as session:
        logs: List[ResearchLog] = (
            session.query(ResearchLog)
            .filter(ResearchLog.created_at >= since)
            .order_by(ResearchLog.created_at.desc())
            .all()
        )

    if not logs:
        typer.echo("No research sessions found in the selected window.")
        return

    total = len(logs)
    executed = sum(log.executed_queries or 0 for log in logs)
    sources = sum(log.sources_collected or 0 for log in logs)
    avg_cost = float(
        (sum(float(log.cost_usd or 0.0) for log in logs) / total) if total else 0.0
    )

    gap_counter: Counter[str] = Counter()
    for log in logs:
        gaps = (log.gap_types or {}) if isinstance(log.gap_types, dict) else {}
        for key, val in gaps.items():
            if val:
                gap_counter[key] += 1

    top_gaps = gap_counter.most_common()
    payload = {
        "since": since.isoformat(),
        "sessions": total,
        "executed_queries": executed,
        "sources_collected": sources,
        "avg_cost_usd": round(avg_cost, 4),
        "gap_counts": top_gaps,
    }

    import json

    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo(json.dumps(payload, indent=2))

    for row_provider, tokens_in, tokens_out, cost in rows:
        tokens_in_val = int(tokens_in or 0)
        tokens_out_val = int(tokens_out or 0)
        cost_val = Decimal(cost or 0).quantize(Decimal("0.000006"))
        typer.echo(
            f"{row_provider:12} tokens_in={tokens_in_val}, "
            f"tokens_out={tokens_out_val}, cost_usd={cost_val}"
        )


@app.command("catalog-domains")
def catalog_domains(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name to catalog (default: knowledge).",
    ),
    provider: str = typer.Option(
        "google-ai",
        "--provider",
        help="LLM provider for classification (default: google-ai).",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Optional model identifier for the chosen provider.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        min=1,
        help="Maximum number of points to process (default: all).",
    ),
    batch_size: int = typer.Option(
        64,
        "--batch-size",
        min=1,
        help="Number of Qdrant points to process per batch.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Log what would be done without writing to Qdrant or Postgres.",
    ),
) -> None:
    """Run a domain catalog job over the knowledge collection.

    This command walks Qdrant chunks, classifies them into domains and personas
    using an LLM, updates Qdrant payload metadata, and records discovered
    domains in the knowledge_domains table.
    """
    import json

    result = catalog_collection_domains(
        collection_name=collection_name,
        provider=provider,
        model=model,
        limit=limit,
        batch_size=batch_size,
        dry_run=dry_run,
    )

    payload = {
        "collection_name": result.collection_name,
        "points_processed": result.points_processed,
        "domains_created": result.domains_created,
        "dry_run": dry_run,
    }

    typer.echo(json.dumps(payload, indent=2))


@app.command("enrich-chunks")
def enrich_chunks(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name to enrich (default: knowledge).",
    ),
    provider: str = typer.Option(
        "perplexity",
        "--provider",
        help="LLM provider for enrichment (default: perplexity).",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Optional model identifier for the chosen provider.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        min=1,
        help="Maximum number of points to process (default: all).",
    ),
    batch_size: int = typer.Option(
        32,
        "--batch-size",
        min=1,
        help="Number of Qdrant points to process per batch.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Log what would be done without writing to Qdrant.",
    ),
    include_domains: Optional[str] = typer.Option(
        None,
        "--domains",
        help="Comma-separated list of payload domains to enrich (default: all).",
    ),
    rescan: bool = typer.Option(
        False,
        "--rescan",
        help="Re-enrich chunks even if they already have a summary.",
    ),
) -> None:
    """Run an enrichment job over knowledge chunks.

    This command walks Qdrant chunks, and for each one generates a short
    summary, bullet-style facts and tags, and a coarse doc_type, then
    writes those fields back into the payload.
    """
    import json

    domains = None
    if include_domains:
        domains = [d.strip() for d in include_domains.split(",") if d.strip()]

    result = enrich_collection_chunks(
        collection_name=collection_name,
        provider=provider,
        model=model,
        limit=limit,
        batch_size=batch_size,
        dry_run=dry_run,
        skip_if_present=not rescan,
        domains=domains,
    )

    payload = {
        "collection_name": result.collection_name,
        "points_processed": result.points_processed,
        "points_enriched": result.points_enriched,
        "dry_run": dry_run,
        "domains": domains,
    }

    typer.echo(json.dumps(payload, indent=2))


@app.command("catalog-docs")
def catalog_docs(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name to process documents for (default: knowledge).",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        min=1,
        help="Maximum number of points to process when building profiles (default: all).",
    ),
    batch_size: int = typer.Option(
        512,
        "--batch-size",
        min=1,
        help="Number of Qdrant points to process per batch.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Log what would be done without writing to Qdrant.",
    ),
) -> None:
    """Build document-level profiles and propagate them to chunks.

    This command groups chunks by document (source_file or conversation_id),
    derives a doc_primary_domain via majority vote over chunk domains,
    aggregates tags into doc_tags, and writes those fields back into each
    chunk. If a chunk has no meaningful primary_domain, it inherits the
    document primary domain.
    """
    import json

    result = catalog_documents(
        collection_name=collection_name,
        limit=limit,
        batch_size=batch_size,
        dry_run=dry_run,
    )

    payload = {
        "collection_name": result.collection_name,
        "documents_processed": result.documents_processed,
        "points_updated": result.points_updated,
        "dry_run": dry_run,
    }

    typer.echo(json.dumps(payload, indent=2))


@app.command("init-snapshots")
def init_snapshots() -> None:
    """Create PostgreSQL tables for domain evolution tracking.

    Run this once before using snapshot commands.
    """
    try:
        create_snapshot_tables()
        typer.echo("✓ Snapshot tables created successfully")
    except Exception as e:
        typer.echo(f"Error creating snapshot tables: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command("snapshot")
def snapshot(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
) -> None:
    """Capture domain and system snapshots for evolution tracking.

    Use this daily (via cron) to track how your knowledge base evolves.
    """
    import json

    try:
        capture_domain_snapshot(collection_name)
        capture_system_snapshot(collection_name)

        payload = {
            "status": "success",
            "collection": collection_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        typer.echo(json.dumps(payload, indent=2))

    except Exception as e:
        typer.echo(f"Error capturing snapshots: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command("growth")
def growth(
    days: int = typer.Option(
        7,
        "--days",
        min=1,
        help="Look back this many days (default: 7).",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        min=1,
        help="Show top N growing domains (default: 10).",
    ),
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
) -> None:
    """Show top growing domains over time.

    Requires daily snapshots to be captured first.
    """
    try:
        growth_data = get_top_growing_domains(
            collection_name=collection_name,
            days=days,
            limit=limit,
        )

        if not growth_data:
            typer.echo(f"No growth data available for the last {days} days.")
            typer.echo("Run 'jarvis analytics snapshot' daily to collect data.")
            return

        report = format_domain_growth_report(growth_data)
        typer.echo(report)

    except Exception as e:
        typer.echo(f"Error generating growth report: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command("mine-keywords")
def mine_keywords(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
    min_occurrences: int = typer.Option(
        10,
        "--min-occurrences",
        min=1,
        help="Minimum keyword occurrences to suggest (default: 10).",
    ),
    max_suggestions: int = typer.Option(
        50,
        "--max-suggestions",
        min=1,
        help="Maximum number of suggestions per domain (default: 50).",
    ),
    top_domains: int = typer.Option(
        10,
        "--top-domains",
        min=1,
        help="Show top N domains in report (default: 10).",
    ),
) -> None:
    """Mine keywords from LLM-classified chunks to expand heuristics.

    Analyzes chunks that fell back to LLM classification and suggests
    keywords that could be added to heuristic rules.
    """
    try:
        typer.echo("Mining keywords from LLM-classified chunks...")

        suggestions = mine_llm_classified_keywords(
            collection_name=collection_name,
            min_occurrences=min_occurrences,
            max_suggestions=max_suggestions,
        )

        if not suggestions:
            typer.echo("No keyword suggestions found.")
            typer.echo("Make sure domain catalog job has been run first.")
            return

        report = format_keyword_suggestions(suggestions, top_domains=top_domains)
        typer.echo(report)

    except Exception as e:
        typer.echo(f"Error mining keywords: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command("enrichment-roi")
def enrichment_roi(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
    lookback_days: int = typer.Option(
        30,
        "--lookback-days",
        min=1,
        help="Days to look back for retrieval stats (default: 30).",
    ),
) -> None:
    """Calculate ROI for enriched documents.

    Shows which enrichments improved retrieval quality.
    """
    try:
        typer.echo("Calculating enrichment ROI...")

        scores = calculate_enrichment_roi(
            collection_name=collection_name,
            lookback_days=lookback_days,
        )

        if not scores:
            typer.echo("No enrichment data found.")
            return

        report = format_enrichment_report(scores)
        typer.echo(report)

    except Exception as e:
        typer.echo(f"Error calculating enrichment ROI: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command("enrichment-recommendations")
def enrichment_recommendations(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
) -> None:
    """Get recommendations for which documents to enrich next.

    Analyzes unenriched documents and prioritizes based on:
    - Retrieval frequency
    - Domain ROI history
    - Document size
    """
    try:
        typer.echo("Analyzing enrichment opportunities...")

        recommendations = get_enrichment_recommendations(collection_name=collection_name)

        report = format_recommendations_report(recommendations)
        typer.echo(report)

    except Exception as e:
        typer.echo(f"Error generating recommendations: {str(e)}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
