from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from pipeline.quant.extract_timeseries import (
    ExtractionError,
    build_timeseries,
    write_timeseries,
)


REPO = Path(__file__).resolve().parents[3]


class HdFixtureTests(unittest.TestCase):
    def test_builds_committed_hd_fixture_deterministically(self) -> None:
        kwargs = {
            "repo_root": REPO,
            "company_id": "HD",
            "dossier_path": REPO / "fixtures" / "HD" / "research" / "dossier.md",
            "facts_path": REPO / "fixtures" / "HD" / "analysis" / "facts.md",
            "as_of": "2026-08-16",
            "target_period": "FY2026Q2",
        }

        first = build_timeseries(**kwargs)
        second = build_timeseries(**kwargs)

        self.assertEqual(first.document, second.document)
        self.assertEqual(first.document["company_id"], "HD")
        self.assertEqual(
            [series["metric_id"] for series in first.document["series"]],
            ["hd_net_sales", "hd_adj_eps", "hd_comp_sales"],
        )
        self.assertEqual(
            [point["period"] for point in first.document["series"][0]["points"]],
            ["FY2024Q2", "FY2025Q2", "FY2026Q1"],
        )
        self.assertEqual(first.document["series"][0]["points"][1]["value"], 45277.0)
        self.assertEqual(len(first.warnings), 3)

    def test_matches_the_committed_hd_contract_fixture(self) -> None:
        result = build_timeseries(
            repo_root=REPO,
            company_id="HD",
            dossier_path=REPO / "fixtures" / "HD" / "research" / "dossier.md",
            facts_path=REPO / "fixtures" / "HD" / "analysis" / "facts.md",
            as_of="2026-08-16",
            target_period="FY2026Q2",
        )
        expected = json.loads((REPO / "fixtures" / "HD" / "timeseries.json").read_text())
        self.assertEqual(result.document, expected)


class SyntheticExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / "schemas").mkdir()
        (self.repo / "evidence").mkdir()
        (self.repo / "inputs").mkdir()
        manifest = {
            "schema_version": 1,
            "companies": {
                "HAS": {
                    "period": "FY2026",
                    "period_type": "FY",
                    "metrics": [
                        {
                            "metric_id": "has_net_fees",
                            "unit": "GBPm",
                            "basis": "as-reported",
                        }
                    ],
                }
            },
        }
        (self.repo / "schemas" / "metrics.json").write_text(json.dumps(manifest))
        (self.repo / "evidence" / "source.md").write_text(
            "Annual net fees were GBP 1,200 million.\n"
            "H1 net fees were GBP 500 million.\n"
            "H2 net fees were GBP 700 million.\n"
            "Later net fees were GBP 1,250 million.\n"
            "Target net fees were GBP 1,300 million.\n"
            "Restated annual net fees were GBP 1,210 million.\n"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def fact(
        self,
        *,
        period: str = "FY2025",
        value: object = 1200.0,
        unit: str = "GBPm",
        basis: str = "as-reported",
        source: str = "evidence/source.md",
        published_at: str = "2025-08-01",
        quote: str = "Annual net fees were GBP 1,200 million.",
        metric_id: str = "has_net_fees",
    ) -> dict:
        return {
            "metric_id": metric_id,
            "period": period,
            "value": value,
            "unit": unit,
            "basis": basis,
            "source": source,
            "published_at": published_at,
            "quote": quote,
        }

    def markdown(self, name: str, facts: list[dict], *, blocks: int = 1) -> Path:
        path = self.repo / "inputs" / name
        block = "```jsonl\n" + "\n".join(json.dumps(fact) for fact in facts) + "\n```\n"
        path.write_text("# Facts\n\n" + block * blocks)
        return path

    def build(
        self,
        dossier_facts: list[dict],
        curated_facts: list[dict] | None = None,
        *,
        as_of: str = "2026-08-16",
        target_period: str = "FY2026",
    ):
        dossier = self.markdown("dossier.md", dossier_facts)
        curated = self.markdown("facts.md", curated_facts or dossier_facts)
        return build_timeseries(
            repo_root=self.repo,
            company_id="HAS",
            dossier_path=dossier,
            facts_path=curated,
            as_of=as_of,
            target_period=target_period,
        )

    def assert_rejected(self, fact: dict, message: str) -> None:
        with self.assertRaisesRegex(ExtractionError, message):
            self.build([fact])

    def test_keeps_fy_h1_and_h2_as_separate_series(self) -> None:
        facts = [
            self.fact(),
            self.fact(
                period="FY2025H1",
                value=500.0,
                quote="H1 net fees were GBP 500 million.",
            ),
            self.fact(
                period="FY2025H2",
                value=700.0,
                quote="H2 net fees were GBP 700 million.",
            ),
        ]
        result = self.build(facts)
        self.assertEqual(
            [series["period_type"] for series in result.document["series"]],
            ["FY", "H1", "H2"],
        )

    def test_curated_duplicate_citation_wins(self) -> None:
        dossier = self.fact()
        curated = self.fact(published_at="2025-08-02")
        result = self.build([dossier], [curated])
        point = result.document["series"][0]["points"][0]
        self.assertEqual(point["published_at"], "2025-08-02")

    def test_excludes_post_cutoff_and_target_period(self) -> None:
        facts = [
            self.fact(),
            self.fact(
                period="FY2024",
                value=1250.0,
                quote="Later net fees were GBP 1,250 million.",
                published_at="2026-08-17",
            ),
            self.fact(
                period="FY2026",
                value=1300.0,
                quote="Target net fees were GBP 1,300 million.",
            ),
        ]
        result = self.build(facts)
        points = result.document["series"][0]["points"]
        self.assertEqual([point["period"] for point in points], ["FY2025"])
        self.assertTrue(any("post-cutoff" in warning for warning in result.warnings))
        self.assertTrue(any("held-out target" in warning for warning in result.warnings))

    def test_conflicting_values_are_rejected(self) -> None:
        curated = self.fact(
            value=1210.0,
            quote="Restated annual net fees were GBP 1,210 million.",
        )
        with self.assertRaisesRegex(ExtractionError, "conflicting facts"):
            self.build([self.fact()], [curated])

    def test_wrong_unit_is_rejected(self) -> None:
        self.assert_rejected(self.fact(unit="GBP"), "unit .* does not match")

    def test_wrong_basis_is_rejected(self) -> None:
        self.assert_rejected(self.fact(basis="adjusted"), "basis .* does not match")

    def test_unknown_metric_is_rejected(self) -> None:
        self.assert_rejected(self.fact(metric_id="has_revenue"), "unknown metric_id")

    def test_non_canonical_period_is_rejected(self) -> None:
        self.assert_rejected(self.fact(period="2025 FY"), "non-canonical period")

    def test_target_period_type_must_match_the_company(self) -> None:
        with self.assertRaisesRegex(ExtractionError, "does not match company target type"):
            self.build([self.fact()], target_period="FY2026H1")

    def test_non_finite_and_boolean_values_are_rejected(self) -> None:
        for value in (True, math.nan, math.inf):
            with self.subTest(value=value):
                self.assert_rejected(self.fact(value=value), "finite JSON number")

    def test_invalid_date_is_rejected(self) -> None:
        self.assert_rejected(self.fact(published_at="2025-02-30"), "invalid published_at")

    def test_url_missing_and_escaping_sources_are_rejected(self) -> None:
        cases = [
            ("https://example.com/result", "URL sources"),
            ("evidence/missing.md", "does not exist"),
            ("../outside.md", "escapes the repository"),
            (str((self.repo / "evidence" / "source.md").resolve()), "repository-relative"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                self.assert_rejected(self.fact(source=source), message)

    def test_quote_and_value_must_be_verifiable(self) -> None:
        self.assert_rejected(self.fact(quote="This sentence is absent."), "quote is not present")
        self.assert_rejected(
            self.fact(value=999.0),
            "value 999.0 is not recognisable",
        )

    def test_closed_fact_schema_rejects_missing_and_extra_fields(self) -> None:
        missing = self.fact()
        del missing["basis"]
        extra = self.fact()
        extra["note"] = "not in the contract"
        for fact, message in ((missing, "missing"), (extra, "extra")):
            with self.subTest(message=message):
                self.assert_rejected(fact, message)

    def test_requires_exactly_one_non_empty_fact_block(self) -> None:
        dossier = self.markdown("dossier.md", [self.fact()], blocks=2)
        curated = self.markdown("facts.md", [self.fact()])
        with self.assertRaisesRegex(ExtractionError, "expected exactly one"):
            build_timeseries(
                repo_root=self.repo,
                company_id="HAS",
                dossier_path=dossier,
                facts_path=curated,
                as_of="2026-08-16",
                target_period="FY2026",
            )

    def test_rejects_missing_empty_and_malformed_fact_blocks(self) -> None:
        curated = self.markdown("facts.md", [self.fact()])
        cases = [
            ("# No machine-readable facts\n", "found 0"),
            ("```jsonl\n```\n", "fact block is empty"),
            ("```jsonl\n{not-json}\n```\n", "invalid JSON"),
        ]
        for content, message in cases:
            with self.subTest(message=message):
                dossier = self.repo / "inputs" / "dossier.md"
                dossier.write_text(content)
                with self.assertRaisesRegex(ExtractionError, message):
                    build_timeseries(
                        repo_root=self.repo,
                        company_id="HAS",
                        dossier_path=dossier,
                        facts_path=curated,
                        as_of="2026-08-16",
                        target_period="FY2026",
                    )

    def test_rejects_when_no_required_metric_observation_remains(self) -> None:
        target = self.fact(
            period="FY2026",
            value=1300.0,
            quote="Target net fees were GBP 1,300 million.",
        )
        with self.assertRaisesRegex(ExtractionError, "no admissible observations remain"):
            self.build([target])

    def test_json_serialization_is_byte_stable(self) -> None:
        document = self.build([self.fact()]).document
        first = self.repo / "first.json"
        second = self.repo / "second.json"
        write_timeseries(first, document)
        write_timeseries(second, document)
        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
