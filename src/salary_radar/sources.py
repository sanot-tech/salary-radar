"""Job source clients: fetch + normalize listings from English job APIs.

Every provider has its own JSON shape, so each one gets a dedicated normalizer
that converts a raw record into a canonical :class:`JobRecord`.

If a network call fails (rate limit, bot wall, sandbox without internet) the
module seamlessly falls back to the bundled offline sample so the whole
pipeline still runs and stays testable.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from . import config

RawRecord = dict[str, Any]


@dataclass
class JobRecord:
    """Canonical, source-agnostic job listing."""

    source: str
    external_id: str
    title: str
    company: str
    url: str
    location: str = "Remote"
    category: str = ""
    tags: list[str] = field(default_factory=list)
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str = "USD"
    description: str = ""
    published: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def uid(self) -> str:
        return f"{self.source}:{self.external_id}"


def _flatten_tags(tags) -> list[str]:
    """Flatten potentially nested/mixed tag payloads from live APIs into strings."""
    out: list[str] = []
    for tag in tags or []:
        if isinstance(tag, list):
            out.extend(str(x) for x in tag)
        elif tag is not None:
            out.append(str(tag))
    return out


def _parse_salary(raw) -> tuple[int | None, int | None]:
    """Turn a messy salary field into (min, max) USD integers when possible."""
    if isinstance(raw, (int, float)):
        return int(raw), int(raw)
    if raw is None:
        return None, None
    text = str(raw)
    import re

    numbers = re.findall(r"\d[\d,\.]*", text)
    if not numbers:
        return None, None
    def clean(n: str) -> int:
        try:
            return int(float(n.replace(",", "")))
        except ValueError:
            return 0
    vals = [clean(n) for n in numbers[:2]]
    if not vals:
        return None, None
    vals.sort()
    if len(vals) == 1:
        return vals[0], vals[0]
    return vals[0], vals[1]


def _normalize_remoteok(rec: RawRecord) -> JobRecord | None:
    uid = rec.get("id")
    if not uid:
        return None
    lo, hi = _parse_salary(rec.get("salary_min")), _parse_salary(rec.get("salary_max"))
    return JobRecord(
        source="remoteok",
        external_id=str(uid),
        title=rec.get("position") or rec.get("title") or "Unknown",
        company=rec.get("company") or "Unknown",
        url=rec.get("url") or "",
        location=rec.get("location") or "Remote",
        category=rec.get("category") or "",
        tags=rec.get("tags") or [],
        salary_min=lo[0] if lo[0] is not None else None,
        salary_max=hi[1] if hi[1] is not None else None,
        description=rec.get("description") or "",
        published=rec.get("date") or "",
    )


def _normalize_remotive(rec: RawRecord) -> JobRecord | None:
    uid = rec.get("id")
    if not uid:
        return None
    return JobRecord(
        source="remotive",
        external_id=str(uid),
        title=rec.get("title") or "Unknown",
        company=rec.get("company_name") or rec.get("company") or "Unknown",
        url=rec.get("url") or rec.get("application_url") or "",
        location=rec.get("candidate_required_location") or "Remote",
        category=rec.get("category") or "",
        tags=rec.get("tags") or [],
        salary_min=None,
        salary_max=None,
        description=rec.get("description") or "",
        published=rec.get("publication_date") or "",
    )


def _normalize_jobicy(rec: RawRecord) -> JobRecord | None:
    uid = rec.get("id")
    if not uid:
        return None
    lo, hi = _parse_salary(rec.get("salaryMin")), _parse_salary(rec.get("salaryMax"))
    return JobRecord(
        source="jobicy",
        external_id=str(uid),
        title=rec.get("jobTitle") or "Unknown",
        company=rec.get("companyName") or "Unknown",
        url=rec.get("url") or "",
        location=rec.get("jobGeo") or "Remote",
        category=rec.get("jobIndustry") or "",
        tags=rec.get("jobType") and [rec["jobType"]] or [],
        salary_min=lo[0],
        salary_max=hi[0],
        description=rec.get("jobExcerpt") or "",
        published=rec.get("pubDate") or "",
    )


def _normalize_arcdev(rec: RawRecord) -> JobRecord | None:
    uid = rec.get("id")
    company = (rec.get("company") or {}).get("name") or "Unknown"
    comp = (rec.get("compensation") or {}).get("currency") or ""
    sal = rec.get("compensation") or {}
    lo = sal.get("min") or sal.get("minValue") if isinstance(sal, dict) else None
    hi = sal.get("max") or sal.get("maxValue") if isinstance(sal, dict) else None
    return JobRecord(
        source="arcdev",
        external_id=str(uid),
        title=rec.get("title") or "Unknown",
        company=company,
        url=rec.get("url") or rec.get("applyUrl") or "",
        location=(rec.get("jobType") or "Remote"),
        category=(rec.get("category") or ""),
        tags=(rec.get("keywords") or [])[:6],
        salary_min=_parse_salary(lo)[0],
        salary_max=_parse_salary(hi)[1],
        description=rec.get("description", "") or "",
        published=rec.get("createdAt") or "",
    )


NORMALIZERS: dict[str, Callable[[RawRecord], JobRecord | None]] = {
    "remoteok": _normalize_remoteok,
    "remotive": _normalize_remotive,
    "jobicy": _normalize_jobicy,
    "arcdev": _normalize_arcdev,
}


def _root_of(payload: Any, source: str) -> list[Any]:
    """Return the list of records according to the source's 'root' shape."""
    root_key = config.SOURCE_CONFIG[source].get("root")
    if source == "remoteok":
        if isinstance(payload, list):
            # First element of remoteok payload is a metadata dict.
            return payload[1:] if payload and isinstance(payload[0], dict) else payload
        return []
    if isinstance(payload, dict) and root_key in payload:
        return payload[root_key] or []
    if isinstance(payload, list):
        return payload
    return []


def _fetch_json(url: str, *, timeout: int = config.TIMEOUT_SECONDS) -> Any:
    """GET a URL and parse JSON. Raises on non-JSON response."""
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:  # pragma: no cover - depends on network
        raise ValueError(f"non-JSON response from {url}: {exc}") from exc


def _load_sample(source: str) -> list[RawRecord]:
    """Offline fallback: read bundled sample data for a source."""
    path = config.SAMPLE_DIR / f"{source}_sample.json"
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return _root_of(payload, source)


def scrape_source(
    source: str,
    *,
    offline: bool = False,
    sample: bool = False,
) -> list[JobRecord]:
    """Fetch a source online, or fall back to the bundled sample."""
    normalizer = NORMALIZERS[source]
    records: list[RawRecord] = []

    if not offline:
        try:
            payload = _fetch_json(config.SOURCE_CONFIG[source]["url"])
            records = _root_of(payload, source)
        except Exception:
            records = []  # network failure -> fall through to sample below

    if sample or not records:
        records = _load_sample(source)

    jobs = []
    for rec in records:
        job = normalizer(rec)
        if job is None:
            continue
        job.tags = _flatten_tags(job.tags)
        if isinstance(job.category, list):
            job.category = ", ".join(_flatten_tags(job.category))
        jobs.append(job)
    return jobs


def scrape_all(*, offline: bool = False, sample: bool = False) -> dict[str, list[JobRecord]]:
    """Scrape every configured source; never raises because of one bad source."""
    result: dict[str, list[JobRecord]] = {}
    for source in config.SOURCE_CONFIG:
        try:
            result[source] = scrape_source(source, offline=offline, sample=sample)
        except Exception:
            # A single broken source must not kill the whole pipeline.
            result[source] = []
    return result


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")