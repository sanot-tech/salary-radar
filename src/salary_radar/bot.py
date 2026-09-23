"""Loot-Elf: a daily Telegram digest, stdlib-only.

Builds a human "loot drop" message from the freshest no-code-friendly
listings and sends it via the Telegram Bot API using only urllib.
Dry-run mode prints the message so it is testable without a token.

Environment:
    TG_BOT_TOKEN  — bot token from @BotFather
    TG_CHAT_ID    — target chat (user id or group id)

Usage:
    env python3 main.py bot          # live send (needs env vars)
    env python3 main.py bot --dry    # print digest only
"""

from __future__ import annotations

import os
import urllib.parse
import urllib.request
from typing import Any

from .analyze import resolve_tracks, track_enabled

API = "https://api.telegram.org/bot{token}/sendMessage"

DIGEST_HEADER = "🎮 Loot-Elf digest — today's TOP no-code drops"


def build_digest_text(summary: dict[str, Any], rows: list[Any]) -> str:
    """Turn stored listings into a short Telegram-ready digest.

    Prefers no-code listings that carry an actual salary band (sorted
    descending), otherwise falls back to any fresh no-code posting.
    """
    candidates = []
    for r in rows:
        if not r["no_code"]:
            continue
        score = r["salary_max"] or r["salary_min"] or 0
        candidates.append((score, r))
    candidates.sort(key=lambda t: -t[0])

    lines = [DIGEST_HEADER, ""]
    for i, (_, r) in enumerate(candidates[:3], start=1):
        band = ""
        if r["salary_min"] or r["salary_max"]:
            lo = f"${r['salary_min']:,}" if r["salary_min"] else "—"
            hi = f"${r['salary_max']:,}" if r["salary_max"] else "—"
            band = f" · 💰 {lo}–{hi}"
        lines.append(
            f"{i}) {r['title']}\n   {r['company']} · {r['role']}{band}\n   {r['url'] or '—'}"
        )
        lines.append("")

    total = summary.get("total", 0)
    no_code = summary.get("no_code_total", 0)
    lines.append(f"📡 Radar: {total} tracked · {no_code} no-code friendly · daily auto-update")
    return "\n".join(lines)


def send_message(text: str, token: str, chat_id: str) -> bool:
    """POST a message to Telegram and return success status."""
    url = API.format(token=token)
    params = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "false",
    })
    req = urllib.request.Request(f"{url}?{params}", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return '"ok":true' in body
    except Exception:
        return False


def run_digest(*, dry: bool = False) -> int:
    """Fetch latest summary+listings, build digest, send (or print)."""
    from . import db, report
    from .analyze import summarize

    tracks = resolve_tracks(os.environ.get("RADAR_TRACKS"))
    store = db.RadarDB()
    try:
        rows = store.all_jobs()
        summary = summarize(rows, tracks=tracks)
        visible = [r for r in rows if track_enabled(r["role"], tracks)]
        text = build_digest_text(summary, visible)
    finally:
        store.close()

    print(text)
    if dry:
        return 0

    token = os.environ.get("TG_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TG_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("[bot] TG_BOT_TOKEN / TG_CHAT_ID not set (dry-run only).")
        return 2

    ok = send_message(text, token, chat_id)
    print(f"[bot] sent={ok}")
    return 0 if ok else 3