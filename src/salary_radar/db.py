"""SQLite storage for deduplicated, upserted job listings."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from . import config
from .sources import JobRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    uid          TEXT PRIMARY KEY,
    source       TEXT NOT NULL,
    external_id  TEXT NOT NULL,
    title        TEXT NOT NULL,
    company      TEXT NOT NULL,
    url          TEXT,
    location     TEXT,
    category     TEXT,
    tags         TEXT,
    salary_min   INTEGER,
    salary_max   INTEGER,
    currency     TEXT,
    description  TEXT,
    published    TEXT,
    role         TEXT,
    vibe         INTEGER DEFAULT 0,
    first_seen   TEXT,
    last_seen    TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_role  ON jobs (role);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs (source);
CREATE INDEX IF NOT EXISTS idx_jobs_vibe  ON jobs (vibe);
"""


class RadarDB:
    def __init__(self, path: str | None = None) -> None:
        self.path = str(path or config.DB_PATH)
        self.path = self.path.replace("sqlite:///", "")
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        # Migration: the old schema used a 'no_code' column; rename in place
        # so any pre-existing db works without a rebuild.
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(jobs)").fetchall()}
        if "vibe" not in cols and "no_code" in cols:
            self.conn.execute("ALTER TABLE jobs RENAME COLUMN no_code TO vibe")
        elif "vibe" not in cols:
            self.conn.execute("ALTER TABLE jobs ADD COLUMN vibe INTEGER DEFAULT 0")

    def _insert_args(self, job: JobRecord, role: str, vibe: bool, seen: str) -> tuple:
        return (
            job.uid(),
            job.source,
            job.external_id,
            job.title,
            job.company,
            job.url,
            job.location,
            job.category,
            ",".join(job.tags),
            job.salary_min,
            job.salary_max,
            job.currency,
            job.description,
            job.published,
            role,
            1 if vibe else 0,
            seen,
            seen,
        )

    def upsert(self, job: JobRecord, role: str, vibe: bool) -> bool:
        """Insert a new listing or refresh last_seen for a known one.

        Returns True when the record was new (helpful for metrics).
        """
        seen = datetime.now(timezone.utc).isoformat(timespec="seconds")
        args = self._insert_args(job, role, vibe, seen)
        cur = self.conn.execute(
            """
            INSERT INTO jobs (uid, source, external_id, title, company, url, location,
                              category, tags, salary_min, salary_max, currency,
                              description, published, role, vibe, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                title=excluded.title, company=excluded.company, url=excluded.url,
                salary_min=excluded.salary_min, salary_max=excluded.salary_max,
                tags=excluded.tags, description=excluded.description,
                role=excluded.role, vibe=excluded.vibe, last_seen=excluded.last_seen
            """,
            args,
        )
        self.conn.commit()
        return cur.rowcount == 1

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()
        return int(row["c"]) if row else 0

    def count_new_today(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM jobs WHERE DATE(first_seen) = DATE('now')"
        ).fetchone()
        return int(row["c"]) if row else 0

    def all_jobs(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM jobs ORDER BY last_seen DESC").fetchall()

    def close(self) -> None:
        self.conn.close()