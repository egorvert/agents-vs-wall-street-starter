from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from pipeline.quant.guardrails import (
    GuardrailError,
    seasonal_naive_band,
    seasonal_naive_baselines,
    seasonal_naive_bands,
    seasonal_naive_for_series,
    yoy_trend_band_for_series,
    yoy_trend_bands,
)


REPO = Path(__file__).resolve().parents[3]


def point(period: str, value: object) -> dict:
    return {
        "period": period,
        "value": value,
        "source": "evidence/source.md",
        "published_at": "2025-01-01",
        "quote": f"reported {value}",
    }


def series(
    points: list[dict],
    *,
    metric_id: str = "metric",
    unit: str = "USDm",
    basis: str = "as-reported",
    period_type: str = "Q",
) -> dict:
    return {
        "metric_id": metric_id,
        "unit": unit,
        "basis": basis,
        "period_type": period_type,
        "points": points,
    }


class HdBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeseries = json.loads((REPO / "fixtures" / "HD" / "timeseries.json").read_text())
        self.estimates = {
            estimate.metric_id: estimate
            for estimate in seasonal_naive_baselines(self.timeseries, "FY2026Q2")
        }

    def test_builds_all_three_hd_b0_estimates(self) -> None:
        self.assertEqual(
            set(self.estimates),
            {"hd_net_sales", "hd_adj_eps", "hd_comp_sales"},
        )

    def test_money_and_eps_extend_trailing_yoy(self) -> None:
        sales = self.estimates["hd_net_sales"]
        eps = self.estimates["hd_adj_eps"]
        self.assertAlmostEqual(sales.value, 45277.0 * (45277.0 / 43175.0))
        self.assertAlmostEqual(eps.value, 4.68 * (4.68 / 4.67))
        self.assertEqual(sales.method, "seasonal_naive_trailing_yoy")
        self.assertEqual(sales.comparable_periods, ("FY2024Q2", "FY2025Q2"))

    def test_percentage_metric_uses_additive_percentage_points(self) -> None:
        comp = self.estimates["hd_comp_sales"]
        self.assertAlmostEqual(comp.value, 5.3)
        self.assertAlmostEqual(comp.trend, 4.3)
        self.assertEqual(comp.method, "seasonal_naive_additive_drift")

    def test_builds_hd_seasonal_bands_from_move_and_floor(self) -> None:
        bands = {
            band.metric_id: band
            for band in seasonal_naive_bands(self.timeseries, "FY2026Q2")
        }

        sales = bands["hd_net_sales"]
        sales_move = abs(self.estimates["hd_net_sales"].value - 45277.0)
        self.assertAlmostEqual(sales.low, sales.base - sales_move)
        self.assertAlmostEqual(sales.high, sales.base + sales_move)

        eps = bands["hd_adj_eps"]
        eps_floor = abs(eps.base) * 0.005
        self.assertAlmostEqual(eps.low, eps.base - eps_floor)
        self.assertAlmostEqual(eps.high, eps.base + eps_floor)

        comp = bands["hd_comp_sales"]
        self.assertAlmostEqual(comp.low, 1.0)
        self.assertAlmostEqual(comp.high, 9.6)
        self.assertEqual(comp.methods[0], "seasonal_naive_band")

    def test_band_serializes_to_the_closed_contract_e_shape(self) -> None:
        band = seasonal_naive_band(self.estimates["hd_adj_eps"])
        output = band.as_range()
        self.assertEqual(
            set(output),
            {"metric_id", "unit", "basis", "low", "base", "high", "methods", "evidence", "notes"},
        )
        self.assertEqual(
            set(output["evidence"][0]),
            {"source", "published_at", "quote"},
        )

    def test_hd_fixture_honestly_lacks_independent_trend_history(self) -> None:
        with self.assertRaisesRegex(GuardrailError, "requires at least 3 comparable periods"):
            yoy_trend_bands(self.timeseries, "FY2026Q2")


class SeasonalNaiveRulesTests(unittest.TestCase):
    def test_uses_only_the_same_quarter_and_excludes_target_or_future(self) -> None:
        data = series(
            [
                point("FY2024Q3", 90.0),
                point("FY2025Q2", 999.0),
                point("FY2025Q3", 100.0),
                point("FY2026Q3", 500.0),
                point("FY2027Q3", 600.0),
            ]
        )
        estimate = seasonal_naive_for_series(data, "FY2026Q3")
        self.assertAlmostEqual(estimate.value, 100.0 * (100.0 / 90.0))
        self.assertEqual(estimate.comparable_periods, ("FY2024Q3", "FY2025Q3"))

    def test_one_observation_falls_back_to_last_comparable(self) -> None:
        estimate = seasonal_naive_for_series(series([point("FY2025Q3", 100.0)]), "FY2026Q3")
        self.assertEqual(estimate.value, 100.0)
        self.assertIsNone(estimate.trend)
        self.assertEqual(estimate.method, "seasonal_naive_last_comparable")

    def test_non_positive_levels_use_additive_drift(self) -> None:
        estimate = seasonal_naive_for_series(
            series([point("FY2024Q3", -2.0), point("FY2025Q3", 1.0)], unit="GBp"),
            "FY2026Q3",
        )
        self.assertEqual(estimate.value, 4.0)
        self.assertEqual(estimate.method, "seasonal_naive_additive_drift")

    def test_hays_full_year_target_ignores_half_year_series(self) -> None:
        timeseries = {
            "company_id": "HAS",
            "series": [
                series(
                    [point("FY2024", 100.0), point("FY2025", 110.0)],
                    metric_id="has_net_fees",
                    unit="GBPm",
                    period_type="FY",
                ),
                series(
                    [point("FY2025H1", 50.0)],
                    metric_id="has_net_fees",
                    unit="GBPm",
                    period_type="H1",
                ),
                series(
                    [point("FY2025H2", 60.0)],
                    metric_id="has_net_fees",
                    unit="GBPm",
                    period_type="H2",
                ),
            ],
        }
        estimates = seasonal_naive_baselines(timeseries, "FY2026")
        self.assertEqual(len(estimates), 1)
        self.assertEqual(estimates[0].comparable_periods, ("FY2024", "FY2025"))

    def test_rejects_series_and_point_period_type_mismatches(self) -> None:
        with self.assertRaisesRegex(GuardrailError, "does not match target"):
            seasonal_naive_for_series(
                series([point("FY2025Q2", 10.0)], period_type="Q"),
                "FY2026",
            )
        with self.assertRaisesRegex(GuardrailError, "not series type"):
            seasonal_naive_for_series(
                series([point("FY2025", 10.0)], period_type="Q"),
                "FY2026Q2",
            )

    def test_rejects_duplicate_periods_and_duplicate_metric_series(self) -> None:
        duplicate_points = series([point("FY2025Q2", 10.0), point("FY2025Q2", 10.0)])
        with self.assertRaisesRegex(GuardrailError, "duplicate period"):
            seasonal_naive_for_series(duplicate_points, "FY2026Q2")

        valid_series = series([point("FY2025Q2", 10.0)])
        duplicate_series = {"series": [valid_series, valid_series]}
        with self.assertRaisesRegex(GuardrailError, "duplicate Q series"):
            seasonal_naive_baselines(duplicate_series, "FY2026Q2")

    def test_rejects_non_finite_values_and_missing_evidence(self) -> None:
        for value in (True, math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(GuardrailError, "finite number"):
                    seasonal_naive_for_series(series([point("FY2025Q2", value)]), "FY2026Q2")

        missing = point("FY2025Q2", 10.0)
        del missing["quote"]
        with self.assertRaisesRegex(GuardrailError, "missing evidence"):
            seasonal_naive_for_series(series([missing]), "FY2026Q2")

    def test_rejects_when_no_prior_comparable_period_exists(self) -> None:
        with self.assertRaisesRegex(GuardrailError, "no prior Q2 observation"):
            seasonal_naive_for_series(series([point("FY2025Q1", 10.0)]), "FY2026Q2")

    def test_wraps_malformed_period_and_series_errors(self) -> None:
        with self.assertRaisesRegex(GuardrailError, "non-canonical period"):
            seasonal_naive_for_series(series([point("2025 Q2", 10.0)]), "FY2026Q2")
        with self.assertRaisesRegex(GuardrailError, "must be an object"):
            seasonal_naive_baselines({"series": ["not-a-series"]}, "FY2026Q2")

    def test_one_point_band_uses_the_minimum_floor(self) -> None:
        estimate = seasonal_naive_for_series(series([point("FY2025Q2", 100.0)]), "FY2026Q2")
        band = seasonal_naive_band(estimate)
        self.assertEqual((band.low, band.base, band.high), (99.5, 100.0, 100.5))

    def test_zero_level_requires_an_explicit_minimum(self) -> None:
        estimate = seasonal_naive_for_series(series([point("FY2025Q2", 0.0)]), "FY2026Q2")
        with self.assertRaisesRegex(GuardrailError, "requires an explicit"):
            seasonal_naive_band(estimate)
        band = seasonal_naive_band(estimate, minimum_half_width=1.0)
        self.assertEqual((band.low, band.base, band.high), (-1.0, 0.0, 1.0))

    def test_rejects_invalid_explicit_minimum_widths(self) -> None:
        estimate = seasonal_naive_for_series(series([point("FY2025Q2", 100.0)]), "FY2026Q2")
        for width in (True, 0, -1, math.nan, math.inf):
            with self.subTest(width=width):
                with self.assertRaisesRegex(GuardrailError, "positive finite"):
                    seasonal_naive_band(estimate, minimum_half_width=width)


class YoyTrendBandTests(unittest.TestCase):
    def test_positive_levels_use_median_growth_and_observed_envelope(self) -> None:
        data = series(
            [
                point("FY2023Q2", 100.0),
                point("FY2024Q2", 110.0),
                point("FY2025Q2", 132.0),
            ]
        )
        band = yoy_trend_band_for_series(data, "FY2026Q2")
        self.assertAlmostEqual(band.base, 132.0 * 1.15)
        self.assertAlmostEqual(band.low, 132.0 * 1.10)
        self.assertAlmostEqual(band.high, 132.0 * 1.20)
        self.assertEqual(band.methods, ("yoy_trend_band", "yoy_trend_median_growth"))
        self.assertEqual(len(band.evidence), 3)

    def test_percentages_use_median_point_change(self) -> None:
        data = series(
            [
                point("FY2023Q2", -2.0),
                point("FY2024Q2", 1.0),
                point("FY2025Q2", 3.0),
            ],
            unit="%",
        )
        band = yoy_trend_band_for_series(data, "FY2026Q2")
        self.assertEqual((band.low, band.base, band.high), (5.0, 5.5, 6.0))
        self.assertEqual(band.methods, ("yoy_trend_band", "yoy_trend_median_change"))

    def test_median_resists_one_growth_outlier(self) -> None:
        data = series(
            [
                point("FY2022Q2", 100.0),
                point("FY2023Q2", 110.0),
                point("FY2024Q2", 121.0),
                point("FY2025Q2", 242.0),
            ]
        )
        band = yoy_trend_band_for_series(data, "FY2026Q2")
        self.assertAlmostEqual(band.base, 242.0 * 1.10)
        self.assertAlmostEqual(band.high, 242.0 * 2.0)

    def test_identical_changes_expand_to_the_minimum_width(self) -> None:
        data = series(
            [
                point("FY2023Q2", 100.0),
                point("FY2024Q2", 110.0),
                point("FY2025Q2", 121.0),
            ]
        )
        band = yoy_trend_band_for_series(data, "FY2026Q2")
        minimum = abs(band.base) * 0.005
        self.assertAlmostEqual(band.low, band.base - minimum)
        self.assertAlmostEqual(band.high, band.base + minimum)

    def test_non_positive_levels_switch_to_additive_changes(self) -> None:
        data = series(
            [
                point("FY2023Q2", -3.0),
                point("FY2024Q2", -1.0),
                point("FY2025Q2", 2.0),
            ],
            unit="GBp",
        )
        band = yoy_trend_band_for_series(data, "FY2026Q2")
        self.assertEqual((band.low, band.base, band.high), (4.0, 4.5, 5.0))
        self.assertEqual(band.methods[1], "yoy_trend_median_change")

    def test_requires_two_independent_changes(self) -> None:
        data = series([point("FY2024Q2", 100.0), point("FY2025Q2", 110.0)])
        with self.assertRaisesRegex(GuardrailError, "requires at least 3 comparable periods"):
            yoy_trend_band_for_series(data, "FY2026Q2")

    def test_group_builder_keeps_hays_period_types_separate(self) -> None:
        fy = series(
            [point("FY2023", 100.0), point("FY2024", 110.0), point("FY2025", 121.0)],
            metric_id="has_net_fees",
            unit="GBPm",
            period_type="FY",
        )
        h1 = series(
            [point("FY2023H1", 40.0), point("FY2024H1", 45.0), point("FY2025H1", 50.0)],
            metric_id="has_net_fees",
            unit="GBPm",
            period_type="H1",
        )
        bands = yoy_trend_bands({"series": [fy, h1]}, "FY2026")
        self.assertEqual(len(bands), 1)
        self.assertEqual(tuple(point.period for point in bands[0].evidence), ("FY2023", "FY2024", "FY2025"))

    def test_trend_band_serializes_to_contract_e_fields(self) -> None:
        data = series(
            [point("FY2023Q2", 100.0), point("FY2024Q2", 110.0), point("FY2025Q2", 121.0)]
        )
        output = yoy_trend_band_for_series(data, "FY2026Q2").as_range()
        self.assertEqual(
            set(output),
            {"metric_id", "unit", "basis", "low", "base", "high", "methods", "evidence", "notes"},
        )


if __name__ == "__main__":
    unittest.main()
