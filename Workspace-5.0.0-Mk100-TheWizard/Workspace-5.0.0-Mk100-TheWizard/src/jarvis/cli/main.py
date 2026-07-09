from __future__ import annotations

import typer

from jarvis.cli import analytics, doctor, health, memory, query as query_cli, watch, trace as trace_cli, snapshot, provenance
from jarvis.cli.commands import personas

import sys
import structlog

# Configure logging to stderr to keep stdout clean for JSON output
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

logger = structlog.get_logger(__name__)

app = typer.Typer(help="JARVIS CLI")

# Global callback for CLI flags
@app.callback()
def main(
    safe: bool = typer.Option(
        False,
        "--safe",
        help="Enable safe mode (read-only, no agent invocation or writes)",
    ),
):
    """JARVIS CLI - Global configuration."""
    import os
    if safe:
        os.environ["JARVIS_SAFE_MODE"] = "true"
        logger.warning(
            "safe_mode_enabled",
            message="🛡️  SAFE MODE ACTIVE - Read-only operation (no agent invocation or writes)"
        )


# Subcommands
app.add_typer(doctor.app, name="doctor")
app.add_typer(memory.app, name="memory")
app.add_typer(analytics.app, name="analytics")
app.add_typer(health.app, name="health")
app.add_typer(watch.app, name="watch")
app.add_typer(personas.app, name="personas")
app.add_typer(trace_cli.app, name="trace")  # Story 4.5.6
app.add_typer(snapshot.app, name="snapshot")  # Story 8-6 Phase 2
app.add_typer(provenance.app, name="provenance")  # Story 11-8
app.command()(query_cli.query)


if __name__ == "__main__":
    app()
