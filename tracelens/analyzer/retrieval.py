"""Detect retrieval steps that returned too few documents."""

from __future__ import annotations

from tracelens.models.review import Issue
from tracelens.models.trace import ExecutionTrace

DEFAULT_MIN_DOCUMENTS = 3


def detect_retrieval_issues(
    trace: ExecutionTrace,
    min_documents: int = DEFAULT_MIN_DOCUMENTS,
) -> list[Issue]:
    issues = []
    for step in trace.steps:
        if step.type != "retrieval" or step.documents_found is None:
            continue
        if step.documents_found < min_documents:
            issues.append(
                Issue(
                    category="low_retrieval_documents",
                    message=(
                        f"'{step.name}' step returned only "
                        f"{step.documents_found} document(s)."
                    ),
                    step_name=step.name,
                    severity="warning",
                )
            )
    return issues
