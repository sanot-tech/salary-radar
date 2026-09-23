# 🚀 Vibe Coder Salary Radar

> Track remote AI-era IT salaries from English job boards — and spot the
> **vibe-friendly** roles worth targeting.
>
> **Vibe Coder = super-universal**: 🏗️ architect + 💻 programmer + 💼 businessman,
> all in one. No-code is just the on-ramp; vibe is the destination.

![pipeline](https://github.com/sanot-tech/salary-radar/actions/workflows/daily.yml/badge.svg)

A tiny, zero-dependency Python pipeline that runs **daily on GitHub Actions**:

1. **Collects** listings from 8 public English APIs (RemoteOK, Remotive, Jobicy, Arc.dev, Himalayas, AI Dev Board, NoCodeJobs, Working Nomads)
2. **Normalizes** every job into one canonical schema → SQLite
3. **Classifies** roles and flags *vibe-friendly* postings (AI agents, prompt/AI interfaces, visual/low-code builders, generative creative, AI product)
4. **Analyzes** salary medians per role, per vibe sub-track, and company popularity
5. **Renders** a dark-theme HTML dashboard + CSV/JSON exports
6. **Commits** the fresh report back to the repo automatically

The result is a living dataset: which remote roles are hiring this week, what they
pay, and which of them fit the vibe-coder path (build fast with AI copilots instead
of grinding 10 kLoC by hand).

## Vibe sub-tracks

| Track | What a vibe coder does there |
|---|---|
| 🤖 **AI Agents / Automation** | n8n, MCP, agentic workflows, autonomous pipelines |
| 🗣️ **Prompt & AI Interfaces** | LLM prompt design, RAG, natural-language products |
| 🧱 **Visual / Low-Code Builders** | Bubble, Webflow, Airtable — ship UIs without C++ |
| 🎨 **Generative Creative** | Midjourney, generative design, AI video/image |
| 🚀 **AI Product (Super-Universal)** | architect + programmer + businessman, build in public |

Toggle any sub-track live on the dashboard — the counts recalc instantly.

## Why it exists

The 2026 AI-era job market split is real: classic junior engineering is crowded
(20+ resumes per vacancy), while **vibe builders** who can ship products with AI
copilots are in demand. A vibe coder is never "just a no-coder" — they are the
super-universal who reads code, ships code *with AI*, and sells the result.
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

# Toggle vibe sub-tracks (agents,prompt,build,creative,product / !name to disable one)
env python3 main.py report --tracks agents,prompt

# Telegram vibe digest — prints, or sends when TG_BOT_TOKEN/TG_CHAT_ID are set
env python3 main.py bot --dry
```

No `pip install` needed — **standard library only** (Python ≥ 3.10).

## Outputs (`outputs/`)

| File | Description |
|---|---|
| `index.html` | Dark-theme dashboard: role medians, vibe sub-tracks, latest listings, 14-day trend |
| `jobs.csv` | Full normalized dataset |
| `report.json` | Machine-readable summary (feeds the JSON API) |
| `history.json` | Daily totals time series |

## Source providers (all English)

- **RemoteOK** — https://remoteok.com/api
- **Remotive** — https://remotive.com/api/remote-jobs
- **Jobicy** — https://jobicy.com/api/v2/remote-jobs
- **Arc.dev** — https://www.arc.dev/api/public/jobs
- **Himalayas** — https://himalayas.app/jobs-api (remote-first board)
- **AI Dev Board** — https://aidevboard.com/api/v1/jobs (AI-native jobs from ATS)
- **NoCodeJobs** — https://nocodejobs.org/jobs.json (Bubble/Webflow/automation)
- **Working Nomads** — https://www.workingnomads.com/api/exposed_jobs/

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
`activity.yml` keeps the contribution graph full and green.

## Layout

```
salary-radar/
├── main.py                  # entry point
├── src/salary_radar/
│   ├── config.py            # paths, sources, role + vibe sub-track keywords
│   ├── sources.py           # HTTP clients + normalizers + fallback
│   ├── db.py                # SQLite upsert store
│   ├── analyze.py           # role classification + vibe stats
│   ├── report.py            # HTML / CSV / JSON exports (+ worth calculator, quests, stories)
│   ├── bot.py               # Telegram vibe digest (stdlib only)
│   └── cli.py               # collect | report | run | bot
├── data/sample/             # offline fixtures per source
├── tests/                   # offline unit + pipeline tests
├── outputs/                 # generated (gitignored, committed by CI)
└── .github/workflows/       # daily automation
```

## License

MIT