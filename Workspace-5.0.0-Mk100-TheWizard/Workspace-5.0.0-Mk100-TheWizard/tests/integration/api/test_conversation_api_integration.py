"""Integration tests for conversation API using TestClient.

These tests validate the API endpoints work with real PostgreSQL database,
maintaining robust cleanup via transaction rollbacks.
"""

from __future__ import annotations

import pytest
from uuid import UUID


@pytest.fixture(scope="module")
def api_server():
    """Deprecated: using internal client fixture."""
    pass


class TestConversationAPIIntegration:
    """Integration tests for conversation API endpoints."""

    def test_health_check(self, client) -> None:
        """Test API health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_create_conversation(self, client) -> None:
        """Test creating a conversation via API."""
        response = client.post(
            "/api/conversations",
            json={"user_id": "integration_test_user"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "created_at" in data

        # Validate UUID format
        conversation_id = UUID(data["id"])
        assert conversation_id is not None

    def test_get_conversation(self, client) -> None:
        """Test retrieving a conversation with messages."""
        # First create a conversation
        create_response = client.post(
            "/api/conversations",
            json={"user_id": "test_user"},
        )
        assert create_response.status_code == 201
        conversation_id = create_response.json()["id"]

        # Then retrieve it
        get_response = client.get(
            f"/api/conversations/{conversation_id}",
        )
        assert get_response.status_code == 200
        data = get_response.json()

        assert "conversation" in data
        assert "messages" in data
        assert "total_messages" in data
        assert data["total_messages"] == 0  # No messages yet
        assert data["page"] == 1
        assert data["page_size"] == 50

    def test_create_message(self, client) -> None:
        """Test adding a message to a conversation."""
        # Create conversation
        create_conv_response = client.post(
            "/api/conversations",
            json={"user_id": "test_user"},
        )
        conversation_id = create_conv_response.json()["id"]

        # Add message
        create_msg_response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "Hello, JARVIS!",
                "agent_persona": None,
                "cost_usd": None,
                "provider": None,
                "model": None,
                "token_count": None
            },
        )
        assert create_msg_response.status_code == 201
        message_data = create_msg_response.json()
        assert "id" in message_data
        assert message_data["conversation_id"] == conversation_id

    def test_full_conversation_flow(self, client) -> None:
        """Test complete conversation flow: create -> add messages -> retrieve."""
        # Step 1: Create conversation
        conv_response = client.post(
            "/api/conversations",
            json={"user_id": "flow_test_user"},
        )
        assert conv_response.status_code == 201
        conversation_id = conv_response.json()["id"]

        # Step 2: Add multiple messages
        messages = [
            {"role": "user", "content": "What is RAG?"},
            {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation...",
             "agent_persona": "Rickiest Rick", "cost_usd": "0.002"},
            {"role": "user", "content": "How does it work?"},
        ]

        for msg in messages:
            msg_response = client.post(
                f"/api/conversations/{conversation_id}/messages",
                json=msg,
            )
            assert msg_response.status_code == 201

        # Step 3: Retrieve conversation with messages
        get_response = client.get(
            f"/api/conversations/{conversation_id}",
        )
        assert get_response.status_code == 200
        data = get_response.json()

        assert data["total_messages"] == 3
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "What is RAG?"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["agent_persona"] == "Rickiest Rick"

    def test_pagination(self, client) -> None:
        """Test message pagination."""
        # Create conversation
        conv_response = client.post(
            "/api/conversations",
            json={},
        )
        conversation_id = conv_response.json()["id"]

        # Add 15 messages
        for i in range(15):
            client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"role": "user", "content": f"Message {i+1}"},
            )

        # Get first page (10 messages)
        page1_response = client.get(
            f"/api/conversations/{conversation_id}?page=1&page_size=10",
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert page1_data["total_messages"] == 15
        assert len(page1_data["messages"]) == 10
        assert page1_data["has_more"] is True

        # Get second page (5 messages)
        page2_response = client.get(
            f"/api/conversations/{conversation_id}?page=2&page_size=10",
        )
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["messages"]) == 5
        assert page2_data["has_more"] is False

    def test_conversation_not_found(self, client) -> None:
        """Test retrieving non-existent conversation."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/conversations/{fake_id}",
        )
        assert response.status_code == 404
