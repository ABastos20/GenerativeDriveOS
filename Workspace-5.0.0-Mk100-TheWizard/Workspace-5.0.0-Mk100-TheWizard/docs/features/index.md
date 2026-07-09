# Features Documentation

This folder contains detailed documentation for JARVIS features and capabilities.

## 🧠 Cognitive Features

### [Autonomous Knowledge Graph](autonomous-knowledge-graph.md)
**Epic 8-7 | Status: Production**

Self-maintaining knowledge graph that automatically:
- Extracts entities and relationships from conversations
- Creates bidirectional links between concepts
- Identifies clusters and topic hierarchies
- Detects knowledge gaps and suggests research

**Key Capabilities:**
- Entity extraction (people, places, concepts, technologies)
- Relationship inference (is-a, part-of, related-to)
- Graph traversal for context expansion
- Visualization via Cytoscape.js

**Use Cases:**
- "Show me everything related to BMAD methodology"
- "What connects Epic 4 and autonomous research?"
- "Find experts in domain X"

---

### [Advanced Conversation Management](advanced-conversation-management.md)
**Epic 2-3 | Status: Production**

Sophisticated conversation lifecycle management:
- Conversation threading and branching
- Context preservation across sessions
- Conversation search and filtering
- Export/import conversation history

**Key Capabilities:**
- Thread-aware context windows
- Conversation tagging and categorization
- Full-text search across conversation history
- Pagination for large conversations

**Database Schema:**
- `conversations` table (title, created_at, last_active)
- `messages` table (role, content, metadata, voting_metadata, memory_attribution)
- JSONB for flexible metadata storage

---

### [Conversation Pagination & Search](conversation-pagination-search.md)
**Epic 3-4 Enhancement | Status: Production**

Fast, scalable conversation discovery:
- Paginated conversation lists (20 per page default)
- Full-text search on titles and content
- Filter by date range, participant, domain
- Sort by relevance, recency, or activity

**Performance:**
- Indexed searches: <50ms for 10K+ conversations
- Lazy loading for message content
- Efficient count queries with `COUNT(*)` optimization

**API Endpoints:**
- `GET /api/conversations?page=1&limit=20`
- `GET /api/conversations/search?q=query`
- `GET /api/conversations/{id}/messages?page=1`

---

## 🎨 UI/UX Features

### [UI Collapsible Panels](ui-collapsible-panels.md)
**Epic 4.5 UX | Status: Production**

Iron Man-style collapsible UI panels for cognitive cockpit:
- Primary Document Viewer (persistent across queries)
- Trust Scores Panel (domain expertise leaderboard)
- Governance Dashboard (proposals, votes, constitution)
- Cognitive Trace Inspector (replay query execution)

**Interaction Design:**
- Click header to expand/collapse
- Panels remember state across sessions
- Mobile-responsive (stack vertically on small screens)
- Smooth CSS transitions

**Technologies:**
- Vanilla JavaScript (no frameworks)
- CSS Grid for layout
- LocalStorage for state persistence

---

## 🔗 Feature Integration

### Multi-Agent Orchestration (Epic 4)
Features that leverage the Council of Ricks:
- **Autonomous Knowledge Graph**: Personas collaborate on entity extraction
- **Conversation Management**: Per-agent attribution in conversation history
- **Advanced Search**: Agent-specific context filtering

### Governance (Epic 9)
Features that integrate with democratic governance:
- **Trust Scores**: Displayed in UI panels
- **Conversation History**: Governance proposals stored as conversations
- **Knowledge Graph**: Governance relationships tracked

### ARCHES Cognitive Controller (Epic 4.5)
Features that use centralized cognitive state:
- **All Features**: Session tracking via ARCHESController
- **Knowledge Graph**: Gap detection triggers graph expansion
- **Conversation Management**: Cognitive trace attached to messages

---

## 📊 Feature Status Matrix

| Feature | Epic | Status | Dependencies |
|---------|------|--------|--------------|
| Autonomous Knowledge Graph | 8-7 | ✅ Production | Epic 4 (agents), Epic 4.5 (ARCHES) |
| Advanced Conversation Mgmt | 2-3 | ✅ Production | Epic 2 (memory backbone) |
| Conversation Pagination | 3-4 | ✅ Production | Epic 3 (RAG), PostgreSQL indexes |
| UI Collapsible Panels | 4.5 | ✅ Production | Epic 4.5 (UX authority) |

---

## 🎯 Planned Features (Future Epics)

### Epic 5: Cost-First LLM Router
- Provider priority dashboard
- Cost tracking visualization
- Free-tier depletion alerts

### Epic 6: Developer-Grade CLI
- Shell command invocation panel
- Git context awareness display
- Structured command outputs

### Epic 7: Web Intake & Refresh
- URL source manager
- Automatic refresh scheduler
- Content diff visualization

### Epic 10: 60-Year Memory Continuum
- Tiered storage browser
- Temporal query interface
- Memory migration dashboard

---

## 🔗 Related Documentation

**Architecture:**
- [../architecture/jarvis-memory-architecture.md](../architecture/jarvis-memory-architecture.md) - Memory system design
- [../architecture/domain-taxonomy.md](../architecture/domain-taxonomy.md) - Domain classification

**Technical Reference:**
- [../reference/knowledge-pipeline.md](../reference/knowledge-pipeline.md) - Data ingestion flow
- [../reference/agent-coordination.md](../reference/agent-coordination.md) - Multi-agent system

**Sprint Documentation:**
- [../sprints/epic-4-retro-2025-12-09.md](../sprints/epic-4-retro-2025-12-09.md) - Council of Ricks
- [../sprints/epic-4-5-retro-2025-12-09.md](../sprints/epic-4-5-retro-2025-12-09.md) - ARCHES stabilization

---

*Last Updated: 2025-12-09*
*Feature Set: v2.x (Cognitive OS with Governance)*
