# Autonomous Knowledge Graph 🧠

**Version**: 4.0.0 (Cognitive Cockpit)  
**Status**: Production  
**Component**: `jarvis.memory`

---

## Overview

The Autonomous Knowledge Graph transforms JARVIS from a passive document store into an **active, self-organizing, cognitively navigable** system. It provides:

- 🔍 **Self-Discovering Ingestion** - Automatic entity/relationship extraction
- 🧩 **Graph Algorithms** - PageRank, Louvain clustering, shortest paths
- 🎮 **Cognitive Cockpit** - Interactive visualization with expand/collapse
- 🌐 **Domain Navigation** - Filter by knowledge domain

---

## 🚀 Key Features

### 1. Self-Discovering Ingestion
When a file is uploaded, the system automatically:
- **Classifies** the document domain (e.g., `jarvis.core`, `project.sprints`)
- **Extracts** Entities and Relationships via LLM (Gemini 2.5 Flash)
- **Links** the document to the Knowledge Graph
- **Computes** PageRank and cluster membership

### 2. Graph Schema (`jarvis.database.models`)

| Table | Purpose |
|-------|---------|
| `entities` | Nodes with name, kind, properties (JSONB) |
| `relationships` | Directed edges with relation_type |
| `document_entities` | Links documents to mentioned entities |

### 3. Graph Algorithms (`jarvis.memory.graph_analytics`)

| Algorithm | Purpose | Endpoint |
|-----------|---------|----------|
| **PageRank** | Entity importance scoring | `/graph/important` |
| **Louvain** | Community detection | `/graph/clusters` |
| **Shortest Path** | Find connections | `/graph/path` |
| **Hop Traversal** | Neighborhood expansion | `/graph/viewport` |

---

## 🛠️ API Reference

### Core Endpoints

#### `POST /api/memory/ingest`
Ingest a document with automatic graph enrichment.

```bash
curl -X POST "http://localhost:8000/api/memory/ingest" \
     -F "file=@./my-document.txt"
```

**Response**:
```json
{
  "status": "queued",
  "doc_id": "9f6846e8-...",
  "message": "Document ingested and enrichment scheduled."
}
```

---

### Graph Visualization Endpoints

#### `GET /api/memory/graph`
Get full graph for Cytoscape.js visualization.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `limit` | 500 | Max entities to return |
| `domain` | - | Filter by domain (optional) |

**Response**: Cytoscape.js format `{elements: {nodes, edges}}`

---

#### `GET /api/memory/graph/viewport`
Get neighborhood around a center node (viewport-aware pagination).

| Parameter | Default | Description |
|-----------|---------|-------------|
| `center_id` | required | UUID of center entity |
| `hops` | 2 | Number of hops to traverse |
| `limit` | 100 | Max nodes to return |

**Use case**: Double-click a node → load its neighbors dynamically.

---

### Graph Analytics Endpoints

#### `GET /api/memory/graph/important`
Get most important entities by PageRank score.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `limit` | 50 | Number of top entities |

**Response**:
```json
{
  "entities": [
    {"id": "...", "name": "Jarvis", "kind": "Product", "pagerank": 77.853}
  ],
  "count": 50
}
```

---

#### `GET /api/memory/graph/path`
Find shortest path between two entities.

| Parameter | Description |
|-----------|-------------|
| `from_id` | Source entity UUID |
| `to_id` | Target entity UUID |

**Response**:
```json
{
  "path": [
    {"name": "Jarvis", "kind": "Product"},
    {"name": "Qdrant", "kind": "Technology"},
    {"name": "Memory Pipeline", "kind": "Product"}
  ],
  "edges": ["QUERIES", "USES_TECHNOLOGY"],
  "length": 2
}
```

---

### Cluster Endpoints

#### `GET /api/memory/graph/clusters`
Get community clusters detected by Louvain algorithm.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `limit` | 20 | Max clusters to return |

**Response**:
```json
{
  "clusters": [
    {
      "cluster_id": 5,
      "size": 64,
      "representative": {"name": "Jarvis", "kind": "Product"},
      "top_entities": [...],
      "member_ids": [...]
    }
  ],
  "count": 5
}
```

---

#### `GET /api/memory/graph/cluster/{cluster_id}`
Get all nodes and edges within a specific cluster.

**Response**: Cytoscape.js format `{elements: {nodes, edges}}`

---

### Maintenance Endpoints

#### `POST /api/memory/graph/recompute`
Recompute PageRank scores for all entities.

#### `POST /api/memory/graph/recompute-clusters`
Recompute Louvain cluster assignments.

---

## 🎮 Cognitive Cockpit UI

Access at: **`GET /graph`**

### Features
- **Domain Matrix** - Sidebar navigation by knowledge domain
- **Entity Search** - Real-time filtering with highlighting
- **Coherent Chains** - Click node to see connection paths
- **Cluster View** - Toggle 🧩 button to see community clusters
- **Expand/Collapse** - Double-click clusters to expand members
- **Viewport Pagination** - Double-click nodes to load neighbors

### Keyboard/Mouse
| Action | Effect |
|--------|--------|
| Click node | Show info panel + highlight chains |
| Double-click node | Expand neighborhood (2 hops) |
| Double-click cluster | Expand to member nodes |
| Click background | Reset view |
| Search box | Filter + highlight matching entities |

---

## 🏗️ Architecture

```mermaid
graph TD
    User[User] -->|Upload| API[Ingest API]
    API -->|Save| FS[File System]
    API -->|Index| Qdrant[Vector DB]
    API -->|Queue| BG[Background Task]
    
    BG -->|Read| FS
    BG -->|Extract| LLM[Gemini 2.5 Flash]
    LLM -->|JSON| BG
    BG -->|Upsert| PG[Postgres Graph]
    
    PG --> Entities
    PG --> Relationships
    PG --> DocumentEntities
    
    subgraph Graph Analytics
        GA[graph_analytics.py]
        GA -->|PageRank| NX[NetworkX]
        GA -->|Clusters| LV[Louvain]
        GA -->|Paths| NX
    end
    
    subgraph Cognitive Cockpit
        UI[graph_viewer.html]
        UI -->|Fetch| GraphAPI[/api/memory/graph/*]
        UI -->|Render| CY[Cytoscape.js]
    end
```

---

## 📊 Performance

| Operation | Time (459 nodes) |
|-----------|------------------|
| PageRank | < 30ms |
| Louvain clustering | < 80ms |
| Shortest path | < 2ms |
| Graph viewport | < 50ms |
| Full graph load | < 200ms |

---

## ⚙️ Configuration

| Setting | Value | Location |
|---------|-------|----------|
| LLM Model | `gemini-2.5-flash` | `graph_enricher.py` |
| Context Window | 6000 chars | `graph_enricher.py` |
| Max Tokens | 1500 | `graph_enricher.py` |
| Retry Attempts | 3 | `graph_enricher.py` |
| Default Graph Limit | 500 | `memory.py` |

---

## 📁 File Structure

```
src/jarvis/
├── memory/
│   ├── graph_enricher.py    # LLM entity extraction
│   ├── graph_analytics.py   # PageRank, Louvain, paths
│   └── ingest.py            # Document ingestion
├── api/
│   └── memory.py            # All graph endpoints
├── frontend/
│   └── templates/
│       └── graph_viewer.html # Cognitive Cockpit UI
└── database/
    └── models.py            # Entity, Relationship, DocumentEntity

scripts/maintenance/
└── batch_graph_enrich.py    # Re-enrich all documents
```

---

## 🔧 Maintenance

### Re-enrich all documents
```bash
docker exec -it jarvis-app python scripts/maintenance/batch_graph_enrich.py
```

### Recompute analytics
```bash
curl -X POST http://localhost:8000/api/memory/graph/recompute
curl -X POST http://localhost:8000/api/memory/graph/recompute-clusters
```

### Query graph via SQL
```sql
-- Top entities by PageRank
SELECT name, kind, properties->>'pagerank' as rank
FROM entities
ORDER BY (properties->>'pagerank')::float DESC NULLS LAST
LIMIT 10;

-- Entities in cluster 5
SELECT name, kind FROM entities
WHERE properties->>'cluster' = '5';
```

---

## 📈 Current Stats

| Metric | Value |
|--------|-------|
| Entities | 459 |
| Relationships | 828 |
| Document Links | 875 |
| Clusters | 5+ |
| Domains | 15+ |

---

## 🧠 Phase 9: Epistemic Autonomy Layer

> **Motto**: "The system learns how to doubt itself."

**Status**: DORMANT (awaiting governance completion)

### New Models

| Table | Purpose |
|-------|---------|
| `epistemic_conflicts` | Contradiction tracking between beliefs |
| `belief_snapshots` | Temporal belief history per entity |
| `hypotheses` | Auto-generated research hypotheses |
| `model_performance` | LLM performance tracking per domain |

### New Modules

| Module | Purpose |
|--------|---------|
| `epistemic_engine.py` | Conflict detection (source, temporal) |
| `stability_index.py` | Cognitive Stability Index (CSI) |
| `belief_tracker.py` | Belief timeline and drift detection |
| `hypothesis_generator.py` | Auto-hypothesis from conflicts/sparse regions |
| `governance_node.py` | Human sovereignty and escalation |
| `model_calibrator.py` | Dynamic LLM model selection |

### Phase 9 Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/graph/conflicts` | List active contradictions |
| POST | `/graph/detect-conflicts` | Run conflict detection |
| POST | `/conflicts/{id}/resolve` | Human conflict resolution |
| GET | `/graph/stability` | System CSI metrics |
| POST | `/graph/recompute-csi` | Recompute CSI |
| GET | `/entity/{id}/beliefs` | Belief timeline |
| GET | `/graph/hypotheses` | Pending hypotheses |
| GET | `/graph/governance` | Governance status |

### Governance Configuration

```python
GOVERNANCE_CONFIG = {
    "csi_warning_threshold": 0.5,    # Below: warning
    "csi_critical_threshold": 0.3,   # Below: block actions
    "conflict_warning_threshold": 50, # Above: warning
    "conflict_critical_threshold": 100, # Above: block
    "require_approval_for": [
        "hypothesis_validation",
        "auto_conflict_resolution",
        "model_reselection",
        "belief_supersession",
    ],
}
```

### Why Dormant?

The epistemic autonomy layer is **not activated** until:
1. Epic 9 political governance is complete
2. Multi-human voting is implemented
3. Constitutional limits are defined

> "We don't want the model to evolve unbounded."
