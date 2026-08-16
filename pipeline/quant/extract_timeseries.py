#!/usr/bin/env python3
"""Build Contract D time series from cited JSONL fact blocks.

The extractor deliberately does not scrape prose. It accepts only facts that satisfy
the repository's metric, period, unit, basis, date, and citation contracts, then
merges the dossier with the curated analysis facts deterministically.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence


FACT_FIELDS = frozenset(
    {"metric_id", "period", "value", "unit", "basis", "source", "published_at", "quote"}
)
FACT_BLOCK_RE = re.compile(r"```jsonl[ \t]*\r?\n(.*?)```", re.DOTALL)
PERIOD_RE = re.compile(r"^FY\d{4}(?:(Q)([1-4])|(H)([12]))?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NUMBER_RE = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
PERIOD_TYPE_ORDER = {"FY": 0, "H1": 1, "H2": 2, "Q": 3}


class ExtractionError(ValueError):
    """Raised when an input cannot safely enter the quantitative time series."""


@dataclass(frozen=True)
class Fact:
    metric_id: str
    period: str
    value: int | float
    unit: str
    basis: str
    source: str
    published_at: str
    quote: str
    period_type: str
    origin: str
    priority: int
    line_number: int

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.metric_id, self.period_type, self.period)

    @property
    def preference(self) -> tuple[int, str, str, str, str, int]:
        """Choose duplicate citations deterministically; curated facts rank first."""
        return (
            self.priority,
            self.published_at,
            self.source,
            self.quote,
            self.origin,
            self.line_number,
        )

    def as_point(self) -> dict:
        return {
            "period": self.period,
            "value": self.value,
            "source": self.source,
            "published_at": self.published_at,
            "quote": self.quote,
        }


@dataclass(frozen=True)
class ExtractionResult:
    document: dict
    warnings: tuple[str, ...]


def _normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("*", "")).strip()


def canonical_period_type(period: str, where: str = "period") -> str:
    match = PERIOD_RE.fullmatch(period)
    if not match:
        raise ExtractionError(
            f"{where}: non-canonical period {period!r}; expected FY2026, FY2026Q2, or FY2026H1"
        )
    if match.group(1) == "Q":
        return "Q"
    if match.group(3) == "H":
        return f"H{match.group(4)}"
    return "FY"


def _parse_date(value: object, where: str) -> date:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ExtractionError(f"{where}: published_at must be an ISO YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ExtractionError(f"{where}: invalid published_at date {value!r}") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _citation_path(repo_root: Path, source: object, where: str) -> Path:
    if not isinstance(source, str) or not source.strip():
        raise ExtractionError(f"{where}: source must be a non-empty repository-relative path")
    if source.startswith(("http://", "https://")):
        raise ExtractionError(
            f"{where}: URL sources are not admissible; save the evidence as a dated repository note"
        )
    relative = Path(source)
    if relative.is_absolute():
        raise ExtractionError(f"{where}: source must be repository-relative, got {source!r}")
    root = repo_root.resolve()
    resolved = (root / relative).resolve()
    if not _is_within(resolved, root):
        raise ExtractionError(f"{where}: source escapes the repository: {source!r}")
    if not resolved.is_file():
        raise ExtractionError(f"{where}: cited source file does not exist: {source}")
    return resolved


def _numbers_in(text: str) -> list[float]:
    return [abs(float(match.group(0).replace(",", ""))) for match in NUMBER_RE.finditer(text)]


def _granularity(value: int | float) -> float:
    """Rounding granularity implied by a value's decimal representation:
    39900 -> 100 (two trailing zeros), 192.1 -> 0.1, 197 -> 1, 3160.263 -> 0.001."""
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    if "." in text:
        return 10.0 ** -len(text.split(".")[1])
    stripped = text.rstrip("0")
    return float(10 ** (len(text) - len(stripped))) if stripped else 1.0


def _close_enough(candidate: float, expected: float) -> bool:
    tolerance = max(0.005, expected * 0.001)
    return math.isclose(candidate, expected, rel_tol=0.0, abs_tol=tolerance)


def _value_is_recognisable(value: int | float, unit: str, quote: str) -> bool:
    expected = abs(float(value))
    numbers = _numbers_in(quote)
    if any(_close_enough(number, expected) for number in numbers):
        return True

    quote_lower = quote.lower()
    is_millions_unit = unit in {"USDm", "GBPm"}
    quotes_billions = bool(re.search(r"\b(?:billion|bn)\b", quote_lower))
    if is_millions_unit and quotes_billions:
        return any(_close_enough(number * 1000.0, expected) for number in numbers)
    if is_millions_unit:
        # 10-Q/10-K statement tables are commonly denominated in thousands:
        # "$ 3,160,263" supports a fact of 3160.263 USDm. Only accept the
        # thousands reading for large quote numbers, so plain small figures
        # can never alias into it.
        return any(
            number >= 100_000 and _close_enough(number / 1000.0, expected)
            for number in numbers
        )
    return False


def _validate_citation(
    repo_root: Path,
    fact: dict,
    where: str,
    source_cache: dict[Path, str],
) -> None:
    quote = fact["quote"]
    if not isinstance(quote, str) or not quote.strip():
        raise ExtractionError(f"{where}: quote must be a non-empty string")
    source_path = _citation_path(repo_root, fact["source"], where)
    if source_path not in source_cache:
        source_cache[source_path] = _normalise_text(
            source_path.read_text(encoding="utf-8", errors="replace")
        )
    if _normalise_text(quote) not in source_cache[source_path]:
        raise ExtractionError(f"{where}: quote is not present in cited source {fact['source']}")
    if not _value_is_recognisable(fact["value"], fact["unit"], quote):
        raise ExtractionError(f"{where}: value {fact['value']} is not recognisable in its quote")


def _validate_fact(
    raw: object,
    *,
    where: str,
    repo_root: Path,
    metrics: dict[str, dict],
    origin: str,
    priority: int,
    line_number: int,
    source_cache: dict[Path, str],
) -> Fact:
    if not isinstance(raw, dict):
        raise ExtractionError(f"{where}: each fact line must decode to a JSON object")
    fields = set(raw)
    if fields != FACT_FIELDS:
        missing = sorted(FACT_FIELDS - fields)
        extra = sorted(fields - FACT_FIELDS)
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"extra {extra}")
        raise ExtractionError(f"{where}: fact fields do not match the closed contract ({'; '.join(details)})")

    metric_id = raw["metric_id"]
    if not isinstance(metric_id, str) or metric_id not in metrics:
        raise ExtractionError(f"{where}: unknown metric_id {metric_id!r} for this company")
    metric = metrics[metric_id]

    value = raw["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ExtractionError(f"{where}: value must be a finite JSON number, got {value!r}")
    if raw["unit"] != metric["unit"]:
        raise ExtractionError(
            f"{where}: unit {raw['unit']!r} does not match manifest {metric['unit']!r}"
        )
    if raw["basis"] != metric["basis"]:
        raise ExtractionError(
            f"{where}: basis {raw['basis']!r} does not match manifest {metric['basis']!r}"
        )
    if not isinstance(raw["period"], str):
        raise ExtractionError(f"{where}: period must be a canonical string")
    period_type = canonical_period_type(raw["period"], where)
    _parse_date(raw["published_at"], where)
    _validate_citation(repo_root, raw, where, source_cache)

    return Fact(
        metric_id=metric_id,
        period=raw["period"],
        value=value,
        unit=raw["unit"],
        basis=raw["basis"],
        source=raw["source"],
        published_at=raw["published_at"],
        quote=raw["quote"],
        period_type=period_type,
        origin=origin,
        priority=priority,
        line_number=line_number,
    )


def parse_fact_block(
    path: Path,
    *,
    repo_root: Path,
    metrics: dict[str, dict],
    priority: int,
    source_cache: dict[Path, str] | None = None,
) -> list[Fact]:
    """Parse and validate exactly one JSONL fact block from a Markdown file."""
    path = Path(path)
    if not path.is_file():
        raise ExtractionError(f"fact-block input does not exist: {path}")
    blocks = FACT_BLOCK_RE.findall(path.read_text(encoding="utf-8", errors="replace"))
    if len(blocks) != 1:
        raise ExtractionError(f"{path}: expected exactly one ```jsonl fact block, found {len(blocks)}")

    lines = [line.strip() for line in blocks[0].splitlines() if line.strip()]
    if not lines:
        raise ExtractionError(f"{path}: fact block is empty")

    cache = source_cache if source_cache is not None else {}
    facts = []
    for line_number, line in enumerate(lines, 1):
        where = f"{path} fact {line_number}"
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"{where}: invalid JSON ({exc.msg})") from exc
        facts.append(
            _validate_fact(
                raw,
                where=where,
                repo_root=repo_root,
                metrics=metrics,
                origin=str(path),
                priority=priority,
                line_number=line_number,
                source_cache=cache,
            )
        )
    return facts


def _load_company(repo_root: Path, company_id: str) -> dict:
    manifest_path = repo_root / "schemas" / "metrics.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExtractionError(f"metric manifest does not exist: {manifest_path}") from exc
    companies = manifest.get("companies", {})
    if company_id not in companies:
        raise ExtractionError(f"unknown company_id {company_id!r}")
    return companies[company_id]


def build_timeseries(
    *,
    repo_root: Path,
    company_id: str,
    dossier_path: Path,
    facts_path: Path,
    as_of: str,
    target_period: str,
) -> ExtractionResult:
    """Validate, filter, merge, and materialize a Contract D document."""
    repo_root = Path(repo_root).resolve()
    company = _load_company(repo_root, company_id)
    metrics = {metric["metric_id"]: metric for metric in company["metrics"]}
    cutoff = _parse_date(as_of, "extractor cutoff")
    target_period_type = canonical_period_type(target_period, "extractor target")
    expected_period_type = company.get("period_type")
    if expected_period_type and target_period_type != expected_period_type:
        raise ExtractionError(
            f"extractor target: period type {target_period_type!r} does not match "
            f"company target type {expected_period_type!r}"
        )

    source_cache: dict[Path, str] = {}
    dossier_facts = parse_fact_block(
        dossier_path,
        repo_root=repo_root,
        metrics=metrics,
        priority=0,
        source_cache=source_cache,
    )
    curated_facts = parse_fact_block(
        facts_path,
        repo_root=repo_root,
        metrics=metrics,
        priority=1,
        source_cache=source_cache,
    )

    warnings: list[str] = []
    labels = {metric["metric_id"]: metric.get("label", "") for metric in company["metrics"]}
    admitted: dict[tuple[str, str, str], Fact] = {}
    for fact in dossier_facts + curated_facts:
        fact_date = date.fromisoformat(fact.published_at)
        label = f"{fact.origin} fact {fact.line_number} ({fact.metric_id}/{fact.period})"
        if fact_date > cutoff:
            warnings.append(f"excluded post-cutoff {label}: {fact.published_at} > {as_of}")
            continue
        if fact.period == target_period:
            warnings.append(f"excluded held-out target {label}")
            continue

        previous = admitted.get(fact.identity)
        if previous is None:
            admitted[fact.identity] = fact
            continue
        if fact.value != previous.value:
            # Rounding-aware agreement: tolerate a gap up to half the coarser
            # source's rounding granularity ("$39.9 billion" prose vs the exact
            # 39,856 table are the same figure). Keep the more precise value.
            # granularity capped at 1% of the value: "39.9 billion" prose rounds
            # at 100M, but a round 1,200 does not imply +/-50 of slack
            tolerance = max(
                min(_granularity(v), abs(float(v)) * 0.01)
                for v in (previous.value, fact.value)
            ) / 2.0
            if abs(fact.value - previous.value) <= tolerance:
                more_precise = min(
                    (previous, fact), key=lambda f: _granularity(f.value)
                )
                warnings.append(
                    f"rounding variance {fact.metric_id}/{fact.period}: {previous.value} vs "
                    f"{fact.value} — kept {more_precise.value}"
                )
                admitted[fact.identity] = more_precise
                continue
            # True conflict. If exactly one quote states the metric's own label
            # verbatim, prefer it — the other is usually a near-miss line item
            # (e.g. "earnings from operations" vs "pre-exceptional operating
            # profit"). Otherwise refuse loudly.
            label = labels.get(fact.metric_id, "")
            prev_has = label.casefold() in previous.quote.casefold() if label else False
            fact_has = label.casefold() in fact.quote.casefold() if label else False
            if prev_has != fact_has:
                keep = previous if prev_has else fact
                drop = fact if prev_has else previous
                warnings.append(
                    f"label-preference {fact.metric_id}/{fact.period}: kept {keep.value} "
                    f"(quote states '{label}') over {drop.value} ({drop.source})"
                )
                admitted[fact.identity] = keep
                continue
            raise ExtractionError(
                "conflicting facts for "
                f"{fact.metric_id}/{fact.period}: {previous.value} ({previous.source}) vs "
                f"{fact.value} ({fact.source})"
            )
        if fact.preference > previous.preference:
            admitted[fact.identity] = fact

    grouped: dict[tuple[str, str], list[Fact]] = {}
    for fact in admitted.values():
        grouped.setdefault((fact.metric_id, fact.period_type), []).append(fact)

    series = []
    for metric in company["metrics"]:
        metric_id = metric["metric_id"]
        period_types = sorted(
            (period_type for mid, period_type in grouped if mid == metric_id),
            key=PERIOD_TYPE_ORDER.__getitem__,
        )
        if not period_types:
            raise ExtractionError(
                f"{company_id}/{metric_id}: no admissible observations remain after point-in-time filtering"
            )
        for period_type in period_types:
            points = sorted(grouped[(metric_id, period_type)], key=lambda fact: fact.period)
            if len(points) < 8:
                warnings.append(
                    f"{company_id}/{metric_id}/{period_type}: only {len(points)} comparable points "
                    "(the plan asks for 8+ where the corpus allows)"
                )
            series.append(
                {
                    "metric_id": metric_id,
                    "unit": metric["unit"],
                    "basis": metric["basis"],
                    "period_type": period_type,
                    "points": [fact.as_point() for fact in points],
                }
            )

    return ExtractionResult(
        document={"schema_version": 1, "company_id": company_id, "series": series},
        warnings=tuple(warnings),
    )


def write_timeseries(path: Path, document: dict) -> None:
    path = Path(path)
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
    parser.add_argument("--target-period", help="held-out/forecast period; defaults to the manifest target")
    parser.add_argument("--repo-root", default=str(default_repo))
    parser.add_argument("--dossier", help="dossier Markdown path, relative to repo root")
    parser.add_argument("--facts", help="curated facts Markdown path, relative to repo root")
    parser.add_argument("--output", help="Contract D output path, relative to repo root")
    args = parser.parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()
        company = _load_company(repo_root, args.company)
        input_root = repo_root / "out" / args.company
        dossier = _repo_path(repo_root, args.dossier, input_root / "research" / "dossier.md")
        facts = _repo_path(repo_root, args.facts, input_root / "analysis" / "facts.md")
        output = _repo_path(repo_root, args.output, input_root / "timeseries.json")
        result = build_timeseries(
            repo_root=repo_root,
            company_id=args.company,
            dossier_path=dossier,
            facts_path=facts,
            as_of=args.as_of,
            target_period=args.target_period or company["period"],
        )
        write_timeseries(output, result.document)
    except (ExtractionError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for warning in result.warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
