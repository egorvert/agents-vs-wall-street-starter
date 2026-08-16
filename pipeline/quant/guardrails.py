"""Deterministic forecast baselines and guardrail building blocks.

Step 3 implements B0 only: a seasonal-naive estimate from like-for-like fiscal
periods. Range construction and other anchors are deliberately separate steps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from pipeline.quant.extract_timeseries import canonical_period_type


class GuardrailError(ValueError):
    """Raised when a deterministic baseline cannot be computed safely."""


@dataclass(frozen=True)
class EvidencePoint:
    period: str
    value: int | float
    source: str
    published_at: str
    quote: str

    @classmethod
    def from_point(cls, point: dict) -> "EvidencePoint":
        return cls(
            period=point["period"],
            value=point["value"],
            source=point["source"],
            published_at=point["published_at"],
            quote=point["quote"],
        )


@dataclass(frozen=True)
class SeasonalNaiveEstimate:
    metric_id: str
    unit: str
    basis: str
    target_period: str
    value: float
    method: str
    trend: float | None
    evidence: tuple[EvidencePoint, ...]

    @property
    def comparable_periods(self) -> tuple[str, ...]:
        return tuple(point.period for point in self.evidence)


def _guardrail_period_type(period: object, where: str) -> str:
    if not isinstance(period, str):
        raise GuardrailError(f"{where}: period must be a canonical string")
    try:
        return canonical_period_type(period, where)
    except ValueError as exc:
        raise GuardrailError(str(exc)) from exc


def _seasonal_slot(period: str) -> str:
    period_type = _guardrail_period_type(period, "seasonal-naive period")
    if period_type == "Q":
        return period[-2:]
    return period_type


def _validated_points(series: dict, target_period: str) -> list[dict]:
    metric_id = series.get("metric_id", "<unknown>")
    period_type = series.get("period_type")
    target_type = _guardrail_period_type(target_period, "seasonal-naive target")
    if period_type != target_type:
        raise GuardrailError(
            f"{metric_id}: series period_type {period_type!r} does not match target {target_type!r}"
        )

    points = series.get("points")
    if not isinstance(points, list):
        raise GuardrailError(f"{metric_id}: points must be a list")

    target_slot = _seasonal_slot(target_period)
    comparable: list[dict] = []
    seen_periods: set[str] = set()
    for index, point in enumerate(points, 1):
        where = f"{metric_id} point {index}"
        if not isinstance(point, dict):
            raise GuardrailError(f"{where}: point must be an object")
        try:
            period = point["period"]
            value = point["value"]
        except KeyError as exc:
            raise GuardrailError(f"{where}: missing {exc.args[0]!r}") from exc
        point_type = _guardrail_period_type(period, where)
        if point_type != period_type:
            raise GuardrailError(
                f"{where}: period {period!r} is {point_type}, not series type {period_type}"
            )
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise GuardrailError(f"{where}: value must be a finite number")
        missing_evidence = [
            field for field in ("source", "published_at", "quote") if not point.get(field)
        ]
        if missing_evidence:
            raise GuardrailError(f"{where}: missing evidence fields {missing_evidence}")
        if period in seen_periods:
            raise GuardrailError(f"{metric_id}: duplicate period {period}")
        seen_periods.add(period)

        # Target and future observations are never predictors. Q series also require
        # the same fiscal quarter; FY/H1/H2 matching is carried by period_type.
        if period < target_period and _seasonal_slot(period) == target_slot:
            comparable.append(point)

    comparable.sort(key=lambda point: point["period"])
    if not comparable:
        raise GuardrailError(
            f"{metric_id}: no prior {target_slot} observation exists for target {target_period}"
        )
    return comparable


def seasonal_naive_for_series(series: dict, target_period: str) -> SeasonalNaiveEstimate:
    """Compute B0 for one metric from the most recent like-for-like periods.

    Money and per-share levels extend the latest YoY rate when both levels are
    positive. Percentages and sign-changing/non-positive levels extend the latest
    additive change, avoiding invalid ratio arithmetic. One observation falls back
    to the last comparable value and records that lower-information method.
    """
    required = ("metric_id", "unit", "basis", "period_type")
    missing = [field for field in required if not series.get(field)]
    if missing:
        raise GuardrailError(f"series is missing required fields {missing}")

    comparable = _validated_points(series, target_period)
    latest = comparable[-1]
    evidence_points = [latest]

    if len(comparable) == 1:
        forecast = float(latest["value"])
        method = "seasonal_naive_last_comparable"
        trend = None
    else:
        previous = comparable[-2]
        evidence_points.insert(0, previous)
        previous_value = float(previous["value"])
        latest_value = float(latest["value"])
        if series["unit"] != "%" and previous_value > 0 and latest_value > 0:
            trend = latest_value / previous_value - 1.0
            forecast = latest_value * (1.0 + trend)
            method = "seasonal_naive_trailing_yoy"
        else:
            trend = latest_value - previous_value
            forecast = latest_value + trend
            method = "seasonal_naive_additive_drift"

    if not math.isfinite(forecast):
        raise GuardrailError(f"{series['metric_id']}: seasonal-naive forecast is not finite")

    return SeasonalNaiveEstimate(
        metric_id=series["metric_id"],
        unit=series["unit"],
        basis=series["basis"],
        target_period=target_period,
        value=forecast,
        method=method,
        trend=trend,
        evidence=tuple(EvidencePoint.from_point(point) for point in evidence_points),
    )


def seasonal_naive_baselines(timeseries: dict, target_period: str) -> tuple[SeasonalNaiveEstimate, ...]:
    """Compute one target-period B0 estimate for every matching metric series."""
    if not isinstance(timeseries, dict):
        raise GuardrailError("timeseries must be an object")
    series_list = timeseries.get("series")
    if not isinstance(series_list, list):
        raise GuardrailError("timeseries.series must be a list")

    target_type = _guardrail_period_type(target_period, "seasonal-naive target")
    matching = []
    for index, series in enumerate(series_list, 1):
        if not isinstance(series, dict):
            raise GuardrailError(f"timeseries series {index} must be an object")
        if series.get("period_type") == target_type:
            matching.append(series)
    if not matching:
        raise GuardrailError(f"no {target_type} series available for target {target_period}")

    seen_metrics: set[str] = set()
    estimates = []
    for series in matching:
        metric_id = series.get("metric_id")
        if metric_id in seen_metrics:
            raise GuardrailError(f"duplicate {target_type} series for metric {metric_id!r}")
        seen_metrics.add(metric_id)
        estimates.append(seasonal_naive_for_series(series, target_period))
    return tuple(estimates)
