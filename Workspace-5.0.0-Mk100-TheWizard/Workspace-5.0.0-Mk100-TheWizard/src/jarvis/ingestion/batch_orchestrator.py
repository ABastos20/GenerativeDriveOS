"""
Batch Ingestion Orchestrator (Story 11-6).
Handles scalable ingestion with backpressure and risk aggregation.
"""
from typing import List, Dict
import concurrent.futures
from dataclasses import dataclass

from jarvis.ingestion.pipeline import IngestionPipeline, IngestionResult

@dataclass
class BatchResult:
    batch_id: str
    total_items: int
    processed: int
    success_count: int
    quarantined_count: int
    rejected_count: int
    results: List[IngestionResult]

class BatchOrchestrator:
    def __init__(self, pipeline: IngestionPipeline, max_workers: int = 4):
        self.pipeline = pipeline
        self.max_workers = max_workers

    def ingest_batch(self, batch_id: str, items: List[Dict]) -> BatchResult:
        """
        Parallel ingestion of a list of items.
        Item format: {"content": str, "metadata": dict}
        """
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(self.pipeline.ingest, item["content"], item["metadata"]): item 
                for item in items
            }
            
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # In a real system we might log this or synthesize a failure result
                    pass
                    
        # Aggregate stats
        success = len([r for r in results if r.status == "success"])
        quarantined = len([r for r in results if r.status == "quarantined"])
        rejected = len([r for r in results if r.status == "rejected"])

        return BatchResult(
            batch_id=batch_id,
            total_items=len(items),
            processed=len(results),
            success_count=success,
            quarantined_count=quarantined,
            rejected_count=rejected,
            results=results
        )
