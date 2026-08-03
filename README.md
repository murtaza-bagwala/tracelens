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

See [DESIGN.md](DESIGN.md) for the longer-term vision (an experimentation
platform for reasoning-loop architectures). This tool is the analysis layer of
that vision, usable today against traces you already have.

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
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
