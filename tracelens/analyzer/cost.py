"""Detect a single step consuming a disproportionate share of total cost."""

from __future__ import annotations

from tracelens.models.review import Issue
from tracelens.models.trace import ExecutionTrace

DEFAULT_COST_THRESHOLD = 0.5


def detect_cost_concentration(
    trace: ExecutionTrace,
    threshold: float = DEFAULT_COST_THRESHOLD,
) -> list[Issue]:
    costed_steps = [step for step in trace.steps if step.cost]
    if len(costed_steps) < 2:
        # Nothing to compare against — a single costed step trivially accounts
        # for 100% of cost, which isn't a meaningful concentration signal.
        return []

    total_cost = sum(step.cost for step in costed_steps)
    if total_cost <= 0:
        return []

    heaviest = max(costed_steps, key=lambda step: step.cost)
    share = heaviest.cost / total_cost
    if share < threshold:
        return []

    pct = round(share * 100)
    return [
        Issue(
            category="cost_concentration",
            message=(
                f"'{heaviest.name}' step accounted for {pct}% of total cost "
                f"(${heaviest.cost:.4f})."
            ),
            step_name=heaviest.name,
            severity="info",
        )
    ]
