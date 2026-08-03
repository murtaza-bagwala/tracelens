import pytest

from tracelens.analyzer.batch import analyze_batch
from tracelens.models.trace import ExecutionTrace


def _traces(sample_trace_dict, sample_trace_reflective_dict):
    return [
        ("baseline", ExecutionTrace.from_dict(sample_trace_dict)),
        ("reflective", ExecutionTrace.from_dict(sample_trace_reflective_dict)),
    ]


def test_analyze_batch_preserves_order_and_labels(
    sample_trace_dict, sample_trace_reflective_dict
):
    summary = analyze_batch(_traces(sample_trace_dict, sample_trace_reflective_dict))

    assert [entry.label for entry in summary.entries] == ["baseline", "reflective"]


def test_analyze_batch_success_rate(sample_trace_dict, sample_trace_reflective_dict):
    summary = analyze_batch(_traces(sample_trace_dict, sample_trace_reflective_dict))

    # baseline fails, reflective succeeds -> 1/2.
    assert summary.success_rate == pytest.approx(0.5)


def test_analyze_batch_averages(sample_trace_dict, sample_trace_reflective_dict):
    summary = analyze_batch(_traces(sample_trace_dict, sample_trace_reflective_dict))

    assert summary.avg_duration_ms == pytest.approx((1150.0 + 1900.0) / 2)
    assert summary.avg_tokens == pytest.approx((1250 + 2250) / 2)
    assert summary.avg_cost == pytest.approx((0.0127 + 0.0147) / 2)


def test_analyze_batch_issue_counts(sample_trace_dict, sample_trace_reflective_dict):
    summary = analyze_batch(_traces(sample_trace_dict, sample_trace_reflective_dict))

    # baseline hits low_retrieval_documents, latency_bottleneck, token_concentration,
    # cost_concentration, failure; reflective only hits cost_concentration.
    assert summary.issue_counts["cost_concentration"] == 2
    assert summary.issue_counts["failure"] == 1
    assert summary.issue_counts["low_retrieval_documents"] == 1


def test_analyze_batch_empty_list():
    summary = analyze_batch([])

    assert summary.entries == ()
    assert summary.success_rate == 0.0
    assert summary.avg_duration_ms == 0.0
    assert summary.avg_tokens == 0.0
    assert summary.avg_cost == 0.0
    assert summary.issue_counts == {}
