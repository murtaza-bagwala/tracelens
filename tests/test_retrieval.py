from tracelens.analyzer.retrieval import detect_retrieval_issues
from tracelens.models.trace import ExecutionTrace


def test_flags_low_document_count(sample_trace_dict):
    trace = ExecutionTrace.from_dict(sample_trace_dict)
    issues = detect_retrieval_issues(trace)

    assert len(issues) == 1
    assert issues[0].step_name == "retrieve_policy"
    assert issues[0].category == "low_retrieval_documents"
    assert "2 document" in issues[0].message


def test_sufficient_documents_no_issue():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "r", "type": "retrieval", "documents_found": 5, "duration_ms": 10}
            ],
        }
    )
    assert detect_retrieval_issues(trace) == []


def test_missing_documents_found_no_issue():
    trace = ExecutionTrace.from_dict(
        {"task": "t", "steps": [{"name": "r", "type": "retrieval", "duration_ms": 10}]}
    )
    assert detect_retrieval_issues(trace) == []


def test_custom_min_documents():
    trace = ExecutionTrace.from_dict(
        {
            "task": "t",
            "steps": [
                {"name": "r", "type": "retrieval", "documents_found": 4, "duration_ms": 10}
            ],
        }
    )
    assert detect_retrieval_issues(trace, min_documents=3) == []
    issues = detect_retrieval_issues(trace, min_documents=5)
    assert len(issues) == 1
