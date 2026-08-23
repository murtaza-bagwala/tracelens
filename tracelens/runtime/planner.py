"""Planner node: sketches an approach before the executor answers."""

from __future__ import annotations

from tracelens.runtime.model_client import ModelClient
from tracelens.runtime.node import LoopContext, NodeResult


class MockPlanner:
    """Deterministic stand-in for an LLM planning step. Its exact wording
    doesn't affect the executor's answer content (the mock executor derives
    that from dataset context, not from plan text) — it exists to add a
    realistic planning step with its own cost/latency to the trace."""

    name = "planner"
    step_type = "llm"

    def __init__(self, client: ModelClient) -> None:
        self.client = client

    def run(self, ctx: LoopContext) -> NodeResult:
        prompt = f"Plan how to answer: {ctx.task}"
        if ctx.critique:
            prompt += f"\nPrevious attempt was revised because: {ctx.critique}"

        response = self.client.complete(prompt)
        output = f"Plan: gather information relevant to '{ctx.task}' and answer directly."

        return NodeResult(
            output=output,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost=response.cost,
            latency_ms=response.latency_ms,
        )
