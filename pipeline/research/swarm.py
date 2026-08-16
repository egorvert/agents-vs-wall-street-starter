"""Research swarm orchestrator (Stage A: W1 custodian + W2 guidance).

    python3 -m pipeline.research.swarm --company HD
    python3 -m pipeline.research.swarm --all

Deterministic fan-out: same workers every run, clean contexts, single-writer
merge, every rejection logged. Writes out/<cid>/research/{dossier.md,
claims.jsonl, coverage.json} and appends a timestamped run log to logs/.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import sys
import uuid
from pathlib import Path

from langsmith import traceable

from . import config, verify
from .dossier import render_dossier
from .retrieval import Evidence
from .workers import (counterevidence_pass, prose_pass, w1_custodian,
                      w2_guidance, w3_operating_model, w4_demand_peers)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


class RunLog:
    def __init__(self, run_id: str):
        config.LOGS.mkdir(exist_ok=True)
        self.path = config.LOGS / f"research-{run_id}.jsonl"

    def event(self, kind: str, **data) -> None:
        rec = {"ts": _now(), "kind": kind, **data}
        with self.path.open("a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[{rec['ts']}] {kind}: " + json.dumps(data, ensure_ascii=False)[:200], flush=True)


def _merge(packets: list[dict]) -> dict:
    """Single-writer merge of worker packets (anonymised: worker tags dropped
    from content, kept only in the log)."""
    evidence: dict[str, dict] = {}
    evidence_objects: dict[str, Evidence] = {}
    facts, claims, notes, suggested = [], [], [], []
    gaps = []
    for p in packets:
        # re-key eids per worker to avoid collisions (E1 from W1 vs E1 from W2)
        prefix = p["_worker"][:2]
        remap = {}
        for eid, meta in p["_evidence"].items():
            new = f"{prefix}:{eid}"
            remap[eid] = new
            evidence[new] = meta
            evidence_objects[new] = Evidence(
                eid=new, source=meta["source"], published_at=meta["published_at"],
                document_type="", period="", text="",
            )
        for f in p["facts"]:
            facts.append({**f, "eid": remap[f["eid"]]})
        for c in p["claims"]:
            # _lens kept for coverage/logs; stripped before any LLM sees claims
            claims.append({**c, "eid": remap[c["eid"]], "_lens": p["_worker"]})
        for n in p["basis_notes"]:
            notes.append({**n, "eid": remap[n["eid"]]})
        suggested += p["suggested_indicators"]
        if p["gaps"]:
            gaps.append(p["gaps"])
    facts = verify.dedupe_facts(facts, evidence_objects)
    return {
        "facts": facts, "claims": claims, "basis_notes": notes,
        "suggested_indicators": suggested, "gaps": " ".join(gaps),
        "evidence": evidence, "evidence_objects": evidence_objects,
    }


@traceable(run_type="chain", name="research_company")
async def research_company(cid: str, run_id: str, log: RunLog) -> bool:
    info = config.manifest()[cid]
    log.event("company_start", company_id=cid, metrics=[m["metric_id"] for m in info["metrics"]])

    async def guarded(name, coro):
        try:
            return await coro
        except Exception as e:  # one worker failing must not sink the company
            log.event("worker_error", company_id=cid, worker=name, error=repr(e))
            return None

    packets = await asyncio.gather(
        guarded("w1_custodian", w1_custodian(cid, info, run_id)),
        guarded("w2_guidance", w2_guidance(cid, info, run_id)),
        guarded("w3_operating_model", w3_operating_model(cid, info, run_id)),
        guarded("w4_demand_peers", w4_demand_peers(cid, info, run_id)),
    )
    packets = [p for p in packets if p]
    if not packets:
        log.event("company_failed", company_id=cid, reason="all workers failed")
        return False

    for p in packets:
        for r in p["_rejects"]:
            log.event("rejected", company_id=cid, worker=p["_worker"], detail=r)
        log.event("worker_done", company_id=cid, worker=p["_worker"],
                  facts=len(p["facts"]), claims=len(p["claims"]))

    merged = _merge(packets)

    # counterevidence: clean-context skeptic over anonymised claims + guidance
    anon_claims = [{k: v for k, v in c.items() if not k.startswith("_")}
                   for c in merged["claims"]]
    guidance_facts = [f for f in merged["facts"] if f.get("is_guidance")]
    challenges: list[dict] = []
    ce = await guarded("counterevidence", counterevidence_pass(
        cid, info, run_id, anon_claims, guidance_facts))
    if ce:
        for r in ce["_rejects"]:
            log.event("rejected", company_id=cid, worker="counterevidence", detail=r)
        for eid, meta in ce["_evidence"].items():
            new = f"ce:{eid}"
            merged["evidence"][new] = meta
        challenges = [{**c, "eid": f"ce:{c['eid']}"} for c in ce["challenges"]]
        log.event("challenges", company_id=cid, kept=len(challenges),
                  severities=[c["severity"] for c in challenges])

    coverage = verify.coverage_report(
        cid, {m["metric_id"]: m for m in info["metrics"]}, merged["facts"],
        merged["claims"], challenges,
    )
    log.event("coverage", company_id=cid, coverage=coverage["coverage"])

    outdir = config.OUT / cid / "research"
    outdir.mkdir(parents=True, exist_ok=True)

    # templated dossier first (always shippable), then prose overviews on top
    text = render_dossier(cid, info, merged, challenges=challenges)
    prose = await guarded("prose", prose_pass(cid, run_id, text))
    if prose:
        if prose["_dropped"]:
            for d in prose["_dropped"]:
                log.event("prose_dropped", company_id=cid, **d)
        text = render_dossier(cid, info, merged, prose=prose, challenges=challenges)
    tmp = outdir / (config.DOSSIER_NAME + ".tmp")
    tmp.write_text(text)
    tmp.rename(outdir / config.DOSSIER_NAME)  # atomic
    with (outdir / config.CLAIMS_NAME).open("w") as fh:
        for c in merged["claims"]:
            e = merged["evidence"][c["eid"]]
            rec = {k: v for k, v in c.items() if k != "_lens"}
            rec.update(lens=c.get("_lens", ""), source=e["source"],
                       published_at=e["published_at"])
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        for ch in challenges:
            e = merged["evidence"][ch["eid"]]
            fh.write(json.dumps({**ch, "lens": "counterevidence", "source": e["source"],
                                 "published_at": e["published_at"]}, ensure_ascii=False) + "\n")
    (outdir / config.COVERAGE_NAME).write_text(json.dumps(coverage, indent=2))
    log.event("dossier_written", company_id=cid, path=str(outdir / config.DOSSIER_NAME),
              chars=len(text), facts=len(merged["facts"]))
    return True


async def amain(cids: list[str]) -> int:
    run_id = uuid.uuid4().hex[:8]
    log = RunLog(run_id)
    log.event("run_start", run_id=run_id, companies=cids, cutoff=config.CUTOFF_DATE,
              models={"custodian": config.CUSTODIAN_MODEL, "worker": config.WORKER_MODEL})
    results = await asyncio.gather(*(research_company(c, run_id, log) for c in cids))
    ok = sum(1 for r in results if r)
    log.event("run_done", ok=ok, total=len(cids))
    return 0 if ok == len(cids) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--company", choices=sorted(config.DOC_DIRS))
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()
    cids = sorted(config.DOC_DIRS) if args.all else [args.company]
    return asyncio.run(amain(cids))


if __name__ == "__main__":
    sys.exit(main())
