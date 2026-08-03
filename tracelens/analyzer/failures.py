"""Detect repeated/retried steps, per-step errors, and overall task failure."""

from __future__ import annotations

from collections import Counter

from tracelens.models.review import Issue
from tracelens.models.trace import ExecutionTrace


def detect_repeated_steps(trace: ExecutionTrace) -> list[Issue]:
    """Flag step names that appear more than once (a common retry-loop signature)."""
    counts = Counter(step.name for step in trace.steps)
    issues = []
    for name, count in counts.items():
        if count > 1:
            issues.append(
                Issue(
                    category="repeated_step",
                    message=(
                        f"'{name}' step executed {count} times "
                        "— possible retry loop or unstable step."
                    ),
                    step_name=name,
                    severity="warning",
                )
            )
    return issues


def detect_step_errors(trace: ExecutionTrace) -> list[Issue]:
    """Flag individual steps that reported their own error, independent of overall success."""
    issues = []
    for step in trace.steps:
        if step.error:
            issues.append(
                Issue(
                    category="step_error",
                    message=f"'{step.name}' step reported an error: {step.error}",
                    step_name=step.name,
                    severity="critical",
                )
            )
    return issues


def detect_failure(trace: ExecutionTrace, prior_issues: list[Issue]) -> list[Issue]:
    """If the overall task failed, report it and, if possible, correlate it with an
    earlier step that was already flagged by another detector."""
    if trace.success:
        return []

    flagged_step_names = {issue.step_name for issue in prior_issues if issue.step_name}

    correlated_step_name = None
    for step in trace.steps:
        if step.name in flagged_step_names:
            correlated_step_name = step.name
            break

    error_text = trace.error or "no error message provided"
    if correlated_step_name:
        message = (
            f"Failure occurred after the '{correlated_step_name}' step "
            f"(error: {error_text}), which was already flagged above as a "
            "potential issue."
        )
    else:
        message = f"Task failed: {error_text}"

    return [
        Issue(
            category="failure",
            message=message,
            step_name=correlated_step_name,
            severity="critical",
        )
    ]
