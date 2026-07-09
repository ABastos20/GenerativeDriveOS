import pytest
import time
import uuid
import os
from sqlalchemy.orm import Session
from jarvis.database import models
from jarvis.memory.graph_enricher import process_document

@pytest.mark.integration
class TestGraphEnrichment:
    """Test end-to-end graph enrichment flow."""
    
    def test_graph_extraction_flow(self, db_session: Session):
        """
        Verify that:
        1. We can create a document in the DB.
        2. We can run the enrichment process.
        3. Entities and Relationships are created.
        """
        # 1. Setup Data
        doc_content = """
        Anthropic released Claude 3.5 Sonnet.
        Claude 3.5 Sonnet excels at coding tasks.
        Anthropic is an AI safety company based in San Francisco.
        """
        doc_id = uuid.uuid4()
        doc_key = f"test::graph::{doc_id}"
        
        doc = models.Document(
            id=doc_id,
            doc_key=doc_key,
            content=doc_content,
            source_file="test_graph.txt",
            domain="test.ai",
            metadata_={"test": True}
        )
        db_session.add(doc)
        db_session.commit()
        
        # 2. Run Enrichment (Synchronously for test)
        # Note: process_document uses its own session but we can mock or just let it run if DB is shared.
        # In integration tests, we usually target the same DB.
        
        # Since we just committed it, it should be visible.
        
        # FIX: Pass the test session to process_document so it can see uncommitted data
        # and participate in the test transaction.
        process_document(doc_id, session=db_session)
        
        # 3. Verify Results
        # Check Entities
        entities = db_session.query(models.Entity).filter(
            models.Entity.name.in_(["Anthropic", "Claude 3.5 Sonnet", "San Francisco"])
        ).all()
        
        entity_names = {e.name for e in entities}
        assert "Anthropic" in entity_names
        assert "Claude 3.5 Sonnet" in entity_names
        # "San Francisco" might be extracted depending on the model, but the first two are core.
        
        # Check Relationships
        # We expect Anthropic -> Claude 3.5 Sonnet (DEVELOPED_BY or similar)
        # We need to find the IDs first
        anthropic = next((e for e in entities if e.name == "Anthropic"), None)
        claude = next((e for e in entities if e.name == "Claude 3.5 Sonnet"), None)
        
        if anthropic and claude:
            rels = db_session.query(models.Relationship).filter(
                ((models.Relationship.source_id == anthropic.id) & (models.Relationship.target_id == claude.id)) |
                ((models.Relationship.source_id == claude.id) & (models.Relationship.target_id == anthropic.id))
            ).all()
            
            assert len(rels) > 0, "No relationship found between Anthropic and Claude"
            print(f"Found relationships: {[r.relation_type for r in rels]}")

        # Check Document-Entity Links
        links = db_session.query(models.DocumentEntity).filter(
            models.DocumentEntity.document_id == doc_id
        ).all()
        assert len(links) >= 1, "Document should be linked to at least 1 entity"
