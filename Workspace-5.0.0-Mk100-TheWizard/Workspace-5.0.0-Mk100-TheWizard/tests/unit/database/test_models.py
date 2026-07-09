"""Unit tests for SQLAlchemy database models.

Tests model instantiation, validation, relationships, and UTC timestamp handling.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from src.jarvis.database.models import (
    AgentPersona,
    Conversation,
    LLMProvider,
    LLMUsageLog,
    Message,
)


class TestConversationModel(unittest.TestCase):
    """Test Conversation model."""

    def test_conversation_instantiation(self) -> None:
        """Test creating a Conversation instance."""
        conversation = Conversation()
        conversation.user_id = "test_user"
        conversation.created_at = datetime.now(timezone.utc)
        conversation.updated_at = datetime.now(timezone.utc)

        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.user_id, "test_user")
        self.assertIsInstance(conversation.created_at, datetime)
        self.assertEqual(conversation.created_at.tzinfo, timezone.utc)

    def test_conversation_repr(self) -> None:
        """Test Conversation __repr__ method."""
        conversation = Conversation()
        conversation.id = "123e4567-e89b-12d3-a456-426614174000"
        conversation.created_at = datetime(2025, 11, 17, 15, 30, 0, tzinfo=timezone.utc)

        repr_str = repr(conversation)
        self.assertIn("Conversation", repr_str)
        self.assertIn("123e4567-e89b-12d3-a456-426614174000", repr_str)


class TestMessageModel(unittest.TestCase):
    """Test Message model."""

    def test_message_instantiation(self) -> None:
        """Test creating a Message instance."""
        message = Message()
        message.role = "user"
        message.content = "Hello, JARVIS!"
        message.agent_persona = "Rickiest Rick"
        message.cost_usd = Decimal("0.002")
        message.provider = "openrouter"
        message.model = "meta-llama/llama-3.1-70b"
        message.token_count = 1250
        message.created_at = datetime.now(timezone.utc)

        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello, JARVIS!")
        self.assertEqual(message.agent_persona, "Rickiest Rick")
        self.assertIsInstance(message.cost_usd, Decimal)
        self.assertEqual(message.provider, "openrouter")
        self.assertEqual(message.token_count, 1250)

    def test_message_utc_timestamp(self) -> None:
        """Test Message timestamps are UTC."""
        message = Message()
        message.created_at = datetime.now(timezone.utc)

        self.assertEqual(message.created_at.tzinfo, timezone.utc)


class TestLLMProviderModel(unittest.TestCase):
    """Test LLMProvider model."""

    def test_llm_provider_instantiation(self) -> None:
        """Test creating an LLMProvider instance."""
        provider = LLMProvider()
        provider.name = "openrouter"
        provider.type = "free_tier"
        provider.priority = 1
        provider.quota_limit = 1000000
        provider.tokens_used = 50000
        provider.api_key_env = "OPENROUTER_API_KEY"
        provider.is_active = True

        self.assertEqual(provider.name, "openrouter")
        self.assertEqual(provider.type, "free_tier")
        self.assertEqual(provider.priority, 1)
        self.assertEqual(provider.quota_limit, 1000000)
        self.assertEqual(provider.tokens_used, 50000)
        self.assertTrue(provider.is_active)

    def test_llm_provider_repr(self) -> None:
        """Test LLMProvider __repr__ method."""
        provider = LLMProvider()
        provider.id = 1
        provider.name = "together_ai"
        provider.type = "free_tier"
        provider.is_active = True

        repr_str = repr(provider)
        self.assertIn("LLMProvider", repr_str)
        self.assertIn("together_ai", repr_str)
        self.assertIn("free_tier", repr_str)


class TestLLMUsageLogModel(unittest.TestCase):
    """Test LLMUsageLog model."""

    def test_usage_log_instantiation(self) -> None:
        """Test creating an LLMUsageLog instance."""
        log = LLMUsageLog()
        log.provider_id = 1
        log.model = "meta-llama/llama-3.1-70b"
        log.tokens_input = 500
        log.tokens_output = 750
        log.cost_usd = Decimal("0.002")
        log.created_at = datetime.now(timezone.utc)

        self.assertEqual(log.provider_id, 1)
        self.assertEqual(log.model, "meta-llama/llama-3.1-70b")
        self.assertEqual(log.tokens_input, 500)
        self.assertEqual(log.tokens_output, 750)
        self.assertEqual(log.cost_usd, Decimal("0.002"))
        self.assertIsInstance(log.created_at, datetime)

    def test_usage_log_repr(self) -> None:
        """Test LLMUsageLog __repr__ method."""
        log = LLMUsageLog()
        log.id = 1
        log.provider_id = 1
        log.tokens_input = 500
        log.tokens_output = 750
        log.cost_usd = Decimal("0.002")

        repr_str = repr(log)
        self.assertIn("LLMUsageLog", repr_str)
        self.assertIn("500", repr_str)
        self.assertIn("750", repr_str)


class TestAgentPersonaModel(unittest.TestCase):
    """Test AgentPersona model."""

    def test_agent_persona_instantiation(self) -> None:
        """Test creating an AgentPersona instance."""
        persona = AgentPersona()
        persona.name = "Rickiest Rick"
        persona.system_prompt = "You are the Rickiest Rick..."
        persona.weight = Decimal("0.40")
        persona.is_active = True
        persona.created_at = datetime.now(timezone.utc)

        self.assertEqual(persona.name, "Rickiest Rick")
        self.assertEqual(persona.system_prompt, "You are the Rickiest Rick...")
        self.assertEqual(persona.weight, Decimal("0.40"))
        self.assertTrue(persona.is_active)

    def test_agent_persona_repr(self) -> None:
        """Test AgentPersona __repr__ method."""
        persona = AgentPersona()
        persona.id = 1
        persona.name = "Supportive Rick"
        persona.weight = Decimal("0.20")
        persona.is_active = True

        repr_str = repr(persona)
        self.assertIn("AgentPersona", repr_str)
        self.assertIn("Supportive Rick", repr_str)
        self.assertIn("0.20", repr_str)


if __name__ == "__main__":
    unittest.main()
