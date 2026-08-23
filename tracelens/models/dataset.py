"""Data model for a dataset of tasks to run through an experiment loop."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class DatasetRow:
    """One task to run through a loop: an input, its reference answer, and
    optionally the supporting context a real retrieval step would surface."""

    id: str
    input: str
    reference: str
    context: str = ""
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "DatasetRow":
        for required in ("id", "input", "reference"):
            if required not in data:
                raise ValueError(f"Dataset row is missing required field '{required}'")

        return cls(
            id=data["id"],
            input=data["input"],
            reference=data["reference"],
            context=data.get("context", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class Dataset:
    """A named collection of dataset rows to run through an experiment."""

    name: str
    rows: tuple[DatasetRow, ...]

    @classmethod
    def from_dict(cls, data: dict) -> "Dataset":
        if "rows" not in data or not isinstance(data["rows"], list):
            raise ValueError("Dataset must contain a 'rows' list")

        return cls(
            name=data.get("name", ""),
            rows=tuple(DatasetRow.from_dict(row) for row in data["rows"]),
        )

    @classmethod
    def from_json(cls, raw: str) -> "Dataset":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def load(cls, path: Union[str, Path]) -> "Dataset":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))
