"""Council of Ricks persona handling."""
from pathlib import Path
from typing import Optional, List
import typer

from jarvis.agents.orchestrator import PersonaRegistry
from jarvis.agents.personas import PersonaConfig


def parse_and_validate_personas(
    agents: Optional[str],
    select: Optional[str],
    json_output: bool,
) -> Optional[List[PersonaConfig]]:
    """Parse and validate persona selection.
    
    Returns:
        List of personas or None if not council mode
        
    Raises:
        typer.Exit: If validation fails
    """
    if not agents and not select:
        return None
        
    # Auto-enable agents if select is provided
    if select and not agents:
        agents = "all"
    
    # Initialize persona registry
    config_path = Path("src/jarvis/agents/config/personas.yaml")
    if not config_path.exists():
        typer.echo(
            "Error: personas.yaml not found. Council of Ricks requires persona configuration.",
            err=True
        )
        raise typer.Exit(code=1)
    
    try:
        from jarvis.database.postgres import get_connection_string
        database_url = get_connection_string()
        
        registry = PersonaRegistry(
            config_path=config_path,
            database_url=database_url,
            watch_interval=2.0
        )
    except Exception as exc:
        typer.echo(f"Error initializing PersonaRegistry: {exc}", err=True)
        raise typer.Exit(code=1)
    
    # Get requested personas
    if agents.lower() == "all":
        selected_personas = list(registry.get_enabled_personas().values())
        if not json_output:
            typer.echo(f"  → Using all {len(selected_personas)} enabled personas")
    else:
        # Parse comma-separated list
        persona_names = [name.strip() for name in agents.split(",")]
        selected_personas = []
        
        for name in persona_names:
            persona = registry.get_persona(name)
            if persona is None:
                available = list(registry.personas.keys())
                typer.echo(
                    f"Error: Persona '{name}' not found. Available: {', '.join(available)}",
                    err=True
                )
                raise typer.Exit(code=1)
            if not persona.enabled:
                typer.echo(f"Warning: Persona '{name}' is disabled but will be used anyway", err=True)
            selected_personas.append(persona)
        
        if not json_output:
            typer.echo(f"  → Using {len(selected_personas)} personas: {', '.join(p.name for p in selected_personas)}")
    
    # Validate --select persona name if provided
    if select:
        if not any(p.name == select for p in selected_personas):
            typer.echo(
                f"Error: Selected persona '{select}' not in active personas. "
                f"Available: {', '.join(p.name for p in selected_personas)}",
                err=True
            )
            raise typer.Exit(code=1)
        if not json_output:
            typer.echo(f"  → Manual override: will select '{select}' response")
    
    return selected_personas
