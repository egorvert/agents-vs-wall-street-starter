# Agent rules — Agents vs Wall Street team repo

You are working inside a 4-person hackathon team's repo. The full plan and handoff
contracts are in `docs/TEAM-PLAN.md` — **read it before writing code.** These rules
are non-negotiable for both humans and AI coding agents.

## Ownership map — stay in your lane

| Path | Owner | May be edited by others? |
|---|---|---|
| `pipeline/research/` | Egor & co (red) | No |
| `pipeline/analysis/`, `pipeline/combine/` | David | No |
| `pipeline/quant/` | Rachel | No |
| `pipeline/workbook/`, `pipeline/run.py` | Egor & co | No |
| `challenge/live-data/` | David | Append new dated notes only; never edit or refresh in place (cutoff 10:55) |
| `challenge/offline-data/`, `challenge/templates/`, `challenge/companies.json` | organisers | **Never edit** |
| `starter/`, `scripts/`, `architecture/`, `docs/`, root config (`.gitignore`, `requirements.txt`, `package.json`) | shared | Yes — announce in team chat in the same breath as the commit |
| `schemas/`, `fixtures/` | shared | Freely during bootstrap; after the freeze (HD fixture passes end-to-end, ~13:45), only with all-team ack + `schema_version` bump |
| `submission/`, `logs/` | written by the pipeline / final run only | No manual edits |

For personal `pipeline/` areas: if a diff touches another member's area, stop and say
so instead of committing it. Shared paths don't require stopping — make the change and
announce it. **Never delete or rewrite another member's directory without their
explicit ack — even if it looks like boilerplate.**

## Contracts

- Stage handoffs are files in `out/<TICKER>/` with schemas defined in
  `docs/TEAM-PLAN.md` §4 and mirrored in `schemas/`. **Never add, rename, or
  reinterpret schema fields.** A missing field is a team conversation, not an edit.
- Every value carries `unit`, `basis` (GAAP / adjusted / pre-exceptional /
  as-reported), and a citation object `{source, published_at, quote}` — the quote
  is a verbatim sentence containing the number, and the validator checks it.
- **Units are copied verbatim from `challenge/companies.json`** — `USDm`,
  `USD / share` (with spaces), `%`, `GBPm`, `GBp`. Never hand-type a unit string.
- `metric_id` values come only from the table in `docs/TEAM-PLAN.md` §1.
  Paths and schemas use `company_id` ∈ {HD, ADI, HAS, DE}; the official ticker
  (Hays is `LSE:HAS`) appears only in `ticker` metadata fields.
- Percentages are entered as points (4.5 means 4.5%). Hays EPS is in pence.
  Hays periods carry `period_type` (FY / H1 / H2); half-years are never
  comparable to full-year values.
- Evidence published after the live-data snapshot cutoff (2026-08-16 10:55 London)
  must not feed a forecast; backtests only use documents dated before their target
  period.
- The LLM never emits a submitted number: models output drivers/deltas/evidence;
  deterministic code computes, clamps to `ranges.json`, and writes workbooks.

## Workflow

- Run `python scripts/validate_contracts.py` before every commit; fix failures first.
- Commit small and push to origin immediately — commit history is our proof the
  work was built during the event.
- Keep `main` green: validators + `python pipeline/run.py --company HD --stub` must pass.
- Prompts live as versioned `.md` files inside the owner's directory, never inline
  string literals.
- Never commit: `entry.json`, `.env*`, `out/`, `submission/*.xlsx`, secrets, or
  team email addresses. Never let generated files claim `challenge/` provenance.
- Do not submit anything to openstocks.com programmatically — uploads are manual.
- Log external fetches and model calls with timestamps; the final-run log in
  `logs/` is a judged deliverable.
- Pre-event code: only *generic* components may be reused, and they must be
  declared in `entry.json`. Pre-event challenge-specific code, prompts or
  workflows (including `research-rachel/` scaffolding) may NOT be reused even
  with declaration — rebuild them fresh today.
