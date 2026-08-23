# TraceLens

Analyze AI agent execution traces and get back concrete, actionable suggestions
for improving the reasoning architecture — not just a trace viewer, a review.

Point it at a JSON trace of an agent run (planner/LLM calls, tool calls,
retrieval steps, ...) and it tells you: where the time went, where the tokens
and cost went, and what's likely wrong (thin retrieval, a runaway retry loop,
a step that silently errored, a failure that correlates with an earlier
issue). Point it at *two or more* traces — e.g. the same task run through two
different loop configurations — and it ranks them side by side. Point it at a
whole directory of traces and it summarizes the batch: success rate, average
cost/latency/tokens, and which issues show up most often across the dataset.

Point it at a dataset and two or more loop *configs* (planner/executor/
evaluator/reflection/retries) instead, and it actually **runs** each config
over every row — with a deterministic mock model backend, no API key
required — and prints a ranked comparison: does reflection pay for itself?
Do retries alone help, or only retries *plus* reflection?

See [DESIGN.md](DESIGN.md) for the longer-term vision (an experimentation
platform for reasoning-loop architectures). This tool is both the analysis
layer of that vision (usable today against traces you already have) and a
first slice of the execution layer (running configured loops over a dataset
yourself, rather than hand-authoring trace JSON).

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.10+. No runtime dependencies.

## Quickstart

```bash
# Analyze a single trace
tracelens analyze examples/sample_trace.json

# Same, as JSON (for piping into other tools)
tracelens analyze examples/sample_trace.json --format json

# Analyze every trace in a directory and get an aggregate summary
tracelens analyze examples/

# Compare two (or more) architectures on the same task
tracelens compare examples/sample_trace.json examples/sample_trace_reflective.json

# Compare every trace in a directory
tracelens compare examples/

# Actually run two loop architectures over the same dataset and compare them
tracelens experiment examples/datasets/insurance_faq.json \
  --config examples/configs/baseline.json \
  --config examples/configs/reflective.json
```

## Commands

### `tracelens analyze <path>`

Analyzes one execution trace and prints a review: statistics, detected
issues, and suggestions.

If `<path>` is a directory instead of a file, it analyzes every `*.json` file
inside (non-recursive, sorted by filename) and prints a **batch summary**
instead: success rate, average duration/tokens/cost across the batch, how
often each issue category fired, and a one-line status per trace.

| Flag | Default | Meaning |
|---|---|---|
| `--format {text,json}` | `text` | Output format. |
| `--min-documents N` | `3` | Retrieval steps returning fewer documents than this are flagged. |
| `--latency-threshold F` | `0.3` | A tool/retrieval step consuming more than this share of total time is flagged. |
| `--token-threshold F` | `0.5` | A single LLM step consuming more than this share of total tokens is flagged. |
| `--cost-threshold F` | `0.5` | A single step consuming more than this share of total cost is flagged. |

### `tracelens compare <path> [<path> ...]`

Analyzes two or more traces and prints a side-by-side comparison table,
ranking each entry on success, duration, tokens, cost, and issue count (the
metrics that were tied are marked `tie`).

Any argument that's a directory is expanded to the sorted `*.json` files
inside it, so `tracelens compare traces/` and
`tracelens compare traces/a.json extra_run.json` (a directory mixed with an
individual file) both work. At least two trace files are required after
expansion.

| Flag | Default | Meaning |
|---|---|---|
| `--format {text,json}` | `text` | Output format. |
| `--labels a,b,...` | filename stems | One label per trace path, in order. |
| `--min-documents` / `--latency-threshold` / `--token-threshold` / `--cost-threshold` | same as `analyze` | Detector thresholds, shared across all traces being compared. |

### `tracelens experiment <dataset> --config <config> --config <config> ...`

Actually **runs** two or more loop configs over every row of a dataset (with
a deterministic mock model backend — no API key, no network calls), then
aggregates each config's results with the same analyzer used by `analyze`
and ranks the configs against each other.

| Flag | Default | Meaning |
|---|---|---|
| `--config` | *(required, ≥2)* | Path to a loop config JSON file. Repeat once per config to compare. |
| `--format {text,json}` | `text` | Output format. |
| `--labels a,b,...` | each config's `name` field | One label per `--config`, in order. |
| `--min-documents` / `--latency-threshold` / `--token-threshold` / `--cost-threshold` | same as `analyze` | Detector thresholds, applied to every generated trace before aggregation. |

## Trace format

A trace is a JSON object describing one run of an agent against one task:

```json
{
  "task": "Recommend a travel insurance policy",
  "success": true,
  "error": null,
  "steps": [
    {
      "name": "retrieve_policy",
      "type": "retrieval",
      "duration_ms": 80,
      "documents_found": 2,
      "tokens": null,
      "cost": 0.0002,
      "input": "...",
      "output": "...",
      "error": null
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `task` | no | Free-text description of what the agent was asked to do. |
| `success` | no (default `true`) | Whether the run succeeded overall. |
| `error` | no | Overall failure reason, if `success` is `false`. |
| `steps` | yes | Ordered list of step objects (see below). |

Each step requires `name` and `type` (`type` is typically one of `llm`,
`tool`, or `retrieval` — anything else is counted as "other"). All other
fields are optional:

| Field | Meaning |
|---|---|
| `duration_ms` | How long the step took, in milliseconds. |
| `tokens` | Tokens consumed by an `llm` step. |
| `cost` | Dollar cost attributed to this step (any step type — LLM tokens, a paid tool/API call, etc.). |
| `documents_found` | Number of documents returned by a `retrieval` step. |
| `input` / `output` | Whatever you want to keep for debugging; not used by the analyzer. |
| `error` | Set if this specific step failed, independent of overall `success`. |

Unknown fields are preserved but ignored by the analyzer.

## What it detects

| Category | Trigger |
|---|---|
| `low_retrieval_documents` | A retrieval step returned fewer than `--min-documents`. |
| `latency_bottleneck` | A tool/retrieval step dominates total execution time. |
| `token_concentration` | A single LLM step consumes most of the run's tokens. |
| `cost_concentration` | A single step consumes most of the run's cost. |
| `repeated_step` | The same step name executed more than once (retry-loop signature). |
| `step_error` | A step reported its own error. |
| `failure` | The overall run failed; correlated with an earlier flagged step when possible. |

Each detected issue maps to a suggestion (e.g. "cache or parallelize this
step", "add a reflection step before returning").

## Dataset format (for `tracelens experiment`)

A dataset is a JSON object with a name and a list of rows to run through a
loop:

```json
{
  "name": "insurance_faq",
  "rows": [
    {
      "id": "deductible",
      "input": "What is the deductible on the Basic Travel plan?",
      "reference": "The Basic Travel plan has a $250 deductible per claim.",
      "context": "The Basic Travel plan is our entry-level travel insurance product..."
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Row identifier, used as its label within a batch. |
| `input` | yes | The task/question given to the loop. |
| `reference` | yes | The expected answer, scored against by the mock evaluator. |
| `context` | no | What a real retrieval step would have found. Ignored by a `single_call` executor; used by a `rag` executor. |
| `metadata` | no | Free-form extra fields (e.g. category, difficulty). Not used by the runtime today. |

## Loop config format (for `tracelens experiment`)

A loop config describes one swappable reasoning-loop architecture:

```json
{
  "name": "reflective",
  "planner": { "type": "llm" },
  "executor": { "type": "rag" },
  "evaluator": { "type": "keyword_overlap", "pass_threshold": 0.6 },
  "reflection": { "enabled": true },
  "retries": 2
}
```

| Field | Meaning |
|---|---|
| `name` | Config name, used as its label if `--labels` isn't given. |
| `planner.type` | `"none"` (skip planning) or `"llm"`. |
| `executor.type` | `"single_call"` (answers from the task alone, no grounding) or `"rag"` (grounds its answer in the row's `context`). |
| `evaluator.type` | `"keyword_overlap"` — the only evaluator today; scores the answer against the reference's content words. `pass_threshold` (default `0.6`) is the minimum coverage to pass. |
| `reflection.enabled` | Whether a failed attempt gets a critique (built from the evaluator's missing terms) before retrying. |
| `retries` | Max retries after the first attempt. Restarts from the planner each retry, so a critique can correct a bad plan, not just a bad answer. |

The loop runs against a fully deterministic mock model backend (see
`tracelens.MockModelClient`) — no API key or network access needed. A real
provider adapter isn't wired in yet.

## Using it as a library

```python
from tracelens import ExecutionTrace, analyze_trace, compare_traces, analyze_batch

trace = ExecutionTrace.load("examples/sample_trace.json")
review = analyze_trace(trace)
print(review.issues, review.suggestions)

# Compare architectures
baseline = ExecutionTrace.load("examples/sample_trace.json")
reflective = ExecutionTrace.load("examples/sample_trace_reflective.json")
comparison = compare_traces([("baseline", baseline), ("reflective", reflective)])
print(comparison.best)  # {"success": "reflective", "total_cost": "baseline", ...}

# Actually run loop configs over a dataset (instead of loading pre-made traces)
from tracelens import Dataset, LoopConfig, run_experiment, compare_experiments

dataset = Dataset.load("examples/datasets/insurance_faq.json")
baseline_cfg = LoopConfig.load("examples/configs/baseline.json")
reflective_cfg = LoopConfig.load("examples/configs/reflective.json")

entries = run_experiment(dataset, [("baseline", baseline_cfg), ("reflective", reflective_cfg)])
experiment_comparison = compare_experiments(entries)
print(experiment_comparison.best)  # {"success_rate": "reflective", "avg_cost": "baseline", ...}
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
