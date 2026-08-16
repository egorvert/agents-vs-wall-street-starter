from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pipeline.quant.backtest import (
    BacktestCase,
    audit_forecast_inputs,
    build_case_configurations,
    load_backtest_case,
    run_backtest,
    write_results,
)
from pipeline.quant.evaluation import EvaluationError


REPO = Path(__file__).resolve().parents[3]


def create_case(root: Path) -> Path:
    (root / "schemas").mkdir(parents=True)
    (root / "evidence").mkdir()
    case_dir = root / "case"
    case_dir.mkdir()
    (root / "schemas" / "metrics.json").write_bytes(
        (REPO / "schemas" / "metrics.json").read_bytes()
    )

    history_quotes = [
        "Comparable sales for FY2024Q2 decreased 3.0%.",
        "Comparable sales for FY2025Q2 increased 1.0%.",
    ]
    guidance_quote = "Management guidance midpoint for comparable sales was 1.0%."
    actual_quote = "Reported comparable sales for FY2026Q2 increased 2.0%."
    (root / "evidence" / "history.md").write_text("\n".join(history_quotes), encoding="utf-8")
    (root / "evidence" / "guidance.md").write_text(guidance_quote, encoding="utf-8")
    (root / "evidence" / "actual.md").write_text(actual_quote, encoding="utf-8")

    event = {
        "schema_version": 1,
        "event_id": "HD-FY2026Q2-synthetic",
        "company_id": "HD",
        "target_period": "FY2026Q2",
        "as_of": "2026-08-16",
        "actuals": [
            {
                "metric_id": "hd_comp_sales",
                "value": 2.0,
                "unit": "%",
                "basis": "as-reported",
                "source": "evidence/actual.md",
                "published_at": "2026-08-17",
                "quote": actual_quote,
            }
        ],
    }
    timeseries = {
        "schema_version": 1,
        "company_id": "HD",
        "series": [
            {
                "metric_id": "hd_comp_sales",
                "unit": "%",
                "basis": "as-reported",
                "period_type": "Q",
                "points": [
                    {
                        "period": "FY2024Q2",
                        "value": -3.0,
                        "source": "evidence/history.md",
                        "published_at": "2024-08-13",
                        "quote": history_quotes[0],
                    },
                    {
                        "period": "FY2025Q2",
                        "value": 1.0,
                        "source": "evidence/history.md",
                        "published_at": "2025-08-19",
                        "quote": history_quotes[1],
                    },
                ],
            }
        ],
    }
    consensus = {
        "schema_version": 1,
        "company_id": "HD",
        "retrieved_at": "2026-08-16T09:00:00+01:00",
        "anchors": [
            {
                "metric_id": "hd_comp_sales",
                "kind": "guidance_midpoint",
                "value": 1.0,
                "unit": "%",
                "basis": "as-reported",
                "source": "evidence/guidance.md",
                "published_at": "2026-05-19",
                "quote": guidance_quote,
                "note": "synthetic test anchor",
            }
        ],
    }
    for name, value in (
        ("event.json", event),
        ("timeseries.json", timeseries),
        ("consensus.json", consensus),
    ):
        (case_dir / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return case_dir


class BacktestConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.case_dir = create_case(self.root)
        self.case = load_backtest_case(self.case_dir, self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_builds_baselines_current_range_and_fixed_blends(self) -> None:
        configs, ranges, proxy_kinds = build_case_configurations(self.case)
        metric = "hd_comp_sales"
        self.assertEqual(configs["b0_seasonal"][metric], 2.0)  # damped %-drift (16:45) — Rachel to review
        self.assertEqual(configs["b1_anchor"][metric], 1.0)
        self.assertEqual(configs["current_ranges_base"][metric], 1.5)
        self.assertEqual(configs["blend_b1_25"][metric], 1.75)  # damped %-drift (16:45) — Rachel to review
        self.assertEqual(configs["blend_b1_50"][metric], 3.0)
        self.assertEqual(configs["blend_b1_75"][metric], 2.0)
        self.assertEqual((ranges[metric]["low"], ranges[metric]["high"]), (0.0, 9.0))
        self.assertEqual(proxy_kinds[metric], "guidance_midpoint")

    def test_scores_all_configs_on_the_same_held_out_actual(self) -> None:
        result = run_backtest([self.case])
        summaries = {item.config_id: item for item in result.summaries}
        self.assertEqual(result.event_ids, ("HD-FY2026Q2-synthetic",))
        self.assertEqual(len(result.metrics), 6)
        self.assertEqual(summaries["b0_seasonal"].mean_official_score, 0.0)  # damped %-drift (16:45) — Rachel to review
        self.assertEqual(summaries["b1_anchor"].mean_official_score, 1.0)
        self.assertEqual(summaries["current_ranges_base"].mean_official_score, 0.5)
        self.assertEqual(summaries["blend_b1_75"].mean_official_score, 0.75)  # damped %-drift (16:45) — Rachel to review
        self.assertEqual(summaries["blend_b1_75"].win_rate_vs_proxy, 1.0)
        self.assertEqual(summaries["blend_b1_50"].tie_rate_vs_proxy, 1.0)
        self.assertEqual(result.proxy_usage[0].kind, "guidance_midpoint")
        self.assertEqual(len(result.metric_summaries), 6)

    def test_falls_back_to_b0_when_no_anchor_exists(self) -> None:
        no_anchor = BacktestCase(
            event=self.case.event,
            timeseries=self.case.timeseries,
            consensus=dict(self.case.consensus, anchors=[]),
        )
        configs, _, proxy_kinds = build_case_configurations(no_anchor)
        self.assertEqual(configs["b1_anchor"], configs["b0_seasonal"])
        self.assertEqual(proxy_kinds["hd_comp_sales"], "b0_fallback")

    def test_rejects_post_cutoff_and_target_period_inputs(self) -> None:
        future_point = copy.deepcopy(self.case.timeseries)
        future_point["series"][0]["points"][0]["published_at"] = "2026-08-17"
        target_point = copy.deepcopy(self.case.timeseries)
        target_point["series"][0]["points"][0]["period"] = "FY2026Q2"
        future_anchor = copy.deepcopy(self.case.consensus)
        future_anchor["anchors"][0]["published_at"] = "2026-08-17"
        cases = [
            (BacktestCase(self.case.event, future_point, self.case.consensus), "point-in-time leakage"),
            (BacktestCase(self.case.event, target_point, self.case.consensus), "target leakage"),
            (BacktestCase(self.case.event, self.case.timeseries, future_anchor), "point-in-time leakage"),
        ]
        for case, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(EvaluationError, message):
                    audit_forecast_inputs(case, self.root)

    def test_rejects_duplicate_event_ids(self) -> None:
        with self.assertRaisesRegex(EvaluationError, "event_id values must be unique"):
            run_backtest([self.case, self.case])

    def test_results_json_is_byte_stable(self) -> None:
        result = run_backtest([self.case])
        first = self.root / "first.json"
        second = self.root / "second.json"
        write_results(first, result)
        write_results(second, result)
        self.assertEqual(first.read_bytes(), second.read_bytes())


class BacktestCliTests(unittest.TestCase):
    def test_cli_runs_as_a_direct_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            create_case(root)
            output = root / "results.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "pipeline" / "quant" / "backtest.py"),
                    "--repo-root",
                    str(root),
                    "--case",
                    "case",
                    "--output",
                    str(output),
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            document = json.loads(output.read_text())
            self.assertEqual(len(document["configs"]), 6)
            self.assertEqual(len(document["configs_by_metric"]), 6)
            self.assertEqual(document["event_sensitivity"], [])
            self.assertEqual(document["proxy_usage"][0]["kind"], "guidance_midpoint")
            self.assertEqual(len(document["metrics"]), 6)
            self.assertIn("blend_b1_75", result.stdout)


class CommittedHdSmokeTests(unittest.TestCase):
    def test_three_point_in_time_events_run_and_preserve_proxy_coverage(self) -> None:
        case_root = REPO / "pipeline" / "quant" / "backtests" / "HD"
        cases = [
            load_backtest_case(case_root / period, REPO)
            for period in ("FY2023Q2", "FY2024Q2", "FY2025Q2")
        ]
        result = run_backtest(cases)
        summaries = {summary.config_id: summary for summary in result.summaries}
        self.assertEqual(result.event_ids, ("HD-FY2023Q2", "HD-FY2024Q2", "HD-FY2025Q2"))
        self.assertEqual(len(result.metrics), 36)
        self.assertEqual(
            [usage.kind for usage in result.proxy_usage].count("guidance_midpoint"), 3
        )
        self.assertEqual([usage.kind for usage in result.proxy_usage].count("b0_fallback"), 3)
        self.assertAlmostEqual(summaries["b1_anchor"].mean_official_score, 5 / 6)
        self.assertAlmostEqual(
            summaries["current_ranges_base"].mean_official_score,
            1.0792407557326889,
        )


class CommittedAdiReplayTests(unittest.TestCase):
    def test_three_point_in_time_events_cover_all_target_metrics(self) -> None:
        case_root = REPO / "pipeline" / "quant" / "backtests" / "ADI"
        cases = [
            load_backtest_case(case_root / period, REPO)
            for period in ("FY2023Q3", "FY2024Q3", "FY2025Q3")
        ]
        result = run_backtest(cases)
        summaries = {summary.config_id: summary for summary in result.summaries}

        self.assertEqual(
            result.event_ids,
            ("ADI-FY2023Q3", "ADI-FY2024Q3", "ADI-FY2025Q3"),
        )
        self.assertEqual(len(result.metrics), 54)
        self.assertEqual(
            {evaluation.metric_id for evaluation in result.metrics},
            {"adi_revenue", "adi_adj_eps", "adi_adj_gm"},
        )
        self.assertEqual(
            [usage.kind for usage in result.proxy_usage].count("guidance_midpoint"),
            6,
        )
        self.assertEqual(
            [usage.kind for usage in result.proxy_usage].count("b0_fallback"),
            3,
        )
        self.assertAlmostEqual(summaries["b1_anchor"].mean_official_score, 1.0)
        self.assertAlmostEqual(
            summaries["current_ranges_base"].mean_official_score,
            1.1122583435083429,
        )
        self.assertAlmostEqual(
            summaries["current_ranges_base"].win_rate_vs_proxy,
            5 / 9,
        )


class CombinedHistoricalSensitivityTests(unittest.TestCase):
    def test_leave_one_event_out_results_do_not_depend_on_one_quarter(self) -> None:
        cases = []
        for company, periods in (
            ("HD", ("FY2023Q2", "FY2024Q2", "FY2025Q2")),
            ("ADI", ("FY2023Q3", "FY2024Q3", "FY2025Q3")),
        ):
            case_root = REPO / "pipeline" / "quant" / "backtests" / company
            cases.extend(load_backtest_case(case_root / period, REPO) for period in periods)

        result = run_backtest(cases)
        sensitivity = {item.config_id: item for item in result.event_sensitivity}

        self.assertEqual(len(result.event_ids), 6)
        self.assertEqual(len(result.metrics), 90)
        self.assertEqual(len(sensitivity), 6)
        self.assertEqual(sensitivity["b1_anchor"].event_count, 6)
        self.assertEqual(sensitivity["b1_anchor"].winner_count, 6)
        self.assertLess(
            sensitivity["b1_anchor"].leave_one_event_out_mean_max,
            sensitivity["current_ranges_base"].leave_one_event_out_mean_min,
        )


if __name__ == "__main__":
    unittest.main()
