from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from pipeline.analysis.generate import run_analysis
from pipeline.analysis.model_client import ModelClientError, ModelResult, OpenAIResponsesClient
from pipeline.quant.extract_timeseries import build_timeseries


REPO = Path(__file__).resolve().parents[3]


class AnalysisFakeClient:
    model = "fake-model"
    reasoning_effort = "low"

    def generate_json(self, *, schema_name, instructions, input_text, schema, metadata=None):
        payload = json.loads(input_text)
        evidence = payload["evidence"]

        def find(text: str) -> str:
            for item in evidence:
                if text in item["quote"].replace("*", ""):
                    return item["evidence_id"]
            self.fail(f"evidence containing {text!r} not supplied to {schema_name}")

        if "context" in schema_name:
            evidence_id = evidence[0]["evidence_id"]
            data = {
                "summary": "Repair demand remains supportive, while large-project demand is mixed.",
                "metric_outlooks": [
                    {
                        "metric_id": metric["metric_id"],
                        "direction": "neutral",
                        "bottom_line": "The accepted record does not justify a directional forecast edge.",
                        "evidence_ids": [evidence_id],
                    }
                    for metric in payload["metrics"]
                ],
                "risks": [],
            }
        elif "facts" in schema_name:
            data = {
                "facts": [
                    {
                        "metric_id": "hd_net_sales",
                        "period": "FY2026Q1",
                        "value": 41800.0,
                        "evidence_id": find("first-quarter fiscal 2026 sales of $41.8 billion"),
                        "commentary": "Reported current-year sales.",
                    },
                    {
                        "metric_id": "hd_comp_sales",
                        "period": "FY2026Q1",
                        "value": 0.6,
                        "evidence_id": find("Total-company comparable sales increased 0.6%"),
                        "commentary": "Reported total-company comparable sales.",
                    },
                    {
                        "metric_id": "hd_adj_eps",
                        "period": "FY2026Q1",
                        "value": 3.43,
                        "evidence_id": find("Adjusted diluted EPS was $3.43"),
                        "commentary": "Reported adjusted diluted EPS.",
                    },
                ]
            }
        elif "news" in schema_name:
            evidence_id = evidence[0]["evidence_id"]
            data = {
                "items": [
                    {
                        "headline": "Latest point-in-time evidence",
                        "summary": "The item is directionally mixed across the requested metrics.",
                        "evidence_ids": [evidence_id],
                        "impacts": [
                            {"metric_id": metric["metric_id"], "direction": "neutral"}
                            for metric in payload["metrics"]
                        ],
                    }
                ]
            }
        elif "consensus" in schema_name:
            data = {
                "anchors": [
                    {
                        "metric_id": "hd_comp_sales",
                        "kind": "guidance_midpoint",
                        "value": 1.0,
                        "evidence_id": find("comparable sales growth of approximately flat to 2.0%"),
                        "note": "Midpoint of explicit company guidance.",
                    }
                ]
            }
        else:
            raise AssertionError(schema_name)
        return ModelResult(data=data, response_id="fake", model=self.model, usage={})

    def fail(self, message: str):
        raise AssertionError(message)


class AnalysisIntegrationTests(unittest.TestCase):
    def test_generated_facts_pass_rachels_extractor(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO / "out") as temp_name:
            out = Path(temp_name)
            dossier = out / "HD" / "research" / "dossier.md"
            dossier.parent.mkdir(parents=True)
            shutil.copyfile(REPO / "fixtures" / "HD" / "research" / "dossier.md", dossier)
            events = []
            run_analysis(
                "HD",
                REPO,
                out,
                AnalysisFakeClient(),
                datetime.fromisoformat("2026-08-16T13:00:00+01:00"),
                events.append,
            )
            result = build_timeseries(
                repo_root=REPO,
                company_id="HD",
                dossier_path=dossier,
                facts_path=out / "HD" / "analysis" / "facts.md",
                as_of="2026-08-16",
                target_period="FY2026Q2",
            )
            expected = json.loads((REPO / "fixtures" / "HD" / "timeseries.json").read_text())
            self.assertEqual(result.document["schema_version"], 1)
            self.assertEqual(result.document["company_id"], "HD")
            actual_values = {
                (series["metric_id"], point["period"]): point["value"]
                for series in result.document["series"]
                for point in series["points"]
            }
            expected_values = {
                (series["metric_id"], point["period"]): point["value"]
                for series in expected["series"]
                for point in series["points"]
            }
            self.assertEqual(actual_values, expected_values)
            consensus = json.loads((out / "HD" / "consensus.json").read_text())
            self.assertEqual(consensus["anchors"][0]["kind"], "guidance_midpoint")
            self.assertTrue(any(event["event"] == "analysis_published" for event in events))
            for name in ("context.md", "news.md"):
                text = (out / "HD" / "analysis" / name).read_text()
                self.assertLessEqual(len(text.split()), 600)


class ModelClientResponseTests(unittest.TestCase):
    def test_parses_completed_structured_output(self) -> None:
        result = OpenAIResponsesClient._parse_response(
            {
                "id": "resp_1",
                "model": "gpt-5.6-terra",
                "status": "completed",
                "usage": {"input_tokens": 10, "output_tokens": 3},
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": '{"ok": true}'}],
                    }
                ],
            }
        )
        self.assertEqual(result.data, {"ok": True})
        self.assertEqual(result.response_id, "resp_1")

    def test_rejects_refusal_and_incomplete_output(self) -> None:
        with self.assertRaisesRegex(ModelClientError, "refused"):
            OpenAIResponsesClient._parse_response(
                {
                    "status": "completed",
                    "output": [
                        {"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}
                    ],
                }
            )
        with self.assertRaisesRegex(ModelClientError, "did not complete"):
            OpenAIResponsesClient._parse_response({"status": "incomplete", "output": []})


if __name__ == "__main__":
    unittest.main()
