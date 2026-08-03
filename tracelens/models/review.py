"""Data model for the output of an analysis run: statistics, issues, suggestions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Statistics:
    """Aggregate numbers computed from an execution trace."""

    total_duration_ms: float
    step_count: int
    llm_calls: int
    tool_calls: int
    retrieval_calls: int
    other_calls: int
    total_tokens: int
    success: bool
    total_cost: float = 0.0

    @property
    def total_duration_seconds(self) -> float:
        return self.total_duration_ms / 1000.0


@dataclass(frozen=True)
class Issue:
    """A single detected problem in the trace, e.g. a bottleneck or a failure."""

    category: str
    message: str
    step_name: str | None = None
    severity: str = "warning"  # one of: info, warning, critical


@dataclass(frozen=True)
class Suggestion:
    """A single actionable recommendation tied to one or more detected issues."""

    category: str
    message: str


@dataclass(frozen=True)
class Review:
    """The full result of analyzing an execution trace."""

    task: str
    statistics: Statistics
    issues: tuple[Issue, ...]
    suggestions: tuple[Suggestion, ...]


@dataclass(frozen=True)
class ComparisonEntry:
    """One labeled trace's review, as part of a multi-trace comparison."""

    label: str
    review: Review


@dataclass(frozen=True)
class Comparison:
    """Side-by-side result of analyzing multiple traces (e.g. loop configs)."""

    entries: tuple[ComparisonEntry, ...]
    # Metric name -> label of the winning entry, or None if tied.
    best: dict[str, str | None]


@dataclass(frozen=True)
class BatchSummary:
    """Aggregate result of analyzing every trace in a batch (e.g. a directory)."""

    entries: tuple[ComparisonEntry, ...]
    success_rate: float  # 0.0-1.0
    avg_duration_ms: float
    avg_tokens: float
    avg_cost: float
    # Issue category -> number of times it fired across the whole batch.
    issue_counts: dict[str, int]
