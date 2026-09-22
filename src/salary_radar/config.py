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
]

ROLE_ORDER = [
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