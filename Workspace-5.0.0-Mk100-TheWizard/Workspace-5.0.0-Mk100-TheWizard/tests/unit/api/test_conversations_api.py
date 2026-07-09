"""Unit tests for conversation API endpoints."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from src.jarvis.api.app import app


class TestConversationAPI(unittest.TestCase):
    """Test conversation API endpoints with mocked database."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_check(self) -> None:
        """Test health check endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_root_endpoint(self) -> None:
        """Test root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("service", response.json())


if __name__ == "__main__":
    unittest.main()
