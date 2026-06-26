from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev

from llm_cost_lens.models import Anomaly, CallRecord, GroupSummary, LensReport


def analyze_calls(
    records: list[CallRecord],
    *,
    budget_usd: float | None = None,
    group_by: str = "model",
    anomaly_zscore: float = 2.5,
    latency_threshold_ms: float | None = None,
    warnings: list[str] | None = None,
) -> LensReport:
    report_warnings = list(warnings or [])
    if not records:
        return LensReport(
            calls=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            avg_latency_ms=None,
            p95_latency_ms=None,
            error_rate=0.0,
            budget_usd=budget_usd,
            budget_used_ratio=None,
            groups=[],
            anomalies=[],
            warnings=report_warnings,
        )

    prompt_tokens = sum(record.usage.prompt_tokens for record in records)
    completion_tokens = sum(record.usage.completion_tokens for record in records)
    total_tokens = prompt_tokens + completion_tokens
    total_cost = sum(record.cost_usd or 0.0 for record in records)
    latencies = [record.latency_ms for record in records if record.latency_ms is not None]
    errors = [record for record in records if record.status.lower() not in {"ok", "success", "200"}]
    budget_used_ratio = None if budget_usd in (None, 0) else total_cost / budget_usd

    anomalies = _token_anomalies(records, anomaly_zscore)
    if latency_threshold_ms is not None:
        anomalies.extend(_latency_anomalies(records, latency_threshold_ms))

    return LensReport(
        calls=len(records),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=total_cost,
        avg_latency_ms=mean(latencies) if latencies else None,
        p95_latency_ms=_percentile(latencies, 0.95) if latencies else None,
        error_rate=len(errors) / len(records),
        budget_usd=budget_usd,
        budget_used_ratio=budget_used_ratio,
        groups=_group_summaries(records, group_by),
        anomalies=anomalies,
        warnings=report_warnings,
    )


def _group_summaries(records: list[CallRecord], group_by: str) -> list[GroupSummary]:
    buckets: dict[str, list[CallRecord]] = defaultdict(list)
    for record in records:
        buckets[_group_value(record, group_by)].append(record)

    summaries = []
    for name, group_records in buckets.items():
        latencies = [record.latency_ms for record in group_records if record.latency_ms is not None]
        errors = [
            record
            for record in group_records
            if record.status.lower() not in {"ok", "success", "200"}
        ]
        prompt_tokens = sum(record.usage.prompt_tokens for record in group_records)
        completion_tokens = sum(record.usage.completion_tokens for record in group_records)
        summaries.append(
            GroupSummary(
                name=name,
                calls=len(group_records),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=sum(record.cost_usd or 0.0 for record in group_records),
                avg_latency_ms=mean(latencies) if latencies else None,
                error_rate=len(errors) / len(group_records),
            )
        )
    return sorted(summaries, key=lambda item: item.cost_usd, reverse=True)


def _group_value(record: CallRecord, group_by: str) -> str:
    if group_by == "team":
        return record.group
    if group_by == "endpoint":
        return record.endpoint
    return record.model


def _token_anomalies(records: list[CallRecord], zscore: float) -> list[Anomaly]:
    values = [record.usage.total_tokens for record in records]
    if len(values) < 3:
        return []
    baseline = mean(values)
    spread = pstdev(values)
    if spread == 0:
        return []
    anomalies = []
    for record in records:
        score = (record.usage.total_tokens - baseline) / spread
        if score >= zscore:
            anomalies.append(
                Anomaly(
                    line_number=record.line_number,
                    request_id=record.request_id,
                    model=record.model,
                    reason="token spike",
                    value=record.usage.total_tokens,
                    baseline=baseline,
                )
            )
    return anomalies


def _latency_anomalies(records: list[CallRecord], threshold_ms: float) -> list[Anomaly]:
    anomalies = []
    for record in records:
        if record.latency_ms is not None and record.latency_ms > threshold_ms:
            anomalies.append(
                Anomaly(
                    line_number=record.line_number,
                    request_id=record.request_id,
                    model=record.model,
                    reason="slow call",
                    value=record.latency_ms,
                    baseline=threshold_ms,
                )
            )
    return anomalies


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * percentile)))
    return ordered[index]
