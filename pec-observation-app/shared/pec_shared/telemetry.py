"""OpenTelemetry initialization — mirrors auditai/backend/app/core/telemetry.py."""
import os
import logging

logger = logging.getLogger(__name__)

_tracer = None


class _NoOpTracer:
    def start_as_current_span(self, name, **kwargs):
        from contextlib import contextmanager

        @contextmanager
        def _noop():
            yield None

        return _noop()


def init_telemetry() -> None:
    global _tracer
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    enabled = os.getenv("OTEL_EXPORTER_ENABLED", "false").lower() == "true"
    service_name = os.getenv("OTEL_SERVICE_NAME", "pec-service")

    if not enabled or not endpoint:
        _tracer = _NoOpTracer()
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource(attributes={SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
        logger.info("OpenTelemetry initialized for %s → %s", service_name, endpoint)
    except Exception as exc:
        logger.warning("OTel init failed (%s), using no-op tracer", exc)
        _tracer = _NoOpTracer()


def get_tracer():
    global _tracer
    if _tracer is None:
        _tracer = _NoOpTracer()
    return _tracer


def get_current_trace_id() -> str:
    try:
        from opentelemetry import trace
        ctx = trace.get_current_span().get_span_context()
        return format(ctx.trace_id, "032x") if ctx.is_valid else ""
    except Exception:
        return ""
