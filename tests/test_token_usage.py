from tracelens.analyzer.token_usage import detect_token_concentration
from tracelens.models.trace import ExecutionTrace


def test_flags_dominant_token_step(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    issues = detect_token_concentration(trace)

    assert len(issues) == 1
    assert issues[0].step_name == "generate_recommendation"
    assert issues[0].category == "token_concentration"
    assert "72%" in issues[0].message


def test_no_llm_steps_no_issue():
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "a", "type": "tool", "duration_ms": 10}]}
    )
    assert detect_token_concentration(trace) == []


def test_evenly_split_tokens_no_issue():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "llm", "tokens": 100},
                {"name": "b", "type": "llm", "tokens": 100},
                {"name": "c", "type": "llm", "tokens": 100},
            ],
        }
    )
    assert detect_token_concentration(trace) == []


def test_single_llm_step_no_issue():
    # A lone LLM step trivially "consumes" 100% of tokens — not meaningful
    # without another step to compare against.
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "a", "type": "llm", "tokens": 900}]}
    )
    assert detect_token_concentration(trace) == []


def test_custom_threshold():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "llm", "tokens": 60},
                {"name": "b", "type": "llm", "tokens": 40},
            ],
        }
    )
    assert detect_token_concentration(trace, threshold=0.7) == []
    issues = detect_token_concentration(trace, threshold=0.5)
    assert len(issues) == 1
    assert issues[0].step_name == "a"
