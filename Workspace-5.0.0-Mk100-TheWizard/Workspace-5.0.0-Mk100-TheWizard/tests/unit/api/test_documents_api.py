from __future__ import annotations
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.jarvis.api.app import app
from src.jarvis.api import memory
from src.jarvis.database import models

client = TestClient(app)

def test_get_document_by_key(monkeypatch):
    mock_session = MagicMock()
    mock_doc = models.Document(
        id="123e4567-e89b-12d3-a456-426614174000",
        doc_key="file::/tmp/test.pdf",
        content="Full document content",
        source_file="/tmp/test.pdf",
        domain="test",
        metadata_={"pages": 1}
    )
    
    # Mock session.query().filter().one_or_none()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.one_or_none.return_value = mock_doc
    
    # Mock get_session context manager
    class MockSessionContext:
        def __enter__(self):
            return mock_session
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    monkeypatch.setattr(memory, "get_session", lambda: MockSessionContext())

    # Note: FastAPI TestClient handles URL encoding, but we pass the raw path param
    # The path param is {doc_key:path}, so slashes are allowed.
    response = client.get("/api/memory/documents/key/file::/tmp/test.pdf")
    
    assert response.status_code == 200
    data = response.json()
    assert data["doc_key"] == "file::/tmp/test.pdf"
    assert data["content"] == "Full document content"
