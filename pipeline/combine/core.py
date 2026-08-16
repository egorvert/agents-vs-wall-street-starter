"""Blind/reveal reconciliation and deterministic Contract F finalization."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence

from pipeline.analysis.conventions import load_conventions
from pipeline.analysis.evidence import (
    EvidenceItem,
    build_evidence_catalog,
    evidence_map,
    parse_iso_date,
    resolve_repo_source,
    select_evidence,
    validate_citation,
)
from pipeline.analysis.model_client import DEFAULT_MODEL, EventLogger, StructuredModelClient, emit_event
from pipeline.quant.guardrails import GuardrailError, anchor_bands, seasonal_naive_baselines


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
DIRECTIONS = ("up", "down", "neutral", "unknown")
CONFIDENCE = ("low", "medium", "high")
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


class CombineError(ValueError):
    pass


@dataclass(frozen=True)
class CombineConfig:
    # Rachel's HD smoke favored 75% B1; one global weight avoids fitting 12 noisy cases.
    model_delta_share: Decimal = Decimal("0.25")
    raw_delta_range_fraction: Decimal = Decimal("0.50")
    max_deviations_batch: int = 3
    max_deviations_single: int = 1
    model: str = DEFAULT_MODEL
    reasoning_effort: str = "low"
    prompt_version: str = "v1"

    def as_log_record(self) -> dict[str, Any]:
        return {
            "model_delta_share": str(self.model_delta_share),
            "raw_delta_range_fraction": str(self.raw_delta_range_fraction),
            "max_deviations_batch": self.max_deviations_batch,
            "max_deviations_single": self.max_deviations_single,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "prompt_version": self.prompt_version,
        }


@dataclass(frozen=True)
class CompanyInputs:
    company_id: str
    company: dict[str, Any]
    conventions: dict[str, dict[str, Any]]
    cutoff: date
    timeseries: dict[str, Any]
    ranges: dict[str, dict[str, Any]]
    anchors: tuple[dict[str, Any], ...]
    b0: dict[str, Any]
    context: str
    news: str
    evidence: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class MetricCandidate:
    company_id: str
    metric_id: str
    manifest_index: int
    unit: str
    basis: str
    anchor: Decimal
    anchor_kind: str
    low: Decimal
    base: Decimal
    high: Decimal
    blind_direction: str
    reveal_direction: str
    proposed_delta: Decimal
    confidence: str
    evidence: tuple[dict[str, str], ...]
    rationale: str
    eligible: bool
    rejection_reasons: tuple[str, ...]

    @property
    def range_width(self) -> Decimal:
        return self.high - self.low

    @property
    def normalized_delta(self) -> Decimal:
        if self.range_width == 0:
            return Decimal(0)
        return abs(self.proposed_delta) / self.range_width


@dataclass(frozen=True)
class FinalPayload:
    company_id: str
    finals: tuple[dict[str, Any], ...]

    def as_document(self) -> dict[str, Any]:
        return {"schema_version": 1, "company_id": self.company_id, "finals": list(self.finals)}


def _prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def _load_manifest(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / "schemas" / "metrics.json").read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise CombineError("schemas/metrics.json must be schema version 1")
    return payload


def _load_cutoff(repo_root: Path) -> date:
    snapshot = json.loads(
        (repo_root / "challenge" / "live-data" / "snapshot.json").read_text(encoding="utf-8")
    )
    value = snapshot.get("snapshotCutoffAt")
    if not isinstance(value, str):
        raise CombineError("live-data snapshot is missing snapshotCutoffAt")
    return date.fromisoformat(value[:10])


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise CombineError(f"{label} does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CombineError(f"{label} must contain a JSON object")
    return payload


def _finite_number(value: object, where: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CombineError(f"{where}: expected a finite JSON number")
    return Decimal(str(value))


def _validate_ranges(
    *,
    repo_root: Path,
    company_id: str,
    company: dict[str, Any],
    payload: dict[str, Any],
    cutoff: date,
) -> dict[str, dict[str, Any]]:
    if payload.get("schema_version") != 1 or payload.get("company_id") != company_id:
        raise CombineError(f"{company_id}: ranges schema_version/company_id mismatch")
    rows = payload.get("ranges")
    if not isinstance(rows, list):
        raise CombineError(f"{company_id}: ranges must be a list")
    metrics = {metric["metric_id"]: metric for metric in company["metrics"]}
    indexed = {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise CombineError(f"{company_id}: range {index} must be an object")
        metric_id = row.get("metric_id")
        if metric_id not in metrics or metric_id in indexed:
            raise CombineError(f"{company_id}: invalid or duplicate range metric {metric_id!r}")
        metric = metrics[metric_id]
        if row.get("unit") != metric["unit"] or row.get("basis") != metric["basis"]:
            raise CombineError(f"{company_id}/{metric_id}: range unit/basis mismatch")
        low = _finite_number(row.get("low"), f"{company_id}/{metric_id} low")
        base = _finite_number(row.get("base"), f"{company_id}/{metric_id} base")
        high = _finite_number(row.get("high"), f"{company_id}/{metric_id} high")
        if not low <= base <= high:
            raise CombineError(f"{company_id}/{metric_id}: require low <= base <= high")
        if not isinstance(row.get("methods"), list) or not isinstance(row.get("evidence"), list):
            raise CombineError(f"{company_id}/{metric_id}: range methods/evidence must be lists")
        for evidence_index, citation in enumerate(row["evidence"], 1):
            validate_citation(
                repo_root,
                citation,
                cutoff=cutoff,
                where=f"{company_id}/{metric_id} range evidence {evidence_index}",
            )
        indexed[metric_id] = row
    expected = set(metrics)
    if set(indexed) != expected:
        raise CombineError(f"{company_id}: ranges cover {sorted(indexed)}, expected {sorted(expected)}")
    return indexed


def _validate_consensus(
    *,
    repo_root: Path,
    company_id: str,
    company: dict[str, Any],
    payload: dict[str, Any],
    cutoff: date,
) -> tuple[dict[str, Any], ...]:
    if payload.get("schema_version") != 1 or payload.get("company_id") != company_id:
        raise CombineError(f"{company_id}: consensus schema_version/company_id mismatch")
    # Rachel's public helper owns kind/date/duplicate validation and future filtering.
    anchor_bands(payload, as_of=cutoff.isoformat())
    metrics = {metric["metric_id"]: metric for metric in company["metrics"]}
    accepted = []
    for index, anchor in enumerate(payload.get("anchors", []), 1):
        published = parse_iso_date(anchor.get("published_at"), f"{company_id} anchor {index}")
        if published > cutoff:
            continue
        metric_id = anchor.get("metric_id")
        if metric_id not in metrics:
            raise CombineError(f"{company_id}: anchor {index} has unknown metric {metric_id!r}")
        metric = metrics[metric_id]
        if anchor.get("unit") != metric["unit"] or anchor.get("basis") != metric["basis"]:
            raise CombineError(f"{company_id}/{metric_id}: anchor unit/basis mismatch")
        _finite_number(anchor.get("value"), f"{company_id}/{metric_id} anchor value")
        validate_citation(
            repo_root,
            anchor,
            cutoff=cutoff,
            where=f"{company_id}/{metric_id} anchor",
        )
        accepted.append(anchor)
    return tuple(accepted)


def load_company_inputs(
    *,
    company_id: str,
    repo_root: Path,
    out_root: Path,
    logger: EventLogger | None = None,
) -> CompanyInputs:
    repo_root = Path(repo_root).resolve()
    out_root = Path(out_root).resolve()
    manifest = _load_manifest(repo_root)
    companies = manifest.get("companies", {})
    if company_id not in companies:
        raise CombineError(f"unknown company_id {company_id!r}")
    company = companies[company_id]
    cutoff = _load_cutoff(repo_root)
    conventions = load_conventions(repo_root, manifest, cutoff)
    company_root = out_root / company_id
    timeseries = _load_json(company_root / "timeseries.json", f"{company_id} timeseries")
    if timeseries.get("schema_version") != 1 or timeseries.get("company_id") != company_id:
        raise CombineError(f"{company_id}: timeseries schema_version/company_id mismatch")
    estimates = seasonal_naive_baselines(timeseries, company["period"])
    b0 = {estimate.metric_id: estimate for estimate in estimates}
    expected_metrics = {metric["metric_id"] for metric in company["metrics"]}
    if set(b0) != expected_metrics:
        raise CombineError(f"{company_id}: B0 coverage {sorted(b0)} != {sorted(expected_metrics)}")

    ranges_payload = _load_json(company_root / "ranges.json", f"{company_id} ranges")
    ranges = _validate_ranges(
        repo_root=repo_root,
        company_id=company_id,
        company=company,
        payload=ranges_payload,
        cutoff=cutoff,
    )
    consensus = _load_json(company_root / "consensus.json", f"{company_id} consensus")
    anchors = _validate_consensus(
        repo_root=repo_root,
        company_id=company_id,
        company=company,
        payload=consensus,
        cutoff=cutoff,
    )
    dossier_path = company_root / "research" / "dossier.md"
    context_path = company_root / "analysis" / "context.md"
    news_path = company_root / "analysis" / "news.md"
    for path, label in ((dossier_path, "dossier"), (context_path, "context"), (news_path, "news")):
        if not path.is_file():
            raise CombineError(f"{company_id} {label} does not exist: {path}")
    context = context_path.read_text(encoding="utf-8")
    news = news_path.read_text(encoding="utf-8")
    cited_sources = {
        source
        for text in (context, news)
        for source in re.findall(r"((?:challenge|out)/[^`),\s]+\.md)", text)
    }
    cited_sources.update(anchor["source"] for anchor in anchors)
    cited_sources.update(
        citation["source"]
        for row in ranges.values()
        for citation in row["evidence"]
    )
    cited_sources.update(
        conventions[metric_id]["citation"]["source"] for metric_id in expected_metrics
    )
    source_paths = {dossier_path}
    source_paths.update(resolve_repo_source(repo_root, source) for source in cited_sources)
    evidence = tuple(
        item
        for item in build_evidence_catalog(
            repo_root=repo_root,
            company_id=company_id,
            dossier_path=dossier_path,
            cutoff=cutoff,
            source_paths=tuple(source_paths),
        )
        if item.published_at
    )
    emit_event(
        logger,
        "combine_inputs_validated",
        company_id=company_id,
        range_methods={metric_id: row.get("methods", []) for metric_id, row in ranges.items()},
        evidence_count=len(evidence),
    )
    return CompanyInputs(
        company_id=company_id,
        company=company,
        conventions=conventions,
        cutoff=cutoff,
        timeseries=timeseries,
        ranges=ranges,
        anchors=anchors,
        b0=b0,
        context=context,
        news=news,
        evidence=evidence,
    )


def _response_schema(metric_ids: list[str]) -> dict[str, Any]:
    direction = {"type": "string", "enum": list(DIRECTIONS)}
    evidence_ids = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    driver = {
        "type": "object",
        "properties": {
            "driver": {"type": "string"},
            "direction": direction,
            "evidence_ids": evidence_ids,
        },
        "required": ["driver", "direction", "evidence_ids"],
        "additionalProperties": False,
    }
    metric = {
        "type": "object",
        "properties": {
            "metric_id": {"type": "string", "enum": metric_ids},
            "direction": direction,
            "proposed_delta": {"type": "number"},
            "confidence": {"type": "string", "enum": list(CONFIDENCE)},
            "drivers": {"type": "array", "items": driver},
            "rationale": {"type": "string"},
        },
        "required": [
            "metric_id",
            "direction",
            "proposed_delta",
            "confidence",
            "drivers",
            "rationale",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "metrics": {
                "type": "array",
                "items": metric,
                "minItems": len(metric_ids),
                "maxItems": len(metric_ids),
            }
        },
        "required": ["metrics"],
        "additionalProperties": False,
    }


def _series_by_metric(timeseries: dict[str, Any], period_type: str) -> dict[str, dict[str, Any]]:
    selected = {}
    for series in timeseries.get("series", []):
        if series.get("period_type") != period_type:
            continue
        metric_id = series.get("metric_id")
        if metric_id in selected:
            raise CombineError(f"duplicate target-period series for {metric_id!r}")
        selected[metric_id] = series
    return selected


def _consensus_free_evidence(inputs: CompanyInputs) -> tuple[EvidenceItem, ...]:
    consensus_anchors = [anchor for anchor in inputs.anchors if anchor["kind"] == "consensus"]
    forbidden_sources = {anchor["source"] for anchor in consensus_anchors}
    forbidden_quotes = {re.sub(r"\s+", " ", anchor["quote"]).casefold() for anchor in consensus_anchors}
    safe = []
    for item in inputs.evidence:
        normalized = re.sub(r"\s+", " ", item.quote).casefold()
        if item.source in forbidden_sources or normalized in forbidden_quotes:
            continue
        if "consensus" in normalized or "analyst estimate" in normalized:
            continue
        safe.append(item)
    terms = {
        "demand",
        "guidance",
        "sales",
        "revenue",
        "earnings",
        "profit",
        "margin",
        "industry",
        "risk",
        "market",
    }
    return select_evidence(safe, terms=terms, limit=55)


def _assert_consensus_starved(packet: dict[str, Any], anchors: Sequence[dict[str, Any]]) -> None:
    serialized = json.dumps(packet, sort_keys=True, ensure_ascii=False).casefold()
    if "consensus" in serialized:
        raise CombineError("blind packet contains the consensus label")
    for anchor in anchors:
        if anchor.get("kind") != "consensus":
            continue
        for field in ("source", "quote"):
            value = str(anchor.get(field, "")).strip().casefold()
            if value and value in serialized:
                raise CombineError(f"blind packet leaked consensus {field}")


def _blind_packet(inputs: CompanyInputs) -> tuple[dict[str, Any], tuple[EvidenceItem, ...]]:
    series = _series_by_metric(inputs.timeseries, inputs.company["period_type"])
    evidence = _consensus_free_evidence(inputs)
    metrics = []
    for metric in inputs.company["metrics"]:
        metric_id = metric["metric_id"]
        estimate = inputs.b0[metric_id]
        metrics.append(
            {
                "metric_id": metric_id,
                "unit": metric["unit"],
                "basis": metric["basis"],
                "definition": inputs.conventions[metric_id]["definition"],
                "b0": estimate.value,
                "b0_method": estimate.method,
                "historical_series": series[metric_id],
            }
        )
    packet = {
        "company_id": inputs.company_id,
        "company": inputs.company["company"],
        "target_period": inputs.company["period"],
        "metrics": metrics,
        "evidence": [item.prompt_record() for item in evidence],
    }
    _assert_consensus_starved(packet, inputs.anchors)
    return packet, evidence


def _validate_model_metrics(
    data: dict[str, Any],
    *,
    metric_ids: list[str],
    allowed_evidence: Mapping[str, EvidenceItem],
    where: str,
) -> dict[str, dict[str, Any]]:
    rows = data.get("metrics")
    if not isinstance(rows, list):
        raise CombineError(f"{where}: metrics must be a list")
    indexed = {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise CombineError(f"{where} metric {index}: expected object")
        metric_id = row.get("metric_id")
        if metric_id not in metric_ids or metric_id in indexed:
            raise CombineError(f"{where}: invalid or duplicate metric_id {metric_id!r}")
        direction = row.get("direction")
        confidence = row.get("confidence")
        delta = row.get("proposed_delta")
        if direction not in DIRECTIONS or confidence not in CONFIDENCE:
            raise CombineError(f"{where}/{metric_id}: invalid direction/confidence")
        _finite_number(delta, f"{where}/{metric_id} proposed_delta")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            raise CombineError(f"{where}/{metric_id}: rationale must be non-empty")
        ids = []
        if not isinstance(row.get("drivers"), list):
            raise CombineError(f"{where}/{metric_id}: drivers must be a list")
        for driver_index, driver in enumerate(row["drivers"], 1):
            if not isinstance(driver, dict) or driver.get("direction") not in DIRECTIONS:
                raise CombineError(f"{where}/{metric_id} driver {driver_index}: invalid object")
            if not isinstance(driver.get("driver"), str) or not isinstance(driver.get("evidence_ids"), list):
                raise CombineError(f"{where}/{metric_id} driver {driver_index}: invalid fields")
            ids.extend(driver["evidence_ids"])
        # A hallucinated evidence_id must never abort the company: drop it and
        # let the fewer_than_two_distinct_sources gate reject the delta instead.
        known = [
            evidence_id for evidence_id in ids
            if isinstance(evidence_id, str) and evidence_id in allowed_evidence
        ]
        row["_resolved_evidence_ids"] = list(dict.fromkeys(known))
        indexed[metric_id] = row
    if set(indexed) != set(metric_ids):
        raise CombineError(f"{where}: expected metrics {metric_ids}, got {sorted(indexed)}")
    return indexed


def _valid_anchor(
    *,
    inputs: CompanyInputs,
    metric: dict[str, Any],
    range_row: dict[str, Any],
    logger: EventLogger | None,
) -> tuple[Decimal, str]:
    metric_id = metric["metric_id"]
    low = Decimal(str(range_row["low"]))
    high = Decimal(str(range_row["high"]))
    for kind in ("consensus", "guidance_midpoint"):
        matching = [
            anchor
            for anchor in inputs.anchors
            if anchor["metric_id"] == metric_id and anchor["kind"] == kind
        ]
        if not matching:
            continue
        anchor = Decimal(str(matching[0]["value"]))
        if low <= anchor <= high:
            return anchor, kind
        emit_event(
            logger,
            "combine_anchor_rejected",
            company_id=inputs.company_id,
            metric_id=metric_id,
            anchor_kind=kind,
            anchor=str(anchor),
            reason="outside_range",
        )
    range_base = Decimal(str(range_row["base"]))
    if low <= range_base <= high:
        return range_base, "range_base"
    seasonal = Decimal(str(inputs.b0[metric_id].value))
    if low <= seasonal <= high:
        return seasonal, "seasonal_naive"
    raise CombineError(f"{inputs.company_id}/{metric_id}: no valid in-range anchor")


def _reveal_packet(
    *,
    inputs: CompanyInputs,
    blind: dict[str, Any],
    selected_anchors: dict[str, tuple[Decimal, str]],
) -> tuple[dict[str, Any], tuple[EvidenceItem, ...]]:
    terms = {
        "demand",
        "guidance",
        "consensus",
        "estimate",
        "sales",
        "revenue",
        "earnings",
        "profit",
        "margin",
        "market",
        "risk",
    }
    evidence = select_evidence(inputs.evidence, terms=terms, limit=75)
    metrics = []
    for metric in inputs.company["metrics"]:
        metric_id = metric["metric_id"]
        anchor, anchor_kind = selected_anchors[metric_id]
        metrics.append(
            {
                "metric_id": metric_id,
                "unit": metric["unit"],
                "basis": metric["basis"],
                "definition": inputs.conventions[metric_id]["definition"],
                "anchor": float(anchor),
                "anchor_kind": anchor_kind,
                "range": inputs.ranges[metric_id],
                "public_anchors": [
                    row for row in inputs.anchors if row["metric_id"] == metric_id
                ],
            }
        )
    return (
        {
            "company_id": inputs.company_id,
            "company": inputs.company["company"],
            "target_period": inputs.company["period"],
            "blind_result": blind,
            "analysis_context": inputs.context,
            "analysis_news": inputs.news,
            "metrics": metrics,
            "evidence": [item.prompt_record() for item in evidence],
        },
        evidence,
    )


def _direction_matches_delta(direction: str, delta: Decimal) -> bool:
    if direction == "up":
        return delta > 0
    if direction == "down":
        return delta < 0
    return delta == 0


def propose_company(
    company_id: str,
    inputs: CompanyInputs,
    config: CombineConfig,
    client: StructuredModelClient,
    logger: EventLogger | None = None,
) -> list[MetricCandidate]:
    if company_id != inputs.company_id:
        raise CombineError("company_id does not match CompanyInputs")
    metric_ids = [metric["metric_id"] for metric in inputs.company["metrics"]]
    schema = _response_schema(metric_ids)
    blind_packet, blind_evidence = _blind_packet(inputs)
    blind_result = client.generate_json(
        schema_name=f"avws_combine_blind_{config.prompt_version}",
        instructions=_prompt("blind.md"),
        input_text=json.dumps(blind_packet, indent=2, ensure_ascii=False),
        schema=schema,
        metadata={"stage": "combine_blind", "company_id": company_id},
    ).data
    blind = _validate_model_metrics(
        blind_result,
        metric_ids=metric_ids,
        allowed_evidence=evidence_map(blind_evidence),
        where=f"{company_id} blind",
    )

    selected_anchors = {
        metric["metric_id"]: _valid_anchor(
            inputs=inputs,
            metric=metric,
            range_row=inputs.ranges[metric["metric_id"]],
            logger=logger,
        )
        for metric in inputs.company["metrics"]
    }
    reveal_packet, reveal_evidence = _reveal_packet(
        inputs=inputs,
        blind=blind_result,
        selected_anchors=selected_anchors,
    )
    reveal_result = client.generate_json(
        schema_name=f"avws_combine_reveal_{config.prompt_version}",
        instructions=_prompt("reveal.md"),
        input_text=json.dumps(reveal_packet, indent=2, ensure_ascii=False),
        schema=schema,
        metadata={"stage": "combine_reveal", "company_id": company_id},
    ).data
    reveal_map = evidence_map(reveal_evidence)
    reveal = _validate_model_metrics(
        reveal_result,
        metric_ids=metric_ids,
        allowed_evidence=reveal_map,
        where=f"{company_id} reveal",
    )

    candidates = []
    for manifest_index, metric in enumerate(inputs.company["metrics"]):
        metric_id = metric["metric_id"]
        blind_row = blind[metric_id]
        reveal_row = reveal[metric_id]
        delta = Decimal(str(reveal_row["proposed_delta"]))
        reasons = []
        if blind_row["direction"] != reveal_row["direction"]:
            reasons.append("blind_reveal_direction_disagreement")
        if reveal_row["direction"] not in {"up", "down"}:
            reasons.append("no_directional_edge")
        if not _direction_matches_delta(blind_row["direction"], Decimal(str(blind_row["proposed_delta"]))):
            reasons.append("blind_delta_direction_mismatch")
        if not _direction_matches_delta(reveal_row["direction"], delta):
            reasons.append("reveal_delta_direction_mismatch")
        resolved_items = [reveal_map[eid] for eid in reveal_row["_resolved_evidence_ids"]]
        distinct = []
        sources = set()
        for item in resolved_items:
            if item.source in sources:
                continue
            sources.add(item.source)
            distinct.append(item.citation())
            if len(distinct) == 3:
                break
        if len(distinct) < 2:
            reasons.append("fewer_than_two_distinct_sources")
        anchor, anchor_kind = selected_anchors[metric_id]
        range_row = inputs.ranges[metric_id]
        low, base, high = (
            Decimal(str(range_row[name])) for name in ("low", "base", "high")
        )
        raw_target = anchor + delta
        if raw_target < low or raw_target > high:
            emit_event(
                logger,
                "combine_outside_range_escalation",
                company_id=company_id,
                metric_id=metric_id,
                proposed_value=str(raw_target),
                low=str(low),
                high=str(high),
            )
        candidate = MetricCandidate(
            company_id=company_id,
            metric_id=metric_id,
            manifest_index=manifest_index,
            unit=metric["unit"],
            basis=metric["basis"],
            anchor=anchor,
            anchor_kind=anchor_kind,
            low=low,
            base=base,
            high=high,
            blind_direction=blind_row["direction"],
            reveal_direction=reveal_row["direction"],
            proposed_delta=delta,
            confidence=reveal_row["confidence"],
            evidence=tuple(distinct),
            rationale=reveal_row["rationale"].strip(),
            eligible=not reasons,
            rejection_reasons=tuple(reasons),
        )
        if reasons:
            emit_event(
                logger,
                "combine_delta_rejected",
                company_id=company_id,
                metric_id=metric_id,
                reasons=reasons,
            )
        candidates.append(candidate)
    return candidates


def _precision(*values: Decimal) -> int:
    return max(max(-value.as_tuple().exponent, 0) for value in values)


def _quantize(value: Decimal, places: int) -> Decimal:
    quantum = Decimal(1).scaleb(-places)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def _clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    return min(max(value, low), high)


def _one_sentence(value: str) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    match = re.match(r"(.+?[.!?])(?:\s|$)", compact)
    if match:
        return match.group(1)
    return compact.rstrip(".") + "."


def _number(value: Decimal) -> float:
    return float(value)


def finalize_batch(
    candidates_by_company: Mapping[str, Sequence[MetricCandidate]],
    inputs: Mapping[str, CompanyInputs],
    config: CombineConfig,
    logger: EventLogger | None = None,
) -> dict[str, FinalPayload]:
    all_candidates = [candidate for rows in candidates_by_company.values() for candidate in rows]
    eligible = [candidate for candidate in all_candidates if candidate.eligible]
    eligible.sort(
        key=lambda candidate: (
            -len({citation["source"] for citation in candidate.evidence}),
            -CONFIDENCE_RANK[candidate.confidence],
            -candidate.normalized_delta,
            list(inputs).index(candidate.company_id),
            candidate.manifest_index,
        )
    )
    limit = config.max_deviations_single if len(candidates_by_company) == 1 else config.max_deviations_batch
    selected = {(candidate.company_id, candidate.metric_id) for candidate in eligible[:limit]}
    outputs = {}
    for company_id, candidates in candidates_by_company.items():
        if company_id not in inputs:
            raise CombineError(f"missing CompanyInputs for {company_id}")
        expected = [metric["metric_id"] for metric in inputs[company_id].company["metrics"]]
        indexed = {candidate.metric_id: candidate for candidate in candidates}
        if set(indexed) != set(expected) or len(indexed) != len(candidates):
            raise CombineError(f"{company_id}: candidate metric coverage mismatch")
        finals = []
        for metric_id in expected:
            candidate = indexed[metric_id]
            key = (company_id, metric_id)
            chosen = key in selected
            if chosen:
                cap = candidate.range_width * config.raw_delta_range_fraction
                capped_delta = _clamp(candidate.proposed_delta, -cap, cap)
                unrounded = candidate.anchor + config.model_delta_share * capped_delta
                clamped = _clamp(unrounded, candidate.low, candidate.high)
                places = _precision(candidate.anchor, candidate.low, candidate.base, candidate.high)
                value = _clamp(_quantize(clamped, places), candidate.low, candidate.high)
                delta = value - candidate.anchor
            else:
                value = candidate.anchor
                delta = Decimal(0)
            if delta == 0:
                evidence = []
                if candidate.rejection_reasons:
                    rationale = "Anchor retained because the proposed delta failed validation."
                elif candidate.eligible and not chosen:
                    rationale = "Anchor retained under the global deviation budget."
                else:
                    rationale = "Anchor retained because no validated directional edge was available."
            else:
                evidence = list(candidate.evidence[:3])
                if len({item["source"] for item in evidence}) < 2:
                    raise CombineError(f"{company_id}/{metric_id}: nonzero delta lost evidence coverage")
                rationale = _one_sentence(candidate.rationale)
            final = {
                "metric_id": metric_id,
                "value": _number(value),
                "unit": candidate.unit,
                "basis": candidate.basis,
                "anchor": _number(candidate.anchor),
                "anchor_kind": candidate.anchor_kind,
                "delta": _number(delta),
                "delta_evidence": evidence,
                "fallback_tier": 0,
                "rationale": rationale,
            }
            if Decimal(str(final["anchor"])) + Decimal(str(final["delta"])) != Decimal(
                str(final["value"])
            ):
                raise CombineError(f"{company_id}/{metric_id}: anchor + delta != value")
            if not candidate.low <= Decimal(str(final["value"])) <= candidate.high:
                raise CombineError(f"{company_id}/{metric_id}: final escaped Rachel's range")
            finals.append(final)
            emit_event(
                logger,
                "combine_finalized",
                company_id=company_id,
                metric_id=metric_id,
                selected_deviation=bool(delta),
                anchor_kind=candidate.anchor_kind,
                value=final["value"],
            )
        outputs[company_id] = FinalPayload(company_id=company_id, finals=tuple(finals))
    return outputs


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def run_combine(
    company_ids: Sequence[str],
    repo_root: Path,
    out_root: Path,
    config: CombineConfig,
    client: StructuredModelClient,
    run_started_at: datetime,
    logger: EventLogger | None = None,
) -> None:
    if run_started_at.tzinfo is None:
        raise CombineError("run_started_at must be timezone-aware")
    repo_root = Path(repo_root).resolve()
    out_root = Path(out_root).resolve()
    if not company_ids:
        raise CombineError("company_ids cannot be empty")
    emit_event(logger, "combine_config", run_started_at=run_started_at.isoformat(), **config.as_log_record())
    loaded = {
        company_id: load_company_inputs(
            company_id=company_id,
            repo_root=repo_root,
            out_root=out_root,
            logger=logger,
        )
        for company_id in company_ids
    }
    candidates = {
        company_id: propose_company(company_id, loaded[company_id], config, client, logger)
        for company_id in company_ids
    }
    final_payloads = finalize_batch(candidates, loaded, config, logger)
    for company_id, payload in final_payloads.items():
        _write_json_atomic(out_root / company_id / "final.json", payload.as_document())
        emit_event(logger, "combine_published", company_id=company_id, output=str(out_root / company_id / "final.json"))
