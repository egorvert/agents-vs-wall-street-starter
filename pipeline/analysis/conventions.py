"""Validated metric definitions shared by analysis and combine."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.analysis.evidence import EvidenceError, validate_citation


CONVENTIONS_PATH = Path(__file__).resolve().parent / "conventions.json"


def load_conventions(
    repo_root: Path,
    manifest: dict[str, Any],
    cutoff: date,
) -> dict[str, dict[str, Any]]:
    payload = json.loads(CONVENTIONS_PATH.read_text(encoding="utf-8"))
    conventions = payload.get("metrics")
    expected = {
        metric["metric_id"]
        for company in manifest["companies"].values()
        for metric in company["metrics"]
    }
    if payload.get("schema_version") != 1 or not isinstance(conventions, dict):
        raise EvidenceError("conventions.json is not schema version 1")
    if set(conventions) != expected:
        raise EvidenceError("conventions.json must cover the metric manifest exactly")
    for metric_id, convention in conventions.items():
        if not isinstance(convention.get("definition"), str):
            raise EvidenceError(f"{metric_id}: convention definition must be text")
        validate_citation(
            repo_root,
            convention.get("citation"),
            cutoff=cutoff,
            where=f"{metric_id} convention",
        )
    return conventions
