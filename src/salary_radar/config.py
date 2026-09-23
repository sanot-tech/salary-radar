"""Central configuration: paths, sources and role categories.

A Vibe Coder is a super-universal: architect + programmer + businessman
in one. Vibe coding is the modern way to build & launch faster. The radar
is rebranded from "no-code" to "vibe" everywhere — no-code is just the
on-ramp; vibe is the destination.
"""

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
    # --- vibe-era sources (added 2026) ----------------------------------
    "himalayas": {
        "url": "https://himalayas.app/jobs-api",
        "auth": "none",
        "root": "jobs",
    },
    "aidevboard": {
        "url": "https://aidevboard.com/api/v1/jobs",
        "auth": "none",
        "root": "jobs",
    },
    "nocodejobs": {
        "url": "https://nocodejobs.org/jobs.json",
        "auth": "none",
        "root": "jobs",
    },
    "workingnomads": {
        "url": "https://www.workingnomads.com/api/exposed_jobs/",
        "auth": "none",
        "root": "array",
    },
}

# Vibe Coder = super-universal: architect + programmer + businessman in one.
# These are the sub-categories a vibe coder can specialise in.
TRACKS: dict[str, bool] = {
    "ai_agents": True,    # 🤖 AI agents / automation / MCP
    "prompt_eng": True,   # 🗣️ prompt & AI interfaces / LLM
    "builders": True,     # 🧱 visual / low-code builders (Bubble, Webflow, PowerApps...)
    "ai_creative": True,  # 🎨 generative design / media / content
    "ai_product": True,   # 🚀 AI product / business / launch (super-universal)
}

# Friendly aliases accepted in --tracks / env RADAR_TRACKS.
TRACK_ALIASES: dict[str, str] = {
    "vibe": None,  # special: "all vibe tracks"
    "ai": "ai_agents",
    "agents": "ai_agents",
    "ai_agents": "ai_agents",
    "automation": "ai_agents",
    "mcp": "ai_agents",
    "prompt": "prompt_eng",
    "prompt_eng": "prompt_eng",
    "llm": "prompt_eng",
    "build": "builders",
    "builders": "builders",
    "builder": "builders",
    "lowcode": "builders",
    "creative": "ai_creative",
    "ai_creative": "ai_creative",
    "gen": "ai_creative",
    "product": "ai_product",
    "ai_product": "ai_product",
    "business": "ai_product",
}

# Vibe-signal keywords used to split a vibe-coder role into a sub-track.
# Later keys run first so specific tools win over generic terms.
VIBE_SUBCATEGORY_KEYWORDS: dict[str, list[str]] = {
    "builders": [
        "bubble", "webflow", "flutterflow", "adalo", "glide", "thunkable",
        "powerapps", "power automate", "powerplatform", "retool", "airtable",
        "zapier", "make.com", "notion", "low-code", "lowcode", "visual builder",
    ],
    "ai_agents": [
        "ai agent", "agents", "agentic", "mcp", "n8n", "automation",
        "autonomous", "workflow", "orchestration",
    ],
    "ai_creative": [
        "midjourney", "stable diffusion", "generative design", "generative art",
        "ai art", "genai content", "ai video", "ai image", "multimodal",
        "illustrator", "creative technologist", "creative", "designer", "design",
    ],
    "prompt_eng": [
        "prompt", "llm", "gpt", "claude", "rag", "fine-tun", "fine tun",
        "natural language", "language model",
    ],
    "ai_product": [
        "vibe coder", "vibe coding", "ai developer", "ai product",
        "ai product manager", "build in public", "solo founder", "indie hacker",
        "ai startup", "super-universal", "super universal",
    ],
}

# Role categories are guesses from the job title.
# They power the "vibe friendly" analysis.
ROLE_KEYWORDS = {
    "AI / Vibe Dev": ["prompt engineer", "vibe coder", "vibe coding", "ai agent",
                      "ai developer", "natural language", "copilot", "llm", "genai",
                      "generative ai", "ai tools", "chatgpt", "cursor", "vibe",
                      "low-code", "no-code", "bubble", "webflow", "n8n", "mcp"],
    "QA / Testing": ["qa", "quality", "test", "tester", "automation test"],
    "Business Analyst": ["business analyst", "data analyst", "product analyst"],
    "Data": ["data engineer", "data scientist", "analysis", "analytics",
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

# Strong vibe signals: these ALWAYS count as vibe / no-code friendly.
VIBE_KEYWORDS_STRONG: list[str] = [
    "prompt engineer",
    "prompt editor",
    "natural language",
    "vibe coder",
    "vibe coding",
    "genai",
    "generative ai",
    "copilot",
    "no-code",
    "low-code",
    "no code",
    "low code",
    "bubble.io",
    "webflow",
    "n8n",
    "ai developer",
    "ai agent developer",
    "automation developer",
    "agentic",
    "vibe",
]

# Advisory vibe signals: count ONLY when no hard coding word is present.
VIBE_KEYWORDS_GENERIC: list[str] = [
    "ai agent",
    "llm",
    "ai tools",
    "chatgpt",
    "cursor",
    "chatbot",
    "assistant",
    "automation",
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

# English keywords that signal a pure vibe role (loose fallback, no
# QA/support/analyst — those are NOT vibe coders).
VIBE_KEYWORDS = [
    "prompt engineer",
    "vibe",
    "natural language",
    "ai app",
    "mvp",
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