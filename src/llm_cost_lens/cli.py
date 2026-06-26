from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llm_cost_lens.analysis import analyze_calls
from llm_cost_lens.parser import LogParseError, load_jsonl
from llm_cost_lens.pricing import load_pricing
from llm_cost_lens.report import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-cost-lens",
        description="Inspect LLM API JSONL logs for cost, latency, budget, and usage anomalies.",
    )
    parser.add_argument(
        "log_file",
        nargs="?",
        type=Path,
        help="JSONL file with one LLM call per line",
    )
    parser.add_argument(
        "--pricing",
        type=Path,
        help="optional JSON pricing file keyed by model name",
    )
    parser.add_argument(
        "--budget",
        type=float,
        help="budget in USD for the analyzed log window",
    )
    parser.add_argument(
        "--group-by",
        choices=["model", "team", "endpoint"],
        default="model",
        help="group summary rows by model, team, or endpoint",
    )
    parser.add_argument(
        "--latency-threshold-ms",
        type=float,
        help="flag calls slower than this threshold",
    )
    parser.add_argument(
        "--anomaly-zscore",
        type=float,
        default=2.5,
        help="token spike sensitivity; lower values flag more calls",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="report output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the report to a file instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.log_file is None:
        parser.print_help()
        return 0

    try:
        pricing = load_pricing(args.pricing)
        records, warnings = load_jsonl(args.log_file, pricing)
        report = analyze_calls(
            records,
            budget_usd=args.budget,
            group_by=args.group_by,
            anomaly_zscore=args.anomaly_zscore,
            latency_threshold_ms=args.latency_threshold_ms,
            warnings=warnings,
        )
        rendered = render_report(report, output_format=args.format)
    except (LogParseError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0
