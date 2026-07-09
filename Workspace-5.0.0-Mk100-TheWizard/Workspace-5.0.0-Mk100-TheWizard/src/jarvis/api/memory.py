"""Memory search API endpoints.

This module exposes retrieval from the Qdrant-backed memory store via HTTP.
"""

from __future__ import annotations

import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import os
from pathlib import Path
from uuid import uuid4

from jarvis.memory.ingest import ingest_file
from jarvis.memory.graph_enricher import process_document

from jarvis.database import models as db_models
from jarvis.database.postgres import get_session

from jarvis.memory import search as memory_search
from src.jarvis.api.schemas import (
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    DocumentResponse,
    DomainListResponse,
    DomainMetadata,
    DomainMetadataResponse,
    TagsListResponse,
    TagMetadata,
    TagMetadataResponse,
)

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Simple in-memory cache for metadata endpoints (per Architect Notes)
# TTL: 120 seconds (2 minutes) - balances freshness with performance
_METADATA_CACHE_TTL = 120.0
_metadata_cache: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/search",
    response_model=MemorySearchResponse,
    summary="Search Jarvis memory",
    description="Semantic search over the Jarvis knowledge base (Qdrant-backed).",
)
def search_memory_endpoint(request: MemorySearchRequest) -> MemorySearchResponse:
    """Search memory and return ranked results.

    This is a thin wrapper around ``jarvis.memory.search.search_memory``.
    """
    try:
        domains = [request.source] if request.source else None
        results = memory_search.search_memory(
            request.query,
            k=request.k,
            domains=domains,
            tags=request.tags,
        )
    except ValueError as exc:
        # Invalid input (empty query, bad k value)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Memory search failed: {exc}",
        ) from exc

    return MemorySearchResponse(
        results=[
            MemorySearchResult(
                text=r.text,
                score=r.score,
                doc_id=getattr(r, "doc_id", None),
                doc_key=getattr(r, "doc_key", None),
                source_file=r.source_file,
                section=r.section,
                domain=(r.domain or None).replace(".", "-") if r.domain else None,
                metadata=r.metadata,
            )
            for r in results
        ]
    )





@router.get(
    "/documents/key/{doc_key:path}",
    response_model=DocumentResponse,
    summary="Fetch full document content by Key",
    description="Return the stored document (full text) and metadata using its stable key.",
)
def get_document_by_key(doc_key: str) -> DocumentResponse:
    """Retrieve a document by doc_key."""
    with get_session() as session:  # type: Session
        doc = session.query(db_models.Document).filter(db_models.Document.doc_key == doc_key).one_or_none()
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        return DocumentResponse(
            id=getattr(doc, "id", None) or uuid4(),
            doc_key=getattr(doc, "doc_key", doc_key),
            source_file=getattr(doc, "source_file", ""),
            domain=getattr(doc, "domain", None),
            content=getattr(doc, "content", ""),
            metadata=getattr(doc, "metadata_", {}) or {},
        )



@router.get(
    "/documents/{doc_id:path}",
    response_model=DocumentResponse,
    summary="Fetch full document content by ID or key",
    description="Return the stored document (full text) and metadata. Supports both UUID and doc_key lookups.",
)
def get_document(doc_id: str) -> DocumentResponse:
    """Retrieve a document by UUID or doc_key.

    Dual-mode retrieval:
    - If doc_id is a UUID → query by Document.id
    - If doc_id contains '::' → query by Document.doc_key
    """
    try:
        with get_session() as session:  # type: Session
            # Detect if this is a doc_key (contains ::) or UUID
            if "::" in doc_id:
                # doc_key format: "conv::uuid" or "domain::filename"
                doc = session.query(db_models.Document).filter(db_models.Document.doc_key == doc_id).one_or_none()
            else:
                # UUID format
                # If doc_id contains slashes but no ::, it's not a UUID and not a key.
                # Standard UUID validation handles this, or database raises DataError.
                # However, with :path, we capture "key/foo".
                # If it doesn't match UUID format, Postgres might err.
                # We should try/except or validate UUID.
                # For now, relying on Postgres to return None or specific error structure.
                # Actually, invalid input syntax for type uuid is a database error.
                # But typically we assume if no :: it implies UUID *intent* or failed key lookup.
                pass
                try:
                    doc = session.query(db_models.Document).filter(db_models.Document.id == doc_id).one_or_none()
                except Exception:
                    # If invalid UUID string, ignore and treat as not found
                    doc = None

            if doc is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

            return DocumentResponse(
                id=doc.id,
                doc_key=doc.doc_key,
                source_file=doc.source_file,
                domain=doc.domain,
                content=doc.content,
                metadata=doc.metadata_,
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Document retrieval failed: {exc}",
        ) from exc


@router.get(
    "/domains",
    response_model=DomainListResponse,
    summary="List known domains with entities",
    description="Returns distinct domains that have at least one entity extracted.",
)
def list_domains() -> DomainListResponse:
    """Return domains that have entities linked (for Cognitive Cockpit navigation)."""
    try:
        with get_session() as session:  # type: Session
            # Only return domains that have at least one entity linked
            domains_with_entities = (
                session.query(db_models.Document.domain)
                .join(db_models.DocumentEntity, db_models.Document.id == db_models.DocumentEntity.document_id)
                .filter(db_models.Document.domain.isnot(None))
                .distinct()
                .all()
            )
            domains = {row[0] for row in domains_with_entities if row and row[0]}

            return DomainListResponse(domains=sorted(domains))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Domain listing failed: {exc}",
        ) from exc


@router.get(
    "/domains/metadata",
    response_model=DomainMetadataResponse,
    summary="List domains with metadata",
    description="Returns domains with descriptions and chunk counts. Cached for performance.",
)
def list_domains_metadata() -> DomainMetadataResponse:
    """Return domains with descriptions and chunk counts.

    Implements caching with 120s TTL per Architect Notes performance guidance.
    """
    # Check cache first
    cache_key = "domains_metadata"
    now = time.time()

    if cache_key in _metadata_cache:
        cached_data = _metadata_cache[cache_key]
        if now - cached_data["timestamp"] < _METADATA_CACHE_TTL:
            return DomainMetadataResponse(domains=cached_data["data"])

    try:
        from jarvis.database.qdrant import get_qdrant_client
        from jarvis.memory.heuristics.domain_descriptions import get_domain_description

        client = get_qdrant_client()

        # Scroll through all points and collect domain counts
        domain_counts: Dict[str, int] = {}
        scroll_result = client.scroll(
            collection_name="knowledge",
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = scroll_result
        while points:
            for point in points:
                if point.payload and "domain" in point.payload:
                    domain = point.payload["domain"]
                    if domain:
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1

            if next_offset is None:
                break

            scroll_result = client.scroll(
                collection_name="knowledge",
                limit=1000,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            points, next_offset = scroll_result

        # Build metadata list
        domain_metadata_list = [
            DomainMetadata(
                name=domain,
                description=get_domain_description(domain),
                chunk_count=count
            )
            for domain, count in sorted(domain_counts.items())
        ]

        # Update cache
        _metadata_cache[cache_key] = {
            "timestamp": now,
            "data": domain_metadata_list
        }

        return DomainMetadataResponse(domains=domain_metadata_list)

    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Domains metadata listing failed: {exc}",
        ) from exc


@router.get(
    "/tags",
    response_model=TagsListResponse,
    summary="List known tags",
    description="Returns distinct tags from all ingested chunks for UI filters.",
)
def list_tags() -> TagsListResponse:
    """Return the distinct set of tags found across all memory chunks."""
    try:
        from jarvis.database.qdrant import get_qdrant_client

        client = get_qdrant_client()

        # Scroll through all points and collect unique tags
        all_tags = set()
        scroll_result = client.scroll(
            collection_name="knowledge",
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = scroll_result
        while points:
            for point in points:
                if point.payload and "tags" in point.payload:
                    tags = point.payload["tags"]
                    if isinstance(tags, list):
                        all_tags.update(tags)

            if next_offset is None:
                break

            scroll_result = client.scroll(
                collection_name="knowledge",
                limit=1000,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            points, next_offset = scroll_result

        return TagsListResponse(tags=sorted(all_tags))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Tags listing failed: {exc}",
        ) from exc


@router.get(
    "/tags/metadata",
    response_model=TagMetadataResponse,
    summary="List tags with metadata",
    description="Returns tags with descriptions and usage counts. Cached for performance.",
)
def list_tags_metadata() -> TagMetadataResponse:
    """Return tags with descriptions and counts.

    Implements caching with 120s TTL per Architect Notes performance guidance.
    """
    # Check cache first
    cache_key = "tags_metadata"
    now = time.time()

    if cache_key in _metadata_cache:
        cached_data = _metadata_cache[cache_key]
        if now - cached_data["timestamp"] < _METADATA_CACHE_TTL:
            return TagMetadataResponse(tags=cached_data["data"])

    try:
        from jarvis.database.qdrant import get_qdrant_client
        from jarvis.memory.heuristics.tag_descriptions import get_tag_description

        client = get_qdrant_client()

        # Scroll through all points and collect tag counts
        tag_counts: Dict[str, int] = {}
        scroll_result = client.scroll(
            collection_name="knowledge",
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        points, next_offset = scroll_result
        while points:
            for point in points:
                if point.payload and "tags" in point.payload:
                    tags = point.payload["tags"]
                    if isinstance(tags, list):
                        for tag in tags:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1

            if next_offset is None:
                break

            scroll_result = client.scroll(
                collection_name="knowledge",
                limit=1000,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            points, next_offset = scroll_result

        # Build metadata list
        tag_metadata_list = [
            TagMetadata(
                tag=tag,
                description=get_tag_description(tag),
                count=count
            )
            for tag, count in sorted(tag_counts.items())
        ]

        # Update cache
        _metadata_cache[cache_key] = {
            "timestamp": now,
            "data": tag_metadata_list
        }

        return TagMetadataResponse(tags=tag_metadata_list)

    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Tags metadata listing failed: {exc}",
        ) from exc


@router.post(
    "/ingest",
    summary="Ingest and Enrich Document",
    description="Upload a document for ingestion. Triggers autonomous graph enrichment.",
)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict:
    """Ingest document and trigger graph enrichment."""
    try:
        # 1. Save to docs/inbox
        inbox_dir = Path("/workspace/docs/inbox")
        inbox_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = inbox_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Ingest
        # This writes to Postgres and Qdrant
        # It also applies the "Self Discovery" policy
        ingest_file(file_path)
        
        # 3. Retrieve ID for Enrichment
        # We construct key predictably
        doc_key = f"file::{file_path}"
        
        with get_session() as session:
            doc = session.query(db_models.Document).filter(db_models.Document.doc_key == doc_key).first()
            if doc:
                # 4. Schedule Enrichment
                background_tasks.add_task(process_document, doc.id)
                return {
                    "status": "queued",
                    "doc_id": str(doc.id),
                    "doc_key": doc_key,
                    "message": "Document ingested and enrichment scheduled."
                }
            else:
                return {
                    "status": "warning",
                    "message": "Ingestion ran but document not found in DB immediately."
                }
                
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc


@router.get(
    "/graph",
    summary="Get Relationship Graph",
    description="Retrieve nodes and edges for visualization. Optionally filter by domain.",
    response_model=dict,
)
async def get_graph_data(
    limit: int = 500,  # Increased to show full interconnected galaxy
    domain: Optional[str] = None
) -> dict:
    """Fetch graph data for Cytoscape.js, optionally matching a specific domain."""
    try:
        with get_session() as session:
            # Base query for entities
            query = session.query(db_models.Entity)
            
            # Filter by domain if requested
            if domain:
                # Entity -> DocumentEntity -> Document.domain == domain
                query = query.join(db_models.DocumentEntity).join(db_models.Document).filter(
                    db_models.Document.domain == domain
                )
            
            # Order by recency and limit
            entities = query.order_by(db_models.Entity.created_at.desc()).limit(limit).all()
            entity_ids = {e.id for e in entities}
            
            if not entity_ids:
                 return {"elements": {"nodes": [], "edges": []}}

            # Fetch relationships between these entities
            rels = session.query(db_models.Relationship).filter(
                (db_models.Relationship.source_id.in_(entity_ids)) | 
                (db_models.Relationship.target_id.in_(entity_ids))
            ).limit(limit * 2).all()
            
            nodes = [
                {
                    "data": {
                        "id": str(e.id),
                        "label": e.name,
                        "kind": e.kind,
                        "weight": 20  # default size
                    }
                }
                for e in entities
            ]
            
            edges = [
                {
                    "data": {
                        "source": str(r.source_id),
                        "target": str(r.target_id),
                        "label": r.relation_type,
                        "id": str(r.id)
                    }
                }
                for r in rels
                if r.source_id in entity_ids and r.target_id in entity_ids
            ]
            
            return {"elements": {"nodes": nodes, "edges": edges}}
            
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph fetch failed: {exc}",
        ) from exc


@router.get(
    "/graph/viewport",
    summary="Get graph subgraph centered on a node",
    response_model=dict,
)
async def get_graph_viewport(
    center_id: str,
    hops: int = 2,
    limit: int = 100
) -> dict:
    """Fetch graph neighborhood around a center node using hop-based traversal."""
    import networkx as nx
    from uuid import UUID
    
    try:
        with get_session() as session:
            # Build NetworkX graph from all relationships
            rels = session.query(db_models.Relationship).all()
            
            G = nx.DiGraph()
            for r in rels:
                G.add_edge(str(r.source_id), str(r.target_id), 
                          rel_type=r.relation_type, rel_id=str(r.id))
            
            # Get neighborhood within N hops
            try:
                center_uuid = UUID(center_id)
                center_str = str(center_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid center_id UUID")
            
            if center_str not in G:
                # Node exists but has no relationships - just return the node
                entity = session.query(db_models.Entity).filter(
                    db_models.Entity.id == center_uuid
                ).first()
                if not entity:
                    raise HTTPException(status_code=404, detail="Center node not found")
                return {"elements": {"nodes": [{
                    "data": {"id": center_str, "label": entity.name, 
                             "kind": entity.kind, "weight": 20}
                }], "edges": []}}
            
            # Get nodes within N hops (undirected for full neighborhood)
            undirected = G.to_undirected()
            neighborhood = nx.single_source_shortest_path_length(undirected, center_str, cutoff=hops)
            neighbor_ids = set(list(neighborhood.keys())[:limit])
            
            # Fetch entities
            entity_uuids = [UUID(eid) for eid in neighbor_ids]
            entities = session.query(db_models.Entity).filter(
                db_models.Entity.id.in_(entity_uuids)
            ).all()
            
            entity_id_set = {str(e.id) for e in entities}
            
            nodes = [
                {
                    "data": {
                        "id": str(e.id),
                        "label": e.name,
                        "kind": e.kind,
                        "weight": 20 if str(e.id) != center_str else 40,  # Center node bigger
                        "distance": neighborhood.get(str(e.id), 0)
                    }
                }
                for e in entities
            ]
            
            # Get edges between these nodes
            edges = []
            for source, target, data in G.edges(data=True):
                if source in entity_id_set and target in entity_id_set:
                    edges.append({
                        "data": {
                            "source": source,
                            "target": target,
                            "label": data.get("rel_type", "RELATED"),
                            "id": data.get("rel_id", f"{source}-{target}")
                        }
                    })
            
            return {"elements": {"nodes": nodes, "edges": edges}}
            
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Viewport fetch failed: {exc}",
        ) from exc


@router.get(
    "/graph/important",
    summary="Get most important entities by PageRank",
    response_model=dict,
)
async def get_important_entities(limit: int = 50) -> dict:
    """Get the most important/central entities in the knowledge graph using PageRank."""
    from jarvis.memory.graph_analytics import get_top_entities
    
    try:
        entities = get_top_entities(limit=limit)
        return {"entities": entities, "count": len(entities)}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PageRank computation failed: {exc}",
        ) from exc


@router.get(
    "/graph/path",
    summary="Find shortest path between two entities",
    response_model=dict,
)
async def get_shortest_path(from_id: str, to_id: str) -> dict:
    """Find the shortest path between two entities in the knowledge graph."""
    from jarvis.memory.graph_analytics import find_shortest_path
    
    try:
        result = find_shortest_path(from_id, to_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No path found between the specified entities"
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Path finding failed: {exc}",
        ) from exc


@router.post(
    "/graph/recompute",
    summary="Recompute graph analytics (PageRank)",
    response_model=dict,
)
async def recompute_graph_analytics() -> dict:
    """Recompute and store PageRank scores for all entities."""
    from jarvis.memory.graph_analytics import update_entity_pagerank
    
    try:
        updated = update_entity_pagerank()
        return {"status": "success", "entities_updated": updated}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PageRank update failed: {exc}",
        ) from exc


# ============================================================================
# Task 21: Cluster Endpoints (Louvain Community Detection)
# ============================================================================

@router.get(
    "/graph/clusters",
    summary="Get community clusters detected by Louvain algorithm",
    response_model=dict,
)
async def get_graph_clusters(limit: int = 20) -> dict:
    """Get community clusters with representative nodes and top entities."""
    from jarvis.memory.graph_analytics import get_clusters
    
    try:
        clusters = get_clusters(limit=limit)
        return {"clusters": clusters, "count": len(clusters)}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cluster detection failed: {exc}",
        ) from exc


@router.get(
    "/graph/cluster/{cluster_id}",
    summary="Get subgraph for a specific cluster",
    response_model=dict,
)
async def get_cluster_subgraph(cluster_id: int, limit: int = 50) -> dict:
    """Get all nodes and edges within a specific cluster."""
    from jarvis.memory.graph_analytics import get_cluster_graph
    
    try:
        return get_cluster_graph(cluster_id=cluster_id, limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cluster graph fetch failed: {exc}",
        ) from exc


@router.post(
    "/graph/recompute-clusters",
    summary="Recompute cluster assignments for all entities",
    response_model=dict,
)
async def recompute_clusters() -> dict:
    """Recompute and store cluster IDs for all entities using Louvain."""
    from jarvis.memory.graph_analytics import update_entity_clusters
    
    try:
        updated = update_entity_clusters()
        return {"status": "success", "entities_updated": updated}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cluster update failed: {exc}",
        ) from exc


# ============================================================================
# Phase 9: Epistemic Autonomy Layer Endpoints
# ============================================================================

@router.get(
    "/graph/conflicts",
    summary="Get active epistemic conflicts (contradictions)",
    response_model=dict,
)
async def get_conflicts(
    entity_id: Optional[str] = None,
    limit: int = 50
) -> dict:
    """Get active conflicts in the knowledge graph.
    
    Returns contradictions detected between beliefs about entities.
    """
    from jarvis.memory.epistemic_engine import get_active_conflicts, get_conflict_stats
    from jarvis.database.postgres import get_session
    
    try:
        with get_session() as session:
            conflicts = get_active_conflicts(
                session,
                entity_id=UUID(entity_id) if entity_id else None,
                limit=limit
            )
            stats = get_conflict_stats(session)
            
            return {
                "conflicts": conflicts,
                "count": len(conflicts),
                "stats": stats,
            }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conflicts: {exc}",
        ) from exc


@router.post(
    "/graph/detect-conflicts",
    summary="Run conflict detection algorithms",
    response_model=dict,
)
async def detect_conflicts() -> dict:
    """Run all conflict detection algorithms and persist new conflicts."""
    from jarvis.memory.epistemic_engine import run_conflict_detection
    
    try:
        result = run_conflict_detection()
        return {"status": "success", **result}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conflict detection failed: {exc}",
        ) from exc


@router.post(
    "/conflicts/{conflict_id}/resolve",
    summary="Resolve an epistemic conflict",
    response_model=dict,
)
async def resolve_conflict_endpoint(
    conflict_id: str,
    resolution: str = "human_override"
) -> dict:
    """Resolve a conflict with human or system decision.
    
    resolution: human_override | auto_reconciled | fact_1_wins | fact_2_wins
    """
    from jarvis.memory.epistemic_engine import resolve_conflict
    from jarvis.database.postgres import get_session
    
    valid_resolutions = {"human_override", "auto_reconciled", "fact_1_wins", "fact_2_wins"}
    if resolution not in valid_resolutions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resolution. Must be one of: {valid_resolutions}",
        )
    
    try:
        with get_session() as session:
            result = resolve_conflict(
                session,
                conflict_id=UUID(conflict_id),
                resolution=resolution,
                resolved_by="human"
            )
            return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflict: {exc}",
        ) from exc


@router.get(
    "/graph/stability",
    summary="Get Cognitive Stability Index (CSI) metrics",
    response_model=dict,
)
async def get_stability_metrics() -> dict:
    """Get system-wide and per-entity stability metrics.
    
    CSI = belief_coherence × evidence_freshness × domain_agreement
    """
    from jarvis.memory.stability_index import compute_system_csi
    
    try:
        metrics = compute_system_csi()
        return metrics
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute CSI: {exc}",
        ) from exc


@router.post(
    "/graph/recompute-csi",
    summary="Recompute and store CSI for all entities",
    response_model=dict,
)
async def recompute_csi() -> dict:
    """Recompute Cognitive Stability Index for all entities."""
    from jarvis.memory.stability_index import update_entity_csi
    
    try:
        updated = update_entity_csi()
        return {"status": "success", "entities_updated": updated}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSI update failed: {exc}",
        ) from exc


@router.get(
    "/entity/{entity_id}/beliefs",
    summary="Get belief timeline for an entity",
    response_model=dict,
)
async def get_entity_beliefs(entity_id: str, limit: int = 50) -> dict:
    """Get temporal belief history for a specific entity."""
    from jarvis.memory.belief_tracker import get_belief_timeline
    from jarvis.database.postgres import get_session
    
    try:
        with get_session() as session:
            beliefs = get_belief_timeline(session, UUID(entity_id), limit)
            return {
                "entity_id": entity_id,
                "beliefs": beliefs,
                "count": len(beliefs),
            }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get beliefs: {exc}",
        ) from exc


@router.get(
    "/graph/hypotheses",
    summary="Get pending hypotheses (DORMANT)",
    response_model=dict,
)
async def get_hypotheses(limit: int = 50) -> dict:
    """Get pending hypotheses awaiting human approval.
    
    Note: Hypothesis generation is DORMANT until Epic 9 governance complete.
    """
    from jarvis.memory.hypothesis_generator import get_pending_hypotheses
    from jarvis.database.postgres import get_session
    
    try:
        with get_session() as session:
            hypotheses = get_pending_hypotheses(session, limit)
            return {
                "status": "dormant",
                "message": "Hypothesis system awaiting governance approval",
                "hypotheses": hypotheses,
                "count": len(hypotheses),
            }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hypotheses: {exc}",
        ) from exc


@router.get(
    "/graph/governance",
    summary="Get governance status and escalation state",
    response_model=dict,
)
async def get_governance_status_endpoint() -> dict:
    """Get current governance status, CSI thresholds, and escalation reasons."""
    from jarvis.memory.governance_node import get_governance_status
    
    try:
        return get_governance_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get governance status: {exc}",
        ) from exc
