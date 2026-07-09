"""Custom metrics registry for JARVIS.

OpenTelemetry metrics are optional - if the library is not installed,
we provide no-op stubs so the rest of the application can run without errors.
"""

try:
    from opentelemetry import metrics
    meter = metrics.get_meter("jarvis-core")
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    meter = None


class _NoOpCounter:
    """No-op counter stub when OpenTelemetry is unavailable."""
    def add(self, amount, attributes=None):
        pass


class _NoOpHistogram:
    """No-op histogram stub when OpenTelemetry is unavailable."""
    def record(self, amount, attributes=None):
        pass


# --- Cognitive Metrics ---

if _OTEL_AVAILABLE and meter:
    llm_tokens_total = meter.create_counter(
        "jarvis_llm_tokens_total",
        description="Total input/output tokens used by LLMs",
        unit="tokens"
    )
    planner_stages_completed = meter.create_counter(
        "jarvis_planner_stages_completed_total",
        description="Number of ARCHES planner stages completed",
        unit="stage"
    )
    safety_violations_total = meter.create_counter(
        "jarvis_safety_violations_total",
        description="Number of safety system interventions (Loop Guard, Safe Mode)",
        unit="violation"
    )
    # --- Performance Metrics ---
    memory_search_latency = meter.create_histogram(
        "jarvis_memory_search_latency_ms",
        description="Latency of Qdrant memory searches",
        unit="ms"
    )
    memory_freshness_score = meter.create_histogram(
        "jarvis_memory_freshness_score",
        description="Freshness score of retrieved memory chunks (0.0-1.0)",
        unit="score"
    )
else:
    # Provide no-op stubs
    llm_tokens_total = _NoOpCounter()
    planner_stages_completed = _NoOpCounter()
    safety_violations_total = _NoOpCounter()
    memory_search_latency = _NoOpHistogram()
    memory_freshness_score = _NoOpHistogram()
