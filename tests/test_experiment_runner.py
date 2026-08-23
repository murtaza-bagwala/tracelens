from tracelens.analyzer.batch import analyze_batch
from tracelens.experiments.runner import run_experiment
from tracelens.models.dataset import Dataset
from tracelens.models.loop_config import LoopConfig
from tracelens.runtime.loop import run_loop
from tracelens.runtime.model_client import MockModelClient


def _configs(baseline_config_dict, reflective_config_dict):
    return [
        ("baseline", LoopConfig.from_dict(baseline_config_dict)),
        ("reflective", LoopConfig.from_dict(reflective_config_dict)),
    ]


def test_run_experiment_preserves_order_and_labels(
    insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    dataset = Dataset.from_dict(insurance_faq_dataset_dict)
    entries = run_experiment(dataset, _configs(baseline_config_dict, reflective_config_dict))

    assert [entry.label for entry in entries] == ["baseline", "reflective"]
    assert entries[0].config.name == "baseline"


def test_run_experiment_batch_matches_direct_analyze_batch(
    insurance_faq_dataset_dict, baseline_config_dict
):
    dataset = Dataset.from_dict(insurance_faq_dataset_dict)
    config = LoopConfig.from_dict(baseline_config_dict)
    client = MockModelClient()

    entries = run_experiment(dataset, [("baseline", config)], client=client)

    expected_traces = [(row.id, run_loop(row, config, client)) for row in dataset.rows]
    expected_batch = analyze_batch(expected_traces)

    assert entries[0].batch == expected_batch


def test_run_experiment_reflective_beats_baseline_on_success_rate(
    insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    dataset = Dataset.from_dict(insurance_faq_dataset_dict)
    entries = run_experiment(dataset, _configs(baseline_config_dict, reflective_config_dict))

    baseline, reflective = entries
    assert reflective.batch.success_rate > baseline.batch.success_rate
