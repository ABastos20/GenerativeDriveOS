# JARVIS Memory Architecture

> *"It's easier to understand the data as seeing it as building blocks pointing to something, multiple iterations multiple improvements, some work some not, but everything is important, what to do what to not."*

## Overview

JARVIS memory architecture is a **cognitive knowledge system** that mirrors the way human memory works - not as a static database, but as a living, evolving structure where knowledge chunks connect through semantic relationships, domain associations, and conversational context.

This document describes the **Memory Arches** - the foundational cognitive patterns that enable JARVIS to:
- Ingest and organize polymath knowledge spanning 166 domains
- Retrieve contextually relevant information across multiple modalities
- Learn from iterations and adapt retrieval strategies
- Maintain provenance and citation trails
- Evolve understanding over time through enrichment

### Current State (2025-12-02)

- **43,715 Qdrant points** across 6 collections
- **166 domain taxonomy** with 881 keyword heuristics
- **4-stage knowledge pipeline** (ingest → catalog → profile → enrich)
- **Multi-modal retrieval** (semantic, keyword, hybrid, expanded)
- **Cost-optimized LLM routing** (OpenRouter → Perplexity → local → direct)
- **Document-level intelligence** via majority-vote profiling

---

## I. Memory Arches - The Building Blocks

### Arch 1: Knowledge Atoms (Qdrant Points)

Every piece of knowledge in JARVIS memory is represented as a **point** in Qdrant - a vector embedding paired with rich metadata. These are the atomic building blocks.

#### Point Structure

```python
{
    "id": "chunk-uuid",
    "vector": [768-dim embedding],  # sentence-transformers/all-mpnet-base-v2
    "payload": {
        # Core identity
        "text": str,              # chunk content (1200-1500 chars)
        "hash": str,              # SHA-256 of text (deduplication)
        "chunk_index": int,       # position in source document

        # Provenance
        "source_file": str,       # workspace-relative path
        "source_type": str,       # pdf | md | txt | json | ipynb
        "section": str,           # logical heading/context
        "ingestion_timestamp": str,

        # Domain classification
        "domain": str,            # chunk-level domain (e.g., "jarvis.memory.rag")
        "domain_source": str,     # "heuristic" | "llm" | "direct"
        "doc_primary_domain": str, # document-level domain (majority vote)

        # Enrichment (optional)
        "summary": str,           # LLM-generated 1-2 sentence summary
        "facts": List[str],       # extracted key facts
        "tags": List[str],        # semantic tags
        "doc_type": str,          # architecture | reference | tutorial | conversation | ...

        # Metadata
        "tokens": int,            # approx token count
        "created_at": str,
        "updated_at": str,
    }
}
```

#### Collections Architecture

| Collection | Points | Purpose | Ingestion Source |
|-----------|--------|---------|------------------|
| `jarvis-core` | ~8,500 | System architecture, docs, code | `docs/`, `src/jarvis/`, workspace files |
| `jarvis-conversations` | ~25,000 | GPT export summaries, chat history | `external/gpt-export/`, `/api/chat` |
| `md` | ~4,200 | Markdown documentation | `*.md` files |
| `pdf` | ~3,800 | Research papers, manuals | `*.pdf` files |
| `txt` | ~1,500 | Plain text notes | `*.txt` files |
| `jarvis-insights` | ~715 | Compiled insights, learnings | `insights/`, enrichment pipeline |

**Design Rationale**: Separate collections allow targeted retrieval (e.g., search only `jarvis-conversations` for GPT export summaries) while enabling cross-collection semantic search when needed.

---

### Arch 2: Domain Taxonomy (Classification Framework)

The **domain taxonomy** is the cognitive framework that organizes knowledge into 166 semantic domains across 12 disciplines. This is how JARVIS understands *what kind of knowledge* a chunk represents.

See [domain-taxonomy.md](domain-taxonomy.md) for complete taxonomy reference.

#### Taxonomy Statistics

- **17 top-level categories**: jarvis, science, network, ai, infra, cyber, math, dev, philosophy, psychology, enterprise, finance, telecom, project, bmad, economics, ntt_data
- **166 unique domains**: Maximum 3 hierarchy levels (e.g., `jarvis.memory.rag`)
- **881 keyword mappings**: Zero-LLM classification via heuristics
- **~70% heuristic hit rate**: Reduces LLM calls for cost optimization

#### Domain Naming Convention

```
<category>.<subcategory>.<specialization>
│           │              │
│           │              └─ Optional 3rd level (e.g., "rag")
│           └─ 2nd level (e.g., "memory")
└─ Top level (e.g., "jarvis")

Examples:
- jarvis.memory.rag
- cyber.stix
- science.physics.quantum
- finance.banking.core
- psychology.adhd
```

#### Integration with Memory

Every Qdrant point carries **two domain fields**:
1. **`domain`** - Chunk-level classification (what this specific chunk is about)
2. **`doc_primary_domain`** - Document-level classification (what the whole document is about)

This dual-level classification enables:
- **Precise retrieval**: Find chunks about "STIX threat intelligence" (`domain: cyber.stix`)
- **Document context**: Understand the chunk came from a cybersecurity architecture doc (`doc_primary_domain: cyber.stix`)
- **Cross-domain insights**: Identify when JARVIS internals reference external domains (e.g., `jarvis.memory` chunks citing `ai.rag` concepts)

---

### Arch 3: Knowledge Pipeline (4-Stage Flow)

The knowledge pipeline is the **cognitive assembly line** that transforms raw documents into semantically enriched, domain-classified, retrievable knowledge.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  INGESTION  │───▶│   CATALOG   │───▶│   PROFILE   │───▶│  ENRICHMENT │
│             │    │             │    │             │    │             │
│  Raw docs   │    │  Domain     │    │  Document   │    │  LLM        │
│  → chunks   │    │  classify   │    │  majority   │    │  summaries, │
│  → embed    │    │  chunks     │    │  vote       │    │  facts,tags │
│  → Qdrant   │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Stage 1: Ingestion

**Purpose**: Convert documents into semantically meaningful chunks and store in Qdrant.

**Process**:
1. **Document parsing**:
   - PDF: `pdfplumber` (text + table extraction)
   - Markdown: AST parsing preserving structure
   - Text: Line-based chunking with context
   - JSON: GPT export format with conversation threading
   - Jupyter: Cell-level with output preservation

2. **Semantic chunking**:
   - Target: 1200-1500 characters per chunk
   - Preserve: Sentences, paragraphs, code blocks
   - Context: Section headings, surrounding text
   - Overlap: 100-200 chars for continuity

3. **Embedding generation**:
   - Model: `sentence-transformers/all-mpnet-base-v2`
   - Dimension: 768
   - Normalization: L2 (cosine similarity)

4. **Deduplication**:
   - Hash: SHA-256 of chunk text
   - Strategy: Skip if hash exists in collection

5. **Qdrant storage**:
   - Collection routing based on source type
   - Batch upsert (100 points at a time)
   - Metadata preservation

**CLI**:
```bash
jarvis ingest <path>                    # Ingest single file or directory
jarvis ingest --collection jarvis-core  # Target specific collection
jarvis ingest --reprocess              # Force re-ingestion (skip dedup)
```

**Iteration Learnings**:
- ✅ **Semantic chunking > fixed size**: Respecting sentence boundaries improves retrieval quality
- ✅ **Section context critical**: Preserving headings as metadata doubles retrieval precision
- ❌ **Don't chunk too small**: <800 char chunks lose context, <1200 is sweet spot
- ✅ **Deduplication essential**: Prevents duplicate insights across file copies

---

#### Stage 2: Catalog (Domain Classification)

**Purpose**: Classify each chunk into a domain using heuristics + LLM fallback.

**Process**:
```python
def classify_chunk(text: str, source_file: str) -> Tuple[str, str]:
    """
    Classify chunk into domain.
    Returns: (domain, source)  # source = "heuristic" | "llm" | "direct"
    """
    # 1. Check direct mapping (file path patterns)
    if domain := check_direct_mapping(source_file):
        return domain, "heuristic"

    # 2. Check keyword mapping (881 keywords)
    if domain := check_keyword_mapping(text):
        return domain, "heuristic"

    # 3. LLM fallback (Gemini 2.0 Flash)
    domain = llm_classify(text, available_domains=DOMAIN_LIST)
    return domain, "llm"
```

**Heuristic Classification** (Fast Path):

1. **Direct mapping** - File path patterns:
```python
DIRECT_DOMAIN_MAP = {
    "jarvis/memory/": "jarvis.memory",
    "jarvis/agents/": "jarvis.agents",
    "docs/architecture": "jarvis.architecture",
    "external/gpt-export": "jarvis.conversations",
    "GenerativeDrive/": "gd.generative_drive",
}
```

2. **Keyword mapping** - 881 keyword → domain rules:
```python
# Example from jarvis_domains.py
"council of ricks" → "jarvis.agents"
"query expansion" → "jarvis.memory.rag"
"persona registry" → "jarvis.personas"

# Example from cyber_domains.py
"stix 2.1" → "cyber.stix"
"certificate authority" → "cyber.pki"
"nessus scan" → "cyber.tenable"
```

**LLM Classification** (Fallback):

When heuristics miss (~30% of chunks), use Gemini 2.0 Flash:

```python
# Windowing strategy for long documents
def llm_classify_document(chunks: List[str], max_windows: int = 3) -> str:
    """
    Classify document using representative windows.
    Avoids MAX_TOKENS errors on long docs.
    """
    # Sample 2-3 chunks: beginning, middle, end
    windows = [
        chunks[0],                    # Beginning (context, intro)
        chunks[len(chunks) // 2],     # Middle (core content)
        chunks[-1] if len(chunks) > 1 else None  # End (conclusion)
    ]

    # Concatenate with separators
    text = "\n\n---\n\n".join([w for w in windows if w])

    # Prompt with available domains
    prompt = f"""Classify this document into ONE domain from:
{'\n'.join(DOMAIN_LIST)}

Document samples:
{text}

Return only the domain key (e.g., 'jarvis.memory.rag')."""

    return call_gemini(prompt, max_tokens=50)
```

**Performance**:
- **~70% heuristic hit rate** (30,650 / 43,715 points)
- **~30% LLM fallback** (13,065 points)
- **Cost**: ~$0.15 for 13k LLM classifications (Gemini 2.0 Flash)
- **Throughput**: ~500 chunks/min (heuristics), ~50 chunks/min (LLM)

**CLI**:
```bash
jarvis catalog domain-job            # Run full domain cataloging job
jarvis catalog stats                 # Show domain distribution stats
jarvis catalog validate              # Check for missing/invalid domains
```

**Iteration Learnings**:
- ✅ **Windowing prevents MAX_TOKENS errors**: Sample 2-3 chunks instead of full doc
- ✅ **Heuristics first = 70% cost savings**: Fast path covers most common domains
- ✅ **Domain list in prompt essential**: LLM invents domains without constraint
- ❌ **Don't use GPT-4 for classification**: 10x more expensive, negligible quality gain
- ✅ **Gemini 2.0 Flash optimal**: Free tier, fast, accurate enough for domain keys

---

#### Stage 3: Profile (Document-Level Intelligence)

**Purpose**: Aggregate chunk-level domains into document-level understanding via majority vote.

**Process**:
```python
def profile_document(source_file: str) -> str:
    """
    Determine document primary domain via majority vote.

    Example:
    - doc.md has 10 chunks:
      - 7 chunks → "jarvis.memory.rag"
      - 2 chunks → "ai.embeddings"
      - 1 chunk → "dev.python"
    - doc_primary_domain = "jarvis.memory.rag" (70% majority)
    """
    chunks = fetch_chunks_by_source(source_file)
    domain_counts = Counter([c.domain for c in chunks])
    primary_domain, count = domain_counts.most_common(1)[0]

    # Update all chunks with doc_primary_domain
    update_chunks(source_file, doc_primary_domain=primary_domain)

    return primary_domain
```

**Why Document-Level Profiling?**

1. **Contextual retrieval**: "Show me documents about RAG systems" → filter by `doc_primary_domain: jarvis.memory.rag`
2. **Cross-domain insights**: Find when JARVIS memory docs cite external AI concepts
3. **Domain analytics**: "Which domains dominate my knowledge base?"
4. **Provenance**: Trace answers back to source documents, not just chunks

**Profile Schema**:
```python
{
    "source_file": "docs/architecture/jarvis-memory-architecture.md",
    "doc_primary_domain": "jarvis.memory",
    "chunk_count": 15,
    "domain_distribution": {
        "jarvis.memory": 10,        # 67% - primary
        "jarvis.memory.rag": 3,     # 20%
        "ai.embeddings": 2,         # 13%
    },
    "confidence": 0.67,  # primary_count / total_chunks
    "tokens_total": 18750,
    "created_at": "2025-12-02T10:30:00Z",
}
```

**CLI**:
```bash
jarvis catalog profile-docs          # Run document profiling job
jarvis catalog doc-stats             # Show document-level domain stats
jarvis catalog doc-view <file>       # View document profile
```

**Iteration Learnings**:
- ✅ **Majority vote > first chunk**: First chunk often intro/boilerplate, not representative
- ✅ **Confidence threshold**: Flag docs with <50% majority for manual review
- ✅ **Cross-domain detection**: Docs with 30%+ secondary domain = cross-domain insight
- ❌ **Don't profile short docs**: <3 chunks = unreliable majority vote

---

#### Stage 4: Enrichment (LLM Augmentation)

**Purpose**: Add LLM-generated metadata (summaries, facts, tags, doc_type) to high-value documents.

**Process**:
```python
def enrich_document(source_file: str) -> Dict:
    """
    Generate LLM-enriched metadata for document.

    Enrichment fields:
    - summary: 1-2 sentence document overview
    - facts: List of key facts/insights (3-10 items)
    - tags: Semantic tags (5-15 tags)
    - doc_type: architecture | reference | tutorial | conversation | research | ...
    """
    chunks = fetch_chunks_by_source(source_file)

    # Use same windowing strategy as catalog
    windows = sample_representative_chunks(chunks, max_windows=3)
    text = "\n\n---\n\n".join(windows)

    prompt = f"""Analyze this document and provide:
1. Summary (1-2 sentences)
2. Key Facts (3-10 bullet points)
3. Tags (5-15 semantic tags)
4. Document Type (architecture|reference|tutorial|conversation|research|playbook|insight)

Document samples:
{text}

Return JSON:
{{
  "summary": "...",
  "facts": ["...", "..."],
  "tags": ["...", "..."],
  "doc_type": "..."
}}"""

    enrichment = call_gemini(prompt, max_tokens=500, response_format="json")

    # Update all chunks in document with enrichment
    update_chunks(source_file, **enrichment)

    return enrichment
```

**Enrichment Strategy**:

1. **Selective enrichment** - Target high-value docs:
   - Architecture docs (`docs/architecture/`, `docs/jarvis-*.md`)
   - Research papers (`*.pdf` in science domains)
   - Insights (`insights/`, compiled learnings)
   - GPT export summaries (`external/gpt-export/conversations/`)

2. **Batch processing** - Avoid overwhelming LLM API:
   - Process 50 docs at a time
   - 1-second delay between calls
   - Retry with exponential backoff

3. **Cost optimization**:
   - Use Gemini 2.0 Flash (free tier)
   - Window to 1200-1500 chars (not full doc)
   - Cache common prompts

**Enrichment Examples**:

```json
// jarvis-memory-architecture.md
{
  "summary": "JARVIS memory architecture document describing cognitive knowledge system with 43,715 Qdrant points, 166 domain taxonomy, 4-stage pipeline, and multi-modal retrieval strategies.",
  "facts": [
    "43,715 Qdrant points across 6 collections",
    "166 domain taxonomy with 881 keyword heuristics",
    "4-stage pipeline: ingest → catalog → profile → enrich",
    "70% heuristic hit rate reduces LLM calls",
    "Majority vote profiling for document-level intelligence"
  ],
  "tags": ["jarvis", "memory", "rag", "qdrant", "domain-taxonomy", "knowledge-pipeline", "embeddings", "retrieval", "cognitive-architecture"],
  "doc_type": "architecture"
}

// research-paper-quantum-computing.pdf
{
  "summary": "Research paper on quantum error correction using surface codes for fault-tolerant quantum computation.",
  "facts": [
    "Surface codes achieve threshold error rate of 1%",
    "Topological protection via qubit lattice geometry",
    "Logical qubit encoded in physical qubit array",
    "Syndrome measurement without destroying quantum state"
  ],
  "tags": ["quantum-computing", "error-correction", "surface-codes", "fault-tolerance", "qubits", "topology", "physics"],
  "doc_type": "research"
}
```

**CLI**:
```bash
jarvis enrich docs                   # Enrich all unenriched documents
jarvis enrich --collection jarvis-core  # Target specific collection
jarvis enrich --force                # Re-enrich existing
jarvis enrich stats                  # Show enrichment coverage
```

**Iteration Learnings**:
- ✅ **Summaries boost discovery**: "Find docs about X" matches summary text
- ✅ **Facts enable factual QA**: Retrieve specific facts, not full docs
- ✅ **Tags improve semantic search**: Tags capture implicit concepts
- ❌ **Don't enrich everything**: Code files, logs, trivial docs = waste of tokens
- ✅ **doc_type enables type-specific retrieval**: "Show me all architecture docs"
- ✅ **Windowing prevents hallucination**: Full doc → LLM invents facts, samples → stays grounded

---

## II. Retrieval Strategies (Cognitive Access Patterns)

JARVIS memory supports **4 retrieval strategies** optimized for different query patterns:

### 1. Semantic Search (Default)

**Use case**: Natural language questions, conceptual queries

**How it works**:
1. Embed query using same model as ingestion (`all-mpnet-base-v2`)
2. Qdrant cosine similarity search
3. Return top-k most similar chunks

**Example**:
```bash
jarvis query "How does JARVIS handle domain classification?"
# Retrieves chunks about heuristics, LLM fallback, taxonomy
```

**Strengths**: Best for conceptual matches, synonyms, paraphrasing
**Weaknesses**: Misses exact keywords, technical terms

---

### 2. Keyword Search

**Use case**: Exact term matching, code symbols, technical jargon

**How it works**:
1. Tokenize query into keywords
2. Qdrant BM25 full-text search on `text` field
3. Return top-k by BM25 score

**Example**:
```bash
jarvis query "STIX 2.1 threat intelligence" --retriever keyword
# Retrieves chunks with exact "STIX 2.1" mentions
```

**Strengths**: Exact matches, proper nouns, code identifiers
**Weaknesses**: Misses semantic variations, requires exact wording

---

### 3. Hybrid Search (Best of Both)

**Use case**: General-purpose retrieval balancing semantic + keyword

**How it works**:
1. Run semantic search → normalize scores to [0,1]
2. Run keyword search → normalize scores to [0,1]
3. Combine with weighted sum: `score = w * semantic + (1-w) * keyword`
4. Return top-k by combined score

**Example**:
```bash
jarvis query "JARVIS RAG memory system" --retriever hybrid --weight 0.7
# 70% semantic, 30% keyword
```

**Configuration**:
- Default weight: 0.7 (70% semantic, 30% keyword)
- Configurable via `--weight` flag or `settings.query.semantic_weight`

**Strengths**: Robust across query types, balances precision/recall
**Weaknesses**: Slightly slower (2x retrieval calls)

---

### 4. Expanded Search (Multi-Query + Fusion)

**Use case**: Complex queries requiring multiple perspectives

**How it works**:
1. Generate 3-5 query variations using LLM:
   ```
   Original: "How does JARVIS memory work?"
   Expansions:
   - "JARVIS knowledge storage architecture"
   - "RAG retrieval pipeline in JARVIS"
   - "Qdrant vector database integration"
   - "Domain classification and cataloging"
   ```

2. Execute semantic search for each variation
3. Fuse results using Reciprocal Rank Fusion (RRF):
   ```python
   rrf_score(chunk) = sum(1 / (k + rank_i)) for all queries where chunk appears
   # k = 60 (fusion constant)
   ```

4. Return top-k by RRF score

**Example**:
```bash
jarvis query "memory architecture" --expand 3
# Generates 3 query variations, fuses results
```

**Configuration**:
- Default expansions: 3
- Max expansions: 5
- Configurable via `--expand` flag or `settings.query.expand_count`

**Strengths**: Best recall, surfaces diverse perspectives, reduces query brittleness
**Weaknesses**: Slower (3-5x retrieval calls), higher LLM cost for expansion

**Iteration Learnings**:
- ✅ **RRF > score averaging**: Handles score scale differences across queries
- ✅ **3 expansions sweet spot**: 5+ → diminishing returns, noise
- ✅ **Expansion prompt critical**: "Rephrase in different technical contexts" > "Give me synonyms"
- ❌ **Don't expand simple queries**: "What is X?" doesn't need expansion

---

## III. Cognitive Patterns (How JARVIS Thinks)

### Pattern 1: Heuristic → LLM Fallback (Cost-First Intelligence)

**Principle**: Solve 70% of problems with fast, cheap heuristics before invoking expensive LLM.

**Application**: Domain classification
- Try keyword matching first (instant, free)
- Fall back to Gemini only when heuristics miss
- Result: 70% cost savings, 10x faster throughput

**Lessons**:
- Build comprehensive heuristic libraries (881 keywords)
- Monitor heuristic hit rates
- Expand heuristics based on LLM fallback patterns

---

### Pattern 2: Majority Vote (Wisdom of Chunks)

**Principle**: Aggregate chunk-level signals into document-level intelligence.

**Application**: Document profiling
- Each chunk votes for a domain
- Document inherits majority domain
- Result: Document-level context for retrieval

**Lessons**:
- Requires minimum 3 chunks for reliable vote
- Confidence score = majority_count / total_chunks
- Flag <50% confidence for review

---

### Pattern 3: Windowing (Sample, Don't Summarize)

**Principle**: For long documents, sample representative windows instead of full text.

**Application**: LLM classification and enrichment
- Sample beginning, middle, end chunks (2-3 windows)
- Preserves context without MAX_TOKENS errors
- Result: Handles 100-page PDFs reliably

**Lessons**:
- Window size: 1200-1500 chars (Gemini sweet spot)
- Max windows: 3 (diminishing returns beyond)
- Always include first chunk (context) and last chunk (conclusion)

---

### Pattern 4: Dual-Level Classification (Chunk + Document)

**Principle**: Maintain both micro (chunk) and macro (document) domain context.

**Application**: Retrieval and analytics
- Chunk domain: What is this specific chunk about?
- Document domain: What is the overall document about?
- Result: Precise retrieval + document context

**Lessons**:
- Chunk domains capture fine-grained topics
- Document domains enable cross-document insights
- Both are essential for provenance

---

### Pattern 5: Semantic Chunking (Respect Meaning Boundaries)

**Principle**: Chunk on semantic boundaries (sentences, paragraphs, code blocks), not fixed byte counts.

**Application**: Ingestion
- Preserve sentences and paragraphs
- Never split mid-sentence
- Include section headings as metadata
- Result: Higher retrieval quality, better context

**Lessons**:
- Target range: 1200-1500 chars
- Acceptable range: 800-2000 chars
- Overlap: 100-200 chars for continuity
- Too small (<800): Loses context
- Too large (>2000): Dilutes semantic signal

---

### Pattern 6: Multi-Query Fusion (Diversity over Precision)

**Principle**: For complex queries, retrieve from multiple angles and fuse results.

**Application**: Expanded search
- Generate query variations (rephrasing, perspective shifts)
- Retrieve for each variation
- Fuse with RRF (rewards consistency across queries)
- Result: Better recall, reduced query brittleness

**Lessons**:
- 3 expansions optimal
- RRF better than score averaging (handles scale differences)
- Don't expand trivial queries
- Expansion prompt quality matters

---

## IV. Iteration Timeline & Learnings

### Iteration 1: Naive RAG (Early 2024)

**What we built**:
- Fixed 512-char chunking
- Semantic search only
- No domain classification
- Single "knowledge" collection

**What worked**:
- ✅ Basic retrieval functional
- ✅ Qdrant fast and reliable

**What didn't**:
- ❌ Fixed chunking split sentences mid-word
- ❌ No way to filter by topic/domain
- ❌ Retrieved irrelevant context from wrong domains
- ❌ No provenance tracking

**Lessons learned**:
- Semantic boundaries > fixed sizes
- Need domain taxonomy for precision
- Provenance essential for trust

---

### Iteration 2: Semantic Chunking + Collections (Mid 2024)

**What we changed**:
- Semantic chunking (respect sentences)
- Separate collections (core, conversations, md, pdf, txt)
- Source file metadata
- Section heading preservation

**What worked**:
- ✅ Retrieval quality doubled
- ✅ Collection filtering enabled domain hints
- ✅ Provenance via source_file

**What didn't**:
- ❌ Collection = domain too coarse (can't distinguish subtopics)
- ❌ No way to search across collections semantically
- ❌ Still no proper domain classification

**Lessons learned**:
- Collections good for source type, not domain
- Need finer-grained domain taxonomy
- Cross-collection search essential

---

### Iteration 3: Domain Taxonomy + Heuristics (Nov 2024)

**What we changed**:
- Created initial domain taxonomy (~20 domains)
- Added keyword heuristics (~50 mappings)
- Domain field in Qdrant payload
- LLM fallback for missed domains

**What worked**:
- ✅ Domain filtering precision jumped
- ✅ Heuristics covered common cases
- ✅ LLM fallback handled edge cases

**What didn't**:
- ❌ Only ~20 domains insufficient for polymath knowledge
- ❌ Missing entire disciplines (finance, psychology, philosophy)
- ❌ No JARVIS self-awareness domains
- ❌ Heuristic coverage only ~40%

**Lessons learned**:
- Taxonomy must match knowledge breadth
- Heuristics need continuous expansion
- Self-awareness critical (JARVIS should know about JARVIS)

---

### Iteration 4: Comprehensive Taxonomy (Dec 2024)

**What we changed**:
- Expanded taxonomy to 166 domains
- 881 keyword heuristics across 12 disciplines
- Modular heuristics architecture
- JARVIS self-awareness domains (20 domains)
- Added missing disciplines: finance, psychology, philosophy, enterprise

**What worked**:
- ✅ Heuristic hit rate → 70%
- ✅ Full polymath coverage
- ✅ JARVIS can classify its own docs
- ✅ Domain profiling enables document-level insights

**What didn't**:
- ❌ Keyword list maintenance overhead
- ❌ Some domains still ambiguous (overlap)

**Lessons learned**:
- Modular architecture essential for maintenance
- Validation tools catch conflicts
- 70% heuristic hit rate = sustainable cost
- Domain granularity sweet spot: 2-3 levels

---

### Iteration 5: Document Profiling + Enrichment (Dec 2024)

**What we changed**:
- Majority vote document profiling
- LLM enrichment (summaries, facts, tags, doc_type)
- Windowing strategy for long docs
- Dual-level domain classification (chunk + doc)

**What worked**:
- ✅ Document-level intelligence enables new query patterns
- ✅ Enrichment boosts discovery ("find docs about X")
- ✅ Windowing prevents MAX_TOKENS errors
- ✅ Facts enable factual QA

**What didn't**:
- ❌ Enrichment cost adds up (need selective strategy)
- ❌ Some LLM-generated tags too generic

**Lessons learned**:
- Enrich selectively (high-value docs only)
- Windowing > full doc for classification
- Facts must be grounded in text (no hallucination)
- doc_type enables powerful filtering

---

### Iteration 6: Multi-Modal Retrieval (Dec 2024)

**What we changed**:
- Added keyword search (BM25)
- Hybrid search with configurable weighting
- Expanded search with RRF fusion
- Query expansion via LLM

**What worked**:
- ✅ Hybrid search robust across query types
- ✅ Expanded search best recall
- ✅ RRF fusion effective
- ✅ Query variations capture diverse perspectives

**What didn't**:
- ❌ Expansion adds latency
- ❌ Some expanded queries too similar (redundant)

**Lessons learned**:
- Default to hybrid for general queries
- Use expanded for complex/ambiguous queries
- 3 expansions optimal (5+ diminishing returns)
- RRF > score averaging

---

## V. Cross-Links: Domain Taxonomy ↔ Memory Arches

The **domain taxonomy** and **memory arches** are symbiotic - one provides the classification framework, the other provides the storage and retrieval substrate.

### How They Connect

```
Domain Taxonomy (166 domains)
    ↓
Heuristic Classification (881 keywords)
    ↓
Qdrant Points (43,715 chunks)
    ↓
Document Profiles (majority vote)
    ↓
Retrieval (semantic, keyword, hybrid, expanded)
    ↓
LLM Context (citations with domain provenance)
```

### Taxonomy → Memory Flow

1. **Taxonomy defines domains**:
   - 166 semantic domains across 12 disciplines
   - Hierarchical structure (e.g., `jarvis.memory.rag`)

2. **Heuristics map keywords → domains**:
   - 881 keyword rules
   - Fast classification without LLM

3. **Memory stores domain metadata**:
   - Every Qdrant point has `domain` field
   - Every document has `doc_primary_domain` field

4. **Retrieval uses domain filters**:
   - `source` parameter in queries
   - Domain-scoped search (e.g., "search only jarvis.memory")

5. **LLM context includes domain provenance**:
   - Citations show which domains contributed to answer
   - Enables domain analytics

### Memory → Taxonomy Feedback Loop

1. **LLM fallback identifies gaps**:
   - Track which chunks require LLM classification
   - High LLM usage in topic → add heuristics

2. **Domain distribution analytics**:
   - Which domains are over/under-represented?
   - Adjust ingestion sources to balance

3. **Cross-domain insights**:
   - Documents with 30%+ secondary domain = cross-domain
   - Reveal interdisciplinary connections

4. **Heuristic expansion**:
   - Mine LLM-classified chunks for new keywords
   - Add to heuristic library, reduce LLM calls

### Example: JARVIS Self-Awareness

```
Taxonomy: jarvis.memory.rag domain
    ↓
Heuristics: "query expansion", "reciprocal rank fusion", "semantic search"
    ↓
Memory: 342 chunks classified as jarvis.memory.rag
    ↓
Document Profile: 18 docs with doc_primary_domain = jarvis.memory.rag
    ↓
Retrieval: User asks "How does RAG work in JARVIS?"
    ↓
Filter: source = jarvis.memory.rag
    ↓
LLM Context: 10 chunks from jarvis.memory.rag domain
    ↓
Answer: Detailed explanation with citations to architecture docs
```

---

## VI. Operational Runbooks

### Runbook 1: Daily Operations

**Health Check**:
```bash
# Check Qdrant status
docker ps --filter "name=jarvis-qdrant"
curl http://localhost:6333/collections

# Check point counts
jarvis stats collections

# Check domain distribution
jarvis catalog stats
```

**Expected**:
- Qdrant healthy, 6 collections active
- ~43,715 total points (±5% growth per week)
- Top domains: jarvis.conversations (~57%), jarvis.memory (~5%), cyber.stix (~3%)

---

### Runbook 2: Ingestion Workflow

**Daily Ingestion** (new files):
```bash
# Ingest workspace changes
jarvis ingest docs/
jarvis ingest src/jarvis/

# Ingest GPT export updates (if mounted)
jarvis ingest external/gpt-export/
```

**Weekly Ingestion** (OneDrive sync):
```bash
# Ingest OneDrive documents (if mounted)
jarvis ingest /mnt/onedrive/Documents/
```

**Validation**:
```bash
# Check for failed ingestions
jarvis stats ingestion-errors

# Verify new points added
jarvis stats collections --since 1d
```

---

### Runbook 3: Domain Cataloging

**Weekly Domain Job**:
```bash
# Run domain cataloging for uncataloged chunks
jarvis catalog domain-job

# Check heuristic hit rate
jarvis catalog stats --detail

# Review LLM fallback patterns
jarvis catalog llm-fallback-report
```

**Expected**:
- ~70% heuristic hit rate
- <30% LLM fallback
- Cost: ~$0.05-0.15 per 1000 new chunks

**Heuristic Expansion** (monthly):
```bash
# Extract common keywords from LLM-classified chunks
jarvis catalog mine-keywords --domain jarvis.memory.rag

# Add to heuristics/*.py
# Re-run validation
jarvis catalog validate-heuristics
```

---

### Runbook 4: Document Profiling

**Weekly Profile Job**:
```bash
# Profile unprofiled documents
jarvis catalog profile-docs

# Check document domain distribution
jarvis catalog doc-stats

# Review low-confidence docs (<50% majority)
jarvis catalog low-confidence-docs
```

**Manual Review**:
```bash
# View document profile
jarvis catalog doc-view docs/architecture/jarvis-memory-architecture.md

# Override if incorrect
jarvis catalog set-doc-domain docs/path/to/file.md jarvis.memory
```

---

### Runbook 5: Enrichment

**Selective Enrichment** (weekly):
```bash
# Enrich architecture docs
jarvis enrich --collection jarvis-core --doc-type architecture

# Enrich research papers
jarvis enrich --collection pdf --domain science.*

# Check enrichment coverage
jarvis enrich stats
```

**Cost Control**:
```bash
# Estimate enrichment cost before running
jarvis enrich --dry-run --collection jarvis-core

# Set budget limit (max LLM calls)
jarvis enrich --max-docs 100
```

---

### Runbook 6: Retrieval Testing

**Weekly Retrieval Quality Check**:
```bash
# Test semantic search
jarvis query "JARVIS memory architecture" --verbose

# Test keyword search
jarvis query "Qdrant vector database" --retriever keyword --verbose

# Test hybrid search
jarvis query "domain classification pipeline" --retriever hybrid --verbose

# Test expanded search
jarvis query "how does RAG work?" --expand 3 --verbose
```

**Validation**:
- Semantic: Top results semantically relevant?
- Keyword: Exact terms present in results?
- Hybrid: Balanced precision/recall?
- Expanded: Diverse perspectives retrieved?

---

### Runbook 7: Analytics & Monitoring

**Weekly Analytics**:
```bash
# Domain distribution
jarvis analytics domain-distribution

# Citation provenance (from /api/chat)
jarvis analytics citations --since 7d

# Query performance
jarvis analytics query-latency --since 7d

# LLM cost tracking
jarvis analytics llm-costs --since 30d
```

**Alerts** (configure monitoring):
- Qdrant point count drops >10%
- Heuristic hit rate <65%
- Enrichment cost >$5/day
- Query latency p95 >2s

---

### Runbook 8: Disaster Recovery

**Backup Qdrant**:
```bash
# Create snapshot
curl -X POST http://localhost:6333/collections/jarvis-core/snapshots

# Download snapshot
curl http://localhost:6333/collections/jarvis-core/snapshots/<snapshot-id> \
  --output jarvis-core-backup.snapshot

# Repeat for all collections
```

**Restore from Backup**:
```bash
# Upload snapshot
curl -X POST http://localhost:6333/collections/jarvis-core/snapshots/upload \
  -F "snapshot=@jarvis-core-backup.snapshot"

# Restore collection
curl -X PUT http://localhost:6333/collections/jarvis-core/snapshots/<snapshot-id>/recover
```

**PostgreSQL Backup**:
```bash
# Backup conversations database
docker exec jarvis-postgres pg_dump -U jarvis jarvis > jarvis-pg-backup.sql

# Restore
cat jarvis-pg-backup.sql | docker exec -i jarvis-postgres psql -U jarvis jarvis
```

---

## VII. Future Enhancements

### Short-term (Next Sprint)

1. **Temporal Intelligence**:
   - Add `created_at`, `updated_at` filters to retrieval
   - "Show me recent insights about X" → filter by timestamp
   - Track knowledge evolution over time

2. **Cross-Document Links**:
   - Detect references between documents (citations, see-also)
   - Build document graph in Qdrant (via payload metadata)
   - "What other docs relate to this one?"

3. **Personalization**:
   - User-specific domain preferences (weight certain domains higher)
   - Query history for personalized expansions
   - "Continue previous conversation" via conversation_id

4. **Performance Optimization**:
   - Cache frequent query embeddings
   - Batch retrieval for multi-turn conversations
   - Async retrieval for web UI responsiveness

---

### Medium-term (Next Month)

1. **Graph Memory Layer**:
   - Neo4j integration for entity relationships
   - Extract entities from chunks (people, projects, concepts)
   - "How do these concepts relate?" → graph traversal

2. **Active Learning**:
   - User feedback on retrieval quality ("Was this helpful?")
   - Fine-tune retrieval weights based on feedback
   - Identify low-quality chunks for re-ingestion

3. **Multi-Modal Embeddings**:
   - Image embeddings (diagrams, screenshots)
   - Code embeddings (specialized model for code)
   - Audio/video transcription + embedding

4. **Federated Search**:
   - Search across Qdrant + web (Google, arXiv, GitHub)
   - Merge Qdrant results with web results
   - "Latest research on X" → web search, "JARVIS notes on X" → Qdrant

---

### Long-term (Next Quarter)

1. **Self-Improving Taxonomy**:
   - Automatically propose new domains based on LLM patterns
   - Merge similar domains (clustering analysis)
   - Taxonomy versioning and migration

2. **Collaborative Memory**:
   - Multi-user JARVIS instances share insights
   - Privacy-preserving federated learning
   - "What have other JARVIS instances learned about X?"

3. **Causal Memory**:
   - Track cause-effect relationships in knowledge
   - "Why did X lead to Y?" → causal chain retrieval
   - Intervention analysis ("What if we changed X?")

4. **Memory Consolidation**:
   - Periodic summarization of old chunks (compress)
   - Promote frequently retrieved chunks to "core memory"
   - Archive low-value chunks to cold storage

---

## VIII. Appendices

### Appendix A: Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Vector DB | Qdrant | Semantic search, chunk storage |
| Embeddings | sentence-transformers/all-mpnet-base-v2 | 768-dim vectors |
| LLM (classification) | Google Gemini 2.0 Flash | Domain classification, query expansion |
| LLM (QA) | OpenRouter (cost-first routing) | Answer generation |
| Relational DB | PostgreSQL | Conversations, messages, provenance |
| Cache | Redis | Session state, query cache |
| Orchestration | Docker Compose | Service management |
| CLI | Typer | Command-line interface |
| API | FastAPI | Web chat, MCP server |
| Logging | structlog | Structured logging |

---

### Appendix B: Key Metrics

| Metric | Current Value | Target | Notes |
|--------|--------------|--------|-------|
| Total Qdrant points | 43,715 | 50,000 | Steady growth |
| Domain taxonomy size | 166 domains | 180 | Add niche domains as needed |
| Heuristic keyword mappings | 881 | 1,000 | Expand to 75% hit rate |
| Heuristic hit rate | ~70% | 75% | Reduces LLM cost |
| Avg query latency (p95) | ~800ms | <1s | Includes LLM call |
| Enrichment coverage | ~35% | 50% | High-value docs only |
| Monthly LLM cost | ~$15 | <$25 | Classification + QA + enrichment |
| Collections | 6 | 8 | Add jarvis-playbooks, jarvis-code |

---

### Appendix C: Domain Taxonomy Summary

See [domain-taxonomy.md](domain-taxonomy.md) for full taxonomy.

**Top-level categories** (17):
1. jarvis (20 domains) - JARVIS system internals
2. science (30 domains) - Math, physics, chemistry, biology
3. network (22 domains) - Routing, telemetry, carrier systems
4. ai (15 domains) - LLMs, RAG, ML, computer vision
5. infra (12 domains) - Docker, Kubernetes, cloud
6. cyber (13 domains) - Security, PKI, SIEM, STIX
7. math (11 domains) - Calculus, geometry, transforms
8. dev (12 domains) - Languages, frameworks, databases
9. philosophy (7 domains) - Epistemology, ethics, logic
10. psychology (7 domains) - Cognitive, ADHD, neuroscience
11. enterprise (8 domains) - TOGAF, digital transformation, cloud platforms
12. finance (10 domains) - Banking, trading, risk, compliance
13. telecom (covered in network)
14. project (5 domains) - GenerativeDrive energy project
15. bmad (5 domains) - BMAD methodology
16. economics (4 domains) - Macro, micro, trade, energy
17. ntt_data (3 domains) - NTT DATA consulting projects

**Total**: 166 unique domains, 881 keyword heuristics

---

### Appendix D: Glossary

- **Chunk**: A semantically meaningful fragment of a document (1200-1500 chars), stored as a Qdrant point
- **Point**: Qdrant's term for a vector + metadata payload
- **Domain**: A semantic category from the taxonomy (e.g., `jarvis.memory.rag`)
- **Heuristic**: A fast, deterministic rule for classification (keyword → domain)
- **LLM Fallback**: Using Gemini to classify when heuristics miss
- **Document Profile**: Aggregated metadata for a document (majority domain, confidence, stats)
- **Enrichment**: LLM-generated metadata (summary, facts, tags, doc_type)
- **Windowing**: Sampling representative chunks from long documents
- **Majority Vote**: Determining document domain by most common chunk domain
- **RRF**: Reciprocal Rank Fusion, a method for combining ranked lists
- **Expanded Search**: Multi-query retrieval with fusion
- **Provenance**: Tracking which chunks/documents contributed to an answer
- **Collection**: A Qdrant namespace for grouping related points
- **Hybrid Search**: Combining semantic + keyword search with weighted sum

---

## Conclusion

The JARVIS Memory Architecture is a **living cognitive system** that:
- Organizes 43,715 knowledge atoms across 166 semantic domains
- Learns from iterations ("some work some not, but everything is important")
- Optimizes for cost and performance (heuristics → LLM fallback)
- Maintains dual-level intelligence (chunk + document)
- Supports multi-modal retrieval (semantic, keyword, hybrid, expanded)
- Tracks provenance for trust and analytics
- Evolves through enrichment and profiling

This architecture mirrors human memory: **not a static archive, but a dynamic network of meaning-linked building blocks, continuously refined through experience.**

The Memory Arches stand ready to support the next phase of JARVIS evolution - whether that's graph-based reasoning, multi-modal intelligence, or collaborative learning across instances.

*"Everything is important, what to do what to not."* ✨

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Authors**: Codex (foundation), Ariel (synthesis)
**Related Docs**:
- [domain-taxonomy.md](domain-taxonomy.md) - Complete domain taxonomy reference
- [jarvis-brain-status-2025-12-02.md](../jarvis-brain-status-2025-12-02.md) - Qdrant corpus status
- [jarvis-knowledge-pipeline.md](../jarvis-knowledge-pipeline.md) - Pipeline reference
- [architecture.md](../architecture.md) - JARVIS system architecture
