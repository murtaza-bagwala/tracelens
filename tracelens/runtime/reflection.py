"""Reflection node: turns the evaluator's verdict into a concrete critique
the executor can act on next attempt."""

from __future__ import annotations

from tracelens.runtime.model_client import ModelClient
from tracelens.runtime.node import LoopContext, NodeResult


class MockReflection:
    """Deterministic critique built directly from the evaluator's missing
    reference terms — a legible stand-in for a real self-critique step."""

    name = "reflect"
    step_type = "llm"

    def __init__(self, client: ModelClient) -> None:
        self.client = client

    def run(self, ctx: LoopContext) -> NodeResult:
        if ctx.missing_keywords:
            critique = f"Include these terms: {', '.join(ctx.missing_keywords)}"
        else:
            critique = "Revise the answer for clarity and completeness."

        response = self.client.complete(critique)

        return NodeResult(
            output=critique,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost=response.cost,
            latency_ms=response.latency_ms,
        )
