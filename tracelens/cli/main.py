"""tracelens CLI: analyze an agent execution trace and print an architecture review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from tracelens.analyzer.batch import analyze_batch
from tracelens.analyzer.bottlenecks import DEFAULT_LATENCY_THRESHOLD
from tracelens.analyzer.comparison import compare_traces
from tracelens.analyzer.cost import DEFAULT_COST_THRESHOLD
from tracelens.analyzer.engine import AnalyzerConfig, analyze_trace
from tracelens.analyzer.retrieval import DEFAULT_MIN_DOCUMENTS
from tracelens.analyzer.token_usage import DEFAULT_TOKEN_THRESHOLD
from tracelens.models.trace import ExecutionTrace
from tracelens.reporters.json_reporter import batch_to_json, comparison_to_json, to_json
from tracelens.reporters.text import render_batch_text, render_comparison_text, render_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracelens",
        description="Analyze AI agent execution traces and suggest architecture improvements.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze", help="Analyze an execution trace JSON file and print a review."
    )
    analyze.add_argument(
        "trace_path",
        help="Path to a JSON execution trace file, or a directory of them "
        "(all *.json files inside, non-recursive) for a batch summary.",
    )
    analyze.add_argument(
        "--format", choices=("text", "json"), default="text", help="Output format."
    )
    analyze.add_argument(
        "--min-documents",
        type=int,
        default=DEFAULT_MIN_DOCUMENTS,
        help="Minimum documents a retrieval step should return before it's flagged.",
    )
    analyze.add_argument(
        "--latency-threshold",
        type=float,
        default=DEFAULT_LATENCY_THRESHOLD,
        help="Share (0-1) of total execution time a tool/retrieval step must "
        "reach to be flagged as a latency bottleneck.",
    )
    analyze.add_argument(
        "--token-threshold",
        type=float,
        default=DEFAULT_TOKEN_THRESHOLD,
        help="Share (0-1) of total LLM tokens a single step must reach to be "
        "flagged as token concentration.",
    )
    analyze.add_argument(
        "--cost-threshold",
        type=float,
        default=DEFAULT_COST_THRESHOLD,
        help="Share (0-1) of total run cost a single step must reach to be "
        "flagged as cost concentration.",
    )

    compare = subparsers.add_parser(
        "compare",
        help="Analyze multiple execution traces and print a side-by-side comparison.",
    )
    compare.add_argument(
        "trace_paths",
        nargs="+",
        help="Paths to two or more JSON execution trace files, or a directory "
        "containing them (all *.json files inside, non-recursive).",
    )
    compare.add_argument(
        "--format", choices=("text", "json"), default="text", help="Output format."
    )
    compare.add_argument(
        "--labels",
        help="Comma-separated labels, one per trace path, in the same order "
        "(default: each file's name without extension).",
    )
    compare.add_argument(
        "--min-documents",
        type=int,
        default=DEFAULT_MIN_DOCUMENTS,
        help="Minimum documents a retrieval step should return before it's flagged.",
    )
    compare.add_argument(
        "--latency-threshold",
        type=float,
        default=DEFAULT_LATENCY_THRESHOLD,
        help="Share (0-1) of total execution time a tool/retrieval step must "
        "reach to be flagged as a latency bottleneck.",
    )
    compare.add_argument(
        "--token-threshold",
        type=float,
        default=DEFAULT_TOKEN_THRESHOLD,
        help="Share (0-1) of total LLM tokens a single step must reach to be "
        "flagged as token concentration.",
    )
    compare.add_argument(
        "--cost-threshold",
        type=float,
        default=DEFAULT_COST_THRESHOLD,
        help="Share (0-1) of total run cost a single step must reach to be "
        "flagged as cost concentration.",
    )

    return parser


def _config_from_args(args: argparse.Namespace) -> AnalyzerConfig:
    return AnalyzerConfig(
        latency_threshold=args.latency_threshold,
        token_threshold=args.token_threshold,
        cost_threshold=args.cost_threshold,
        min_documents=args.min_documents,
    )


def _run_analyze(args: argparse.Namespace) -> int:
    path = Path(args.trace_path)
    if path.is_dir():
        return _run_analyze_batch(path, args)

    try:
        trace = ExecutionTrace.load(args.trace_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    review = analyze_trace(trace, _config_from_args(args))

    if args.format == "json":
        print(to_json(review))
    else:
        print(render_text(review))

    return 0


def _run_analyze_batch(directory: Path, args: argparse.Namespace) -> int:
    trace_paths = sorted(directory.glob("*.json"))
    if not trace_paths:
        print(f"Error: no *.json trace files found in '{directory}'.", file=sys.stderr)
        return 1

    labeled_traces = []
    for trace_path in trace_paths:
        try:
            labeled_traces.append((trace_path.stem, ExecutionTrace.load(trace_path)))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Error loading '{trace_path}': {exc}", file=sys.stderr)
            return 1

    summary = analyze_batch(labeled_traces, _config_from_args(args))

    if args.format == "json":
        print(batch_to_json(summary))
    else:
        print(render_batch_text(summary))

    return 0


def _expand_trace_paths(paths: list[str]) -> list[str]:
    """Expand any directory argument into the sorted *.json files inside it."""
    expanded = []
    for path in paths:
        candidate = Path(path)
        if candidate.is_dir():
            expanded.extend(str(p) for p in sorted(candidate.glob("*.json")))
        else:
            expanded.append(path)
    return expanded


def _run_compare(args: argparse.Namespace) -> int:
    trace_paths = _expand_trace_paths(args.trace_paths)

    if len(trace_paths) < 2:
        print(
            "Error: compare requires at least two trace files "
            "(found "
            f"{len(trace_paths)} after resolving paths/directories).",
            file=sys.stderr,
        )
        return 1

    if args.labels:
        labels = [label.strip() for label in args.labels.split(",")]
        if len(labels) != len(trace_paths):
            print(
                f"Error: got {len(labels)} labels for {len(trace_paths)} "
                "trace files — they must match 1:1.",
                file=sys.stderr,
            )
            return 1
    else:
        labels = [Path(path).stem for path in trace_paths]

    labeled_traces = []
    for label, path in zip(labels, trace_paths):
        try:
            labeled_traces.append((label, ExecutionTrace.load(path)))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Error loading '{path}': {exc}", file=sys.stderr)
            return 1

    comparison = compare_traces(labeled_traces, _config_from_args(args))

    if args.format == "json":
        print(comparison_to_json(comparison))
    else:
        print(render_comparison_text(comparison))

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args)
    if args.command == "compare":
        return _run_compare(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
