from tracelens.analyzer.bottlenecks import detect_latency_bottlenecks
from tracelens.models.trace import ExecutionTrace


def test_flags_dominant_tool_step(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    issues = detect_latency_bottlenecks(trace, total_duration_ms=1150.0)

    assert len(issues) == 1
    assert issues[0].step_name == "call_pricing_api"
    assert issues[0].category == "latency_bottleneck"
    assert "39%" in issues[0].message


def test_ignores_llm_steps_even_if_slowest():
    # generate_recommendation (500ms) is slower than call_pricing_api (450ms)
    # but LLM latency isn't something caching/parallelizing fixes, so only
    # the tool/retrieval step should be flagged.
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "call_pricing_api", "type": "tool", "duration_ms": 450},
                {"name": "generate_recommendation", "type": "llm", "duration_ms": 500},
            ],
        }
    )
    issues = detect_latency_bottlenecks(trace, total_duration_ms=950.0)
    assert len(issues) == 1
    assert issues[0].step_name == "call_pricing_api"


def test_below_threshold_no_issue():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "tool", "duration_ms": 10},
                {"name": "b", "type": "llm", "duration_ms": 990},
            ],
        }
    )
    issues = detect_latency_bottlenecks(trace, total_duration_ms=1000.0)
    assert issues == []


def test_zero_total_duration_no_issue():
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "a", "type": "tool", "duration_ms": 0}]}
    )
    issues = detect_latency_bottlenecks(trace, total_duration_ms=0.0)
    assert issues == []


def test_custom_threshold():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [{"name": "a", "type": "tool", "duration_ms": 200}],
        }
    )
    # 200/1000 = 20%, below default 30% threshold, above a custom 10% threshold
    assert detect_latency_bottlenecks(trace, 1000.0) == []
    issues = detect_latency_bottlenecks(trace, 1000.0, threshold=0.1)
    assert len(issues) == 1
