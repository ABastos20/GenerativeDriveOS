"""Persona sync and validation utilities - Separated for complexity compliance.

This module handles persona synchronization from config and validation logic.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from jarvis.agents.personas import PersonaConfig
from jarvis.database.models import AgentPersona


class PersonaSyncer:
    """Handles persona config synchronization to database."""

    def __init__(self, session: Session):
        self.session = session

    def sync(self, personas_config: List[PersonaConfig]) -> None:
        """Sync personas from configuration to database."""
        existing = self._get_existing_personas()
        config_names = {p.name for p in personas_config}

        self._update_or_create(personas_config, existing)
        self._deactivate_removed(existing, config_names)
        self.session.commit()

    def _get_existing_personas(self) -> dict[str, AgentPersona]:
        """Get existing personas as name->persona dict."""
        return {p.name: p for p in self.session.execute(select(AgentPersona)).scalars().all()}

    def _update_or_create(self, configs: List[PersonaConfig], existing: dict[str, AgentPersona]) -> None:
        """Update existing or create new personas."""
        for config in configs:
            if config.name in existing:
                self._update_persona(existing[config.name], config)
            else:
                self._create_persona(config)

    def _update_persona(self, persona: AgentPersona, config: PersonaConfig) -> None:
        """Update existing persona from config."""
        persona.system_prompt = config.system_prompt
        persona.weight = Decimal(str(config.weight))
        persona.is_active = config.enabled

    def _create_persona(self, config: PersonaConfig) -> None:
        """Create new persona from config."""
        new_persona = AgentPersona(
            name=config.name,
            system_prompt=config.system_prompt,
            weight=Decimal(str(config.weight)),
            is_active=config.enabled,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(new_persona)

    @staticmethod
    def _deactivate_removed(existing: dict[str, AgentPersona], config_names: Set[str]) -> None:
        """Deactivate personas not in config."""
        for name, persona in existing.items():
            if name not in config_names:
                persona.is_active = False


class PersonaValidator:
    """Validation logic for personas."""

    @staticmethod
    def validate_weight(weight: float) -> None:
        """Validate persona weight is between 0.0 and 1.0."""
        if not (0.0 <= weight <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")

    @staticmethod
    def validate_system_prompt(system_prompt: str) -> None:
        """Validate system prompt is not empty."""
        if not system_prompt:
            raise ValueError("system_prompt cannot be empty")

    @staticmethod
    def validate_active_weights(personas: List[AgentPersona]) -> tuple[bool, float, List[str]]:
        """Validate that active personas weights sum to 1.00."""
        if not personas:
            return False, 0.0, []

        total_weight = sum(float(p.weight) for p in personas)
        names = [p.name for p in personas]
        is_valid = abs(total_weight - 1.0) <= 0.005  # 0.5% tolerance
        return is_valid, total_weight, names

    @staticmethod
    def apply_updates(
        persona: AgentPersona,
        system_prompt: str | None,
        weight: float | None,
        is_active: bool | None,
    ) -> None:
        """Apply validated updates to a persona object."""
        if system_prompt is not None:
            PersonaValidator.validate_system_prompt(system_prompt)
            persona.system_prompt = system_prompt
        if weight is not None:
            PersonaValidator.validate_weight(weight)
            persona.weight = Decimal(str(weight))
        if is_active is not None:
            persona.is_active = is_active
