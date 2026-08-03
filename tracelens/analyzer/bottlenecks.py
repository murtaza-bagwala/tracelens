"""Detect latency bottlenecks among non-LLM steps (tool calls, retrieval)."""

from __future__ import annotations

from tracelens.models.review import Issue
from tracelens.models.trace import ExecutionTrace

DEFAULT_LATENCY_THRESHOLD = 0.3

# LLM latency is largely inherent to the model call itself; tool and retrieval
# latency is usually the part an engineer can actually do something about
# (caching, parallelizing, swapping providers), so that's what we flag here.
_BOTTLENECK_TYPES = ("tool", "retrieval")


def detect_latency_bottlenecks(
    trace: ExecutionTrace,
    total_duration_ms: float,
    threshold: float = DEFAULT_LATENCY_THRESHOLD,
) -> list[Issue]:
    if total_duration_ms <= 0:
        return []

    candidates = [
        step
        for step in trace.steps
        if step.type in _BOTTLENECK_TYPES and step.duration_ms > 0
    ]
    if not candidates:
        return []

    slowest = max(candidates, key=lambda step: step.duration_ms)
    share = slowest.duration_ms / total_duration_ms
    if share < threshold:
        return []

    pct = round(share * 100)
    return [
        Issue(
            category="latency_bottleneck",
            message=(
                f"'{slowest.name}' step dominates latency "
                f"({pct}% of total execution time, {slowest.duration_ms:.0f}ms)."
            ),
            step_name=slowest.name,
            severity="warning",
        )
    ]
