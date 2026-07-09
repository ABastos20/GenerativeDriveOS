"""Batch Graph Enrichment Script.

Run this to populate Entity/Relationship links for all existing documents
that haven't been enriched yet.
"""
from __future__ import annotations

import sys
import time
sys.path.insert(0, "/workspace")

from jarvis.database.postgres import get_session
from jarvis.database.models import Document, DocumentEntity
from jarvis.memory.graph_enricher import process_document

def main():
    print("🧠 Batch Graph Enrichment Starting...")
    
    with get_session() as session:
        # Find documents without entity links
        from sqlalchemy import select
        enriched_doc_ids_stmt = select(DocumentEntity.document_id).distinct()
        
        unenriched_docs = session.query(Document).filter(
            ~Document.id.in_(enriched_doc_ids_stmt)
        ).all()
        
        total = len(unenriched_docs)
        print(f"📄 Found {total} unenriched documents")
        
        if total == 0:
            print("✅ All documents already enriched!")
            return
        
        for i, doc in enumerate(unenriched_docs, 1):
            print(f"[{i}/{total}] Enriching: {doc.doc_key[:60]}... (domain: {doc.domain})")
            try:
                # Call enricher (it creates its own session)
                process_document(doc.id)
                print(f"         ✓ Done")
            except Exception as e:
                print(f"         ✗ Error: {e}")
            
            # Rate limit to avoid hammering LLM
            if i < total:
                time.sleep(1)
    
    print("\n🎉 Batch Enrichment Complete!")
    
    # Show final stats
    with get_session() as session:
        entity_count = session.query(Document).count()
        link_count = session.execute("SELECT COUNT(*) FROM document_entities").scalar()
        print(f"📊 Total Documents: {entity_count}")
        print(f"📊 Total Entity Links: {link_count}")

if __name__ == "__main__":
    main()
