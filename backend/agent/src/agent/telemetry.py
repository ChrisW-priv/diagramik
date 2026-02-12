"""OpenTelemetry configuration for the diagram generation agent.

Provides tracing instrumentation for monitoring agent execution.
"""

import os
from functools import lru_cache

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

SERVICE_NAME = "diagram-agent"


def _is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("DEPLOYMENT_ENVIRONMENT") == "DEPLOYED_SERVICE"


@lru_cache(maxsize=1)
def configure_telemetry() -> TracerProvider:
    """Initialize OpenTelemetry with appropriate exporter.

    Uses console exporter for development and OTLP for production.
    Called once and cached.

    Returns:
        Configured TracerProvider
    """
    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "deployment.environment": "production"
            if _is_production()
            else "development",
        }
    )

    provider = TracerProvider(resource=resource)

    if _is_production():
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
            provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        # Development: log spans to console if OTEL_DEBUG is set
        if os.getenv("OTEL_DEBUG"):
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str = SERVICE_NAME) -> trace.Tracer:
    """Get a configured tracer instance.

    Ensures telemetry is configured before returning tracer.

    Args:
        name: Tracer name (defaults to service name)

    Returns:
        Configured Tracer instance
    """
    configure_telemetry()
    return trace.get_tracer(name)
