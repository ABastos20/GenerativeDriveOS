"""Provenance Ledger for Knowledge Sovereignty (Story 11-5, Lock 7).

This module implements the cryptographically-sealed, append-only provenance ledger
that tracks the full lineage and authority of every knowledge unit in JARVIS.

The provenance ledger ensures:
- Full historical lineage preservation
- Cryptographic integrity (SHA-256 sealing)
- Append-only constraint (no deletions/modifications)
- Queryable audit trail for governance & C-IDS

Provenance Vector: P(i) = ⟨s, o, m, c₀, t₀, K⟩
Where:
- s = source_type
- o = origin (DOI, URL, hash, sensor_id)
- m = collection_method
- c₀ = initial_confidence ∈ [0,1]
- t₀ = ingestion_time
- K = knowledge_tier

References:
- [Story 11-5, AC #2: Provenance Ledger]
- [Lock 7: Epistemic Sovereignty]
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from src.jarvis.knowledge.tiers import (
    KnowledgeTier,
    SourceType,
    CollectionMethod,
)
from src.jarvis.database.models import (
    ProvenanceLedgerEntry,
    KnowledgeUnit,
)


@dataclass(frozen=True)
class ProvenanceVector:
    """Immutable provenance vector for knowledge units.

    Implements the provenance vector specification from AC #2:
        P(i) = ⟨s, o, m, c₀, t₀, K⟩

    All fields are immutable after creation to ensure provenance integrity.
    """
    source_type: SourceType
    origin: str  # DOI, URL, file path, sensor ID, etc.
    collection_method: CollectionMethod
    initial_confidence: float  # c₀ ∈ [0,1]
    ingestion_time: datetime  # t₀ (UTC timezone-aware)
    knowledge_tier: KnowledgeTier  # K

    def __post_init__(self):
        """Validate provenance vector constraints."""
        if not 0.0 <= self.initial_confidence <= 1.0:
            raise ValueError(
                f"initial_confidence must be in [0, 1], got {self.initial_confidence}"
            )

        if self.ingestion_time.tzinfo is None:
            raise ValueError("ingestion_time must be timezone-aware (UTC)")

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dictionary for hashing.

        Returns deterministic, sorted dictionary for consistent hashing.
        Converts datetime to ISO format string for serialization.
        """
        return {
            "source_type": self.source_type.value,
            "origin": self.origin,
            "collection_method": self.collection_method.value,
            "initial_confidence": self.initial_confidence,
            "ingestion_time": self.ingestion_time.isoformat(),
            "knowledge_tier": self.knowledge_tier.value,
        }


def compute_provenance_hash(vector: ProvenanceVector) -> str:
    """Compute SHA-256 hash of provenance vector.

    Implements cryptographic sealing requirement from AC #2.
    Hash is deterministic and collision-resistant.

    Formula:
        hash = SHA-256(source_type || origin || method || c₀ || t₀ || K)

    Args:
        vector: Provenance vector to hash

    Returns:
        64-character hexadecimal SHA-256 hash
    """
    # Convert to canonical form for deterministic hashing
    canonical = vector.to_canonical_dict()

    # Create deterministic JSON (sorted keys, no whitespace)
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))

    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    return hash_obj.hexdigest()


def compute_chain_hash(current_vector: ProvenanceVector, previous_hash: Optional[str]) -> str:
    """Compute chained hash for blockchain-style ledger.

    Links current entry to previous entry for tamper detection.

    Args:
        current_vector: Current provenance vector
        previous_hash: Hash of previous ledger entry (None for first entry)

    Returns:
        64-character hexadecimal SHA-256 hash
    """
    current_hash = compute_provenance_hash(current_vector)

    if previous_hash is None:
        return current_hash

    # Chain: SHA-256(current_hash || previous_hash)
    chain_input = current_hash + previous_hash
    hash_obj = hashlib.sha256(chain_input.encode('utf-8'))
    return hash_obj.hexdigest()


class ProvenanceLedger:
    """Append-only provenance ledger with cryptographic sealing.

    Implements AC #2: Provenance Ledger
    - Append-only (no deletions/updates)
    - Cryptographically sealed with SHA-256
    - Full historical lineage preserved
    - Queryable by governance & C-IDS
    """

    def __init__(self, session: Session):
        """Initialize provenance ledger.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def record_provenance(
        self,
        knowledge_unit_id: UUID,
        vector: ProvenanceVector,
        parent_ledger_id: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> ProvenanceLedgerEntry:
        """Record provenance in append-only ledger.

        This is the ONLY way to add entries to the provenance ledger.
        No updates or deletions are permitted.

        Args:
            knowledge_unit_id: UUID of knowledge unit
            vector: Provenance vector
            parent_ledger_id: Parent ledger entry ID if derived knowledge
            metadata: Optional additional metadata

        Returns:
            Created provenance ledger entry

        Raises:
            ValueError: If validation fails
        """
        # Compute provenance hash
        provenance_hash = compute_provenance_hash(vector)

        # Get previous hash for chain (if any)
        previous_hash = self._get_latest_hash()

        # Compute chained hash
        #chained_hash = compute_chain_hash(vector, previous_hash)

        # Create ledger entry
        entry = ProvenanceLedgerEntry(
            knowledge_unit_id=knowledge_unit_id,
            source_type=vector.source_type.value,
            origin=vector.origin,
            collection_method=vector.collection_method.value,
            initial_confidence=vector.initial_confidence,
            ingestion_time=vector.ingestion_time,
            knowledge_tier=vector.knowledge_tier.value,
            provenance_hash=provenance_hash,
            previous_hash=previous_hash,
            parent_ledger_id=parent_ledger_id,
            metadata_=metadata,
        )

        # Append to ledger (NEVER update or delete)
        self.session.add(entry)
        self.session.flush()  # Get entry.id

        return entry

    def _get_latest_hash(self) -> Optional[str]:
        """Get hash of most recent ledger entry.

        Used for blockchain-style chaining.

        Returns:
            Hash of latest entry, or None if ledger is empty
        """
        latest = (
            self.session.query(ProvenanceLedgerEntry)
            .order_by(ProvenanceLedgerEntry.id.desc())
            .first()
        )

        return latest.provenance_hash if latest else None

    def get_lineage(self, knowledge_unit_id: UUID) -> List[ProvenanceLedgerEntry]:
        """Get full provenance lineage for a knowledge unit.

        Follows parent_ledger_id links to reconstruct full lineage.

        Args:
            knowledge_unit_id: UUID of knowledge unit

        Returns:
            List of provenance entries from root to current (chronological)
        """
        # Get direct provenance entry
        entry = (
            self.session.query(ProvenanceLedgerEntry)
            .filter(ProvenanceLedgerEntry.knowledge_unit_id == knowledge_unit_id)
            .first()
        )

        if not entry:
            return []

        # Build lineage by following parent links
        lineage = [entry]

        current = entry
        while current.parent_ledger_id is not None:
            parent = (
                self.session.query(ProvenanceLedgerEntry)
                .filter(ProvenanceLedgerEntry.id == current.parent_ledger_id)
                .first()
            )

            if not parent:
                break

            lineage.insert(0, parent)  # Insert at beginning for chronological order
            current = parent

        return lineage

    def verify_chain_integrity(self) -> tuple[bool, Optional[str]]:
        """Verify provenance chain integrity.

        Checks that all entries properly chain together via hashes.
        Detects any tampering or corruption.

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if chain is valid
            - (False, error_message) if corruption detected
        """
        entries = (
            self.session.query(ProvenanceLedgerEntry)
            .order_by(ProvenanceLedgerEntry.id.asc())
            .all()
        )

        if not entries:
            return (True, None)

        previous_hash = None

        for entry in entries:
            # Reconstruct vector from entry
            vector = ProvenanceVector(
                source_type=SourceType(entry.source_type),
                origin=entry.origin,
                collection_method=CollectionMethod(entry.collection_method),
                initial_confidence=float(entry.initial_confidence),
                ingestion_time=entry.ingestion_time,
                knowledge_tier=KnowledgeTier(entry.knowledge_tier),
            )

            # Recompute hash
            expected_hash = compute_provenance_hash(vector)

            # Verify hash matches
            if entry.provenance_hash != expected_hash:
                return (
                    False,
                    f"Hash mismatch at entry {entry.id}: "
                    f"expected {expected_hash}, got {entry.provenance_hash}"
                )

            # Verify chain link
            if entry.previous_hash != previous_hash:
                return (
                    False,
                    f"Chain break at entry {entry.id}: "
                    f"expected previous_hash {previous_hash}, got {entry.previous_hash}"
                )

            previous_hash = entry.provenance_hash

        return (True, None)

    def query_by_source(
        self,
        source_type: SourceType,
        limit: Optional[int] = None
    ) -> List[ProvenanceLedgerEntry]:
        """Query provenance entries by source type.

        Args:
            source_type: Source type to filter by
            limit: Optional limit on number of results

        Returns:
            List of provenance entries matching source type
        """
        query = (
            self.session.query(ProvenanceLedgerEntry)
            .filter(ProvenanceLedgerEntry.source_type == source_type.value)
            .order_by(ProvenanceLedgerEntry.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def query_by_tier(
        self,
        tier: KnowledgeTier,
        limit: Optional[int] = None
    ) -> List[ProvenanceLedgerEntry]:
        """Query provenance entries by knowledge tier.

        Args:
            tier: Knowledge tier to filter by
            limit: Optional limit on number of results

        Returns:
            List of provenance entries matching tier
        """
        query = (
            self.session.query(ProvenanceLedgerEntry)
            .filter(ProvenanceLedgerEntry.knowledge_tier == tier.value)
            .order_by(ProvenanceLedgerEntry.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def query_by_origin_pattern(
        self,
        pattern: str,
        limit: Optional[int] = None
    ) -> List[ProvenanceLedgerEntry]:
        """Query provenance entries by origin pattern (SQL LIKE).

        Useful for finding all entries from a specific domain or source.

        Args:
            pattern: SQL LIKE pattern (e.g., "https://arxiv.org/%")
            limit: Optional limit on number of results

        Returns:
            List of provenance entries matching origin pattern
        """
        query = (
            self.session.query(ProvenanceLedgerEntry)
            .filter(ProvenanceLedgerEntry.origin.like(pattern))
            .order_by(ProvenanceLedgerEntry.created_at.desc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()
