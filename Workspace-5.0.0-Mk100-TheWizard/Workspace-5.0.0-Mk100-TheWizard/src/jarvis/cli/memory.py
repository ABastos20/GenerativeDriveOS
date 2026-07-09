from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import typer

from jarvis.memory import compile as memory_compile
from jarvis.memory import ingest, search

app = typer.Typer(help="Memory ingestion and retrieval commands.")


@app.command("add")
def memory_add(
    path: Path,
    collection: str = "knowledge",
) -> None:
    """Ingest a document into the memory store.

    Args:
        path: Path to document to ingest
        collection: Qdrant collection name
    """
    try:
        result = ingest.ingest_file(path, collection_name=collection)
        typer.echo(
            f"Ingested {result.chunks} chunk(s) into collection '{result.collection_name}' "
            f"(vectors written: {result.points_written}, vector size: {result.vector_size})"
        )
    except Exception as exc:  # pragma: no cover - CLI surface
        typer.echo(f"Error ingesting '{path}': {exc}", err=True)
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    """Parse a simple since value like '7d' or ISO-8601."""
    if not since:
        return None
    since = since.strip()
    if since.endswith("d") and since[:-1].isdigit():
        days = int(since[:-1])
        return datetime.now(timezone.utc) - timedelta(days=days)
    try:
        # Parse ISO string and ensure it's timezone-aware
        dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


@app.command("search")
def memory_search(
    query: str,
    persona: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[str] = None,
    since: Optional[str] = None,
    k: int = 10,
) -> None:
    """Search memory and print ranked snippets.

    Args:
        query: Natural language query
        persona: Filter by persona (future use)
        source: Logical source/domain filter (e.g., 'jarvis-core', 'jarvis-conversations')
        tags: Comma-separated tags to filter by (e.g., 'hydrogen,solar,batteries')
        since: Optional time filter (e.g., '7d' for last 7 days or ISO-8601 datetime)
        k: Number of results (1-50)
    """
    # For now, persona and since are parsed but unused; kept for future Story 2.4 extensions.
    _ = persona
    _parse_since(since)

    domains = [source] if source else None
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    try:
        results = search.search_memory(query, k=k, domains=domains, tags=tag_list)
    except Exception as exc:  # pragma: no cover - CLI surface
        typer.echo(f"Error searching memory: {exc}", err=True)
        raise typer.Exit(code=1)

    if not results:
        typer.echo("No results.")
        raise typer.Exit(code=0)

    for idx, res in enumerate(results, start=1):
        typer.echo(f"[{idx}] score={res.score:.3f} domain={res.domain or '-'}")
        if res.source_file:
            typer.echo(f"    source: {res.source_file}#{res.section or ''}")
        # Show tags if present
        chunk_tags = res.metadata.get("tags", []) if res.metadata else []
        if chunk_tags:
            typer.echo(f"    tags: {', '.join(chunk_tags[:5])}")
        typer.echo(f"    {res.text.strip()[:500]}")
        typer.echo("")

    raise typer.Exit(code=0)


@app.command("compile")
def memory_compile_cmd(
    since: str,
    until: Optional[str] = None,
    output: Optional[Path] = None,
    no_ingest: bool = False,
) -> None:
    """Compile conversations into LLM-generated insights.

    Args:
        since: Time range start (e.g., '7d' or ISO-8601)
        until: Time range end (ISO-8601, defaults to now)
        output: Override default insights directory (~/.jarvis/knowledge/insights/)
        no_ingest: Skip automatic ingestion of compiled insights

    Aggregates conversations from PostgreSQL within the specified time range,
    uses LLM to generate insights summary, and writes structured Markdown output.

    Examples:
        jarvis memory compile --since 7d
        jarvis memory compile --since 2025-11-01 --until 2025-11-30
        jarvis memory compile --since 30d --output /custom/path --no-ingest
    """
    # Parse since date
    since_dt = _parse_since(since)
    if not since_dt:
        typer.echo(f"Error: Invalid --since value: {since}", err=True)
        raise typer.Exit(code=1)

    # Parse until date if provided
    until_dt = None
    if until:
        try:
            until_dt = datetime.fromisoformat(until)
        except ValueError:
            typer.echo(f"Error: Invalid --until value (use ISO-8601): {until}", err=True)
            raise typer.Exit(code=1)

    # Show compilation parameters
    date_range = f"{since_dt.strftime('%Y-%m-%d')}"
    if until_dt:
        date_range += f" to {until_dt.strftime('%Y-%m-%d')}"
    else:
        date_range += " to now"

    typer.echo(f"\n📚 Compiling memories from {date_range}...")
    typer.echo(f"   Auto-ingest: {'No' if no_ingest else 'Yes'}")
    if output:
        typer.echo(f"   Output: {output}")

    try:
        result = memory_compile.compile_memories(
            since=since_dt,
            until=until_dt,
            output_dir=output,
            auto_ingest=not no_ingest,
        )

        # Display results
        typer.echo("\n✅ Compilation completed successfully!")
        typer.echo(f"\n📊 Summary:")
        typer.echo(f"   Conversations: {result.conversation_count}")
        typer.echo(f"   Messages: {result.message_count}")
        typer.echo(f"   Provider: {result.llm_response.provider}")
        typer.echo(f"   Model: {result.llm_response.model}")
        typer.echo(
            f"   Tokens: {result.llm_response.input_tokens} in + {result.llm_response.output_tokens} out"
        )
        typer.echo(f"   Cost: ${result.llm_response.cost_usd:.4f}")
        typer.echo(f"\n📄 Output file: {result.output_file}")

        if result.ingestion_result:
            typer.echo(
                f"\n🔍 Auto-ingested: {result.ingestion_result.chunks} chunks, "
                f"{result.ingestion_result.points_written} points written"
            )
            typer.echo(
                "   Search with: jarvis memory search --source jarvis-insights \"your query\""
            )

    except Exception as exc:
        typer.echo(f"\n❌ Compilation failed: {exc}", err=True)
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
