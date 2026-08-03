from tracelens.analyzer.failures import (
    detect_failure,
    detect_repeated_steps,
    detect_step_errors,
)
from tracelens.models.review import Issue
from tracelens.models.trace import ExecutionTrace


def test_detect_repeated_steps():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "call_llm", "type": "llm", "duration_ms": 10},
                {"name": "call_llm", "type": "llm", "duration_ms": 10},
                {"name": "call_llm", "type": "llm", "duration_ms": 10},
                {"name": "call_tool", "type": "tool", "duration_ms": 10},
            ],
        }
    )
    issues = detect_repeated_steps(trace)
    assert len(issues) == 1
    assert issues[0].step_name == "call_llm"
    assert "3 times" in issues[0].message


def test_detect_repeated_steps_none():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [{"name": "a", "type": "llm"}, {"name": "b", "type": "tool"}],
        }
    )
    assert detect_repeated_steps(trace) == []


def test_detect_step_errors():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "tool", "error": "timeout"},
                {"name": "b", "type": "llm"},
            ],
        }
    )
    issues = detect_step_errors(trace)
    assert len(issues) == 1
    assert issues[0].step_name == "a"
    assert "timeout" in issues[0].message


def test_detect_failure_success_no_issue():
    trace = ExecutionTrace.from_dict({"task": "t", "steps": [], "success": True})
    assert detect_failure(trace, prior_issues=[]) == []


def test_detect_failure_no_correlation():
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "a", "type": "llm"}], "success": False, "error": "boom"}
    )
    issues = detect_failure(trace, prior_issues=[])
    assert len(issues) == 1
    assert issues[0].step_name is None
    assert "Task failed: boom" in issues[0].message


def test_detect_failure_with_correlation(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    prior = [
        Issue(
            category="low_retrieval_documents",
            message="'retrieve_policy' step returned only 2 document(s).",
            step_name="retrieve_policy",
        )
    ]
    issues = detect_failure(trace, prior_issues=prior)
    assert len(issues) == 1
    assert issues[0].step_name == "retrieve_policy"
    assert "retrieve_policy" in issues[0].message
    assert "Incorrect policy recommendation" in issues[0].message
