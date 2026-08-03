"""Render a Review, Comparison, or BatchSummary as a JSON-serializable dict."""

from __future__ import annotations

import json

from tracelens.models.review import BatchSummary, Comparison, Review


def to_dict(review: Review) -> dict:
    stats = review.statistics
    return {
        "task": review.task,
        "statistics": {
            "total_duration_ms": stats.total_duration_ms,
            "total_duration_seconds": stats.total_duration_seconds,
            "step_count": stats.step_count,
            "llm_calls": stats.llm_calls,
            "tool_calls": stats.tool_calls,
            "retrieval_calls": stats.retrieval_calls,
            "other_calls": stats.other_calls,
            "total_tokens": stats.total_tokens,
            "total_cost": stats.total_cost,
            "success": stats.success,
        },
        "issues": [
            {
                "category": issue.category,
                "message": issue.message,
                "step_name": issue.step_name,
                "severity": issue.severity,
            }
            for issue in review.issues
        ],
        "suggestions": [
            {"category": suggestion.category, "message": suggestion.message}
            for suggestion in review.suggestions
        ],
    }


def to_json(review: Review, indent: int = 2) -> str:
    return json.dumps(to_dict(review), indent=indent)


def comparison_to_dict(comparison: Comparison) -> dict:
    return {
        "entries": [
            {"label": entry.label, "review": to_dict(entry.review)}
            for entry in comparison.entries
        ],
        "best": dict(comparison.best),
    }


def comparison_to_json(comparison: Comparison, indent: int = 2) -> str:
    return json.dumps(comparison_to_dict(comparison), indent=indent)


def batch_to_dict(summary: BatchSummary) -> dict:
    count = len(summary.entries)
    successes = sum(1 for entry in summary.entries if entry.review.statistics.success)
    return {
        "trace_count": count,
        "success_count": successes,
        "success_rate": summary.success_rate,
        "avg_duration_ms": summary.avg_duration_ms,
        "avg_duration_seconds": summary.avg_duration_ms / 1000.0,
        "avg_tokens": summary.avg_tokens,
        "avg_cost": summary.avg_cost,
        "issue_counts": dict(summary.issue_counts),
        "entries": [
            {"label": entry.label, "review": to_dict(entry.review)}
            for entry in summary.entries
        ],
    }


def batch_to_json(summary: BatchSummary, indent: int = 2) -> str:
    return json.dumps(batch_to_dict(summary), indent=indent)
