# Variable Grounding System with Autonomous Intent Analysis

**Status**: ✅ IMPLEMENTED
**Version**: 1.0.0
**Author**: Claude (Anthropic)
**Date**: 2025-12-03

## Overview

The Variable Grounding System transforms Jarvis from a static RAG system into an **adaptive, self-aware intelligence** that automatically adjusts its grounding strategy based on query intent while maintaining creativity and factual accuracy as complementary forces, not conflicting constraints.

## Core Concept: Creative Context

> **"We want to keep creativity, don't force strict-mode, but force always having sources you get it? It's like creative context."**

The system implements three key innovations:

1. **Autonomous Grounding**: Jarvis analyzes query intent and auto-selects the appropriate grounding level
2. **In-line Confidence Scoring**: Claims are tagged with their evidence pedigree
3. **Interactive Grounding**: Users can challenge creative leaps with "prove it" requests

## Architecture

### 1. Intent Analyzer (`src/jarvis/memory/intent_analyzer.py`)

Classifies queries into three intent types and maps them to grounding levels:

| Intent Type | Grounding Level | Description | Example Query |
|-------------|----------------|-------------|---------------|
| **Factual** | strict | High-precision, zero-hallucination | "What is the current version of the auth API?" |
| **Creative** | soft | Allow bridging with speculation markers | "Brainstorm names for the new logging service" |
| **Explanatory** | balanced | Cite major claims, allow inference | "Explain the data flow for user profiles" |

#### Pattern Matching

The analyzer uses regex patterns to detect intent:

**Factual Patterns**:
- `what is|what are|define|version|current|status`
- `how does...work|function|operate`
- `spec|requirement|configuration`
- `error|bug|issue|problem`

**Creative Patterns**:
- `brainstorm|ideas|suggest|imagine|design`
- `name|naming|call it`
- `innovate|improve|optimize`
- `could we|what if|possible`

**Explanatory Patterns**:
- `explain|describe|overview|summary`
- `why|reason|purpose|goal`
- `architecture|design|pattern`
- `flow|pipeline|process`

#### Confidence Scoring

The analyzer calculates a confidence score (0.0-1.0) based on pattern matches and returns a `QueryIntent`:

```python
@dataclass
class QueryIntent:
    intent_type: Literal["factual", "creative", "explanatory"]
    grounding_level: GroundingLevel  # "soft" | "balanced" | "strict"
    confidence: float
    reasoning: str
```

### 2. Confidence Scorer (`src/jarvis/memory/confidence_scorer.py`)

Tags claims in LLM responses with their evidence pedigree:

| Tag Type | Trust Level | Source Examples |
|----------|-------------|-----------------|
| **[Grounded: source.md]** | High | `jarvis.core`, PDFs, architecture docs |
| **[Inferred: conversation.txt]** | Medium | `jarvis.conversations`, chat exports |
| **[Creative Leap]** | Low | No source, speculative bridge |

#### How It Works

1. **Extract Citations**: Parse response for `[1]`, `[2]`, etc.
2. **Classify Source Trust**: Categorize each source as high/medium/low trust
3. **Tag Citations**: Insert confidence tags before citation markers
4. **Detect Unsupported Claims**: Flag sentences without citations in strict/balanced mode

#### Example Output

**Input**:
```
The auth API uses JWT tokens [1] and connects to Redis [2].
```

**Output with Confidence Tags**:
```
The auth API uses JWT tokens [Grounded: auth/config.md] [1] and connects to Redis [Grounded: infrastructure/redis.yaml] [2].
```

### 3. Grounding Levels

Three grounding strategies that balance creativity and factual accuracy:

#### **Soft** (Creative Mode)
- **Philosophy**: Prefer sources, but allow bridging
- **Rules**:
  - Tie specific claims to sources when possible
  - Mark speculative ideas as `[Creative Leap]`
  - Never fabricate citations
- **Use Cases**: Brainstorming, ideation, exploratory questions

#### **Balanced** (Default)
- **Philosophy**: Every major claim must cite
- **Rules**:
  - All factual claims cite retrieved sources
  - If detail not present, say "not in memory"
  - Allow brief speculative glue, labeled as such
- **Use Cases**: Explanatory answers, technical documentation

#### **Strict** (Librarian Mode)
- **Philosophy**: Zero hallucination tolerance
- **Rules**:
  - Do NOT invent facts, entities, metrics, or examples
  - Do NOT infer beyond what's written
  - If context insufficient, respond: "No grounded context for this question"
  - Only summarize and reorganize exact information from context
- **Use Cases**: Compliance, legal, mission-critical queries

## Integration Points

### CLI (`src/jarvis/cli/query.py`)

```bash
# Auto-grounding (default)
jarvis query "What is the Jarvis memory architecture?"
# Output: 🧠 Intent: explanatory → grounding=balanced (confidence=0.67)

# Manual override
jarvis query "Brainstorm features" --grounding-level soft

# Disable auto-grounding
jarvis query "Some query" --no-auto-grounding

# Show confidence tags
jarvis query "Explain the pipeline" --show-confidence
```

### API (`src/jarvis/api/chat.py`)

```json
{
  "message": "What is the ingestion pipeline?",
  "auto_grounding": true,
  "show_confidence": false,
  "grounding_level": null
}
```

**Response includes**:
```json
{
  "query": "What is the ingestion pipeline?",
  "response": "The ingestion pipeline converts uploads (Markdown, PDF, HTML) into normalized chunks [Grounded: docs/architecture.md] [1]...",
  "sources": [...],
  "metadata": {
    "grounding_level": "balanced",
    ...
  }
}
```

### Web UI (`/chat` endpoint in `src/jarvis/api/app.py`)

The Jarvis BMAD Console web UI now includes autonomous grounding controls:

**Controls**:
- **🧠 auto** (checkbox, default: checked) - Enable autonomous grounding level selection
- **📊 confidence** (checkbox, default: unchecked) - Show in-line confidence tags
- **domain:** (text input) - Optional domain filter

**Optimized Defaults**:
- `k: 15` - Increased from 12 for better context retrieval
- `expand: 3` - Query expansion enabled for multi-query RRF fusion
- `auto_grounding: true` - Jarvis automatically selects grounding level
- All settings persisted in `localStorage`

**Access**: `http://localhost:8000/chat`

### Configuration (`config/settings.example.yaml`)

```yaml
query:
  default_grounding_level: "balanced"  # soft | balanced | strict
```

**Environment Variable Override**:
```bash
export JARVIS_GROUNDING_LEVEL=strict
```

## User Experience Flow

### Example 1: Factual Query (Auto-Strict)

**Input**:
```
User: "What is the current Qdrant collection configuration?"
```

**Process**:
1. Intent analyzer detects factual patterns: "what is", "current", "configuration"
2. Auto-selects `grounding_level=strict`
3. CLI shows: `🧠 Intent: factual → grounding=strict (confidence=0.85)`
4. LLM receives strict system prompt
5. Response cites only retrieved documentation

**Output**:
```
The Qdrant collection uses:
- 384-d vectors (all-MiniLM-L6-v2) [1]
- Cosine distance metric [1]
- HNSW indexing with m=16, ef_construct=200 [1]

Sources:
[1] docs/architecture.md (section: Qdrant Configuration)
```

### Example 2: Creative Query (Auto-Soft)

**Input**:
```
User: "Brainstorm ideas for improving the chat UI"
```

**Process**:
1. Intent analyzer detects creative patterns: "brainstorm", "ideas", "improving"
2. Auto-selects `grounding_level=soft`
3. CLI shows: `🧠 Intent: creative → grounding=soft (confidence=0.92)`
4. LLM receives soft system prompt
5. Response blends sources with creative suggestions

**Output**:
```
Based on existing chat patterns [1], here are some ideas:

1. **Real-time typing indicators** [Inferred: conversations/ui-feedback.txt] [2]
2. **Collapsible source panels** [Creative Leap]
3. **Keyboard shortcuts for common actions** [Grounded: docs/ux-design.md] [3]
4. **Dark mode with auto-detection** [Creative Leap]

Note: Ideas marked [Creative Leap] are speculative and not directly sourced from retrieved context.
```

### Example 3: Explanatory Query (Auto-Balanced)

**Input**:
```
User: "Explain how the domain inference works" --show-confidence
```

**Process**:
1. Intent analyzer detects explanatory patterns: "explain", "how"
2. Auto-selects `grounding_level=balanced`
3. Confidence scoring enabled
4. Response includes in-line trust indicators

**Output**:
```
Domain inference analyzes query text using heuristic patterns [Grounded: src/jarvis/memory/search.py] [1].

The system matches keywords to domain mappings [Inferred: docs/architecture/domain-taxonomy.md] [2]:
- "generative drive" → gd.generative_drive
- "epic" or "story" → project.sprints
- "cyber" keywords → cyber.security

If no patterns match, it defaults to jarvis.conversations as a hub [Grounded: src/jarvis/memory/search.py] [1].

📊 Confidence Legend:
- [Grounded: source.md] = Directly from high-trust source (core docs, PDFs)
- [Inferred: conversation.txt] = Inferred from conversational context
- [Creative Leap] = Speculative bridge built by Jarvis (challenge with "prove it")
```

## Interactive Grounding: "Prove It" Mode

### Future Enhancement (Not Yet Implemented)

When Jarvis generates a `[Creative Leap]`, users can challenge it:

```
User: "Explain the new CI/CD pipeline"

Jarvis: "...it connects to the staging environment using a dynamic token service [Creative Leap]."

User: "Ground that."

Jarvis: "Searching for evidence of 'dynamic token service' in CI/CD documentation..."
[Executes targeted search]

Jarvis: "I could not find direct evidence for a dynamic token service in the CI/CD docs.
This was an inference based on similar patterns in the auth workflow [1].
Would you like me to clarify this part of the pipeline?"
```

## Testing

### Manual Testing Script

```bash
# Test factual query → strict
jarvis query "What is the Qdrant vector size?" --show-confidence

# Test creative query → soft
jarvis query "Suggest improvements for the memory store" --show-confidence

# Test explanatory query → balanced
jarvis query "Explain the RAG pipeline" --show-confidence

# Test manual override
jarvis query "Some query" --grounding-level soft --show-confidence

# Test API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the ingestion pipeline?",
    "auto_grounding": true,
    "show_confidence": true
  }'
```

### Expected Outcomes

1. **Factual queries** should show `🧠 Intent: factual → grounding=strict`
2. **Creative queries** should show `🧠 Intent: creative → grounding=soft`
3. **Explanatory queries** should show `🧠 Intent: explanatory → grounding=balanced`
4. **Confidence tags** should appear when `--show-confidence` is enabled
5. **API responses** should include `metadata.grounding_level`

## Benefits

### 1. Reduced Cognitive Load
Users no longer need to manually select grounding levels for every query.

### 2. Adaptive Intelligence
Jarvis automatically adjusts its behavior based on context.

### 3. Transparency
In-line confidence scoring shows exactly where information comes from.

### 4. Flexibility
Manual overrides available when auto-detection is wrong.

### 5. Trust
Users can trace every claim back to its source or see when Jarvis is speculating.

## Future Roadmap

### Phase 1: ✅ COMPLETE
- [x] Intent analyzer with pattern matching
- [x] Confidence scorer with in-line tags
- [x] CLI integration with auto-grounding
- [x] API integration with auto-grounding
- [x] Documentation

### Phase 2: PLANNED
- [ ] "Prove it" interactive verification mode
- [ ] NLP-based sentence parsing (vs regex)
- [ ] Machine learning intent classification (vs heuristics)
- [ ] User feedback loop to improve intent detection
- [ ] Domain-specific grounding profiles

### Phase 3: VISIONARY
- [ ] Multi-agent consensus voting (Council of Ricks)
- [ ] Real-time grounding adjustment mid-response
- [ ] Confidence visualization in web UI
- [ ] Knowledge graph integration for evidence trails

## References

- **Intent Analyzer**: [`src/jarvis/memory/intent_analyzer.py`](../src/jarvis/memory/intent_analyzer.py)
- **Confidence Scorer**: [`src/jarvis/memory/confidence_scorer.py`](../src/jarvis/memory/confidence_scorer.py)
- **CLI Integration**: [`src/jarvis/cli/query.py`](../src/jarvis/cli/query.py)
- **API Integration**: [`src/jarvis/api/chat.py`](../src/jarvis/api/chat.py)
- **Schemas**: [`src/jarvis/api/schemas.py`](../src/jarvis/api/schemas.py)

---

**Valete-by-default. Non-binding. Always ready to riff.**
🚀 JARVIS — Autonomous Grounding Intelligence
