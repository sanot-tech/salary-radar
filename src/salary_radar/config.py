"""Central configuration: paths, sources and role categories."""

from pathlib import Path

# Project root (../.. from src/salary_radar => root)
ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"
DB_PATH = ROOT_DIR / "data" / "radar.db"
OUTPUT_DIR = ROOT_DIR / "outputs"
SAMPLE_DIR = DATA_DIR / "sample"
REPORT_JSON = OUTPUT_DIR / "report.json"
REPORT_HTML = OUTPUT_DIR / "index.html"
REPORT_CSV = OUTPUT_DIR / "jobs.csv"
HISTORY_JSON = OUTPUT_DIR / "history.json"

# User-agent: polite + identifiable.
USER_AGENT = (
    "Mozilla/5.0 (compatible; SalaryRadar/1.0; "
    "research project; contact: radar@localhost)"
)

TIMEOUT_SECONDS = 20

# English public job APIs. Each entry describes how to parse a listing.
SOURCE_CONFIG = {
    "remoteok": {
        "url": "https://remoteok.com/api",
        "auth": "footer",
        "root": "array",
        "skip": 1,  # first element is a metadata block
    },
    "remotive": {
        "url": "https://remotive.com/api/remote-jobs",
        "auth": "none",
        "root": "jobs",
    },
    "jobicy": {
        "url": "https://jobicy.com/api/v2/remote-jobs",
        "auth": "none",
        "root": "jobs",
    },
    "arcdev": {
        "url": "https://www.arc.dev/api/public/jobs",
        "auth": "none",
        "root": "jobs",
    },
}

# Role categories are guesses from the job title.
# They power the "no-code friendly" analysis.
ROLE_KEYWORDS = {
    "AI / Vibe Dev": ["prompt engineer", "vibe", "ai developer", "ai agent",
                      "natural language", "copilot", "llm", "genai",
                      "generative ai", "ai tools", "chatgpt", "cursor"],
    "QA / Testing": ["qa", "quality", "test", "tester", "automation test"],
    "Business Analyst": ["business analyst", "data analyst", "product analyst"],
    "Data": ["data engineer", "data scientist", "data analysis", "data analyst",
             "sql", "bi ", "dashboard", "etl"],
    "Support": ["support", "service desk", "helpdesk", "customer success"],
    "Sysadmin / DevOps": ["sysadmin", "system administrator", "devops", "sre", "infrastructure"],
    "Cybersecurity": ["security", "cyber", "soc", "pentest", "infosec"],
    "Design (UI/UX)": ["designer", "ui", "ux", "product design", "motion"],
    "Product / PM": ["product manager", "project manager", "product owner"],
    "Sales / SDR": ["sales", "sdr", "account manager", "business development", "sales development"],
    "Marketing": ["marketing", "seo", "media buyer", "growth", "affiliate", "content"],
    "HR": ["recruiter", "talent", "hr ", "people ops"],
    "Engineering": ["engineer", "developer", "software", "backend", "frontend", "full-stack", "dev"],
}

# --- Priority tracks (toggleable manually per run) -------------------------
# Key = track id (used in --tracks / RADAR_TRACKS / dashboard checkboxes)
# Value = default on/off. Every track can also be re-enabled at runtime.
TRACKS: dict[str, bool] = {
    "vibe_ai": True,   # ✨ vibe coding / AI-assisted roles
    "support": True,   # 🎧 key support / customer success
    "qa": True,        # 🐞 QA / testing
    "data": True,      # 📊 data / analytics
}

# Which role maps onto which track (used for manual toggles + card counts).
ROLE_TO_TRACK: dict[str, str] = {
    "AI / Vibe Dev": "vibe_ai",
    "Support": "support",
    "QA / Testing": "qa",
    "Data": "data",
    "Business Analyst": "data",  # analyst is part of the data track
}

# Friendly aliases accepted in --tracks / env RADAR_TRACKS.
TRACK_ALIASES: dict[str, str] = {
    "vibe": "vibe_ai",
    "ai": "vibe_ai",
    "vibe_ai": "vibe_ai",
    "support": "support",
    "key_support": "support",
    "qa": "qa",
    "data": "data",
    "analytics": "data",
}

# Strong vibe-coding signals: these phrases ALWAYS count as no-code / vibe
# ("Prompt Engineer" stays vibe even though it contains the word "engineer").
VIBE_KEYWORDS_STRONG: list[str] = [
    "prompt engineer",
    "natural language",
    "vibe",
    "vibe coder",
    "genai",
    "generative ai",
    "copilot",
    "no-code",
    "low-code",
]

# Advisory vibe signals: count as no-code ONLY when no hard coding word
# (engineer/developer/...) is present, so "LLM Engineer" stays engineering.
VIBE_KEYWORDS_GENERIC: list[str] = [
    "llm",
    "ai agent",
    "ai tools",
    "chatgpt",
    "cursor",
    "ai developer",
    "build with ai",
]

# Hard coding words: when present in the title, generic vibe signals lose.
CODE_WORDS: list[str] = [
    "engineer",
    "developer",
    "software",
    "backend",
    "frontend",
    "full-stack",
    "programmer",
    "devops",
    "sre",
]

# English keywords that signal a manual / no-code-first role.
NO_CODE_KEYWORDS = [
    "quality assurance",
    "manual",
    "support",
    "analyst",
    "product",
    "project",
    "sales",
    "marketing",
    "design",
    "recruiter",
    "success",
    "administrator",
    "security analyst",
    "prompt engineer",
    "vibe",
    "natural language",
]

ROLE_ORDER = [
    "AI / Vibe Dev",
    "Engineering",
    "QA / Testing",
    "Data",
    "Business Analyst",
    "Support",
    "Sysadmin / DevOps",
    "Cybersecurity",
    "Design (UI/UX)",
    "Product / PM",
    "Sales / SDR",
    "Marketing",
    "HR",
    "Unknown",
]