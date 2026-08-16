# 🔵 Quant: extraction, guardrails, evals — Rachel

Produces `out/<company_id>/timeseries.json` (Contract D) and `ranges.json` (Contract E)
— examples in `schemas/`. Extractor parses the ```jsonl fact blocks from 🔴's dossier
and 🟢's facts.md. Guardrails are deterministic (no LLM in ranges.json). The hill-climb
eval harness scores configs on the official JUDGING.md formula with the B1 baseline as
the Wall Street proxy — see TEAM-PLAN §7. Prompts (if any) live here as `.md` files.

## Evaluation contract

`evaluation.py` is the deterministic foundation for the walk-forward backtest. A
historical-event manifest is deliberately local to this module rather than a new shared
pipeline contract. Its closed shape is:

```json
{
  "schema_version": 1,
  "event_id": "HD-FY2025Q2",
  "company_id": "HD",
  "target_period": "FY2025Q2",
  "as_of": "2025-08-18",
  "actuals": [
    {
      "metric_id": "hd_adj_eps",
      "value": 4.68,
      "unit": "USD / share",
      "basis": "adjusted",
      "source": "challenge/offline-data/home-depot/filings/example.md",
      "published_at": "2025-08-19",
      "quote": "Adjusted diluted earnings per share ... were $4.68"
    }
  ]
}
```

The loader verifies metric identity, unit, basis, local quote provenance, and that every
actual was published strictly after `as_of`. This keeps held-out answers separate from
the forecast-time information set.

The primary per-metric score is the exact `JUDGING.md` formula:

```text
min(5, |forecast - actual| / max(|B1 - actual|, official floor))
```

Missing or invalid forecasts score `5.0`; they are never dropped from an average.
Secondary diagnostics include paired win/tie/loss versus B1, capped-score rate, APE,
range coverage, and range width measured in official-floor units. The paired comparison
is kept separate because B1 itself scores below `1.0` whenever its miss is smaller than
the denominator floor.
