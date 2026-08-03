from tracelens.analyzer.cost import detect_cost_concentration
from tracelens.models.trace import ExecutionTrace


def test_flags_dominant_cost_step():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "llm", "cost": 0.001},
                {"name": "call_pricing_api", "type": "tool", "cost": 0.01},
            ],
        }
    )
    issues = detect_cost_concentration(trace)

    assert len(issues) == 1
    assert issues[0].step_name == "call_pricing_api"
    assert issues[0].category == "cost_concentration"
    assert "91%" in issues[0].message


def test_no_costed_steps_no_issue():
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "a", "type": "tool", "duration_ms": 10}]}
    )
    assert detect_cost_concentration(trace) == []


def test_evenly_split_cost_no_issue():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "llm", "cost": 0.01},
                {"name": "b", "type": "llm", "cost": 0.01},
                {"name": "c", "type": "llm", "cost": 0.01},
            ],
        }
    )
    assert detect_cost_concentration(trace) == []


def test_single_costed_step_no_issue():
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "a", "type": "llm", "cost": 0.05}]}
    )
    assert detect_cost_concentration(trace) == []


def test_custom_threshold():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "llm", "cost": 0.06},
                {"name": "b", "type": "llm", "cost": 0.04},
            ],
        }
    )
    assert detect_cost_concentration(trace, threshold=0.7) == []
    issues = detect_cost_concentration(trace, threshold=0.5)
    assert len(issues) == 1
    assert issues[0].step_name == "a"
