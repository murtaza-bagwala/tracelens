"""Data model for a single AI agent execution trace."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

_KNOWN_STEP_FIELDS = {
    "name",
    "type",
    "duration_ms",
    "tokens",
    "cost",
    "documents_found",
    "input",
    "output",
    "error",
}


@dataclass(frozen=True)
class Step:
    """A single step in an agent's execution (an LLM call, tool call, retrieval, ...)."""

    name: str
    type: str
    duration_ms: float = 0.0
    tokens: Optional[int] = None
    cost: Optional[float] = None
    documents_found: Optional[int] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        if "name" not in data:
            raise ValueError("Step is missing required field 'name'")
        if "type" not in data:
            raise ValueError(f"Step '{data['name']}' is missing required field 'type'")

        extra = {k: v for k, v in data.items() if k not in _KNOWN_STEP_FIELDS}

        return cls(
            name=data["name"],
            type=data["type"],
            duration_ms=float(data.get("duration_ms") or 0.0),
            tokens=data.get("tokens"),
            cost=data.get("cost"),
            documents_found=data.get("documents_found"),
            input=data.get("input"),
            output=data.get("output"),
            error=data.get("error"),
            extra=extra,
        )


@dataclass(frozen=True)
class ExecutionTrace:
    """A full execution trace for one run of an agent against one task."""

    task: str
    steps: tuple[Step, ...]
    success: bool = True
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionTrace":
        if "steps" not in data or not isinstance(data["steps"], list):
            raise ValueError("Trace must contain a 'steps' list")

        steps = tuple(Step.from_dict(step) for step in data["steps"])

        return cls(
            task=data.get("task", ""),
            steps=steps,
            success=bool(data.get("success", True)),
            error=data.get("error"),
        )

    @classmethod
    def from_json(cls, raw: str) -> "ExecutionTrace":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ExecutionTrace":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))
