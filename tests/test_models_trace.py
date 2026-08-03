import pytest

from tracelens.models.trace import ExecutionTrace, Step


def test_step_from_dict_full():
    step = Step.from_dict(
        {
            "name": "intent_detection",
            "type": "llm",
            "input": "hi",
            "output": "bye",
            "duration_ms": 120,
            "tokens": 350,
        }
    )
    assert step.name == "intent_detection"
    assert step.type == "llm"
    assert step.duration_ms == 120.0
    assert step.tokens == 350
    assert step.documents_found is None
    assert step.error is None


def test_step_from_dict_minimal_defaults():
    step = Step.from_dict({"name": "call_tool", "type": "tool"})
    assert step.duration_ms == 0.0
    assert step.tokens is None
    assert step.documents_found is None
    assert step.extra == {}


def test_step_from_dict_captures_extra_fields():
    step = Step.from_dict({"name": "x", "type": "tool", "retry_count": 2})
    assert step.extra == {"retry_count": 2}


def test_step_from_dict_missing_name_raises():
    with pytest.raises(ValueError, match="name"):
        Step.from_dict({"type": "llm"})


def test_step_from_dict_missing_type_raises():
    with pytest.raises(ValueError, match="type"):
        Step.from_dict({"name": "x"})


def test_execution_trace_from_dict(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    assert trace.task == "Recommend a travel insurance policy"
    assert len(trace.steps) == 4
    assert trace.success is False
    assert trace.error == "Incorrect policy recommendation"


def test_execution_trace_defaults_success_true():
    trace = ExecutionTrace.from_dict({"task": "t", "steps": []})
    assert trace.success is True
    assert trace.error is None


def test_execution_trace_missing_steps_raises():
    with pytest.raises(ValueError, match="steps"):
        ExecutionTrace.from_dict({"task": "t"})


def test_execution_trace_from_json(sample_trace_dict):
    import json

    trace = ExecutionTrace.from_json(json.dumps(sample_trace_dict))
    assert trace.task == sample_trace_dict["task"]


def test_execution_trace_load(tmp_path, sample_trace_dict):
    import json

    path = tmp_path / "trace.json"
    path.write_text(json.dumps(sample_trace_dict))
    trace = ExecutionTrace.load(path)
    assert len(trace.steps) == 4
