from collections import Counter

from tracelens.analyzer.engine import analyze_trace
from tracelens.models.dataset import DatasetRow
from tracelens.models.loop_config import LoopConfig
from tracelens.runtime.loop import run_loop
from tracelens.runtime.model_client import MockModelClient

ROW = DatasetRow(
    id="deductible",
    input="What is the deductible on the Basic Travel plan?",
    reference="The Basic Travel plan has a $250 deductible per claim.",
    context="The Basic Travel plan is our entry-level travel insurance product, "
    "covering trip cancellation and baggage loss.",
)


def test_baseline_config_fails_with_minimal_steps():
    config = LoopConfig(
        name="baseline",
        planner={"type": "none"},
        executor={"type": "single_call"},
        reflection={"enabled": False},
        retries=0,
    )

    trace = run_loop(ROW, config, MockModelClient())

    assert trace.success is False
    assert trace.error is not None
    assert [step.name for step in trace.steps] == ["executor", "evaluator"]


def test_reflective_config_eventually_passes():
    config = LoopConfig(
        name="reflective",
        planner={"type": "llm"},
        executor={"type": "rag"},
        reflection={"enabled": True},
        retries=2,
    )

    trace = run_loop(ROW, config, MockModelClient())

    assert trace.success is True
    assert trace.error is None
    step_names = [step.name for step in trace.steps]
    assert Counter(step_names)["executor"] >= 2
    assert "reflect" in step_names


def test_retries_without_reflection_do_not_help_and_trigger_repeated_step_detection():
    config = LoopConfig(
        name="retries_only",
        planner={"type": "llm"},
        executor={"type": "rag"},
        reflection={"enabled": False},
        retries=2,
    )

    trace = run_loop(ROW, config, MockModelClient())

    assert trace.success is False
    step_names = [step.name for step in trace.steps]
    assert Counter(step_names)["executor"] == 3
    assert "reflect" not in step_names

    # Feed the generated trace into the existing analyzer unmodified — the
    # retry-loop signature should fire "for free", proving the reuse contract.
    review = analyze_trace(trace)
    assert any(issue.category == "repeated_step" for issue in review.issues)


def test_retries_exhausted_without_reflection_reports_last_evaluator_reason():
    config = LoopConfig(
        name="retries_only",
        planner={"type": "none"},
        executor={"type": "single_call"},
        reflection={"enabled": False},
        retries=1,
    )

    trace = run_loop(ROW, config, MockModelClient())

    assert trace.success is False
    assert "missing" in trace.error
