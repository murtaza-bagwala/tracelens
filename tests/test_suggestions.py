from tracelens.analyzer.suggestions import build_suggestions
from tracelens.models.review import Issue


def test_maps_known_categories_to_suggestions():
    issues = [
        Issue(category="low_retrieval_documents", message="m", step_name="retrieve"),
        Issue(category="latency_bottleneck", message="m", step_name="call_api"),
    ]
    suggestions = build_suggestions(issues)
    assert len(suggestions) == 2
    assert "retrieve" in suggestions[0].message
    assert "call_api" in suggestions[1].message


def test_unknown_category_produces_no_suggestion():
    issues = [Issue(category="mystery_category", message="m", step_name="x")]
    assert build_suggestions(issues) == []


def test_deduplicates_same_category_and_step():
    issues = [
        Issue(category="repeated_step", message="m1", step_name="x"),
        Issue(category="repeated_step", message="m2", step_name="x"),
    ]
    suggestions = build_suggestions(issues)
    assert len(suggestions) == 1


def test_distinct_steps_same_category_both_kept():
    issues = [
        Issue(category="repeated_step", message="m1", step_name="x"),
        Issue(category="repeated_step", message="m2", step_name="y"),
    ]
    suggestions = build_suggestions(issues)
    assert len(suggestions) == 2
