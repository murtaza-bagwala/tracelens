import json

from tracelens.cli.main import main


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return path


def test_experiment_text_output(
    capsys, tmp_path, insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    dataset_path = _write(tmp_path, "dataset.json", insurance_faq_dataset_dict)
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)
    reflective_path = _write(tmp_path, "reflective.json", reflective_config_dict)

    exit_code = main(
        ["experiment", str(dataset_path), "--config", str(baseline_path), "--config", str(reflective_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Experiment Results" in captured.out
    assert "baseline" in captured.out
    assert "reflective" in captured.out


def test_experiment_json_output(
    capsys, tmp_path, insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    dataset_path = _write(tmp_path, "dataset.json", insurance_faq_dataset_dict)
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)
    reflective_path = _write(tmp_path, "reflective.json", reflective_config_dict)

    exit_code = main(
        [
            "experiment",
            str(dataset_path),
            "--config",
            str(baseline_path),
            "--config",
            str(reflective_path),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["best"]["success_rate"] == "reflective"


def test_experiment_custom_labels(
    capsys, tmp_path, insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    dataset_path = _write(tmp_path, "dataset.json", insurance_faq_dataset_dict)
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)
    reflective_path = _write(tmp_path, "reflective.json", reflective_config_dict)

    exit_code = main(
        [
            "experiment",
            str(dataset_path),
            "--config",
            str(baseline_path),
            "--config",
            str(reflective_path),
            "--format",
            "json",
            "--labels",
            "run1,run2",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert [entry["label"] for entry in parsed["entries"]] == ["run1", "run2"]


def test_experiment_requires_two_configs(capsys, tmp_path, insurance_faq_dataset_dict, baseline_config_dict):
    dataset_path = _write(tmp_path, "dataset.json", insurance_faq_dataset_dict)
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)

    exit_code = main(["experiment", str(dataset_path), "--config", str(baseline_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "at least two" in captured.err


def test_experiment_mismatched_labels_returns_error(
    capsys, tmp_path, insurance_faq_dataset_dict, baseline_config_dict, reflective_config_dict
):
    dataset_path = _write(tmp_path, "dataset.json", insurance_faq_dataset_dict)
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)
    reflective_path = _write(tmp_path, "reflective.json", reflective_config_dict)

    exit_code = main(
        [
            "experiment",
            str(dataset_path),
            "--config",
            str(baseline_path),
            "--config",
            str(reflective_path),
            "--labels",
            "only_one",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_experiment_missing_dataset_returns_error(
    capsys, tmp_path, baseline_config_dict, reflective_config_dict
):
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)
    reflective_path = _write(tmp_path, "reflective.json", reflective_config_dict)

    exit_code = main(
        [
            "experiment",
            "/nonexistent/path/dataset.json",
            "--config",
            str(baseline_path),
            "--config",
            str(reflective_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_experiment_missing_config_returns_error(capsys, tmp_path, insurance_faq_dataset_dict, baseline_config_dict):
    dataset_path = _write(tmp_path, "dataset.json", insurance_faq_dataset_dict)
    baseline_path = _write(tmp_path, "baseline.json", baseline_config_dict)

    exit_code = main(
        [
            "experiment",
            str(dataset_path),
            "--config",
            str(baseline_path),
            "--config",
            "/nonexistent/path/config.json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err
