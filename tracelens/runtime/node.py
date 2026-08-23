"""Shared types for loop nodes: the minimal contract a planner/executor/
evaluator/reflection node implements."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass(frozen=True)
class NodeResult:
    """What a node reports after one run: its output plus cost/latency
    accounting and, for an evaluator, a pass/fail decision."""

    output: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    documents_found: Optional[int] = None
    decision: str = "ok"  # "ok" | "pass" | "fail" (evaluator only)
    reason: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class LoopContext:
    """Mutable state threaded through one dataset row's loop execution."""

    task: str
    reference: str
    context: str = ""
    attempt: int = 1
    plan: str = ""
    draft_answer: str = ""
    critique: str = ""
    # Reference terms the evaluator's last verdict found missing from the
    # answer; set by the loop runner after each evaluator run, consumed by
    # the reflection node to build a concrete critique.
    missing_keywords: tuple = ()


class LoopNode(Protocol):
    """The contract every planner/executor/evaluator/reflection node implements."""

    name: str
    step_type: str  # "llm" | "tool" | "retrieval" | "other" -> maps to Step.type

    def run(self, ctx: LoopContext) -> NodeResult: ...
