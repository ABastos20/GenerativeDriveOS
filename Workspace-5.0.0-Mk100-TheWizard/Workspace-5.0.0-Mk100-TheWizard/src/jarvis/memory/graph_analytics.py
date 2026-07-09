"""
Graph Analytics Module - Server-side graph algorithms using NetworkX.

Provides:
- PageRank computation for entity importance
- Connected component detection
- Shortest path finding between nodes

Phase 7 Task 20: Server-Side Graph Algorithms
"""

import networkx as nx
import structlog
from uuid import UUID
from typing import Dict, List, Optional, Tuple, Any

from jarvis.database.postgres import get_session
from jarvis.database import models as db_models

logger = structlog.get_logger(__name__)


def build_graph_from_db() -> nx.DiGraph:
    """Build a NetworkX graph from all relationships in the database."""
    G = nx.DiGraph()
    
    with get_session() as session:
        # Load all entities as nodes
        entities = session.query(db_models.Entity).all()
        for e in entities:
            G.add_node(str(e.id), name=e.name, kind=e.kind)
        
        # Load all relationships as edges
        rels = session.query(db_models.Relationship).all()
        for r in rels:
            G.add_edge(
                str(r.source_id), 
                str(r.target_id),
                rel_type=r.relation_type,
                rel_id=str(r.id)
            )
    
    logger.info("graph_built", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    return G


def compute_pagerank(alpha: float = 0.85) -> Dict[str, float]:
    """
    Compute PageRank for all entities.
    Higher scores = more important/central nodes.
    """
    G = build_graph_from_db()
    
    if G.number_of_nodes() == 0:
        return {}
    
    # Use undirected for symmetric importance
    undirected = G.to_undirected()
    pagerank_scores = nx.pagerank(undirected, alpha=alpha)
    
    logger.info("pagerank_computed", num_nodes=len(pagerank_scores))
    return pagerank_scores


def get_top_entities(limit: int = 50) -> List[Dict[str, Any]]:
    """Get the most important entities by PageRank score."""
    scores = compute_pagerank()
    
    if not scores:
        return []
    
    # Sort by score descending
    sorted_entities = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    # Fetch entity details
    entity_ids = [UUID(eid) for eid, _ in sorted_entities]
    score_map = {eid: score for eid, score in sorted_entities}
    
    with get_session() as session:
        entities = session.query(db_models.Entity).filter(
            db_models.Entity.id.in_(entity_ids)
        ).all()
        
        results = []
        for e in entities:
            eid = str(e.id)
            results.append({
                "id": eid,
                "name": e.name,
                "kind": e.kind,
                "pagerank": round(score_map.get(eid, 0) * 1000, 3),  # Scale for readability
                "description": e.description
            })
        
        # Re-sort by pagerank (query doesn't preserve order)
        results.sort(key=lambda x: x["pagerank"], reverse=True)
        return results


def find_shortest_path(from_id: str, to_id: str) -> Optional[Dict[str, Any]]:
    """
    Find the shortest path between two entities.
    Returns path nodes and relationship types.
    """
    G = build_graph_from_db()
    
    # Use undirected for bidirectional path finding
    undirected = G.to_undirected()
    
    try:
        path = nx.shortest_path(undirected, source=from_id, target=to_id)
    except nx.NetworkXNoPath:
        return None
    except nx.NodeNotFound:
        return None
    
    # Fetch entity details for path nodes
    entity_ids = [UUID(eid) for eid in path]
    
    with get_session() as session:
        entities = session.query(db_models.Entity).filter(
            db_models.Entity.id.in_(entity_ids)
        ).all()
        
        entity_map = {str(e.id): {"id": str(e.id), "name": e.name, "kind": e.kind} for e in entities}
        
        # Build path with edge labels
        path_nodes = []
        path_edges = []
        
        for i, node_id in enumerate(path):
            path_nodes.append(entity_map.get(node_id, {"id": node_id, "name": "Unknown"}))
            
            if i < len(path) - 1:
                next_node = path[i + 1]
                # Check both directions for edge
                if G.has_edge(node_id, next_node):
                    edge_data = G.get_edge_data(node_id, next_node)
                    path_edges.append(edge_data.get("rel_type", "RELATED"))
                elif G.has_edge(next_node, node_id):
                    edge_data = G.get_edge_data(next_node, node_id)
                    path_edges.append(edge_data.get("rel_type", "RELATED"))
                else:
                    path_edges.append("CONNECTED")
        
        return {
            "path": path_nodes,
            "edges": path_edges,
            "length": len(path) - 1
        }


def get_connected_components() -> List[Dict[str, Any]]:
    """Get connected component statistics."""
    G = build_graph_from_db()
    undirected = G.to_undirected()
    
    components = list(nx.connected_components(undirected))
    
    results = []
    for i, component in enumerate(sorted(components, key=len, reverse=True)[:10]):
        results.append({
            "component_id": i,
            "size": len(component),
            "sample_nodes": list(component)[:5]
        })
    
    return results


def update_entity_pagerank():
    """
    Compute PageRank and store scores in Entity.properties JSONB field.
    Call this periodically to update importance scores.
    """
    scores = compute_pagerank()
    
    if not scores:
        logger.warning("no_pagerank_scores")
        return 0
    
    updated = 0
    with get_session() as session:
        for entity_id, score in scores.items():
            entity = session.query(db_models.Entity).filter(
                db_models.Entity.id == UUID(entity_id)
            ).first()
            
            if entity:
                if entity.properties is None:
                    entity.properties = {}
                entity.properties["pagerank"] = round(score * 1000, 3)
                updated += 1
        
        session.commit()
    
    logger.info("pagerank_updated", entities=updated)
    return updated


# ============================================================================
# Task 21: Louvain Community Detection (Level-of-Detail Clustering)
# ============================================================================

def detect_clusters() -> Dict[str, int]:
    """
    Detect communities using Louvain algorithm.
    Returns mapping of node_id -> cluster_id.
    """
    import community as community_louvain
    
    G = build_graph_from_db()
    
    if G.number_of_nodes() == 0:
        return {}
    
    # Louvain works on undirected graphs
    undirected = G.to_undirected()
    partition = community_louvain.best_partition(undirected)
    
    num_clusters = len(set(partition.values()))
    logger.info("louvain_clusters_detected", num_clusters=num_clusters, num_nodes=len(partition))
    
    return partition


def get_clusters(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get cluster summaries with representative nodes.
    Returns top clusters by size with their top entities.
    """
    partition = detect_clusters()
    
    if not partition:
        return []
    
    # Group nodes by cluster
    clusters: Dict[int, List[str]] = {}
    for node_id, cluster_id in partition.items():
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(node_id)
    
    # Sort clusters by size and take top N
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:limit]
    
    # Get PageRank scores for representative selection
    pagerank_scores = compute_pagerank()
    
    # Fetch entity details for all top cluster members
    all_node_ids = []
    for _, members in sorted_clusters:
        all_node_ids.extend(members[:10])  # Top 10 from each cluster
    
    with get_session() as session:
        entities = session.query(db_models.Entity).filter(
            db_models.Entity.id.in_([UUID(nid) for nid in all_node_ids])
        ).all()
        
        entity_map = {str(e.id): {"id": str(e.id), "name": e.name, "kind": e.kind} for e in entities}
        
        results = []
        for cluster_id, members in sorted_clusters:
            # Sort members by PageRank to find representative
            members_with_rank = [(m, pagerank_scores.get(m, 0)) for m in members]
            members_with_rank.sort(key=lambda x: x[1], reverse=True)
            
            representative_id = members_with_rank[0][0] if members_with_rank else None
            representative = entity_map.get(representative_id, {"name": f"Cluster {cluster_id}"})
            
            top_entities = [
                entity_map.get(m, {"id": m, "name": "Unknown"})
                for m, _ in members_with_rank[:5]
                if m in entity_map
            ]
            
            results.append({
                "cluster_id": cluster_id,
                "size": len(members),
                "representative": representative,
                "top_entities": top_entities,
                "member_ids": members[:20]  # Limit for payload size
            })
        
        return results


def update_entity_clusters():
    """
    Compute clusters and store cluster_id in Entity.properties JSONB field.
    Call this periodically after graph changes.
    """
    partition = detect_clusters()
    
    if not partition:
        logger.warning("no_clusters_detected")
        return 0
    
    updated = 0
    with get_session() as session:
        for entity_id, cluster_id in partition.items():
            entity = session.query(db_models.Entity).filter(
                db_models.Entity.id == UUID(entity_id)
            ).first()
            
            if entity:
                if entity.properties is None:
                    entity.properties = {}
                entity.properties["cluster"] = cluster_id
                updated += 1
        
        session.commit()
    
    logger.info("clusters_updated", entities=updated, num_clusters=len(set(partition.values())))
    return updated


def get_cluster_graph(cluster_id: int, limit: int = 50) -> Dict[str, Any]:
    """
    Get the subgraph for a specific cluster.
    Returns nodes and edges within the cluster.
    """
    partition = detect_clusters()
    
    # Get nodes in this cluster
    cluster_nodes = [nid for nid, cid in partition.items() if cid == cluster_id][:limit]
    
    if not cluster_nodes:
        return {"elements": {"nodes": [], "edges": []}}
    
    G = build_graph_from_db()
    cluster_set = set(cluster_nodes)
    
    with get_session() as session:
        entities = session.query(db_models.Entity).filter(
            db_models.Entity.id.in_([UUID(nid) for nid in cluster_nodes])
        ).all()
        
        nodes = [
            {
                "data": {
                    "id": str(e.id),
                    "label": e.name,
                    "kind": e.kind,
                    "weight": 20
                }
            }
            for e in entities
        ]
        
        # Get edges within cluster
        edges = []
        for source, target, data in G.edges(data=True):
            if source in cluster_set and target in cluster_set:
                edges.append({
                    "data": {
                        "source": source,
                        "target": target,
                        "label": data.get("rel_type", "RELATED"),
                        "id": data.get("rel_id", f"{source}-{target}")
                    }
                })
        
        return {"elements": {"nodes": nodes, "edges": edges}}
