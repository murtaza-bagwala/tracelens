import pytest

from tracelens.models.loop_config import LoopConfig


def test_loop_config_from_dict_round_trips(reflective_config_dict):
    config = LoopConfig.from_dict(reflective_config_dict)

    assert config.name == "reflective"
    assert config.planner == {"type": "llm"}
    assert config.executor == {"type": "rag"}
    assert config.reflection == {"enabled": True}
    assert config.retries == 2


def test_loop_config_defaults():
    config = LoopConfig.from_dict({"name": "minimal"})

    assert config.planner == {"type": "none"}
    assert config.executor == {"type": "single_call"}
    assert config.evaluator["type"] == "keyword_overlap"
    assert config.reflection == {"enabled": False}
    assert config.retries == 0


def test_loop_config_missing_name_raises():
    with pytest.raises(ValueError):
        LoopConfig.from_dict({})
