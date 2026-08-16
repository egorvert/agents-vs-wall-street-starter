"""Point-in-time event validation and deterministic forecast evaluation."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from statistics import fmean, median
from typing import Mapping, Sequence


class EvaluationError(ValueError):
    """Raised when an evaluation input would make a score unreliable."""


@dataclass(frozen=True)
class ActualObservation:
    metric_id: str
    value: float
    unit: str
    basis: str
    source: str
    published_at: str
    quote: str


@dataclass(frozen=True)
class HistoricalEvent:
    event_id: str
    company_id: str
    target_period: str
    as_of: str
    actuals: tuple[ActualObservation, ...]


@dataclass(frozen=True)
class MetricEvaluation:
    event_id: str
    company_id: str
    target_period: str
    config_id: str
    metric_id: str
    unit: str
    basis: str
    actual: float
    forecast: float | None
    proxy: float
    floor: float
    forecast_absolute_miss: float | None
    proxy_absolute_miss: float
    official_score: float
    proxy_score: float
    outcome_vs_proxy: str
    status: str
    absolute_percentage_error: float | None
    actual_in_range: bool | None
    range_width_in_floors: float | None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ConfigSummary:
    config_id: str
    metric_count: int
    mean_official_score: float
    median_official_score: float
    mean_proxy_score: float
    delta_vs_proxy: float
    win_rate_vs_proxy: float
    tie_rate_vs_proxy: float
    capped_score_rate: float
    missing_forecasts: int
    invalid_forecasts: int
    mean_absolute_percentage_error: float | None
    median_absolute_percentage_error: float | None
    range_coverage: float | None
    mean_range_width_in_floors: float | None

    def as_dict(self) -> dict:
        return asdict(self)


_EVENT_FIELDS = {
    "schema_version",
    "event_id",
    "company_id",
    "target_period",
    "as_of",
    "actuals",
}
_ACTUAL_FIELDS = {
    "metric_id",
    "value",
    "unit",
    "basis",
    "source",
    "published_at",
    "quote",
}


def _require_closed_fields(value: dict, expected: set[str], label: str) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        raise EvaluationError(f"{label} fields are not closed; missing={missing}, extra={extra}")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"{label} must be a non-empty string")
    return value


def _require_date(value: object, label: str) -> date:
    text = _require_text(value, label)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise EvaluationError(f"{label} must be an ISO date, YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        raise EvaluationError(f"{label} must be an ISO date, YYYY-MM-DD")
    return parsed


def _require_finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise EvaluationError(f"{label} must be a finite number")
    return number


def _load_metric_definitions(repo_root: Path, company_id: str) -> dict[str, dict]:
    manifest_path = repo_root / "schemas" / "metrics.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read metric manifest {manifest_path}: {exc}") from exc
    companies = manifest.get("companies", {})
    if company_id not in companies:
        raise EvaluationError(f"unknown company_id {company_id!r}")
    return {metric["metric_id"]: metric for metric in companies[company_id]["metrics"]}


def _verify_local_quote(repo_root: Path, source: str, quote: str, label: str) -> None:
    source_path = Path(source)
    if source_path.is_absolute() or "://" in source:
        raise EvaluationError(f"{label}.source must be a repository-relative path")
    resolved_root = repo_root.resolve()
    resolved_source = (resolved_root / source_path).resolve()
    try:
        resolved_source.relative_to(resolved_root)
    except ValueError as exc:
        raise EvaluationError(f"{label}.source escapes the repository: {source!r}") from exc
    try:
        contents = resolved_source.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvaluationError(f"{label}.source cannot be read: {source!r}") from exc
    if quote not in contents:
        raise EvaluationError(f"{label}.quote is not present in {source!r}")


def validate_event_manifest(document: dict, repo_root: Path) -> HistoricalEvent:
    """Validate a closed historical-event manifest and its held-out actual citations."""
    if not isinstance(document, dict):
        raise EvaluationError("event manifest must be a JSON object")
    _require_closed_fields(document, _EVENT_FIELDS, "event manifest")
    if document["schema_version"] != 1:
        raise EvaluationError("event manifest schema_version must be 1")

    event_id = _require_text(document["event_id"], "event_id")
    company_id = _require_text(document["company_id"], "company_id")
    target_period = _require_text(document["target_period"], "target_period")
    as_of_text = _require_text(document["as_of"], "as_of")
    as_of = _require_date(as_of_text, "as_of")
    metrics = _load_metric_definitions(Path(repo_root), company_id)

    raw_actuals = document["actuals"]
    if not isinstance(raw_actuals, list) or not raw_actuals:
        raise EvaluationError("actuals must be a non-empty list")
    actuals = []
    seen_metrics: set[str] = set()
    for index, raw in enumerate(raw_actuals, start=1):
        label = f"actuals[{index}]"
        if not isinstance(raw, dict):
            raise EvaluationError(f"{label} must be an object")
        _require_closed_fields(raw, _ACTUAL_FIELDS, label)
        metric_id = _require_text(raw["metric_id"], f"{label}.metric_id")
        if metric_id not in metrics:
            raise EvaluationError(f"{label}.metric_id is unknown for {company_id}: {metric_id!r}")
        if metric_id in seen_metrics:
            raise EvaluationError(f"duplicate actual metric_id {metric_id!r}")
        seen_metrics.add(metric_id)
        expected = metrics[metric_id]
        unit = _require_text(raw["unit"], f"{label}.unit")
        basis = _require_text(raw["basis"], f"{label}.basis")
        if unit != expected["unit"]:
            raise EvaluationError(
                f"{label}.unit {unit!r} != metric manifest {expected['unit']!r}"
            )
        if basis != expected["basis"]:
            raise EvaluationError(
                f"{label}.basis {basis!r} != metric manifest {expected['basis']!r}"
            )
        published_text = _require_text(raw["published_at"], f"{label}.published_at")
        published_at = _require_date(published_text, f"{label}.published_at")
        if published_at <= as_of:
            raise EvaluationError(
                f"{label} is not held out: published_at {published_text} <= as_of {as_of_text}"
            )
        source = _require_text(raw["source"], f"{label}.source")
        quote = _require_text(raw["quote"], f"{label}.quote")
        _verify_local_quote(Path(repo_root), source, quote, label)
        actuals.append(
            ActualObservation(
                metric_id=metric_id,
                value=_require_finite(raw["value"], f"{label}.value"),
                unit=unit,
                basis=basis,
                source=source,
                published_at=published_text,
                quote=quote,
            )
        )

    return HistoricalEvent(
        event_id=event_id,
        company_id=company_id,
        target_period=target_period,
        as_of=as_of_text,
        actuals=tuple(actuals),
    )


def load_event_manifest(path: Path, repo_root: Path) -> HistoricalEvent:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationError(f"event manifest does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read event manifest {path}: {exc}") from exc
    return validate_event_manifest(document, repo_root)


def official_floor(actual: float, unit: str, *, zero_result_floor: float | None = None) -> float:
    """Return the JUDGING.md denominator floor for one reported result."""
    actual_value = _require_finite(actual, "actual")
    _require_text(unit, "unit")
    if unit == "%":
        return 0.5
    if actual_value != 0.0:
        return abs(actual_value) * 0.005
    if zero_result_floor is None:
        raise EvaluationError(
            "zero money/EPS actual requires an explicit zero_result_floor; JUDGING.md "
            "does not specify the fixed fallback value"
        )
    fallback = _require_finite(zero_result_floor, "zero_result_floor")
    if fallback <= 0.0:
        raise EvaluationError("zero_result_floor must be greater than zero")
    return fallback


def _forecast_value(value: object) -> tuple[float | None, str]:
    if value is None:
        return None, "missing_forecast"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, "invalid_forecast"
    number = float(value)
    if not math.isfinite(number):
        return None, "invalid_forecast"
    return number, "ok"


def score_metric(
    *,
    event_id: str,
    company_id: str,
    target_period: str,
    config_id: str,
    actual: ActualObservation,
    forecast: object,
    proxy: object,
    range_low: object | None = None,
    range_high: object | None = None,
    zero_result_floor: float | None = None,
) -> MetricEvaluation:
    """Score one metric exactly once, preserving failures and interval diagnostics."""
    for value, label in (
        (event_id, "event_id"),
        (company_id, "company_id"),
        (target_period, "target_period"),
        (config_id, "config_id"),
    ):
        _require_text(value, label)
    proxy_value = _require_finite(proxy, "proxy")
    floor = official_floor(actual.value, actual.unit, zero_result_floor=zero_result_floor)
    proxy_miss = abs(proxy_value - actual.value)
    denominator = max(proxy_miss, floor)
    proxy_score = min(5.0, proxy_miss / denominator)
    forecast_value, status = _forecast_value(forecast)

    if forecast_value is None:
        forecast_miss = None
        score = 5.0
        outcome = "missing" if status == "missing_forecast" else "invalid"
        ape = None
    else:
        forecast_miss = abs(forecast_value - actual.value)
        score = min(5.0, forecast_miss / denominator)
        if forecast_miss < proxy_miss:
            outcome = "win"
        elif forecast_miss > proxy_miss:
            outcome = "loss"
        else:
            outcome = "tie"
        ape = None if actual.value == 0.0 else forecast_miss / abs(actual.value)

    if (range_low is None) != (range_high is None):
        raise EvaluationError("range_low and range_high must be supplied together")
    if range_low is None:
        actual_in_range = None
        width_in_floors = None
    else:
        low = _require_finite(range_low, "range_low")
        high = _require_finite(range_high, "range_high")
        if low > high:
            raise EvaluationError("range_low must be less than or equal to range_high")
        actual_in_range = low <= actual.value <= high
        width_in_floors = (high - low) / floor

    return MetricEvaluation(
        event_id=event_id,
        company_id=company_id,
        target_period=target_period,
        config_id=config_id,
        metric_id=actual.metric_id,
        unit=actual.unit,
        basis=actual.basis,
        actual=actual.value,
        forecast=forecast_value,
        proxy=proxy_value,
        floor=floor,
        forecast_absolute_miss=forecast_miss,
        proxy_absolute_miss=proxy_miss,
        official_score=score,
        proxy_score=proxy_score,
        outcome_vs_proxy=outcome,
        status=status,
        absolute_percentage_error=ape,
        actual_in_range=actual_in_range,
        range_width_in_floors=width_in_floors,
    )


def score_event(
    event: HistoricalEvent,
    *,
    config_id: str,
    forecasts: Mapping[str, object],
    proxies: Mapping[str, object],
    ranges: Mapping[str, tuple[object, object]] | None = None,
    zero_result_floor: float | None = None,
) -> tuple[MetricEvaluation, ...]:
    """Score all held-out actuals in an event without hiding missing forecasts."""
    if not isinstance(event, HistoricalEvent):
        raise EvaluationError("event must be a validated HistoricalEvent")
    metric_ids = {actual.metric_id for actual in event.actuals}
    for values, label in ((forecasts, "forecasts"), (proxies, "proxies")):
        unknown = sorted(set(values) - metric_ids)
        if unknown:
            raise EvaluationError(f"{label} contain unknown event metrics: {unknown}")
    missing_proxies = sorted(metric_ids - set(proxies))
    if missing_proxies:
        raise EvaluationError(f"proxies are missing event metrics: {missing_proxies}")
    range_values = ranges or {}
    unknown_ranges = sorted(set(range_values) - metric_ids)
    if unknown_ranges:
        raise EvaluationError(f"ranges contain unknown event metrics: {unknown_ranges}")

    results = []
    for actual in event.actuals:
        bounds = range_values.get(actual.metric_id, (None, None))
        if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
            raise EvaluationError(f"range for {actual.metric_id} must be a low/high pair")
        results.append(
            score_metric(
                event_id=event.event_id,
                company_id=event.company_id,
                target_period=event.target_period,
                config_id=config_id,
                actual=actual,
                forecast=forecasts.get(actual.metric_id),
                proxy=proxies[actual.metric_id],
                range_low=bounds[0],
                range_high=bounds[1],
                zero_result_floor=zero_result_floor,
            )
        )
    return tuple(results)


def summarize_config(evaluations: Sequence[MetricEvaluation]) -> ConfigSummary:
    """Aggregate paired metric scores for one configuration."""
    if not evaluations:
        raise EvaluationError("cannot summarize an empty evaluation collection")
    if not all(isinstance(item, MetricEvaluation) for item in evaluations):
        raise EvaluationError("all summary inputs must be MetricEvaluation instances")
    config_ids = {item.config_id for item in evaluations}
    if len(config_ids) != 1:
        raise EvaluationError(f"summary contains multiple config_ids: {sorted(config_ids)}")
    identities = [(item.event_id, item.metric_id) for item in evaluations]
    if len(identities) != len(set(identities)):
        raise EvaluationError("summary contains duplicate event/metric evaluations")

    scores = [item.official_score for item in evaluations]
    proxy_scores = [item.proxy_score for item in evaluations]
    apes = [
        item.absolute_percentage_error
        for item in evaluations
        if item.absolute_percentage_error is not None
    ]
    ranged = [item for item in evaluations if item.actual_in_range is not None]
    widths = [
        item.range_width_in_floors
        for item in ranged
        if item.range_width_in_floors is not None
    ]
    count = len(evaluations)
    mean_score = fmean(scores)
    mean_proxy = fmean(proxy_scores)
    return ConfigSummary(
        config_id=next(iter(config_ids)),
        metric_count=count,
        mean_official_score=mean_score,
        median_official_score=median(scores),
        mean_proxy_score=mean_proxy,
        delta_vs_proxy=mean_score - mean_proxy,
        win_rate_vs_proxy=sum(item.outcome_vs_proxy == "win" for item in evaluations) / count,
        tie_rate_vs_proxy=sum(item.outcome_vs_proxy == "tie" for item in evaluations) / count,
        capped_score_rate=sum(item.official_score == 5.0 for item in evaluations) / count,
        missing_forecasts=sum(item.status == "missing_forecast" for item in evaluations),
        invalid_forecasts=sum(item.status == "invalid_forecast" for item in evaluations),
        mean_absolute_percentage_error=fmean(apes) if apes else None,
        median_absolute_percentage_error=median(apes) if apes else None,
        range_coverage=(
            sum(bool(item.actual_in_range) for item in ranged) / len(ranged) if ranged else None
        ),
        mean_range_width_in_floors=fmean(widths) if widths else None,
    )
