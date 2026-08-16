# Home Depot curated facts — HD FY2026Q2 (FIXTURE)

Hand-written golden sample for Contract B (`facts.md`). Real Q1 FY2026 run-rate
figures the extractor should trust for the current-year trajectory.

- `hd_net_sales`: Q1 FY2026 sales were $41,800m, up 4.8% YoY (cited below).
- `hd_comp_sales`: total-company comp +0.6% in Q1 FY2026; FX added ~55bp.
- `hd_adj_eps`: Q1 FY2026 adjusted diluted EPS $3.43 vs $3.56 a year earlier.

## Fact block

```jsonl
{"metric_id": "hd_net_sales", "period": "FY2026Q1", "value": 41800.0, "unit": "USDm", "basis": "as-reported", "source": "challenge/live-data/home-depot/company-releases/2026-05-19__hd-q1-results-fy2026-guidance.md", "published_at": "2026-05-19", "quote": "Home Depot reported first-quarter fiscal 2026 sales of $41.8 billion, up 4.8% year over year"}
{"metric_id": "hd_comp_sales", "period": "FY2026Q1", "value": 0.6, "unit": "%", "basis": "as-reported", "source": "challenge/live-data/home-depot/company-releases/2026-05-19__hd-q1-results-fy2026-guidance.md", "published_at": "2026-05-19", "quote": "Total-company comparable sales increased 0.6%"}
{"metric_id": "hd_adj_eps", "period": "FY2026Q1", "value": 3.43, "unit": "USD / share", "basis": "adjusted", "source": "challenge/live-data/home-depot/company-releases/2026-05-19__hd-q1-results-fy2026-guidance.md", "published_at": "2026-05-19", "quote": "Adjusted diluted EPS was $3.43, versus $3.56 a year earlier"}
```
