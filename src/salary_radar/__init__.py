"""Salary Radar - a daily pipeline that tracks remote IT salaries from public English job APIs.

It scrapes several public job boards, normalizes the listings into a SQLite store,
detects "no-code friendly" roles (QA, analyst, support, sysadmin, design, sales, marketing),
computes salary statistics by role/category, and renders a small HTML dashboard.

Standard-library only. No external dependencies.
"""

__version__ = "1.0.0"