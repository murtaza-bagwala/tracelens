"""Orchestrates statistics computation and issue detection into a Review."""

from __future__ import annotations

from dataclasses import dataclass

from tracelens.analyzer.bottlenecks import DEFAULT_LATENCY_THRESHOLD, detect_latency_bottlenecks
from tracelens.analyzer.cost import DEFAULT_COST_THRESHOLD, detect_cost_concentration
from tracelens.analyzer.failures import detect_failure, detect_repeated_steps, detect_step_errors
from tracelens.analyzer.retrieval import DEFAULT_MIN_DOCUMENTS, detect_retrieval_issues
from tracelens.analyzer.statistics import compute_statistics
from tracelens.analyzer.suggestions import build_suggestions
from tracelens.analyzer.token_usage import DEFAULT_TOKEN_THRESHOLD, detect_token_concentration
from tracelens.models.review import Review
from tracelens.models.trace import ExecutionTrace


@dataclass(frozen=True)
class AnalyzerConfig:
    """Thresholds that control how aggressively each detector fires."""

    latency_threshold: float = DEFAULT_LATENCY_THRESHOLD
    token_threshold: float = DEFAULT_TOKEN_THRESHOLD
    cost_threshold: float = DEFAULT_COST_THRESHOLD
    min_documents: int = DEFAULT_MIN_DOCUMENTS


def analyze_trace(trace: ExecutionTrace, config: AnalyzerConfig | None = None) -> Review:
    config = config or AnalyzerConfig()

    stats = compute_statistics(trace)

    issues = []
    issues += detect_retrieval_issues(trace, min_documents=config.min_documents)
    issues += detect_latency_bottlenecks(
        trace, stats.total_duration_ms, threshold=config.latency_threshold
    )
    issues += detect_token_concentration(trace, threshold=config.token_threshold)
    issues += detect_cost_concentration(trace, threshold=config.cost_threshold)
    issues += detect_repeated_steps(trace)
    issues += detect_step_errors(trace)
    # Failure correlation runs last so it can reference issues already found above.
    issues += detect_failure(trace, prior_issues=issues)

    suggestions = build_suggestions(issues)

    return Review(
        task=trace.task,
        statistics=stats,
        issues=tuple(issues),
        suggestions=tuple(suggestions),
    )
