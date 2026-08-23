"""Executes one configured reasoning loop over one dataset row, producing a
plain ExecutionTrace — the same shape the existing analyzer already reads
from hand-authored trace JSON, so nothing downstream needs to change."""

from __future__ import annotations

from typing import Optional

from tracelens.models.dataset import DatasetRow
from tracelens.models.loop_config import LoopConfig
from tracelens.models.trace import ExecutionTrace, Step
from tracelens.runtime.evaluator import DEFAULT_PASS_THRESHOLD, KeywordOverlapEvaluator
from tracelens.runtime.executor import RagExecutor, SingleCallExecutor
from tracelens.runtime.model_client import MockModelClient, ModelClient
from tracelens.runtime.node import LoopContext, LoopNode, NodeResult
from tracelens.runtime.planner import MockPlanner
from tracelens.runtime.reflection import MockReflection


def _build_planner(config: LoopConfig, client: ModelClient) -> Optional[LoopNode]:
    node_type = config.planner.get("type", "none")
    if node_type == "none":
        return None
    if node_type == "llm":
        return MockPlanner(client)
    raise ValueError(f"Unknown planner type '{node_type}'")


def _build_executor(config: LoopConfig, client: ModelClient) -> LoopNode:
    node_type = config.executor.get("type", "single_call")
    if node_type == "single_call":
        return SingleCallExecutor(client)
    if node_type == "rag":
        return RagExecutor(client)
    raise ValueError(f"Unknown executor type '{node_type}'")


def _build_evaluator(config: LoopConfig, client: ModelClient) -> LoopNode:
    node_type = config.evaluator.get("type", "keyword_overlap")
    if node_type == "keyword_overlap":
        threshold = config.evaluator.get("pass_threshold", DEFAULT_PASS_THRESHOLD)
        return KeywordOverlapEvaluator(client, pass_threshold=threshold)
    raise ValueError(f"Unknown evaluator type '{node_type}'")


def _build_reflection(config: LoopConfig, client: ModelClient) -> Optional[LoopNode]:
    return MockReflection(client) if config.reflection.get("enabled", False) else None


def _to_step(node: LoopNode, result: NodeResult, attempt: int) -> Step:
    return Step(
        name=node.name,
        type=node.step_type,
        duration_ms=result.latency_ms,
        tokens=(result.tokens_in + result.tokens_out) or None,
        cost=result.cost or None,
        documents_found=result.documents_found,
        output=result.output,
        error=result.error,
        extra={
            "attempt": attempt,
            "decision": result.decision,
            "reason": result.reason,
            **result.metadata,
        },
    )


def run_loop(row: DatasetRow, config: LoopConfig, client: Optional[ModelClient] = None) -> ExecutionTrace:
    """Run one dataset row through one loop config, retrying (and, if
    enabled, reflecting) until the evaluator passes or the retry budget is
    exhausted. Restarts from the planner each retry, so a critique can
    correct a bad plan, not just a bad answer."""

    client = client or MockModelClient()
    planner = _build_planner(config, client)
    executor = _build_executor(config, client)
    evaluator = _build_evaluator(config, client)
    reflection = _build_reflection(config, client)

    ctx = LoopContext(task=row.input, reference=row.reference, context=row.context)
    steps: list[Step] = []
    max_attempts = config.retries + 1
    final_result: Optional[NodeResult] = None

    for attempt in range(1, max_attempts + 1):
        ctx.attempt = attempt

        if planner is not None:
            planner_result = planner.run(ctx)
            steps.append(_to_step(planner, planner_result, attempt))
            ctx.plan = planner_result.output

        executor_result = executor.run(ctx)
        steps.append(_to_step(executor, executor_result, attempt))
        ctx.draft_answer = executor_result.output

        eval_result = evaluator.run(ctx)
        steps.append(_to_step(evaluator, eval_result, attempt))
        final_result = eval_result

        if eval_result.decision == "pass":
            break

        ctx.missing_keywords = tuple(eval_result.metadata.get("missing_keywords", ()))

        if attempt < max_attempts and reflection is not None:
            reflect_result = reflection.run(ctx)
            steps.append(_to_step(reflection, reflect_result, attempt))
            ctx.critique = reflect_result.output

    success = final_result.decision == "pass"
    error = None if success else final_result.reason

    return ExecutionTrace(task=row.input, steps=tuple(steps), success=success, error=error)
