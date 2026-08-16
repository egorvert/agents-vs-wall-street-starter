# <Company> dossier — <company_id> <target period>

Contract A (🔴 research swarm → everyone). ≤ ~8k tokens. Sections in this order.

## Basis and conventions
For each of the company's 3 metrics: what the label means, GAAP/adjusted definition,
where the company states it (cited inline).

## Historical figures
Per metric, reported values for the last 8+ comparable periods, each cited.

## Guidance
Most recent management guidance for the target period (range, date given, cited).
Say explicitly if none exists.

## Segment / driver detail
Whatever moves this quarter (cited).

## Risks and watch items
Dated, cited.

## Fact block
Every numeric fact from the prose above, one JSON object per line. Reported figures
only — guidance stays in prose and in `ranges.json` evidence. Downstream code parses
only this block.

```jsonl
{"metric_id": "hd_net_sales", "period": "FY2025Q2", "value": 45277.0, "unit": "USDm", "basis": "as-reported", "source": "challenge/offline-data/home-depot/filings/…md", "published_at": "2025-08-19", "quote": "verbatim sentence containing the number"}
```
