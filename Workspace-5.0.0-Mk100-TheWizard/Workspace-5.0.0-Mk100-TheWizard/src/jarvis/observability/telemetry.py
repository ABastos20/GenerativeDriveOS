"""Telemetry manager for OpenTelemetry integration.

OpenTelemetry is optional - if not installed, the TelemetryManager.setup()
method will silently do nothing, allowing the application to run without
observability features.
"""
import os
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class TelemetryManager:
    """Manages OpenTelemetry tracing and metrics configuration.
    
    If OpenTelemetry libraries are not installed, setup() is a no-op.
    """

    def __init__(self, service_name: str = "jarvis-core", otlp_endpoint: Optional[str] = None):
        """Initialize telemetry manager."""
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint or os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"
        )
        self.tracer_provider = None
        self.meter_provider = None
        self._available = False

    def setup(self) -> None:
        """Initialize and set global telemetry providers.
        
        If OpenTelemetry is not available, this method does nothing.
        """
        try:
            from opentelemetry import trace, metrics
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.exporter.prometheus import PrometheusMetricReader
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.semconv.resource import ResourceAttributes
        except ImportError:
            logger.info("opentelemetry_not_available", message="Observability disabled")
            return

        try:
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: "0.1.0",
            })

            # 1. Tracing Setup (Targeting Jaeger via OTLP gRPC)
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Use insecure channel for internal Docker networking
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True
            )
            
            # Batch processor for performance
            self.tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(self.tracer_provider)

            # 2. Metrics Setup (Targeting Prometheus via scraping)
            reader = PrometheusMetricReader()
            self.meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[reader]
            )
            metrics.set_meter_provider(self.meter_provider)

            self._available = True
            logger.info(
                "telemetry_initialized",
                service=self.service_name,
                trace_endpoint=self.otlp_endpoint,
                metrics_backend="prometheus"
            )

        except Exception as e:
            logger.error("telemetry_init_failed", error=str(e))
            # OTel defaults to no-op if providers aren't set, which is safe.
