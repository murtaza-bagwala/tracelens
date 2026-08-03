"""TraceLens: analyze AI agent execution traces and suggest reasoning-architecture improvements."""

from tracelens.analyzer.batch import analyze_batch
from tracelens.analyzer.comparison import compare_traces
from tracelens.analyzer.engine import AnalyzerConfig, analyze_trace
from tracelens.models.review import (
    BatchSummary,
    Comparison,
    ComparisonEntry,
    Issue,
    Review,
    Statistics,
    Suggestion,
)
from tracelens.models.trace import ExecutionTrace, Step
from tracelens.reporters.json_reporter import (
    batch_to_dict,
    batch_to_json,
    comparison_to_dict,
    comparison_to_json,
    to_dict,
    to_json,
)
from tracelens.reporters.text import render_batch_text, render_comparison_text, render_text

__version__ = "0.1.0"

__all__ = [
    "AnalyzerConfig",
    "analyze_trace",
    "compare_traces",
    "analyze_batch",
    "ExecutionTrace",
    "Step",
    "Issue",
    "Review",
    "Statistics",
    "Suggestion",
    "Comparison",
    "ComparisonEntry",
    "BatchSummary",
    "render_text",
    "render_comparison_text",
    "render_batch_text",
    "to_dict",
    "to_json",
    "comparison_to_dict",
    "comparison_to_json",
    "batch_to_dict",
    "batch_to_json",
]
