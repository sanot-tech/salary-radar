"""Command-line interface.

Usage:
    env python3 main.py collect [--offline] [--sample]
    env python3 main.py report
    env python3 main.py run    (collect + report)
"""

from __future__ import annotations

import argparse
import os
import sys

from . import bot, config, db, report, sources
from .analyze import classify_role, is_no_code_friendly, resolve_tracks, summarize


def _log(msg: str) -> None:
    print(f"[salary-radar] {msg}")


def _tracks_from_args(args: argparse.Namespace) -> dict[str, bool]:
    """--tracks beats env RADAR_TRACKS; both fall back to config defaults."""
    raw = getattr(args, "tracks", None)
    if raw is None:
        raw = os.environ.get("RADAR_TRACKS") or None
    return resolve_tracks(raw)


def cmd_collect(args: argparse.Namespace) -> int:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    store = db.RadarDB()
    fetched = sources.scrape_all(offline=args.offline, sample=args.sample)

    total_new = 0
    per_source: dict[str, int] = {}
    for source_name, jobs in fetched.items():
        per_source[source_name] = len(jobs)
        for job in jobs:
            role = classify_role(job.title)
            no_code = is_no_code_friendly(job.title, job.category, job.tags)
            if store.upsert(job, role, no_code):
                total_new += 1
        _log(f"{source_name}: {len(jobs)} listings")

    stored = store.count()
    store.close()
    _log(f"new today: {total_new} | stored: {stored}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    store = db.RadarDB()
    rows = store.all_jobs()
    tracks = _tracks_from_args(args)
    summary = summarize(rows, tracks=tracks)
    history = report.update_history(summary)
    report.write_all_summary_artifacts(summary, rows, history)
    store.close()
    disabled = [k for k, v in tracks.items() if not v]
    _log(
        f"report written: total={summary['total']} "
        f"no-code={summary['no_code_total']} -> {config.REPORT_HTML}"
        + (f" (tracks off: {', '.join(disabled)})" if disabled else "")
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    code = cmd_collect(args)
    if code != 0:
        return code
    return cmd_report(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="salary-radar",
        description="Track remote IT salaries from English job APIs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Fetch listings into the SQLite store.")
    collect.add_argument("--offline", action="store_true", help="Never touch the network.")
    collect.add_argument("--sample", action="store_true", help="Force bundled sample data.")
    collect.set_defaults(func=cmd_collect)

    report = sub.add_parser("report", help="Render dashboard + exports from the store.")
    report.add_argument(
        "--tracks",
        help="Comma list of tracks to ENABLE (others off): vibe,ai,support,qa,data. "
             "Prefix with ! or -off to disable a single one, e.g. vibe,!support.",
    )
    report.set_defaults(func=cmd_report)

    run = sub.add_parser("run", help="collect then report (default CI step).")
    run.add_argument("--offline", action="store_true")
    run.add_argument("--sample", action="store_true")
    run.add_argument(
        "--tracks",
        help="Comma list of tracks to ENABLE (see report --tracks).",
    )
    run.set_defaults(func=cmd_run)

    dig = sub.add_parser("bot", help="Send/pring the daily no-code Telegram digest.")
    dig.add_argument("--dry", action="store_true", help="Print digest without sending.")
    dig.set_defaults(func=lambda a: bot.run_digest(dry=a.dry))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())