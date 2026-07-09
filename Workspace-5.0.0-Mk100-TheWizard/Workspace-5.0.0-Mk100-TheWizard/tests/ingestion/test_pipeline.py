
import pytest
from jarvis.ingestion.pipeline import IngestionPipeline, IngestionResult
from jarvis.ingestion.batch_orchestrator import BatchOrchestrator
from jarvis.knowledge.epistemic_ledger import EpistemicLedger
from jarvis.knowledge.tiers import KnowledgeTier

@pytest.fixture
def ledger():
    return EpistemicLedger()

@pytest.fixture
def pipeline(ledger):
    return IngestionPipeline(ledger_service=ledger)

def test_high_trust_ingestion(pipeline):
    """Test that high-reputation sources get K0 tier."""
    content = "A sufficiently long content string for sensor data 1234567890."
    result = pipeline.ingest(content, {"source_type": "sensor", "source_uri": "device://s1"})
    
    assert result.status == "success"
    assert result.trust_score.tier == KnowledgeTier.K0
    assert result.trust_score.score >= 0.8
    assert result.ledger_id is not None

def test_low_trust_ingestion(pipeline):
    """Test that social media sources get K4 tier (quarantined)."""
    content = "Some random tweet content that is long enough 1234567890."
    result = pipeline.ingest(content, {"source_type": "social", "source_uri": "twitter://t1"})
    
    assert result.status == "quarantined"
    assert result.trust_score.tier == KnowledgeTier.K4
    assert result.trust_score.score < 0.4
    assert result.ledger_id is not None

def test_narrative_ingestion(pipeline):
    """Test that news/blog sources get K3 tier (accepted but low priority)."""
    content = "News article content about recent developments 1234567890."
    result = pipeline.ingest(content, {"source_type": "news", "source_uri": "cnn://article1"})
    
    assert result.status == "success"
    assert result.trust_score.tier == KnowledgeTier.K3
    assert result.trust_score.score >= 0.4

def test_firewall_rejection(pipeline):
    """Test that the firewall blocks invalid data."""
    # Case 1: Empty content
    res1 = pipeline.ingest("", {"source_type": "sensor", "source_uri": "s1"})
    assert res1.status == "rejected"
    assert "Empty content" in res1.error

    # Case 2: Missing metadata
    res2 = pipeline.ingest("valid content", {})
    assert res2.status == "rejected"
    assert "Missing required metadata" in res2.error

def test_batch_processing(pipeline):
    """Test batch orchestration with mixed trust levels."""
    orchestrator = BatchOrchestrator(pipeline)
    items = [
        {"content": "High trust sensor content 12345", "metadata": {"source_type": "sensor", "source_uri": "s1"}},
        {"content": "Low trust social content 12345", "metadata": {"source_type": "social", "source_uri": "s2"}},
        {"content": "", "metadata": {"source_type": "news", "source_uri": "s3"}},
    ]
    
    result = orchestrator.ingest_batch("batch-1", items)
    
    assert result.total_items == 3
    assert result.processed == 3
    assert result.success_count == 1  # sensor -> K0 -> success
    assert result.quarantined_count == 1  # social -> K4 -> quarantined
    assert result.rejected_count == 1  # empty content -> rejected
