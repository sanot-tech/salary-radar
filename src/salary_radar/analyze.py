"""Role classification and statistics for the collected listings."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from statistics import median
from typing import Any

from . import config


# --- Track helpers (manual toggles) ---------------------------------------

def resolve_tracks(raw: str | list[str] | None) -> dict[str, bool]:
    """Build a track dict from a CLI/env string or list.

    Accepts aliases ("vibe", "ai", "key_support") and short names.
    Examples:
        resolve_tracks("vibe,qa")   -> only vibe_ai + qa enabled
        resolve_tracks(None)        -> config.TRACKS defaults
    """
    if raw is None:
        return dict(config.TRACKS)
    if isinstance(raw, str):
        items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    else:
        items = [str(x).strip().lower() for x in raw]
    if not items:
        return dict(config.TRACKS)
    # "vibe,qa" -> only those two enabled; "vibe,!support" -> everything on.
    has_negation = any(i.startswith("!") or i.endswith("-off") for i in items)
    result = {key: has_negation for key in config.TRACKS}
    for item in items:
        off = item.startswith("!") or item.endswith("-off")
        name = item.lstrip("!").removesuffix("-off")
        track = config.TRACK_ALIASES.get(name, name if name in config.TRACKS else None)
        if track is None:
            continue
        result[track] = not off
    return result


def row_track(role: str | None) -> str | None:
    """Map a role to its track id (None = not part of any toggled track)."""
    return config.ROLE_TO_TRACK.get(role or "")


def track_enabled(role: str | None, tracks: dict[str, bool] | None) -> bool:
    """True unless the row's track exists AND is explicitly switched off."""
    if tracks is None:
        return True
    track = row_track(role)
    if track is None:
        return True
    return bool(tracks.get(track, True))


def evaluate_no_code(
    title: str,
    category: str,
    tags: list[str] | None,
    role: str | None = None,
    tracks: dict[str, bool] | None = None,
) -> bool:
    """no-code verdict with the vibe guard + manual track switches applied."""
    if not track_enabled(role, tracks):
        return False
    return is_no_code_friendly(title, category, tags)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _has_code_word(title: str) -> bool:
    t = " " + title.lower() + " "
    return any(w in t for w in config.CODE_WORDS)


def classify_role(title: str) -> str:
    """Best-effort bucket of a job title into one of the known categories.

    "AI / Vibe Dev" is resolved FIRST: strong vibe phrases always win
    ("Prompt Engineer"), while advisory signals (llm/ai agent/...) only win
    when the title carries no hard coding word — so "LLM Engineer" or
    "AI Agent Engineer" fall through to Engineering instead of becoming
    no-code fakes. Engineering is matched last on purpose.
    """
    t = " " + title.lower() + " "

    for kw in config.VIBE_KEYWORDS_STRONG:
        if kw.lstrip("-") in t:
            return "AI / Vibe Dev"
    if not _has_code_word(t):
        for kw in config.VIBE_KEYWORDS_GENERIC:
            if kw.lstrip("-") in t:
                return "AI / Vibe Dev"

    for role in config.ROLE_ORDER:
        if role in ("Unknown", "Engineering", "AI / Vibe Dev"):
            continue
        for kw in config.ROLE_KEYWORDS.get(role, []):
            if kw.lstrip("-") in t:
                return role
    for kw in config.ROLE_KEYWORDS.get("Engineering", []):
        if kw.lstrip("-") in t:
            return "Engineering"
    return "Unknown"


def is_no_code_friendly(title: str, category: str, tags: list[str] | None) -> bool:
    """Heuristic: does this listing look doable without live coding skills?

    Live APIs sometimes return nested categories/tags, so every value is
    flattened into strings defensively. Strong vibe phrases always count as
    no-code; advisory vibe signals count only when no hard coding word is in
    the title.
    """

    def as_str(value) -> str:
        if isinstance(value, list):
            return " ".join(str(v) for v in value if v is not None)
        return str(value or "")

    haystack = " ".join([
        title,
        as_str(category),
        " ".join(as_str(x) for x in (tags or []) if x is not None),
    ]).lower()
    t = " " + haystack + " "

    for kw in config.VIBE_KEYWORDS_STRONG:
        if kw in t:
            return True
    if not _has_code_word(haystack):
        for kw in config.VIBE_KEYWORDS_GENERIC:
            if kw in t:
                return True

    return any(kw in haystack for kw in config.NO_CODE_KEYWORDS)


def _median(values: list[int]) -> int | None:
    if not values:
        return None
    return int(median(values))


@dataclass
class RoleSummary:
    role: str
    count: int
    companies: int
    no_code_count: int
    salary_min_med: int | None
    salary_max_med: int | None
    top_company: tuple[str, int] | None
    top_tags: list[tuple[str, int]] | None


def summarize(db_rows: list[Any], tracks: dict[str, bool] | None = None) -> dict[str, Any]:
    """Build a compact, JSON-friendly summary from raw DB rows.

    ``tracks`` applies the manual on/off switches: a no-code row whose track
    is switched off is not counted as no-code (it stays in the listing table).
    """

    def nocode(row: Any) -> bool:
        return bool(row["no_code"]) and track_enabled(row["role"], tracks)

    rows_by_role: dict[str, list[Any]] = {}
    for row in db_rows:
        rows_by_role.setdefault(row["role"], []).append(row)

    summaries: list[dict[str, Any]] = []
    for role in config.ROLE_ORDER:
        rows = rows_by_role.pop(role, [])
        if not rows:
            continue
        companies = {r["company"] for r in rows}
        no_code_count = sum(1 for r in rows if nocode(r))
        mins = [r["salary_min"] for r in rows if r["salary_min"]]
        maxs = [r["salary_max"] for r in rows if r["salary_max"]]
        top_company = Counter(r["company"] for r in rows).most_common(1)
        tag_counter: Counter[str] = Counter()
        for r in rows:
            for tag in (r["tags"] or "").split(","):
                if tag.strip():
                    tag_counter[tag.strip()] += 1
        summaries.append({
            "role": role,
            "count": len(rows),
            "companies": len(companies),
            "no_code_count": no_code_count,
            "no_code_share": round(no_code_count / len(rows), 2),
            "salary_min_median": _median(mins),
            "salary_max_median": _median(maxs),
            "top_company": top_company[0][0] if top_company else None,
            "top_tags": [t for t, _ in tag_counter.most_common(8)],
        })

    # Any role outside the known ordering goes to 'Other'.
    for role, rows in rows_by_role.items():
        if not rows:
            continue
        summaries.append({
            "role": role,
            "count": len(rows),
            "companies": len({r["company"] for r in rows}),
            "no_code_count": sum(1 for r in rows if nocode(r)),
            "no_code_share": round(sum(1 for r in rows if nocode(r)) / len(rows), 2),
            "salary_min_median": _median([r["salary_min"] for r in rows if r["salary_min"]]),
            "salary_max_median": _median([r["salary_max"] for r in rows if r["salary_max"]]),
            "top_company": Counter(r["company"] for r in rows).most_common(1)[0][0],
            "top_tags": [],
        })

    by_source: dict[str, int] = {}
    for row in db_rows:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1

    # Per-track aggregates for the dashboard's priority-track cards.
    track_counts: dict[str, dict[str, int]] = {}
    for track in config.TRACKS:
        trows = [r for r in db_rows if row_track(r["role"]) == track]
        track_counts[track] = {
            "count": len(trows),
            "no_code": sum(1 for r in trows if nocode(r)),
            "enabled": bool(tracks.get(track, True)) if tracks else bool(config.TRACKS[track]),
        }

    return {
        "total": len(db_rows),
        "no_code_total": sum(1 for r in db_rows if nocode(r)),
        "no_code_share": round(
            sum(1 for r in db_rows if nocode(r)) / max(len(db_rows), 1), 2
        ),
        "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
        "roles": summaries,
        "track_counts": track_counts,
    }