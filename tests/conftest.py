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
