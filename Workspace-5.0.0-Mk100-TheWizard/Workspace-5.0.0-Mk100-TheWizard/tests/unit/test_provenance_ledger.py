"""Unit tests for Provenance Ledger (Story 11-5, Task 2).

Tests provenance vector hashing, append-only ledger, lineage tracking, and integrity verification.
Coverage target: ≥90% per AC #2 requirements.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.jarvis.knowledge.provenance import (
    ProvenanceVector,
    compute_provenance_hash,
    compute_chain_hash,
    ProvenanceLedger,
)
from src.jarvis.knowledge.tiers import (
    KnowledgeTier,
    SourceType,
    CollectionMethod,
)


class TestProvenanceVector:
    """Test ProvenanceVector immutability and validation."""

    def test_valid_vector(self):
        """Test valid provenance vector creation."""
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.PEER_REVIEWED_PAPER,
            origin="doi://10.1234/example",
            collection_method=CollectionMethod.DOCUMENT_PARSE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K2,
        )

        assert vector.source_type == SourceType.PEER_REVIEWED_PAPER
        assert vector.origin == "doi://10.1234/example"
        assert vector.initial_confidence == 0.95
        assert vector.knowledge_tier == KnowledgeTier.K2

    def test_invalid_confidence_high(self):
        """Test that confidence > 1.0 is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="initial_confidence must be in"):
            ProvenanceVector(
                source_type=SourceType.TELEMETRY,
                origin="sensor://test",
                collection_method=CollectionMethod.DIRECT_CAPTURE,
                initial_confidence=1.5,
                ingestion_time=now,
                knowledge_tier=KnowledgeTier.K0,
            )

    def test_invalid_confidence_low(self):
        """Test that confidence < 0.0 is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="initial_confidence must be in"):
            ProvenanceVector(
                source_type=SourceType.TELEMETRY,
                origin="sensor://test",
                collection_method=CollectionMethod.DIRECT_CAPTURE,
                initial_confidence=-0.1,
                ingestion_time=now,
                knowledge_tier=KnowledgeTier.K0,
            )

    def test_timezone_naive_rejected(self):
        """Test that timezone-naive datetime is rejected."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # No timezone
        with pytest.raises(ValueError, match="must be timezone-aware"):
            ProvenanceVector(
                source_type=SourceType.TELEMETRY,
                origin="sensor://test",
                collection_method=CollectionMethod.DIRECT_CAPTURE,
                initial_confidence=1.0,
                ingestion_time=naive_dt,
                knowledge_tier=KnowledgeTier.K0,
            )

    def test_immutability(self):
        """Test that provenance vector is immutable (frozen dataclass)."""
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=1.0,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        # Attempt to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # dataclass.FrozenInstanceError
            vector.origin = "modified://origin"

    def test_to_canonical_dict(self):
        """Test canonical dictionary conversion for hashing."""
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        canonical = vector.to_canonical_dict()

        assert canonical["source_type"] == "telemetry"
        assert canonical["origin"] == "sensor://test"
        assert canonical["collection_method"] == "direct_capture"
        assert canonical["initial_confidence"] == 0.95
        assert canonical["ingestion_time"] == now.isoformat()
        assert canonical["knowledge_tier"] == "ground_truth"


class TestProvenanceHashing:
    """Test cryptographic hashing functions."""

    def test_hash_determinism(self):
        """Test that same vector always produces same hash (AC #2 invariant)."""
        now = datetime.now(timezone.utc)
        vector1 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )
        vector2 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        hash1 = compute_provenance_hash(vector1)
        hash2 = compute_provenance_hash(vector2)

        assert hash1 == hash2

    def test_hash_uniqueness(self):
        """Test that different vectors produce different hashes."""
        now = datetime.now(timezone.utc)
        vector1 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test1",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )
        vector2 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test2",  # Different origin
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        hash1 = compute_provenance_hash(vector1)
        hash2 = compute_provenance_hash(vector2)

        assert hash1 != hash2

    def test_hash_length(self):
        """Test that hash is SHA-256 (64 hex characters)."""
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        hash_val = compute_provenance_hash(vector)

        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_chain_hash_first_entry(self):
        """Test chain hash for first entry (no previous hash)."""
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        # First entry: chain hash equals provenance hash
        chain_hash = compute_chain_hash(vector, None)
        provenance_hash = compute_provenance_hash(vector)

        assert chain_hash == provenance_hash

    def test_chain_hash_linked_entries(self):
        """Test chain hash links entries together."""
        now = datetime.now(timezone.utc)
        vector1 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test1",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )
        vector2 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test2",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        hash1 = compute_provenance_hash(vector1)
        chain_hash2 = compute_chain_hash(vector2, hash1)

        # Chain hash should be different from standalone hash
        hash2 = compute_provenance_hash(vector2)
        assert chain_hash2 != hash2


@pytest.mark.skip(reason="Requires PostgreSQL database - integration test only")
class TestProvenanceLedger:
    """Test provenance ledger operations.

    Note: These are integration tests that require PostgreSQL.
    For CI/CD, these tests are skipped unless a PostgreSQL database is available.
    """

    @pytest.fixture
    def session(self):
        """Create database session for testing.

        This requires a PostgreSQL database to be available.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from src.jarvis.database.models import Base

        # Note: For actual integration testing, use real PostgreSQL
        # In-memory SQLite doesn't support JSONB which is required by models
        engine = create_engine("postgresql://localhost/jarvis_test")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.rollback()
        session.close()

    @pytest.fixture
    def ledger(self, session):
        """Create provenance ledger instance."""
        return ProvenanceLedger(session)

    def test_record_provenance(self, ledger, session):
        """Test recording provenance in ledger."""
        ku_id = uuid4()
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        entry = ledger.record_provenance(ku_id, vector)

        assert entry.knowledge_unit_id == ku_id
        assert entry.source_type == "telemetry"
        assert entry.origin == "sensor://test"
        assert entry.provenance_hash is not None
        assert len(entry.provenance_hash) == 64

    def test_ledger_append_only(self, ledger, session):
        """Test that ledger is append-only (no updates/deletes)."""
        ku_id = uuid4()
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        entry = ledger.record_provenance(ku_id, vector)
        session.commit()

        # Verify entry exists
        from src.jarvis.database.models import ProvenanceLedgerEntry
        retrieved = session.query(ProvenanceLedgerEntry).filter_by(id=entry.id).first()
        assert retrieved is not None

        # Ledger interface provides no update/delete methods (append-only by design)
        assert not hasattr(ledger, 'update_provenance')
        assert not hasattr(ledger, 'delete_provenance')

    def test_get_lineage_single(self, ledger, session):
        """Test lineage retrieval for single knowledge unit."""
        ku_id = uuid4()
        now = datetime.now(timezone.utc)
        vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://test",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )

        entry = ledger.record_provenance(ku_id, vector)
        session.commit()

        lineage = ledger.get_lineage(ku_id)

        assert len(lineage) == 1
        assert lineage[0].id == entry.id

    def test_get_lineage_with_parent(self, ledger, session):
        """Test lineage retrieval with parent-child relationship."""
        # Create parent knowledge unit
        parent_ku_id = uuid4()
        now = datetime.now(timezone.utc)
        parent_vector = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://parent",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=1.0,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )
        parent_entry = ledger.record_provenance(parent_ku_id, parent_vector)
        session.commit()

        # Create child knowledge unit derived from parent
        child_ku_id = uuid4()
        child_vector = ProvenanceVector(
            source_type=SourceType.DERIVED_MODEL,
            origin="model://child",
            collection_method=CollectionMethod.API_FETCH,
            initial_confidence=0.9,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K1,
        )
        child_entry = ledger.record_provenance(
            child_ku_id,
            child_vector,
            parent_ledger_id=parent_entry.id
        )
        session.commit()

        # Get lineage for child
        lineage = ledger.get_lineage(child_ku_id)

        # Should include both parent and child in chronological order
        assert len(lineage) == 2
        assert lineage[0].id == parent_entry.id
        assert lineage[1].id == child_entry.id

    def test_query_by_source(self, ledger, session):
        """Test querying by source type."""
        now = datetime.now(timezone.utc)

        # Create telemetry entry
        ku1 = uuid4()
        v1 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://1",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=1.0,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )
        ledger.record_provenance(ku1, v1)

        # Create paper entry
        ku2 = uuid4()
        v2 = ProvenanceVector(
            source_type=SourceType.PEER_REVIEWED_PAPER,
            origin="doi://test",
            collection_method=CollectionMethod.DOCUMENT_PARSE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K2,
        )
        ledger.record_provenance(ku2, v2)

        session.commit()

        # Query for telemetry
        results = ledger.query_by_source(SourceType.TELEMETRY)
        assert len(results) == 1
        assert results[0].source_type == "telemetry"

        # Query for papers
        results = ledger.query_by_source(SourceType.PEER_REVIEWED_PAPER)
        assert len(results) == 1
        assert results[0].source_type == "peer_reviewed_paper"

    def test_query_by_tier(self, ledger, session):
        """Test querying by knowledge tier."""
        now = datetime.now(timezone.utc)

        # Create K0 entry
        ku1 = uuid4()
        v1 = ProvenanceVector(
            source_type=SourceType.TELEMETRY,
            origin="sensor://1",
            collection_method=CollectionMethod.DIRECT_CAPTURE,
            initial_confidence=1.0,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K0,
        )
        ledger.record_provenance(ku1, v1)

        # Create K2 entry
        ku2 = uuid4()
        v2 = ProvenanceVector(
            source_type=SourceType.PEER_REVIEWED_PAPER,
            origin="doi://test",
            collection_method=CollectionMethod.DOCUMENT_PARSE,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K2,
        )
        ledger.record_provenance(ku2, v2)

        session.commit()

        # Query for K0
        results = ledger.query_by_tier(KnowledgeTier.K0)
        assert len(results) == 1
        assert results[0].knowledge_tier == "ground_truth"

        # Query for K2
        results = ledger.query_by_tier(KnowledgeTier.K2)
        assert len(results) == 1
        assert results[0].knowledge_tier == "trust_scored_external"

    def test_query_by_origin_pattern(self, ledger, session):
        """Test querying by origin pattern."""
        now = datetime.now(timezone.utc)

        # Create entries with different origins
        ku1 = uuid4()
        v1 = ProvenanceVector(
            source_type=SourceType.PEER_REVIEWED_PAPER,
            origin="https://arxiv.org/paper1",
            collection_method=CollectionMethod.WEB_FETCH,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K2,
        )
        ledger.record_provenance(ku1, v1)

        ku2 = uuid4()
        v2 = ProvenanceVector(
            source_type=SourceType.PEER_REVIEWED_PAPER,
            origin="https://arxiv.org/paper2",
            collection_method=CollectionMethod.WEB_FETCH,
            initial_confidence=0.95,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K2,
        )
        ledger.record_provenance(ku2, v2)

        ku3 = uuid4()
        v3 = ProvenanceVector(
            source_type=SourceType.NEWS_ARTICLE,
            origin="https://news.example.com/article",
            collection_method=CollectionMethod.WEB_FETCH,
            initial_confidence=0.7,
            ingestion_time=now,
            knowledge_tier=KnowledgeTier.K3,
        )
        ledger.record_provenance(ku3, v3)

        session.commit()

        # Query for arxiv.org papers
        results = ledger.query_by_origin_pattern("https://arxiv.org/%")
        assert len(results) == 2
        assert all("arxiv.org" in r.origin for r in results)

    def test_verify_chain_integrity_valid(self, ledger, session):
        """Test chain integrity verification for valid chain."""
        now = datetime.now(timezone.utc)

        # Create multiple entries
        for i in range(3):
            ku_id = uuid4()
            vector = ProvenanceVector(
                source_type=SourceType.TELEMETRY,
                origin=f"sensor://test{i}",
                collection_method=CollectionMethod.DIRECT_CAPTURE,
                initial_confidence=0.95,
                ingestion_time=now,
                knowledge_tier=KnowledgeTier.K0,
            )
            ledger.record_provenance(ku_id, vector)

        session.commit()

        # Verify integrity
        is_valid, error = ledger.verify_chain_integrity()
        assert is_valid is True
        assert error is None
