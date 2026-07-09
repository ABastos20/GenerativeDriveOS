# Epic 5: Provider Registry & Cost Management - Planning Document

**Status**: Backlog → Planning
**Created**: 2025-12-03
**Dependencies**: Epic 4 Complete (✅)
**PRD Reference**: FR3.1-FR3.3 (Multi-LLM Routing & Cost Optimization)

---

## Executive Summary

Epic 5 implements intelligent LLM provider management with cost-first routing. The system maximizes free-tier usage across multiple providers (OpenRouter, Together AI, Google AI, etc.) before touching paid subscriptions, using "run until depleted, switch" strategy with real-time usage tracking and automated fallback.

**Philosophy**: "Zero Manual Cost Management" - The user should never think about API quotas or costs. JARVIS handles provider rotation, quota tracking, and cost optimization autonomously.

---

## Current State Assessment

### What's Already Built (Epic 1-4)

#### ✅ Provider Infrastructure (Partial)
- **File**: [src/jarvis/llm/providers.py](../../src/jarvis/llm/providers.py)
- **Providers Implemented**:
  - OpenRouterProvider (free tier: 50 req/day per model)
  - PerplexityProvider (cheap: ~$0.001/req)
  - GoogleAIProvider (Gemini 2.5 Pro with Search grounding)
  - AnthropicProvider (Claude)
  - OpenAIProvider (GPT models)
  - LocalCLIProvider (wrapper for authenticated CLIs)
- **Router**: ProviderRouter with fallback chain (auto mode)
- **Response Format**: LLMResponse with content, provider, model, tokens, cost_usd

#### ✅ Basic Usage Logging (Partial)
- **File**: [src/jarvis/llm/client.py](../../src/jarvis/llm/client.py#L147)
- **Function**: `_log_llm_usage()` logs every LLM call to PostgreSQL
- **Database Models**: [src/jarvis/database/models.py](../../src/jarvis/database/models.py)
  - `LLMProvider` table (name, type, priority, tokens_used, is_active)
  - `LLMUsageLog` table (provider_id, message_id, model, tokens_input, tokens_output, cost_usd, timestamp)
- **Logging**: Structured logging via structlog with provider, model, cost per call

#### ✅ Configuration System
- **File**: [src/jarvis/config/settings.py](../../src/jarvis/config/settings.py)
- **ProviderConfig**: name, type, priority, model, api_key_env
- **Settings YAML**: [config/settings.example.yaml](../../config/settings.example.yaml#L37)
  - Provider list with priorities defined
  - Research mode provider configuration (Epic 4)

#### ⚠️ Gaps Identified for Epic 5

1. **No Real-Time Quota Tracking**
   - Current: Cost calculated post-facto from token usage
   - Needed: API-driven quota checking before each call
   - Example: OpenRouter returns quota remaining in headers

2. **No Provider Priority Rules**
   - Current: Hardcoded fallback chain in ProviderRouter
   - Needed: Database-driven priority system with dynamic updates
   - Example: "Use free tiers first, paid only when depleted"

3. **No Depletion Detection**
   - Current: No automatic provider switching on quota exceeded
   - Needed: Catch 429/quota errors and rotate to next provider
   - Example: OpenRouter daily limit → switch to Together AI

4. **No Cost Reporting**
   - Current: Usage logged to DB but no aggregation/reporting
   - Needed: CLI commands and API endpoints for cost analysis
   - Example: `jarvis costs --month 2025-12`

5. **No Provider Health Monitoring**
   - Current: Providers fail silently and retry with same provider
   - Needed: Circuit breaker pattern, provider health checks
   - Example: If provider fails 3x in 5min, mark as unhealthy

---

## Epic 5 Stories Breakdown

### Story 5.1: Provider Registry & Priority Rules

**Objective**: Database-driven provider registry with configurable priority rules and quota limits.

**Acceptance Criteria**:
- [ ] Provider configuration stored in database (not just YAML)
- [ ] Priority rules: free_tier (priority 1-10), paid (priority 100+)
- [ ] Per-provider quota configuration (daily/monthly limits)
- [ ] Provider enable/disable toggle
- [ ] Migration script to seed database from settings.yaml
- [ ] API endpoints: `GET /api/providers`, `PUT /api/providers/{id}`

**Technical Design**:
```python
# Database schema enhancement
class LLMProvider:
    id: int
    name: str  # "openrouter", "gemini", "perplexity"
    type: str  # "free_tier", "paid"
    priority: int  # Lower = higher priority (1 = use first)
    model: str  # Default model for this provider
    api_key_env: str  # Environment variable name
    is_active: bool  # Enable/disable provider

    # NEW: Quota tracking fields
    quota_type: str  # "daily", "monthly", "unlimited"
    quota_limit: int  # Max requests/tokens per period
    quota_used: int  # Current usage in period
    quota_reset_at: datetime  # When quota resets

    # NEW: Health monitoring
    health_status: str  # "healthy", "degraded", "unhealthy"
    last_success_at: datetime
    last_failure_at: datetime
    consecutive_failures: int
```

**Files to Create/Modify**:
- `alembic/versions/20251203_add_provider_quotas.py` - Migration
- `src/jarvis/database/models.py` - Update LLMProvider model
- `src/jarvis/api/providers.py` - New API endpoints
- `src/jarvis/llm/provider_registry.py` - New registry service

**References**:
- Current LLMProvider model: [models.py#L91](../../src/jarvis/database/models.py#L91)
- Settings provider config: [settings.py#L14](../../src/jarvis/config/settings.py#L14)

---

### Story 5.2: Usage Tracking & Cost Ledger

**Objective**: Comprehensive usage tracking with per-provider cost attribution and historical analysis.

**Acceptance Criteria**:
- [ ] Every LLM call logs: provider, model, tokens, cost, timestamp, success/failure
- [ ] Cost calculation using provider-specific pricing tables
- [ ] Aggregation queries: costs by day/week/month, costs by provider
- [ ] Cost attribution: link LLM calls to conversations/messages for traceability
- [ ] Database indexes for efficient time-range queries
- [ ] Pricing table updates via config or API (for when provider prices change)

**Technical Design**:
```python
# Enhanced usage log (already exists, needs cost attribution)
class LLMUsageLog:
    id: int
    provider_id: int  # FK to LLMProvider
    conversation_id: UUID  # NEW: Conversation attribution
    message_id: UUID  # Message attribution (optional)

    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal  # Calculated from pricing table

    status: str  # NEW: "success", "rate_limited", "quota_exceeded", "error"
    error_message: str  # NEW: Error details if failed

    created_at: datetime

# NEW: Provider pricing table
class LLMProviderPricing:
    id: int
    provider_id: int
    model: str
    input_price_per_1m: Decimal  # Cost per 1M input tokens
    output_price_per_1m: Decimal  # Cost per 1M output tokens
    effective_from: datetime
    effective_until: datetime  # NULL for current pricing
```

**Aggregation Queries**:
```sql
-- Daily cost by provider
SELECT
    p.name as provider,
    DATE(created_at) as date,
    SUM(cost_usd) as total_cost,
    COUNT(*) as call_count
FROM llm_usage_logs l
JOIN llm_providers p ON l.provider_id = p.id
WHERE created_at >= '2025-12-01'
GROUP BY p.name, DATE(created_at)
ORDER BY date DESC, total_cost DESC;

-- Monthly total
SELECT
    DATE_TRUNC('month', created_at) as month,
    SUM(cost_usd) as total_cost
FROM llm_usage_logs
GROUP BY month;
```

**Files to Create/Modify**:
- `alembic/versions/20251203_add_cost_attribution.py` - Migration
- `src/jarvis/database/models.py` - Update LLMUsageLog, add LLMProviderPricing
- `src/jarvis/llm/cost_calculator.py` - New cost calculation service
- `src/jarvis/api/analytics.py` - Cost analytics endpoints

**References**:
- Current usage logging: [client.py#L147](../../src/jarvis/llm/client.py#L147)
- LLMUsageLog model: [models.py#L117](../../src/jarvis/database/models.py#L117)

---

### Story 5.3: Free-Tier Depletion Logic

**Objective**: Automatic provider rotation when quotas exceeded, maximizing free tier usage.

**Acceptance Criteria**:
- [ ] Detect quota exceeded errors (429 status, quota headers)
- [ ] Automatically rotate to next available provider by priority
- [ ] Update provider quota_used after each successful call
- [ ] Reset quota counters when quota_reset_at reached
- [ ] Circuit breaker: Temporarily disable provider after N consecutive failures
- [ ] Fallback chain: free tier → paid tier → error with clear message
- [ ] Logging: Provider rotation events with reason

**Technical Design**:
```python
class SmartProviderRouter:
    """Cost-first LLM provider router with automatic fallback."""

    def __init__(self):
        self.registry = ProviderRegistry()  # Database-backed
        self.circuit_breakers = {}  # provider_name -> CircuitBreaker

    def call_with_fallback(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = 4000,
        prefer_free: bool = True,
    ) -> LLMResponse:
        """Call LLM with automatic provider fallback on quota/error."""

        # Get providers in priority order (free tier first if prefer_free)
        providers = self.registry.get_available_providers(prefer_free=prefer_free)

        last_error = None
        for provider_config in providers:
            # Skip if circuit breaker is open
            if self._is_circuit_open(provider_config.name):
                logger.warning("circuit_breaker_open", provider=provider_config.name)
                continue

            # Check quota before attempting call
            if not self._has_quota_available(provider_config):
                logger.info("quota_depleted", provider=provider_config.name)
                continue

            try:
                # Attempt call
                provider = self._get_provider_instance(provider_config)
                response = provider.call(prompt, system, max_tokens)

                # Update quota usage
                self._update_quota_usage(provider_config, response)

                # Record success, reset circuit breaker
                self._record_success(provider_config)

                return response

            except QuotaExceededError as exc:
                # Provider hit quota mid-call, mark as depleted
                self._mark_quota_depleted(provider_config)
                logger.warning("quota_exceeded", provider=provider_config.name, error=str(exc))
                last_error = exc
                continue

            except RateLimitError as exc:
                # Temporary rate limit, try next provider
                logger.warning("rate_limited", provider=provider_config.name, error=str(exc))
                last_error = exc
                continue

            except Exception as exc:
                # Record failure, possibly open circuit breaker
                self._record_failure(provider_config, exc)
                logger.error("provider_failed", provider=provider_config.name, error=str(exc))
                last_error = exc
                continue

        # All providers exhausted
        raise AllProvidersExhaustedError(
            f"All LLM providers depleted or unavailable. Last error: {last_error}"
        )

    def _has_quota_available(self, provider: ProviderConfig) -> bool:
        """Check if provider has quota remaining."""
        if provider.quota_type == "unlimited":
            return True

        # Reset quota if reset time passed
        if provider.quota_reset_at and provider.quota_reset_at <= datetime.utcnow():
            self.registry.reset_quota(provider.id)
            return True

        return provider.quota_used < provider.quota_limit

    def _is_circuit_open(self, provider_name: str) -> bool:
        """Check if circuit breaker is open for this provider."""
        breaker = self.circuit_breakers.get(provider_name)
        if not breaker:
            return False
        return breaker.is_open()

    def _record_failure(self, provider: ProviderConfig, error: Exception):
        """Record provider failure, potentially opening circuit breaker."""
        self.registry.record_failure(provider.id, str(error))

        # Open circuit breaker after 3 consecutive failures
        if provider.consecutive_failures >= 3:
            self._open_circuit(provider.name)
```

**Error Classes**:
```python
class QuotaExceededError(Exception):
    """Provider quota exceeded (daily/monthly limit)."""
    pass

class RateLimitError(Exception):
    """Temporary rate limit, retry with different provider."""
    pass

class AllProvidersExhaustedError(Exception):
    """All providers depleted or unavailable."""
    pass
```

**Files to Create/Modify**:
- `src/jarvis/llm/smart_router.py` - New smart router with fallback
- `src/jarvis/llm/circuit_breaker.py` - Circuit breaker implementation
- `src/jarvis/llm/exceptions.py` - New exception classes
- `src/jarvis/llm/client.py` - Update call_llm() to use SmartProviderRouter

**References**:
- Current router: [providers.py#L492](../../src/jarvis/llm/providers.py#L492)
- Provider list: [client.py#L258](../../src/jarvis/llm/client.py#L258)

---

### Story 5.4: Cost Reporting CLI & API

**Objective**: User-facing cost reporting via CLI commands and dashboard API endpoints.

**Acceptance Criteria**:
- [ ] CLI command: `jarvis costs --today` (today's costs)
- [ ] CLI command: `jarvis costs --month 2025-12` (monthly costs)
- [ ] CLI command: `jarvis costs --provider gemini` (per-provider breakdown)
- [ ] API endpoint: `GET /api/analytics/costs?period=month&year=2025&month=12`
- [ ] API endpoint: `GET /api/analytics/costs/providers` (per-provider totals)
- [ ] Dashboard widget: Monthly cost chart
- [ ] Dashboard widget: Provider usage pie chart
- [ ] Export: CSV download of usage logs

**CLI Output Format**:
```bash
$ jarvis costs --month 2025-12

JARVIS Cost Report - December 2025
═══════════════════════════════════════════════════════

Provider Breakdown:
┌─────────────────┬───────────┬────────┬────────────┐
│ Provider        │ Calls     │ Tokens │ Cost (USD) │
├─────────────────┼───────────┼────────┼────────────┤
│ OpenRouter      │ 1,247     │ 89.2K  │ $0.00      │
│ Together AI     │ 563       │ 45.1K  │ $0.00      │
│ Gemini          │ 89        │ 12.3K  │ $0.34      │
│ Perplexity      │ 12        │ 3.5K   │ $0.02      │
└─────────────────┴───────────┴────────┴────────────┘

Daily Trend:
Dec 01: ████████░░ $0.02 (823 calls)
Dec 02: ██████████ $0.04 (1,245 calls)
Dec 03: ███████░░░ $0.01 (543 calls)

Total: $0.36 across 1,911 calls (150.1K tokens)
Free tier usage: 94.8% | Paid usage: 5.2%

$ jarvis costs --provider gemini

Gemini Cost Breakdown
═════════════════════════════════════════════

Model Usage:
- gemini-2.5-pro: 89 calls, 12.3K tokens, $0.34

Recent Calls:
2025-12-03 23:45 | Research query | 1,234 tokens | $0.004
2025-12-03 23:42 | Web search     | 567 tokens   | $0.002
2025-12-03 23:40 | Content fetch  | 890 tokens   | $0.003
```

**API Response Format**:
```json
{
  "period": "month",
  "year": 2025,
  "month": 12,
  "total_cost_usd": 0.36,
  "total_calls": 1911,
  "total_tokens": 150100,
  "free_tier_percentage": 94.8,
  "providers": [
    {
      "name": "openrouter",
      "calls": 1247,
      "tokens": 89200,
      "cost_usd": 0.00,
      "models": ["google/gemini-2.0-flash-exp:free"]
    },
    {
      "name": "gemini",
      "calls": 89,
      "tokens": 12300,
      "cost_usd": 0.34,
      "models": ["gemini-2.5-pro"]
    }
  ],
  "daily_breakdown": [
    {"date": "2025-12-01", "cost_usd": 0.02, "calls": 823},
    {"date": "2025-12-02", "cost_usd": 0.04, "calls": 1245}
  ]
}
```

**Files to Create/Modify**:
- `src/jarvis/cli/costs.py` - New CLI cost reporting commands
- `src/jarvis/api/analytics.py` - Cost analytics API endpoints
- `src/jarvis/api/dashboard.py` - Add cost widgets to dashboard
- `scripts/export-costs.py` - CSV export script

**References**:
- CLI structure: [src/jarvis/cli/query.py](../../src/jarvis/cli/query.py)
- Dashboard API: [src/jarvis/api/dashboard.py](../../src/jarvis/api/dashboard.py)

---

## Implementation Order

**Recommended sequence** (can be parallelized within each phase):

### Phase 1: Foundation (Stories 5.1 + 5.2)
1. Database schema: Provider quotas, cost attribution, pricing table
2. Migrations: Seed from settings.yaml, add indexes
3. Provider registry service: Database CRUD operations
4. Cost calculation service: Pricing lookup, attribution logic
5. API endpoints: Provider management, cost queries

**Deliverable**: Database-backed provider registry with historical cost tracking

### Phase 2: Intelligence (Story 5.3)
1. Circuit breaker implementation
2. Smart router with quota checking
3. Error handling: Quota exceeded, rate limits
4. Provider rotation logic
5. Integration: Update call_llm() to use smart router

**Deliverable**: Automatic provider fallback with zero manual intervention

### Phase 3: Visibility (Story 5.4)
1. Cost aggregation SQL queries
2. CLI cost reporting commands
3. API analytics endpoints
4. Dashboard cost widgets
5. CSV export functionality

**Deliverable**: User-facing cost transparency and reporting

---

## Success Metrics

**Business Metrics**:
- Free tier usage > 90% of total LLM calls
- Zero manual provider switching required
- Cost reporting accessible in < 2 seconds
- Provider rotation successful within 100ms of quota error

**Technical Metrics**:
- Provider failover latency < 100ms
- Circuit breaker recovery time < 5 minutes
- Cost calculation accuracy: 100% (matches provider billing)
- Database query performance: Cost reports < 500ms for 30-day window

---

## Risk Assessment

### High Risk
1. **Provider API Changes**: Free tier quotas/pricing could change without notice
   - **Mitigation**: Weekly monitoring, pricing table updates, alerts on cost anomalies

2. **Quota Detection Failures**: Some providers may not return clear quota errors
   - **Mitigation**: Multiple detection methods (status codes, headers, error messages)

### Medium Risk
1. **Database Performance**: Usage logs could grow to millions of rows
   - **Mitigation**: Partitioning by month, indexes on timestamp + provider_id

2. **Circuit Breaker Tuning**: False positives could disable healthy providers
   - **Mitigation**: Configurable thresholds, exponential backoff, manual override

### Low Risk
1. **CLI UX**: Cost report formatting may need iterations
   - **Mitigation**: User feedback loop, configurable output formats

---

## Open Questions for User Input

1. **Cost Alerts**: Should JARVIS send notifications when costs exceed threshold?
   - Example: Alert when monthly cost > $10
   - Delivery: Email, CLI warning, dashboard banner?

2. **Quota Refresh**: How to handle daily quota resets?
   - Option A: Reset at midnight UTC
   - Option B: Rolling 24-hour window
   - Option C: Provider-specific (query API for reset time)

3. **Paid Tier Activation**: Require explicit user confirmation before using paid providers?
   - Option A: Auto-fallback to paid (current behavior)
   - Option B: Prompt for confirmation first time
   - Option C: Never use paid without explicit `--allow-paid` flag

4. **Cost Budget**: Should there be a monthly cost cap?
   - Example: Stop all LLM calls if monthly cost > $50
   - Alternative: Fallback to free-only mode

---

## References

### PRD Sections
- FR3.1: Provider Registry & Priority Rules ([prd.md#L773](../../docs/prd.md#L773))
- FR3.2: Free-Tier Depletion Strategy ([prd.md#L777](../../docs/prd.md#L777))
- FR3.3: Usage Tracking & Cost Calculation ([prd.md#L783](../../docs/prd.md#L783))

### Current Implementation
- Provider Infrastructure: [src/jarvis/llm/providers.py](../../src/jarvis/llm/providers.py)
- LLM Client: [src/jarvis/llm/client.py](../../src/jarvis/llm/client.py)
- Database Models: [src/jarvis/database/models.py](../../src/jarvis/database/models.py)
- Settings: [src/jarvis/config/settings.py](../../src/jarvis/config/settings.py)

### Similar Systems
- LangChain Router: Cost-aware routing (reference architecture)
- OpenAI Fallback Libraries: Provider rotation patterns
- AWS Cost Explorer: Cost reporting UX inspiration

---

## Next Steps

1. **User Review**: Get feedback on open questions above
2. **Story Refinement**: Break down stories into specific tasks
3. **Tech Spec**: Detailed database schema and API contracts
4. **Sprint Planning**: Allocate stories to sprint cycles
5. **Implementation**: Start with Phase 1 (Foundation)

**Target Start**: After Epic 4 retrospective complete
**Estimated Duration**: 2-3 sprint cycles (4-6 weeks)
**Priority**: High (enables cost-free scaling of JARVIS usage)
