#!/usr/bin/env python3
"""Materialize deterministic Contract E ranges from Contract C and Contract D."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.quant.guardrails import GuardrailError, build_ranges_document


def _load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GuardrailError(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GuardrailError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise GuardrailError(f"{label} must contain a JSON object")
    return value


def write_ranges(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _repo_path(repo_root: Path, value: str | None, default: Path) -> Path:
    if value is None:
        return default
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def main(argv: Sequence[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", required=True, help="company_id from schemas/metrics.json")
    parser.add_argument("--as-of", required=True, help="point-in-time cutoff, YYYY-MM-DD")
    parser.add_argument("--target-period", help="forecast fiscal period; defaults to the manifest target")
    parser.add_argument("--repo-root", default=str(default_repo))
    parser.add_argument("--timeseries", help="Contract D path, relative to repo root")
    parser.add_argument("--consensus", help="Contract C path, relative to repo root")
    parser.add_argument("--output", help="Contract E path, relative to repo root")
    args = parser.parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()
        manifest = _load_json(repo_root / "schemas" / "metrics.json", "metric manifest")
        companies = manifest.get("companies", {})
        if args.company not in companies:
            raise GuardrailError(f"unknown company_id {args.company!r}")
        company = companies[args.company]
        root = repo_root / "out" / args.company
        timeseries_path = _repo_path(repo_root, args.timeseries, root / "timeseries.json")
        consensus_path = _repo_path(repo_root, args.consensus, root / "consensus.json")
        output_path = _repo_path(repo_root, args.output, root / "ranges.json")
        timeseries = _load_json(timeseries_path, "timeseries")
        consensus = _load_json(consensus_path, "consensus")
        if timeseries.get("company_id") != args.company:
            raise GuardrailError(
                f"timeseries company_id {timeseries.get('company_id')!r} != {args.company!r}"
            )
        document = build_ranges_document(
            timeseries,
            consensus,
            target_period=args.target_period or company["period"],
            as_of=args.as_of,
        )
        write_ranges(output_path, document)
    except (GuardrailError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {output_path}")
    for item in document["ranges"]:
        print(
            f"{item['metric_id']}: [{item['low']:.6g}, {item['base']:.6g}, "
            f"{item['high']:.6g}] via {', '.join(item['methods'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
