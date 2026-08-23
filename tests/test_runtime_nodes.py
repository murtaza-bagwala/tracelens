from tracelens.runtime.evaluator import KeywordOverlapEvaluator
from tracelens.runtime.executor import RagExecutor, SingleCallExecutor
from tracelens.runtime.model_client import MockModelClient
from tracelens.runtime.node import LoopContext
from tracelens.runtime.planner import MockPlanner
from tracelens.runtime.reflection import MockReflection


def _ctx(**overrides) -> LoopContext:
    defaults = dict(task="What is the deductible?", reference="The plan has a $250 deductible.")
    defaults.update(overrides)
    return LoopContext(**defaults)


def test_planner_is_deterministic():
    planner = MockPlanner(MockModelClient())
    ctx = _ctx()

    first = planner.run(ctx)
    second = planner.run(ctx)

    assert first == second
    assert first.decision == "ok"


def test_single_call_executor_ignores_context():
    executor = SingleCallExecutor(MockModelClient())
    with_context = executor.run(_ctx(context="The plan has a $250 deductible per claim."))
    without_context = executor.run(_ctx(context=""))

    assert with_context.output == without_context.output


def test_rag_executor_folds_in_context_and_documents_found():
    executor = RagExecutor(MockModelClient())

    grounded = executor.run(_ctx(context="The plan has a $250 deductible per claim."))
    ungrounded = executor.run(_ctx(context=""))

    assert "deductible" in grounded.output
    assert grounded.documents_found == 1
    assert ungrounded.documents_found == 0


def test_rag_executor_appends_critique():
    executor = RagExecutor(MockModelClient())

    result = executor.run(_ctx(context="Some context.", critique="Include these terms: 250"))

    assert "Include these terms: 250" in result.output


def test_evaluator_passes_when_answer_covers_reference():
    evaluator = KeywordOverlapEvaluator(MockModelClient(), pass_threshold=0.6)

    result = evaluator.run(
        _ctx(reference="The plan has a $250 deductible.", draft_answer="Your plan has a 250 deductible.")
    )

    assert result.decision == "pass"
    assert result.metadata["missing_keywords"] == []


def test_evaluator_fails_and_reports_missing_keywords():
    evaluator = KeywordOverlapEvaluator(MockModelClient(), pass_threshold=0.6)

    result = evaluator.run(
        _ctx(
            reference="The plan has a $250 deductible per claim.",
            draft_answer="Please consult the relevant documentation.",
        )
    )

    assert result.decision == "fail"
    assert "deductible" in result.metadata["missing_keywords"]
    assert result.reason is not None


def test_reflection_critique_contains_missing_keywords():
    reflection = MockReflection(MockModelClient())

    result = reflection.run(_ctx(missing_keywords=("deductible", "claim")))

    assert "deductible" in result.output
    assert "claim" in result.output


def test_reflection_falls_back_when_nothing_missing():
    reflection = MockReflection(MockModelClient())

    result = reflection.run(_ctx(missing_keywords=()))

    assert result.output
