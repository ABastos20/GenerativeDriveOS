"""Integration tests for MCP log_message provenance storage.

These tests validate that citation_provenance sent via /mcp/log_message
is persisted on the corresponding message record and exposed via the
conversation API.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

import pytest
import requests


API_BASE_URL = "http://localhost:8000"
MCP_BASE_URL = "http://localhost:8001"


@pytest.mark.integration
class TestMCPProvenanceIntegration:
    """Integration tests for MCP provenance logging."""

    def test_mcp_log_message_persists_citation_provenance(self) -> None:
        """Round-trip citation_provenance via MCP -> DB -> conversation API."""

        provenance: List[Dict[str, Any]] = [
            {
                "id": 1,
                "content": "Test snippet",
                "source_file": "/tmp/test.md",
                "section": "Test Section",
                "domain": "jarvis-core",
                "relevance_score": 0.99,
                "score": 0.99,
                "chunk_id": "chunk-1",
                "hash": "deadbeef",
            }
        ]

        # Log assistant message with provenance via MCP
        mcp_response = requests.post(
            f"{MCP_BASE_URL}/mcp/log_message",
            json={
                "agent": "integration-mcp-test",
                "role": "assistant",
                "content": "Test answer with citations",
                "citation_provenance": provenance,
            },
            timeout=5,
        )
        assert mcp_response.status_code == 200
        mcp_data = mcp_response.json()
        conversation_id = UUID(mcp_data["conversation_id"])
        message_id = UUID(mcp_data["message_id"])

        # Fetch conversation via API and verify the stored provenance
        conv_response = requests.get(
            f"{API_BASE_URL}/api/conversations/{conversation_id}",
            timeout=5,
        )
        assert conv_response.status_code == 200
        conv_data = conv_response.json()

        messages = conv_data.get("messages", [])
        # Find the message we just logged
        target = None
        for msg in messages:
            if msg.get("id") == str(message_id):
                target = msg
                break

        assert target is not None, "Logged MCP message not found in conversation API response"
        assert target["role"] == "assistant"
        assert target["citation_provenance"] == provenance
