"""CLI commands for managing Council of Ricks personas."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from jarvis.agents.persona_db import PersonaDB
from jarvis.agents.personas import PersonaConfig, load_personas_config

app = typer.Typer(help="Manage Council of Ricks personas (YAML + PostgreSQL sync)")
console = Console()


def get_persona_db() -> PersonaDB:
    """Get PersonaDB instance from environment configuration."""
    from jarvis.database.postgres import get_connection_string
    database_url = get_connection_string()
    return PersonaDB(database_url)


def get_personas_config_path() -> Path:
    """Get path to personas.yaml configuration file."""
    # Default to src/jarvis/agents/config/personas.yaml
    config_path = Path(__file__).parent.parent.parent / "agents" / "config" / "personas.yaml"

    # Check environment override
    env_path = os.environ.get("PERSONAS_CONFIG_PATH")
    if env_path:
        config_path = Path(env_path)

    return config_path


@app.command()
def list(
    active_only: bool = typer.Option(False, "--active", help="Show only active personas"),
) -> None:
    """List all personas with weights and status.

    Examples:
        jarvis personas list
        jarvis personas list --active
    """
    try:
        persona_db = get_persona_db()
        personas = persona_db.list_personas(active_only=active_only)

        if not personas:
            console.print("[yellow]No personas found.[/yellow]")
            return

        # Validate weights
        is_valid, total_weight, active_names = persona_db.validate_active_weights()

        # Create rich table
        table = Table(title="Council of Ricks Personas")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Weight", justify="right", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("System Prompt Preview", style="dim")

        for persona in personas:
            status_emoji = "✅" if persona.is_active else "❌"
            status_text = f"{status_emoji} {'Active' if persona.is_active else 'Disabled'}"

            # Truncate system prompt for display
            prompt_preview = persona.system_prompt[:60] + "..." if len(persona.system_prompt) > 60 else persona.system_prompt

            weight_pct = float(persona.weight) * 100
            table.add_row(
                persona.name,
                f"{weight_pct:.1f}%",
                status_text,
                prompt_preview
            )

        console.print(table)

        # Show weight validation summary
        console.print()
        if is_valid:
            console.print(f"[green]✓[/green] Active personas weights sum to {total_weight:.3f} (100%)")
        else:
            console.print(f"[red]⚠[/red] Active personas weights sum to {total_weight:.3f} (expected 1.00)")
            console.print(f"    Active personas: {', '.join(active_names)}")

    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def add(
    name: str = typer.Argument(..., help="Persona name (e.g., 'Creative Rick')"),
    system_prompt: Optional[str] = typer.Option(None, "--prompt", help="System prompt"),
    weight: float = typer.Option(0.1, "--weight", help="Voting weight (0.0-1.0)"),
    active: bool = typer.Option(True, "--active/--inactive", help="Enable persona"),
) -> None:
    """Add a new persona interactively.

    Examples:
        jarvis personas add "Creative Rick" --prompt "You are creative..." --weight 0.15
        jarvis personas add "Debug Rick" --weight 0.05 --inactive
    """
    # Validate weight
    if not (0.0 <= weight <= 1.0):
        console.print("[red]Error:[/red] Weight must be between 0.0 and 1.0")
        raise typer.Exit(code=1)

    # Interactive prompt for system_prompt if not provided
    if system_prompt is None:
        console.print(f"\n[cyan]Creating persona:[/cyan] {name}")
        console.print("[dim]Enter system prompt (press Enter twice when done):[/dim]")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        system_prompt = "\n".join(lines).strip()

    if not system_prompt:
        console.print("[red]Error:[/red] System prompt cannot be empty")
        raise typer.Exit(code=1)

    try:
        persona_db = get_persona_db()
        persona = persona_db.create_persona(
            name=name,
            system_prompt=system_prompt,
            weight=weight,
            is_active=active,
        )

        console.print(f"[green]✓[/green] Created persona: {persona.name}")
        console.print(f"  Weight: {float(persona.weight) * 100:.1f}%")
        console.print(f"  Status: {'Active' if persona.is_active else 'Disabled'}")

        # Warn if weights don't sum to 100%
        is_valid, total_weight, active_names = persona_db.validate_active_weights()
        if not is_valid:
            console.print()
            console.print(f"[yellow]⚠ Warning:[/yellow] Active personas weights sum to {total_weight:.3f} (expected 1.00)")
            console.print(f"    You may need to adjust weights to maintain 100% total.")

    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def update(
    name: str = typer.Argument(..., help="Persona name to update"),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="New system prompt"),
    weight: Optional[float] = typer.Option(None, "--weight", help="New weight (0.0-1.0)"),
) -> None:
    """Update persona properties.

    Examples:
        jarvis personas update "Rickiest Rick" --weight 0.35
        jarvis personas update "Supportive Rick" --prompt "New prompt..."
    """
    # Validate weight if provided
    if weight is not None and not (0.0 <= weight <= 1.0):
        console.print("[red]Error:[/red] Weight must be between 0.0 and 1.0")
        raise typer.Exit(code=1)

    if prompt is None and weight is None:
        console.print("[red]Error:[/red] Must provide at least --prompt or --weight")
        raise typer.Exit(code=1)

    try:
        persona_db = get_persona_db()
        persona = persona_db.update_persona(
            name=name,
            system_prompt=prompt,
            weight=weight,
        )

        if persona is None:
            console.print(f"[red]Error:[/red] Persona '{name}' not found")
            raise typer.Exit(code=1)

        console.print(f"[green]✓[/green] Updated persona: {persona.name}")

        if weight is not None:
            console.print(f"  Weight: {float(persona.weight) * 100:.1f}%")

            # Warn if weights don't sum to 100%
            is_valid, total_weight, active_names = persona_db.validate_active_weights()
            if not is_valid:
                console.print()
                console.print(f"[yellow]⚠ Warning:[/yellow] Active personas weights sum to {total_weight:.3f} (expected 1.00)")

    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def enable(
    name: str = typer.Argument(..., help="Persona name to enable"),
) -> None:
    """Enable a persona (set is_active = True).

    Examples:
        jarvis personas enable "Supportive Rick"
    """
    try:
        persona_db = get_persona_db()
        persona = persona_db.enable_persona(name)

        if persona is None:
            console.print(f"[red]Error:[/red] Persona '{name}' not found")
            raise typer.Exit(code=1)

        console.print(f"[green]✓[/green] Enabled persona: {persona.name}")

        # Warn if weights don't sum to 100%
        is_valid, total_weight, active_names = persona_db.validate_active_weights()
        if not is_valid:
            console.print()
            console.print(f"[yellow]⚠ Warning:[/yellow] Active personas weights sum to {total_weight:.3f} (expected 1.00)")
            console.print(f"    You may need to adjust weights to maintain 100% total.")

    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def disable(
    name: str = typer.Argument(..., help="Persona name to disable"),
) -> None:
    """Disable a persona (set is_active = False).

    Examples:
        jarvis personas disable "Empathetic Rick"
    """
    try:
        persona_db = get_persona_db()
        persona = persona_db.disable_persona(name)

        if persona is None:
            console.print(f"[red]Error:[/red] Persona '{name}' not found")
            raise typer.Exit(code=1)

        console.print(f"[green]✓[/green] Disabled persona: {persona.name}")

        # Check if at least one persona is still active
        active_personas = persona_db.list_personas(active_only=True)
        if not active_personas:
            console.print()
            console.print("[yellow]⚠ Warning:[/yellow] No active personas remaining!")
            console.print("    You should enable at least one persona for consensus voting.")

    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def sync(
    config_path: Optional[Path] = typer.Option(None, "--config", help="Path to personas.yaml"),
) -> None:
    """Sync personas from YAML configuration to PostgreSQL.

    Reads personas.yaml and updates the database accordingly.
    Creates new personas, updates existing ones, deactivates removed ones.

    Examples:
        jarvis personas sync
        jarvis personas sync --config /custom/path/personas.yaml
    """
    try:
        # Use provided path or default
        yaml_path = config_path if config_path else get_personas_config_path()

        if not yaml_path.exists():
            console.print(f"[red]Error:[/red] Config file not found: {yaml_path}")
            raise typer.Exit(code=1)

        # Load and validate config
        console.print(f"[cyan]Loading:[/cyan] {yaml_path}")
        personas_config = load_personas_config(yaml_path)

        console.print(f"[cyan]Syncing {len(personas_config.personas)} personas to database...[/cyan]")

        # Sync to database
        persona_db = get_persona_db()
        persona_db.sync_from_config(personas_config.personas)

        console.print("[green]✓[/green] Sync complete")

        # Show validation summary
        is_valid, total_weight, active_names = persona_db.validate_active_weights()
        if is_valid:
            console.print(f"[green]✓[/green] Active personas weights sum to {total_weight:.3f} (100%)")
        else:
            console.print(f"[red]⚠[/red] Active personas weights sum to {total_weight:.3f} (expected 1.00)")

    except ValueError as exc:
        console.print(f"[red]Validation Error:[/red] {exc}")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)
