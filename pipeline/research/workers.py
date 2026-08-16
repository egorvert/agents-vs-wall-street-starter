"""Stage-A lens workers: W1 metric/historical custodian, W2 guidance analyst.

Each worker: versioned query pack -> evidence blocks -> one structured call ->
verified claim packet. Workers never see each other's output (clean contexts);
the orchestrator merges.
"""

from __future__ import annotations

import re

from langsmith import traceable

from . import config, llm, verify
from .retrieval import Evidence, render_evidence, search_evidence

BASIS_ENUM = ["GAAP", "adjusted", "pre-exceptional", "as-reported"]


def packet_schema(metric_ids: list[str]) -> dict:
    fact = {
        "type": "object", "additionalProperties": False,
        "required": ["metric_id", "period", "period_type", "value", "basis", "eid", "quote", "is_guidance"],
        "properties": {
            "metric_id": {"type": "string", "enum": metric_ids},
            "period": {"type": "string"},
            "period_type": {"type": "string", "enum": ["FY", "H1", "H2", "Q"]},
            "value": {"type": "number"},
            "basis": {"type": "string", "enum": BASIS_ENUM},
            "eid": {"type": "string"},
            "quote": {"type": "string"},
            "is_guidance": {"type": "boolean"},
        },
    }
    claim = {
        "type": "object", "additionalProperties": False,
        "required": ["claim", "metric_ids", "kind", "direction", "driver", "eid", "quote",
                     "counterevidence", "falsifier"],
        "properties": {
            "claim": {"type": "string"},
            "metric_ids": {"type": "array", "items": {"type": "string", "enum": metric_ids}},
            "kind": {"type": "string", "enum": ["fact", "inference"]},
            "direction": {"type": "string", "enum": ["up", "down", "neutral", "unknown"]},
            "driver": {"type": "string"},
            "eid": {"type": "string"},
            "quote": {"type": "string"},
            "counterevidence": {"type": "string"},
            "falsifier": {"type": "string"},
        },
    }
    basis_note = {
        "type": "object", "additionalProperties": False,
        "required": ["metric_id", "definition", "eid", "quote"],
        "properties": {
            "metric_id": {"type": "string", "enum": metric_ids},
            "definition": {"type": "string"},
            "eid": {"type": "string"},
            "quote": {"type": "string"},
        },
    }
    return {
        "type": "object", "additionalProperties": False,
        "required": ["facts", "claims", "basis_notes", "suggested_indicators", "gaps"],
        "properties": {
            "facts": {"type": "array", "items": fact},
            "claims": {"type": "array", "items": claim},
            "basis_notes": {"type": "array", "items": basis_note},
            "suggested_indicators": {"type": "array", "items": {"type": "string"}},
            "gaps": {"type": "string"},
        },
    }


def _prompt(name: str) -> tuple[str, str]:
    text = (config.PROMPTS / name).read_text()
    version = "unversioned"
    if m := re.search(r"prompt_version:\s*(\S+)", text):
        version = m.group(1)
    return text, version


def _metric_context(cid: str, info: dict) -> str:
    lines = [
        f"Company: {info['company']} ({info['ticker']}), company_id={cid}.",
        f"Target period to be forecast: {info['period']} (period_type {info['period_type']}).",
        "Target metrics (the ONLY valid metric_id values, with authoritative unit and basis):",
    ]
    for m in info["metrics"]:
        lines.append(
            f"- {m['metric_id']}: \"{m['label']}\" unit={m['unit']!r} basis={m['basis']}"
        )
    lines.append(
        "Values must be at the unit's scale: USDm/GBPm in millions, USD / share per share, "
        "% in points (4.5 means 4.5%), GBp in pence."
    )
    return "\n".join(lines)


def _query_pack_w1(cid: str, info: dict) -> list[str]:
    queries = []
    for m in info["metrics"]:
        queries.append(m["label"])
        queries.append(f"{m['label']} fiscal quarter")
    queries.append("reconciliation non-GAAP")
    # hints first: the global evidence-block budget must not starve them
    return config.QUERY_HINTS.get(cid, {}).get("w1", []) + queries


def _query_pack_w2(cid: str, info: dict) -> list[str]:
    queries = [f"guidance {m['label']}" for m in info["metrics"]]
    queries += ["guidance fiscal outlook expects", "reaffirms guidance full year",
                "trading statement update", "outlook assumptions"]
    return config.QUERY_HINTS.get(cid, {}).get("w2", []) + queries


def _verified_packet(parsed: dict, evidence_by_eid: dict[str, Evidence],
                     metrics: dict[str, dict]) -> tuple[dict, list[str]]:
    """Drop anything that fails the gates; return (clean packet, rejection log)."""
    rejects: list[str] = []
    facts = []
    for f in parsed.get("facts", []):
        problems = verify.check_fact(f, evidence_by_eid, metrics)
        if problems:
            rejects.extend(problems)
        else:
            facts.append(f)
    rejects.extend(verify.magnitude_outliers(facts))
    facts = [f for f in facts if not f.get("_drop")]
    claims = []
    for c in parsed.get("claims", []):
        problems = verify.check_claim(c, evidence_by_eid)
        if problems:
            rejects.extend(problems)
        else:
            claims.append(c)
    notes = []
    for n in parsed.get("basis_notes", []):
        problems = verify.check_claim({"claim": n.get("definition", ""), "eid": n.get("eid"),
                                       "quote": n.get("quote")}, evidence_by_eid)
        if problems:
            rejects.extend(problems)
        else:
            notes.append(n)
    clean = {
        "facts": facts, "claims": claims, "basis_notes": notes,
        "suggested_indicators": parsed.get("suggested_indicators", []),
        "gaps": parsed.get("gaps", ""),
    }
    return clean, rejects


async def _run_worker(*, worker: str, prompt_file: str, model: str, cid: str,
                      info: dict, queries: list[str], run_id: str) -> dict:
    system, version = _prompt(prompt_file)
    evidence = search_evidence(cid, queries)
    ev_by_eid = {e.eid: e for e in evidence}
    metrics = {m["metric_id"]: m for m in info["metrics"]}
    user = _metric_context(cid, info) + "\n\nEVIDENCE BLOCKS:\n\n" + render_evidence(evidence)

    def validate(parsed: dict) -> list[str]:
        problems = []
        for f in parsed.get("facts", []):
            problems += verify.check_fact(f, ev_by_eid, metrics)
        for c in parsed.get("claims", []):
            problems += verify.check_claim(c, ev_by_eid)
        return problems

    parsed = await llm.call_structured(
        model=model, system=system, user=user,
        schema_name=f"{worker}_packet", schema=packet_schema(list(metrics)),
        prompt_version=version,
        metadata={"run_id": run_id, "company_id": cid, "worker": worker,
                  "stage": "research", "prompt_version": version, "model": model},
        validate=validate,
    )
    clean, rejects = _verified_packet(parsed, ev_by_eid, metrics)
    clean["_worker"] = worker
    clean["_rejects"] = rejects
    clean["_evidence"] = {e.eid: {"source": e.source, "published_at": e.published_at} for e in evidence}
    return clean


@traceable(run_type="chain", name="worker:w1_custodian")
async def w1_custodian(cid: str, info: dict, run_id: str) -> dict:
    return await _run_worker(
        worker="w1_custodian", prompt_file="w1_custodian.md",
        model=config.CUSTODIAN_MODEL, cid=cid, info=info,
        queries=_query_pack_w1(cid, info), run_id=run_id,
    )


@traceable(run_type="chain", name="worker:w2_guidance")
async def w2_guidance(cid: str, info: dict, run_id: str) -> dict:
    return await _run_worker(
        worker="w2_guidance", prompt_file="w2_guidance.md",
        model=config.CUSTODIAN_MODEL, cid=cid, info=info,
        queries=_query_pack_w2(cid, info), run_id=run_id,
    )
