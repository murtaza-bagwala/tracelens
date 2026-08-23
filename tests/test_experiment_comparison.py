from tracelens.experiments.comparison import compare_experiments
from tracelens.experiments.runner import run_experiment
from tracelens.models.dataset import Dataset
from tracelens.models.loop_config import LoopConfig


def _run(insurance_faq_dataset_dict, *config_dicts):
    dataset = Dataset.from_dict(insurance_faq_dataset_dict)
    labeled_configs = [
        (config_dict["name"], LoopConfig.from_dict(config_dict)) for config_dict in config_dicts
    ]
    return run_experiment(dataset, labeled_configs)


def test_compare_experiments_picks_best_per_metric(
    insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    entries = _run(insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict)
    comparison = compare_experiments(entries)

    assert comparison.best["success_rate"] == "reflective"
    assert comparison.best["avg_duration_ms"] == "baseline"
    assert comparison.best["avg_tokens"] == "baseline"
    assert comparison.best["avg_cost"] == "baseline"


def test_compare_experiments_tie_reports_none(insurance_faq_dataset_dict, baseline_config_dict):
    dataset = Dataset.from_dict(insurance_faq_dataset_dict)
    config = LoopConfig.from_dict(baseline_config_dict)
    entries = run_experiment(dataset, [("a", config), ("b", config)])
    comparison = compare_experiments(entries)

    assert comparison.best["success_rate"] is None
    assert comparison.best["avg_duration_ms"] is None


def test_compare_experiments_single_entry_wins_trivially(
    insurance_faq_dataset_dict, baseline_config_dict
):
    entries = _run(insurance_faq_dataset_dict, baseline_config_dict)
    comparison = compare_experiments(entries)

    assert len(comparison.entries) == 1
    assert comparison.best["avg_duration_ms"] == entries[0].label
