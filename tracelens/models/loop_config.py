"""Data model for a configurable reasoning-loop architecture."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

DEFAULT_PASS_THRESHOLD = 0.6


@dataclass(frozen=True)
class LoopConfig:
    """Describes one swappable loop architecture: which nodes run, and how."""

    name: str
    planner: dict = field(default_factory=lambda: {"type": "none"})
    executor: dict = field(default_factory=lambda: {"type": "single_call"})
    evaluator: dict = field(
        default_factory=lambda: {"type": "keyword_overlap", "pass_threshold": DEFAULT_PASS_THRESHOLD}
    )
    reflection: dict = field(default_factory=lambda: {"enabled": False})
    retries: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "LoopConfig":
        if "name" not in data:
            raise ValueError("Loop config is missing required field 'name'")

        defaults = cls(name=data["name"])
        return cls(
            name=data["name"],
            planner=data.get("planner", defaults.planner),
            executor=data.get("executor", defaults.executor),
            evaluator=data.get("evaluator", defaults.evaluator),
            reflection=data.get("reflection", defaults.reflection),
            retries=int(data.get("retries", 0)),
        )

    @classmethod
    def from_json(cls, raw: str) -> "LoopConfig":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def load(cls, path: Union[str, Path]) -> "LoopConfig":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))
