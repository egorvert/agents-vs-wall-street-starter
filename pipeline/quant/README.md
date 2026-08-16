# 🔵 Quant: extraction, guardrails, evals — Rachel

Produces `out/<company_id>/timeseries.json` (Contract D) and `ranges.json` (Contract E)
— examples in `schemas/`. Extractor parses the ```jsonl fact blocks from 🔴's dossier
and 🟢's facts.md. Guardrails are deterministic (no LLM in ranges.json). The hill-climb
eval harness scores configs on the official JUDGING.md formula with the B1 baseline as
the Wall Street proxy — see TEAM-PLAN §7. Prompts (if any) live here as `.md` files.
