"""Detect a single LLM step consuming a disproportionate share of tokens."""

from __future__ import annotations

from tracelens.models.review import Issue
from tracelens.models.trace import ExecutionTrace

DEFAULT_TOKEN_THRESHOLD = 0.5


def detect_token_concentration(
    trace: ExecutionTrace,
    threshold: float = DEFAULT_TOKEN_THRESHOLD,
) -> list[Issue]:
    llm_steps = [step for step in trace.steps if step.type == "llm" and step.tokens]
    if len(llm_steps) < 2:
        # Nothing to compare against — a single LLM step trivially "consumes"
        # 100% of tokens, which isn't a meaningful concentration signal.
        return []

    total_tokens = sum(step.tokens for step in llm_steps)
    if total_tokens <= 0:
        return []

    heaviest = max(llm_steps, key=lambda step: step.tokens)
    share = heaviest.tokens / total_tokens
    if share < threshold:
        return []

    pct = round(share * 100)
    return [
        Issue(
            category="token_concentration",
            message=(
                f"'{heaviest.name}' step consumed {pct}% of total tokens "
                f"({heaviest.tokens} tokens)."
            ),
            step_name=heaviest.name,
            severity="info",
        )
    ]
