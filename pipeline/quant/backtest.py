#!/usr/bin/env python3
"""Run deterministic point-in-time forecast configurations on historical events."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.quant.evaluation import (
    ConfigSummary,
    EvaluationError,
    HistoricalEvent,
    MetricEvaluation,
    _require_date,
    _require_finite,
    _require_text,
    _verify_local_quote,
    load_event_manifest,
    score_event,
    summarize_config,
)
from pipeline.quant.guardrails import build_ranges_document, seasonal_naive_baselines


CONFIG_ORDER = (
    "b0_seasonal",
    "b1_anchor",
    "current_ranges_base",
    "blend_b1_25",
    "blend_b1_50",
    "blend_b1_75",
)


@dataclass(frozen=True)
class BacktestCase:
    event: HistoricalEvent
    timeseries: dict
    consensus: dict


@dataclass(frozen=True)
class ProxyUsage:
    event_id: str
    metric_id: str
    kind: str


@dataclass(frozen=True)
class BacktestResult:
    event_ids: tuple[str, ...]
    summaries: tuple[ConfigSummary, ...]
    metric_summaries: tuple[tuple[str, ConfigSummary], ...]
    proxy_usage: tuple[ProxyUsage, ...]
    metrics: tuple[MetricEvaluation, ...]

    def as_dict(self) -> dict:
        return {
            "schema_version": 1,
            "event_ids": list(self.event_ids),
            "configs": [summary.as_dict() for summary in self.summaries],
            "configs_by_metric": [
                {"metric_id": metric_id, **summary.as_dict()}
                for metric_id, summary in self.metric_summaries
            ],
            "proxy_usage": [
                {
                    "event_id": usage.event_id,
                    "metric_id": usage.metric_id,
                    "kind": usage.kind,
                }
                for usage in self.proxy_usage
            ],
            "metrics": [metric.as_dict() for metric in self.metrics],
        }


def _load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationError(f"{label} does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must contain a JSON object")
    return value


def load_backtest_case(case_dir: Path, repo_root: Path) -> BacktestCase:
    directory = Path(case_dir)
    event = load_event_manifest(directory / "event.json", repo_root)
    timeseries = _load_json(directory / "timeseries.json", "backtest timeseries")
    consensus = _load_json(directory / "consensus.json", "backtest consensus")
    case = BacktestCase(event=event, timeseries=timeseries, consensus=consensus)
    audit_forecast_inputs(case, repo_root)
    return case


def _audit_citation(
    value: dict,
    *,
    label: str,
    as_of,
    repo_root: Path,
) -> None:
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must be an object")
    published_text = _require_text(value.get("published_at"), f"{label}.published_at")
    published_at = _require_date(published_text, f"{label}.published_at")
    if published_at > as_of:
        raise EvaluationError(
            f"point-in-time leakage: {label}.published_at {published_text} is after cutoff "
            f"{as_of.isoformat()}"
        )
    source = _require_text(value.get("source"), f"{label}.source")
    quote = _require_text(value.get("quote"), f"{label}.quote")
    _verify_local_quote(repo_root, source, quote, label)


def audit_forecast_inputs(case: BacktestCase, repo_root: Path) -> None:
    """Reject forecast-time inputs that can see the held-out answer or future evidence."""
    event = case.event
    as_of = _require_date(event.as_of, "event.as_of")
    for document, label in ((case.timeseries, "timeseries"), (case.consensus, "consensus")):
        if document.get("company_id") != event.company_id:
            raise EvaluationError(
                f"{label}.company_id {document.get('company_id')!r} != event company "
                f"{event.company_id!r}"
            )

    raw_series = case.timeseries.get("series")
    if not isinstance(raw_series, list) or not raw_series:
        raise EvaluationError("timeseries.series must be a non-empty list")
    for series_index, series in enumerate(raw_series, start=1):
        if not isinstance(series, dict):
            raise EvaluationError(f"timeseries.series[{series_index}] must be an object")
        metric_id = _require_text(
            series.get("metric_id"), f"timeseries.series[{series_index}].metric_id"
        )
        points = series.get("points")
        if not isinstance(points, list) or not points:
            raise EvaluationError(f"timeseries {metric_id} points must be a non-empty list")
        for point_index, point in enumerate(points, start=1):
            label = f"timeseries {metric_id} point[{point_index}]"
            if not isinstance(point, dict):
                raise EvaluationError(f"{label} must be an object")
            period = _require_text(point.get("period"), f"{label}.period")
            if period == event.target_period:
                raise EvaluationError(
                    f"target leakage: {label} includes held-out period {event.target_period}"
                )
            _audit_citation(point, label=label, as_of=as_of, repo_root=repo_root)

    anchors = case.consensus.get("anchors")
    if not isinstance(anchors, list):
        raise EvaluationError("consensus.anchors must be a list")
    for index, anchor in enumerate(anchors, start=1):
        _audit_citation(
            anchor,
            label=f"consensus anchor[{index}]",
            as_of=as_of,
            repo_root=repo_root,
        )


def _b1_forecasts(
    event: HistoricalEvent,
    consensus: dict,
    b0: Mapping[str, float],
) -> tuple[dict[str, float], dict[str, str]]:
    priority = {"consensus": 0, "guidance_midpoint": 1}
    anchors: dict[str, list[dict]] = {}
    for raw in consensus.get("anchors", []):
        if not isinstance(raw, dict):
            raise EvaluationError("consensus anchors must be objects")
        metric_id = _require_text(raw.get("metric_id"), "anchor.metric_id")
        kind = _require_text(raw.get("kind"), f"anchor {metric_id}.kind")
        if kind not in priority:
            raise EvaluationError(f"anchor {metric_id} has unsupported kind {kind!r}")
        anchors.setdefault(metric_id, []).append(raw)

    forecasts = {}
    kinds = {}
    for actual in event.actuals:
        candidates = sorted(
            anchors.get(actual.metric_id, []),
            key=lambda raw: priority[raw["kind"]],
        )
        if candidates:
            forecasts[actual.metric_id] = _require_finite(
                candidates[0].get("value"), f"B1 anchor {actual.metric_id}.value"
            )
            kinds[actual.metric_id] = candidates[0]["kind"]
        elif actual.metric_id in b0:
            forecasts[actual.metric_id] = b0[actual.metric_id]
            kinds[actual.metric_id] = "b0_fallback"
        else:
            raise EvaluationError(f"no B0 or B1 forecast for {actual.metric_id}")
    return forecasts, kinds


def build_case_configurations(
    case: BacktestCase,
) -> tuple[dict[str, dict[str, float]], dict, dict[str, str]]:
    """Compute all deterministic comparison arms from one audited fold."""
    event = case.event
    b0_all = {
        estimate.metric_id: estimate.value
        for estimate in seasonal_naive_baselines(case.timeseries, event.target_period)
    }
    actual_metrics = {actual.metric_id for actual in event.actuals}
    missing_b0 = sorted(actual_metrics - set(b0_all))
    if missing_b0:
        raise EvaluationError(f"B0 is missing held-out metrics: {missing_b0}")
    b0 = {metric_id: b0_all[metric_id] for metric_id in actual_metrics}
    b1, b1_kinds = _b1_forecasts(event, case.consensus, b0)

    ranges_document = build_ranges_document(
        case.timeseries,
        case.consensus,
        target_period=event.target_period,
        as_of=event.as_of,
    )
    ranges_by_metric = {item["metric_id"]: item for item in ranges_document["ranges"]}
    missing_ranges = sorted(actual_metrics - set(ranges_by_metric))
    if missing_ranges:
        raise EvaluationError(f"current range build is missing held-out metrics: {missing_ranges}")
    current = {metric_id: ranges_by_metric[metric_id]["base"] for metric_id in actual_metrics}

    configs = {
        "b0_seasonal": b0,
        "b1_anchor": b1,
        "current_ranges_base": current,
    }
    for anchor_weight in (0.25, 0.50, 0.75):
        config_id = f"blend_b1_{int(anchor_weight * 100):02d}"
        configs[config_id] = {
            metric_id: anchor_weight * b1[metric_id] + (1.0 - anchor_weight) * b0[metric_id]
            for metric_id in actual_metrics
        }
    return configs, ranges_by_metric, b1_kinds


def evaluate_case(case: BacktestCase) -> tuple[tuple[MetricEvaluation, ...], tuple[ProxyUsage, ...]]:
    configs, ranges_by_metric, b1_kinds = build_case_configurations(case)
    proxies = configs["b1_anchor"]
    bounds = {
        metric_id: (item["low"], item["high"])
        for metric_id, item in ranges_by_metric.items()
        if metric_id in proxies
    }
    results = []
    for config_id in CONFIG_ORDER:
        results.extend(
            score_event(
                case.event,
                config_id=config_id,
                forecasts=configs[config_id],
                proxies=proxies,
                ranges=bounds,
            )
        )
    usage = tuple(
        ProxyUsage(event_id=case.event.event_id, metric_id=metric_id, kind=kind)
        for metric_id, kind in sorted(b1_kinds.items())
    )
    return tuple(results), usage


def run_backtest(cases: Sequence[BacktestCase]) -> BacktestResult:
    if not cases:
        raise EvaluationError("backtest requires at least one historical event")
    event_ids = [case.event.event_id for case in cases]
    if len(event_ids) != len(set(event_ids)):
        raise EvaluationError("backtest event_id values must be unique")
    metrics_list = []
    proxy_usage = []
    for case in cases:
        case_metrics, case_usage = evaluate_case(case)
        metrics_list.extend(case_metrics)
        proxy_usage.extend(case_usage)
    metrics = tuple(metrics_list)
    summaries = []
    for config_id in CONFIG_ORDER:
        config_metrics = [metric for metric in metrics if metric.config_id == config_id]
        summaries.append(summarize_config(config_metrics))
    metric_summaries = []
    metric_ids = sorted({metric.metric_id for metric in metrics})
    for config_id in CONFIG_ORDER:
        for metric_id in metric_ids:
            group = [
                metric
                for metric in metrics
                if metric.config_id == config_id and metric.metric_id == metric_id
            ]
            if group:
                metric_summaries.append((metric_id, summarize_config(group)))
    return BacktestResult(
        event_ids=tuple(event_ids),
        summaries=tuple(summaries),
        metric_summaries=tuple(metric_summaries),
        proxy_usage=tuple(proxy_usage),
        metrics=metrics,
    )


def write_results(path: Path, result: BacktestResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.as_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def main(argv: Sequence[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(default_repo))
    parser.add_argument(
        "--case",
        action="append",
        required=True,
        help="event directory containing event.json, timeseries.json and consensus.json; repeatable",
    )
    parser.add_argument("--output", required=True, help="results JSON path")
    args = parser.parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()
        cases = [load_backtest_case(_repo_path(repo_root, value), repo_root) for value in args.case]
        result = run_backtest(cases)
        output = _repo_path(repo_root, args.output)
        write_results(output, result)
    except (EvaluationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {output}")
    print("config                mean    median  win-rate  capped")
    for summary in result.summaries:
        print(
            f"{summary.config_id:<21} {summary.mean_official_score:>6.3f}  "
            f"{summary.median_official_score:>6.3f}  "
            f"{summary.win_rate_vs_proxy:>8.1%}  {summary.capped_score_rate:>6.1%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
