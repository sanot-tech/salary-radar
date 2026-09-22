#!/usr/bin/env python3
"""Salary Radar entry point.

Runs the full pipeline: fetch -> store -> summarize -> dashboard.

    env python3 main.py run            # live source (falls back to samples offline)
    env python3 main.py run --sample   # always use bundled samples (CI-safe)
"""

from src.salary_radar.cli import main

if __name__ == "__main__":
    raise SystemExit(main())