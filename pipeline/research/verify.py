"""Deterministic verification gates for worker output.

Mirrors scripts/validate_contracts.py normalisation exactly, so anything that
passes here passes the team validator. Every rejection is returned as a problem
string (fed to the one retry) and logged — the judges' rubric credits visibly
rejected values.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import config
from .retrieval import Evidence

PERIOD_RE = re.compile(r"^FY\d{4}(Q[1-4]|H[12])?$")
BASIS = {"GAAP", "adjusted", "pre-exceptional", "as-reported"}

_file_cache: dict[str, str] = {}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("*", "")).strip()


def _file_text(source: str) -> str | None:
    if source not in _file_cache:
        p = config.REPO / source
        if not p.exists():
            return None
        _file_cache[source] = normalise(p.read_text(errors="replace"))
    return _file_cache[source]


def value_in_quote(value: float, quote: str) -> bool:
    v = abs(float(value))
    candidates = {
        f"{v:,.0f}", f"{v:.0f}", f"{v:g}", f"{v:.1f}", f"{v:.2f}",
        f"{v:,.1f}", f"{v:,.2f}",          # 1,113.6 — UK GBPm style
        f"{v / 1000:.1f}", f"{v / 1000:.2f}",
    }
    return any(c in quote for c in candidates)


def _nearby_sentences(source_text: str, quote: str, n: int = 2) -> list[str]:
    """Admissible alternatives for the retry message: sentences from the source
    that share the most words with the failed quote."""
    words = set(re.findall(r"[a-z0-9]{3,}", quote.casefold()))
    best: list[tuple[int, str]] = []
    for sent in re.split(r"(?<=[.!?]) ", source_text):
        overlap = len(words & set(re.findall(r"[a-z0-9]{3,}", sent.casefold())))
        if overlap:
            best.append((overlap, sent.strip()))
    best.sort(key=lambda t: -t[0])
    return [s for _, s in best[:n]]


def check_fact(
    fact: dict, evidence_by_eid: dict[str, Evidence], metrics: dict[str, dict]
) -> list[str]:
    """Return problem strings for one fact; empty list = verified."""
    problems = []
    eid, quote = fact.get("eid", ""), fact.get("quote", "")
    ev = evidence_by_eid.get(eid)
    if ev is None:
        return [f"fact {fact.get('metric_id')}/{fact.get('period')}: unknown eid {eid!r}"]

    src_text = _file_text(ev.source)
    if src_text is None:
        return [f"fact eid {eid}: source file missing {ev.source}"]
    if not quote or normalise(quote) not in src_text:
        alts = _nearby_sentences(src_text, quote or "")
        hint = f" Admissible verbatim sentences from {ev.source}: " + " | ".join(alts) if alts else ""
        problems.append(
            f"fact {fact.get('metric_id')}/{fact.get('period')}: quote is not a verbatim "
            f"span of {ev.source}.{hint}"
        )
    mid = fact.get("metric_id")
    m = metrics.get(mid)
    if m is None:
        problems.append(f"fact: unknown metric_id {mid!r} — use only the configured metric ids")
    else:
        if fact.get("basis") != m["basis"]:
            problems.append(
                f"fact {mid}/{fact.get('period')}: basis {fact.get('basis')!r} must be "
                f"{m['basis']!r} for this metric (manifest is authoritative)"
            )
    for marker in config.QUOTE_DISQUALIFIERS.get(mid or "", []):
        if marker in (quote or "").casefold():
            problems.append(
                f"fact {mid}/{fact.get('period')}: quote is a '{marker}' line, not "
                f"'{(m or {}).get('label', mid)}' — quote the row stating the metric's own label"
            )
    if not PERIOD_RE.match(fact.get("period", "")):
        problems.append(
            f"fact {mid}: bad period {fact.get('period')!r} (want FY2026, FY2026Q2, FY2026H1)"
        )
    v = fact.get("value")
    if not isinstance(v, (int, float)):
        problems.append(f"fact {mid}/{fact.get('period')}: non-numeric value {v!r}")
    elif quote and normalise(quote) in (src_text or "") and not value_in_quote(v, quote):
        problems.append(
            f"fact {mid}/{fact.get('period')}: value {v} does not appear in its own quote — "
            f"check scale (USDm means millions; percentages are points; GBp is pence)"
        )
    return problems


def check_claim(claim: dict, evidence_by_eid: dict[str, Evidence]) -> list[str]:
    eid, quote = claim.get("eid", ""), claim.get("quote", "")
    ev = evidence_by_eid.get(eid)
    if ev is None:
        return [f"claim {claim.get('claim', '')[:40]!r}: unknown eid {eid!r}"]
    src = _file_text(ev.source)
    if src is None:
        return [f"claim eid {eid}: source file missing {ev.source}"]
    if quote and normalise(quote) not in src:
        alts = _nearby_sentences(src, quote)
        hint = " Admissible: " + " | ".join(alts) if alts else ""
        return [f"claim {claim.get('claim', '')[:40]!r}: quote not verbatim in {ev.source}.{hint}"]
    return []


def magnitude_outliers(facts: list[dict]) -> list[str]:
    """Same-metric values should sit within 2 orders of magnitude of the median."""
    problems = []
    by_metric: dict[str, list[dict]] = {}
    for f in facts:
        by_metric.setdefault(f["metric_id"], []).append(f)
    for mid, fs in by_metric.items():
        vals = sorted(abs(float(f["value"])) for f in fs if f.get("value"))
        if len(vals) < 3:
            continue
        med = vals[len(vals) // 2] or 1.0
        for f in fs:
            v = abs(float(f["value"]))
            if v and (v / med > 100 or med / v > 100):
                problems.append(
                    f"magnitude: {mid}/{f['period']} value {f['value']} is >100x from the "
                    f"series median {med} — likely a scale error; dropped"
                )
                f["_drop"] = True
    return problems


def dedupe_facts(facts: list[dict], evidence_by_eid: dict[str, Evidence]) -> list[dict]:
    """One fact per (metric, period[, guidance-flag]); prefer earlier-published sources."""
    def keyfn(f):
        return (f["metric_id"], f["period"], bool(f.get("is_guidance")))
    best: dict[tuple, dict] = {}
    for f in facts:
        if f.get("_drop"):
            continue
        k = keyfn(f)
        cur = best.get(k)
        pub = evidence_by_eid[f["eid"]].published_at if f["eid"] in evidence_by_eid else ""
        curpub = (
            evidence_by_eid[cur["eid"]].published_at
            if cur and cur.get("eid") in evidence_by_eid else ""
        )
        if cur is None:
            best[k] = f
        elif pub and curpub:
            # reported facts: earliest (primary) source wins;
            # guidance: newest statement wins (supersession)
            newer_wins = bool(f.get("is_guidance"))
            if (pub > curpub) == newer_wins and pub != curpub:
                best[k] = f
    return list(best.values())


def latest_guidance(facts: list[dict], evidence_by_eid: dict[str, Evidence]) -> dict[str, dict]:
    """Supersession: newest pre-cutoff guidance statement wins per metric."""
    latest: dict[str, dict] = {}
    for f in facts:
        if not f.get("is_guidance"):
            continue
        pub = evidence_by_eid[f["eid"]].published_at if f["eid"] in evidence_by_eid else ""
        cur = latest.get(f["metric_id"])
        curpub = (
            evidence_by_eid[cur["eid"]].published_at
            if cur and cur.get("eid") in evidence_by_eid else ""
        )
        if cur is None or pub > curpub:
            latest[f["metric_id"]] = f
    return latest


def coverage_report(cid: str, metrics: dict, facts: list[dict], claims: list[dict],
                    challenges: list[dict] | None = None) -> dict:
    """metric x dimension matrix — the personas.md completeness gate.
    Dimensions: historical baseline, guidance, operating-driver bridge,
    independent external corroboration, counterevidence."""
    challenges = challenges or []
    report = {}
    for mid in metrics:
        historical = [f for f in facts if f["metric_id"] == mid and not f.get("is_guidance")]
        guidance = [f for f in facts if f["metric_id"] == mid and f.get("is_guidance")]
        drivers = [c for c in claims if mid in c.get("metric_ids", [])
                   and c.get("_lens") == "w3_operating_model"]
        external = [c for c in claims if mid in c.get("metric_ids", [])
                    and c.get("_lens") == "w4_demand_peers"]
        # challenges name a claim, not a metric — map through the claims they attack
        challenged = [
            ch for ch in challenges
            if any(mid in c.get("metric_ids", []) and c["claim"][:60] in ch["target_claim"]
                   for c in claims)
            or "guidance" in ch["target_claim"].casefold()
        ]
        counter = [c for c in claims if mid in c.get("metric_ids", []) and c.get("counterevidence")]
        report[mid] = {
            "historical_points": len(historical),
            "historical_ok": len(historical) >= 8,   # 8+ where the corpus allows
            "guidance_present": bool(guidance),
            "driver_claims": len(drivers),
            "external_corroboration": bool(external),
            "counterevidence_present": bool(counter or challenged),
        }
    return {"company_id": cid, "coverage": report}
