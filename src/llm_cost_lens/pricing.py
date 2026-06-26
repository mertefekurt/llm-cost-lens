from __future__ import annotations

import json
from pathlib import Path

from llm_cost_lens.models import Pricing, Usage

DEFAULT_PRICING: dict[str, Pricing] = {
    "gpt-4o-mini": Pricing("gpt-4o-mini", input_per_million=0.15, output_per_million=0.60),
    "gpt-4o": Pricing("gpt-4o", input_per_million=2.50, output_per_million=10.00),
    "gpt-4.1-mini": Pricing("gpt-4.1-mini", input_per_million=0.40, output_per_million=1.60),
    "gpt-4.1": Pricing("gpt-4.1", input_per_million=2.00, output_per_million=8.00),
    "claude-3-5-sonnet": Pricing(
        "claude-3-5-sonnet", input_per_million=3.00, output_per_million=15.00
    ),
}


def load_pricing(path: Path | None = None) -> dict[str, Pricing]:
    if path is None:
        return DEFAULT_PRICING

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read pricing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"pricing file is not valid JSON: {path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("pricing file must be a JSON object keyed by model name")

    pricing: dict[str, Pricing] = {}
    for model, values in raw.items():
        if not isinstance(values, dict):
            raise ValueError(f"pricing for {model!r} must be an object")
        try:
            pricing[model] = Pricing(
                model=model,
                input_per_million=float(values["input_per_million"]),
                output_per_million=float(values["output_per_million"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"pricing for {model!r} must include numeric input_per_million and "
                "output_per_million"
            ) from exc
    return pricing


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    pricing: dict[str, Pricing],
) -> float:
    model_pricing = pricing.get(model)
    if model_pricing is None:
        return 0.0
    return model_pricing.estimate(Usage(prompt_tokens, completion_tokens))
