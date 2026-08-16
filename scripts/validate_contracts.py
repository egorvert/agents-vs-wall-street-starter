#!/usr/bin/env python3
"""Validate the file-based handoff contracts defined in docs/TEAM-PLAN.md §4.

Usage:
    python3 scripts/validate_contracts.py --fixtures            # validate fixtures/HD
    python3 scripts/validate_contracts.py --company HD          # validate out/HD
    python3 scripts/validate_contracts.py --company HD --final-only

Stdlib only. Exit code 1 if any ERROR; WARNs never fail the run.
Checks: file presence, schema shape, verbatim units/labels vs schemas/metrics.json,
basis enum, metric coverage, low<=base<=high, final within range, and citations —
the cited file must exist and contain the quote (whitespace/markdown-normalised).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "schemas" / "metrics.json"
BASIS_VALUES = {"GAAP", "adjusted", "pre-exceptional", "as-reported"}
PERIOD_RE = re.compile(r"^FY\d{4}(Q[1-4]|H[12])?$")
FACT_FIELDS = {"metric_id", "period", "value", "unit", "basis", "source", "published_at", "quote"}

errors: list[str] = []
warns: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warns.append(msg)


def load_manifest() -> dict:
    with open(MANIFEST) as f:
        return json.load(f)["companies"]


def normalise(text: str) -> str:
    """Collapse whitespace and strip markdown emphasis so quotes match prose."""
    return re.sub(r"\s+", " ", text.replace("*", "")).strip()


_file_cache: dict[str, str] = {}


def check_citation(where: str, source: str, quote: str, value: float | None = None) -> None:
    if not source:
        err(f"{where}: citation missing 'source'")
        return
    if source.startswith("http://") or source.startswith("https://"):
        warn(f"{where}: URL source not verifiable offline ({source}) — prefer a live-data note")
        return
    path = REPO / source
    if not path.exists():
        err(f"{where}: cited file does not exist: {source}")
        return
    if not quote:
        err(f"{where}: citation missing 'quote'")
        return
    if source not in _file_cache:
        _file_cache[source] = normalise(path.read_text(errors="replace"))
    if normalise(quote) not in _file_cache[source]:
        err(f"{where}: quote not found verbatim in {source}: \"{quote[:60]}…\"")
        return
    if value is not None and not _value_in_quote(value, quote):
        warn(f"{where}: value {value} not recognisably present in its quote")


def _value_in_quote(value: float, quote: str) -> bool:
    v = abs(float(value))
    candidates = {
        f"{v:,.0f}", f"{v:.0f}", f"{v:g}", f"{v:.1f}", f"{v:.2f}",
        f"{v / 1000:.1f}",  # 45277 quoted as "$45.3 billion"
    }
    return any(c in quote for c in candidates)


def check_period(where: str, period: str) -> None:
    if not PERIOD_RE.match(period or ""):
        err(f"{where}: bad period string {period!r} (want FY2026, FY2026Q2, FY2026H1)")


def check_common(where: str, obj: dict, metrics: dict, expect_unit_of: str | None = None) -> None:
    mid = obj.get("metric_id")
    if mid not in metrics:
        err(f"{where}: unknown metric_id {mid!r}")
        return
    m = metrics[mid]
    if obj.get("unit") != m["unit"]:
        err(f"{where}: unit {obj.get('unit')!r} != manifest {m['unit']!r} (copy verbatim)")
    basis = obj.get("basis")
    if basis not in BASIS_VALUES:
        err(f"{where}: basis {basis!r} not in {sorted(BASIS_VALUES)}")


def parse_fact_block(path: Path, metrics: dict) -> int:
    text = path.read_text(errors="replace")
    m = re.search(r"```jsonl\n(.*?)```", text, re.DOTALL)
    if not m:
        err(f"{path.name}: no ```jsonl fact block found")
        return 0
    n = 0
    for i, line in enumerate(m.group(1).strip().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        where = f"{path.name} fact {i}"
        try:
            fact = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"{where}: invalid JSON ({e})")
            continue
        missing = FACT_FIELDS - fact.keys()
        if missing:
            err(f"{where}: missing fields {sorted(missing)}")
            continue
        check_common(where, fact, metrics)
        check_period(where, fact["period"])
        check_citation(where, fact["source"], fact["quote"], fact["value"])
        n += 1
    return n


def validate_company(root: Path, cid: str, manifest: dict, final_only: bool = False) -> None:
    info = manifest[cid]
    metrics = {m["metric_id"]: m for m in info["metrics"]}
    all_ids = set(metrics)

    def need(rel: str) -> Path | None:
        p = root / rel
        if not p.exists():
            err(f"{cid}: missing {rel}")
            return None
        return p

    ranges_by_id: dict[str, dict] = {}

    if not final_only:
        for rel in ("research/dossier.md", "analysis/facts.md"):
            if p := need(rel):
                if parse_fact_block(p, metrics) == 0:
                    warn(f"{cid}/{rel}: fact block is empty")
        for rel in ("analysis/context.md", "analysis/news.md"):
            need(rel)

        if p := need("consensus.json"):
            data = json.loads(p.read_text())
            if data.get("company_id") != cid:
                err(f"{cid}/consensus.json: company_id {data.get('company_id')!r} != {cid}")
            for i, a in enumerate(data.get("anchors", []), 1):
                where = f"{cid}/consensus.json anchor {i}"
                check_common(where, a, metrics)
                if not a.get("kind"):
                    err(f"{where}: missing 'kind'")
                check_citation(where, a.get("source", ""), a.get("quote", ""), a.get("value"))

        if p := need("timeseries.json"):
            data = json.loads(p.read_text())
            if data.get("company_id") != cid:
                err(f"{cid}/timeseries.json: company_id mismatch")
            for s in data.get("series", []):
                where = f"{cid}/timeseries {s.get('metric_id')}"
                check_common(where, s, metrics)
                if s.get("period_type") not in {"FY", "H1", "H2", "Q"}:
                    err(f"{where}: bad period_type {s.get('period_type')!r}")
                pts = s.get("points", [])
                if len(pts) < 8:
                    warn(f"{where}: only {len(pts)} points (plan asks for 8+ where the corpus allows)")
                for pt in pts:
                    pw = f"{where} {pt.get('period')}"
                    check_period(pw, pt.get("period", ""))
                    check_citation(pw, pt.get("source", ""), pt.get("quote", ""), pt.get("value"))

        if p := need("ranges.json"):
            data = json.loads(p.read_text())
            for r in data.get("ranges", []):
                where = f"{cid}/ranges {r.get('metric_id')}"
                check_common(where, r, metrics)
                lo, base, hi = r.get("low"), r.get("base"), r.get("high")
                if None in (lo, base, hi) or not (lo <= base <= hi):
                    err(f"{where}: need low <= base <= high, got {lo}/{base}/{hi}")
                if not r.get("methods"):
                    warn(f"{where}: no methods listed")
                for ev in r.get("evidence", []):
                    check_citation(f"{where} evidence", ev.get("source", ""), ev.get("quote", ""))
                ranges_by_id[r.get("metric_id")] = r
            missing = all_ids - set(ranges_by_id)
            if missing:
                err(f"{cid}/ranges.json: metrics missing entirely: {sorted(missing)}")

    if p := need("final.json"):
        data = json.loads(p.read_text())
        seen = set()
        for f in data.get("finals", []):
            where = f"{cid}/final {f.get('metric_id')}"
            check_common(where, f, metrics)
            seen.add(f.get("metric_id"))
            v = f.get("value")
            if not isinstance(v, (int, float)):
                err(f"{where}: value must be numeric, got {v!r}")
                continue
            if metrics.get(f.get("metric_id"), {}).get("unit") == "%" and abs(v) > 50:
                warn(f"{where}: {v} looks implausible for a percentage-point metric")
            tier = f.get("fallback_tier")
            if tier not in (0, 1, 2, 3, 4):
                err(f"{where}: fallback_tier must be 0-4, got {tier!r}")
            if f.get("anchor_kind") is None:
                err(f"{where}: missing anchor_kind")
            r = ranges_by_id.get(f.get("metric_id"))
            if r and not (r["low"] <= v <= r["high"]):
                err(f"{where}: value {v} outside guardrail range [{r['low']}, {r['high']}]")
            if abs(f.get("delta") or 0) > 0 and not f.get("delta_evidence"):
                err(f"{where}: non-zero delta with no delta_evidence")
            for ev in f.get("delta_evidence", []):
                check_citation(f"{where} delta_evidence", ev.get("source", ""), ev.get("quote", ""))
        missing = all_ids - seen
        if missing:
            err(f"{cid}/final.json: metrics missing entirely: {sorted(missing)} — NEVER leave a metric blank")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixtures", action="store_true", help="validate fixtures/<company> instead of out/<company>")
    ap.add_argument("--company", action="append", help="company_id (repeatable); default: all present")
    ap.add_argument("--final-only", action="store_true", help="only validate final.json (stub companies)")
    args = ap.parse_args()

    manifest = load_manifest()
    base = REPO / ("fixtures" if args.fixtures else "out")
    cids = args.company or [c for c in manifest if (base / c).exists()]
    if not cids:
        print(f"nothing to validate under {base}/ — run the pipeline or pass --company")
        return 1

    for cid in cids:
        if cid not in manifest:
            err(f"unknown company_id {cid!r} (manifest has {sorted(manifest)})")
            continue
        if not (base / cid).exists():
            err(f"{base.name}/{cid} does not exist")
            continue
        validate_company(base / cid, cid, manifest, final_only=args.final_only)

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{base.name}: {len(cids)} company(ies), {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
