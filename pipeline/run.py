#!/usr/bin/env python3
"""Orchestrator: one command, four companies, four workbooks.

    python3 pipeline/run.py --company HD --stub     # walking skeleton from fixtures
    python3 pipeline/run.py --all --stub
    python3 pipeline/run.py --all                   # real pipeline (stages TBD)

Stage owners (docs/TEAM-PLAN.md §3): research 🔴, analysis+combine 🟢, quant 🔵.
This file (🔴) wires stages together, enforces the fallback chain, and guarantees
a normalised out/<cid>/final.json exists before the workbook writer runs — the
no-blank guarantee lives HERE, not in any model.

Fallback chain per metric (§5): 0 combine → 1 range base → 2 consensus anchor →
3 seasonal naive from timeseries → 4 last reported value.
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "pipeline"))
from workbook.writer import write_workbook  # noqa: E402

OUT = REPO / "out"
FIXTURES = REPO / "fixtures"
COMPANIES = ("HD", "ADI", "HAS", "DE")


def log(msg: str) -> None:
    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def manifest() -> dict:
    with open(REPO / "schemas" / "metrics.json") as f:
        return json.load(f)["companies"]


# ---------------------------------------------------------------- fallback chain

def resolve_finals(cid: str, root: Path) -> dict:
    """Return a normalised final.json dict, applying the fallback chain per metric."""
    info = manifest()[cid]

    def read(name: str) -> dict:
        p = root / name
        return json.loads(p.read_text()) if p.exists() else {}

    combine = {f["metric_id"]: f for f in read("final.json").get("finals", [])}
    ranges = {r["metric_id"]: r for r in read("ranges.json").get("ranges", [])}
    anchors = {a["metric_id"]: a for a in read("consensus.json").get("anchors", [])}
    series = {s["metric_id"]: s for s in read("timeseries.json").get("series", [])}

    finals = []
    for m in info["metrics"]:
        mid, unit, basis = m["metric_id"], m["unit"], m["basis"]
        f = None
        if mid in combine:                                   # tier 0
            f = dict(combine[mid])
            r = ranges.get(mid)
            if r and not (r["low"] <= f["value"] <= r["high"]):
                log(f"REJECTED {cid}/{mid}: combine value {f['value']} outside "
                    f"[{r['low']}, {r['high']}] — clamping to range base (tier 1)")
                f = None
        if f is None and mid in ranges:                      # tier 1
            f = {"metric_id": mid, "value": ranges[mid]["base"], "unit": unit, "basis": basis,
                 "anchor": ranges[mid]["base"], "anchor_kind": "range_base", "delta": 0.0,
                 "delta_evidence": [], "fallback_tier": 1,
                 "rationale": "fallback: guardrail range base"}
        if f is None and mid in anchors:                     # tier 2
            f = {"metric_id": mid, "value": anchors[mid]["value"], "unit": unit, "basis": basis,
                 "anchor": anchors[mid]["value"], "anchor_kind": anchors[mid].get("kind", "consensus"),
                 "delta": 0.0, "delta_evidence": [], "fallback_tier": 2,
                 "rationale": "fallback: public anchor"}
        if f is None and mid in series:                      # tier 3 / 4
            pts = sorted(series[mid].get("points", []), key=lambda p: p["period"])
            comparable = [p for p in pts if p["period"].endswith(info["period"][-2:])] \
                if info["period_type"] == "Q" else pts
            if len(comparable) >= 2:
                prev, last = comparable[-2]["value"], comparable[-1]["value"]
                value = last * (last / prev) if prev else last
                tier, why = 3, "fallback: seasonal naive (last comparable x trailing YoY)"
            else:
                value, tier, why = pts[-1]["value"], 4, "fallback: last reported value"
            f = {"metric_id": mid, "value": round(value, 2), "unit": unit, "basis": basis,
                 "anchor": pts[-1]["value"], "anchor_kind": "last_reported", "delta": 0.0,
                 "delta_evidence": [], "fallback_tier": tier, "rationale": why}
        if f is None:
            raise RuntimeError(f"{cid}/{mid}: no data at any fallback tier — cannot produce a number")
        if f["fallback_tier"] != 0:
            log(f"FALLBACK {cid}/{mid}: tier {f['fallback_tier']} ({f['rationale']})")
        finals.append(f)
    return {"schema_version": 1, "company_id": cid, "finals": finals}


# ---------------------------------------------------------------------- stages

def run_company(cid: str, stub: bool) -> None:
    root = OUT / cid
    log(f"=== {cid} start (stub={stub}) ===")

    if stub:
        fix = FIXTURES / cid
        if fix.exists():
            shutil.copytree(fix, root, dirs_exist_ok=True)
            log(f"{cid}: copied fixtures -> {root}")
        else:
            root.mkdir(parents=True, exist_ok=True)
            log(f"{cid}: no fixtures — STUB placeholders only (not a forecast)")
            info = manifest()[cid]
            stub_finals = [{"metric_id": m["metric_id"], "value": 1.0, "unit": m["unit"],
                            "basis": m["basis"], "anchor": 1.0, "anchor_kind": "stub",
                            "delta": 0.0, "delta_evidence": [], "fallback_tier": 4,
                            "rationale": "STUB placeholder — replace via pipeline"}
                           for m in info["metrics"]]
            (root / "final.json").write_text(json.dumps(
                {"schema_version": 1, "company_id": cid, "finals": stub_finals}, indent=2))
    else:
        # TODO 🔴 research swarm -> out/<cid>/research/dossier.md
        # TODO 🟢 analysis      -> out/<cid>/analysis/* + consensus.json
        # TODO 🔵 quant         -> out/<cid>/timeseries.json + ranges.json
        # TODO 🟢 combine       -> out/<cid>/final.json
        raise SystemExit(f"{cid}: real pipeline stages not wired yet — use --stub")

    resolved = resolve_finals(cid, root)
    (root / "final.json").write_text(json.dumps(resolved, indent=2))
    log(f"{cid}: final.json normalised "
        f"(tiers: {[f['fallback_tier'] for f in resolved['finals']]})")

    full_fixture = (FIXTURES / cid / "timeseries.json").exists()
    check = [sys.executable, "scripts/validate_contracts.py", "--company", cid]
    if stub and not full_fixture:
        check.append("--final-only")
    r = subprocess.run(check, cwd=REPO)
    if r.returncode != 0:
        raise SystemExit(f"{cid}: contract validation FAILED — not writing a workbook")

    out = write_workbook(cid, resolved["finals"])
    log(f"{cid}: wrote {out.relative_to(REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--company", choices=COMPANIES)
    g.add_argument("--all", action="store_true")
    ap.add_argument("--stub", action="store_true", help="run from fixtures/placeholders")
    args = ap.parse_args()

    targets = COMPANIES if args.all else (args.company,)
    for cid in targets:
        run_company(cid, stub=args.stub)
    log(f"done: {len(targets)} company(ies) -> submission/")


if __name__ == "__main__":
    main()
