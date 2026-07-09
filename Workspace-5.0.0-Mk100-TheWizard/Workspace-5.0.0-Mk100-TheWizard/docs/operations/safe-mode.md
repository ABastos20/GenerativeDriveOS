# Safe Mode & Rollback Operations

**Status:** Provisional
**Last Updated:** 2025-12-08

## Safe Mode Defaults
By default, JARVIS operates with safety rails enabled:
- **Sandbox**: Tool execution is limited to specific directories.
- **Confirmation**: High-risk actions (file deletion, external API calls) require user confirmation unless explicitly bypassed (not recommended in production).
- **Read-Only Context**: Git operations are generally read-only unless specifically authorized for a task.

## Snapshot & Rollback
Currently, JARVIS relies on **Git** for state rollback of code and documentation.

### Code/Docs Rollback
To revert changes made by JARVIS:
```bash
git checkout .
git clean -fd
```

### Database Snapshot (Future)
*Planned for Epic 10 (Time-Decay Memory).*
Mechanisms to snapshot Qdrant and Postgres states before major autonomous updates.

## Emergency Stop
If `jarvis` acts unexpectedly:
1.  **Ctrl+C**: Terminates the CLI process immediately.
2.  **Docker Stop**: `docker compose down` kills all backend services.
3.  **Kill Switch**: Define `JARVIS_EMERGENCY_STOP=1` in `.env` to disable all autonomous loops (future implementation).
