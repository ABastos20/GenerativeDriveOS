"""File watching CLI commands."""

from __future__ import annotations

from typing import List
import typer

from jarvis.memory.file_watcher import start_file_watcher

app = typer.Typer(help="File watching and auto re-ingestion commands.")


@app.command("start")
def start(
    paths: List[str] = typer.Argument(
        ...,
        help="Paths to watch (files or directories).",
    ),
    collection_name: str = typer.Option(
        "jarvis-core",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: jarvis-core).",
    ),
    debounce_seconds: float = typer.Option(
        2.0,
        "--debounce",
        min=0.5,
        help="Wait this many seconds after last event before processing (default: 2.0).",
    ),
    daemon: bool = typer.Option(
        False,
        "--daemon",
        help="Run in background (no output).",
    ),
) -> None:
    """Start file watcher for auto re-ingestion.

    Monitors specified paths for changes and automatically re-ingests
    modified files into Qdrant.

    Examples:
        # Watch docs folder
        jarvis watch start docs/

        # Watch multiple paths
        jarvis watch start docs/ src/jarvis/

        # Run in foreground with custom debounce
        jarvis watch start docs/ --debounce 5.0
    """
    if not paths:
        typer.echo("Error: No paths specified to watch", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Starting file watcher...")
    typer.echo(f"Collection: {collection_name}")
    typer.echo(f"Watching paths: {', '.join(paths)}")
    typer.echo(f"Debounce: {debounce_seconds}s")
    typer.echo(f"Daemon mode: {daemon}")
    typer.echo("")

    if not daemon:
        typer.echo("Press Ctrl+C to stop")
        typer.echo("")

    try:
        start_file_watcher(
            watch_paths=paths,
            collection_name=collection_name,
            debounce_seconds=debounce_seconds,
            daemon=daemon,
        )

        if not daemon:
            # If daemon=False, start_file_watcher blocks until interrupted
            typer.echo("\nFile watcher stopped")

    except KeyboardInterrupt:
        typer.echo("\nFile watcher stopped")
    except Exception as e:
        typer.echo(f"Error starting file watcher: {str(e)}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
