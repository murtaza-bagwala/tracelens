from tracelens.analyzer.engine import AnalyzerConfig, analyze_trace
from tracelens.models.trace import ExecutionTrace


def test_analyze_trace_sample_end_to_end(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    review = analyze_trace(trace)

    assert review.task == "Recommend a travel insurance policy"
    assert review.statistics.total_duration_ms == 1150.0

    categories = {issue.category for issue in review.issues}
    assert "low_retrieval_documents" in categories
    assert "latency_bottleneck" in categories
    assert "token_concentration" in categories
    assert "cost_concentration" in categories
    assert "failure" in categories

    # The failure should correlate with the retrieval issue found earlier.
    failure_issue = next(i for i in review.issues if i.category == "failure")
    assert failure_issue.step_name == "retrieve_policy"

    suggestion_categories = {s.category for s in review.suggestions}
    assert suggestion_categories == categories


def test_analyze_trace_clean_success_no_issues():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "a", "type": "llm", "duration_ms": 1000, "tokens": 100},
                {"name": "b_llm", "type": "llm", "duration_ms": 100, "tokens": 100},
                {"name": "c_llm", "type": "llm", "duration_ms": 100, "tokens": 100},
                {
                    "name": "b",
                    "type": "retrieval",
                    "duration_ms": 50,
                    "documents_found": 5,
                },
            ],
            "success": True,
        }
    )
    review = analyze_trace(trace)
    assert review.issues == ()
    assert review.suggestions == ()


def test_analyze_trace_respects_custom_config():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "llm_step", "type": "llm", "duration_ms": 1000, "tokens": 100},
                {
                    "name": "r",
                    "type": "retrieval",
                    "duration_ms": 10,
                    "documents_found": 4,
                },
            ],
        }
    )
    default_review = analyze_trace(trace)
    assert default_review.issues == ()

    strict_review = analyze_trace(trace, AnalyzerConfig(min_documents=5))
    assert len(strict_review.issues) == 1
    assert strict_review.issues[0].category == "low_retrieval_documents"
