# Health Checks & Diagnostics

**Status:** Stable
**Last Updated:** 2025-12-08

This document outlines how to verify the health of the JARVIS system, primarily using the built-in diagnostic tools.

## Automated Checks: `jarvis doctor`

The primary method for system verification is the `doctor` command.

```bash
jarvis doctor
```

### What it Checks
1.  **Docker Connectivity**: Verifies `qdrant`, `postgres`, and `redis` services are reachable.
2.  **Database Schemas**: Checks if Alembic migrations are applied.
3.  **Embedding Model**: Verifies `sentence-transformers` is loaded and functional.
4.  **Vector Store**: Checks if Qdrant collections exist and are accessible.
5.  **Workspace**: Verifies write permissions to `.jarvis/`.

## Manual Verification

### 1. API Health
Check the MCP server status (if running via Docker or stdio).
*   **Endpoint**: (Internal) Check logs for `MCP Server Initialized`.

### 2. Log Analysis
Logs are stored in `.jarvis/logs/`.
*   **Errors**: `grep ERROR .jarvis/logs/jarvis.log`
*   **Trace ID**: Look for `trace_id` in logs to correlate requests across components.

### 3. Recovery
If `doctor` reports issues:
1.  **Restart Services**: `docker compose restart`
2.  **Rebuild**: `docker compose up --build -d`
3.  **Clean State**: `jarvis memory reset` (Warning: Destructive)
