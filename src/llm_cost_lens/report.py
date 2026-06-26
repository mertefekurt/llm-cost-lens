from __future__ import annotations

import json
from dataclasses import asdict

from llm_cost_lens.models import LensReport


def render_report(report: LensReport, *, output_format: str = "markdown") -> str:
    if output_format == "json":
        return json.dumps(asdict(report), indent=2, sort_keys=True)
    if output_format != "markdown":
        raise ValueError("output format must be 'markdown' or 'json'")
    return _render_markdown(report)


def _render_markdown(report: LensReport) -> str:
    lines = [
        "# LLM Cost Lens Report",
        "",
        f"- calls: {report.calls}",
        f"- tokens: {report.total_tokens:,} "
        f"({report.prompt_tokens:,} prompt, {report.completion_tokens:,} completion)",
        f"- estimated cost: ${report.cost_usd:.4f}",
        f"- average latency: {_ms(report.avg_latency_ms)}",
        f"- p95 latency: {_ms(report.p95_latency_ms)}",
        f"- error rate: {report.error_rate:.1%}",
    ]
    if report.budget_usd is not None:
        used = "unknown" if report.budget_used_ratio is None else f"{report.budget_used_ratio:.1%}"
        lines.append(f"- budget: ${report.budget_usd:.2f} ({used} used)")

    if report.groups:
        lines.extend(
            ["", "## Top groups", "", "| group | calls | tokens | cost | avg latency | errors |"]
        )
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for group in report.groups:
            lines.append(
                f"| {group.name} | {group.calls} | {group.total_tokens:,} | "
                f"${group.cost_usd:.4f} | {_ms(group.avg_latency_ms)} | {group.error_rate:.1%} |"
            )

    if report.anomalies:
        lines.extend(["", "## Anomalies", ""])
        for anomaly in report.anomalies:
            request = f" ({anomaly.request_id})" if anomaly.request_id else ""
            lines.append(
                f"- line {anomaly.line_number}{request}: {anomaly.reason} on {anomaly.model} "
                f"value={anomaly.value:.1f}, baseline={anomaly.baseline:.1f}"
            )

    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)

    return "\n".join(lines) + "\n"


def _ms(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.0f} ms"
