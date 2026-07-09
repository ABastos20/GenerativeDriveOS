"""Persona configuration schema and validation for Council of Ricks.

This module defines the pydantic schema for agent personas, including:
- PersonaConfig: Individual persona definition
- PersonasConfig: Collection of personas with weight validation
- YAML loading and validation utilities

Weight validation ensures enabled personas sum to exactly 100% (1.00 decimal).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PersonaConfig:
    """Configuration for a single agent persona.

    Attributes:
        name: Persona identifier (e.g., "Rickiest Rick", "Supportive Rick")
        system_prompt: LLM system prompt defining persona behavior
        weight: Voting weight as decimal (0.00-1.00), must sum to 1.00 across enabled personas
        enabled: Whether persona is active in consensus voting
    """

    name: str
    system_prompt: str
    weight: float
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate persona configuration."""
        if not self.name:
            raise ValueError("Persona name cannot be empty")

        if not self.system_prompt:
            raise ValueError(f"Persona '{self.name}' system_prompt cannot be empty")

        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(
                f"Persona '{self.name}' weight must be between 0.0 and 1.0, got {self.weight}"
            )

    def to_dict(self) -> Dict[str, any]:
        """Convert persona to dictionary for serialization."""
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "weight": float(self.weight),
            "enabled": self.enabled,
        }


@dataclass
class PersonasConfig:
    """Collection of persona configurations with weight validation.

    Validates that enabled personas' weights sum to exactly 100% (1.00 decimal).
    """

    personas: List[PersonaConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate personas collection."""
        if not self.personas:
            raise ValueError("PersonasConfig must contain at least one persona")

        # Validate enabled personas weights sum to 1.00
        enabled_personas = [p for p in self.personas if p.enabled]

        if not enabled_personas:
            raise ValueError("PersonasConfig must have at least one enabled persona")

        total_weight = sum(p.weight for p in enabled_personas)

        # Allow small floating point tolerance (0.005 = 0.5%)
        if abs(total_weight - 1.0) > 0.005:
            enabled_names = [p.name for p in enabled_personas]
            raise ValueError(
                f"Enabled personas weights must sum to 1.00 (100%), got {total_weight:.3f}. "
                f"Enabled personas: {enabled_names}"
            )

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> PersonasConfig:
        """Load PersonasConfig from dictionary (parsed from YAML/JSON).

        Args:
            data: Dictionary with 'personas' key containing list of persona dicts

        Returns:
            Validated PersonasConfig instance

        Raises:
            ValueError: If validation fails
        """
        if "personas" not in data:
            raise ValueError("Configuration must contain 'personas' key")

        personas_data = data["personas"]

        if not isinstance(personas_data, list):
            raise ValueError("'personas' must be a list")

        personas = []
        for idx, persona_dict in enumerate(personas_data):
            if not isinstance(persona_dict, dict):
                raise ValueError(f"Persona at index {idx} must be a dictionary")

            try:
                persona = PersonaConfig(
                    name=persona_dict.get("name", ""),
                    system_prompt=persona_dict.get("system_prompt", ""),
                    weight=float(persona_dict.get("weight", 0.0)),
                    enabled=bool(persona_dict.get("enabled", True)),
                )
                personas.append(persona)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid persona at index {idx}: {exc}") from exc

        return cls(personas=personas)

    def to_dict(self) -> Dict[str, any]:
        """Convert personas config to dictionary for serialization."""
        return {
            "personas": [p.to_dict() for p in self.personas]
        }

    def get_enabled_personas(self) -> List[PersonaConfig]:
        """Get list of enabled personas."""
        return [p for p in self.personas if p.enabled]

    def get_persona_by_name(self, name: str) -> Optional[PersonaConfig]:
        """Get persona by name (case-sensitive).

        Args:
            name: Persona name to find

        Returns:
            PersonaConfig if found, None otherwise
        """
        for persona in self.personas:
            if persona.name == name:
                return persona
        return None


def load_personas_config(config_path: Path) -> PersonasConfig:
    """Load and validate personas configuration from YAML file.

    Args:
        config_path: Path to personas.yaml file

    Returns:
        Validated PersonasConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Personas config file not found: {config_path}")

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON/YAML in {config_path}: {exc}") from exc

    return PersonasConfig.from_dict(data)
