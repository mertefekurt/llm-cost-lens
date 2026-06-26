from llm_cost_lens.parser import parse_jsonl
from llm_cost_lens.pricing import DEFAULT_PRICING


def test_parse_openai_usage_and_estimates_cost() -> None:
    records, warnings = parse_jsonl(
        [
            '{"model":"gpt-4o-mini","request_id":"r1","usage":'
            '{"prompt_tokens":1000,"completion_tokens":500},"latency_ms":120}'
        ],
        DEFAULT_PRICING,
    )

    assert warnings == []
    assert records[0].request_id == "r1"
    assert records[0].usage.total_tokens == 1500
    assert records[0].cost_usd == 0.00045


def test_parse_accepts_input_output_token_aliases() -> None:
    records, warnings = parse_jsonl(
        ['{"model":"gpt-4.1-mini","team":"ops","usage":{"input_tokens":30,"output_tokens":5}}'],
        DEFAULT_PRICING,
    )

    assert warnings == []
    assert records[0].group == "ops"
    assert records[0].usage.prompt_tokens == 30
    assert records[0].usage.completion_tokens == 5


def test_parse_skips_invalid_lines_with_warning() -> None:
    records, warnings = parse_jsonl(
        ["not-json", '{"model":"gpt-4o-mini","usage":{}}'],
        DEFAULT_PRICING,
    )

    assert records == []
    assert "invalid JSON" in warnings[0]
    assert "usage must include token counts" in warnings[1]
