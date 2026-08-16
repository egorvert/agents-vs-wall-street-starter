from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pipeline.quant.build_ranges import main, write_ranges
from pipeline.quant.guardrails import (
    GuardrailBand,
    GuardrailError,
    build_ranges_document,
    combine_metric_bands,
)


REPO = Path(__file__).resolve().parents[3]


def citation() -> tuple:
    from pipeline.quant.guardrails import EvidenceCitation

    return (
        EvidenceCitation(
            source="evidence/source.md",
            published_at="2026-01-01",
            quote="reported value",
        ),
    )


def band(
    method: str,
    *,
    low: float,
    base: float,
    high: float,
    metric_id: str = "metric",
    unit: str = "USDm",
    basis: str = "as-reported",
) -> GuardrailBand:
    return GuardrailBand(
        metric_id=metric_id,
        unit=unit,
        basis=basis,
        low=low,
        base=base,
        high=high,
        methods=(method,),
        evidence=citation(),
        notes=method,
    )


def point(period: str, value: float) -> dict:
    return {
        "period": period,
        "value": value,
        "source": "evidence/source.md",
        "published_at": "2025-01-01",
        "quote": f"reported {value}",
    }


class BandCombinationTests(unittest.TestCase):
    def test_fixed_base_priority_and_union_envelope(self) -> None:
        seasonal = band("seasonal_naive_band", low=90.0, base=100.0, high=110.0)
        trend = band("yoy_trend_band", low=95.0, base=105.0, high=115.0)
        guidance = band("guidance_upper_bias", low=98.0, base=108.0, high=112.0)
        consensus = band("consensus_anchor", low=102.0, base=104.0, high=106.0)
        combined = combine_metric_bands([seasonal, trend, guidance, consensus])
        self.assertEqual((combined.low, combined.base, combined.high), (90.0, 104.0, 115.0))
        self.assertIn("consensus_anchor", combined.notes)

    def test_priority_falls_through_in_documented_order(self) -> None:
        seasonal = band("seasonal_naive_band", low=90.0, base=100.0, high=110.0)
        trend = band("yoy_trend_band", low=95.0, base=105.0, high=115.0)
        guidance = band("guidance_upper_bias", low=98.0, base=108.0, high=112.0)
        self.assertEqual(combine_metric_bands([seasonal, trend, guidance]).base, 108.0)
        self.assertEqual(combine_metric_bands([seasonal, trend]).base, 105.0)
        self.assertEqual(combine_metric_bands([seasonal]).base, 100.0)

    def test_deduplicates_shared_evidence(self) -> None:
        first = band("seasonal_naive_band", low=90.0, base=100.0, high=110.0)
        second = band("yoy_trend_band", low=95.0, base=105.0, high=115.0)
        combined = combine_metric_bands([first, second])
        self.assertEqual(len(combined.evidence), 1)

    def test_rejects_empty_mismatched_duplicate_and_invalid_bands(self) -> None:
        valid = band("seasonal_naive_band", low=90.0, base=100.0, high=110.0)
        cases = [
            ([], "empty"),
            ([valid, band("yoy_trend_band", low=90, base=100, high=110, unit="%")], "mismatched"),
            ([valid, valid], "duplicate component"),
            ([band("seasonal_naive_band", low=110, base=100, high=90)], "invalid component"),
        ]
        for values, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(GuardrailError, message):
                    combine_metric_bands(values)


class RangeDocumentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeseries = json.loads((REPO / "fixtures" / "HD" / "timeseries.json").read_text())
        self.consensus = json.loads((REPO / "fixtures" / "HD" / "consensus.json").read_text())

    def test_builds_all_hd_ranges_with_fixed_priority(self) -> None:
        document = build_ranges_document(
            self.timeseries,
            self.consensus,
            target_period="FY2026Q2",
            as_of="2026-08-16",
        )
        ranges = {item["metric_id"]: item for item in document["ranges"]}
        self.assertEqual(document["company_id"], "HD")
        self.assertEqual(set(ranges), {"hd_net_sales", "hd_adj_eps", "hd_comp_sales"})
        self.assertAlmostEqual(ranges["hd_net_sales"]["base"], 45277.0 * (45277.0 / 43175.0))
        self.assertAlmostEqual(ranges["hd_adj_eps"]["base"], 4.68 * (4.68 / 4.67))
        self.assertEqual(ranges["hd_comp_sales"]["base"], 1.5)
        self.assertEqual(ranges["hd_comp_sales"]["low"], 0.0)
        self.assertEqual(ranges["hd_comp_sales"]["high"], 3.0)  # damped %-drift (16:45) — Rachel to review
        self.assertIn("guidance_upper_bias", ranges["hd_comp_sales"]["methods"])
        self.assertIn("yoy_trend_band", ranges["hd_net_sales"]["notes"])

    def test_range_entries_have_the_closed_contract_e_shape(self) -> None:
        document = build_ranges_document(
            self.timeseries,
            self.consensus,
            target_period="FY2026Q2",
            as_of="2026-08-16",
        )
        expected = {"metric_id", "unit", "basis", "low", "base", "high", "methods", "evidence", "notes"}
        self.assertTrue(all(set(item) == expected for item in document["ranges"]))

    def test_rejects_company_unit_and_unknown_anchor_metric_mismatches(self) -> None:
        wrong_company = dict(self.consensus, company_id="ADI")
        with self.assertRaisesRegex(GuardrailError, "company_id mismatch"):
            build_ranges_document(
                self.timeseries, wrong_company, target_period="FY2026Q2", as_of="2026-08-16"
            )

        wrong_unit = json.loads(json.dumps(self.consensus))
        wrong_unit["anchors"][0]["unit"] = "USDm"
        with self.assertRaisesRegex(GuardrailError, "mismatched metric/unit/basis"):
            build_ranges_document(
                self.timeseries, wrong_unit, target_period="FY2026Q2", as_of="2026-08-16"
            )

        unknown = json.loads(json.dumps(self.consensus))
        unknown["anchors"][0]["metric_id"] = "unknown_metric"
        with self.assertRaisesRegex(GuardrailError, "no matching"):
            build_ranges_document(
                self.timeseries, unknown, target_period="FY2026Q2", as_of="2026-08-16"
            )

    def test_post_cutoff_anchor_is_unavailable_not_leaked(self) -> None:
        future = json.loads(json.dumps(self.consensus))
        future["anchors"][0]["published_at"] = "2026-08-17"
        document = build_ranges_document(
            self.timeseries,
            future,
            target_period="FY2026Q2",
            as_of="2026-08-16",
        )
        comp = next(item for item in document["ranges"] if item["metric_id"] == "hd_comp_sales")
        self.assertAlmostEqual(comp["base"], 2.0)  # damped %-drift (16:45) — Rachel to review
        self.assertIn("guidance_upper_bias", comp["notes"])

    def test_write_ranges_is_byte_stable(self) -> None:
        document = build_ranges_document(
            self.timeseries,
            self.consensus,
            target_period="FY2026Q2",
            as_of="2026-08-16",
        )
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.json"
            second = Path(temp) / "second.json"
            write_ranges(first, document)
            write_ranges(second, document)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_cli_materializes_the_fixture_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "ranges.json"
            result = main(
                [
                    "--company",
                    "HD",
                    "--as-of",
                    "2026-08-16",
                    "--target-period",
                    "FY2026Q2",
                    "--repo-root",
                    str(REPO),
                    "--timeseries",
                    "fixtures/HD/timeseries.json",
                    "--consensus",
                    "fixtures/HD/consensus.json",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(result, 0)
            document = json.loads(output.read_text())
            self.assertEqual(len(document["ranges"]), 3)

    def test_cli_runs_as_a_direct_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "ranges.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "pipeline" / "quant" / "build_ranges.py"),
                    "--company",
                    "HD",
                    "--as-of",
                    "2026-08-16",
                    "--target-period",
                    "FY2026Q2",
                    "--repo-root",
                    str(REPO),
                    "--timeseries",
                    "fixtures/HD/timeseries.json",
                    "--consensus",
                    "fixtures/HD/consensus.json",
                    "--output",
                    str(output),
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(output.read_text())["ranges"]), 3)


class AllCompanyContractReadinessTests(unittest.TestCase):
    def test_all_twelve_manifest_metrics_materialize_exact_contract_ranges(self) -> None:
        manifest = json.loads((REPO / "schemas" / "metrics.json").read_text())["companies"]

        for company_id, company in manifest.items():
            with self.subTest(company_id=company_id):
                target_period = company["period"]
                if company["period_type"] == "Q":
                    suffix = target_period[-2:]
                    historical_periods = [f"FY{year}{suffix}" for year in (2023, 2024, 2025)]
                else:
                    historical_periods = [f"FY{year}" for year in (2023, 2024, 2025)]

                series = []
                for metric_index, metric in enumerate(company["metrics"], start=1):
                    start = 10.0 * metric_index if metric["unit"] in {"%", "GBp"} else 1000.0 * metric_index
                    series.append(
                        {
                            "metric_id": metric["metric_id"],
                            "unit": metric["unit"],
                            "basis": metric["basis"],
                            "period_type": company["period_type"],
                            "points": [
                                point(period, start + offset)
                                for offset, period in enumerate(historical_periods)
                            ],
                        }
                    )

                document = build_ranges_document(
                    {"schema_version": 1, "company_id": company_id, "series": series},
                    {
                        "schema_version": 1,
                        "company_id": company_id,
                        "retrieved_at": "2026-08-16T10:00:00+01:00",
                        "anchors": [],
                    },
                    target_period=target_period,
                    as_of="2026-08-16",
                )
                ranges = {item["metric_id"]: item for item in document["ranges"]}

                self.assertEqual(document["company_id"], company_id)
                self.assertEqual(set(ranges), {metric["metric_id"] for metric in company["metrics"]})
                for metric in company["metrics"]:
                    item = ranges[metric["metric_id"]]
                    self.assertEqual(item["unit"], metric["unit"])
                    self.assertEqual(item["basis"], metric["basis"])
                    self.assertLessEqual(item["low"], item["base"])
                    self.assertLessEqual(item["base"], item["high"])
                    self.assertIn("seasonal_naive_band", item["methods"])
                    self.assertIn("yoy_trend_band", item["methods"])


if __name__ == "__main__":
    unittest.main()
