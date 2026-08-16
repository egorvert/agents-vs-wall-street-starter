"""Templated Contract-A dossier writer — deterministic, no prose model call.

Every sentence is assembled from verified facts/claims with inline citations.
The jsonl fact block carries reported figures only (guidance stays in prose,
per schemas/dossier.template.md); units are copied from the manifest, never
from model output.
"""

from __future__ import annotations

import json

from . import config
from .verify import latest_guidance


def _cite(ev: dict) -> str:
    return f"(source: `{ev['source']}`, published {ev['published_at'] or 'unknown'})"


def _fact_line(f: dict, ev: dict, unit: str) -> str:
    return json.dumps({
        "metric_id": f["metric_id"], "period": f["period"], "value": f["value"],
        "unit": unit, "basis": f["basis"], "source": ev["source"],
        "published_at": ev["published_at"], "quote": f["quote"],
    }, ensure_ascii=False)


def render_dossier(cid: str, info: dict, merged: dict) -> str:
    metrics = {m["metric_id"]: m for m in info["metrics"]}
    ev = merged["evidence"]          # eid -> {source, published_at}
    facts = merged["facts"]          # verified, deduped
    claims = merged["claims"]
    notes = merged["basis_notes"]
    gaps = merged["gaps"]

    reported = [f for f in facts if not f.get("is_guidance")]
    guidance = [f for f in facts if f.get("is_guidance")]
    current_guidance = latest_guidance(facts, merged["evidence_objects"])

    L: list[str] = []
    L.append(f"# {info['company']} dossier — {cid} {info['period']}")
    L.append("")

    L.append("## Basis and conventions")
    for mid, m in metrics.items():
        note = next((n for n in notes if n["metric_id"] == mid), None)
        line = f"- **{m['label']}** (`{mid}`, unit `{m['unit']}`, basis {m['basis']})."
        if note:
            line += f" {note['definition']} — \"{note['quote']}\" {_cite(ev[note['eid']])}"
        else:
            line += " No explicit definition found in evidence; basis taken from the metrics manifest."
        L.append(line)
    L.append("")

    L.append("## Historical figures")
    for mid, m in metrics.items():
        rows = sorted((f for f in reported if f["metric_id"] == mid), key=lambda f: f["period"])
        L.append(f"### {m['label']} (`{mid}`)")
        if not rows:
            L.append("- No verified historical values extracted — see gaps below.")
        for f in rows:
            e = ev[f["eid"]]
            L.append(
                f"- {f['period']} ({f['period_type']}): **{f['value']} {m['unit']}** — "
                f"\"{f['quote']}\" {_cite(e)}"
            )
        L.append("")

    L.append("## Guidance")
    if guidance:
        for mid, m in metrics.items():
            rows = [f for f in guidance if f["metric_id"] == mid]
            if not rows:
                L.append(f"- {m['label']}: no explicit management guidance found for {info['period']}.")
                continue
            cur = current_guidance.get(mid)
            for f in sorted(rows, key=lambda f: ev[f["eid"]]["published_at"]):
                e = ev[f["eid"]]
                tag = " **[current]**" if cur is f else " [superseded]" if cur else ""
                L.append(
                    f"- {m['label']} {f['period']}: {f['value']} {m['unit']}{tag} — "
                    f"\"{f['quote']}\" {_cite(e)}"
                )
    else:
        L.append("No management guidance for the target period was found in the evidence.")
    L.append("")

    L.append("## Segment / driver detail")
    drivers = [c for c in claims if c["kind"] == "inference" or c["direction"] != "unknown"]
    if drivers:
        for c in drivers:
            mids = ",".join(c["metric_ids"]) or "general"
            L.append(
                f"- [{c['kind']}; {mids}; direction {c['direction']}] {c['claim']} "
                f"Driver: {c['driver']}. \"{c['quote']}\" {_cite(ev[c['eid']])}"
            )
    else:
        L.append("Driver-level research runs in a later stage; none captured yet.")
    if merged["suggested_indicators"]:
        L.append(f"- Suggested indicators for follow-up: {', '.join(sorted(set(merged['suggested_indicators'])))}.")
    L.append("")

    L.append("## Risks and watch items")
    risky = [c for c in claims if c.get("counterevidence")]
    if risky:
        for c in risky:
            e = ev[c["eid"]]
            L.append(
                f"- ({e['published_at'] or 'undated'}) {c['claim']} "
                f"Counterevidence: {c['counterevidence']} Falsifier: {c['falsifier']} {_cite(e)}"
            )
    else:
        L.append("- No counterevidence-bearing claims verified yet.")
    if gaps:
        L.append(f"- **Known gaps (honest):** {gaps}")
    L.append("")

    L.append("## Fact block")
    L.append("```jsonl")
    for f in sorted(reported, key=lambda f: (f["metric_id"], f["period"])):
        L.append(_fact_line(f, ev[f["eid"]], metrics[f["metric_id"]]["unit"]))
    L.append("```")
    L.append("")

    text = "\n".join(L)
    # ~8k-token cap (4 chars/token): trim claim prose before ever touching facts
    if len(text) > config.DOSSIER_TOKEN_CAP * 4 and claims:
        return render_dossier(cid, info, {**merged, "claims": claims[:-1]})
    return text
