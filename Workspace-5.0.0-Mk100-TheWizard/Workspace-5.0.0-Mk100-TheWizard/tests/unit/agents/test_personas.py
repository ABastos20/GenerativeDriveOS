"""Unit tests for persona configuration schema and validation."""

from __future__ import annotations

import pytest

from jarvis.agents.personas import PersonaConfig, PersonasConfig


class TestPersonaConfig:
    """Tests for PersonaConfig dataclass."""

    def test_persona_config_valid(self):
        """Test creating valid PersonaConfig."""
        persona = PersonaConfig(
            name="Test Rick",
            system_prompt="You are a test persona",
            weight=0.25,
            enabled=True
        )

        assert persona.name == "Test Rick"
        assert persona.system_prompt == "You are a test persona"
        assert persona.weight == 0.25
        assert persona.enabled is True

    def test_persona_config_default_enabled(self):
        """Test PersonaConfig defaults enabled to True."""
        persona = PersonaConfig(
            name="Test Rick",
            system_prompt="Test prompt",
            weight=0.5
        )

        assert persona.enabled is True

    def test_persona_config_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            PersonaConfig(
                name="",
                system_prompt="Test prompt",
                weight=0.5
            )

    def test_persona_config_empty_prompt_raises_error(self):
        """Test that empty system_prompt raises ValueError."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            PersonaConfig(
                name="Test Rick",
                system_prompt="",
                weight=0.5
            )

    def test_persona_config_weight_too_low_raises_error(self):
        """Test that weight < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="weight must be between 0.0 and 1.0"):
            PersonaConfig(
                name="Test Rick",
                system_prompt="Test prompt",
                weight=-0.1
            )

    def test_persona_config_weight_too_high_raises_error(self):
        """Test that weight > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="weight must be between 0.0 and 1.0"):
            PersonaConfig(
                name="Test Rick",
                system_prompt="Test prompt",
                weight=1.5
            )

    def test_persona_config_weight_boundaries(self):
        """Test that weight boundaries 0.0 and 1.0 are valid."""
        # Test 0.0
        persona_zero = PersonaConfig(
            name="Zero Rick",
            system_prompt="Test",
            weight=0.0
        )
        assert persona_zero.weight == 0.0

        # Test 1.0
        persona_one = PersonaConfig(
            name="One Rick",
            system_prompt="Test",
            weight=1.0
        )
        assert persona_one.weight == 1.0

    def test_persona_config_to_dict(self):
        """Test PersonaConfig.to_dict() serialization."""
        persona = PersonaConfig(
            name="Test Rick",
            system_prompt="You are a test",
            weight=0.3,
            enabled=False
        )

        result = persona.to_dict()

        assert result == {
            "name": "Test Rick",
            "system_prompt": "You are a test",
            "weight": 0.3,
            "enabled": False
        }


class TestPersonasConfig:
    """Tests for PersonasConfig collection with weight validation."""

    def test_personas_config_valid_weights_sum_to_100(self):
        """Test PersonasConfig with valid weights summing to 1.00."""
        personas = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 0.4, True),
            PersonaConfig("Rick B", "Prompt B", 0.3, True),
            PersonaConfig("Rick C", "Prompt C", 0.3, True),
        ])

        assert len(personas.personas) == 3

    def test_personas_config_weights_sum_to_100_with_disabled(self):
        """Test that disabled personas don't count toward weight total."""
        personas = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 0.5, True),
            PersonaConfig("Rick B", "Prompt B", 0.5, True),
            PersonaConfig("Rick C", "Prompt C", 0.2, False),  # Disabled
        ])

        # Should pass - only enabled personas (0.5 + 0.5 = 1.0) count
        assert len(personas.personas) == 3

    def test_personas_config_weights_not_sum_to_100_raises_error(self):
        """Test that weights not summing to 1.00 raises ValueError."""
        with pytest.raises(ValueError, match="must sum to 1.00"):
            PersonasConfig(personas=[
                PersonaConfig("Rick A", "Prompt A", 0.4, True),
                PersonaConfig("Rick B", "Prompt B", 0.4, True),
            ])

    def test_personas_config_weights_tolerance(self):
        """Test weight validation allows small floating point tolerance (0.5%)."""
        # 0.333 + 0.333 + 0.333 = 0.999 (within 0.5% tolerance)
        personas = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 0.333, True),
            PersonaConfig("Rick B", "Prompt B", 0.333, True),
            PersonaConfig("Rick C", "Prompt C", 0.333, True),
        ])

        assert len(personas.personas) == 3

    def test_personas_config_empty_list_raises_error(self):
        """Test that empty personas list raises ValueError."""
        with pytest.raises(ValueError, match="must contain at least one persona"):
            PersonasConfig(personas=[])

    def test_personas_config_no_enabled_personas_raises_error(self):
        """Test that all disabled personas raises ValueError."""
        with pytest.raises(ValueError, match="must have at least one enabled persona"):
            PersonasConfig(personas=[
                PersonaConfig("Rick A", "Prompt A", 1.0, False),
            ])

    def test_personas_config_from_dict_valid(self):
        """Test PersonasConfig.from_dict() with valid data."""
        data = {
            "personas": [
                {
                    "name": "Rick A",
                    "system_prompt": "Prompt A",
                    "weight": 0.6,
                    "enabled": True
                },
                {
                    "name": "Rick B",
                    "system_prompt": "Prompt B",
                    "weight": 0.4,
                    "enabled": True
                }
            ]
        }

        config = PersonasConfig.from_dict(data)

        assert len(config.personas) == 2
        assert config.personas[0].name == "Rick A"
        assert config.personas[1].name == "Rick B"

    def test_personas_config_from_dict_missing_personas_key(self):
        """Test PersonasConfig.from_dict() with missing 'personas' key."""
        with pytest.raises(ValueError, match="must contain 'personas' key"):
            PersonasConfig.from_dict({})

    def test_personas_config_from_dict_personas_not_list(self):
        """Test PersonasConfig.from_dict() with non-list personas value."""
        with pytest.raises(ValueError, match="must be a list"):
            PersonasConfig.from_dict({"personas": "not a list"})

    def test_personas_config_from_dict_invalid_persona(self):
        """Test PersonasConfig.from_dict() with invalid persona data."""
        data = {
            "personas": [
                {
                    "name": "Rick A",
                    "system_prompt": "Prompt A",
                    "weight": 1.5,  # Invalid weight
                    "enabled": True
                }
            ]
        }

        with pytest.raises(ValueError, match="Invalid persona at index 0"):
            PersonasConfig.from_dict(data)

    def test_personas_config_to_dict(self):
        """Test PersonasConfig.to_dict() serialization."""
        config = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 1.0, True),
            PersonaConfig("Rick B", "Prompt B", 0.3, False),
        ])

        result = config.to_dict()

        assert result == {
            "personas": [
                {
                    "name": "Rick A",
                    "system_prompt": "Prompt A",
                    "weight": 1.0,
                    "enabled": True
                },
                {
                    "name": "Rick B",
                    "system_prompt": "Prompt B",
                    "weight": 0.3,
                    "enabled": False
                }
            ]
        }

    def test_personas_config_get_enabled_personas(self):
        """Test PersonasConfig.get_enabled_personas() returns only enabled."""
        config = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 0.5, True),
            PersonaConfig("Rick B", "Prompt B", 0.5, True),
            PersonaConfig("Rick C", "Prompt C", 0.1, False),
        ])

        enabled = config.get_enabled_personas()

        assert len(enabled) == 2
        assert all(p.enabled for p in enabled)
        assert enabled[0].name == "Rick A"
        assert enabled[1].name == "Rick B"

    def test_personas_config_get_persona_by_name(self):
        """Test PersonasConfig.get_persona_by_name() lookup."""
        config = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 0.5, True),
            PersonaConfig("Rick B", "Prompt B", 0.5, True),
        ])

        persona = config.get_persona_by_name("Rick B")

        assert persona is not None
        assert persona.name == "Rick B"
        assert persona.system_prompt == "Prompt B"

    def test_personas_config_get_persona_by_name_not_found(self):
        """Test PersonasConfig.get_persona_by_name() returns None if not found."""
        config = PersonasConfig(personas=[
            PersonaConfig("Rick A", "Prompt A", 1.0, True),
        ])

        persona = config.get_persona_by_name("Nonexistent Rick")

        assert persona is None
