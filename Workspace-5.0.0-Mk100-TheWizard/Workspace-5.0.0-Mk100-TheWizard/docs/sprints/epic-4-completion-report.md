# Epic 4 Completion Report: Council of Ricks & Memory Enhancements

**Date:** 2025-12-04
**Status:** Completed

## 1. Overview
This epic focused on establishing the "Council of Ricks" multi-agent system, enhancing the document ingestion pipeline, and fixing critical bugs in search and CLI tool execution.

## 2. Key Achievements

### 2.1. Memory & Ingestion Pipeline
*   **Hybrid Retrieval Architecture**: Implemented a robust hybrid search combining:
    *   **Semantic Search**: Qdrant dense vectors (chunks).
    *   **Keyword Search**: PostgreSQL full-text search on both **Conversation History** (`messages`) and **Ingested Documents** (`documents`).
*   **Full Document Storage**: Added a `Document` model in Postgres to store the complete text of ingested files, enabling "FULL DOCUMENT" retrieval and preventing data loss from chunking.
*   **Optimized Ingestion**:
    *   **PDF Handling**: Improved `PyPDF2` integration with per-page error handling and null-byte sanitization.
    *   **Domain Heuristics**: Integrated domain classification directly into the ingestion process (`ingest.py`), assigning `primary_domain` and `tags` immediately.
    *   **Chunking**: Increased default chunk size to 2000 chars for better context.

### 2.2. Search & Research
*   **Gemini Fixes**: Resolved empty responses by setting safety settings to `BLOCK_NONE`.
*   **Perplexity (Sonar) Fixes**:
    *   Set default model to `sonar`.
    *   Implemented `disable_search=True` to prevent unwanted web searches during simple queries.
*   **Research Planner**: Improved prompt engineering to generate concise, keyword-focused queries and avoid repeating the full user question.

### 2.3. CLI Tools & Execution
*   **Local CLI Fixes**:
    *   Fixed `codex` and `claude` execution by using correct positional arguments.
    *   Enhanced robustness with `CI=true` and `NO_COLOR=true` env vars to prevent interactive hangs.

## 3. Technical Implementation Details

### 3.1. Hybrid Search Logic
The `hybrid_search` function in `src/jarvis/memory/search.py` now orchestrates:
1.  `search_memory(query)`: Qdrant semantic search.
2.  `keyword_search(query)`: Postgres search on `messages`.
3.  `document_keyword_search(query)`: Postgres search on `documents` (using `ts_headline` for snippets).
Results are normalized and merged using a weighted score (default 0.7 semantic / 0.3 keyword).

### 3.2. Database Schema
*   **New Table**: `documents`
    *   `doc_key` (Unique ID, e.g., `file:///path/to/doc.pdf`)
    *   `content` (Full text)
    *   `metadata` (JSONB)
    *   `domain` (String)

## 4. Operational Guide

### 4.1. Initialization
Run the full pipeline initialization script:
```bash
./scripts/init_pipeline.sh
```
This will:
1.  Verify environment.
2.  Initialize Postgres tables and Qdrant collection.
3.  Setup cron jobs (including daily cataloging).

### 4.2. Ingestion
Ingest documents using the CLI:
```bash
jarvis memory ingest /path/to/folder_or_file
```
This automatically:
*   Chunks text for Qdrant.
*   Upserts full text to Postgres.
*   Applies domain heuristics.

### 4.3. Background Jobs
Cron jobs are installed in the container:
*   **Daily 1 AM**: `catalog_documents` (Refines domain classification).
*   **Daily 2 AM**: Domain snapshots.
*   **Weekly Sun 3 AM**: Keyword mining.

## 5. Future Work
*   **Sparse Vectors**: Consider adding `fastembed` or similar for Qdrant sparse vector support (currently using Postgres for keyword search as a robust alternative).
*   **UI Enhancements**: Visualize "Document" results distinct from "Message" results in the chat UI.
