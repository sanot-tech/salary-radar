# Salary Radar

> Track remote IT salaries from English job boards — and spot the
> **no-code friendly** roles worth targeting (QA, analyst, support,
> sysadmin, design, sales, marketing).

![pipeline](https://github.com/<OWNER>/salary-radar/actions/workflows/daily.yml/badge.svg)

A tiny, zero-dependency Python pipeline that runs **daily on GitHub Actions**:

1. **Collects** listings from public English APIs (RemoteOK, Remotive, Jobicy, Arc.dev)
2. **Normalizes** every job into one canonical schema → SQLite
3. **Classifies** roles and flags *no-code friendly* postings using keywords
4. **Analyzes** salary medians per role and company popularity
5. **Renders** a dark-theme HTML dashboard + CSV/JSON exports
6. **Commits** the fresh report back to the repo automatically

The result is a living dataset: which remote roles are hiring this week, what they
pay, and which of them don't require live coding.

## Why it exists

The 2026 IT job market is divided: **junior engineering is crowded**
(20+ resumes per vacancy), while QA, analysis, support, sysadmin and security
roles remain in demand and are **reachable without a live-coding interview**.
Salary Radar keeps that market on a weekly dashboard so a job search becomes a
data question instead of a guessing game.

## Quick start

```bash
# Live sources (falls back to bundled samples if a board is down)
env python3 main.py run

# Always offline (CI-safe, uses data/sample fixtures)
env python3 main.py run --sample

# Individual steps
env python3 main.py collect --sample
env python3 main.py report
```

No `pip install` needed — **standard library only** (Python ≥ 3.10).

## Outputs (`outputs/`)

| File | Description |
|---|---|
| `index.html` | Dark-theme dashboard: role medians, latest listings, 14-day trend |
| `jobs.csv` | Full normalized dataset |
| `report.json` | Machine-readable summary (feeds the JSON API) |
| `history.json` | Daily totals time series |

## Source providers (all English)

- **RemoteOK** — https://remoteok.com/api
- **Remotive** — https://remotive.com/api/remote-jobs
- **Jobicy** — https://jobicy.com/api/v2/remote-jobs
- **Arc.dev** — https://www.arc.dev/api/public/jobs

Each provider is an isolated parser in `src/salary_radar/sources.py`. Adding a new
board = one dict in `config.SOURCE_CONFIG` + one normalizer + one sample file.
If a source is unreachable, the pipeline **gracefully falls back** to its bundled
sample so the run and the tests never break.

## Tests

```bash
env python3 -m pytest tests/           # or
env python3 -m unittest discover -s tests -v
```

## Automation

`.github/workflows/daily.yml` schedules a run every day (UTC 06:00), collects fresh
data, regenerates the dashboard and commits it with `auto-chore: refresh daily report`.

## Layout

```
salary-radar/
├── main.py                  # entry point
├── src/salary_radar/
│   ├── config.py            # paths, sources, role keywords
│   ├── sources.py           # HTTP clients + normalizers + fallback
│   ├── db.py                # SQLite upsert store
│   ├── analyze.py           # role classification + stats
│   ├── report.py            # HTML / CSV / JSON exports
│   └── cli.py               # collect | report | run
├── data/sample/             # offline fixtures per source
├── tests/                   # offline unit + pipeline tests
├── outputs/                 # generated (gitignored, committed by CI)
└── .github/workflows/       # daily automation
```

## License

MIT