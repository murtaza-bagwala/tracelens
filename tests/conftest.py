import json
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def sample_trace_dict() -> dict:
    return json.loads((EXAMPLES_DIR / "sample_trace.json").read_text())


@pytest.fixture
def sample_trace_reflective_dict() -> dict:
    return json.loads((EXAMPLES_DIR / "sample_trace_reflective.json").read_text())


@pytest.fixture
def insurance_faq_dataset_dict() -> dict:
    return json.loads((EXAMPLES_DIR / "datasets" / "insurance_faq.json").read_text())


@pytest.fixture
def baseline_config_dict() -> dict:
    return json.loads((EXAMPLES_DIR / "configs" / "baseline.json").read_text())


@pytest.fixture
def reflective_config_dict() -> dict:
    return json.loads((EXAMPLES_DIR / "configs" / "reflective.json").read_text())


@pytest.fixture
def retries_only_config_dict() -> dict:
    return json.loads((EXAMPLES_DIR / "configs" / "retries_only.json").read_text())
