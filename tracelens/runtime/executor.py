"""Executor node: produces the draft answer. Two variants model the two
architectures DESIGN.md's worked example compares: a bare single LLM call
with no grounding, and a retrieval-grounded ("RAG") call."""

from __future__ import annotations

from tracelens.runtime.model_client import ModelClient
from tracelens.runtime.node import LoopContext, NodeResult

_NO_GROUNDING_ANSWER = (
    "I don't have enough information to answer this precisely — "
    "please consult the relevant documentation."
)


class SingleCallExecutor:
    """Answers from the task alone, with no retrieved context — models a
    bare single-LLM-call architecture that can't ground specific facts."""

    name = "executor"
    step_type = "llm"

    def __init__(self, client: ModelClient) -> None:
        self.client = client

    def run(self, ctx: LoopContext) -> NodeResult:
        prompt = ctx.task + (f"\n{ctx.critique}" if ctx.critique else "")
        response = self.client.complete(prompt)

        output = _NO_GROUNDING_ANSWER
        if ctx.critique:
            output = f"{output} {ctx.critique}"

        return NodeResult(
            output=output,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost=response.cost,
            latency_ms=response.latency_ms,
        )


class RagExecutor:
    """Retrieves the dataset row's supporting context and answers from it —
    models a retrieval-grounded architecture. If a reflection critique is
    present (from a prior failed attempt), it's folded in too."""

    name = "executor"
    step_type = "retrieval"

    def __init__(self, client: ModelClient) -> None:
        self.client = client

    def run(self, ctx: LoopContext) -> NodeResult:
        prompt = f"{ctx.task}\n{ctx.context}" + (f"\n{ctx.critique}" if ctx.critique else "")
        response = self.client.complete(prompt)

        parts = [part for part in (ctx.context, ctx.critique) if part]
        output = " ".join(parts) if parts else "No relevant information found."

        return NodeResult(
            output=output,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost=response.cost,
            latency_ms=response.latency_ms,
            documents_found=1 if ctx.context else 0,
        )
