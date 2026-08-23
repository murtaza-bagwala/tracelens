"""Compare multiple loop configs run over the same dataset (aggregate vs.
aggregate), mirroring analyzer/comparison.py's single-trace comparison but
one level up: BatchSummary vs. BatchSummary instead of Review vs. Review."""

from __future__ import annotations

from tracelens.models.experiment import ExperimentComparison, ExperimentEntry

# metric name -> (value extractor over a BatchSummary, direction). "min" or "max" wins.
_METRICS: dict[str, tuple] = {
    "success_rate": (lambda batch: batch.success_rate, "max"),
    "avg_duration_ms": (lambda batch: batch.avg_duration_ms, "min"),
    "avg_tokens": (lambda batch: batch.avg_tokens, "min"),
    "avg_cost": (lambda batch: batch.avg_cost, "min"),
    "avg_issue_count": (
        lambda batch: sum(batch.issue_counts.values()) / max(len(batch.entries), 1),
        "min",
    ),
}


def _best_label(entries: tuple[ExperimentEntry, ...], value_of, direction: str) -> str | None:
    values = [(entry.label, value_of(entry.batch)) for entry in entries]
    best_value = min(v for _, v in values) if direction == "min" else max(v for _, v in values)
    winners = [label for label, v in values if v == best_value]
    return winners[0] if len(winners) == 1 else None


def compare_experiments(entries: tuple[ExperimentEntry, ...]) -> ExperimentComparison:
    """Rank each config's aggregate BatchSummary against the others per metric."""
    best = {
        metric: _best_label(entries, value_of, direction)
        for metric, (value_of, direction) in _METRICS.items()
    }

    return ExperimentComparison(entries=entries, best=best)
