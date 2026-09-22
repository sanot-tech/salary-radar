"""HTML dashboard + CSV/JSON/history exports."""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config


def _clean(rows: list[Any]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            "source": r["source"],
            "title": r["title"],
            "company": r["company"],
            "url": r["url"],
            "location": r["location"],
            "salary_min": r["salary_min"],
            "salary_max": r["salary_max"],
            "currency": r["currency"],
            "role": r["role"],
            "no_code": bool(r["no_code"]),
            "tags": (r["tags"] or "").split(","),
            "first_seen": r["first_seen"],
        })
    return out


def export_csv(path: Any, rows: list[Any]) -> None:
    out_dir = Path(config.OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "source", "role", "no_code", "title", "company",
            "salary_min_usd", "salary_max_usd", "location", "url",
        ])
        for r in rows:
            writer.writerow([
                r["source"], r["role"], r["no_code"], r["title"], r["company"],
                r["salary_min"], r["salary_max"], r["location"], r["url"],
            ])


def export_json(path: Any, payload: dict[str, Any]) -> None:
    Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def update_history(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Append today's totals to a small time-series file for trending."""
    path = config.HISTORY_JSON
    history: list[dict[str, Any]] = []
    if path.exists():
        try:
            history = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
    history.append({
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total": summary["total"],
        "no_code_total": summary["no_code_total"],
    })
    history = history[-90:]  # keep the last 90 days
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return history


def _bar(value: float, max_value: float) -> str:
    if max_value <= 0:
        return ""
    pct = int(round(value / max_value * 100))
    return f'<div class="bar"><div class="bar-fill" style="width:{pct}%"></div></div>'


def render_html(summary: dict[str, Any], rows: list[Any], history: list[dict[str, Any]]) -> str:
    """Render the standalone dashboard. Dark theme, no external assets."""
    role_rows = summary["roles"]
    max_count = max((r["count"] for r in role_rows), default=1)

    def sal(v: int | None) -> str:
        return f"${v:,}" if v else "—"

    roles_html = []
    for rr in role_rows:
        noc = "✓" if rr["no_code_count"] else ""
        roles_html.append(
            f"""
            <tr>
              <td class="role">{html.escape(rr['role'])}</td>
              <td>{rr['count']}</td>
              <td>{rr['companies']}</td>
              <td>{noc}</td>
              <td>{sal(rr['salary_min_median'])}</td>
              <td>{sal(rr['salary_max_median'])}</td>
              <td>{html.escape(rr['top_company'] or '—')}</td>
              <td class="bar-cell">{_bar(rr['count'], max_count)}</td>
            </tr>"""
        )

    jobs_html = []
    for j in _clean(rows)[:40]:
        tag_badges = "".join(
            f'<span class="tag">{html.escape(t)}</span>' for t in (j["tags"] or [])[:5]
        )
        jobs_html.append(
            f"""
            <tr>
              <td><a href="{html.escape(j['url'])}">{html.escape(j['title'])}</a></td>
              <td>{html.escape(j['company'])}</td>
              <td>{html.escape(j['role'])}</td>
              <td>{'<span class="ok">no-code</span>' if j['no_code'] else ''}</td>
              <td>{sal(j['salary_min'])}-{sal(j['salary_max'])}</td>
              <td>{tag_badges}</td>
            </tr>"""
        )

    source_spans = "".join(
        f'<span class="tag">{html.escape(src)}: {n}</span>'
        for src, n in summary["by_source"].items()
    )

    history_html = ""
    if history:
        day_rows = "".join(
            f"<tr><td>{h['date']}</td><td>{h['total']}</td><td>{h['no_code_total']}</td></tr>"
            for h in history[-14:]
        )
        history_html = f"""
        <section>
          <h2>Trend (last 14 d)</h2>
          <table><tr><th>Date</th><th>Listings</th><th>No-code</th></tr>{day_rows}</table>
        </section>"""

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Salary Radar — Remote IT salary dashboard</title>
<style>
:root {{ color-scheme: dark; }}
body {{ margin:0; font:15px/1.5 system-ui, sans-serif; background:#0d1117; color:#e6edf3; }}
.wrap {{ max-width:1060px; margin:0 auto; padding:24px 20px 60px; }}
h1 {{ font-size:30px; margin:6px 0 2px; }}
h2 {{ font-size:19px; margin:30px 0 10px; border-bottom:1px solid #21262d; padding-bottom:6px; }}
.sub {{ color:#8b949e; }}
.cards {{ display:flex; gap:12px; margin:18px 0; flex-wrap:wrap; }}
.card {{ flex:1 1 200px; background:#161b22; border:1px solid #21262d; border-radius:10px; padding:14px 18px; }}
.card b {{ font-size:26px; display:block; }}
.badge {{ display:inline-block; padding:2px 10px; border-radius:999px; background:#1f6feb22; color:#58a6ff; font-size:13px; }}
.ok {{ color:#3fb950; font-size:12px; font-weight:600; }}
table {{ width:100%; border-collapse:collapse; background:#161b22; border-radius:10px; overflow:hidden; }}
th, td {{ text-align:left; padding:9px 12px; border-bottom:1px solid #21262d; vertical-align:top; }}
th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:#8b949e; }}
a {{ color:#58a6ff; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.tag {{ display:inline-block; margin:2px 2px; padding:1px 8px; border-radius:999px; background:#161b22; border:1px solid #30363d; font-size:12px; color:#8b949e; }}
.bar-cell {{ width:80px; }}
.bar {{ background:#21262d; border-radius:4px; height:8px; }}
.bar-fill {{ background:linear-gradient(90deg,#1f6feb,#3fb950); height:8px; border-radius:4px; }}
footer {{ margin-top:40px; color:#8b949e; font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>💹 Salary Radar</h1>
  <p class="sub">Remote IT salary dashboard · English job boards · generated {html.escape(generated_at)}</p>

  <div class="cards">
    <div class="card"><b>{summary['total']}</b> listings tracked</div>
    <div class="card"><b>{summary['no_code_total']}</b><span class="badge">no-code friendly</span></div>
    <div class="card"><b>{len(summary['by_source'])}</b> job sources</div>
    <div class="card"><b>daily</b> auto-updated via GitHub Actions</div>
  </div>
  <div>{source_spans}</div>

  <h2>Roles &amp; salary medians (USD)</h2>
  <table>
    <tr><th>Role</th><th>Listings</th><th>Companies</th><th>No-code</th><th>Min $</th><th>Max $</th><th>Top company</th><th>Share</th></tr>
    {''.join(roles_html)}
  </table>

  <h2>Latest listings</h2>
  <table>
    <tr><th>Title</th><th>Company</th><th>Role</th><th>Level</th><th>Salary $</th><th>Tags</th></tr>
    {''.join(jobs_html) if jobs_html else '<tr><td colspan="6">No data yet — run: <code>env python3 main.py collect</code></td></tr>'}
  </table>

  {history_html}

  <footer>
    Salary Radar · filtered from public English APIs · code:% y% · only stdlib.
  </footer>
</div>
</body>
</html>"""


def write_all_summary_artifacts(summary: dict[str, Any], rows: list[Any], history: list[dict[str, Any]]) -> None:
    Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    export_csv(config.REPORT_CSV, rows)
    export_json(config.REPORT_JSON, summary)
    Path(config.REPORT_HTML).write_text(render_html(summary, rows, history), encoding="utf-8")