from llm_cost_lens.analysis import analyze_calls
from llm_cost_lens.models import CallRecord, Usage


def _record(line: int, tokens: int, *, latency: float = 100, status: str = "ok") -> CallRecord:
    return CallRecord(
        line_number=line,
        model="gpt-4o-mini",
        usage=Usage(prompt_tokens=tokens, completion_tokens=0),
        latency_ms=latency,
        cost_usd=tokens * 0.001,
        status=status,
        group="platform",
    )


def test_report_totals_and_budget_ratio() -> None:
    report = analyze_calls([_record(1, 100), _record(2, 300)], budget_usd=1.0)

    assert report.calls == 2
    assert report.total_tokens == 400
    assert report.cost_usd == 0.4
    assert report.budget_used_ratio == 0.4


def test_group_by_team_and_error_rate() -> None:
    report = analyze_calls([_record(1, 100), _record(2, 100, status="error")], group_by="team")

    assert report.error_rate == 0.5
    assert report.groups[0].name == "platform"
    assert report.groups[0].error_rate == 0.5


def test_detects_token_and_latency_anomalies() -> None:
    report = analyze_calls(
        [_record(1, 100), _record(2, 110), _record(3, 120), _record(4, 1000, latency=9000)],
        anomaly_zscore=1.4,
        latency_threshold_ms=1000,
    )

    reasons = {anomaly.reason for anomaly in report.anomalies}
    assert reasons == {"token spike", "slow call"}
