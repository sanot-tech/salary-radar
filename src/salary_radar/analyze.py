"""Role classification and statistics for the collected listings.

Vibe Coder = super-universal (architect + programmer + businessman in one).
Every vibe-friendly listing gets a sub-track so the radar can show which
vibe direction the market is paying for.
"""

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

    Accepts aliases ("agents", "prompt", "build") and short names.
    "vibe" means "all vibe sub-tracks".
    Examples:
        resolve_tracks("agents,prompt")   -> only those two enabled
        resolve_tracks(None)              -> config.TRACKS defaults
    """
    if raw is None:
        return dict(config.TRACKS)
    if isinstance(raw, str):
        items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    else:
        items = [str(x).strip().lower() for x in raw]
    if not items:
        return dict(config.TRACKS)
    has_negation = any(i.startswith("!") or i.endswith("-off") for i in items)
    result = {key: has_negation for key in config.TRACKS}
    for item in items:
        off = item.startswith("!") or item.endswith("-off")
        name = item.lstrip("!").removesuffix("-off")
        if name == "vibe":
            # "vibe" alone (or "!vibe") toggles every sub-track.
            for key in config.TRACKS:
                result[key] = not off
            continue
        track = config.TRACK_ALIASES.get(name)
        if track is None:
            continue
        result[track] = not off
    return result


def vibe_subcategory(title: str, category: str = "", tags: list[str] | None = None) -> str | None:
    """Thread a vibe role into one of the sub-tracks by keyword weight."""
    def as_str(value) -> str:
        if isinstance(value, list):
            return " ".join(str(v) for v in value if v is not None)
        return str(value or "")

    text = " ".join([title, as_str(category), " ".join(as_str(x) for x in (tags or []))]).lower()
    # Specific tools first (already ordered in config), then generic terms.
    for track, kws in config.VIBE_SUBCATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return track
    # Any remaining vibe role that mentions code-shaped words but is vibe-first.
    if any(kw in text for kw in config.VIBE_KEYWORDS_GENERIC):
        return "ai_product"
    return None


def row_track(role: str | None, title: str = "", category: str = "", tags: list[str] | None = None) -> str | None:
    """Map a row (role + title) to a vibe sub-track id; None = not vibe."""
    if (role or "") not in ("AI / Vibe Dev",):
        return None
    return vibe_subcategory(title, category, tags)


def track_enabled(role: str | None, tracks: dict[str, bool] | None,
                  title: str = "", category: str = "", tags: list[str] | None = None) -> bool:
    """True unless the row's track exists AND is explicitly switched off."""
    if tracks is None:
        return True
    track = row_track(role, title, category, tags)
    if track is None:
        return True
    return bool(tracks.get(track, True))


def evaluate_vibe(
    title: str,
    category: str,
    tags: list[str] | None,
    role: str | None = None,
    tracks: dict[str, bool] | None = None,
) -> bool:
    """vibe verdict with the vibe guard + manual track switches applied."""
    if not track_enabled(role, tracks, title, category, tags):
        return False
    return is_vibe_friendly(title, category, tags)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _has_code_word(title: str) -> bool:
    t = " " + title.lower() + " "
    for w in config.CODE_WORDS:
        if f" {w} " in t or t.startswith(f"{w} ") or t.rstrip().endswith(f" {w}"):
            return True
        if w in t:
            return True
    return False


def classify_role(title: str) -> str:
    """Best-effort bucket of a job title into one of the known categories.

    "AI / Vibe Dev" is resolved FIRST: strong vibe phrases always win
    ("Prompt Engineer", "Vibe Coder"), while advisory signals only win when
    the title carries no hard coding word — so "LLM Engineer" falls through
    to Engineering (it's an engineer, not a vibe builder).
    """
    t = " " + title.lower() + " "

    for kw in config.VIBE_KEYWORDS_STRONG:
        if kw in t:
            return "AI / Vibe Dev"
    if not _has_code_word(title):
        for kw in config.VIBE_KEYWORDS_GENERIC:
            if kw in t:
                return "AI / Vibe Dev"

    for role in config.ROLE_ORDER:
        if role in ("Unknown", "Engineering", "AI / Vibe Dev"):
            continue
        for kw in config.ROLE_KEYWORDS.get(role, []):
            if kw in t:
                return role
    for kw in config.ROLE_KEYWORDS.get("Engineering", []):
        if kw in t:
            return "Engineering"
    return "Unknown"


def is_vibe_friendly(title: str, category: str, tags: list[str] | None) -> bool:
    """Heuristic: does this listing look achievable on the vibe track?

    A vibe coder builds products with AI copilots, automations and visual
    builders — they may never write 10 kLoC by hand but they ship like an
    architect + programmer + businessman combined.
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

    for kw in config.VIBE_KEYWORDS_STRONG:
        if kw in haystack:
            return True
    if not _has_code_word(haystack):
        for kw in config.VIBE_KEYWORDS_GENERIC:
            if kw in haystack:
                return True

    return any(kw in haystack for kw in config.VIBE_KEYWORDS)


def _median(values: list[int]) -> int | None:
    if not values:
        return None
    return int(median(values))


@dataclass
class RoleSummary:
    role: str
    count: int
    companies: int
    vibe_count: int
    salary_min_med: int | None
    salary_max_med: int | None
    top_company: tuple[str, int] | None
    top_tags: list[tuple[str, int]] | None


def _nocode(row: Any) -> bool:
    return bool(row["vibe"])


def summarize(db_rows: list[Any], tracks: dict[str, bool] | None = None) -> dict[str, Any]:
    """Build a compact, JSON-friendly summary from raw DB rows.

    ``tracks`` applies the manual on/off switches: a vibe row whose track
    is switched off is not counted as vibe (it stays in the listing table).
    """

    def vibe(row: Any) -> bool:
        return _nocode(row) and track_enabled(
            row["role"], tracks,
            title=row["title"], category=row["category"],
            tags=(row["tags"] or "").split(","),
        )

    rows_by_role: dict[str, list[Any]] = {}
    for row in db_rows:
        rows_by_role.setdefault(row["role"], []).append(row)

    summaries: list[dict[str, Any]] = []
    for role in config.ROLE_ORDER:
        rows = rows_by_role.pop(role, [])
        if not rows:
            continue
        companies = {r["company"] for r in rows}
        vibe_count = sum(1 for r in rows if vibe(r))
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
            "vibe_count": vibe_count,
            "vibe_share": round(vibe_count / len(rows), 2),
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
            "vibe_count": sum(1 for r in rows if vibe(r)),
            "vibe_share": round(sum(1 for r in rows if vibe(r)) / len(rows), 2),
            "salary_min_median": _median([r["salary_min"] for r in rows if r["salary_min"]]),
            "salary_max_median": _median([r["salary_max"] for r in rows if r["salary_max"]]),
            "top_company": Counter(r["company"] for r in rows).most_common(1)[0][0],
            "top_tags": [],
        })

    by_source: dict[str, int] = {}
    for row in db_rows:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1

    # Per-track aggregates for the dashboard's vibe sub-track cards.
    track_counts: dict[str, dict[str, int]] = {}
    for track in config.TRACKS:
        trows = [r for r in db_rows if row_track(
            r["role"], r["title"], r["category"], (r["tags"] or "").split(",")
        ) == track]
        track_counts[track] = {
            "count": len(trows),
            "vibe": sum(1 for r in trows if vibe(r)),
            "enabled": bool(tracks.get(track, True)) if tracks else bool(config.TRACKS[track]),
        }

    return {
        "total": len(db_rows),
        "vibe_total": sum(1 for r in db_rows if vibe(r)),
        "vibe_share": round(
            sum(1 for r in db_rows if vibe(r)) / max(len(db_rows), 1), 2
        ),
        "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
        "roles": summaries,
        "track_counts": track_counts,
    }