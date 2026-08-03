"""Aggregate analyze_trace results across a whole batch of traces (e.g. a dataset)."""

from __future__ import annotations

from collections import Counter

from tracelens.analyzer.engine import AnalyzerConfig, analyze_trace
from tracelens.models.review import BatchSummary, ComparisonEntry
from tracelens.models.trace import ExecutionTrace


def analyze_batch(
    labeled_traces: list[tuple[str, ExecutionTrace]],
    config: AnalyzerConfig | None = None,
) -> BatchSummary:
    """Run analyze_trace over every (label, trace) pair and summarize the batch."""
    config = config or AnalyzerConfig()

    entries = tuple(
        ComparisonEntry(label=label, review=analyze_trace(trace, config))
        for label, trace in labeled_traces
    )

    count = len(entries)
    if count == 0:
        return BatchSummary(
            entries=(),
            success_rate=0.0,
            avg_duration_ms=0.0,
            avg_tokens=0.0,
            avg_cost=0.0,
            issue_counts={},
        )

    successes = sum(1 for entry in entries if entry.review.statistics.success)
    issue_counts = Counter(
        issue.category for entry in entries for issue in entry.review.issues
    )

    return BatchSummary(
        entries=entries,
        success_rate=successes / count,
        avg_duration_ms=sum(e.review.statistics.total_duration_ms for e in entries) / count,
        avg_tokens=sum(e.review.statistics.total_tokens for e in entries) / count,
        avg_cost=sum(e.review.statistics.total_cost for e in entries) / count,
        issue_counts=dict(issue_counts),
    )
