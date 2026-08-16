from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from pipeline.analysis.model_client import ModelResult
from pipeline.combine.core import (
    CombineConfig,
    MetricCandidate,
    finalize_batch,
    load_company_inputs,
    propose_company,
)


REPO = Path(__file__).resolve().parents[3]


class CombineFakeClient:
    model = "fake-model"
    reasoning_effort = "low"

    def __init__(self) -> None:
        self.requests = []

    def generate_json(self, *, schema_name, instructions, input_text, schema, metadata=None):
        payload = json.loads(input_text)
        self.requests.append((schema_name, payload, schema))
        metrics = payload["metrics"]
        evidence = payload["evidence"]
        if "blind" in schema_name:
            ids = [evidence[0]["evidence_id"]] if evidence else []
            rows = [
                {
                    "metric_id": metric["metric_id"],
                    "direction": "up" if metric["metric_id"] == "hd_net_sales" else "neutral",
                    "proposed_delta": 100.0 if metric["metric_id"] == "hd_net_sales" else 0.0,
                    "confidence": "medium",
                    "drivers": [],
                    "evidence_ids": ids if metric["metric_id"] == "hd_net_sales" else [],
                    "rationale": "The blind evidence supports a modest upward signal.",
                }
                for metric in metrics
            ]
        else:
            distinct = []
            seen_sources = set()
            for item in evidence:
                if item["source"] in seen_sources:
                    continue
                seen_sources.add(item["source"])
                distinct.append(item["evidence_id"])
                if len(distinct) == 2:
                    break
            rows = [
                {
                    "metric_id": metric["metric_id"],
                    "direction": "up" if metric["metric_id"] == "hd_net_sales" else "neutral",
                    "proposed_delta": 200.0 if metric["metric_id"] == "hd_net_sales" else 0.0,
                    "confidence": "high",
                    "drivers": [],
                    "evidence_ids": distinct if metric["metric_id"] == "hd_net_sales" else [],
                    "rationale": "Two independent demand indicators support a bounded increase.",
                }
                for metric in metrics
            ]
        return ModelResult(data={"metrics": rows}, response_id="fake", model=self.model, usage={})


class HdCombineTests(unittest.TestCase):
    def setUp(self) -> None:
        (REPO / "out").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=REPO / "out")
        self.out = Path(self.temp.name)
        shutil.copytree(REPO / "fixtures" / "HD", self.out / "HD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_uses_rachels_b0_and_ranges_without_rebuilding_them(self) -> None:
        inputs = load_company_inputs(company_id="HD", repo_root=REPO, out_root=self.out)
        self.assertAlmostEqual(inputs.b0["hd_comp_sales"].value, 5.3)
        self.assertEqual(inputs.ranges["hd_net_sales"]["base"], 46900.0)
        self.assertEqual(
            inputs.ranges["hd_net_sales"]["methods"],
            ["guidance_band_applied_to_prior_q2", "yoy_trend"],
        )

    def test_blind_request_starves_consensus_and_finalizes_deterministically(self) -> None:
        consensus_path = self.out / "HD" / "consensus.json"
        consensus = json.loads(consensus_path.read_text())
        consensus["anchors"].append(
            {
                "metric_id": "hd_adj_eps",
                "kind": "consensus",
                "value": 4.75,
                "unit": "USD / share",
                "basis": "adjusted",
                "source": "challenge/live-data/home-depot/market-data/2026-08-14__hd-us-retail-building-materials.md",
                "published_at": "2026-08-14",
                "quote": "July overlaps the latter part of Home Depot's fiscal Q2 and is directionally supportive for nominal category demand.",
                "note": "Synthetic test anchor.",
            }
        )
        consensus_path.write_text(json.dumps(consensus))
        inputs = load_company_inputs(company_id="HD", repo_root=REPO, out_root=self.out)
        client = CombineFakeClient()
        candidates = propose_company("HD", inputs, CombineConfig(), client)
        blind_name, blind_payload, blind_schema = client.requests[0]
        serialized = json.dumps(blind_payload).casefold()
        self.assertIn("blind", blind_name)
        self.assertNotIn("consensus", serialized)
        self.assertNotIn("2026-08-14__hd-us-retail-building-materials.md", serialized)
        self.assertNotIn('"final"', json.dumps(blind_schema).casefold())

        outputs = finalize_batch({"HD": candidates}, {"HD": inputs}, CombineConfig())
        finals = {row["metric_id"]: row for row in outputs["HD"].finals}
        self.assertEqual(finals["hd_net_sales"]["value"], 46960.0)
        self.assertEqual(finals["hd_net_sales"]["delta"], 60.0)
        self.assertEqual(len(finals["hd_net_sales"]["delta_evidence"]), 2)
        self.assertEqual(finals["hd_adj_eps"]["anchor_kind"], "consensus")
        self.assertEqual(finals["hd_adj_eps"]["delta"], 0.0)
        for row in finals.values():
            self.assertEqual(
                Decimal(str(row["anchor"])) + Decimal(str(row["delta"])),
                Decimal(str(row["value"])),
            )


class GlobalDeviationBudgetTests(unittest.TestCase):
    def test_batch_applies_only_top_three_eligible_deviations(self) -> None:
        base_inputs = load_company_inputs(
            company_id="HD",
            repo_root=REPO,
            out_root=REPO / "fixtures",
        )
        inputs = {}
        candidates = {}
        for index, company_id in enumerate(("A", "B", "C", "D")):
            metric_id = f"metric_{company_id.lower()}"
            company = {
                **base_inputs.company,
                "metrics": [
                    {
                        "metric_id": metric_id,
                        "unit": "USDm",
                        "basis": "as-reported",
                    }
                ],
            }
            inputs[company_id] = replace(base_inputs, company_id=company_id, company=company)
            evidence = (
                {"source": f"evidence/{company_id}-1.md", "published_at": "2026-01-01", "quote": "one"},
                {"source": f"evidence/{company_id}-2.md", "published_at": "2026-01-02", "quote": "two"},
            )
            candidates[company_id] = [
                MetricCandidate(
                    company_id=company_id,
                    metric_id=metric_id,
                    manifest_index=0,
                    unit="USDm",
                    basis="as-reported",
                    anchor=Decimal("100"),
                    anchor_kind="range_base",
                    low=Decimal("90"),
                    base=Decimal("100"),
                    high=Decimal("110"),
                    blind_direction="up",
                    reveal_direction="up",
                    proposed_delta=Decimal(str(index + 1)),
                    confidence="high",
                    evidence=evidence,
                    rationale="Supported increase.",
                    eligible=True,
                    rejection_reasons=(),
                )
            ]
        outputs = finalize_batch(candidates, inputs, CombineConfig())
        nonzero = [
            row
            for payload in outputs.values()
            for row in payload.finals
            if row["delta"] != 0
        ]
        self.assertEqual(len(nonzero), 3)


if __name__ == "__main__":
    unittest.main()
