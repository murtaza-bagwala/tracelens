# TraceLens

**An experimentation platform for reasoning loops.**

## 1. Problem

The agent ecosystem has tools to *build* loops (LangGraph, CrewAI) and tools
to *inspect* a single run (LangSmith, Langfuse). Nothing answers the question
that actually determines whether a technique belongs in production:

> Does this architectural choice pay for itself?

Claims like "reflection improves agents" or "retries help" or "memory
matters" circulate as folklore. Nobody attaches a number, a task
distribution, or a cost to them. TraceLens exists to attach the number.

## 2. Positioning

| Tool | Question it answers |
|---|---|
| LangGraph | "How do I wire this workflow?" |
| LangSmith / Langfuse | "What happened in this one run?" |
| **TraceLens** | "Which architecture is best for this task, at what cost?" |

It is not a framework for building agents, and not a general observability
tool. It is a benchmarking harness: run the same dataset through multiple
loop *configurations* and produce a comparison, not a trace viewer.

Closest adjacent tools and why they don't cover this:
- **PromptFoo / Braintrust** — compare prompts/models on a dataset, not
  multi-step reasoning *architectures* (planner/reflection/retry/memory
  combinations).
- **LangSmith evaluators** — scoped to one chain at a time; no first-class
  concept of "run this same task through 5 different loop shapes and rank
  them."

The wedge is architecture-level A/B testing, not prompt-level.

## 3. Worked example

Task: answer an insurance FAQ question.

| | Run A: single LLM call | Run B: plan → retrieve → answer → reflect → rewrite |
|---|---|---|
| Accuracy | 81% | 92% |
| Cost | $0.02 | $0.12 |
| Latency | 2s | 11s |

Run B is "better" by accuracy alone. Whether it's *worth it* is a
cost/latency/accuracy tradeoff — and that tradeoff is the product.

## 4. Core abstraction

Everything is an **Experiment**:

```
Experiment = Dataset + Reasoning Loop + Evaluator + Metrics → Result
```

An experiment is domain-agnostic. It doesn't know or care whether the task
is insurance FAQs, code review, or paper summarization — that's just the
dataset.

## 5. Runtime architecture

```
                    Experiment
                         │
                         ▼
                  Dataset Loader
                         │
                         ▼
                  Loop Runtime
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
  Planner Node                      Memory Node
        │                                 │
        └────────────────┬────────────────┘
                          ▼
                   Executor Node
                          │
                          ▼
                  Evaluator Node
                          │
                          ▼
                 Reflection Node
                          │
                          ▼
                       Retry?
                     ╱      ╲
                   yes       no
                    │         │
                    └────► Finish
                              │
                              ▼
                    Metrics Collector
                              │
                              ▼
                   Dashboard / Report
```

Every node is swappable independently: planner, executor, evaluator,
reflection, memory. That's what makes "compare reflection ON vs OFF" a
one-line config change rather than a rewrite.

## 6. Config shape

```yaml
experiment:
  dataset: insurance_faq

  planner:
    type: llm

  executor:
    type: rag

  evaluator:
    type: llm_judge

  reflection:
    enabled: true

  retries: 2

  memory: working

  metrics: [accuracy, latency, cost]
```

The runtime resolves this into a node graph, runs it against every row in
the dataset, and produces one `Result` per (experiment, row).

## 7. Folder structure

```
tracelens/
  experiments/          # experiment configs
  datasets/             # task sets (questions + reference answers)
  runtime/
    planner.py
    executor.py
    evaluator.py
    reflection.py
    retry.py
    memory.py
  metrics/
    latency.py
    token_usage.py
    cost.py
    success.py
  traces/               # per-run execution logs
  prompts/
  dashboards/
  examples/
```

## 8. Node emission contract

For comparison and replay to work, every node emits a structured event on
start and end:

```
{ node, start_ts, end_ts, tokens_in, tokens_out, cost, latency_ms,
  decision, reason, retry_count }
```

This is the substrate the dashboard, the leaderboard, and experiment
comparison all read from — nothing above this layer should need a special
case per node type.

## 9. Roadmap

The phases below are the feature breakdown; the versions are the shippable
milestones. Each version should be independently useful, not a stepping
stone that only pays off later.

### V0.1 — Minimal runtime
Goal → Planner → Executor → Done. No reflection, no retries.
Log every step. Emit latency, tokens, cost per run.
*Ships: you can run one loop shape over a dataset and get numbers back.*

### V0.2 — Reflection & retry
Add Evaluator + Reflection node. Retry until pass or max attempts.
Compare **reflection ON vs OFF** and **1 vs 2 vs 5 retries** on the same
dataset.
*Ships: the first real comparison — does reflection pay for itself?*

### V0.3 — Benchmarking
Run the same dataset through N loop configs in one command. Generate a
comparison report (accuracy/cost/latency table, not just logs).
*Ships: the killer feature — Experiment A vs Experiment B, side by side.*

### V0.4 — Memory & plugins
Working memory node (search → remember → answer), comparable ON/OFF.
Planner/evaluator/executor become drop-in plugins — a new file in
`runtime/` with the right interface just works, no core changes.
*Ships: third-party planners and evaluators without touching the runtime.*

### V1.0 — Experiment platform
CLI + web dashboard. Visual timeline per run (click a node, see its
prompt/output/cost). Save and compare historical experiments. Leaderboards
over reusable benchmark datasets. Publish/share loop templates.
*Ships: the Hugging-Face-for-reasoning-loops layer — a place to publish a
loop architecture and let others benchmark it against their own data.*

## 10. Open questions to resolve before V0.1

These are the decisions that are expensive to reverse later — worth
answering before writing the runtime, not during it.

1. **Node interface.** What's the minimum contract a planner/executor/
   evaluator must implement? (input/output types, how it reports its own
   cost/latency, how it signals failure vs "needs retry.")
2. **Determinism vs realism.** Do runs need to be replayable byte-for-byte
   (cached LLM calls, fixed seeds), or is "close enough" accuracy across
   runs acceptable? This affects whether comparisons are trustworthy.
3. **Dataset format.** What does a dataset row look like — just
   `input`/`reference`, or does it need per-row metadata (difficulty,
   category) so the leaderboard can slice results?
4. **Evaluator trust.** LLM-judge evaluators are themselves noisy. Does V0.1
   need a way to sanity-check the judge (e.g. against a small human-labeled
   subset) before its numbers are treated as ground truth?
5. **Cost accounting.** Multi-provider cost tracking (different models,
   different $/token) — hardcoded price table, or pulled from a live
   source? Stale prices silently wrong is worse than not shown.

## 11. Why this, specifically

Every serious team building agentic systems is currently answering these
questions by gut feel:

- Is planning worth it?
- Is reflection worth it?
- When should the loop stop retrying?
- Does memory actually improve outcomes?
- What does each of these cost, and is that cost justified?
- Which architecture wins for *this* task, not tasks in general?

TraceLens's bet is that this becomes a standard part of shipping an agent
to production — the same way a load test is a standard part of shipping a
service — and that there's no dedicated tool for it yet.
