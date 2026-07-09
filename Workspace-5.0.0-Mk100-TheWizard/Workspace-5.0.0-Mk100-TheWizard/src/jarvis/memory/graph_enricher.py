"""Autonomous Knowledge Graph Enrichment Service.

This service processes documents to extract structural knowledge (Entities, Relationships)
using LLMs and persists them to the PostgreSQL Graph tables.
"""
from __future__ import annotations

import json
from uuid import UUID
from typing import List, Dict, Any, Optional

import structlog
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from jarvis.llm.client import call_llm
from jarvis.database.postgres import get_session
from jarvis.database.models import Document, Entity, Relationship, DocumentEntity

logger = structlog.get_logger(__name__)

GRAPH_EXTRACTION_SYSTEM_PROMPT = """Extract entities and relationships from the text as JSON.

Output ONLY this JSON structure with NO markdown:
{"entities":[{"name":"EntityName","kind":"Company|Product|Person|Technology|Concept","description":"Brief description"}],"relationships":[{"source":"EntityName1","target":"EntityName2","type":"RELATION_TYPE"}]}

Rules:
- Extract 3-8 key entities maximum (companies, products, people, technologies)
- Use short descriptions (under 50 chars)
- Avoid generic terms (User, System, It)
- Output valid JSON only, no text before or after"""

def extract_graph_elements(text: str, max_retries: int = 2) -> Dict[str, Any]:
    """Call LLM to extract entities and relations from text with retry logic."""
    if not text or len(text) < 100:
        return {"entities": [], "relationships": []}

    # Balance: 6000 chars input, 1500 tokens output
    preview_text = text[:6000]
    
    for attempt in range(max_retries + 1):
        try:
            response = call_llm(
                prompt=f"Extract knowledge graph:\n\n{preview_text}",
                system=GRAPH_EXTRACTION_SYSTEM_PROMPT,
                provider="google-ai",
                model="gemini-2.5-flash",
                max_tokens=1500
            )
            
            content = response.content.strip()
            if not content:
                logger.warning("llm_empty_response", attempt=attempt)
                continue
                
            # Strip markdown code blocks
            if "```" in content:
                parts = content.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        content = part
                        break
            
            content = content.strip()
            
            # Find JSON object
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                content = content[start:end]
            
            # Attempt parse
            try:
                data = json.loads(content)
                if data.get("entities"):
                    return data
            except json.JSONDecodeError as e:
                logger.warning("json_parse_error", error=str(e), attempt=attempt)
                continue
                
        except Exception as e:
            logger.error("extraction_attempt_failed", error=str(e), attempt=attempt)
            continue
    
    return {"entities": [], "relationships": []}


def process_document(doc_id: str | UUID, session: Session | None = None):
    """Enrich a document by extracting graph elements and updating DB.
    
    Args:
        doc_id: The ID of the document to process.
        session: Optional SQLAlchemy session. If provided, uses this session (useful for tests).
                 If None, creates a new session.
    """
    logger.info("graph_enrichment_start", doc_id=str(doc_id))
    
    # Use existing session or create new one
    if session:
        # Use provided session (no context manager needed as caller manages it)
        _process_with_session(doc_id, session)
    else:
        # Create new session
        with get_session() as new_session:
            _process_with_session(doc_id, new_session)
            new_session.commit()

def _process_with_session(doc_id: str | UUID, session: Session):
    """Internal processing logic reusing a session."""
    doc = session.query(Document).filter(Document.id == doc_id).one_or_none()
    if not doc:
        logger.warning("graph_enrichment_doc_not_found", doc_id=str(doc_id))
        return
    
    text = doc.content
        
    # extract outside session to avoid holding connection during LLM call? 
    # If passed session is open, we can't really "pause" it easily. 
    # But for tests it's fine. For prod, we usually don't pass session.
    # If passed session is open, we can't really "pause" it easily. 
    # But for tests it's fine. For prod, we usually don't pass session.
    # Note: If reusing session, we are holding it while calling LLM. 
    # This is a tradeoff for testability/atomic transactions if needed.
    graph_data = extract_graph_elements(text)
    
    if not graph_data.get("entities"):
        logger.info("graph_enrichment_no_entities", doc_id=str(doc_id))
        return

    # Upsert logic uses the passed 'session'
    # Re-fetch doc in new session
    # Upsert entities
    entity_map = {} # name -> uuid
    
    for e in graph_data.get("entities", []):
        name = e.get("name")
        if not name: continue
        
        # Simple upsert by name
        # Check existence first to get ID
        existing = session.query(Entity).filter(Entity.name == name).first()
        if existing:
            entity_map[name] = existing.id
            # Optionally update properties/kind if missing
        else:
            new_entity = Entity(
                name=name,
                kind=e.get("kind"),
                description=e.get("description"),
                properties=e.get("properties", {})
            )
            session.add(new_entity)
            session.flush() # get ID
            entity_map[name] = new_entity.id
            
    # Upsert relationships
    for r in graph_data.get("relationships", []):
        src_name = r.get("source")
        tgt_name = r.get("target")
        rel_type = r.get("type")
        
        src_id = entity_map.get(src_name)
        tgt_id = entity_map.get(tgt_name)
        
        if src_id and tgt_id and rel_type:
            # Check for existing rel to avoid duplicates
            params = {
                "source_id": src_id, 
                "target_id": tgt_id, 
                "relation_type": rel_type
            }
            exists = session.query(Relationship).filter_by(**params).first()
            if not exists:
                rel = Relationship(
                    source_id=src_id,
                    target_id=tgt_id,
                    relation_type=rel_type,
                    properties=r.get("properties", {})
                )
                session.add(rel)

    # Link Document to Entities
    doc_uuid = UUID(str(doc_id)) if isinstance(doc_id, str) else doc_id
    for name, ent_id in entity_map.items():
        # Check if link exists
        link_exists = session.query(DocumentEntity).filter_by(document_id=doc_uuid, entity_id=ent_id).first()
        if not link_exists:
            link = DocumentEntity(
                document_id=doc_uuid,
                entity_id=ent_id,
                confidence=1.0 # inferred from doc
            )
            session.add(link)
            
    # NOTE: Commit is handled by the caller if needed.
    
    logger.info("graph_enrichment_complete", doc_id=str(doc_id), entities=len(entity_map))
