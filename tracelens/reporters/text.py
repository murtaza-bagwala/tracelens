"""Render a Review, Comparison, or BatchSummary as a human-readable text report."""

from __future__ import annotations

from tracelens.models.experiment import ExperimentComparison
from tracelens.models.review import BatchSummary, Comparison, Review

_RULE = "-" * 48

# (row title, best-metric key or None, value extractor)
_COMPARISON_ROWS = [
    ("Success", "success", lambda review: "Yes" if review.statistics.success else "No"),
    ("Duration (s)", "duration_ms", lambda review: f"{review.statistics.total_duration_seconds:.2f}"),
    ("Steps", None, lambda review: str(review.statistics.step_count)),
    ("LLM Calls", None, lambda review: str(review.statistics.llm_calls)),
    ("Tool Calls", None, lambda review: str(review.statistics.tool_calls)),
    ("Retrieval Calls", None, lambda review: str(review.statistics.retrieval_calls)),
    ("Total Tokens", "total_tokens", lambda review: str(review.statistics.total_tokens)),
    ("Total Cost", "total_cost", lambda review: f"${review.statistics.total_cost:.4f}"),
    ("Issues", "issue_count", lambda review: str(len(review.issues))),
    ("Suggestions", None, lambda review: str(len(review.suggestions))),
]


def render_text(review: Review) -> str:
    stats = review.statistics
    lines = [_RULE, "Architecture Review", _RULE, ""]

    if review.task:
        lines.append(f"Task: {review.task}")
        lines.append("")

    lines.append(f"Execution Time: {stats.total_duration_seconds:.2f} sec")
    lines.append(f"Steps: {stats.step_count}")
    lines.append(f"LLM Calls: {stats.llm_calls}")
    lines.append(f"Tool Calls: {stats.tool_calls}")
    lines.append(f"Retrieval Calls: {stats.retrieval_calls}")
    if stats.other_calls:
        lines.append(f"Other Calls: {stats.other_calls}")
    lines.append(f"Total Tokens: {stats.total_tokens}")
    if stats.total_cost:
        lines.append(f"Total Cost: ${stats.total_cost:.4f}")
    lines.append(f"Success: {'Yes' if stats.success else 'No'}")
    lines.append("")

    lines.append("Potential Issues:")
    lines.append("")
    if review.issues:
        for issue in review.issues:
            lines.append(f"- {issue.message}")
    else:
        lines.append("- No significant issues detected.")
    lines.append("")

    lines.append("Suggestions:")
    lines.append("")
    if review.suggestions:
        for suggestion in review.suggestions:
            lines.append(f"- {suggestion.message}")
    else:
        lines.append("- No suggestions — architecture looks solid.")
    lines.append("")
    lines.append(_RULE)

    return "\n".join(lines)


def render_batch_text(summary: BatchSummary) -> str:
    entries = summary.entries
    count = len(entries)
    successes = sum(1 for entry in entries if entry.review.statistics.success)

    lines = [_RULE, f"Batch Analysis ({count} trace{'s' if count != 1 else ''})", _RULE, ""]

    if count == 0:
        lines.append("No trace files found.")
        lines.append("")
        lines.append(_RULE)
        return "\n".join(lines)

    lines.append(f"Success Rate: {summary.success_rate * 100:.1f}% ({successes}/{count})")
    lines.append(f"Avg Duration: {summary.avg_duration_ms / 1000:.2f} sec")
    lines.append(f"Avg Tokens: {summary.avg_tokens:.0f}")
    lines.append(f"Avg Cost: ${summary.avg_cost:.4f}")
    lines.append("")

    lines.append("Issue Frequency:")
    lines.append("")
    if summary.issue_counts:
        for category, num in sorted(
            summary.issue_counts.items(), key=lambda kv: (-kv[1], kv[0])
        ):
            lines.append(f"- {category}: {num}")
    else:
        lines.append("- No significant issues detected across the batch.")
    lines.append("")

    lines.append("Per-Trace Summary:")
    lines.append("")
    for entry in entries:
        stats = entry.review.statistics
        status = "PASS" if stats.success else "FAIL"
        lines.append(
            f"- {entry.label}: {status}, {stats.total_duration_seconds:.2f}s, "
            f"{stats.total_tokens} tokens, ${stats.total_cost:.4f}, "
            f"{len(entry.review.issues)} issue(s)"
        )
    lines.append("")
    lines.append(_RULE)

    return "\n".join(lines)


def render_comparison_text(comparison: Comparison) -> str:
    entries = comparison.entries
    labels = [entry.label for entry in entries]

    rows = []
    for title, metric_key, value_of in _COMPARISON_ROWS:
        values = [value_of(entry.review) for entry in entries]
        if metric_key is not None:
            best_col = comparison.best.get(metric_key) or "tie"
        else:
            best_col = "-"
        rows.append((title, values, best_col))

    metric_width = max(len("Metric"), *(len(title) for title, _, _ in rows)) + 2
    col_widths = [
        max(len(label), *(len(values[i]) for _, values, _ in rows)) + 2
        for i, label in enumerate(labels)
    ]
    best_width = max(len("Best"), *(len(best_col) for _, _, best_col in rows)) + 2

    lines = [_RULE, "Experiment Comparison", _RULE, ""]

    header = "Metric".ljust(metric_width)
    header += "".join(label.ljust(w) for label, w in zip(labels, col_widths))
    header += "Best".ljust(best_width)
    lines.append(header.rstrip())

    for title, values, best_col in rows:
        line = title.ljust(metric_width)
        line += "".join(v.ljust(w) for v, w in zip(values, col_widths))
        line += best_col.ljust(best_width)
        lines.append(line.rstrip())

    lines.append("")
    lines.append(_RULE)

    return "\n".join(lines)


# (row title, best-metric key or None, value extractor over a BatchSummary)
_EXPERIMENT_ROWS = [
    ("Success Rate", "success_rate", lambda batch: f"{batch.success_rate * 100:.1f}%"),
    ("Avg Duration (s)", "avg_duration_ms", lambda batch: f"{batch.avg_duration_ms / 1000:.2f}"),
    ("Avg Tokens", "avg_tokens", lambda batch: f"{batch.avg_tokens:.0f}"),
    ("Avg Cost", "avg_cost", lambda batch: f"${batch.avg_cost:.4f}"),
    (
        "Avg Issues",
        "avg_issue_count",
        lambda batch: f"{sum(batch.issue_counts.values()) / max(len(batch.entries), 1):.2f}",
    ),
    ("Traces", None, lambda batch: str(len(batch.entries))),
]


def render_experiment_comparison_text(comparison: ExperimentComparison) -> str:
    entries = comparison.entries
    labels = [entry.label for entry in entries]

    rows = []
    for title, metric_key, value_of in _EXPERIMENT_ROWS:
        values = [value_of(entry.batch) for entry in entries]
        best_col = (comparison.best.get(metric_key) or "tie") if metric_key is not None else "-"
        rows.append((title, values, best_col))

    metric_width = max(len("Metric"), *(len(title) for title, _, _ in rows)) + 2
    col_widths = [
        max(len(label), *(len(values[i]) for _, values, _ in rows)) + 2
        for i, label in enumerate(labels)
    ]
    best_width = max(len("Best"), *(len(best_col) for _, _, best_col in rows)) + 2

    lines = [_RULE, "Experiment Results (aggregated over the dataset)", _RULE, ""]

    header = "Metric".ljust(metric_width)
    header += "".join(label.ljust(w) for label, w in zip(labels, col_widths))
    header += "Best".ljust(best_width)
    lines.append(header.rstrip())

    for title, values, best_col in rows:
        line = title.ljust(metric_width)
        line += "".join(v.ljust(w) for v, w in zip(values, col_widths))
        line += best_col.ljust(best_width)
        lines.append(line.rstrip())

    lines.append("")
    lines.append(_RULE)

    return "\n".join(lines)
