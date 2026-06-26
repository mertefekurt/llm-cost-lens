from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class CallRecord:
    line_number: int
    model: str
    usage: Usage
    timestamp: datetime | None = None
    latency_ms: float | None = None
    cost_usd: float | None = None
    status: str = "ok"
    endpoint: str = "chat.completions"
    group: str = "default"
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Pricing:
    model: str
    input_per_million: float
    output_per_million: float

    def estimate(self, usage: Usage) -> float:
        input_cost = usage.prompt_tokens / 1_000_000 * self.input_per_million
        output_cost = usage.completion_tokens / 1_000_000 * self.output_per_million
        return input_cost + output_cost


@dataclass(frozen=True)
class GroupSummary:
    name: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    avg_latency_ms: float | None
    error_rate: float


@dataclass(frozen=True)
class Anomaly:
    line_number: int
    request_id: str | None
    model: str
    reason: str
    value: float
    baseline: float


@dataclass(frozen=True)
class LensReport:
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    error_rate: float
    budget_usd: float | None
    budget_used_ratio: float | None
    groups: list[GroupSummary]
    anomalies: list[Anomaly]
    warnings: list[str]
