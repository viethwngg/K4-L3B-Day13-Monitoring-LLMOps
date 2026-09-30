from datetime import datetime, timezone

from scripts.build_dashboard import build_dashboard, build_dashboard_svg


def test_dashboard_renders_six_operational_panels() -> None:
    timestamp = datetime(2026, 9, 30, tzinfo=timezone.utc)
    records = [
        {
            "_time": timestamp,
            "event": "request_received",
            "ts": timestamp.isoformat(),
        },
        {
            "_time": timestamp,
            "event": "response_sent",
            "ts": timestamp.isoformat(),
            "latency_ms": 2500,
            "ttft_ms": 50,
            "cost_usd": 0.002,
            "tokens_in": 20,
            "tokens_out": 80,
            "quality_score": 0.8,
            "tool_success": True,
        },
    ]

    dashboard = build_dashboard(records)

    for title in (
        "Latency &amp; TTFT",
        "Traffic",
        "Errors &amp; retrieval",
        "Cost",
        "Tokens",
        "Quality proxy",
    ):
        assert f"<h2>{title}</h2>" in dashboard
    assert "SLO ≤ 3000 ms" in dashboard
    assert "Retrieval success<strong>100.0%" in dashboard

    dashboard_svg = build_dashboard_svg(dashboard)
    assert dashboard_svg.count('<rect x="') >= 18
    assert "Latency &amp; TTFT" in dashboard_svg
    assert "Retrieval success" in dashboard_svg
