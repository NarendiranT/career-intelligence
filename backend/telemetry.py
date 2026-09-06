from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from backend.config import settings

TRACER_NAME = "career-intelligence"
METER_NAME = "career-intelligence"

_setup_done = False
_llm_tokens = None
_llm_latency = None
_indexing_duration = None
_rag_duration = None
_indexing_failures = None


def telemetry_enabled() -> bool:
    endpoint = (settings.otel_exporter_otlp_endpoint or "").strip()
    return bool(settings.otel_enabled and endpoint)


def _otlp_base() -> str:
    return settings.otel_exporter_otlp_endpoint.rstrip("/")


def _init_instruments(meter=None) -> None:
    global _llm_tokens, _llm_latency, _indexing_duration, _rag_duration, _indexing_failures
    meter = meter or metrics.get_meter(METER_NAME)
    _llm_tokens = meter.create_counter(
        "ci.llm.tokens",
        unit="1",
        description="LLM prompt and completion tokens",
    )
    _llm_latency = meter.create_histogram(
        "ci.llm.latency_ms",
        unit="ms",
        description="LLM invoke latency",
    )
    _indexing_duration = meter.create_histogram(
        "ci.indexing.duration_ms",
        unit="ms",
        description="Indexing graph duration",
    )
    _rag_duration = meter.create_histogram(
        "ci.rag.duration_ms",
        unit="ms",
        description="RAG graph duration",
    )
    _indexing_failures = meter.create_counter(
        "ci.indexing.failures",
        unit="1",
        description="Indexing graph failures",
    )


def setup_telemetry(app: FastAPI) -> None:
    global _setup_done
    if _setup_done:
        return
    _setup_done = True
    if not telemetry_enabled():
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    base = _otlp_base()

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces"))
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base}/v1/metrics")
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    FastAPIInstrumentor.instrument_app(app, excluded_urls="health")
    from backend.db import engine

    SQLAlchemyInstrumentor().instrument(engine=engine)
    _init_instruments()


def bind_meter(meter) -> None:
    """Test helper: recreate instruments on an isolated meter."""
    _init_instruments(meter)


def tracer() -> trace.Tracer:
    return trace.get_tracer(TRACER_NAME)


def _attrs(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None and value != ""}


def record_llm_usage(
    *,
    event_type: str,
    model: str | None,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
) -> None:
    labels = _attrs(event_type=event_type, model=model)
    if _llm_tokens is not None:
        if input_tokens:
            _llm_tokens.add(input_tokens, {**labels, "direction": "prompt"})
        if output_tokens:
            _llm_tokens.add(output_tokens, {**labels, "direction": "completion"})
    if _llm_latency is not None:
        _llm_latency.record(float(latency_ms), labels)


def record_graph_duration(
    *,
    kind: str,
    duration_ms: float,
    feature: str,
    status: str,
    channel: str | None = None,
    doc_type: str | None = None,
) -> None:
    labels = _attrs(feature=feature, status=status, channel=channel, doc_type=doc_type)
    histogram = _indexing_duration if kind == "indexing" else _rag_duration
    if histogram is not None:
        histogram.record(float(duration_ms), labels)


def record_indexing_failure() -> None:
    if _indexing_failures is not None:
        _indexing_failures.add(1)


@contextmanager
def graph_span(name: str, **attributes: Any) -> Iterator[trace.Span]:
    with tracer().start_as_current_span(name) as span:
        for key, value in _attrs(**attributes).items():
            span.set_attribute(key, value)
        try:
            yield span
        except Exception as exc:
            mark_span_error(span, exc)
            raise


def mark_span_error(span: trace.Span, exc: BaseException) -> None:
    span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
    span.record_exception(exc)


@contextmanager
def llm_invoke_span(*, event_type: str, model: str | None) -> Iterator[trace.Span]:
    with tracer().start_as_current_span("llm.invoke") as span:
        span.set_attribute("event_type", event_type)
        if model:
            span.set_attribute("model", model)
            span.set_attribute("gen_ai.request.model", model)
        yield span
