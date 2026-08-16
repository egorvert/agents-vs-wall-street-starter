# Contract schemas

Machine-checkable versions of the handoff contracts in `docs/TEAM-PLAN.md` §4.

- `metrics.json` — **the metric manifest.** Single source of truth for `company_id`,
  `metric_id`, verbatim workbook labels/units, basis, period. Everything validates
  against this file; nothing else may define a unit or label.
- `*.example.json` — one conforming example per JSON contract. Copy the shape exactly.
- `*.template.md` — required structure for the markdown contracts. Every numeric
  fact must also appear in the trailing ```jsonl fact block — downstream code
  parses only that block.

Validate anything with:

```bash
python3 scripts/validate_contracts.py --fixtures
```

Frozen once the HD fixture passes end-to-end (see TEAM-PLAN §6). After that,
changes need all-team ack + a `schema_version` bump.
