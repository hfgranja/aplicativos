"""
OpenTelemetry initialization for AuditAI backend.
No-ops gracefully when OTEL_EXPORTER_OTLP_ENDPOINT is not configured.
"""
from app.config import settings


def init_telemetry() -> None:
    """
    Configure OTel SDK with OTLP gRPC export.
    Called once at application startup.
    If OTEL_EXPORTER_OTLP_ENDPOINT is empty, installs a no-op tracer.
    """
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        return  # Telemetry disabled — no-op tracer is used by default

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
        })
        provider = TracerProvider(resource=resource)

        # OTLP gRPC exporter
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except ImportError:
            # Fall back to OTLP HTTP if gRPC is not installed
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHTTPExporter
                exporter = OTLPHTTPExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except ImportError:
                return  # No OTLP exporter available

        trace.set_tracer_provider(provider)

        # Instrument FastAPI if available
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor().instrument()
        except ImportError:
            pass

    except ImportError:
        pass  # opentelemetry-sdk not installed — continue without tracing


def get_tracer(name: str = "auditai"):
    """
    Return an OpenTelemetry tracer. Returns a no-op tracer if OTel is not configured.
    """
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


def get_current_trace_id() -> str:
    """
    Return the current trace ID as a hex string, or empty string if no active span.
    Used to embed trace_id in API responses and finding evidence.
    """
    try:
        from opentelemetry import trace
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, '032x')
    except Exception:
        pass
    return ""


class _NoOpTracer:
    """Fallback tracer when opentelemetry is not installed."""

    def start_as_current_span(self, name: str, **kwargs):
        return _NoOpSpanContext()


class _NoOpSpanContext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, key: str, value) -> None:
        pass

    def set_status(self, status) -> None:
        pass

    def record_exception(self, exc) -> None:
        pass
