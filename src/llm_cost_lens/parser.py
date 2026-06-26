from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_cost_lens.models import CallRecord, Pricing, Usage


class LogParseError(ValueError):
    pass


def load_jsonl(path: Path, pricing: dict[str, Pricing]) -> tuple[list[CallRecord], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise LogParseError(f"could not read log file: {path}") from exc
    return parse_jsonl(lines, pricing)


def parse_jsonl(
    lines: Iterable[str],
    pricing: dict[str, Pricing],
) -> tuple[list[CallRecord], list[str]]:
    records: list[CallRecord] = []
    warnings: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            warnings.append(f"line {line_number}: skipped invalid JSON")
            continue
        try:
            records.append(_parse_record(payload, line_number, pricing))
        except LogParseError as exc:
            warnings.append(str(exc))
    return records, warnings


def _parse_record(
    payload: dict[str, Any],
    line_number: int,
    pricing: dict[str, Pricing],
) -> CallRecord:
    if not isinstance(payload, dict):
        raise LogParseError(f"line {line_number}: expected a JSON object")

    model = _string(payload, "model", default="unknown")
    usage_data = payload.get("usage")
    if not isinstance(usage_data, dict):
        raise LogParseError(f"line {line_number}: missing usage object")

    prompt_tokens = _int_any(usage_data, ("prompt_tokens", "input_tokens"))
    completion_tokens = _int_any(usage_data, ("completion_tokens", "output_tokens"))
    if prompt_tokens is None or completion_tokens is None:
        total_tokens = _int_any(usage_data, ("total_tokens",))
        if total_tokens is None:
            raise LogParseError(f"line {line_number}: usage must include token counts")
        prompt_tokens = prompt_tokens or total_tokens
        completion_tokens = completion_tokens or 0

    cost_usd = _float(payload, "cost_usd")
    if cost_usd is None:
        model_pricing = pricing.get(model)
        if model_pricing is not None:
            cost_usd = model_pricing.estimate(Usage(prompt_tokens, completion_tokens))

    return CallRecord(
        line_number=line_number,
        model=model,
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        timestamp=_timestamp(payload.get("timestamp") or payload.get("created_at")),
        latency_ms=_float_any(payload, ("latency_ms", "duration_ms", "elapsed_ms")),
        cost_usd=cost_usd,
        status=_string(payload, "status", default="ok"),
        endpoint=_string(payload, "endpoint", default="chat.completions"),
        group=_string_any(payload, ("team", "project", "user", "service"), default="default"),
        request_id=_maybe_string(payload.get("request_id") or payload.get("id")),
        metadata={k: v for k, v in payload.items() if k not in _KNOWN_KEYS},
    )


_KNOWN_KEYS = {
    "created_at",
    "duration_ms",
    "elapsed_ms",
    "endpoint",
    "id",
    "latency_ms",
    "model",
    "project",
    "request_id",
    "service",
    "status",
    "team",
    "timestamp",
    "usage",
    "user",
    "cost_usd",
}


def _timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _int_any(payload: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                return None
            return max(parsed, 0)
    return None


def _float(payload: dict[str, Any], key: str) -> float | None:
    return _float_any(payload, (key,))


def _float_any(payload: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def _string(payload: dict[str, Any], key: str, *, default: str) -> str:
    return _string_any(payload, (key,), default=default)


def _string_any(payload: dict[str, Any], keys: tuple[str, ...], *, default: str) -> str:
    for key in keys:
        value = _maybe_string(payload.get(key))
        if value:
            return value
    return default


def _maybe_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
