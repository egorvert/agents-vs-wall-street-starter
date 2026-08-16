# Home Depot dossier — HD FY2026Q2 (FIXTURE)

Hand-written golden sample for Contract A. Real figures, real citations, abbreviated
coverage (2 historical periods instead of 8+). The swarm's real output replaces this
at `out/HD/research/dossier.md`.

## Basis and conventions
- **Net sales** (USDm): GAAP total company net sales as headlined in the quarterly 8-K.
- **Adjusted diluted EPS** (USD / share): non-GAAP; excludes intangible amortization from acquisitions, per the 8-K non-GAAP reconciliation ("adjusted diluted earnings per share are non-GAAP financial measures", challenge/offline-data/home-depot/filings/2025-08-19__hd-us-20250819-q2-8k__143666.md, 2025-08-19).
- **Comparable sales, total company** (%): company-defined comp metric, total company (not US-only), percentage points.

## Historical figures
- FY2025Q2 net sales $45,277m; comp +1.0%; adjusted diluted EPS $4.68 (8-K, 2025-08-19, cited in fact block).
- FY2024Q2 net sales $43,175m; comp −3.3%; adjusted diluted EPS $4.67 (8-K, 2024-08-13, cited in fact block).

## Guidance
FY2026 guidance reaffirmed 2026-05-19: total sales growth ~2.5–4.5%; comp sales ~flat to 2.0%; adjusted diluted EPS growth ~flat to 4.0% from fiscal 2025's $14.69 (challenge/live-data/home-depot/company-releases/2026-05-19__hd-q1-results-fy2026-guidance.md). No Q2-specific guidance.

## Segment / driver detail
Q1 FY2026 run-rate: sales $41.8bn (+4.8% YoY), comp +0.6%, FX added ~55bp to comp (same live-data note). SRS/GMS acquisitions lift total sales growth above comp growth — do not apply one growth rate to both metrics.

## Risks and watch items
- 2026-05-19 — housing-affordability pressure and consumer uncertainty flagged by CEO (live-data note above).

## Fact block

```jsonl
{"metric_id": "hd_net_sales", "period": "FY2025Q2", "value": 45277.0, "unit": "USDm", "basis": "as-reported", "source": "challenge/offline-data/home-depot/filings/2025-08-19__hd-us-20250819-q2-8k__143666.md", "published_at": "2025-08-19", "quote": "reported sales of $45.3 billion for the second quarter of fiscal 2025"}
{"metric_id": "hd_comp_sales", "period": "FY2025Q2", "value": 1.0, "unit": "%", "basis": "as-reported", "source": "challenge/offline-data/home-depot/filings/2025-08-19__hd-us-20250819-q2-8k__143666.md", "published_at": "2025-08-19", "quote": "Comparable sales for the second quarter of fiscal 2025 increased 1.0%"}
{"metric_id": "hd_adj_eps", "period": "FY2025Q2", "value": 4.68, "unit": "USD / share", "basis": "adjusted", "source": "challenge/offline-data/home-depot/filings/2025-08-19__hd-us-20250819-q2-8k__143666.md", "published_at": "2025-08-19", "quote": "Adjusted diluted earnings per share for the second quarter of fiscal 2025 were $4.68"}
{"metric_id": "hd_net_sales", "period": "FY2024Q2", "value": 43175.0, "unit": "USDm", "basis": "as-reported", "source": "challenge/offline-data/home-depot/filings/2024-08-13__hd-us-20240813-q2-8k__101849.md", "published_at": "2024-08-13", "quote": "reported sales of $43.2 billion for the second quarter of fiscal 2024"}
{"metric_id": "hd_comp_sales", "period": "FY2024Q2", "value": -3.3, "unit": "%", "basis": "as-reported", "source": "challenge/offline-data/home-depot/filings/2024-08-13__hd-us-20240813-q2-8k__101849.md", "published_at": "2024-08-13", "quote": "Comparable sales for the second quarter of fiscal 2024 decreased 3.3%"}
{"metric_id": "hd_adj_eps", "period": "FY2024Q2", "value": 4.67, "unit": "USD / share", "basis": "adjusted", "source": "challenge/offline-data/home-depot/filings/2024-08-13__hd-us-20240813-q2-8k__101849.md", "published_at": "2024-08-13", "quote": "Adjusted diluted earnings per share for the second quarter of fiscal 2024 were $4.67"}
```
