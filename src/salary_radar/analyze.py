"""Role classification and statistics for the collected listings."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from statistics import median
from typing import Any

from . import config


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def classify_role(title: str) -> str:
    """Best-effort bucket of a job title into one of the known categories.

    Engineering is matched last on purpose: roles like "QA Engineer" or
    "Data Engineer" must win over the vague "engineer" keyword.
    """
    t = " " + title.lower() + " "
    for role in config.ROLE_ORDER:
        if role in ("Unknown", "Engineering"):
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
    flattened into strings defensively.
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


def summarize(db_rows: list[Any]) -> dict[str, Any]:
    """Build a compact, JSON-friendly summary from raw DB rows."""
    rows_by_role: dict[str, list[Any]] = {}
    for row in db_rows:
        rows_by_role.setdefault(row["role"], []).append(row)

    summaries: list[dict[str, Any]] = []
    for role in config.ROLE_ORDER:
        rows = rows_by_role.pop(role, [])
        if not rows:
            continue
        companies = {r["company"] for r in rows}
        no_code_count = sum(1 for r in rows if r["no_code"])
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
            "no_code_count": sum(1 for r in rows if r["no_code"]),
            "no_code_share": round(sum(1 for r in rows if r["no_code"]) / len(rows), 2),
            "salary_min_median": _median([r["salary_min"] for r in rows if r["salary_min"]]),
            "salary_max_median": _median([r["salary_max"] for r in rows if r["salary_max"]]),
            "top_company": Counter(r["company"] for r in rows).most_common(1)[0][0],
            "top_tags": [],
        })

    by_source: dict[str, int] = {}
    for row in db_rows:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1

    return {
        "total": len(db_rows),
        "no_code_total": sum(1 for r in db_rows if r["no_code"]),
        "no_code_share": round(
            sum(1 for r in db_rows if r["no_code"]) / max(len(db_rows), 1), 2
        ),
        "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
        "roles": summaries,
    }