"""Compute aggregate statistics from an execution trace."""

from __future__ import annotations

from tracelens.models.review import Statistics
from tracelens.models.trace import ExecutionTrace


def compute_statistics(trace: ExecutionTrace) -> Statistics:
    llm_calls = tool_calls = retrieval_calls = other_calls = 0
    total_duration_ms = 0.0
    total_tokens = 0
    total_cost = 0.0

    for step in trace.steps:
        total_duration_ms += step.duration_ms
        if step.tokens:
            total_tokens += step.tokens
        if step.cost:
            total_cost += step.cost

        if step.type == "llm":
            llm_calls += 1
        elif step.type == "tool":
            tool_calls += 1
        elif step.type == "retrieval":
            retrieval_calls += 1
        else:
            other_calls += 1

    return Statistics(
        total_duration_ms=total_duration_ms,
        step_count=len(trace.steps),
        llm_calls=llm_calls,
        tool_calls=tool_calls,
        retrieval_calls=retrieval_calls,
        other_calls=other_calls,
        total_tokens=total_tokens,
        success=trace.success,
        total_cost=total_cost,
    )
