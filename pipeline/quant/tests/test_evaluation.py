from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from pipeline.quant.evaluation import (
    ActualObservation,
    EvaluationError,
    load_event_manifest,
    official_floor,
    score_event,
    score_metric,
    summarize_config,
    validate_event_manifest,
)


REPO = Path(__file__).resolve().parents[3]


def hd_event_document() -> dict:
    timeseries = json.loads((REPO / "fixtures" / "HD" / "timeseries.json").read_text())
    actuals = []
    for series in timeseries["series"]:
        point = next(point for point in series["points"] if point["period"] == "FY2025Q2")
        actuals.append(
            {
                "metric_id": series["metric_id"],
                "value": point["value"],
                "unit": series["unit"],
                "basis": series["basis"],
                "source": point["source"],
                "published_at": point["published_at"],
                "quote": point["quote"],
            }
        )
    return {
        "schema_version": 1,
        "event_id": "HD-FY2025Q2",
        "company_id": "HD",
        "target_period": "FY2025Q2",
        "as_of": "2025-08-18",
        "actuals": actuals,
    }


def observation(
    *,
    value: float = 100.0,
    unit: str = "%",
    metric_id: str = "metric",
) -> ActualObservation:
    return ActualObservation(
        metric_id=metric_id,
        value=value,
        unit=unit,
        basis="as-reported",
        source="evidence/source.md",
        published_at="2026-01-02",
        quote="reported value",
    )


def metric_score(
    *,
    metric_id: str,
    actual: float,
    forecast: object,
    proxy: float,
    unit: str = "%",
    bounds: tuple[float | None, float | None] = (None, None),
):
    return score_metric(
        event_id=f"event-{metric_id}",
        company_id="HD",
        target_period="FY2025Q2",
        config_id="candidate",
        actual=observation(value=actual, unit=unit, metric_id=metric_id),
        forecast=forecast,
        proxy=proxy,
        range_low=bounds[0],
        range_high=bounds[1],
    )


class HistoricalEventManifestTests(unittest.TestCase):
    def test_validates_cited_held_out_hd_actuals(self) -> None:
        event = validate_event_manifest(hd_event_document(), REPO)
        self.assertEqual(event.event_id, "HD-FY2025Q2")
        self.assertEqual(len(event.actuals), 3)
        self.assertEqual(
            {actual.metric_id for actual in event.actuals},
            {"hd_net_sales", "hd_adj_eps", "hd_comp_sales"},
        )

    def test_loads_a_manifest_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "event.json"
            path.write_text(json.dumps(hd_event_document()), encoding="utf-8")
            event = load_event_manifest(path, REPO)
        self.assertEqual(event.company_id, "HD")

    def test_rejects_non_closed_or_wrong_version_manifests(self) -> None:
        cases = []
        extra = hd_event_document()
        extra["future_answer"] = 1
        cases.append((extra, "fields are not closed"))
        version = hd_event_document()
        version["schema_version"] = 2
        cases.append((version, "schema_version"))
        missing = hd_event_document()
        del missing["as_of"]
        cases.append((missing, "fields are not closed"))
        for document, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(EvaluationError, message):
                    validate_event_manifest(document, REPO)

    def test_rejects_actuals_that_are_not_truly_held_out(self) -> None:
        document = hd_event_document()
        document["as_of"] = "2025-08-19"
        with self.assertRaisesRegex(EvaluationError, "not held out"):
            validate_event_manifest(document, REPO)

    def test_rejects_duplicate_unknown_and_mismatched_metrics(self) -> None:
        duplicate = hd_event_document()
        duplicate["actuals"].append(dict(duplicate["actuals"][0]))
        unknown = hd_event_document()
        unknown["actuals"][0]["metric_id"] = "unknown_metric"
        wrong_unit = hd_event_document()
        wrong_unit["actuals"][0]["unit"] = "%"
        cases = [
            (duplicate, "duplicate actual"),
            (unknown, "unknown for HD"),
            (wrong_unit, "metric manifest"),
        ]
        for document, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(EvaluationError, message):
                    validate_event_manifest(document, REPO)

    def test_rejects_unverifiable_actual_citations(self) -> None:
        document = hd_event_document()
        document["actuals"][0]["quote"] = "a sentence that is not in the filing"
        with self.assertRaisesRegex(EvaluationError, "quote is not present"):
            validate_event_manifest(document, REPO)


class OfficialScoreTests(unittest.TestCase):
    def test_uses_the_percentage_and_money_floors(self) -> None:
        self.assertEqual(official_floor(4.0, "%"), 0.5)
        self.assertEqual(official_floor(200.0, "USDm"), 1.0)
        self.assertEqual(official_floor(-2.0, "USD / share"), 0.01)

    def test_zero_money_result_requires_an_explicit_fallback(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "explicit zero_result_floor"):
            official_floor(0.0, "USDm")
        self.assertEqual(official_floor(0.0, "USDm", zero_result_floor=0.25), 0.25)
        with self.assertRaisesRegex(EvaluationError, "greater than zero"):
            official_floor(0.0, "USDm", zero_result_floor=0.0)

    def test_matches_the_judging_worked_example(self) -> None:
        result = metric_score(metric_id="sales", actual=110.0, forecast=106.0, proxy=100.0)
        self.assertAlmostEqual(result.official_score, 0.4)
        self.assertEqual(result.proxy_score, 1.0)
        self.assertEqual(result.outcome_vs_proxy, "win")

    def test_floor_can_make_the_proxy_score_less_than_one(self) -> None:
        result = metric_score(metric_id="margin", actual=10.0, forecast=10.1, proxy=10.2)
        self.assertAlmostEqual(result.official_score, 0.2)
        self.assertAlmostEqual(result.proxy_score, 0.4)
        self.assertEqual(result.outcome_vs_proxy, "win")

    def test_caps_large_misses_and_penalizes_missing_or_invalid_forecasts(self) -> None:
        large = metric_score(metric_id="large", actual=10.0, forecast=100.0, proxy=9.0)
        missing = metric_score(metric_id="missing", actual=10.0, forecast=None, proxy=9.0)
        invalid = metric_score(metric_id="invalid", actual=10.0, forecast=math.nan, proxy=9.0)
        self.assertEqual(large.official_score, 5.0)
        self.assertEqual((missing.official_score, missing.status), (5.0, "missing_forecast"))
        self.assertEqual((invalid.official_score, invalid.status), (5.0, "invalid_forecast"))

    def test_reports_range_coverage_and_sharpness(self) -> None:
        result = metric_score(
            metric_id="margin",
            actual=10.0,
            forecast=10.1,
            proxy=9.0,
            bounds=(9.5, 10.5),
        )
        self.assertTrue(result.actual_in_range)
        self.assertEqual(result.range_width_in_floors, 2.0)
        with self.assertRaisesRegex(EvaluationError, "supplied together"):
            metric_score(
                metric_id="bad-range",
                actual=10.0,
                forecast=10.0,
                proxy=9.0,
                bounds=(9.5, None),
            )


class EventAndSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.event = validate_event_manifest(hd_event_document(), REPO)
        self.proxies = {actual.metric_id: actual.value - 1.0 for actual in self.event.actuals}

    def test_scores_missing_forecasts_instead_of_dropping_them(self) -> None:
        first = self.event.actuals[0]
        results = score_event(
            self.event,
            config_id="partial",
            forecasts={first.metric_id: first.value},
            proxies=self.proxies,
        )
        self.assertEqual(len(results), 3)
        self.assertEqual(sum(item.status == "missing_forecast" for item in results), 2)

    def test_rejects_unknown_metrics_and_missing_proxies(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "unknown event metrics"):
            score_event(
                self.event,
                config_id="bad",
                forecasts={"not_a_metric": 1.0},
                proxies=self.proxies,
            )
        with self.assertRaisesRegex(EvaluationError, "proxies are missing"):
            score_event(self.event, config_id="bad", forecasts={}, proxies={})

    def test_summarizes_paired_scores_without_hiding_failures(self) -> None:
        results = [
            metric_score(metric_id="win", actual=110.0, forecast=106.0, proxy=100.0),
            metric_score(metric_id="tie", actual=110.0, forecast=100.0, proxy=100.0),
            metric_score(metric_id="missing", actual=110.0, forecast=None, proxy=100.0),
        ]
        summary = summarize_config(results)
        self.assertAlmostEqual(summary.mean_official_score, (0.4 + 1.0 + 5.0) / 3)
        self.assertEqual(summary.median_official_score, 1.0)
        self.assertEqual(summary.win_rate_vs_proxy, 1 / 3)
        self.assertEqual(summary.tie_rate_vs_proxy, 1 / 3)
        self.assertEqual(summary.capped_score_rate, 1 / 3)
        self.assertEqual(summary.missing_forecasts, 1)

    def test_summary_rejects_mixed_configs_and_duplicate_metrics(self) -> None:
        first = metric_score(metric_id="one", actual=110.0, forecast=106.0, proxy=100.0)
        mixed = score_metric(
            event_id="event-two",
            company_id="HD",
            target_period="FY2025Q2",
            config_id="other",
            actual=observation(metric_id="two", value=110.0),
            forecast=106.0,
            proxy=100.0,
        )
        with self.assertRaisesRegex(EvaluationError, "multiple config_ids"):
            summarize_config([first, mixed])
        with self.assertRaisesRegex(EvaluationError, "duplicate event/metric"):
            summarize_config([first, first])


if __name__ == "__main__":
    unittest.main()
