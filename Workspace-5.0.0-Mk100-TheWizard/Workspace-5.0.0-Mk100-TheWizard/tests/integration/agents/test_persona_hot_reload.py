"""Integration tests for persona hot-reload functionality."""

from __future__ import annotations

import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from jarvis.agents.orchestrator import PersonaRegistry
from jarvis.agents.persona_db import PersonaDB
from jarvis.agents.personas import PersonasConfig


@pytest.mark.integration
class TestPersonaHotReload:
    """Integration tests for hot-reload persona registry."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configuration files."""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def initial_personas_config(self, temp_config_dir):
        """Create initial personas.yaml configuration."""
        config_path = temp_config_dir / "personas.yaml"
        config_data = {
            "personas": [
                {
                    "name": "Rick A",
                    "system_prompt": "You are Rick A",
                    "weight": 0.6,
                    "enabled": True
                },
                {
                    "name": "Rick B",
                    "system_prompt": "You are Rick B",
                    "weight": 0.4,
                    "enabled": True
                }
            ]
        }
        config_path.write_text(json.dumps(config_data), encoding="utf-8")
        return config_path

    @pytest.fixture
    def database_url(self):
        """Get test database URL from environment."""
        import os
        return os.environ.get("TEST_DATABASE_URL", "postgresql://jarvis:jarvis@localhost:5432/jarvis_test")

    def test_persona_registry_loads_initial_config(self, initial_personas_config, database_url):
        """Test PersonaRegistry loads configuration on initialization."""
        registry = PersonaRegistry(
            config_path=initial_personas_config,
            database_url=database_url,
            watch_interval=0.5
        )

        # Check in-memory registry
        assert len(registry.personas) == 2
        assert "Rick A" in registry.personas
        assert "Rick B" in registry.personas

        # Check database sync
        persona_db = PersonaDB(database_url)
        db_personas = persona_db.list_personas()
        assert len(db_personas) >= 2  # May have other test personas

        rick_a = persona_db.get_persona_by_name("Rick A")
        assert rick_a is not None
        assert float(rick_a.weight) == 0.6

    def test_persona_registry_hot_reload_on_file_modification(self, initial_personas_config, database_url):
        """Test PersonaRegistry detects and reloads modified configuration."""
        registry = PersonaRegistry(
            config_path=initial_personas_config,
            database_url=database_url,
            watch_interval=0.5  # Fast polling for testing
        )

        # Start watching
        registry.start_watching()

        try:
            # Wait for initial watch cycle
            time.sleep(0.6)

            # Modify configuration
            modified_config = {
                "personas": [
                    {
                        "name": "Rick A",
                        "system_prompt": "You are Rick A - MODIFIED",
                        "weight": 0.7,
                        "enabled": True
                    },
                    {
                        "name": "Rick B",
                        "system_prompt": "You are Rick B",
                        "weight": 0.3,
                        "enabled": True
                    },
                    {
                        "name": "Rick C",
                        "system_prompt": "You are Rick C - NEW",
                        "weight": 0.0,
                        "enabled": False
                    }
                ]
            }
            initial_personas_config.write_text(json.dumps(modified_config), encoding="utf-8")

            # Wait for watcher to detect and reload
            time.sleep(1.5)

            # Check in-memory registry updated
            assert len(registry.personas) == 3
            assert "Rick C" in registry.personas

            rick_a = registry.get_persona("Rick A")
            assert rick_a is not None
            assert rick_a.weight == 0.7
            assert "MODIFIED" in rick_a.system_prompt

            # Check database synced
            persona_db = PersonaDB(database_url)
            rick_c = persona_db.get_persona_by_name("Rick C")
            assert rick_c is not None
            assert rick_c.is_active is False

        finally:
            registry.stop_watching()

    def test_persona_registry_deactivates_removed_personas(self, initial_personas_config, database_url):
        """Test PersonaRegistry deactivates personas removed from config."""
        registry = PersonaRegistry(
            config_path=initial_personas_config,
            database_url=database_url,
            watch_interval=0.5
        )

        registry.start_watching()

        try:
            time.sleep(0.6)

            # Remove Rick B from config
            modified_config = {
                "personas": [
                    {
                        "name": "Rick A",
                        "system_prompt": "You are Rick A",
                        "weight": 1.0,
                        "enabled": True
                    }
                ]
            }
            initial_personas_config.write_text(json.dumps(modified_config), encoding="utf-8")

            # Wait for reload
            time.sleep(1.5)

            # Check Rick B deactivated in database (not deleted)
            persona_db = PersonaDB(database_url)
            rick_b = persona_db.get_persona_by_name("Rick B")
            assert rick_b is not None  # Still exists
            assert rick_b.is_active is False  # But deactivated

        finally:
            registry.stop_watching()

    def test_persona_registry_validates_weights_after_reload(self, initial_personas_config, database_url):
        """Test PersonaRegistry validates weights after configuration reload."""
        registry = PersonaRegistry(
            config_path=initial_personas_config,
            database_url=database_url,
            watch_interval=0.5
        )

        # Modify to invalid weights
        invalid_config = {
            "personas": [
                {
                    "name": "Rick A",
                    "system_prompt": "You are Rick A",
                    "weight": 0.4,
                    "enabled": True
                },
                {
                    "name": "Rick B",
                    "system_prompt": "You are Rick B",
                    "weight": 0.4,
                    "enabled": True
                }
            ]
        }
        initial_personas_config.write_text(json.dumps(invalid_config), encoding="utf-8")

        # Reload should fail validation but not crash
        with pytest.raises(ValueError, match="must sum to 1.00"):
            registry.reload()

    def test_persona_registry_manual_reload(self, initial_personas_config, database_url):
        """Test PersonaRegistry.reload() manually triggers reload."""
        registry = PersonaRegistry(
            config_path=initial_personas_config,
            database_url=database_url,
            watch_interval=0.5
        )

        # Modify config without starting watcher
        modified_config = {
            "personas": [
                {
                    "name": "Rick A",
                    "system_prompt": "You are Rick A - MANUAL RELOAD",
                    "weight": 0.5,
                    "enabled": True
                },
                {
                    "name": "Rick B",
                    "system_prompt": "You are Rick B",
                    "weight": 0.5,
                    "enabled": True
                }
            ]
        }
        initial_personas_config.write_text(json.dumps(modified_config), encoding="utf-8")

        # Manual reload
        registry.reload()

        # Check updated
        rick_a = registry.get_persona("Rick A")
        assert "MANUAL RELOAD" in rick_a.system_prompt


@pytest.mark.integration
class TestPersonaYamlPostgreSQLSync:
    """Integration tests for YAML → PostgreSQL sync."""

    @pytest.fixture
    def database_url(self):
        """Get test database URL."""
        import os
        return os.environ.get("TEST_DATABASE_URL", "postgresql://jarvis:jarvis@localhost:5432/jarvis_test")

    def test_sync_from_config_creates_new_personas(self, database_url):
        """Test sync_from_config creates new personas in database."""
        from jarvis.agents.personas import PersonaConfig

        persona_db = PersonaDB(database_url)

        # Create test personas
        personas = [
            PersonaConfig("Sync Test Rick A", "Prompt A", 0.5, True),
            PersonaConfig("Sync Test Rick B", "Prompt B", 0.5, True),
        ]

        # Sync to database
        persona_db.sync_from_config(personas)

        # Verify created
        rick_a = persona_db.get_persona_by_name("Sync Test Rick A")
        assert rick_a is not None
        assert rick_a.system_prompt == "Prompt A"
        assert float(rick_a.weight) == 0.5
        assert rick_a.is_active is True

        # Cleanup
        persona_db.delete_persona("Sync Test Rick A")
        persona_db.delete_persona("Sync Test Rick B")

    def test_sync_from_config_updates_existing_personas(self, database_url):
        """Test sync_from_config updates existing personas."""
        from jarvis.agents.personas import PersonaConfig

        persona_db = PersonaDB(database_url)

        # Ensure clean baseline for idempotent test runs
        persona_db.delete_persona("Update Test Rick")

        # Create initial persona
        persona_db.create_persona("Update Test Rick", "Original prompt", 0.5, True)

        # Sync with modified version
        updated_personas = [
            PersonaConfig("Update Test Rick", "Updated prompt", 0.6, False),
        ]
        persona_db.sync_from_config(updated_personas)

        # Verify updated
        rick = persona_db.get_persona_by_name("Update Test Rick")
        assert rick.system_prompt == "Updated prompt"
        assert float(rick.weight) == 0.6
        assert rick.is_active is False

        # Cleanup
        persona_db.delete_persona("Update Test Rick")

    def test_sync_from_config_deactivates_removed_personas(self, database_url):
        """Test sync_from_config deactivates personas not in config."""
        from jarvis.agents.personas import PersonaConfig

        persona_db = PersonaDB(database_url)

        # Ensure clean baseline for idempotent test runs
        persona_db.delete_persona("Deactivate Test Rick A")
        persona_db.delete_persona("Deactivate Test Rick B")

        # Create two personas
        persona_db.create_persona("Deactivate Test Rick A", "Prompt A", 0.5, True)
        persona_db.create_persona("Deactivate Test Rick B", "Prompt B", 0.5, True)

        # Sync with only Rick A
        synced_personas = [
            PersonaConfig("Deactivate Test Rick A", "Prompt A", 1.0, True),
        ]
        persona_db.sync_from_config(synced_personas)

        # Verify Rick B deactivated
        rick_b = persona_db.get_persona_by_name("Deactivate Test Rick B")
        assert rick_b is not None  # Still exists
        assert rick_b.is_active is False  # But deactivated

        # Cleanup
        persona_db.delete_persona("Deactivate Test Rick A")
        persona_db.delete_persona("Deactivate Test Rick B")
