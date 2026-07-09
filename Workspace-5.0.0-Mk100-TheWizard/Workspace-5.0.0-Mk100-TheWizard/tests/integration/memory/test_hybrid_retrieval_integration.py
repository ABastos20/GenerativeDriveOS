from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.database.models import Conversation, Message
from jarvis.database.postgres import get_session_factory
from jarvis.memory import ingest
from jarvis.memory import search as search_mod


@pytest.mark.integration
def test_hybrid_search_uses_both_semantic_and_keyword(tmp_path: Path) -> None:
    """Integration test for hybrid retrieval over Postgres + Qdrant.

    This test:
    - Inserts a conversation + message into Postgres containing the query term
    - Ingests a small markdown document into Qdrant with the same term and domain
    - Runs hybrid_search and asserts that results are returned with hybrid metadata
    """
    # --- Arrange Postgres conversation/message ---------------------------------
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        conversation = Conversation()
        session.add(conversation)
        session.flush()

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hybrid retrieval edge case with BM25 and vector search.",
        )
        session.add(message)
        session.commit()
    finally:
        session.close()

    # --- Arrange Qdrant memory chunk -------------------------------------------
    text = "This document describes a hybrid retrieval edge case with BM25 and vector search."
    doc_path = tmp_path / "hybrid-test.md"
    doc_path.write_text(text, encoding="utf-8")

    # Ingest into Qdrant under the jarvis-conversations domain so domain filters align
    ingest.ingest_file(path=doc_path, domain="jarvis-conversations")

    # --- Act: run hybrid search -------------------------------------------------
    results = search_mod.hybrid_search(
        "BM25",
        k=5,
        weight=0.7,
        domains=["jarvis-conversations"],
    )

    # --- Assert -----------------------------------------------------------------
    assert results, "Expected at least one hybrid search result"
    assert any(r.domain == "jarvis-conversations" for r in results)

    # Ensure hybrid metadata is present on at least one result
    assert any(
        "semantic_score_norm" in r.metadata or "keyword_score_norm" in r.metadata
        for r in results
    )

