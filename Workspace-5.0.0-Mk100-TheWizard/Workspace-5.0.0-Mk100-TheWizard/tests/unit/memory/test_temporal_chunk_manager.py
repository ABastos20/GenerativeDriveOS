from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import uuid4

from jarvis.memory.temporal_chunk_manager import ChunkVersion, TemporalChunkManager


def test_create_version_populates_defaults_and_timezone() -> None:
    mgr = TemporalChunkManager(collection="knowledge")
    version = mgr.create_version(
        domain="jarvis-core",
        source_file="docs/example.md",
        section="Intro",
        content_hash="abc123",
        source_type="web_research",
        confidence=0.8,
        metadata={"quality": 0.9},
    )

    assert version.collection == "knowledge"
    assert version.verified_at.tzinfo == timezone.utc
    assert version.confidence == 0.8
    assert version.supersedes is None


def test_create_version_with_supersedes_links_previous() -> None:
    mgr = TemporalChunkManager(collection="knowledge")
    prev_id = uuid4()
    version = mgr.create_version(
        domain=None,
        source_file=None,
        section=None,
        content_hash="hash-new",
        source_type="user_provided",
        confidence=0.6,
        supersedes=prev_id,
    )
    assert version.supersedes == prev_id


def test_to_model_converts_dataclass_to_orm() -> None:
    mgr = TemporalChunkManager()
    version = mgr.create_version(
        domain="jarvis-core",
        source_file="docs/example.md",
        section="Intro",
        content_hash="abc123",
        source_type="web_research",
        confidence=0.7,
        verified_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    model = mgr.to_model(version)
    assert model.content_hash == "abc123"
    assert model.collection == "knowledge"
    assert model.confidence == version.confidence
