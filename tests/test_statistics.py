import pytest

from tracelens.analyzer.statistics import compute_statistics
from tracelens.models.trace import ExecutionTrace


def test_compute_statistics_sample(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    stats = compute_statistics(trace)

    assert stats.total_duration_ms == 1150.0
    assert stats.total_duration_seconds == pytest.approx(1.15)
    assert stats.step_count == 4
    assert stats.llm_calls == 2
    assert stats.tool_calls == 1
    assert stats.retrieval_calls == 1
    assert stats.other_calls == 0
    assert stats.total_tokens == 1250
    assert stats.total_cost == pytest.approx(0.0127)
    assert stats.success is False


def test_compute_statistics_empty_trace():
    trace = ExecutionTrace.from_dict({"task": "t", "steps": []})
    stats = compute_statistics(trace)
    assert stats.total_duration_ms == 0.0
    assert stats.step_count == 0
    assert stats.total_tokens == 0
    assert stats.total_cost == 0.0
    assert stats.success is True


def test_compute_statistics_counts_unknown_step_types():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [{"name": "custom", "type": "planner", "duration_ms": 10}],
        }
    )
    stats = compute_statistics(trace)
    assert stats.other_calls == 1
    assert stats.llm_calls == 0
