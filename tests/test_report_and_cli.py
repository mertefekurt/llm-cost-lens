from pathlib import Path

from llm_cost_lens.cli import main
from llm_cost_lens.models import LensReport
from llm_cost_lens.report import render_report


def test_render_markdown_includes_core_sections() -> None:
    rendered = render_report(
        LensReport(
            calls=1,
            prompt_tokens=10,
            completion_tokens=4,
            total_tokens=14,
            cost_usd=0.01,
            avg_latency_ms=120,
            p95_latency_ms=120,
            error_rate=0,
            budget_usd=1,
            budget_used_ratio=0.01,
            groups=[],
            anomalies=[],
            warnings=[],
        )
    )

    assert "# LLM Cost Lens Report" in rendered
    assert "estimated cost: $0.0100" in rendered
    assert "budget: $1.00" in rendered


def test_cli_writes_json_report(tmp_path: Path) -> None:
    log_file = tmp_path / "calls.jsonl"
    output_file = tmp_path / "report.json"
    log_file.write_text(
        '{"model":"gpt-4o-mini","usage":{"prompt_tokens":100,"completion_tokens":25}}\n',
        encoding="utf-8",
    )

    exit_code = main([str(log_file), "--format", "json", "--output", str(output_file)])

    assert exit_code == 0
    assert '"calls": 1' in output_file.read_text(encoding="utf-8")


def test_cli_help_without_log_file(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Inspect LLM API JSONL logs" in captured.out
