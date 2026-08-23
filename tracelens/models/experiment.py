"""Data model for comparing multiple loop configs run over the same dataset."""

from __future__ import annotations

from dataclasses import dataclass

from tracelens.models.loop_config import LoopConfig
from tracelens.models.review import BatchSummary


@dataclass(frozen=True)
class ExperimentEntry:
    """One labeled loop config's aggregate result, as part of a multi-config experiment."""

    label: str
    config: LoopConfig
    batch: BatchSummary


@dataclass(frozen=True)
class ExperimentComparison:
    """Side-by-side result of running multiple loop configs over the same dataset."""

    entries: tuple[ExperimentEntry, ...]
    # Metric name -> label of the winning entry, or None if tied.
    best: dict[str, str | None]
