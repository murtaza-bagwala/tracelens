"""Compare multiple execution traces (e.g. different loop configurations)."""

from __future__ import annotations

from tracelens.analyzer.engine import AnalyzerConfig, analyze_trace
from tracelens.models.review import Comparison, ComparisonEntry
from tracelens.models.trace import ExecutionTrace

# metric name -> (value extractor, direction). "min" or "max" wins.
_METRICS: dict[str, tuple] = {
    "success": (lambda review: int(review.statistics.success), "max"),
    "duration_ms": (lambda review: review.statistics.total_duration_ms, "min"),
    "total_tokens": (lambda review: review.statistics.total_tokens, "min"),
    "total_cost": (lambda review: review.statistics.total_cost, "min"),
    "issue_count": (lambda review: len(review.issues), "min"),
}


def _best_label(entries: tuple[ComparisonEntry, ...], value_of, direction: str) -> str | None:
    values = [(entry.label, value_of(entry.review)) for entry in entries]
    best_value = min(v for _, v in values) if direction == "min" else max(v for _, v in values)
    winners = [label for label, v in values if v == best_value]
    return winners[0] if len(winners) == 1 else None


def compare_traces(
    labeled_traces: list[tuple[str, ExecutionTrace]],
    config: AnalyzerConfig | None = None,
) -> Comparison:
    """Run analyze_trace over each (label, trace) pair and rank them per metric."""
    config = config or AnalyzerConfig()

    entries = tuple(
        ComparisonEntry(label=label, review=analyze_trace(trace, config))
        for label, trace in labeled_traces
    )

    best = {
        metric: _best_label(entries, value_of, direction)
        for metric, (value_of, direction) in _METRICS.items()
    }

    return Comparison(entries=entries, best=best)
