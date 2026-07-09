"""Temporal chunk manager for append-only versioned knowledge updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from jarvis.database.models import TemporalChunk


@dataclass
class ChunkVersion:
    id: UUID
    collection: str
    domain: Optional[str]
    source_file: Optional[str]
    section: Optional[str]
    content_hash: str
    source_type: str
    verified_at: datetime
    confidence: float
    supersedes: Optional[UUID]
    metadata: dict


class TemporalChunkManager:
    """Manage versioned chunk metadata in an append-only fashion."""

    def __init__(self, collection: str = "knowledge") -> None:
        self.collection = collection

    def create_version(
        self,
        *,
        domain: Optional[str],
        source_file: Optional[str],
        section: Optional[str],
        content_hash: str,
        source_type: str,
        confidence: float,
        verified_at: Optional[datetime] = None,
        supersedes: Optional[UUID] = None,
        metadata: Optional[dict] = None,
    ) -> ChunkVersion:
        now = verified_at or datetime.now(timezone.utc)
        version = ChunkVersion(
            id=uuid4(),
            collection=self.collection,
            domain=domain,
            source_file=source_file,
            section=section,
            content_hash=content_hash,
            source_type=source_type,
            verified_at=now if now.tzinfo else now.replace(tzinfo=timezone.utc),
            confidence=confidence,
            supersedes=supersedes,
            metadata=metadata or {},
        )
        return version

    def to_model(self, version: ChunkVersion) -> TemporalChunk:
        return TemporalChunk(
            id=version.id,
            collection=version.collection,
            domain=version.domain,
            source_file=version.source_file,
            section=version.section,
            content_hash=version.content_hash,
            source_type=version.source_type,
            verified_at=version.verified_at,
            confidence=version.confidence,
            supersedes=version.supersedes,
            extra_metadata=version.metadata,
        )
