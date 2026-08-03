"""Map detected issues to actionable architecture suggestions."""

from __future__ import annotations

from tracelens.models.review import Issue, Suggestion

_TEMPLATES = {
    "low_retrieval_documents": lambda issue: (
        f"Experiment with hybrid retrieval or increase retrieval depth "
        f"for '{issue.step_name}'."
    ),
    "latency_bottleneck": lambda issue: (
        f"Cache or parallelize the '{issue.step_name}' step to reduce latency."
    ),
    "token_concentration": lambda issue: (
        f"Add an evaluator step after '{issue.step_name}' to verify output "
        "quality before returning."
    ),
    "cost_concentration": lambda issue: (
        f"'{issue.step_name}' drives most of the run's cost — consider a "
        "cheaper model, a cheaper tool/provider, or caching for this step."
    ),
    "repeated_step": lambda issue: (
        f"Investigate why '{issue.step_name}' required multiple attempts; "
        "add backoff or circuit-breaking."
    ),
    "step_error": lambda issue: (
        f"Add error handling or a fallback path around the '{issue.step_name}' step."
    ),
    "failure": lambda issue: (
        "Add a reflection or self-check step before returning the final "
        "answer to catch issues like this earlier."
    ),
}


def build_suggestions(issues: list[Issue]) -> list[Suggestion]:
    """One suggestion per (category, step) pair, in the order issues were found."""
    suggestions = []
    seen = set()
    for issue in issues:
        template = _TEMPLATES.get(issue.category)
        if template is None:
            continue
        key = (issue.category, issue.step_name)
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(Suggestion(category=issue.category, message=template(issue)))
    return suggestions
