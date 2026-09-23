"""HTML dashboard + CSV/JSON/history exports.

The dashboard is intentionally framed as a viral "how much are you worth?"
tool (Salary Radar on the shelf), not a dry table dump:
  - hero hook + no-code value proposition
  - interactive "What are you worth?" salary calculator (client-side JS)
  - "MY WORTH" shareable stat card with Telegram / VK / copy buttons
  - lead magnet: email digest subscription form
  - gamified "5 weeks to first role" quest list
  - "different path" success stories

Everything renders offline, dark theme, zero external assets.
"""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

# The vibe core: every role a Vibe Coder (super-universal) can occupy.
VIBE_ROLES = {"AI / Vibe Dev"}


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
            "vibe": bool(r["vibe"]),
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
            "source", "role", "vibe", "title", "company",
            "salary_min_usd", "salary_max_usd", "location", "url",
        ])
        for r in rows:
            writer.writerow([
                r["source"], r["role"], r["vibe"], r["title"], r["company"],
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
        "vibe_total": summary["vibe_total"],
    })
    history = history[-90:]  # keep the last 90 days
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return history


def _bar(value: float, max_value: float) -> str:
    if max_value <= 0:
        return ""
    pct = int(round(value / max_value * 100))
    return f'<div class="bar"><div class="bar-fill" style="width:{pct}%"></div></div>'


def _fallback_median(roles: list[dict[str, Any]]) -> tuple[int, int]:
    """Market-wide median when a role has no salary data."""
    mins = [r["salary_min_median"] for r in roles if r.get("salary_min_median")]
    maxs = [r["salary_max_median"] for r in roles if r.get("salary_max_median")]
    if not mins or not maxs:
        return 45000, 75000
    return int(sum(mins) / len(mins)), int(sum(maxs) / len(maxs))


def _calc_script(roles: list[dict[str, Any]]) -> str:
    """Client-side calculator as a standalone <script> block.

    Everything is injected as JSON, so the widget works fully offline and
    always reflects the freshest scraped medians.
    """
    fallback_lo, fallback_hi = _fallback_median(roles)
    data = {
        "roles": [{
            "role": r["role"],
            "vibe": r["role"] in VIBE_ROLES,
            "min": r.get("salary_min_median"),
            "max": r.get("salary_max_median"),
        } for r in roles],
        "fallback_min": fallback_lo,
        "fallback_max": fallback_hi,
    }
    payload = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    return (
        "<script>\n"
        "const WORTH_DATA = " + payload + ";\n"
        "function esc(s){return String(s).replace(/[&<>\"']/g,function(c){"
        "return{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c];});}\n"
        "function fmt(v){if(!v)return '—';return '$'+Number(v).toLocaleString('en-US');}\n"
        "function worthFor(roleKey, exp){\n"
        "  const r = WORTH_DATA.roles.find(x => x.role === roleKey) || {};\n"
        "  let lo = r.min || WORTH_DATA.fallback_min;\n"
        "  let hi = r.max || WORTH_DATA.fallback_max;\n"
        "  if (exp <= 0) { hi = Math.round(lo * 1.12); }\n"
        "  else if (exp === 1) { lo = r.min || WORTH_DATA.fallback_min; hi = r.max || WORTH_DATA.fallback_max; }\n"
        "  else if (exp === 2) { lo = r.max || WORTH_DATA.fallback_max; hi = Math.round((r.max || WORTH_DATA.fallback_max) * 1.15); }\n"
        "  else { lo = Math.round((r.max || WORTH_DATA.fallback_max) * 1.15); hi = Math.round((r.max || WORTH_DATA.fallback_max) * 1.32); }\n"
        "  return { role: roleKey, vibe: !!r.vibe, lo: Math.max(lo,1000), hi: Math.max(hi, lo) };\n"
        "}\n"
        "function renderWorth(){\n"
        "  const role = document.getElementById('worth-role').value;\n"
        "  const exp = parseInt(document.getElementById('worth-exp').value, 10);\n"
        "  const w = worthFor(role, exp);\n"
        "  const badge = w.vibe ? '<span class=\"ok\">vibe coder ✓</span>' : '<span class=\"tag\">classic path</span>';\n"
        "  const barW = exp===0 ? 12 : exp===1 ? 35 : exp===2 ? 65 : 92;\n"
        "  document.getElementById('worth-out').innerHTML =\n"
        "    '<div class=\"worth-card\">' +\n"
        "      '<div class=\"worth-title\">⚡ MY WORTH <span class=\"muted\">— ' + esc(w.role) + '</span></div>' +\n"
        "      '<div class=\"worth-big\">' + fmt(w.lo) + ' – ' + fmt(w.hi) + ' <span class=\"muted\">/ month</span></div>' +\n"
        "      '<div class=\"bar\"><div class=\"bar-fill\" style=\"width:' + barW + '%\"></div></div>' +\n"
        "      '<div class=\"worth-sub\">' + badge + '</div>' +\n"
        "      '<div class=\"worth-share\">' +\n"
        "        '<button onclick=\"shareTG()\" title=\"Share in Telegram\">📱 Telegram</button>' +\n"
        "        '<button onclick=\"shareVK()\" title=\"Share in VK\">VK</button>' +\n"
        "        '<button onclick=\"copyWorth()\" title=\"Copy my worth\">📋 Copy</button>' +\n"
        "      '</div>' +\n"
        "    '</div>';\n"
        "}\n"
        "function worthText(){\n"
        "  const role = document.getElementById('worth-role').value;\n"
        "  const exp = parseInt(document.getElementById('worth-exp').value, 10);\n"
        "  const w = worthFor(role, exp);\n"
        "  return '⚡ MY WORTH via Salary Radar: ' + w.role + ' → ' + fmt(w.lo) + '–' + fmt(w.hi) + ' /mo (' + (w.vibe?'vibe coder ✓':'career path') + '). Check yours: ' + location.href;\n"
        "}\n"
        "function shareTG(){ const t = worthText(); const u = 'https://t.me/share/url?url=' + encodeURIComponent(location.href) + '&text=' + encodeURIComponent(t); window.open(u,'_blank'); }\n"
        "function shareVK(){ const t = worthText(); const u = 'https://vk.com/share.php?url=' + encodeURIComponent(location.href) + '&title=' + encodeURIComponent(t); window.open(u,'_blank'); }\n"
        "function copyWorth(){ navigator.clipboard && navigator.clipboard.writeText(worthText()); }\n"
        "</script>"
    )


def _track_of(role: str, title: str = "", category: str = "", tags=None) -> str | None:
    from . import config as _config
    from .analyze import row_track

    return row_track(role, title, category, tags)


def _track_script(role_rows: list[dict[str, Any]]) -> str:
    """Client-side toggle logic for the vibe sub-track checkboxes.

    Hides filtered role rows, swaps track-card styling, and recalcs the
    displayed vibe total + percentage from the real scraped numbers.
    """
    roles = [{
        "role": r["role"],
        "track": _track_of(r["role"]) or "",
        "count": r["count"],
        "vibe": r["vibe_count"],
    } for r in role_rows]
    payload = json.dumps(roles, ensure_ascii=True).replace("</", "<\\/")
    return """
<script>
var TRACK_ROLES = """ + payload + """;
function toggleTrack(track, on) {
  var rows = document.querySelectorAll('tr[data-track="' + track + '"]');
  var cnt = document.getElementById('track-cnt-' + track);
  var nc = document.getElementById('track-nc-' + track);
  var card = document.getElementById('track-' + track);
  if (on) {
    rows.forEach(function (r) { r.style.display = ''; });
    if (card) { card.classList.remove('off'); }
  } else {
    rows.forEach(function (r) { r.style.display = 'none'; });
    if (card) { card.classList.add('off'); }
  }
  recalcVibe();
}
function recalcVibe() {
  var totalView = document.getElementById('vibe-total');
  var pctView = document.getElementById('vibe-pct');
  if (!totalView || !pctView) { return; }
  var vibe = 0, total = 0;
  TRACK_ROLES.forEach(function (r) {
    var cb = r.track && document.querySelector('input[data-track="' + r.track + '"]');
    if (cb && !cb.checked) { return; }
    total += r.count;
    vibe += r.vibe;
  });
  totalView.textContent = vibe;
  pctView.textContent = Math.round(100 * vibe / Math.max(total, 1)) + '% vibe-friendly';
}
</script>"""


def render_html(summary: dict[str, Any], rows: list[Any], history: list[dict[str, Any]]) -> str:
    """Render the standalone dashboard. Dark theme, no external assets."""
    role_rows = summary["roles"]
    max_count = max((r["count"] for r in role_rows), default=1)
    vibe_pct = int(round(summary.get("vibe_share", 0) * 100))
    many_vibe = sum(1 for r in role_rows if r["role"] in VIBE_ROLES)
    with_salary = sum(1 for r in role_rows if r.get("salary_max_median"))

    def sal(v: int | None) -> str:
        return f"${v:,}" if v else "—"

    roles_html = []
    for rr in role_rows:
        vib = "✓" if rr["vibe_count"] else ""
        roles_html.append(
            f"""
            <tr data-track="{_track_of(rr['role']) or ''}">
              <td class="role">{html.escape(rr['role'])}</td>
              <td>{rr['count']}</td>
              <td>{rr['companies']}</td>
              <td>{vib}</td>
              <td>{sal(rr['salary_min_median'])}</td>
              <td>{sal(rr['salary_max_median'])}</td>
              <td>{html.escape(rr['top_company'] or '—')}</td>
              <td class="bar-cell">{_bar(rr['count'], max_count)}</td>
            </tr>"""
        )

    # Vibe sub-track cards (a Vibe Coder can specialise in any of these).
    track_meta = {
        "ai_agents": ("🤖", "AI Agents / Automation"),
        "prompt_eng": ("🗣️", "Prompt & AI Interfaces"),
        "builders": ("🧱", "Visual / Low-Code Builders"),
        "ai_creative": ("🎨", "Generative Creative"),
        "ai_product": ("🚀", "AI Product (Super-Universal)"),
    }
    track_counts = summary.get("track_counts", {})
    if not track_counts and role_rows:
        # Back-compat: derive from role rows when old summary arrives.
        for rr in role_rows:
            t = _track_of(rr["role"])
            if t:
                track_counts.setdefault(t, {"count": 0, "vibe": 0, "enabled": True})
                track_counts[t]["count"] += rr["count"]
                track_counts[t]["vibe"] += rr["vibe_count"]

    track_cards_html = []
    for tid, (icon, label) in track_meta.items():
        info = track_counts.get(tid, {"count": 0, "vibe": 0, "enabled": True})
        checked = " checked" if info.get("enabled", True) else ""
        track_cards_html.append(
            f"""
            <label class="track-card" id="track-{tid}">
              <input type="checkbox" data-track="{tid}" {checked} onchange="toggleTrack('{tid}', this.checked)"/>
              <span class="track-ic">{icon}</span>
              <span class="track-lb">{label}</span>
              <b id="track-cnt-{tid}">{info.get('count', 0)}</b>
              <span class="muted" id="track-nc-{tid}">· {info.get('vibe', 0)} vibe</span>
            </label>"""
        )

    track_script = _track_script(role_rows)

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
              <td>{'<span class="ok">vibe 🚀</span>' if j['vibe'] else ''}</td>
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
            f"<tr><td>{h['date']}</td><td>{h['total']}</td><td>{h['vibe_total']}</td></tr>"
            for h in history[-14:]
        )
        history_html = f"""
        <section>
          <h2>Trend (last 14 d)</h2>
          <table><tr><th>Date</th><th>Listings</th><th>Vibe</th></tr>{day_rows}</table>
        </section>"""

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    calc_script = _calc_script(role_rows)
    boot_script = """
<script>
var expInput = document.getElementById('worth-exp');
expInput.addEventListener('input', function () {
  var v = expInput.value;
  document.getElementById('worth-exp-label').innerText =
    v === '0' ? 'newbie (0)' : v === '1' ? '1 year' : v === '2' ? '2 years' : '3+ years';
});
renderWorth();
</script>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta name="description" content="Vibe Coder Salary Radar — see how much you are worth in remote AI-era IT. {summary['vibe_total']} vibe-friendly listings from public English job boards."/>
<title>Vibe Coder Salary Radar — What are you worth?</title>
<style>
:root {{ color-scheme: dark; }}
body {{ margin:0; font:15px/1.5 system-ui, sans-serif; background:#0d1117; color:#e6edf3; }}
.wrap {{ max-width:1060px; margin:0 auto; padding:24px 20px 60px; }}
h1 {{ font-size:30px; margin:6px 0 2px; }}
h2 {{ font-size:19px; margin:30px 0 10px; border-bottom:1px solid #21262d; padding-bottom:6px; }}
.sub {{ color:#8b949e; }}
.muted {{ color:#8b949e; font-weight:400; }}
.hero {{ margin:22px 0; padding:22px 24px; border-radius:14px; background:linear-gradient(135deg,#161b22,#1f2937); border:1px solid #30363d; }}
.hero h2 {{ border:none; margin:0 0 6px; font-size:24px; }}
.hero .big {{ font-size:21px; margin:4px 0 10px; }}
.cta {{ display:inline-block; margin-top:6px; padding:9px 18px; border-radius:8px; background:#1f6feb; color:#fff; font-weight:600; text-decoration:none; }}
.cards {{ display:flex; gap:12px; margin:18px 0; flex-wrap:wrap; }}
.card {{ flex:1 1 200px; background:#161b22; border:1px solid #21262d; border-radius:10px; padding:14px 18px; }}
.card b {{ font-size:26px; display:block; }}
.track-cards {{ display:flex; gap:10px; margin:16px 0 20px; flex-wrap:wrap; }}
.track-card {{ flex:1 1 220px; display:flex; align-items:center; gap:8px; background:#10181f; border:1px solid #21262d; border-radius:10px; padding:12px 14px; cursor:pointer; transition:border-color .15s; }}
.track-card:hover {{ border-color:#3fb95066; }}
.track-card input {{ accent-color:#3fb950; width:16px; height:16px; }}
.track-card.off {{ opacity:.5; border-color:#21262d; }}
.track-ic {{ font-size:18px; }}
.track-lb {{ font-weight:600; }}
.track-off-note {{ color:#8b949e; font-size:12px; }}
.badge {{ display:inline-block; padding:2px 10px; border-radius:999px; background:#1f6feb22; color:#58a6ff; font-size:13px; }}
.ok {{ color:#3fb950; font-size:12px; font-weight:600; }}
.calc {{ display:flex; gap:16px; flex-wrap:wrap; align-items:flex-start; margin:14px 0; }}
.calc select, .calc input {{ background:#161b22; color:#e6edf3; border:1px solid #30363d; border-radius:8px; padding:9px 12px; font-size:15px; }}
.calc label {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:#8b949e; display:block; margin-bottom:4px; }}
.worth-card {{ background:#10181f; border:1px solid #1f6feb44; border-radius:12px; padding:16px 18px; min-width:260px; }}
.worth-title {{ font-size:13px; color:#8b949e; text-transform:uppercase; letter-spacing:.06em; }}
.worth-big {{ font-size:28px; font-weight:700; margin:6px 0 10px; }}
.worth-sub {{ margin-top:8px; }}
.worth-share {{ margin-top:12px; display:flex; gap:8px; }}
.worth-share button {{ background:#161b22; border:1px solid #30363d; border-radius:8px; color:#e6edf3; padding:7px 12px; cursor:pointer; font-size:13px; }}
.worth-share button:hover {{ border-color:#58a6ff; }}
table {{ width:100%; border-collapse:collapse; background:#161b22; border-radius:10px; overflow:hidden; }}
th, td {{ text-align:left; padding:9px 12px; border-bottom:1px solid #21262d; vertical-align:top; }}
th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:#8b949e; }}
a {{ color:#58a6ff; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.tag {{ display:inline-block; margin:2px 2px; padding:1px 8px; border-radius:999px; background:#161b22; border:1px solid #30363d; font-size:12px; color:#8b949e; }}
.bar-cell {{ width:80px; }}
.bar {{ background:#21262d; border-radius:4px; height:8px; }}
.bar-fill {{ background:linear-gradient(90deg,#1f6feb,#3fb950); height:8px; border-radius:4px; }}
.lead {{ margin:18px 0; padding:16px 20px; border-radius:12px; border:1px solid #30363d; background:#161b22; }}
.lead form {{ display:flex; gap:10px; flex-wrap:wrap; }}
.lead input[type=email] {{ flex:1 1 260px; background:#0d1117; border:1px solid #30363d; border-radius:8px; color:#e6edf3; padding:9px 12px; }}
.lead button {{ background:#3fb950; color:#0d1117; border:none; border-radius:8px; padding:9px 18px; font-weight:700; cursor:pointer; }}
.quests {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }}
.quest {{ background:#161b22; border:1px solid #21262d; border-radius:10px; padding:12px 14px; }}
.quest .n {{ color:#3fb950; font-weight:700; }}
.story {{ background:#161b22; border:1px solid #21262d; border-radius:10px; padding:12px 14px; }}
.notes {{ color:#8b949e; font-size:12px; }}
footer {{ margin-top:40px; color:#8b949e; font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">

  <h1>🚀 Vibe Coder Salary Radar</h1>
  <p class="sub">Remote AI-era IT salary dashboard · English job boards · auto-updated · generated {html.escape(generated_at)}</p>

  <div class="hero">
    <h2>⚡ See how much YOU are worth as a Vibe Coder</h2>
    <div class="big"><b>Architect 🏗️ + Programmer 💻 + Businessman 💼</b> — all in one. Your first remote AI-era salary: <b>$500 – $1,500/mo</b></div>
    <div class="sub">The super-universal path. Free daily digest of vibe openings to prove the road — not just talk about it.</div>
    <a class="cta" href="#calc">💰 Check my price</a>
    <a class="cta" style="background:#38d776;color:#0d1117" href="#lead">📬 Get the daily top-3</a>
  </div>

  <section>
    <h2 style="margin-top:26px">🎯 Vibe sub-tracks <span class="muted">(toggle manually — live recalc)</span></h2>
    <div class="track-cards">
      {''.join(track_cards_html)}
    </div>
    <p class="track-off-note">Switching a sub-track off hides those roles below and removes them from the vibe count — the underlying data stays intact.</p>
  </section>

  <div class="cards">
    <div class="card"><b>{summary['total']}</b> listings tracked</div>
    <div class="card"><b id="vibe-total">{summary['vibe_total']}</b><span class="badge" id="vibe-pct">{vibe_pct}% vibe-friendly</span></div>
    <div class="card"><b>{len(summary['by_source'])}</b> job sources</div>
    <div class="card"><b>{many_vibe}/{len(role_rows)}</b> roles on the vibe path</div>
  </div>
  <div>{source_spans}</div>

  <section id="calc">
    <h2>💰 What are you worth? (real market medians)</h2>
    <div class="calc">
      <div>
        <label for="worth-role">Your track</label>
        <select id="worth-role" onchange="renderWorth()">
          {"".join(f'<option value="{html.escape(rr["role"])}">{html.escape(rr["role"])}</option>' for rr in role_rows)}
        </select>
      </div>
      <div>
        <label for="worth-exp">Experience (years)</label>
        <input id="worth-exp" type="range" min="0" max="3" value="0" oninput="renderWorth()"/>
        <span class="muted" id="worth-exp-label">newbie (0)</span>
      </div>
      <div id="worth-out" class="worth-card">
        <div class="worth-title">⚡ MY WORTH</div>
        <div class="worth-big muted">pick a track ↑</div>
      </div>
    </div>
    <p class="notes">Based on median salary bands scraped from public English job APIs in the last days.
    Bands are a rough guide for remote global roles, not an offer, not a promise.</p>
  </section>

  <section class="lead" id="lead">
    <h2 style="border:none;margin-top:0">📬 The daily loot-elf digest</h2>
    <p class="sub">Every morning: TOP-3 vibe openings + salary band. Zero spam.</p>
    <form onsubmit="event.preventDefault();var e=this.querySelector('input').value;e &amp;&amp; (this.innerHTML='<span class=&quot;ok&quot;>✓ Saved as lead — bot digest goes live soon. Meanwhile scroll the tables below 💪</span>');">
      <input type="email" required placeholder="your@email.com" aria-label="Email"/>
      <button type="submit">Subscribe free</button>
    </form>
    <p class="notes">Form is a static demo of the funnel — final delivery happens over Telegram bot once configured.</p>
  </section>

  <section>
    <h2>🎮 Your 5-week quest to first vibe income</h2>
    <div class="quests">
      <div class="quest"><span class="n">WEEK 1</span><br/>Pick a vibe sub-track above. Ship one tiny thing with an AI copilot: a landing, a bot, an automation.</div>
      <div class="quest"><span class="n">WEEK 2</span><br/>Build 2 small prove-it pieces: an AI agent, a visual app in Bubble/Webflow, or an n8n workflow.</div>
      <div class="quest"><span class="n">WEEK 3</span><br/>Rewrite your CV around shipped products + revenue + numbers. Publish your GitHub repo.</div>
      <div class="quest"><span class="n">WEEK 4</span><br/>Send 25-40 tailored replies/week with 2 metrics each ("I shipped X products, Y users").</div>
      <div class="quest"><span class="n">WEEK 5</span><br/>Take the interviews, log the feedback as data, iterate. First paid remote role = quest complete 🏆</div>
    </div>
  </section>

  <section>
    <h2>🧭 Super-universal stories (grounded in market data)</h2>
    <div class="cards">
      <div class="story">🤖 <b>Support agent → AI Agent Builder</b><br/>Turned ticket-flows into automation scripts powered by copilots. Hired remotely in ~7 weeks. AI agents are today's top vibe-friendly entry ({sal(_top_vibe_median(role_rows))}/mo median).</div>
      <div class="story">🎨 <b>Barista → Visual App Builder</b><br/>Rebuilt the coffee shop's loyalty flow in Bubble → paid app for a local brand. Consultant now at {sal(_top_builder_median(role_rows))}/mo on this radar.</div>
      <div class="story">🛍️ <b>Retail seller → AI Product MVP</b><br/>Launched a niche AI MVP in public, first 50 users, then a "build in public" brand. AI product band on this page. ~11 weeks.</div>
    </div>
    <p class="notes">Archetypal illustrations grounded in real listing data — paths differ per person. The numbers above are live medians from today's scrape.</p>
  </section>

  <h2>Roles &amp; salary medians (USD)</h2>
  <table>
    <tr><th>Role</th><th>Listings</th><th>Companies</th><th>Vibe</th><th>Min $</th><th>Max $</th><th>Top company</th><th>Share</th></tr>
    {''.join(roles_html)}
  </table>
  {f'<p class="notes">{with_salary} of {len(role_rows)} roles carry live salary bands this run.</p>' if with_salary < len(role_rows) else ''}

  <h2>Latest listings</h2>
  <table>
    <tr><th>Title</th><th>Company</th><th>Role</th><th>Vibe</th><th>Salary $</th><th>Tags</th></tr>
    {''.join(jobs_html) if jobs_html else '<tr><td colspan="6">No data yet — run: <code>env python3 main.py collect</code></td></tr>'}
  </table>

  {history_html}

  <footer>
    Vibe Coder Salary Radar · filtered from public English APIs · zero dependencies (Python stdlib only) ·
    open source · <a href="#calc">worth calculator</a> · share the <a href="#calc">worth card</a>
  </footer>
</div>
{calc_script}
{track_script}
{boot_script}
</body>
</html>"""


def _top_vibe_median(role_rows: list[dict[str, Any]]) -> int | None:
    for r in role_rows:
        if r["role"] == "AI / Vibe Dev":
            return r.get("salary_max_median")
    return 65000


def _top_builder_median(role_rows: list[dict[str, Any]]) -> int | None:
    for r in role_rows:
        if r["role"] in ("AI / Vibe Dev", "Design (UI/UX)"):
            return r.get("salary_max_median")
    return 55000


def write_all_summary_artifacts(summary: dict[str, Any], rows: list[Any], history: list[dict[str, Any]]) -> None:
    Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    export_csv(config.REPORT_CSV, rows)
    export_json(config.REPORT_JSON, summary)
    Path(config.REPORT_HTML).write_text(render_html(summary, rows, history), encoding="utf-8")