"""Unit tests for personas CLI commands."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from jarvis.cli.commands import personas as personas_cli
from jarvis.database.models import AgentPersona

runner = CliRunner()


@pytest.fixture
def mock_persona_db():
    """Mock PersonaDB for testing."""
    return MagicMock()


@pytest.fixture
def mock_personas_list():
    """Mock list of personas for testing."""
    return [
        AgentPersona(
            id=1,
            name="Rickiest Rick",
            system_prompt="You are the Rickiest Rick",
            weight=Decimal("0.40"),
            is_active=True,
        ),
        AgentPersona(
            id=2,
            name="Supportive Rick",
            system_prompt="You are supportive",
            weight=Decimal("0.30"),
            is_active=True,
        ),
        AgentPersona(
            id=3,
            name="Disabled Rick",
            system_prompt="You are disabled",
            weight=Decimal("0.30"),
            is_active=False,
        ),
    ]


class TestListCommand:
    """Tests for 'jarvis personas list' command."""

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_list_command_success(self, mock_get_db, mock_persona_db, mock_personas_list):
        """Test personas list command displays all personas."""
        mock_get_db.return_value = mock_persona_db
        mock_persona_db.list_personas.return_value = mock_personas_list
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, ["Rickiest Rick", "Supportive Rick"])

        result = runner.invoke(personas_cli.app, ["list"])

        assert result.exit_code == 0
        assert "Rickiest Rick" in result.stdout
        assert "Supportive Rick" in result.stdout
        assert "40.0%" in result.stdout
        assert "Active personas weights sum to 1.000" in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_list_command_active_only(self, mock_get_db, mock_persona_db, mock_personas_list):
        """Test personas list --active filters to active personas."""
        mock_get_db.return_value = mock_persona_db
        active_only = [p for p in mock_personas_list if p.is_active]
        mock_persona_db.list_personas.return_value = active_only
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, ["Rickiest Rick", "Supportive Rick"])

        result = runner.invoke(personas_cli.app, ["list", "--active"])

        assert result.exit_code == 0
        mock_persona_db.list_personas.assert_called_once_with(active_only=True)
        assert "Disabled Rick" not in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_list_command_no_personas(self, mock_get_db, mock_persona_db):
        """Test personas list with no personas shows message."""
        mock_get_db.return_value = mock_persona_db
        mock_persona_db.list_personas.return_value = []

        result = runner.invoke(personas_cli.app, ["list"])

        assert result.exit_code == 0
        assert "No personas found" in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_list_command_invalid_weights_warning(self, mock_get_db, mock_persona_db, mock_personas_list):
        """Test personas list shows warning when weights don't sum to 100%."""
        mock_get_db.return_value = mock_persona_db
        mock_persona_db.list_personas.return_value = mock_personas_list
        mock_persona_db.validate_active_weights.return_value = (False, 0.70, ["Rickiest Rick", "Supportive Rick"])

        result = runner.invoke(personas_cli.app, ["list"])

        assert result.exit_code == 0
        assert "weights sum to 0.700" in result.stdout


class TestAddCommand:
    """Tests for 'jarvis personas add' command."""

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_add_command_with_prompt_success(self, mock_get_db, mock_persona_db):
        """Test personas add command creates persona."""
        mock_get_db.return_value = mock_persona_db
        new_persona = AgentPersona(
            id=4,
            name="Creative Rick",
            system_prompt="You are creative",
            weight=Decimal("0.15"),
            is_active=True,
        )
        mock_persona_db.create_persona.return_value = new_persona
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, [])

        result = runner.invoke(
            personas_cli.app,
            ["add", "Creative Rick", "--prompt", "You are creative", "--weight", "0.15"]
        )

        assert result.exit_code == 0
        assert "Created persona: Creative Rick" in result.stdout
        mock_persona_db.create_persona.assert_called_once_with(
            name="Creative Rick",
            system_prompt="You are creative",
            weight=0.15,
            is_active=True,
        )

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_add_command_weight_validation_error(self, mock_get_db):
        """Test personas add rejects invalid weight."""
        mock_get_db.return_value = MagicMock()

        result = runner.invoke(
            personas_cli.app,
            ["add", "Test Rick", "--prompt", "Test", "--weight", "1.5"]
        )

        assert result.exit_code == 1
        assert "Weight must be between 0.0 and 1.0" in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_add_command_inactive_flag(self, mock_get_db, mock_persona_db):
        """Test personas add with --inactive flag."""
        mock_get_db.return_value = mock_persona_db
        new_persona = AgentPersona(
            id=5,
            name="Test Rick",
            system_prompt="Test",
            weight=Decimal("0.1"),
            is_active=False,
        )
        mock_persona_db.create_persona.return_value = new_persona
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, [])

        result = runner.invoke(
            personas_cli.app,
            ["add", "Test Rick", "--prompt", "Test", "--weight", "0.1", "--inactive"]
        )

        assert result.exit_code == 0
        mock_persona_db.create_persona.assert_called_once_with(
            name="Test Rick",
            system_prompt="Test",
            weight=0.1,
            is_active=False,
        )


class TestUpdateCommand:
    """Tests for 'jarvis personas update' command."""

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_update_command_weight_success(self, mock_get_db, mock_persona_db):
        """Test personas update --weight modifies weight."""
        mock_get_db.return_value = mock_persona_db
        updated_persona = AgentPersona(
            id=1,
            name="Rickiest Rick",
            system_prompt="Original prompt",
            weight=Decimal("0.35"),
            is_active=True,
        )
        mock_persona_db.update_persona.return_value = updated_persona
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, [])

        result = runner.invoke(
            personas_cli.app,
            ["update", "Rickiest Rick", "--weight", "0.35"]
        )

        assert result.exit_code == 0
        assert "Updated persona: Rickiest Rick" in result.stdout
        mock_persona_db.update_persona.assert_called_once_with(
            name="Rickiest Rick",
            system_prompt=None,
            weight=0.35,
        )

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_update_command_prompt_success(self, mock_get_db, mock_persona_db):
        """Test personas update --prompt modifies system prompt."""
        mock_get_db.return_value = mock_persona_db
        updated_persona = AgentPersona(
            id=1,
            name="Rickiest Rick",
            system_prompt="New prompt",
            weight=Decimal("0.40"),
            is_active=True,
        )
        mock_persona_db.update_persona.return_value = updated_persona
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, [])

        result = runner.invoke(
            personas_cli.app,
            ["update", "Rickiest Rick", "--prompt", "New prompt"]
        )

        assert result.exit_code == 0
        mock_persona_db.update_persona.assert_called_once_with(
            name="Rickiest Rick",
            system_prompt="New prompt",
            weight=None,
        )

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_update_command_persona_not_found(self, mock_get_db, mock_persona_db):
        """Test personas update with nonexistent persona."""
        mock_get_db.return_value = mock_persona_db
        mock_persona_db.update_persona.return_value = None

        result = runner.invoke(
            personas_cli.app,
            ["update", "Nonexistent Rick", "--weight", "0.5"]
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_update_command_no_options_error(self, mock_get_db):
        """Test personas update without --prompt or --weight fails."""
        mock_get_db.return_value = MagicMock()

        result = runner.invoke(
            personas_cli.app,
            ["update", "Rickiest Rick"]
        )

        assert result.exit_code == 1
        assert "Must provide at least --prompt or --weight" in result.stdout


class TestEnableDisableCommands:
    """Tests for 'jarvis personas enable/disable' commands."""

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_enable_command_success(self, mock_get_db, mock_persona_db):
        """Test personas enable activates persona."""
        mock_get_db.return_value = mock_persona_db
        enabled_persona = AgentPersona(
            id=3,
            name="Test Rick",
            system_prompt="Test",
            weight=Decimal("0.3"),
            is_active=True,
        )
        mock_persona_db.enable_persona.return_value = enabled_persona
        mock_persona_db.validate_active_weights.return_value = (True, 1.0, [])

        result = runner.invoke(personas_cli.app, ["enable", "Test Rick"])

        assert result.exit_code == 0
        assert "Enabled persona: Test Rick" in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_disable_command_success(self, mock_get_db, mock_persona_db):
        """Test personas disable deactivates persona."""
        mock_get_db.return_value = mock_persona_db
        disabled_persona = AgentPersona(
            id=2,
            name="Test Rick",
            system_prompt="Test",
            weight=Decimal("0.3"),
            is_active=False,
        )
        mock_persona_db.disable_persona.return_value = disabled_persona
        active_personas = [
            AgentPersona(id=1, name="Rick A", system_prompt="A", weight=Decimal("1.0"), is_active=True)
        ]
        mock_persona_db.list_personas.return_value = active_personas

        result = runner.invoke(personas_cli.app, ["disable", "Test Rick"])

        assert result.exit_code == 0
        assert "Disabled persona: Test Rick" in result.stdout

    @patch("jarvis.cli.commands.personas.get_persona_db")
    def test_disable_command_no_active_remaining_warning(self, mock_get_db, mock_persona_db):
        """Test personas disable shows warning when no active personas remain."""
        mock_get_db.return_value = mock_persona_db
        disabled_persona = AgentPersona(
            id=1,
            name="Last Rick",
            system_prompt="Test",
            weight=Decimal("1.0"),
            is_active=False,
        )
        mock_persona_db.disable_persona.return_value = disabled_persona
        mock_persona_db.list_personas.return_value = []  # No active personas

        result = runner.invoke(personas_cli.app, ["disable", "Last Rick"])

        assert result.exit_code == 0
        assert "No active personas remaining" in result.stdout
