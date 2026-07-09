"""Council of Ricks orchestrator with hot-reload persona registry.

This module implements the Rickiest Rick - the main orchestrator that manages
the persona registry and hot-reload mechanism for dynamic configuration updates.
"""

from __future__ import annotations

import time
from pathlib import Path
from threading import Thread
from typing import Dict, Optional

import structlog

from jarvis.agents.persona_db import PersonaDB
from jarvis.agents.personas import PersonaConfig, PersonasConfig, load_personas_config

logger = structlog.get_logger(__name__)


class PersonaRegistry:
    """Registry of personas with hot-reload capability.

    Watches personas.yaml for modifications and automatically syncs changes
    to PostgreSQL without requiring application restart.
    """

    def __init__(
        self,
        config_path: Path,
        database_url: str,
        watch_interval: float = 2.0,
    ):
        """Initialize persona registry.

        Args:
            config_path: Path to personas.yaml configuration file
            database_url: PostgreSQL connection string
            watch_interval: Seconds between file modification checks (default: 2.0)
        """
        self.config_path = config_path
        self.database_url = database_url
        self.watch_interval = watch_interval

        self._persona_db = PersonaDB(database_url)
        self._personas: Dict[str, PersonaConfig] = {}
        self._last_modified: Optional[float] = None
        self._watcher_thread: Optional[Thread] = None
        self._watching = False

        # Initial load
        self._reload_config()

    def _reload_config(self, raise_on_error: bool = False) -> None:
        """Reload personas configuration from YAML and sync to database.

        Args:
            raise_on_error: If True, propagate exceptions to the caller.
                            Used by the public ``reload`` method so tests
                            can assert on validation failures. The watcher
                            and constructor keep the previous behaviour of
                            logging and continuing on errors.
        """
        try:
            logger.info("reloading_personas_config", config_path=str(self.config_path))

            # Load and validate configuration
            personas_config = load_personas_config(self.config_path)

            # Sync to database
            self._persona_db.sync_from_config(personas_config.personas)

            # Update in-memory registry
            self._personas = {p.name: p for p in personas_config.personas}

            # Update last modified timestamp
            self._last_modified = self.config_path.stat().st_mtime

            # Validate weights
            is_valid, total_weight, active_names = self._persona_db.validate_active_weights()

            logger.info(
                "personas_reloaded",
                count=len(self._personas),
                active_count=len(active_names),
                total_weight=total_weight,
                weights_valid=is_valid,
            )

            if not is_valid:
                logger.warning(
                    "persona_weights_invalid",
                    total_weight=total_weight,
                    active_personas=active_names,
                    message="Active persona weights do not sum to 1.00"
                )

        except Exception as exc:
            logger.error(
                "personas_reload_failed",
                error=str(exc),
                config_path=str(self.config_path),
            )
            # Don't crash for background reloads, but allow the explicit
            # reload() call to surface validation errors.
            if raise_on_error:
                raise

    def _watch_config_file(self) -> None:
        """Watch configuration file for modifications and reload on change."""
        logger.info("starting_persona_watcher", config_path=str(self.config_path))

        while self._watching:
            try:
                if not self.config_path.exists():
                    logger.warning("personas_config_missing", config_path=str(self.config_path))
                    time.sleep(self.watch_interval)
                    continue

                current_modified = self.config_path.stat().st_mtime

                if self._last_modified is None or current_modified > self._last_modified:
                    logger.info("personas_config_modified", config_path=str(self.config_path))
                    self._reload_config()

            except Exception as exc:
                logger.error("persona_watcher_error", error=str(exc))

            time.sleep(self.watch_interval)

        logger.info("persona_watcher_stopped")

    def start_watching(self) -> None:
        """Start background thread to watch for configuration changes."""
        if self._watching:
            logger.warning("persona_watcher_already_running")
            return

        self._watching = True
        self._watcher_thread = Thread(target=self._watch_config_file, daemon=True)
        self._watcher_thread.start()

        logger.info("persona_watcher_started")

    def stop_watching(self) -> None:
        """Stop watching configuration file."""
        if not self._watching:
            return

        self._watching = False

        if self._watcher_thread:
            self._watcher_thread.join(timeout=5.0)
            self._watcher_thread = None

        logger.info("persona_watcher_stopped")

    def get_persona(self, name: str) -> Optional[PersonaConfig]:
        """Get persona by name from in-memory registry.

        Args:
            name: Persona name

        Returns:
            PersonaConfig if found, None otherwise
        """
        return self._personas.get(name)

    def get_enabled_personas(self) -> Dict[str, PersonaConfig]:
        """Get all enabled personas.

        Returns:
            Dictionary of {name: PersonaConfig} for enabled personas
        """
        return {name: p for name, p in self._personas.items() if p.enabled}

    def reload(self) -> None:
        """Manually trigger configuration reload.

        Useful for forcing a reload without waiting for file watcher.
        """
        self._reload_config(raise_on_error=True)

    @property
    def personas(self) -> Dict[str, PersonaConfig]:
        """Get all personas (enabled and disabled)."""
        return dict(self._personas)  # Return copy to prevent external modification
