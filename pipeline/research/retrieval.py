"""Deterministic retrieval: versioned query packs -> numbered evidence blocks.

No LLM chooses what to search. Workers receive evidence blocks with stable ids
(eid) and cite facts by eid; the merger resolves eid -> file path, so the model
never invents a source path. Blocks are verbatim paragraph text (whitespace
collapsed the same way scripts/validate_contracts.py normalises), so any quoted
sub-span survives the validator's quote check.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import config

sys.path.insert(0, str(config.REPO / "starter"))
from search import parse_frontmatter  # noqa: E402  (organiser-supplied helper)

WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOP = {"a", "an", "and", "company", "for", "of", "the", "to", "total"}


@dataclass(frozen=True)
class Evidence:
    eid: str
    source: str          # repo-relative path (what citations must use)
    published_at: str
    document_type: str
    period: str
    text: str            # verbatim block, whitespace-collapsed


def _blocks(path: Path) -> tuple[dict, list[str]]:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    out = []
    for block in re.split(r"\n\s*\n", body):
        flat = re.sub(r"\s+", " ", block).strip()
        if len(flat) >= 40:
            out.append(flat)
    return meta, out


def _score(flat: str, terms: set[str], meta: dict) -> int:
    lowered = flat.casefold()
    matched = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", lowered)]
    required = 1 if len(terms) == 1 else max(2, (len(terms) + 1) // 2)
    if len(matched) < required:
        return -1
    score = len(matched) * 20
    score += sum(min(len(re.findall(rf"\b{re.escape(t)}\b", lowered)), 3) for t in matched) * 2
    doc_type = str(meta.get("document_type") or "")
    score += {
        "OFFICIAL_GUIDANCE": 30, "COMPANY_HOSTED_CONSENSUS": 25, "FILING": 15,
        "LIVE_INDICATOR": 12, "INDUSTRY_FORECAST": 12, "TRANSCRIPT": 8,
        "REGULATORY_UPDATE": 6, "CORPORATE_NEWS": 4, "EVENT_CALENDAR": -40,
    }.get(doc_type, 0)
    published = str(meta.get("published_at") or "")
    if m := re.match(r"(\d{4})", published):
        score += min(max(int(m.group(1)) - 2018, 0) * 3, 24)
    if re.search(r"[\$£%]|\d\.\d", flat):
        score += 12
    return score


def search_evidence(
    cid: str,
    queries: list[str],
    per_query: int = 6,
    max_blocks: int = 24,  # ~24 blocks is the sweet spot: more induces context rot
    since: str | None = None,
) -> list[Evidence]:
    """Rank paragraph blocks across the company's corpus dirs for a query pack.

    `since` (YYYY-MM-DD) drops evidence published before it — the recency clause
    for sources where only post-last-report information is wanted. Everything
    published after the snapshot cutoff is always dropped.
    """
    dirs = config.company_dirs(cid)
    paths = sorted(
        {p for d in dirs for p in d.rglob("*.md") if p.name not in {"INDEX.md", "README.md"}}
    )
    parsed: list[tuple[dict, str, list[str]]] = []
    for path in paths:
        meta, blocks = _blocks(path)
        published = str(meta.get("published_at") or "")[:10]
        if published and published > config.CUTOFF_DATE:
            continue  # cutoff discipline: never even rank post-cutoff evidence
        if since and published and published < since:
            continue
        rel = path.relative_to(config.REPO).as_posix()
        parsed.append((meta, rel, blocks))

    chosen: dict[str, Evidence] = {}
    for query in queries:
        terms = {w.casefold() for w in WORD_RE.findall(query)} - STOP
        ranked: list[tuple[int, str, str, dict]] = []
        for meta, rel, blocks in parsed:
            for flat in blocks:
                s = _score(flat, terms, meta)
                if s > 0:
                    ranked.append((s, rel, flat, meta))
        ranked.sort(key=lambda r: (-r[0], r[1]))
        per_doc: dict[str, int] = {}
        taken = 0
        for s, rel, flat, meta in ranked:
            if taken >= per_query:
                break
            if per_doc.get(rel, 0) >= 2:  # max 2 blocks per document per query
                continue
            key = f"{rel}::{flat[:80]}"
            if key in chosen:
                continue
            per_doc[rel] = per_doc.get(rel, 0) + 1
            taken += 1
            chosen[key] = Evidence(
                eid=f"E{len(chosen) + 1}",
                source=rel,
                published_at=str(meta.get("published_at") or "")[:10],
                document_type=str(meta.get("document_type") or ""),
                period=str(meta.get("period") or ""),
                text=flat,
            )
    return list(chosen.values())[:max_blocks]


def render_evidence(evidence: list[Evidence]) -> str:
    lines = []
    for e in evidence:
        lines.append(
            f"[{e.eid}] source={e.source} published={e.published_at or '?'} "
            f"type={e.document_type or '?'} period={e.period or '?'}\n{e.text}"
        )
    return "\n\n".join(lines)
