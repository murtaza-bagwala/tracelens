"""Evaluator node: scores a draft answer against the dataset row's reference
answer. Mock mode has no real LLM judge, so it uses keyword overlap — a
legible, deterministic, and honestly-limited stand-in for a real judge."""

from __future__ import annotations

import re

from tracelens.runtime.model_client import ModelClient
from tracelens.runtime.node import LoopContext, NodeResult

DEFAULT_PASS_THRESHOLD = 0.6

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS = frozenset(
    """
    a an the this that these those i you he she it we they what which who
    whom and but or if of in on at by for with about against between into
    through during before after above below to from up down off over under
    again further then once here there when where why how all any both
    each few more most other some such no nor not only own same so than
    too very can could may might must shall should will would do does did
    is are was were be been being have has had our your their its my
    within per us
    """.split()
)


def _content_tokens(text: str) -> set[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return {token for token in tokens if token not in _STOPWORDS and len(token) > 2}


class KeywordOverlapEvaluator:
    """Passes an answer when it covers enough of the reference's content
    words. Swappable later for a real LLM-judge without touching the loop."""

    name = "evaluator"
    step_type = "llm"

    def __init__(self, client: ModelClient, pass_threshold: float = DEFAULT_PASS_THRESHOLD) -> None:
        self.client = client
        self.pass_threshold = pass_threshold

    def run(self, ctx: LoopContext) -> NodeResult:
        response = self.client.complete(ctx.draft_answer + ctx.reference)

        reference_tokens = _content_tokens(ctx.reference)
        answer_tokens = _content_tokens(ctx.draft_answer)

        if not reference_tokens:
            score = 1.0
            missing: list[str] = []
        else:
            missing = sorted(reference_tokens - answer_tokens)
            score = (len(reference_tokens) - len(missing)) / len(reference_tokens)

        passed = score >= self.pass_threshold
        reason = (
            None
            if passed
            else f"answer covered {score:.0%} of expected reference terms; missing: {', '.join(missing)}"
        )

        return NodeResult(
            output=f"score={score:.2f}",
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost=response.cost,
            latency_ms=response.latency_ms,
            decision="pass" if passed else "fail",
            reason=reason,
            metadata={"score": score, "missing_keywords": missing},
        )
