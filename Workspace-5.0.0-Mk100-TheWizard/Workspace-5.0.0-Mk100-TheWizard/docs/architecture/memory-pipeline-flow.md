# JARVIS Memory Pipeline - Visual Flow

This document provides visual representations of the JARVIS memory architecture pipeline flows.

---

## 1. Complete Knowledge Flow (End-to-End)

```mermaid
graph TB
    subgraph "Stage 1: INGESTION"
        A[Raw Documents] -->|Parse| B{Document Type?}
        B -->|PDF| C[pdfplumber]
        B -->|Markdown| D[AST Parser]
        B -->|Text| E[Line Chunker]
        B -->|JSON| F[GPT Export Parser]
        B -->|Jupyter| G[Cell Parser]

        C --> H[Semantic Chunker]
        D --> H
        E --> H
        F --> H
        G --> H

        H -->|1200-1500 chars| I[Embedding Generator]
        I -->|all-mpnet-base-v2| J[768-dim Vectors]

        J --> K{Duplicate?}
        K -->|Hash exists| L[Skip]
        K -->|New hash| M[Qdrant Upsert]

        M --> N[(Qdrant Collections)]
    end

    subgraph "Stage 2: CATALOG"
        N --> O[Domain Classifier]
        O --> P{Heuristics Match?}
        P -->|Yes ~70%| Q[Keyword Map]
        P -->|No ~30%| R[LLM Classifier]

        Q --> S[Domain Assigned]
        R -->|Gemini 2.0 Flash| S

        S --> T[Update Qdrant Payload]
        T --> U[domain field set]
    end

    subgraph "Stage 3: PROFILE"
        U --> V[Group by source_file]
        V --> W[Count domain frequencies]
        W --> X{Majority Vote}
        X -->|>50% confidence| Y[Primary Domain]
        X -->|<50% confidence| Z[Flag for Review]

        Y --> AA[Update doc_primary_domain]
        Z --> AA
        AA --> AB[Document Profile Complete]
    end

    subgraph "Stage 4: ENRICHMENT"
        AB --> AC{High-value doc?}
        AC -->|Yes| AD[Sample Windows]
        AC -->|No| AE[Skip Enrichment]

        AD -->|Beginning, Middle, End| AF[LLM Enrichment]
        AF -->|Gemini 2.0 Flash| AG{Generate}

        AG --> AH[Summary]
        AG --> AI[Facts]
        AG --> AJ[Tags]
        AG --> AK[doc_type]

        AH --> AL[Update Qdrant Payload]
        AI --> AL
        AJ --> AL
        AK --> AL

        AL --> AM[Enriched Memory]
        AE --> AM
    end

    subgraph "RETRIEVAL LAYER"
        AM --> AN{Query Mode?}

        AN -->|Semantic| AO[Embed Query]
        AN -->|Keyword| AP[BM25 Search]
        AN -->|Hybrid| AQ[Both + Fusion]
        AN -->|Expanded| AR[Multi-Query + RRF]

        AO --> AS[Qdrant Search]
        AP --> AS
        AQ --> AT[Weighted Combine]
        AR --> AU[Generate Variations]

        AT --> AS
        AU --> AV[Retrieve All Queries]
        AV --> AW[RRF Fusion]
        AW --> AS

        AS --> AX[Top-K Results]
    end

    subgraph "LLM CONTEXT"
        AX --> AY[Build Context Window]
        AY --> AZ[System Prompt + Sources]
        AZ --> BA{LLM Provider?}

        BA -->|auto| BB[Cost-First Router]
        BA -->|specific| BC[Direct Provider]

        BB --> BD[OpenRouter]
        BB --> BE[Perplexity]
        BB --> BF[Local Ollama]
        BB --> BG[Direct API]

        BD --> BH[Generate Answer]
        BE --> BH
        BF --> BH
        BG --> BH
        BC --> BH

        BH --> BI[Response + Citations]
    end

    subgraph "PERSISTENCE"
        BI --> BJ[(PostgreSQL)]
        BJ --> BK[Conversations Table]
        BJ --> BL[Messages Table]

        BL --> BM[citation_provenance JSON]
        BM --> BN[Analytics Ready]
    end

    style A fill:#e1f5ff
    style N fill:#fff4e1
    style AM fill:#e8f5e9
    style BI fill:#f3e5f5
    style BN fill:#fce4ec
```

---

## 2. Domain Classification Decision Tree

```mermaid
graph TD
    A[Chunk Text + source_file] --> B{Direct Mapping?}

    B -->|Path match| C[Check DIRECT_DOMAIN_MAP]
    C -->|jarvis/memory/| D[domain: jarvis.memory]
    C -->|external/gpt-export/| E[domain: jarvis.conversations]
    C -->|GenerativeDrive/| F[domain: gd.generative_drive]

    D --> G[domain_source: heuristic]
    E --> G
    F --> G

    B -->|No path match| H{Keyword Match?}

    H -->|Scan text| I[Check 881 KEYWORD_MAP entries]
    I -->|council of ricks| J[domain: jarvis.agents]
    I -->|stix 2.1| K[domain: cyber.stix]
    I -->|adhd| L[domain: psychology.adhd]

    J --> G
    K --> G
    L --> G

    H -->|No keywords| M[LLM Fallback Required]
    M --> N[Windowing Strategy]

    N --> O{Document Length?}
    O -->|Short <3 chunks| P[Use full text]
    O -->|Long >3 chunks| Q[Sample 3 windows]

    Q --> R[Beginning chunk]
    Q --> S[Middle chunk]
    Q --> T[End chunk]

    R --> U[Concatenate with separators]
    S --> U
    T --> U
    P --> U

    U --> V[Gemini 2.0 Flash Classify]
    V --> W{Valid Domain?}

    W -->|In DOMAIN_LIST| X[Assign domain]
    W -->|Not in list| Y[Log error, assign 'unknown']

    X --> Z[domain_source: llm]
    Y --> Z

    G --> AA[Domain Classification Complete]
    Z --> AA

    style A fill:#e3f2fd
    style G fill:#c8e6c9
    style Z fill:#fff9c4
    style AA fill:#f8bbd0
```

---

## 3. Document Profiling (Majority Vote)

```mermaid
graph TB
    A[Source Document: example.md] --> B[Retrieve All Chunks]

    B --> C[Chunk 1: jarvis.memory.rag]
    B --> D[Chunk 2: jarvis.memory.rag]
    B --> E[Chunk 3: jarvis.memory.rag]
    B --> F[Chunk 4: jarvis.memory.rag]
    B --> G[Chunk 5: jarvis.memory.rag]
    B --> H[Chunk 6: jarvis.memory.rag]
    B --> I[Chunk 7: jarvis.memory.rag]
    B --> J[Chunk 8: ai.embeddings]
    B --> K[Chunk 9: ai.embeddings]
    B --> L[Chunk 10: dev.python]

    C --> M[Count Domain Frequencies]
    D --> M
    E --> M
    F --> M
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M

    M --> N{Domain Counts}
    N --> O[jarvis.memory.rag: 7]
    N --> P[ai.embeddings: 2]
    N --> Q[dev.python: 1]

    O --> R{Majority Vote}
    P --> R
    Q --> R

    R --> S[Primary: jarvis.memory.rag]
    R --> T[Confidence: 70%]

    S --> U{Confidence Check}
    U -->|>= 50%| V[Accept Profile]
    U -->|< 50%| W[Flag for Manual Review]

    V --> X[Update All 10 Chunks]
    W --> Y[Log Warning]

    X --> Z[doc_primary_domain: jarvis.memory.rag]
    Y --> Z

    Z --> AA[Document Profile Complete]

    style A fill:#e1f5ff
    style M fill:#fff9c4
    style S fill:#c8e6c9
    style AA fill:#f8bbd0
```

---

## 4. Retrieval Strategy Comparison

```mermaid
graph LR
    subgraph "Semantic Search"
        A1[Query Text] --> A2[Embed with all-mpnet-base-v2]
        A2 --> A3[Qdrant Cosine Similarity]
        A3 --> A4[Top-K by Vector Distance]
        A4 --> A5[Results: Conceptual Matches]
    end

    subgraph "Keyword Search"
        B1[Query Text] --> B2[Tokenize Keywords]
        B2 --> B3[Qdrant BM25 Search]
        B3 --> B4[Top-K by BM25 Score]
        B4 --> B5[Results: Exact Matches]
    end

    subgraph "Hybrid Search"
        C1[Query Text] --> C2[Run Semantic Search]
        C1 --> C3[Run Keyword Search]
        C2 --> C4[Normalize Scores 0-1]
        C3 --> C4
        C4 --> C5[Weighted Combine]
        C5 --> C6{weight = 0.7}
        C6 --> C7[0.7 * semantic + 0.3 * keyword]
        C7 --> C8[Top-K by Combined Score]
        C8 --> C9[Results: Best of Both]
    end

    subgraph "Expanded Search"
        D1[Query Text] --> D2[LLM Query Expansion]
        D2 --> D3[Generate 3-5 Variations]
        D3 --> D4[Query 1: Original]
        D3 --> D5[Query 2: Rephrase]
        D3 --> D6[Query 3: Alternative Perspective]
        D4 --> D7[Semantic Search Q1]
        D5 --> D8[Semantic Search Q2]
        D6 --> D9[Semantic Search Q3]
        D7 --> D10[RRF Fusion]
        D8 --> D10
        D9 --> D10
        D10 --> D11[Top-K by RRF Score]
        D11 --> D12[Results: Diverse Perspectives]
    end

    style A5 fill:#e3f2fd
    style B5 fill:#fff9c4
    style C9 fill:#c8e6c9
    style D12 fill:#f8bbd0
```

---

## 5. Cognitive Patterns (Decision Flows)

### Pattern 1: Heuristic → LLM Fallback

```mermaid
graph TD
    A[Classification Task] --> B{Try Heuristics}
    B -->|Hit ~70%| C[Fast Path: Instant Result]
    B -->|Miss ~30%| D[Slow Path: LLM Call]

    C --> E[Cost: $0]
    C --> F[Latency: <1ms]

    D --> G[Cost: ~$0.00001]
    D --> H[Latency: ~200ms]

    E --> I[Total System Cost: Low]
    F --> I
    G --> I
    H --> I

    I --> J{Monitor Hit Rate}
    J -->|< 65%| K[Expand Heuristics]
    J -->|>= 65%| L[Maintain Balance]

    K --> M[Mine LLM Results for Keywords]
    M --> N[Add to Keyword Map]
    N --> B

    style C fill:#c8e6c9
    style D fill:#ffecb3
    style I fill:#e1f5ff
```

### Pattern 2: Windowing Strategy

```mermaid
graph TD
    A[Long Document] --> B{Chunk Count?}
    B -->|<= 3 chunks| C[Use Full Text]
    B -->|> 3 chunks| D[Windowing Strategy]

    D --> E[Sample Window 1: Beginning]
    D --> F[Sample Window 2: Middle]
    D --> G[Sample Window 3: End]

    E --> H[Why: Context, Introduction]
    F --> I[Why: Core Content]
    G --> J[Why: Conclusions, Summary]

    H --> K[Concatenate with Separators]
    I --> K
    J --> K

    K --> L[Total: 3600-4500 chars]
    C --> M[Total: Variable, max 4500]

    L --> N{Within MAX_TOKENS?}
    M --> N

    N -->|Yes| O[LLM Call]
    N -->|No| P[ERROR: Document Too Large]

    O --> Q[Result: Accurate, Grounded]

    style D fill:#fff9c4
    style K fill:#c8e6c9
    style Q fill:#f8bbd0
```

### Pattern 3: Dual-Level Classification

```mermaid
graph TB
    subgraph "Chunk Level (Micro)"
        A1[Chunk 1] --> A2[domain: jarvis.memory.rag]
        B1[Chunk 2] --> B2[domain: jarvis.memory.rag]
        C1[Chunk 3] --> C2[domain: ai.embeddings]
    end

    subgraph "Document Level (Macro)"
        A2 --> D[Majority Vote]
        B2 --> D
        C2 --> D
        D --> E[doc_primary_domain: jarvis.memory.rag]
    end

    subgraph "Retrieval Uses Both"
        F[Query: Find RAG docs] --> G{Filter Level?}
        G -->|Chunk-level| H[domain = jarvis.memory.rag]
        G -->|Doc-level| I[doc_primary_domain = jarvis.memory.rag]

        H --> J[Precise: Specific RAG chunks]
        I --> K[Broad: Documents about RAG]
    end

    subgraph "Analytics Uses Both"
        E --> L{Question Type?}
        L -->|Chunk distribution| M[What topics in doc?]
        L -->|Document classification| N[What is doc about?]

        M --> O[domain counts per doc]
        N --> P[doc_primary_domain label]
    end

    style A2 fill:#e3f2fd
    style E fill:#c8e6c9
    style J fill:#fff9c4
    style K fill:#ffecb3
```

---

## 6. Memory Architecture Layers

```mermaid
graph TB
    subgraph "Layer 1: Physical Storage"
        A[(Qdrant)]
        B[(PostgreSQL)]
        C[(Redis)]

        A -->|Vectors + Metadata| D[43,715 Points]
        B -->|Conversations| E[Chat History]
        C -->|Cache| F[Session State]
    end

    subgraph "Layer 2: Domain Framework"
        G[Domain Taxonomy]
        H[Heuristic Rules]
        I[LLM Classifiers]

        G -->|166 Domains| J[Classification Schema]
        H -->|881 Keywords| J
        I -->|Gemini 2.0| J
    end

    subgraph "Layer 3: Knowledge Pipeline"
        K[Ingestion]
        L[Cataloging]
        M[Profiling]
        N[Enrichment]

        K --> L --> M --> N
    end

    subgraph "Layer 4: Retrieval Engine"
        O[Semantic]
        P[Keyword]
        Q[Hybrid]
        R[Expanded]

        O --> S[Multi-Modal Retrieval]
        P --> S
        Q --> S
        R --> S
    end

    subgraph "Layer 5: LLM Integration"
        T[Provider Router]
        U[Context Builder]
        V[Response Generator]

        T --> W[Cost-Optimized Routing]
        U --> X[Provenance Tracking]
        V --> Y[Citation-Rich Answers]
    end

    subgraph "Layer 6: Application Layer"
        Z[CLI]
        AA[Web Chat]
        AB[MCP Server]
        AC[API]
    end

    D --> K
    J --> L
    S --> U
    W --> V
    Y --> Z
    Y --> AA
    Y --> AB
    Y --> AC

    style D fill:#e3f2fd
    style J fill:#fff9c4
    style S fill:#c8e6c9
    style Y fill:#f8bbd0
```

---

## 7. Iteration Evolution Timeline

```mermaid
gantt
    title JARVIS Memory Architecture - Evolution Timeline
    dateFormat  YYYY-MM-DD
    section Iteration 1
    Naive RAG (Fixed chunking, semantic only)           :done, i1, 2024-01-01, 90d
    section Iteration 2
    Semantic Chunking + Collections                     :done, i2, 2024-04-01, 60d
    section Iteration 3
    Domain Taxonomy + Heuristics (20 domains)           :done, i3, 2024-11-01, 20d
    section Iteration 4
    Comprehensive Taxonomy (166 domains)                :done, i4, 2024-12-01, 5d
    section Iteration 5
    Document Profiling + Enrichment                     :done, i5, 2024-12-07, 7d
    section Iteration 6
    Multi-Modal Retrieval (Hybrid, Expanded)            :active, i6, 2024-12-15, 10d
    section Future
    Graph Memory Layer                                  :crit, f1, 2025-01-01, 30d
    Active Learning + Feedback                          :crit, f2, 2025-02-01, 30d
    Multi-Modal Embeddings (Image, Code, Audio)         :crit, f3, 2025-03-01, 30d
```

---

## 8. Cost vs. Quality Trade-offs

```mermaid
graph LR
    subgraph "Classification Strategy"
        A1[100% Heuristic] -->|Cost: $0| A2[Quality: 70%]
        B1[100% LLM] -->|Cost: $$$| B2[Quality: 95%]
        C1[Hybrid 70/30] -->|Cost: $| C2[Quality: 92%]
    end

    subgraph "Retrieval Strategy"
        D1[Semantic Only] -->|Latency: 200ms| D2[Recall: 75%]
        E1[Hybrid] -->|Latency: 400ms| E2[Recall: 85%]
        F1[Expanded x3] -->|Latency: 1200ms| F2[Recall: 95%]
    end

    subgraph "Enrichment Strategy"
        G1[No Enrichment] -->|Cost: $0| G2[Discovery: 60%]
        H1[Selective 35%] -->|Cost: $| H2[Discovery: 85%]
        I1[Full 100%] -->|Cost: $$$| I2[Discovery: 90%]
    end

    subgraph "Current Sweet Spot"
        C1 -.-> J[Classification: Hybrid]
        E1 -.-> K[Retrieval: Hybrid Default]
        H1 -.-> L[Enrichment: Selective]

        J --> M[Total Cost: ~$15/month]
        K --> M
        L --> M

        M --> N[Quality Score: 87%]
    end

    style C2 fill:#c8e6c9
    style E2 fill:#c8e6c9
    style H2 fill:#c8e6c9
    style N fill:#f8bbd0
```

---

## 9. Data Flow: Query to Answer

```mermaid
sequenceDiagram
    participant User
    participant CLI/API
    participant Retriever
    participant Qdrant
    participant LLM Router
    participant Gemini
    participant PostgreSQL

    User->>CLI/API: "How does JARVIS memory work?"
    CLI/API->>CLI/API: Load settings (retriever, k, weight)
    CLI/API->>Retriever: search_memory(query, k=10, hybrid)

    Retriever->>Retriever: Embed query (all-mpnet-base-v2)
    Retriever->>Qdrant: Semantic search (vector similarity)
    Qdrant-->>Retriever: Results A (10 chunks)

    Retriever->>Qdrant: Keyword search (BM25)
    Qdrant-->>Retriever: Results B (10 chunks)

    Retriever->>Retriever: Normalize scores [0,1]
    Retriever->>Retriever: Combine: 0.7*A + 0.3*B
    Retriever->>Retriever: Sort by combined score
    Retriever-->>CLI/API: Top 10 fused results

    CLI/API->>CLI/API: Build context (system + user + sources)
    CLI/API->>LLM Router: call_llm(prompt, provider="auto")

    LLM Router->>LLM Router: Cost-first routing
    LLM Router->>Gemini: OpenRouter → Gemini 2.0 Flash (free)
    Gemini-->>LLM Router: Answer + token count
    LLM Router-->>CLI/API: Response + metadata

    CLI/API->>CLI/API: Format sources (provenance)
    CLI/API->>PostgreSQL: Save conversation + message + citations
    PostgreSQL-->>CLI/API: Saved

    CLI/API-->>User: Answer + Sources

    Note over User,PostgreSQL: Total latency: ~800ms (p95)
    Note over LLM Router,Gemini: Cost: ~$0.00 (free tier)
```

---

## 10. Health Check Flow

```mermaid
graph TD
    A[Health Check Triggered] --> B{Check Qdrant}
    B -->|Success| C[Ping /collections]
    B -->|Fail| D[Alert: Qdrant Down]

    C --> E{Check Point Counts}
    E -->|Expected ~43,715| F[Check PostgreSQL]
    E -->|Deviation >10%| G[Alert: Data Loss?]

    F --> H{Check Connections}
    H -->|Success| I[Query conversations table]
    H -->|Fail| J[Alert: PG Down]

    I --> K{Check Redis}
    K -->|Success| L[Ping cache]
    K -->|Fail| M[Alert: Redis Down]

    L --> N{Check Domain Stats}
    N --> O[Heuristic hit rate]
    O -->|>= 65%| P[Check Enrichment]
    O -->|< 65%| Q[Alert: Heuristics Degraded]

    P --> R{Enrichment Coverage}
    R -->|30-40%| S[Check Query Latency]
    R -->|< 20% or > 60%| T[Warning: Enrichment Off-Target]

    S --> U{p95 Latency}
    U -->|<= 1s| V[All Systems Healthy]
    U -->|> 1s| W[Warning: Slow Queries]

    V --> X[Return Status: OK]

    style V fill:#c8e6c9
    style X fill:#f8bbd0
    style D fill:#ffcdd2
    style G fill:#ffcdd2
    style J fill:#ffcdd2
    style M fill:#ffcdd2
    style Q fill:#fff9c4
    style T fill:#fff9c4
    style W fill:#fff9c4
```

---

## Summary

These visual flows complement the [jarvis-memory-architecture.md](jarvis-memory-architecture.md) document by showing:

1. **Complete Knowledge Flow** - How data moves from raw docs to answers
2. **Domain Classification** - Decision tree for heuristic vs LLM
3. **Document Profiling** - Majority vote visualization
4. **Retrieval Strategies** - Four modes compared
5. **Cognitive Patterns** - How JARVIS thinks (heuristics, windowing, dual-level)
6. **Architecture Layers** - 6-layer stack
7. **Evolution Timeline** - 6 iterations over 12 months
8. **Cost vs Quality** - Trade-off analysis
9. **Query to Answer** - Sequence diagram
10. **Health Checks** - Monitoring flow

Together, these visualizations make the "building blocks pointing to something" concept tangible - showing how 43,715 knowledge atoms flow through cognitive patterns to produce intelligent, citation-backed answers. ✨

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Related Docs**:
- [jarvis-memory-architecture.md](jarvis-memory-architecture.md) - Complete architecture reference
- [domain-taxonomy.md](domain-taxonomy.md) - Domain classification framework
