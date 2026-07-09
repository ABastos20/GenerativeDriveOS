# Domain Filtering & API Improvements

## Overview
This document summarizes the domain filtering enhancements and new API endpoint added post-Epic 4.

## Changes

### 1. Unified Domain Format Handling
- Domain names are now consistently hyphenated (e.g., `jarvis-conversations` instead of `jarvis.conversations`)
- This ensures uniform filtering across CLI, API, and UI components

### 2. Post-Filtering for Domain Leakage Prevention
- Added domain post-filtering in search results to prevent cross-domain data leakage
- Ensures strict compliance when a domain filter is specified

### 3. New `/api/memory/domains` Endpoint
- **GET /api/memory/domains**: Returns a list of all unique domains in the knowledge base
- Used by the UI to populate domain filter dropdowns
- Response format:
  ```json
  {
    "domains": ["jarvis-conversations", "md", "pdf", ...]
  }
  ```

### 4. UI Domain Selector
- Replaced cluttered domain pills with a clean dropdown selector
- Auto-populates from the `/api/memory/domains` endpoint

## Related Files
- `src/jarvis/api/memory.py` - Domains endpoint
- `src/jarvis/memory/search.py` - Domain post-filtering
- `src/jarvis/api/app.py` - UI domain selector
- `src/jarvis/memory/ingest.py` - Domain normalization during ingestion
