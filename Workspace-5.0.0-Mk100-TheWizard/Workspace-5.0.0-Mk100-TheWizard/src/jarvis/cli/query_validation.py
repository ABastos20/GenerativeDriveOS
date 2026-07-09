"""Query input validation and parsing."""
from typing import Optional
import typer


def validate_query_params(
    k: int,
    expansion: int,
    retriever: str,
    weight: float,
    grounding_level: Optional[str],
) -> None:
    """Validate query parameters.
    
    Raises:
        typer.Exit: If validation fails
    """
    # Validate k parameter
    if not (1 <= k <= 20):
        typer.echo("Error: k must be between 1 and 20", err=True)
        raise typer.Exit(code=1)

    # Validate expansion parameter
    if expansion < 0 or expansion > 5:
        typer.echo("Error: --expand must be between 0 and 5", err=True)
        raise typer.Exit(code=1)

    # Validate retriever
    valid_retrievers = {"semantic", "keyword", "hybrid"}
    if retriever not in valid_retrievers:
        typer.echo(
            f"Error: Invalid retriever '{retriever}'. "
            f"Expected one of: semantic, keyword, hybrid.",
            err=True,
        )
        raise typer.Exit(code=1)

    # Validate weight for hybrid
    if retriever == "hybrid":
        if weight < 0.0 or weight > 1.0:
            typer.echo("Error: weight must be between 0.0 and 1.0", err=True)
            raise typer.Exit(code=1)

    # Validate grounding level
    if grounding_level is not None:
        valid_grounding_levels = {"soft", "balanced", "strict"}
        if grounding_level not in valid_grounding_levels:
            typer.echo(
                f"Error: Invalid grounding level '{grounding_level}'. Expected one of: soft, balanced, strict.",
                err=True,
            )
            raise typer.Exit(code=1)


def resolve_effective_params(
    retriever: Optional[str],
    weight: Optional[float],
    expand: Optional[int],
    grounding_level: Optional[str],
    strict_mode: bool,
    settings: object,
) -> tuple[str, float, int, str]:
    """Resolve effective parameters from CLI args and settings.
    
    Returns:
        (effective_retriever, effective_weight, effective_expansion, effective_grounding_level)
    """
    default_retriever = getattr(getattr(settings, "query", None), "default_retriever", "semantic")
    default_weight = getattr(getattr(settings, "query", None), "default_weight", 0.7)
    default_enable_expansion = getattr(getattr(settings, "query", None), "enable_expansion", False)
    default_expansion_count = getattr(getattr(settings, "query", None), "expansion_count", 2)
    default_grounding_level = getattr(
        getattr(settings, "query", None), "default_grounding_level", "balanced"
    )

    effective_retriever = (retriever or default_retriever or "semantic").lower()
    effective_weight = weight if weight is not None else default_weight

    # Expansion logic
    if expand is not None:
        effective_expansion = expand
    elif default_enable_expansion:
        effective_expansion = default_expansion_count
    else:
        effective_expansion = 0

    # Grounding level (CLI > settings > hardcoded default)
    effective_grounding_level = (grounding_level or default_grounding_level or "balanced").lower()
    
    # strict_mode wins if set explicitly
    if strict_mode or bool(getattr(getattr(settings, "query", None), "default_strict_mode", False)):
        effective_grounding_level = "strict"

    return effective_retriever, effective_weight, effective_expansion, effective_grounding_level
