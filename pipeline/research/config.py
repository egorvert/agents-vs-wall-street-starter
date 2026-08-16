"""Research swarm configuration — single place for paths, models, cutoff, metrics.

Key indicators are injected config: the swarm reads each company's metric set from
schemas/metrics.json (edit there to change targets). Nothing in the swarm is
hardcoded to the twelve hackathon metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OFFLINE = REPO / "challenge" / "offline-data"
LIVE = REPO / "challenge" / "live-data"
MANIFEST_PATH = REPO / "schemas" / "metrics.json"
PROMPTS = Path(__file__).resolve().parent / "prompts"
OUT = REPO / "out"
LOGS = REPO / "logs"
CACHE_DIR = OUT / ".cache" / "llm"

# Evidence cutoff (team plan §4): nothing published after this feeds a forecast.
CUTOFF_DATE = "2026-08-16"  # snapshot cutoff 10:55 London

# Recency clause for web recon (Exa, Stage C): only evidence published since the
# company's last report may influence the prediction; older is in the corpus.
LAST_REPORT_DATE = {
    "HD": "2026-05-19",   # Q1 FY2026 results
    "ADI": "2026-05-20",  # Q2 FY2026 results
    "HAS": "2026-07-10",  # Q4 FY2026 trading statement
    "DE": "2026-05-28",   # Q2 FY2026 results
}

WORKER_MODEL = "gpt-5.6-luna"
MERGE_MODEL = "gpt-5.6-terra"
CUSTODIAN_MODEL = "gpt-5.6-terra"  # basis errors swamp modelling gains

# out/<cid>/research/ layout
DOSSIER_NAME = "dossier.md"
CLAIMS_NAME = "claims.jsonl"       # internal working file, NOT a contract
COVERAGE_NAME = "coverage.json"    # internal coverage report

# offline/live directory names per company_id (checked at startup)
DOC_DIRS = {
    "HD": "home-depot",
    "ADI": "analog-devices",
    "HAS": "hays",
    "DE": "deere",
}

DOSSIER_TOKEN_CAP = 8000  # ~4 chars/token heuristic applied in dossier.py

# Per-company query-pack hints — company reporting vocabulary differs (Hays
# speaks "like-for-like"/"preliminary results", Deere guides on net income).
# Versioned config, not code: extend per company as coverage reports show gaps.
QUERY_HINTS: dict[str, dict[str, list[str]]] = {
    "HAS": {
        "w1": ["net fees year ended June", "preliminary results net fees operating profit",
               "pre-exceptional basic earnings per share pence",
               "pre-exceptional operating profit full year"],
        "w2": ["like-for-like net fees FY26", "trading statement fourth quarter net fees",
               "consensus range operating profit"],
        "w3": ["consultant headcount productivity", "temp contracting perm fee mix",
               "cost savings structural"],
        "w4": ["permanent hiring market UK Germany Australia", "job vacancies recruitment market",
               "labour market conditions"],
    },
    "DE": {
        # no w1 hints: tested 13:55 run — they displaced good evidence blocks
        # with PDF-mangled tables and w1 output collapsed from 40 facts to 3
        "w2": ["net income forecast full year outlook", "fiscal 2026 outlook"],
        "w3": ["production precision agriculture segment shipment volumes price",
               "dealer inventory used equipment"],
        "w4": ["farm income commodity prices crop", "agriculture equipment industry demand",
               "large ag tractor combine retail sales"],
    },
    "ADI": {
        "w2": ["outlook revenue midpoint plus or minus", "guidance adjusted gross margin"],
        "w3": ["gross margin utilization factory inventory", "end market industrial automotive mix"],
        "w4": ["semiconductor cycle bookings orders inventory", "industrial automotive demand recovery"],
    },
    "HD": {
        "w2": ["fiscal 2026 guidance comparable sales growth", "guidance total sales growth"],
        "w3": ["comparable transactions average ticket", "pro contractor sales SRS GMS"],
        "w4": ["housing market home improvement demand", "building materials retail sales"],
    },
}


def manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)["companies"]


def company_dirs(cid: str) -> list[Path]:
    dirs = []
    for root in (OFFLINE, LIVE):
        p = root / DOC_DIRS[cid]
        if p.exists():
            dirs.append(p)
    if not dirs:
        raise FileNotFoundError(f"no evidence directories for {cid}")
    return dirs
