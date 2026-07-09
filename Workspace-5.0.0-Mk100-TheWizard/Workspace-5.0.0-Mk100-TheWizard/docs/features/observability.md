# JARVIS Observability Stack (v2.4.0)

## Overview
Implemented a comprehensive observability suite using OpenTelemetry, Jaeger, Prometheus, and Grafana.

## Architecture
- **Application**: Auto-instrumented (FastAPI, SQLAlchemy) + Manual Spans (ARCHES Controller).
- **Collection**: OTLP gRPC/HTTP.
- **Backends**: Jaeger (Traces), Prometheus (Metrics).
- **Visualization**: Grafana.

## How to Run
1. Start the stack:
   ```bash
   docker compose -f docker/docker-compose.yml -f docker/docker-compose.observability.yml up -d
   ```
2. Access Services:
   - **Grafana**: http://localhost:3000 (User: `admin`, Pass: `admin`)
   - **Jaeger UI**: http://localhost:16686
   - **Prometheus**: http://localhost:9090

## Dashboards
- **JARVIS Command Center 2.0**:
  - **Golden Signals**: RPS, Latency (P95), Error Rate, Memory.
  - **Cognitive Veins**: Token Usage, Memory Latency, Planner Throughput, Safety Violations.

## Metrics
- `jarvis_llm_tokens_total`: Counter (input/output).
- `jarvis_memory_search_latency_ms`: Histogram.
- `jarvis_planner_stages_completed_total`: Counter.
- `jarvis_safety_violations_total`: Counter.
