from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "submission" / "evidence" / "11-dashboard-overview.html"
DEFAULT_SVG_PATH = REPO_ROOT / "submission" / "evidence" / "11-dashboard-overview.svg"


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((percentile / 100) * len(ordered) + 0.5) - 1))
    return ordered[index]


def _load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            record["_time"] = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        records.append(record)
    return records


def _bar(value: float, limit: float, *, lower_is_better: bool = True) -> str:
    ratio = 0 if limit <= 0 else min(100, value / limit * 100)
    healthy = value <= limit if lower_is_better else value >= limit
    state = "healthy" if healthy else "breach"
    return (
        f'<div class="bar" role="img" aria-label="Value {value:.2f}, threshold {limit:.2f}">'
        f'<span class="fill {state}" style="width:{ratio:.1f}%"></span>'
        '<span class="threshold" aria-hidden="true"></span></div>'
    )


def build_dashboard(records: list[dict]) -> str:
    if not records:
        raise ValueError("No valid log records were found")

    window_end = max(record["_time"] for record in records)
    window_start = window_end - timedelta(minutes=60)
    window = [record for record in records if record["_time"] >= window_start]
    requests = [record for record in window if record.get("event") == "request_received"]
    responses = [record for record in window if record.get("event") == "response_sent"]
    failures = [record for record in window if record.get("event") == "request_failed"]

    latencies = [float(record["latency_ms"]) for record in responses if "latency_ms" in record]
    ttfts = [float(record["ttft_ms"]) for record in responses if "ttft_ms" in record]
    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    p99 = _percentile(latencies, 99)
    ttft_p95 = _percentile(ttfts, 95)

    request_count = len(requests)
    active_minutes = max(1.0, (window_end - min((record["_time"] for record in requests), default=window_end)).total_seconds() / 60)
    requests_per_minute = request_count / active_minutes
    error_rate = len(failures) / request_count * 100 if request_count else 0.0

    tool_results = [record.get("tool_success") for record in window if record.get("tool_success") is not None]
    retrieval_success = (
        sum(result is True for result in tool_results) / len(tool_results) * 100
        if tool_results
        else 0.0
    )
    total_cost = sum(float(record.get("cost_usd", 0)) for record in responses)
    tokens_in = sum(int(record.get("tokens_in", 0)) for record in responses)
    tokens_out = sum(int(record.get("tokens_out", 0)) for record in responses)
    qualities = [float(record["quality_score"]) for record in responses if "quality_score" in record]
    quality_avg = mean(qualities) if qualities else 0.0

    start_label = window_start.astimezone().strftime("%Y-%m-%d %H:%M")
    end_label = window_end.astimezone().strftime("%H:%M %Z")
    source = html.escape(str(DEFAULT_LOG_PATH.relative_to(REPO_ROOT)))

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>K4-L3B LLMOps Dashboard</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; background:#08111f; color:#e6edf7; }}
body {{ margin:0; padding:32px; background:radial-gradient(circle at top right,#12284a,#08111f 48%); }}
main {{ max-width:1180px; margin:auto; }}
header {{ display:flex; justify-content:space-between; gap:24px; align-items:end; margin-bottom:24px; }}
h1 {{ margin:0 0 6px; font-size:28px; font-weight:600; }}
.sub {{ color:#9fb0c8; font-size:14px; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
.panel {{ background:#0f1c2e; border:1px solid #223652; border-radius:14px; padding:20px; min-height:180px; }}
.panel h2 {{ margin:0 0 16px; font-size:15px; font-weight:500; color:#b9c7da; }}
.value {{ font-size:34px; font-weight:600; font-variant-numeric:tabular-nums; }}
.unit {{ color:#91a2ba; font-size:13px; margin-left:5px; }}
.facts {{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px 14px; margin-top:16px; font-size:13px; }}
.facts span {{ color:#91a2ba; }}
.facts strong {{ display:block; color:#e6edf7; margin-top:3px; font-weight:500; }}
.bar {{ height:8px; margin-top:18px; background:#24344a; border-radius:5px; position:relative; overflow:visible; }}
.fill {{ display:block; height:100%; border-radius:5px; }}
.healthy {{ background:#37c99b; }} .breach {{ background:#ff6b6b; }}
.threshold {{ position:absolute; left:100%; top:-4px; width:2px; height:16px; background:#f2c94c; }}
.threshold-label {{ margin-top:8px; color:#91a2ba; font-size:12px; }}
.footer {{ margin-top:18px; display:flex; justify-content:space-between; color:#7f92ad; font-size:12px; }}
@media (max-width:850px) {{ .grid {{ grid-template-columns:1fr 1fr; }} }}
@media (max-width:560px) {{ body {{ padding:18px; }} header {{ display:block; }} .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><main>
<header><div><h1>Monitoring &amp; LLMOps</h1><div class="sub">Metrics → Logs → Traces · 60-minute operational view</div></div><div class="sub">{start_label} – {end_label}</div></header>
<section class="grid">
<article class="panel"><h2>Latency &amp; TTFT</h2><div class="value">{p95:.0f}<span class="unit">ms P95</span></div>{_bar(p95, 3000)}<div class="threshold-label">SLO ≤ 3000 ms</div><div class="facts"><span>P50<strong>{p50:.0f} ms</strong></span><span>P99<strong>{p99:.0f} ms</strong></span><span>TTFT P95<strong>{ttft_p95:.0f} ms</strong></span><span>Responses<strong>{len(responses)}</strong></span></div></article>
<article class="panel"><h2>Traffic</h2><div class="value">{request_count}<span class="unit">requests</span></div>{_bar(requests_per_minute, 1, lower_is_better=False)}<div class="threshold-label">Traffic floor ≥ 1 request/min</div><div class="facts"><span>Observed rate<strong>{requests_per_minute:.2f}/min</strong></span><span>Window<strong>60 min</strong></span></div></article>
<article class="panel"><h2>Errors &amp; retrieval</h2><div class="value">{error_rate:.1f}<span class="unit">% errors</span></div>{_bar(error_rate, 2)}<div class="threshold-label">Error guardrail ≤ 2%</div><div class="facts"><span>Failures<strong>{len(failures)}</strong></span><span>Retrieval success<strong>{retrieval_success:.1f}%</strong></span></div></article>
<article class="panel"><h2>Cost</h2><div class="value">${total_cost:.4f}<span class="unit">USD</span></div>{_bar(total_cost, 2.5)}<div class="threshold-label">Window budget ≤ $2.50</div><div class="facts"><span>Average/request<strong>${(total_cost / len(responses) if responses else 0):.4f}</strong></span><span>Responses<strong>{len(responses)}</strong></span></div></article>
<article class="panel"><h2>Tokens</h2><div class="value">{tokens_in + tokens_out:,}<span class="unit">total</span></div>{_bar(tokens_in + tokens_out, 50000)}<div class="threshold-label">Window guardrail ≤ 50,000</div><div class="facts"><span>Input<strong>{tokens_in:,}</strong></span><span>Output<strong>{tokens_out:,}</strong></span></div></article>
<article class="panel"><h2>Quality proxy</h2><div class="value">{quality_avg:.2f}<span class="unit">/ 1.00</span></div>{_bar(quality_avg, 0.75, lower_is_better=False)}<div class="threshold-label">Quality floor ≥ 0.75</div><div class="facts"><span>Samples<strong>{len(qualities)}</strong></span><span>Status<strong>{'Healthy' if quality_avg >= 0.75 else 'Below threshold'}</strong></span></div></article>
</section>
<div class="footer"><span>Source: {source}</span><span>Generated from structured logs; no raw prompt or PII shown.</span></div>
</main></body></html>"""


def build_dashboard_svg(dashboard_html: str) -> str:
    panels = re.findall(r'<article class="panel">(.*?)</article>', dashboard_html)
    if len(panels) != 6:
        raise ValueError("Dashboard HTML does not contain six panels")

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img" aria-labelledby="title desc">',
        '<title id="title">K4-L3B Monitoring and LLMOps dashboard</title>',
        '<desc id="desc">Six panels for latency, traffic, errors, cost, tokens, and quality from structured logs.</desc>',
        '<rect width="1200" height="760" fill="#08111f"/>',
        '<text x="44" y="58" fill="#e6edf7" font-family="Segoe UI, sans-serif" font-size="30" font-weight="600">Monitoring &amp; LLMOps</text>',
        '<text x="44" y="86" fill="#9fb0c8" font-family="Segoe UI, sans-serif" font-size="15">Metrics → Logs → Traces · 60-minute operational view</text>',
    ]

    for index, panel in enumerate(panels):
        column = index % 3
        row = index // 3
        x = 40 + column * 385
        y = 120 + row * 295
        title_match = re.search(r"<h2>(.*?)</h2>", panel)
        value_match = re.search(r'<div class="value">(.*?)<span class="unit">(.*?)</span>', panel)
        threshold_match = re.search(r'<div class="threshold-label">(.*?)</div>', panel)
        width_match = re.search(r'class="fill (?:healthy|breach)" style="width:([\d.]+)%"', panel)
        facts = re.findall(r"<span>(.*?)<strong>(.*?)</strong></span>", panel)
        title = html.unescape(title_match.group(1) if title_match else "Panel")
        value = html.unescape(re.sub(r"<[^>]+>", "", value_match.group(1) if value_match else "0"))
        unit = html.unescape(value_match.group(2) if value_match else "")
        threshold = html.unescape(threshold_match.group(1) if threshold_match else "")
        fill_width = 300 * float(width_match.group(1) if width_match else 0) / 100
        color = "#ff6b6b" if 'class="fill breach"' in panel else "#37c99b"

        svg_parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="345" height="255" rx="14" fill="#0f1c2e" stroke="#223652"/>',
                f'<text x="{x + 22}" y="{y + 36}" fill="#b9c7da" font-family="Segoe UI, sans-serif" font-size="16">{html.escape(title)}</text>',
                f'<text x="{x + 22}" y="{y + 92}" fill="#e6edf7" font-family="Segoe UI, sans-serif" font-size="36" font-weight="600">{html.escape(value)}</text>',
                f'<text x="{x + 22}" y="{y + 117}" fill="#91a2ba" font-family="Segoe UI, sans-serif" font-size="14">{html.escape(unit)}</text>',
                f'<rect x="{x + 22}" y="{y + 137}" width="300" height="8" rx="4" fill="#24344a"/>',
                f'<rect x="{x + 22}" y="{y + 137}" width="{fill_width:.1f}" height="8" rx="4" fill="{color}"/>',
                f'<text x="{x + 22}" y="{y + 168}" fill="#91a2ba" font-family="Segoe UI, sans-serif" font-size="13">{html.escape(threshold)}</text>',
            ]
        )
        for fact_index, (label, fact_value) in enumerate(facts[:4]):
            fact_x = x + 22 + (fact_index % 2) * 160
            fact_y = y + 202 + (fact_index // 2) * 35
            svg_parts.append(
                f'<text x="{fact_x}" y="{fact_y}" fill="#91a2ba" font-family="Segoe UI, sans-serif" font-size="12">{html.escape(html.unescape(label))}: '
                f'<tspan fill="#e6edf7">{html.escape(html.unescape(fact_value))}</tspan></text>'
            )

    svg_parts.extend(
        [
            '<text x="44" y="735" fill="#7f92ad" font-family="Segoe UI, sans-serif" font-size="13">Source: data/logs.jsonl · Aggregate metrics only · No raw prompt or PII</text>',
            "</svg>",
        ]
    )
    return "\n".join(svg_parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the six-panel CP2 dashboard")
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--svg-output", type=Path, default=DEFAULT_SVG_PATH)
    args = parser.parse_args()

    try:
        dashboard = build_dashboard(_load_records(args.logs))
        dashboard_svg = build_dashboard_svg(dashboard)
    except (OSError, ValueError) as exc:
        print(f"Dashboard build failed: {exc}")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dashboard, encoding="utf-8")
    args.svg_output.parent.mkdir(parents=True, exist_ok=True)
    args.svg_output.write_text(dashboard_svg, encoding="utf-8")
    print(f"Dashboard written to {args.output}")
    print(f"Dashboard image written to {args.svg_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
