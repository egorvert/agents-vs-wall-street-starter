# <Company> curated facts — <company_id> <target period>

Contract B (🟢 analysis → 🔵 extractor). The specific numerical metrics and
financials that matter for this quarter's call, each cited in prose, and **all of
them repeated in the fact block** — the extractor parses only the block.

Prose: short, grouped by metric_id, each figure cited (source + date + quote).

## Fact block

```jsonl
{"metric_id": "hd_adj_eps", "period": "FY2026Q1", "value": 3.43, "unit": "USD / share", "basis": "adjusted", "source": "challenge/live-data/home-depot/company-releases/…md", "published_at": "2026-05-19", "quote": "verbatim sentence containing the number"}
```
