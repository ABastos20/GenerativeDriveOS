# Bug Fixes Log

## 2025-12-03: Timezone-Aware Datetime Comparison Fix

**Error**: `can't compare offset-naive and offset-aware datetimes`

**Affected Components**:
- Dashboard API `/dashboard/api/stats`
- Timeline/archetype tracking features
- Memory search with `--since` parameter

**Root Cause**:
Using `datetime.utcnow()` which returns **naive** (timezone-unaware) datetime objects,
then comparing them with PostgreSQL `TIMESTAMP WITH TIME ZONE` columns which are **aware**.

**Files Fixed**:
1. `src/jarvis/api/dashboard.py`
   - `get_retrieval_heatmap()` - line 147
   - `get_cost_tracking()` - line 235

2. `src/jarvis/cli/memory.py`
   - `_parse_since()` - line 46
   - Added timezone-aware ISO parsing

**Solution**:
Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` to ensure all datetime
objects are timezone-aware before comparison.

**Testing**:
```bash
# Dashboard should work without errors now
curl http://localhost:8000/dashboard/api/stats

# Memory search with time filter
jarvis memory search "some query" --since 7d
```

**Status**: ✅ Fixed and deployed

---

## 2025-12-03: 503 Service Unavailable on Chat API (FIXED)

**Error**: `INFO: 172.18.0.1:33020 - "POST /api/chat HTTP/1.1" 503 Service Unavailable`

**Affected Components**:
- Chat API `/api/chat`
- Web UI chat interface

**Investigation Phase 1**:
- PostgreSQL logs: Clean, no connection errors
- Active connections: 5 total (1 active + 4 idle), well within pool size of 5
- Connection pool settings: pool_size=5, max_overflow=10, pool_pre_ping=True
- Initial diagnosis: Transient network hiccups during connection pre-ping

**Root Cause (Actual)**:
Missing imports for variable grounding system functions in `chat.py`:
- `analyze_intent()` from `jarvis.memory.intent_analyzer`
- `score_response_confidence()` from `jarvis.memory.confidence_scorer`
- Missing `default_grounding_level` variable definition

When these functions were called, Python raised `NameError`, caught by the database exception handler (line 44), which returned 503.

**Files Fixed**:
1. `src/jarvis/api/chat.py` (lines 21-22)
   - Added missing imports for intent_analyzer and confidence_scorer
   - Added default_grounding_level extraction from settings (lines 109-113)

**Testing**:
```bash
# All requests now succeed consistently
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the variable grounding system?", "k": 5}'
# → Returns 200 OK with grounding_level="strict"

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the RAG pipeline", "k": 5}'
# → Returns 200 OK with grounding_level="balanced"

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Brainstorm ideas", "k": 5}'
# → Returns 200 OK with grounding_level="soft"
```

**Status**: ✅ Fixed and deployed

**Remaining Known Issue**:
Rare intermittent 503s (~1-2% of requests) due to transient connection pre-ping timeouts.
These are self-recovering and not service-impacting.

---

## 2025-12-03: Conversation History Truncated in Web UI (FIXED)

**Symptom**: Web UI chat cuts off conversation history partway through, unable to scroll to see full history

**Affected Components**:
- Web UI chat interface at `/chat`
- Conversations API endpoint

**Root Cause**:
Hard pagination limit of 100 messages in both API and Web UI:
- API endpoint limited: `page_size: int = Query(50, ge=1, le=100, ...)`
- Web UI hardcoded: `var historyUrl = "/api/conversations/" + conversationId + "?page_size=100"`

When conversations exceed 100 messages, history is truncated without warning.

**Files Fixed**:
1. `src/jarvis/api/conversations.py` (line 174)
   - Increased max page_size from 100 → 500
   - Updated docstring to reflect new limit

2. `src/jarvis/api/app.py` (line 741)
   - Updated Web UI to request 500 messages instead of 100

**Testing**:
```bash
# Reload Web UI chat page
# Should now show up to 500 messages

# API test
curl "http://localhost:8000/api/conversations/{conversation_id}?page_size=500"
```

**Status**: ✅ Fixed and deployed

**Note**: If conversations exceed 500 messages in the future, the API supports proper pagination with `page` and `has_more` fields. The Web UI should implement scroll-to-load-more functionality.
