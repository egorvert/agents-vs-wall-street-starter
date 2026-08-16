"""Generate Contract B/C analysis artifacts and validate facts through Rachel's extractor."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

from pipeline.analysis.evidence import (
    EvidenceError,
    EvidenceItem,
    build_evidence_catalog,
    evidence_map,
    parse_iso_date,
    select_evidence,
)
from pipeline.analysis.model_client import (
    DEFAULT_MODEL,
    EventLogger,
    OpenAIResponsesClient,
    StructuredModelClient,
    emit_event,
    json_event_logger,
)
from pipeline.quant.extract_timeseries import ExtractionError, build_timeseries


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
DIRECTIONS = ("up", "down", "neutral", "unknown")
DIRECTION_SYMBOLS = {"up": "↑", "down": "↓", "neutral": "neutral", "unknown": "unknown"}
KINDS = ("consensus", "guidance_midpoint")


class AnalysisError(ValueError):
    """Raised when a generated analysis product violates its handoff contract."""


def _load_manifest(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / "schemas" / "metrics.json").read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("companies"), dict):
        raise AnalysisError("schemas/metrics.json is not schema version 1")
    return payload


def _load_cutoff(repo_root: Path) -> date:
    snapshot = json.loads(
        (repo_root / "challenge" / "live-data" / "snapshot.json").read_text(encoding="utf-8")
    )
    value = snapshot.get("snapshotCutoffAt")
    if not isinstance(value, str):
        raise AnalysisError("live-data snapshot is missing snapshotCutoffAt")
    return date.fromisoformat(value[:10])


def _prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def _object_schema(properties: dict[str, Any], required: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


def _schemas(metric_ids: list[str]) -> dict[str, dict[str, Any]]:
    evidence_ids = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    direction = {"type": "string", "enum": list(DIRECTIONS)}
    metric_id = {"type": "string", "enum": metric_ids}
    return {
        "context": _object_schema(
            {
                "summary": {"type": "string"},
                "metric_outlooks": {
                    "type": "array",
                    "items": _object_schema(
                        {
                            "metric_id": metric_id,
                            "direction": direction,
                            "bottom_line": {"type": "string"},
                            "evidence_ids": evidence_ids,
                        },
                        ("metric_id", "direction", "bottom_line", "evidence_ids"),
                    ),
                    "minItems": len(metric_ids),
                    "maxItems": len(metric_ids),
                },
                "risks": {
                    "type": "array",
                    "items": _object_schema(
                        {"claim": {"type": "string"}, "evidence_ids": evidence_ids},
                        ("claim", "evidence_ids"),
                    ),
                },
            },
            ("summary", "metric_outlooks", "risks"),
        ),
        "facts": _object_schema(
            {
                "facts": {
                    "type": "array",
                    "items": _object_schema(
                        {
                            "metric_id": metric_id,
                            "period": {"type": "string"},
                            "value": {"type": "number"},
                            "evidence_id": {"type": "string"},
                            "commentary": {"type": "string"},
                        },
                        ("metric_id", "period", "value", "evidence_id", "commentary"),
                    ),
                    "minItems": 1,
                }
            },
            ("facts",),
        ),
        "news": _object_schema(
            {
                "items": {
                    "type": "array",
                    "items": _object_schema(
                        {
                            "headline": {"type": "string"},
                            "summary": {"type": "string"},
                            "evidence_ids": evidence_ids,
                            "impacts": {
                                "type": "array",
                                "items": _object_schema(
                                    {"metric_id": metric_id, "direction": direction},
                                    ("metric_id", "direction"),
                                ),
                                "minItems": len(metric_ids),
                                "maxItems": len(metric_ids),
                            },
                        },
                        ("headline", "summary", "evidence_ids", "impacts"),
                    ),
                }
            },
            ("items",),
        ),
        "consensus": _object_schema(
            {
                "anchors": {
                    "type": "array",
                    "items": _object_schema(
                        {
                            "metric_id": metric_id,
                            "kind": {"type": "string", "enum": list(KINDS)},
                            "value": {"type": "number"},
                            "evidence_id": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        ("metric_id", "kind", "value", "evidence_id", "note"),
                    ),
                }
            },
            ("anchors",),
        ),
    }


def _terms(company: dict[str, Any]) -> set[str]:
    terms = set(re.findall(r"[a-z0-9]+", company["company"].casefold()))
    for metric in company["metrics"]:
        terms.update(re.findall(r"[a-z0-9]+", metric["label"].casefold()))
        terms.update(metric["metric_id"].split("_"))
    return terms


def _merge_evidence(*groups: Sequence[EvidenceItem], limit: int) -> tuple[EvidenceItem, ...]:
    merged = {}
    for group in groups:
        for item in group:
            merged.setdefault(item.evidence_id, item)
    return tuple(list(merged.values())[:limit])


def _prompt_payload(
    *,
    company_id: str,
    company: dict[str, Any],
    cutoff: date,
    evidence: Sequence[EvidenceItem],
) -> str:
    return json.dumps(
        {
            "company_id": company_id,
            "company": company["company"],
            "target_period": company["period"],
            "cutoff": cutoff.isoformat(),
            "metrics": company["metrics"],
            "evidence": [item.prompt_record() for item in evidence],
        },
        indent=2,
        ensure_ascii=False,
    )


def _require_metric_coverage(rows: list[dict], metric_ids: list[str], where: str) -> None:
    actual = [row.get("metric_id") for row in rows]
    if len(actual) != len(set(actual)):
        raise AnalysisError(f"{where}: duplicate metric_id")
    if set(actual) != set(metric_ids):
        raise AnalysisError(f"{where}: expected exactly metrics {metric_ids}, got {actual}")


def _resolve_ids(
    ids: object,
    available: dict[str, EvidenceItem],
    *,
    cutoff: date,
    where: str,
) -> tuple[EvidenceItem, ...]:
    if not isinstance(ids, list) or not ids:
        raise AnalysisError(f"{where}: evidence_ids must be a non-empty list")
    resolved = []
    seen = set()
    for evidence_id in ids:
        if not isinstance(evidence_id, str) or evidence_id not in available:
            raise AnalysisError(f"{where}: unknown evidence_id {evidence_id!r}")
        item = available[evidence_id]
        if not item.published_at:
            raise AnalysisError(f"{where}: evidence {evidence_id} has no publication date")
        if parse_iso_date(item.published_at, where) > cutoff:
            raise AnalysisError(f"{where}: evidence {evidence_id} is after cutoff")
        if evidence_id not in seen:
            resolved.append(item)
            seen.add(evidence_id)
    return tuple(resolved)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _citation_lines(items: Sequence[EvidenceItem], indent: str = "  ") -> list[str]:
    lines = []
    for item in items:
        lines.append(
            f'{indent}- Evidence `{item.source}` ({item.published_at}): "{item.quote.strip()}"'
        )
    return lines


def _render_context(
    data: dict[str, Any],
    *,
    company: dict[str, Any],
    available: dict[str, EvidenceItem],
    cutoff: date,
) -> str:
    rows = data.get("metric_outlooks")
    if not isinstance(rows, list):
        raise AnalysisError("context.metric_outlooks must be a list")
    metric_ids = [metric["metric_id"] for metric in company["metrics"]]
    _require_metric_coverage(rows, metric_ids, "context.metric_outlooks")
    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise AnalysisError("context.summary must be non-empty")
    lines = [f"# {company['company']} — context", "", summary.strip(), "", "## Metric outlook"]
    for index, row in enumerate(rows, 1):
        direction = row.get("direction")
        bottom_line = row.get("bottom_line")
        if direction not in DIRECTIONS or not isinstance(bottom_line, str) or not bottom_line.strip():
            raise AnalysisError(f"context outlook {index}: invalid direction or bottom_line")
        evidence = _resolve_ids(
            row.get("evidence_ids"), available, cutoff=cutoff, where=f"context outlook {index}"
        )
        lines.extend(
            ["", f"- `{row['metric_id']}` {DIRECTION_SYMBOLS[direction]} — {bottom_line.strip()}"]
        )
        lines.extend(_citation_lines(evidence))
    risks = data.get("risks")
    if not isinstance(risks, list):
        raise AnalysisError("context.risks must be a list")
    if risks:
        lines.extend(["", "## Risks and counterevidence"])
    for index, risk in enumerate(risks, 1):
        if not isinstance(risk, dict) or not isinstance(risk.get("claim"), str):
            raise AnalysisError(f"context risk {index}: invalid claim")
        evidence = _resolve_ids(
            risk.get("evidence_ids"), available, cutoff=cutoff, where=f"context risk {index}"
        )
        lines.extend(["", f"- {risk['claim'].strip()}"])
        lines.extend(_citation_lines(evidence))
    rendered = "\n".join(lines).rstrip() + "\n"
    if _word_count(rendered) > 600:
        raise AnalysisError(f"context.md exceeds 600 words ({_word_count(rendered)})")
    return rendered


def _render_facts(
    data: dict[str, Any],
    *,
    company: dict[str, Any],
    available: dict[str, EvidenceItem],
    cutoff: date,
) -> str:
    rows = data.get("facts")
    if not isinstance(rows, list) or not rows:
        raise AnalysisError("facts.facts must be a non-empty list")
    metrics = {metric["metric_id"]: metric for metric in company["metrics"]}
    records = []
    prose = [f"# {company['company']} — curated facts", ""]
    seen = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise AnalysisError(f"fact {index}: expected object")
        metric_id = row.get("metric_id")
        period = row.get("period")
        value = row.get("value")
        evidence_id = row.get("evidence_id")
        if metric_id not in metrics:
            raise AnalysisError(f"fact {index}: unknown metric_id {metric_id!r}")
        if not isinstance(period, str) or not re.fullmatch(r"FY\d{4}(?:Q[1-4]|H[12])?", period):
            raise AnalysisError(f"fact {index}: non-canonical period {period!r}")
        if period == company["period"]:
            raise AnalysisError(f"fact {index}: target-period actuals are held out")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise AnalysisError(f"fact {index}: value must be finite")
        identity = (metric_id, period)
        if identity in seen:
            raise AnalysisError(f"fact {index}: duplicate metric/period {identity}")
        seen.add(identity)
        evidence = _resolve_ids(
            [evidence_id], available, cutoff=cutoff, where=f"fact {index}"
        )[0]
        metric = metrics[metric_id]
        record = {
            "metric_id": metric_id,
            "period": period,
            "value": value,
            "unit": metric["unit"],
            "basis": metric["basis"],
            "source": evidence.source,
            "published_at": evidence.published_at,
            "quote": evidence.quote,
        }
        records.append(record)
        prose.extend(
            [
                f"- `{metric_id}` `{period}`: {value} {metric['unit']} ({metric['basis']}).",
                f'  Evidence `{evidence.source}` ({evidence.published_at}): "{evidence.quote.strip()}"',
            ]
        )
    prose.extend(["", "## Fact block", "", "```jsonl"])
    prose.extend(json.dumps(record, ensure_ascii=False, sort_keys=False) for record in records)
    prose.extend(["```", ""])
    return "\n".join(prose)


def _render_news(
    data: dict[str, Any],
    *,
    company: dict[str, Any],
    available: dict[str, EvidenceItem],
    cutoff: date,
) -> str:
    rows = data.get("items")
    if not isinstance(rows, list):
        raise AnalysisError("news.items must be a list")
    metric_ids = [metric["metric_id"] for metric in company["metrics"]]
    materialized = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise AnalysisError(f"news item {index}: expected object")
        headline, summary = row.get("headline"), row.get("summary")
        if not isinstance(headline, str) or not headline.strip() or not isinstance(summary, str):
            raise AnalysisError(f"news item {index}: invalid headline or summary")
        evidence = _resolve_ids(
            row.get("evidence_ids"), available, cutoff=cutoff, where=f"news item {index}"
        )
        impacts = row.get("impacts")
        if not isinstance(impacts, list):
            raise AnalysisError(f"news item {index}: impacts must be a list")
        _require_metric_coverage(impacts, metric_ids, f"news item {index} impacts")
        for impact in impacts:
            if impact.get("direction") not in DIRECTIONS:
                raise AnalysisError(f"news item {index}: invalid direction")
        published_at = max(item.published_at for item in evidence)
        materialized.append((published_at, headline.strip(), summary.strip(), evidence, impacts))
    materialized.sort(key=lambda item: (item[0], item[1]), reverse=True)
    lines = [f"# {company['company']} — news since the last filing"]
    for published_at, headline, summary, evidence, impacts in materialized:
        lines.extend(["", f"## {published_at} — {headline}", "", summary])
        lines.extend(_citation_lines(evidence, indent=""))
        lines.append("")
        for impact in impacts:
            lines.append(
                f"- `{impact['metric_id']}`: {DIRECTION_SYMBOLS[impact['direction']]}"
            )
    rendered = "\n".join(lines).rstrip() + "\n"
    if _word_count(rendered) > 600:
        raise AnalysisError(f"news.md exceeds 600 words ({_word_count(rendered)})")
    return rendered


def _render_consensus(
    data: dict[str, Any],
    *,
    company_id: str,
    company: dict[str, Any],
    available: dict[str, EvidenceItem],
    cutoff: date,
    retrieved_at: datetime,
) -> dict[str, Any]:
    rows = data.get("anchors")
    if not isinstance(rows, list):
        raise AnalysisError("consensus.anchors must be a list")
    metrics = {metric["metric_id"]: metric for metric in company["metrics"]}
    anchors = []
    seen = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise AnalysisError(f"anchor {index}: expected object")
        metric_id, kind, value = row.get("metric_id"), row.get("kind"), row.get("value")
        identity = (metric_id, kind)
        if metric_id not in metrics or kind not in KINDS:
            raise AnalysisError(f"anchor {index}: invalid metric or kind")
        if identity in seen:
            raise AnalysisError(f"anchor {index}: duplicate {identity}")
        seen.add(identity)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise AnalysisError(f"anchor {index}: value must be finite")
        evidence = _resolve_ids(
            [row.get("evidence_id")], available, cutoff=cutoff, where=f"anchor {index}"
        )[0]
        note = row.get("note")
        if not isinstance(note, str):
            raise AnalysisError(f"anchor {index}: note must be a string")
        metric = metrics[metric_id]
        anchors.append(
            {
                "metric_id": metric_id,
                "kind": kind,
                "value": value,
                "unit": metric["unit"],
                "basis": metric["basis"],
                "source": evidence.source,
                "published_at": evidence.published_at,
                "quote": evidence.quote,
                "note": note.strip(),
            }
        )
    anchors.sort(key=lambda row: (row["metric_id"], row["kind"]))
    return {
        "schema_version": 1,
        "company_id": company_id,
        "retrieved_at": retrieved_at.isoformat(),
        "anchors": anchors,
    }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def run_analysis(
    company_id: str,
    repo_root: Path,
    out_root: Path,
    client: StructuredModelClient,
    run_started_at: datetime,
    logger: EventLogger | None = json_event_logger,
) -> None:
    """Generate and atomically publish one company's Contract B/C artifacts."""
    repo_root = Path(repo_root).resolve()
    out_root = Path(out_root).resolve()
    if run_started_at.tzinfo is None:
        raise AnalysisError("run_started_at must be timezone-aware")
    manifest = _load_manifest(repo_root)
    companies = manifest["companies"]
    if company_id not in companies:
        raise AnalysisError(f"unknown company_id {company_id!r}")
    company = companies[company_id]
    cutoff = _load_cutoff(repo_root)
    dossier_path = out_root / company_id / "research" / "dossier.md"
    if not dossier_path.is_file():
        raise AnalysisError(f"research dossier does not exist: {dossier_path}")

    catalog = build_evidence_catalog(
        repo_root=repo_root,
        company_id=company_id,
        dossier_path=dossier_path,
        cutoff=cutoff,
    )
    if not catalog:
        raise AnalysisError(f"{company_id}: no admissible evidence found")
    catalog_by_id = evidence_map(catalog)
    base_terms = _terms(company)
    live_evidence = tuple(item for item in catalog if "challenge/live-data/" in item.source)
    numeric_live_evidence = tuple(item for item in live_evidence if re.search(r"\d", item.quote))
    facts_evidence = _merge_evidence(
        numeric_live_evidence,
        select_evidence(
            catalog,
            terms=base_terms | {"reported", "revenue", "sales", "profit", "earnings", "margin"},
            limit=80,
            require_number=True,
        ),
        limit=100,
    )
    context_evidence = select_evidence(
        catalog,
        terms=base_terms | {"industry", "demand", "market", "peer", "risk", "macro"},
        limit=45,
    )
    news_evidence = select_evidence(
        live_evidence,
        terms=base_terms | {"guidance", "news", "data", "market", "outlook"},
        limit=40,
    )
    consensus_evidence = _merge_evidence(
        numeric_live_evidence,
        select_evidence(
            catalog,
            terms=base_terms | {"consensus", "guidance", "estimate", "range", "midpoint"},
            limit=60,
            require_number=True,
        ),
        limit=80,
    )
    selections = {
        "context": context_evidence,
        "facts": facts_evidence,
        "news": news_evidence,
        "consensus": consensus_evidence,
    }
    schemas = _schemas([metric["metric_id"] for metric in company["metrics"]])
    responses = {}
    for product in ("context", "facts", "news", "consensus"):
        result = client.generate_json(
            schema_name=f"avws_{product}_v1",
            instructions=_prompt(f"{product}.md"),
            input_text=_prompt_payload(
                company_id=company_id,
                company=company,
                cutoff=cutoff,
                evidence=selections[product],
            ),
            schema=schemas[product],
            metadata={"stage": "analysis", "product": product, "company_id": company_id},
        )
        responses[product] = result.data

    out_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{company_id}-analysis-", dir=out_root) as temp_name:
        temporary = Path(temp_name)
        analysis_dir = temporary / "analysis"
        context = _render_context(
            responses["context"], company=company, available=catalog_by_id, cutoff=cutoff
        )
        facts = _render_facts(
            responses["facts"], company=company, available=catalog_by_id, cutoff=cutoff
        )
        news = _render_news(
            responses["news"], company=company, available=catalog_by_id, cutoff=cutoff
        )
        consensus = _render_consensus(
            responses["consensus"],
            company_id=company_id,
            company=company,
            available=catalog_by_id,
            cutoff=cutoff,
            retrieved_at=run_started_at,
        )
        _write_text(analysis_dir / "context.md", context)
        _write_text(analysis_dir / "facts.md", facts)
        _write_text(analysis_dir / "news.md", news)
        _write_json(temporary / "consensus.json", consensus)

        extraction = build_timeseries(
            repo_root=repo_root,
            company_id=company_id,
            dossier_path=dossier_path,
            facts_path=analysis_dir / "facts.md",
            as_of=cutoff.isoformat(),
            target_period=company["period"],
        )
        for warning in extraction.warnings:
            emit_event(
                logger,
                "analysis_quant_warning",
                company_id=company_id,
                warning=warning,
            )

        destination = out_root / company_id
        destination_analysis = destination / "analysis"
        destination_analysis.mkdir(parents=True, exist_ok=True)
        for name in ("context.md", "facts.md", "news.md"):
            os.replace(analysis_dir / name, destination_analysis / name)
        destination.mkdir(parents=True, exist_ok=True)
        os.replace(temporary / "consensus.json", destination / "consensus.json")
    emit_event(logger, "analysis_published", company_id=company_id, output=str(out_root / company_id))


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--company", help="company_id from schemas/metrics.json")
    selection.add_argument("--all", action="store_true", help="generate all companies")
    parser.add_argument("--repo-root", default=str(repo_root))
    parser.add_argument("--out-root", default="out")
    parser.add_argument("--model", default=None)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    out = Path(args.out_root)
    if not out.is_absolute():
        out = root / out
    companies = _load_manifest(root)["companies"]
    company_ids = list(companies) if args.all else [args.company]
    client = OpenAIResponsesClient(
        model=args.model or DEFAULT_MODEL,
        cache_root=out / ".cache",
        use_cache=not args.no_cache,
        logger=json_event_logger,
    )
    started = datetime.now().astimezone()
    failures = []
    for company_id in company_ids:
        try:
            run_analysis(company_id, root, out, client, started, json_event_logger)
        except (AnalysisError, EvidenceError, ExtractionError, OSError, json.JSONDecodeError) as exc:
            failures.append(company_id)
            emit_event(json_event_logger, "analysis_failed", company_id=company_id, error=str(exc))
    if failures:
        print(f"ERROR: analysis failed for {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
