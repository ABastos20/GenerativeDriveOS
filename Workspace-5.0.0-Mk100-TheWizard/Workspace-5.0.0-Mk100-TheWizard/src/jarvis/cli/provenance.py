"""Provenance Verification CLI for Story 11-8.

Implements AC4: jarvis provenance verify
- Checks ledger chain integrity
- Validates event ordering and hash deltas
- Returns exit 0 on success, exit 1 on failure

Usage:
    jarvis provenance verify
"""

from __future__ import annotations

import typer
import structlog

from typing import Optional

logger = structlog.get_logger(__name__)

app = typer.Typer(help="Provenance ledger verification commands")


@app.command()
def verify(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """
    Verify provenance chain integrity.
    
    Checks:
    - Ledger chain hash consistency
    - Event ordering
    - Tier consistency
    
    Exit Codes:
    - 0: Full integrity verified
    - 1: Broken chain, inconsistent tiers, or missing events
    """
    from src.jarvis.database.session import get_session
    from src.jarvis.knowledge.provenance import ProvenanceLedger
    import json
    
    try:
        session = next(get_session())
        ledger = ProvenanceLedger(session)
        
        # Run chain verification
        is_valid, error_message = ledger.verify_chain_integrity()
        
        if is_valid:
            result = {
                "status": "OK",
                "message": "Provenance chain: integrity verified",
                "issues": []
            }
            
            if json_output:
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo("✅ Provenance chain: OK")
                if verbose:
                    # Show stats
                    typer.echo(f"   Entries verified: all")
            
            raise typer.Exit(code=0)
        else:
            result = {
                "status": "BROKEN",
                "message": "Provenance chain: integrity failure detected",
                "issues": [error_message] if error_message else ["Unknown error"]
            }
            
            if json_output:
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo("❌ Provenance chain: BROKEN")
                if error_message:
                    typer.echo(f"   Issue: {error_message}")
            
            logger.error(
                "provenance_verify_failed",
                error=error_message
            )
            raise typer.Exit(code=1)
            
    except typer.Exit:
        raise  # Re-raise Exit to preserve exit code
    except Exception as e:
        result = {
            "status": "ERROR",
            "message": f"Verification failed: {str(e)}",
            "issues": [str(e)]
        }
        
        if json_output:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"❌ Verification error: {e}")
        
        logger.exception("provenance_verify_error")
        raise typer.Exit(code=1)


@app.command()
def stats(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show provenance ledger statistics."""
    from src.jarvis.database.session import get_session
    from src.jarvis.knowledge.provenance import ProvenanceLedger
    from src.jarvis.knowledge.tiers import KnowledgeTier, SourceType
    import json
    
    try:
        session = next(get_session())
        ledger = ProvenanceLedger(session)
        
        # Gather stats by querying different dimensions
        stats_data = {
            "ledger": {
                "status": "operational",
            },
            "by_tier": {},
            "by_source": {},
        }
        
        # Query by tiers
        for tier in KnowledgeTier:
            entries = ledger.query_by_tier(tier, limit=None)
            stats_data["by_tier"][tier.name] = len(entries) if entries else 0
        
        # Query by source types
        for source in SourceType:
            entries = ledger.query_by_source(source, limit=None)
            stats_data["by_source"][source.name] = len(entries) if entries else 0
        
        if json_output:
            typer.echo(json.dumps(stats_data, indent=2))
        else:
            typer.echo("📊 Provenance Ledger Statistics")
            typer.echo("")
            typer.echo("By Tier:")
            for tier, count in stats_data["by_tier"].items():
                typer.echo(f"  {tier}: {count}")
            typer.echo("")
            typer.echo("By Source:")
            for source, count in stats_data["by_source"].items():
                typer.echo(f"  {source}: {count}")
        
        raise typer.Exit(code=0)
        
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"❌ Stats error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
