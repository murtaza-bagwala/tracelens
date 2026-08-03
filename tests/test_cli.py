import json

from tracelens.cli.main import main


def test_analyze_text_output(capsys, tmp_path, sample_trace_dict):
    trace_path = tmp_path / "trace.json"
    trace_path.write_text(json.dumps(sample_trace_dict))

    exit_code = main(["analyze", str(trace_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Architecture Review" in captured.out


def test_analyze_json_output(capsys, tmp_path, sample_trace_dict):
    trace_path = tmp_path / "trace.json"
    trace_path.write_text(json.dumps(sample_trace_dict))

    exit_code = main(["analyze", str(trace_path), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["task"] == sample_trace_dict["task"]


def test_analyze_missing_file_returns_error(capsys):
    exit_code = main(["analyze", "/nonexistent/path/trace.json"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_compare_text_output(capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict):
    trace_a = tmp_path / "baseline.json"
    trace_b = tmp_path / "reflective.json"
    trace_a.write_text(json.dumps(sample_trace_dict))
    trace_b.write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["compare", str(trace_a), str(trace_b)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Experiment Comparison" in captured.out
    assert "baseline" in captured.out
    assert "reflective" in captured.out


def test_compare_json_output(capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict):
    trace_a = tmp_path / "baseline.json"
    trace_b = tmp_path / "reflective.json"
    trace_a.write_text(json.dumps(sample_trace_dict))
    trace_b.write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["compare", str(trace_a), str(trace_b), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["best"]["success"] == "reflective"


def test_compare_custom_labels(capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict):
    trace_a = tmp_path / "a.json"
    trace_b = tmp_path / "b.json"
    trace_a.write_text(json.dumps(sample_trace_dict))
    trace_b.write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(
        ["compare", str(trace_a), str(trace_b), "--format", "json", "--labels", "run1,run2"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert [entry["label"] for entry in parsed["entries"]] == ["run1", "run2"]


def test_compare_mismatched_labels_returns_error(
    capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict
):
    trace_a = tmp_path / "a.json"
    trace_b = tmp_path / "b.json"
    trace_a.write_text(json.dumps(sample_trace_dict))
    trace_b.write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["compare", str(trace_a), str(trace_b), "--labels", "only_one"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_compare_requires_two_traces(capsys, tmp_path, sample_trace_dict):
    trace_a = tmp_path / "a.json"
    trace_a.write_text(json.dumps(sample_trace_dict))

    exit_code = main(["compare", str(trace_a)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "at least two" in captured.err


def test_analyze_with_directory_runs_batch_mode(
    capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict
):
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "baseline.json").write_text(json.dumps(sample_trace_dict))
    (traces_dir / "reflective.json").write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["analyze", str(traces_dir), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["trace_count"] == 2
    assert [entry["label"] for entry in parsed["entries"]] == ["baseline", "reflective"]


def test_analyze_with_directory_text_output(
    capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict
):
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "baseline.json").write_text(json.dumps(sample_trace_dict))
    (traces_dir / "reflective.json").write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["analyze", str(traces_dir)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Batch Analysis (2 traces)" in captured.out


def test_analyze_empty_directory_returns_error(capsys, tmp_path):
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()

    exit_code = main(["analyze", str(traces_dir)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_compare_with_directory(
    capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict
):
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "a_baseline.json").write_text(json.dumps(sample_trace_dict))
    (traces_dir / "b_reflective.json").write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["compare", str(traces_dir), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert [entry["label"] for entry in parsed["entries"]] == [
        "a_baseline",
        "b_reflective",
    ]


def test_compare_with_directory_and_extra_file(
    capsys, tmp_path, sample_trace_dict, sample_trace_reflective_dict
):
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "baseline.json").write_text(json.dumps(sample_trace_dict))
    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps(sample_trace_reflective_dict))

    exit_code = main(["compare", str(traces_dir), str(extra), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert [entry["label"] for entry in parsed["entries"]] == ["baseline", "extra"]


def test_compare_directory_with_too_few_traces_returns_error(
    capsys, tmp_path, sample_trace_dict
):
    traces_dir = tmp_path / "traces"
    traces_dir.mkdir()
    (traces_dir / "only.json").write_text(json.dumps(sample_trace_dict))

    exit_code = main(["compare", str(traces_dir)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "at least two" in captured.err


def test_compare_missing_file_returns_error(capsys, tmp_path, sample_trace_dict):
    trace_a = tmp_path / "a.json"
    trace_a.write_text(json.dumps(sample_trace_dict))

    exit_code = main(["compare", str(trace_a), "/nonexistent/path/trace.json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_analyze_custom_thresholds(capsys, tmp_path):
    trace_path = tmp_path / "trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "task": "t",
                "steps": [
                    {"name": "llm_step", "type": "llm", "duration_ms": 1000, "tokens": 100},
                    {
                        "name": "r",
                        "type": "retrieval",
                        "documents_found": 4,
                        "duration_ms": 10,
                    },
                ],
            }
        )
    )

    exit_code = main(
        ["analyze", str(trace_path), "--format", "json", "--min-documents", "5"]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert len(parsed["issues"]) == 1
    assert parsed["issues"][0]["category"] == "low_retrieval_documents"


def test_analyze_custom_cost_threshold(capsys, tmp_path):
    trace_path = tmp_path / "trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "task": "t",
                "steps": [
                    {"name": "a", "type": "llm", "cost": 0.06},
                    {"name": "b", "type": "llm", "cost": 0.04},
                ],
            }
        )
    )

    lenient_exit_code = main(
        ["analyze", str(trace_path), "--format", "json", "--cost-threshold", "0.7"]
    )
    lenient_out = json.loads(capsys.readouterr().out)
    assert lenient_exit_code == 0
    assert lenient_out["issues"] == []

    strict_exit_code = main(
        ["analyze", str(trace_path), "--format", "json", "--cost-threshold", "0.5"]
    )
    strict_out = json.loads(capsys.readouterr().out)
    assert strict_exit_code == 0
    assert len(strict_out["issues"]) == 1
    assert strict_out["issues"][0]["category"] == "cost_concentration"
