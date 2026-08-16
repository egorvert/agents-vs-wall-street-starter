"""Deterministic forecast baselines and guardrail building blocks.

Step 3 implements B0 only: a seasonal-naive estimate from like-for-like fiscal
periods. Range construction and other anchors are deliberately separate steps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from statistics import median

from pipeline.quant.extract_timeseries import canonical_period_type


class GuardrailError(ValueError):
    """Raised when a deterministic baseline cannot be computed safely."""


class InsufficientHistoryError(GuardrailError):
    """Raised when a method is valid but the time series is not yet deep enough."""


@dataclass(frozen=True)
class EvidenceCitation:
    source: str
    published_at: str
    quote: str

    def as_citation(self) -> dict:
        return {
            "source": self.source,
            "published_at": self.published_at,
            "quote": self.quote,
        }


@dataclass(frozen=True)
class EvidencePoint(EvidenceCitation):
    period: str
    value: int | float

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


@dataclass(frozen=True)
class GuardrailBand:
    metric_id: str
    unit: str
    basis: str
    low: float
    base: float
    high: float
    methods: tuple[str, ...]
    evidence: tuple[EvidencePoint, ...]
    notes: str

    def as_range(self) -> dict:
        """Return exactly the per-metric fields allowed by Contract E."""
        return {
            "metric_id": self.metric_id,
            "unit": self.unit,
            "basis": self.basis,
            "low": self.low,
            "base": self.base,
            "high": self.high,
            "methods": list(self.methods),
            "evidence": [point.as_citation() for point in self.evidence],
            "notes": self.notes,
        }


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
            applied = trend
            if series["unit"] == "%":
                # Damp percent-metric drift: a -3.3 -> +1.0 comp-sales recovery
                # must not extrapolate to +5.3. Cap the APPLIED drift at the
                # larger of |latest| and 1 point; `trend` keeps the raw swing so
                # the band still widens on it — uncertainty preserved, point damped.
                cap = max(abs(latest_value), 1.0)
                applied = math.copysign(min(abs(trend), cap), trend) if trend else 0.0
            forecast = latest_value + applied
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


def _matching_series(timeseries: dict, target_period: str) -> tuple[str, tuple[dict, ...]]:
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
    for series in matching:
        metric_id = series.get("metric_id")
        if metric_id in seen_metrics:
            raise GuardrailError(f"duplicate {target_type} series for metric {metric_id!r}")
        seen_metrics.add(metric_id)
    return target_type, tuple(matching)


def seasonal_naive_baselines(timeseries: dict, target_period: str) -> tuple[SeasonalNaiveEstimate, ...]:
    """Compute one target-period B0 estimate for every matching metric series."""
    _, matching = _matching_series(timeseries, target_period)
    return tuple(seasonal_naive_for_series(series, target_period) for series in matching)


def _minimum_band_half_width(
    *,
    metric_id: str,
    unit: str,
    base: float,
    explicit_minimum: float | None,
) -> float:
    if explicit_minimum is not None:
        if (
            isinstance(explicit_minimum, bool)
            or not isinstance(explicit_minimum, (int, float))
            or not math.isfinite(explicit_minimum)
            or explicit_minimum <= 0
        ):
            raise GuardrailError("minimum_half_width must be a positive finite number")
        return float(explicit_minimum)
    if unit == "%":
        return 0.5
    proxy = abs(base) * 0.005
    if proxy == 0:
        raise GuardrailError(
            f"{metric_id}: zero base requires an explicit money/EPS minimum_half_width"
        )
    return proxy


def seasonal_naive_band(
    estimate: SeasonalNaiveEstimate,
    *,
    minimum_half_width: float | None = None,
) -> GuardrailBand:
    """Create a symmetric, evidence-backed band around a seasonal-naive B0.

    The observed component is the magnitude of the projected move from the latest
    comparable actual to B0. The minimum component mirrors the official 0.5pp
    percentage floor or uses 0.5% of |B0| as the pre-results proxy for money/EPS.
    """
    if not isinstance(estimate, SeasonalNaiveEstimate):
        raise GuardrailError("seasonal_naive_band requires a SeasonalNaiveEstimate")
    latest_value = float(estimate.evidence[-1].value)
    observed_move = abs(estimate.value - latest_value)
    minimum = _minimum_band_half_width(
        metric_id=estimate.metric_id,
        unit=estimate.unit,
        base=estimate.value,
        explicit_minimum=minimum_half_width,
    )
    half_width = max(observed_move, minimum)
    low = estimate.value - half_width
    high = estimate.value + half_width
    if not all(math.isfinite(value) for value in (low, estimate.value, high)):
        raise GuardrailError(f"{estimate.metric_id}: seasonal-naive band is not finite")
    return GuardrailBand(
        metric_id=estimate.metric_id,
        unit=estimate.unit,
        basis=estimate.basis,
        low=low,
        base=estimate.value,
        high=high,
        methods=("seasonal_naive_band", estimate.method),
        evidence=estimate.evidence,
        notes=(
            f"B0 for {estimate.target_period}; symmetric half-width {half_width:g} is the larger "
            f"of projected seasonal move {observed_move:g} and minimum {minimum:g}"
        ),
    )


def seasonal_naive_bands(
    timeseries: dict,
    target_period: str,
    *,
    minimum_half_widths: dict[str, float] | None = None,
) -> tuple[GuardrailBand, ...]:
    """Build one seasonal-naive band for each available target-period metric."""
    overrides = minimum_half_widths or {}
    return tuple(
        seasonal_naive_band(
            estimate,
            minimum_half_width=overrides.get(estimate.metric_id),
        )
        for estimate in seasonal_naive_baselines(timeseries, target_period)
    )


def yoy_trend_band_for_series(
    series: dict,
    target_period: str,
    *,
    minimum_half_width: float | None = None,
) -> GuardrailBand:
    """Build a robust YoY-trend band from multiple like-for-like changes.

    At least three comparable periods (two changes) are required. The median
    historical change sets the base; applying every observed change to the latest
    value creates the low/high scenario envelope. Percentages and non-positive
    levels use additive changes, while consistently positive levels use growth.
    """
    required = ("metric_id", "unit", "basis", "period_type")
    missing = [field for field in required if not series.get(field)]
    if missing:
        raise GuardrailError(f"series is missing required fields {missing}")
    comparable = _validated_points(series, target_period)
    if len(comparable) < 3:
        raise InsufficientHistoryError(
            f"{series['metric_id']}: YoY trend requires at least 3 comparable periods; "
            f"found {len(comparable)}"
        )

    values = [float(point["value"]) for point in comparable]
    latest = values[-1]
    use_growth = series["unit"] != "%" and all(value > 0 for value in values)
    if use_growth:
        changes = [current / previous - 1.0 for previous, current in zip(values, values[1:])]
        central_change = float(median(changes))
        scenarios = [latest * (1.0 + change) for change in changes]
        base = latest * (1.0 + central_change)
        detail_method = "yoy_trend_median_growth"
        change_label = "growth"
    else:
        changes = [current - previous for previous, current in zip(values, values[1:])]
        central_change = float(median(changes))
        scenarios = [latest + change for change in changes]
        base = latest + central_change
        detail_method = "yoy_trend_median_change"
        change_label = "change"

    if not all(math.isfinite(value) for value in (*changes, *scenarios, base)):
        raise GuardrailError(f"{series['metric_id']}: YoY trend calculation is not finite")
    minimum = _minimum_band_half_width(
        metric_id=series["metric_id"],
        unit=series["unit"],
        base=base,
        explicit_minimum=minimum_half_width,
    )
    low = min(min(scenarios), base - minimum)
    high = max(max(scenarios), base + minimum)
    evidence = tuple(EvidencePoint.from_point(point) for point in comparable)
    return GuardrailBand(
        metric_id=series["metric_id"],
        unit=series["unit"],
        basis=series["basis"],
        low=low,
        base=base,
        high=high,
        methods=("yoy_trend_band", detail_method),
        evidence=evidence,
        notes=(
            f"{target_period} median YoY {change_label} {central_change:g} from "
            f"{len(changes)} point-in-time changes; envelope uses every observed change "
            f"and minimum half-width {minimum:g}"
        ),
    )


def yoy_trend_bands(
    timeseries: dict,
    target_period: str,
    *,
    minimum_half_widths: dict[str, float] | None = None,
) -> tuple[GuardrailBand, ...]:
    """Build one YoY-trend band for every target-period metric series."""
    overrides = minimum_half_widths or {}
    _, matching = _matching_series(timeseries, target_period)
    return tuple(
        yoy_trend_band_for_series(
            series,
            target_period,
            minimum_half_width=overrides.get(series["metric_id"]),
        )
        for series in matching
    )


def _iso_date(value: object, where: str) -> date:
    if not isinstance(value, str) or len(value) != 10:
        raise GuardrailError(f"{where}: expected YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise GuardrailError(f"{where}: invalid date {value!r}") from exc
    if parsed.isoformat() != value:
        raise GuardrailError(f"{where}: expected canonical YYYY-MM-DD date")
    return parsed


def anchor_band(
    anchor: dict,
    *,
    half_width: float | None = None,
) -> GuardrailBand:
    """Convert one validated consensus/guidance point into a deterministic band."""
    if not isinstance(anchor, dict):
        raise GuardrailError("anchor must be an object")
    required = (
        "metric_id",
        "kind",
        "value",
        "unit",
        "basis",
        "source",
        "published_at",
        "quote",
    )
    missing = [field for field in required if anchor.get(field) in (None, "")]
    if missing:
        raise GuardrailError(f"anchor is missing required fields {missing}")
    value = anchor["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise GuardrailError(f"{anchor['metric_id']}: anchor value must be a finite number")
    kind = anchor["kind"]
    if kind not in {"consensus", "guidance_midpoint"}:
        raise GuardrailError(f"{anchor['metric_id']}: unsupported anchor kind {kind!r}")
    _iso_date(anchor["published_at"], f"{anchor['metric_id']} anchor")

    if half_width is None:
        minimum = _minimum_band_half_width(
            metric_id=anchor["metric_id"],
            unit=anchor["unit"],
            base=float(value),
            explicit_minimum=None,
        )
        width = minimum if kind == "consensus" else 2.0 * minimum
    else:
        width = _minimum_band_half_width(
            metric_id=anchor["metric_id"],
            unit=anchor["unit"],
            base=float(value),
            explicit_minimum=half_width,
        )

    point = float(value)
    low = point - width
    high = point + width
    if kind == "consensus":
        base = point
        methods = ("consensus_anchor",)
        notes = f"consensus-centered proxy band with half-width {width:g}"
    else:
        base = point + 0.5 * width
        methods = ("guidance_upper_bias",)
        notes = (
            f"guidance midpoint proxy span {point:g} +/- {width:g}; base uses upper-half "
            "position because explicit endpoints are not fields in Contract C"
        )

    citation = EvidenceCitation(
        source=anchor["source"],
        published_at=anchor["published_at"],
        quote=anchor["quote"],
    )
    return GuardrailBand(
        metric_id=anchor["metric_id"],
        unit=anchor["unit"],
        basis=anchor["basis"],
        low=low,
        base=base,
        high=high,
        methods=methods,
        evidence=(citation,),
        notes=notes,
    )


def anchor_bands(
    consensus: dict,
    *,
    as_of: str,
    half_widths: dict[str, float] | None = None,
) -> tuple[GuardrailBand, ...]:
    """Build point-in-time anchor bands, rejecting duplicate kinds per metric."""
    if not isinstance(consensus, dict):
        raise GuardrailError("consensus document must be an object")
    anchors = consensus.get("anchors")
    if not isinstance(anchors, list):
        raise GuardrailError("consensus.anchors must be a list")
    cutoff = _iso_date(as_of, "anchor cutoff")
    overrides = half_widths or {}
    seen: set[tuple[str, str]] = set()
    bands = []
    for index, anchor in enumerate(anchors, 1):
        if not isinstance(anchor, dict):
            raise GuardrailError(f"anchor {index} must be an object")
        metric_id = anchor.get("metric_id")
        kind = anchor.get("kind")
        identity = (metric_id, kind)
        if identity in seen:
            raise GuardrailError(f"duplicate {kind!r} anchor for metric {metric_id!r}")
        seen.add(identity)
        published = _iso_date(anchor.get("published_at"), f"anchor {index}")
        if published > cutoff:
            continue
        bands.append(anchor_band(anchor, half_width=overrides.get(metric_id)))
    return tuple(bands)


BASE_PRIORITY = (
    "consensus_anchor",
    "guidance_upper_bias",
    "yoy_trend_band",
    "seasonal_naive_band",
)


def _base_method(band: GuardrailBand) -> str:
    matches = [method for method in BASE_PRIORITY if method in band.methods]
    if len(matches) != 1:
        raise GuardrailError(
            f"{band.metric_id}: band must identify exactly one base method from {BASE_PRIORITY}"
        )
    return matches[0]


def combine_metric_bands(
    bands: tuple[GuardrailBand, ...] | list[GuardrailBand],
    *,
    unavailable: tuple[str, ...] = (),
) -> GuardrailBand:
    """Combine available method bands with fixed base priority and a union envelope."""
    if not bands:
        raise GuardrailError("cannot combine an empty band collection")
    first = bands[0]
    if not isinstance(first, GuardrailBand):
        raise GuardrailError("all combined bands must be GuardrailBand instances")

    identities: set[str] = set()
    for band in bands:
        if not isinstance(band, GuardrailBand):
            raise GuardrailError("all combined bands must be GuardrailBand instances")
        if (band.metric_id, band.unit, band.basis) != (first.metric_id, first.unit, first.basis):
            raise GuardrailError(
                f"{first.metric_id}: cannot combine mismatched metric/unit/basis band "
                f"{band.metric_id}/{band.unit}/{band.basis}"
            )
        if not (band.low <= band.base <= band.high):
            raise GuardrailError(
                f"{band.metric_id}: invalid component band {band.low}/{band.base}/{band.high}"
            )
        method = _base_method(band)
        if method in identities:
            raise GuardrailError(f"{band.metric_id}: duplicate component band {method}")
        identities.add(method)

    selected_method = next(method for method in BASE_PRIORITY if method in identities)
    selected = next(band for band in bands if selected_method in band.methods)
    low = min(band.low for band in bands)
    high = max(band.high for band in bands)

    methods: list[str] = []
    evidence: list[EvidenceCitation] = []
    seen_evidence: set[tuple[str, str, str]] = set()
    for band in bands:
        for method in band.methods:
            if method not in methods:
                methods.append(method)
        for citation in band.evidence:
            identity = (citation.source, citation.published_at, citation.quote)
            if identity not in seen_evidence:
                seen_evidence.add(identity)
                evidence.append(citation)

    unavailable_text = ", ".join(unavailable) if unavailable else "none"
    component_text = ", ".join(_base_method(band) for band in bands)
    return GuardrailBand(
        metric_id=first.metric_id,
        unit=first.unit,
        basis=first.basis,
        low=low,
        base=selected.base,
        high=high,
        methods=tuple(methods),
        evidence=tuple(evidence),
        notes=(
            f"base selected by fixed priority: {selected_method}; union envelope from "
            f"{component_text}; unavailable: {unavailable_text}"
        ),
    )


def build_ranges_document(
    timeseries: dict,
    consensus: dict,
    *,
    target_period: str,
    as_of: str,
    minimum_half_widths: dict[str, float] | None = None,
    anchor_half_widths: dict[str, float] | None = None,
) -> dict:
    """Build the complete closed Contract E document for one company."""
    if not isinstance(timeseries, dict):
        raise GuardrailError("timeseries must be an object")
    company_id = timeseries.get("company_id")
    if not isinstance(company_id, str) or not company_id:
        raise GuardrailError("timeseries.company_id must be a non-empty string")
    if not isinstance(consensus, dict):
        raise GuardrailError("consensus document must be an object")
    consensus_company = consensus.get("company_id")
    if consensus_company != company_id:
        raise GuardrailError(
            f"company_id mismatch: timeseries={company_id!r}, consensus={consensus_company!r}"
        )

    minimums = minimum_half_widths or {}
    _, matching = _matching_series(timeseries, target_period)
    series_by_metric = {series["metric_id"]: series for series in matching}
    anchors = anchor_bands(
        consensus,
        as_of=as_of,
        half_widths=anchor_half_widths,
    )
    anchor_by_metric: dict[str, list[GuardrailBand]] = {}
    for band in anchors:
        if band.metric_id not in series_by_metric:
            raise GuardrailError(
                f"anchor metric {band.metric_id!r} has no matching {target_period} time series"
            )
        anchor_by_metric.setdefault(band.metric_id, []).append(band)

    ranges = []
    for series in matching:
        metric_id = series["metric_id"]
        unavailable = []
        component_bands = [
            seasonal_naive_band(
                seasonal_naive_for_series(series, target_period),
                minimum_half_width=minimums.get(metric_id),
            )
        ]
        try:
            component_bands.append(
                yoy_trend_band_for_series(
                    series,
                    target_period,
                    minimum_half_width=minimums.get(metric_id),
                )
            )
        except InsufficientHistoryError as exc:
            unavailable.append(f"yoy_trend_band ({exc})")

        metric_anchors = anchor_by_metric.get(metric_id, [])
        component_bands.extend(metric_anchors)
        anchor_methods = {_base_method(band) for band in metric_anchors}
        if "consensus_anchor" not in anchor_methods:
            unavailable.append("consensus_anchor")
        if "guidance_upper_bias" not in anchor_methods:
            unavailable.append("guidance_upper_bias")

        combined = combine_metric_bands(
            component_bands,
            unavailable=tuple(unavailable),
        )
        ranges.append(combined.as_range())

    return {"schema_version": 1, "company_id": company_id, "ranges": ranges}
