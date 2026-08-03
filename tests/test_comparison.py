from tracelens.analyzer.comparison import compare_traces
from tracelens.models.trace import ExecutionTrace


def _traces(sample_trace_dict, sample_trace_reflective_dict):
    return [
        ("baseline", ExecutionTrace.from_dict(sample_trace_dict)),
        ("reflective", ExecutionTrace.from_dict(sample_trace_reflective_dict)),
    ]


def test_compare_traces_preserves_order_and_labels(
    sample_trace_dict, sample_trace_reflective_dict
):
    comparison = compare_traces(_traces(sample_trace_dict, sample_trace_reflective_dict))

    assert [entry.label for entry in comparison.entries] == ["baseline", "reflective"]


def test_compare_traces_picks_best_per_metric(
    sample_trace_dict, sample_trace_reflective_dict
):
    comparison = compare_traces(_traces(sample_trace_dict, sample_trace_reflective_dict))

    # baseline fails and hits more detectors; reflective succeeds and is clean,
    # at the cost of more tokens and latency.
    assert comparison.best["success"] == "reflective"
    assert comparison.best["issue_count"] == "reflective"
    assert comparison.best["duration_ms"] == "baseline"
    assert comparison.best["total_tokens"] == "baseline"
    assert comparison.best["total_cost"] == "baseline"


def test_compare_traces_reports_tie_as_none(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    comparison = compare_traces([("a", trace), ("b", trace)])

    assert comparison.best["duration_ms"] is None
    assert comparison.best["total_tokens"] is None
    assert comparison.best["total_cost"] is None
    assert comparison.best["issue_count"] is None
    assert comparison.best["success"] is None


def test_compare_traces_single_entry_wins_trivially(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    comparison = compare_traces([("only", trace)])

    assert len(comparison.entries) == 1
    assert comparison.best["duration_ms"] == "only"
