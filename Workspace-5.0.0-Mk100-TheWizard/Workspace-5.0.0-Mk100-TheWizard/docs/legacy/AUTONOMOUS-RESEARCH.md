# Jarvis Autonomous Research Mode

## What It Does
- Detects knowledge gaps (coverage, recency, coherence) on every query.
- Triggers web research (Gemini + MCP tools) when gaps exceed thresholds.
- Cross-references new findings, integrates updates, and records provenance.
- Logs rate/cost usage and makes research activity visible in UI and CLI analytics.

## Quick Start
- CLI: `jarvis query "latest qdrant benchmarks" --enable-research --coverage-threshold 0.6 --max-queries 5 --cost-cap 0.5`
- API: `POST /api/chat` with `enable_research: true` and optional `research_config` overrides.
- UI: toggle 🔬 Research in `/chat`, adjust settings (coverage threshold, max queries, cost cap), then send message.

## CLI Examples
```bash
# Enable research with defaults
jarvis query "What changed in Qdrant 1.15?" --enable-research

# Tighten coverage threshold and cap cost
jarvis query "Latest vector DB latency numbers" --enable-research --coverage-threshold 0.7 --cost-cap 0.40

# Reduce queries for quick checks
jarvis query "Recent RAG eval reports" --enable-research --max-queries 2

# Analytics summary (uses ResearchLog)
jarvis analytics research-summary --since 7d
```

## API Request/Response
```json
POST /api/chat
{
  "message": "What are the latest Qdrant performance benchmarks?",
  "enable_research": true,
  "research_config": {
    "coverage_threshold": 0.6,
    "max_queries": 5,
    "cost_cap_usd": 0.50
  }
}
```
Returns `metadata.gap_analysis` and `metadata.research_summary` with queries executed, sources collected, and confidence delta. Research logs feed `/dashboard/api/research-stats` and the UI history card.

## Settings
`config/settings.example.yaml` research block:
```yaml
research:
  enabled: false
  coverage_threshold: 0.6
  recency_threshold_days: 90
  coherence_threshold: 0.3
  min_queries: 2
  max_queries: 5
  cost_cap_usd: 0.5
  hourly_limit: 10
  redis_url: redis://jarvis-redis:6379/0  # optional; falls back to in-memory
```

## UI Tips
- 🔬 Research toggle + settings drawer (coverage, max queries, cost cap).
- Progress HUD with cancellable stages; partial research shows warning and retry.
- Gap analysis card, research summary card, researched sources marked with ✨ and provenance timeline.
- History panel: window/gap filters, charts, CSV export; swipe gestures on mobile.
- Accessibility: focus rings, reduced motion/high-contrast modes, SR announcements for research stages.

## Troubleshooting
- **429 Too Many Requests**: Research hourly limit reached. Lower `max_queries` or wait; check rate bar in UI.
- **402 Payment Required**: Cost cap hit. Raise `cost_cap_usd` cautiously or retry later.
- **Partial research**: HUD shows partial completion; use Retry last.
- **Insufficient context**: In strict mode, research may not trigger if no seed context; relax grounding or allow creative fallback.
- **Redis not reachable**: Limits degrade to in-memory; verify `redis://` and container `jarvis-redis` (`redis-cli ping`), clear with `docker exec jarvis-redis redis-cli FLUSHALL` (destructive).
- **MCP tools unavailable**: Fetch/browser calls are best-effort; ensure MCP server reachable or provide direct URLs in planner prompts.

## Notes
- Research logs: PostgreSQL `research_logs` + temporal chunk metadata; surfaced in `/dashboard/api/research-stats` and `jarvis analytics research-summary`.
- Behavior learning: multiple time-sensitive queries auto-enable research in the UI to keep context fresh.
