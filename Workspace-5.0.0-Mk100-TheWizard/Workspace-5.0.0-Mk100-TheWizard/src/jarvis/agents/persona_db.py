"""CRUD operations for persona management in PostgreSQL.

This module provides database operations for the Council of Ricks persona system,
interacting with the existing agent_personas table from Epic 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from jarvis.agents.personas import PersonaConfig
from jarvis.database.models import AgentPersona


class PersonaDB:
    """Database operations for agent personas."""

    def __init__(self, database_url: str):
        """Initialize persona database connection.

        Args:
            database_url: PostgreSQL connection string
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @staticmethod
    def _validate_weight(weight: float) -> None:
        """Validate persona weight."""
        if not (0.0 <= weight <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")

    @staticmethod
    def _validate_system_prompt(system_prompt: str) -> None:
        """Validate system prompt is not empty."""
        if not system_prompt:
            raise ValueError("system_prompt cannot be empty")

    def create_persona(
        self,
        name: str,
        system_prompt: str,
        weight: float,
        is_active: bool = True,
    ) -> AgentPersona:
        """Create a new persona in the database.

        Args:
            name: Unique persona name
            system_prompt: LLM system prompt
            weight: Voting weight (0.0-1.0)
            is_active: Whether persona is enabled

        Returns:
            Created AgentPersona instance

        Raises:
            IntegrityError: If persona name already exists
            ValueError: If validation fails
        """
        self._validate_weight(weight)

        with self.SessionLocal() as session:
            persona = AgentPersona(
                name=name,
                system_prompt=system_prompt,
                weight=Decimal(str(weight)),  # Convert float to Decimal for precision
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
            )

            try:
                session.add(persona)
                session.commit()
                session.refresh(persona)
                return persona
            except IntegrityError as exc:
                session.rollback()
                raise IntegrityError(
                    f"Persona '{name}' already exists",
                    params=None,
                    orig=exc.orig,
                ) from exc

    def get_persona_by_name(self, name: str) -> Optional[AgentPersona]:
        """Get persona by name.

        Args:
            name: Persona name (case-sensitive)

        Returns:
            AgentPersona if found, None otherwise
        """
        with self.SessionLocal() as session:
            stmt = select(AgentPersona).where(AgentPersona.name == name)
            result = session.execute(stmt)
            return result.scalar_one_or_none()

    def get_persona_by_id(self, persona_id: int) -> Optional[AgentPersona]:
        """Get persona by ID.

        Args:
            persona_id: Persona primary key

        Returns:
            AgentPersona if found, None otherwise
        """
        with self.SessionLocal() as session:
            stmt = select(AgentPersona).where(AgentPersona.id == persona_id)
            result = session.execute(stmt)
            return result.scalar_one_or_none()

    def list_personas(self, active_only: bool = False) -> List[AgentPersona]:
        """List all personas.

        Args:
            active_only: If True, return only active personas

        Returns:
            List of AgentPersona instances
        """
        with self.SessionLocal() as session:
            stmt = select(AgentPersona)

            if active_only:
                stmt = stmt.where(AgentPersona.is_active == True)

            stmt = stmt.order_by(AgentPersona.weight.desc())  # Sort by weight descending
            result = session.execute(stmt)
            return list(result.scalars().all())

    def update_persona(
        self,
        name: str,
        system_prompt: Optional[str] = None,
        weight: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[AgentPersona]:
        """Update persona properties."""
        from jarvis.agents.persona_helpers import PersonaValidator
        with self.SessionLocal() as session:
            persona = session.execute(
                select(AgentPersona).where(AgentPersona.name == name)
            ).scalar_one_or_none()

            if persona is None:
                return None

            PersonaValidator.apply_updates(persona, system_prompt, weight, is_active)
            session.commit()
            session.refresh(persona)
            return persona

    def delete_persona(self, name: str) -> bool:
        """Delete persona by name.

        Args:
            name: Persona name to delete

        Returns:
            True if deleted, False if not found
        """
        with self.SessionLocal() as session:
            persona = session.execute(
                select(AgentPersona).where(AgentPersona.name == name)
            ).scalar_one_or_none()

            if persona is None:
                return False

            session.delete(persona)
            session.commit()
            return True

    def enable_persona(self, name: str) -> Optional[AgentPersona]:
        """Enable persona (set is_active = True).

        Args:
            name: Persona name

        Returns:
            Updated AgentPersona if found, None otherwise
        """
        return self.update_persona(name, is_active=True)

    def disable_persona(self, name: str) -> Optional[AgentPersona]:
        """Disable persona (set is_active = False).

        Args:
            name: Persona name

        Returns:
            Updated AgentPersona if found, None otherwise
        """
        return self.update_persona(name, is_active=False)

    def sync_from_config(self, personas_config: List[PersonaConfig]) -> None:
        """Sync personas from configuration to database."""
        from jarvis.agents.persona_helpers import PersonaSyncer
        with self.SessionLocal() as session:
            syncer = PersonaSyncer(session)
            syncer.sync(personas_config)

    def validate_active_weights(self) -> tuple[bool, float, List[str]]:
        """Validate that active personas weights sum to 1.00."""
        from jarvis.agents.persona_helpers import PersonaValidator
        active_personas = self.list_personas(active_only=True)
        return PersonaValidator.validate_active_weights(active_personas)
