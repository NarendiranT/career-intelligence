from __future__ import annotations

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from backend.telemetry import (
    bind_meter,
    record_graph_duration,
    record_indexing_failure,
    record_llm_usage,
    telemetry_enabled,
)


def _metric_by_name(data, name: str):
    for resource_metrics in data.resource_metrics:
        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name == name:
                    return metric
    return None


def test_telemetry_disabled_by_default():
    from fastapi import FastAPI

    from backend.telemetry import setup_telemetry

    assert telemetry_enabled() is False
    setup_telemetry(FastAPI())


def test_record_llm_usage_increments_in_memory_meter():
    reader = InMemoryMetricReader()
    bind_meter(MeterProvider(metric_readers=[reader]).get_meter("career-intelligence-test"))
    record_llm_usage(
        event_type="rag.generate",
        model="openai/gpt-oss-20b",
        input_tokens=11,
        output_tokens=4,
        latency_ms=12.5,
    )
    data = reader.get_metrics_data()
    tokens = _metric_by_name(data, "ci.llm.tokens")
    latency = _metric_by_name(data, "ci.llm.latency_ms")
    assert tokens is not None
    assert latency is not None
    token_sum = sum(point.value for point in tokens.data.data_points)
    assert token_sum == 15
    assert latency.data.data_points[0].count == 1


def test_record_graph_and_indexing_failure_metrics():
    reader = InMemoryMetricReader()
    bind_meter(MeterProvider(metric_readers=[reader]).get_meter("career-intelligence-test"))
    record_graph_duration(
        kind="indexing",
        duration_ms=40.0,
        feature="documents",
        status="error",
    )
    record_graph_duration(
        kind="rag",
        duration_ms=80.0,
        feature="chat",
        status="ok",
        channel="assistant",
    )
    record_indexing_failure()
    data = reader.get_metrics_data()
    indexing = _metric_by_name(data, "ci.indexing.duration_ms")
    rag = _metric_by_name(data, "ci.rag.duration_ms")
    failures = _metric_by_name(data, "ci.indexing.failures")
    assert indexing is not None and indexing.data.data_points[0].count == 1
    assert rag is not None and rag.data.data_points[0].count == 1
    assert failures is not None
    assert sum(point.value for point in failures.data.data_points) == 1
