"""Run one or more loop configs over the same dataset and aggregate results."""

from __future__ import annotations

from typing import Optional

from tracelens.analyzer.batch import analyze_batch
from tracelens.analyzer.engine import AnalyzerConfig
from tracelens.models.dataset import Dataset
from tracelens.models.experiment import ExperimentEntry
from tracelens.models.loop_config import LoopConfig
from tracelens.runtime.loop import run_loop
from tracelens.runtime.model_client import MockModelClient, ModelClient


def run_experiment(
    dataset: Dataset,
    labeled_configs: list[tuple[str, LoopConfig]],
    client: Optional[ModelClient] = None,
    analyzer_config: Optional[AnalyzerConfig] = None,
) -> tuple[ExperimentEntry, ...]:
    """Execute every dataset row through every config, then reuse the
    existing batch analyzer to aggregate each config's results."""

    client = client or MockModelClient()

    entries = []
    for label, config in labeled_configs:
        labeled_traces = [(row.id, run_loop(row, config, client)) for row in dataset.rows]
        batch = analyze_batch(labeled_traces, analyzer_config)
        entries.append(ExperimentEntry(label=label, config=config, batch=batch))

    return tuple(entries)
