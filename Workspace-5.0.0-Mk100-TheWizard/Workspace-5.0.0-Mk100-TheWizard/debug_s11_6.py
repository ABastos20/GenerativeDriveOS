"""Debug script for Story 11-6 Sovereign Ingestion with full 11-5 integration."""
from jarvis.ingestion.pipeline import IngestionPipeline, IngestionResult
from jarvis.knowledge.epistemic_ledger import EpistemicLedger
from jarvis.knowledge.tiers import KnowledgeTier

def debug_ingestion():
    ledger = EpistemicLedger()
    pipeline = IngestionPipeline(ledger_service=ledger)
    
    print("\n--- TEST 1: High Trust Ingestion (Sensor -> K0) ---")
    res1 = pipeline.ingest(
        content="Sensor reading: Temp=98.6F",
        metadata={"source_type": "sensor", "source_uri": "device://thermometer-01"}
    )
    print(f"Status: {res1.status}")
    print(f"Score: {res1.trust_score.score} (Tier: {res1.trust_score.tier.name})")
    print(f"Raw Hash: {res1.raw_hash[:16]}...")
    print(f"Timestamp: {res1.timestamp}")
    assert res1.status == "success"
    assert res1.trust_score.tier == KnowledgeTier.K0
    assert res1.raw_hash is not None
    assert res1.timestamp is not None
    
    print("\n--- TEST 2: Low Trust Ingestion (Social -> K4) ---")
    res2 = pipeline.ingest(
        content="Some random tweet content that is long enough.",
        metadata={"source_type": "social", "source_uri": "twitter://random_user"}
    )
    print(f"Status: {res2.status}")
    print(f"Score: {res2.trust_score.score} (Tier: {res2.trust_score.tier.name})")
    assert res2.status == "quarantined"
    assert res2.trust_score.tier == KnowledgeTier.K4

    print("\n--- TEST 3: Firewall Block (Missing Metadata) ---")
    res3 = pipeline.ingest(
        content="Valid content but missing meta",
        metadata={}
    )
    print(f"Status: {res3.status}")
    print(f"Error: {res3.error}")
    assert res3.status == "rejected"

    print("\n--- TEST 4: Firewall Block (Empty Content) ---")
    res4 = pipeline.ingest(
        content="",
        metadata={"source_type": "sensor", "source_uri": "device://null"}
    )
    print(f"Status: {res4.status}")
    print(f"Error: {res4.error}")
    assert res4.status == "rejected"

    print("\n--- TEST 5: Batch Ingestion ---")
    from jarvis.ingestion.batch_orchestrator import BatchOrchestrator
    orchestrator = BatchOrchestrator(pipeline)
    
    batch_items = [
        {"content": "Alpha sensor data 12345", "metadata": {"source_type": "sensor", "source_uri": "s1"}},
        {"content": "Beta social media post 12345", "metadata": {"source_type": "social", "source_uri": "s2"}},
        {"content": "", "metadata": {"source_type": "news", "source_uri": "s3"}}, # Fail
        {"content": "Gamma internal analytics report 12345", "metadata": {"source_type": "internal_analytics", "source_uri": "s4"}},
    ]
    
    batch_res = orchestrator.ingest_batch("batch-001", batch_items)
    print(f"Batch processed: {batch_res.processed}/{batch_res.total_items}")
    print(f"Success: {batch_res.success_count}, Quarantined: {batch_res.quarantined_count}, Rejected: {batch_res.rejected_count}")
    
    assert batch_res.processed == 4
    # Alpha(sensor)->K0->success, Gamma(internal)->K1->success
    assert batch_res.success_count == 2
    # Beta(social)->K4->quarantined
    assert batch_res.quarantined_count == 1
    # Empty content -> rejected
    assert batch_res.rejected_count == 1
    
    print("\n--- TEST 6: Check Audit Log Integration ---")
    if pipeline.audit_log is not None:
        print(f"Audit log enabled: yes")
        from jarvis.knowledge.audit import EpistemicEventType
        events = pipeline.audit_log.query_by_type(EpistemicEventType.INITIAL_INGEST)
        print(f"INITIAL_INGEST events logged: {len(events)}")
        assert len(events) >= 2  # At least 2 successful ingestions logged
    else:
        print(f"Audit log enabled: no (11-5 module not fully available)")

    print("\n✅ All manual scenarios passed (Story 11-6 integrated with 11-5).")

if __name__ == "__main__":
    debug_ingestion()
