"""Health monitoring CLI commands."""

from __future__ import annotations

import typer

from jarvis.monitoring import (
    HealthMonitor,
    AlertConfig,
    format_health_report,
)

app = typer.Typer(help="Health monitoring and alerting commands.")


@app.command("check")
def check(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
    min_points: int = typer.Option(
        40000,
        "--min-points",
        help="Minimum expected Qdrant points (default: 40000).",
    ),
    min_heuristic_rate: float = typer.Option(
        65.0,
        "--min-heuristic-rate",
        help="Minimum heuristic hit rate % (default: 65).",
    ),
    min_enrichment: float = typer.Option(
        30.0,
        "--min-enrichment",
        help="Minimum enrichment coverage % (default: 30).",
    ),
    max_enrichment: float = typer.Option(
        60.0,
        "--max-enrichment",
        help="Maximum enrichment coverage % (default: 60).",
    ),
) -> None:
    """Run health checks on JARVIS memory system.

    Checks:
    - Qdrant point count and stability
    - Heuristic classification hit rate
    - Enrichment coverage
    """
    config = AlertConfig(
        qdrant_min_expected_points=min_points,
        heuristic_hit_rate_min=min_heuristic_rate,
        enrichment_coverage_min=min_enrichment,
        enrichment_coverage_max=max_enrichment,
    )

    monitor = HealthMonitor(config)

    try:
        results = monitor.run_all_checks(collection_name=collection_name)

        report = format_health_report(results)
        typer.echo(report)

        # Exit with error code if any checks failed
        failures = [r for r in results if r.status in ["warning", "critical"]]
        if failures:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error running health checks: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command("monitor")
def monitor(
    collection_name: str = typer.Option(
        "knowledge",
        "--collection",
        "--collection-name",
        help="Qdrant collection name (default: knowledge).",
    ),
    interval: int = typer.Option(
        15,
        "--interval",
        min=1,
        help="Check interval in minutes (default: 15).",
    ),
    discord_webhook: str = typer.Option(
        None,
        "--discord-webhook",
        help="Discord webhook URL for alerts.",
    ),
    slack_webhook: str = typer.Option(
        None,
        "--slack-webhook",
        help="Slack webhook URL for alerts.",
    ),
    email: str = typer.Option(
        None,
        "--email",
        help="Email address for alerts.",
    ),
    min_points: int = typer.Option(
        40000,
        "--min-points",
        help="Minimum expected Qdrant points (default: 40000).",
    ),
    min_heuristic_rate: float = typer.Option(
        65.0,
        "--min-heuristic-rate",
        help="Minimum heuristic hit rate % (default: 65).",
    ),
) -> None:
    """Run health monitor as daemon (continuous monitoring).

    Runs health checks at regular intervals and sends alerts to
    configured channels when issues are detected.

    Example:
        jarvis health monitor --interval 15 --discord-webhook <url>
    """
    config = AlertConfig(
        qdrant_min_expected_points=min_points,
        heuristic_hit_rate_min=min_heuristic_rate,
        discord_webhook_url=discord_webhook,
        slack_webhook_url=slack_webhook,
        email_recipient=email,
    )

    monitor = HealthMonitor(config)

    typer.echo(f"Starting health monitor daemon (interval: {interval} minutes)")
    typer.echo(f"Collection: {collection_name}")
    typer.echo(f"Press Ctrl+C to stop")
    typer.echo("")

    try:
        monitor.run_daemon(
            collection_name=collection_name,
            check_interval_minutes=interval,
        )
    except KeyboardInterrupt:
        typer.echo("\nHealth monitor stopped")
    except Exception as e:
        typer.echo(f"Error in health monitor: {str(e)}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
