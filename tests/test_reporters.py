import json

from tracelens.analyzer.batch import analyze_batch
from tracelens.analyzer.comparison import compare_traces
from tracelens.analyzer.engine import analyze_trace
from tracelens.models.trace import ExecutionTrace
from tracelens.reporters.json_reporter import (
    batch_to_dict,
    batch_to_json,
    comparison_to_dict,
    comparison_to_json,
    to_dict,
    to_json,
)
from tracelens.reporters.text import render_batch_text, render_comparison_text, render_text


def _sample_review(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    return analyze_trace(trace)


def test_render_text_contains_key_sections(sample_trace_dict):
    review = _sample_review(sample_trace_dict)
    output = render_text(review)

    assert "Architecture Review" in output
    assert "Execution Time: 1.15 sec" in output
    assert "LLM Calls: 2" in output
    assert "Tool Calls: 1" in output
    assert "Retrieval Calls: 1" in output
    assert "Total Cost: $0.0127" in output
    assert "Potential Issues:" in output
    assert "Suggestions:" in output
    assert "Success: No" in output
    for issue in review.issues:
        assert issue.message in output
    for suggestion in review.suggestions:
        assert suggestion.message in output


def test_render_text_no_issues_message():
    from tracelens.models.review import Review, Statistics

    review = Review(
        task="t",
        statistics=Statistics(
            total_duration_ms=0,
            step_count=0,
            llm_calls=0,
            tool_calls=0,
            retrieval_calls=0,
            other_calls=0,
            total_tokens=0,
            success=True,
        ),
        issues=(),
        suggestions=(),
    )
    output = render_text(review)
    assert "No significant issues detected." in output
    assert "No suggestions" in output


def test_to_dict_round_trips_key_fields(sample_trace_dict):
    review = _sample_review(sample_trace_dict)
    data = to_dict(review)

    assert data["task"] == review.task
    assert data["statistics"]["llm_calls"] == 2
    assert data["statistics"]["total_cost"] == review.statistics.total_cost
    assert len(data["issues"]) == len(review.issues)
    assert len(data["suggestions"]) == len(review.suggestions)


def test_to_json_is_valid_json(sample_trace_dict):
    review = _sample_review(sample_trace_dict)
    parsed = json.loads(to_json(review))
    assert parsed["task"] == review.task


def _sample_comparison(sample_trace_dict, sample_trace_reflective_dict):
    return compare_traces(
        [
            ("baseline", ExecutionTrace.from_dict(sample_trace_dict)),
            ("reflective", ExecutionTrace.from_dict(sample_trace_reflective_dict)),
        ]
    )


def test_render_comparison_text_contains_key_sections(
    sample_trace_dict, sample_trace_reflective_dict
):
    comparison = _sample_comparison(sample_trace_dict, sample_trace_reflective_dict)
    output = render_comparison_text(comparison)

    assert "Experiment Comparison" in output
    assert "baseline" in output
    assert "reflective" in output
    assert "Success" in output
    assert "Duration (s)" in output
    assert "Total Tokens" in output
    assert "Total Cost" in output
    assert "Issues" in output
    assert "Best" in output


def test_comparison_to_dict_round_trips_key_fields(
    sample_trace_dict, sample_trace_reflective_dict
):
    comparison = _sample_comparison(sample_trace_dict, sample_trace_reflective_dict)
    data = comparison_to_dict(comparison)

    assert [entry["label"] for entry in data["entries"]] == ["baseline", "reflective"]
    assert data["best"]["success"] == "reflective"
    assert data["best"]["total_cost"] == "baseline"
    assert data["entries"][0]["review"]["task"] == comparison.entries[0].review.task


def test_comparison_to_json_is_valid_json(sample_trace_dict, sample_trace_reflective_dict):
    comparison = _sample_comparison(sample_trace_dict, sample_trace_reflective_dict)
    parsed = json.loads(comparison_to_json(comparison))
    assert len(parsed["entries"]) == 2


def _sample_batch(sample_trace_dict, sample_trace_reflective_dict):
    return analyze_batch(
        [
            ("baseline", ExecutionTrace.from_dict(sample_trace_dict)),
            ("reflective", ExecutionTrace.from_dict(sample_trace_reflective_dict)),
        ]
    )


def test_render_batch_text_contains_key_sections(
    sample_trace_dict, sample_trace_reflective_dict
):
    summary = _sample_batch(sample_trace_dict, sample_trace_reflective_dict)
    output = render_batch_text(summary)

    assert "Batch Analysis (2 traces)" in output
    assert "Success Rate: 50.0% (1/2)" in output
    assert "Avg Duration" in output
    assert "Avg Tokens" in output
    assert "Avg Cost" in output
    assert "Issue Frequency:" in output
    assert "cost_concentration: 2" in output
    assert "Per-Trace Summary:" in output
    assert "- baseline: FAIL" in output
    assert "- reflective: PASS" in output


def test_render_batch_text_empty():
    from tracelens.models.review import BatchSummary

    summary = BatchSummary(
        entries=(),
        success_rate=0.0,
        avg_duration_ms=0.0,
        avg_tokens=0.0,
        avg_cost=0.0,
        issue_counts={},
    )
    output = render_batch_text(summary)
    assert "Batch Analysis (0 traces)" in output
    assert "No trace files found." in output


def test_batch_to_dict_round_trips_key_fields(sample_trace_dict, sample_trace_reflective_dict):
    summary = _sample_batch(sample_trace_dict, sample_trace_reflective_dict)
    data = batch_to_dict(summary)

    assert data["trace_count"] == 2
    assert data["success_count"] == 1
    assert data["success_rate"] == summary.success_rate
    assert data["issue_counts"]["cost_concentration"] == 2
    assert [entry["label"] for entry in data["entries"]] == ["baseline", "reflective"]


def test_batch_to_json_is_valid_json(sample_trace_dict, sample_trace_reflective_dict):
    summary = _sample_batch(sample_trace_dict, sample_trace_reflective_dict)
    parsed = json.loads(batch_to_json(summary))
    assert parsed["trace_count"] == 2
