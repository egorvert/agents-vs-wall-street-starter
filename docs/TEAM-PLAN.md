# Team plan — Agents vs Wall Street (Sun 16 Aug 2026)

One agent, four companies, **12 numbers** by 18:00. This plan is how we split the work (per the mindmap), the **contracts** for handing work between us, and the **rules** that let three parallel workstreams merge into one system without a 5pm integration fire.

Colour key from the mindmap: 🔴 **Egor & co** — the foundational research swarm · 🟢 **David** — the three analysis products (industry context & competitor analysis, numerical metrics & financials, recent market news) **and** the 🟠 combine step that turns all the signals into the final call · 🔵 **Rachel** — quantitative extraction, hill-climb evals, guardrail ranges.

> Confirm in chat: the mindmap assigns no owner to the delivery glue — orchestrator, validator, workbook writer, architecture HTML, submission logistics — so this plan keeps it with 🔴 (Egor), who's already doing repo admin. Rebalance at the 13:00 sync if red is stretched.

---

## 1. What we're scored on (2 minutes, read once)

**Forecast Accuracy prize** — per metric: `min(5.0, |our miss| / max(|Wall Street's miss|, floor))`, averaged over all 12; **lowest average wins**. Floors: 0.5pp for % metrics, 0.5% of the reported result for money/EPS. **A missing forecast scores 5.0 — the worst possible.** Below 1.0 = we beat Wall Street on that metric.

Strategic consequences we agree to up front:

1. **Never leave a cell blank.** The pipeline has a deterministic fallback chain (§5) so every metric always gets a number.
2. **Forecast as anchor + delta, never a bare level.** Hug our best anchor (consensus/guidance/naive) on metrics where we have no edge — that bounds us near 1.0. **Avoiding 5.0s beats chasing 0.2s:** a blown bold call costs ~0.33 of the average versus just anchoring — roughly four beaten-Wall-Street metrics' worth of gains — and loses a tie-break metric too. Prefer small, evidenced tilts on many metrics over big swings; take a large deviation only with hard, cited evidence, capped at **2–3 metrics**.
3. **The LLM never emits a final number.** Models emit drivers, deltas and rationale; deterministic code computes, clamps and writes every submitted figure.

**Architecture & Design prize** (decided today, 16:00 conversations): 70 pts system + 30 pts write-up. The judges' own rubric rewards: reasoning you can trace from evidence to each of the 12 numbers, data sourcing with citations, **validation that visibly rejects bad values**, a harness that runs reliably, and useful tools. Their stated anti-signal: *"complexity earns no points by itself."* Our eval results table, failed-validation log and conventions table (§6) are worth more than any extra agent.

**The 12 metrics** (exact labels/units from `challenge/companies.json` — units are workbook units, % entered as points, Hays EPS in **pence**):

| Ticker | Period | `metric_id` | Workbook label | Unit | Basis trap to verify |
|---|---|---|---|---|---|
| HD | FY2026Q2 | `hd_net_sales` | Net sales | USDm | — |
| HD | FY2026Q2 | `hd_adj_eps` | Adjusted diluted EPS | USD / share | **Adjusted**, not GAAP |
| HD | FY2026Q2 | `hd_comp_sales` | Comparable sales, total company | % | Total company, in points |
| ADI | FY2026Q3 | `adi_revenue` | Revenue | USDm | — |
| ADI | FY2026Q3 | `adi_adj_eps` | Adjusted diluted EPS | USD / share | **Adjusted** |
| ADI | FY2026Q3 | `adi_adj_gm` | Adjusted gross margin | % | **Adjusted**, in points |
| HAS | FY2026 | `has_net_fees` | Net fees | GBPm | **Full year**, GBP |
| HAS | FY2026 | `has_preexc_eps` | Pre-exceptional basic EPS | GBp | **Pence** (6.2 = 6.2p) |
| HAS | FY2026 | `has_preexc_op` | Pre-exceptional operating profit | GBPm | Pre-exceptional |
| DE | FY2026Q3 | `de_net_sales` | Worldwide net sales and revenues | USDm | Worldwide, incl. financial services |
| DE | FY2026Q3 | `de_eps_gaap` | Diluted EPS (GAAP) | USD / share | **GAAP**, unlike HD/ADI |
| DE | FY2026Q3 | `de_ppa_op` | Production & Precision Ag operating profit | USDm | Segment boundary |

Two identity rules, because validators match exact strings: **units are copied verbatim from `challenge/companies.json`** (it's `USD / share`, with spaces — never hand-type a unit), and the IDs above are our internal **`company_id`** values. Hays' official ticker is `LSE:HAS` in `companies.json`, but paths, filenames and schemas always use `company_id = HAS`; the official ticker appears only in a `ticker` metadata field.

Getting a **basis** wrong (GAAP vs adjusted vs pre-exceptional, midpoint vs total, dollars vs pence) swamps any modelling improvement. Basis verification is scheduled work (🟢, §7), not something we assume.

---

## 2. The pipeline (mindmap → concrete modules)

```
🔴 foundational research swarm ──► dossier.md  (per company; corpus + live-data + web,
        │                                       parallel workers, everything cited)
        ▼
🟢 analysis products (consume the dossier + sources directly):
     context.md   general industry context & competitor analysis (qualitative)
     facts.md     numerical metrics & financials (quantitative, cited)  ──►  🔵 extractor
     news.md      recent market news (external forces)                        │
     consensus.json  public anchors found today                               ▼
                                                                🔵 timeseries.json
                                                                        │
                                                          🔵 guardrails ──► ranges.json
                                                                        ▲   (low/base/high per metric)
                                              🔵 hill-climb eval harness│
                                              (backtests on held-out    │
                                               quarters; scores every   │
                                               config change)           │
        🟠 COMBINE (🟢 owns the code)                                   │
        blind estimate → reveal anchors → bounded reconciliation
        LLM emits drivers/deltas w/ evidence refs; code computes value,
        clamps into [low, high], blends toward anchor ──► final.json
                │
        🔴 workbook writer ──► submission/*.xlsx
        🔴 orchestrator: run.py --company X  (one command, all four)
        🔴 validation gates + fallback chain + architecture HTML + entry + uploads
```

Every arrow above is a **file with an agreed schema** (§4). That's the whole coordination model: we never call each other's code, we read each other's files.

**Data sources feeding the swarm and the analyses** — both already in the repo:

- `challenge/offline-data/` — the organisers' frozen corpus (1,139 filings/transcripts/slides).
- `challenge/live-data/` — 🟢 David's dated snapshot of public evidence up to **10:55 today** (guidance, consensus, market data, news, leakage guards). Respect its cutoff discipline: add new dated notes, never edit in place.
- `starter/search.py` (extended by 🟢) searches both corpora and writes cited research notes.

---

## 3. Repo layout & ownership

```
pipeline/
  research/        🔴 red      foundational swarm, prompts
  analysis/        🟢 David    context / facts / news / consensus generation
  combine/         🟢 David    final-call logic + prompts (the 🟠 step)
  quant/           🔵 Rachel   extractor, guardrails, eval harness
  workbook/        🔴 red      xlsx writer (openpyxl, fills yellow cells only)
  run.py           🔴 red      orchestrator entry point + validation gates + fallbacks
challenge/live-data/  🟢 David    dated evidence snapshot (append-only, cutoff 10:55)
starter/           shared tooling (organiser-supplied, 🟢 extended it) — changes need a chat ack
schemas/           ALL         contract examples — frozen once HD passes e2e (~13:45)
fixtures/          ALL         hand-written golden files per stage (committed)
out/<TICKER>/      generated at runtime (gitignored)
scripts/validate_contracts.py   🔴 red builds; everyone runs it
```

**You own your directory.** Anything outside it — including `schemas/`, `fixtures/`, and this file — changes only after a shout in the group chat. **Deleting or rewriting another person's directory always needs their explicit ack first, even if it looks like boilerplate** — we already had one 10.5k-line cross-directory deletion today (`research-rachel/`, recoverable from git history via `git checkout 05bdd8c -- research-rachel/`); let's not repeat it. This is what lets four people (and four AI agents) commit to `main` all day without conflicts.

Stack (confirm in chat): **Python 3.11+, openpyxl, direct model-API calls, no framework.** Pin everything in `requirements.txt`. The starter search helper is already Python and dependency-free.

---

## 4. Handoff contracts — the important part

### Global conventions (apply to every file)

- **Units are copied verbatim from `challenge/companies.json`** — `USDm`, `USD / share`, `%`, `GBPm`, `GBp` — and every value carries an explicit `"unit"` field. No thousands, no raw dollars, no decimals-for-percent.
- **`company_id` ∈ {HD, ADI, HAS, DE}** names every path, file and schema field. The official ticker (Hays: `LSE:HAS`) lives only in `ticker` metadata.
- **Periods** are canonical strings: `FY2026Q3`, `FY2026H1`, `FY2026` — the company's fiscal calendar, matching the workbook's fiscal-period column. **Hays rule:** `FY2026` means the twelve months to 30 Jun 2026; `FY2026H1`/`FY2026H2` are separate series and are **never** comparable to FY values — the extractor keeps `period_type` (`FY | H1 | H2 | Q`) on every series and comparable-period logic only compares like with like.
- **Basis is explicit** on every number, in every contract including ranges and finals: `"GAAP" | "adjusted" | "pre-exceptional" | "as-reported"`.
- **One citation object everywhere** a number appears — in JSON: `{"source": "<repo path or URL>", "published_at": "YYYY-MM-DD", "quote": "verbatim sentence containing the number"}`. Consensus anchors and range evidence use it too; the validator asserts the quote appears in the cited file, so traceability is mechanical, not aspirational.
- **Cutoff discipline**: nothing published after today's 10:55 snapshot cutoff feeds a forecast. Web evidence enters the system **only** by first being saved as a dated, append-only note in `challenge/live-data/` (with source URL and publication date before the cutoff) — the swarm cites the note, never a live page. Backtests only use documents dated before the target period (point-in-time).
- **`metric_id`** values come from the table in §1, nowhere else.
- Files live at the exact paths below. `scripts/validate_contracts.py` checks presence, schema shape, units, and quote-spans; **run it before every commit** and the orchestrator runs it between stages.

### Contract A — 🔴 dossier: `out/<TICKER>/research/dossier.md`

The swarm's output; the foundation everyone else consumes. Structured markdown, **≤ ~8k tokens** (long context degrades downstream models — cap it, don't dump). Required sections, in order:

1. `## Basis and conventions` — for each of the company's 3 metrics: what the label means, GAAP/adjusted definition, where the company states it (cited).
2. `## Historical figures` — per metric, reported values for the last 8+ comparable periods, each cited with a quote.
3. `## Guidance` — most recent management guidance for the target period (range, date given, cited). Note if none exists.
4. `## Segment / driver detail` — whatever moves this quarter (cited).
5. `## Risks and watch items` — dated, cited.
6. `## Fact block` — **the machine-readable layer**: a fenced ` ```jsonl ` block where every numeric fact from the prose appears as one JSON line: `{"metric_id", "period", "value", "unit", "basis", "source", "published_at", "quote"}`. Downstream code parses **only this block**; the prose is for humans and models. No fact block, no handoff.

### Contract B — 🟢 analysis products: `out/<TICKER>/analysis/`

- `context.md` — **≤ 600 words.** Industry conditions, competitor read-across (competitor results reported this season are gold).
- `facts.md` — the curated quantitative layer: the specific numerical metrics and financials that matter for this quarter's call, each cited with a quote, **ending in the same ` ```jsonl ` fact block as Contract A**. This is the file 🔵's extractor trusts most — and it parses only the fact block.
- `news.md` — **≤ 600 words.** Dated items since the last filing, each with source and a one-line **expected directional impact per metric_id** (`↑ / ↓ / neutral / unknown`).

### Contract C — 🟢 anchors: `out/<TICKER>/consensus.json`

Whatever public anchors exist as of the snapshot (analyst consensus, guidance midpoints — Hays' company-hosted consensus is already captured in `challenge/live-data/hays/`). Missing entries are fine — downstream code handles absence.

```json
{ "company_id": "HD", "retrieved_at": "2026-08-16T13:05:00+01:00",
  "anchors": [
    { "metric_id": "hd_adj_eps", "kind": "consensus", "value": 4.71, "unit": "USD / share",
      "basis": "adjusted", "source": "challenge/live-data/home-depot/…md",
      "published_at": "2026-08-15", "quote": "…consensus adjusted EPS of $4.71…",
      "note": "vendor basis checked" } ] }
```

### Contract D — 🔵 timeseries: `out/<TICKER>/timeseries.json`

```json
{ "company_id": "HD", "series": [
    { "metric_id": "hd_net_sales", "unit": "USDm", "basis": "as-reported", "period_type": "Q",
      "points": [ { "period": "FY2025Q2", "value": 45283.0,
                    "source": "challenge/offline-data/home-depot/filings/…md",
                    "published_at": "2025-08-19",
                    "quote": "Net sales of $45.3 billion…" } ] } ] }
```

Minimum 8 comparable periods per metric where the corpus allows (Hays: annual + half-years).

### Contract E — 🔵 guardrails: `out/<TICKER>/ranges.json`

Deterministically computed — no LLM in this file. **The combine step must land inside `[low, high]`**; code clamps, and if the model argues for outside-the-range, that's an escalation to humans, never a silent override.

```json
{ "company_id": "HD", "ranges": [
    { "metric_id": "hd_adj_eps", "unit": "USD / share", "basis": "adjusted",
      "low": 4.42, "base": 4.68, "high": 4.86,
      "methods": ["seasonal_naive_band", "yoy_trend", "guidance_upper_bias", "consensus_anchor"],
      "evidence": [ { "source": "challenge/offline-data/home-depot/…md",
                      "published_at": "2026-05-20", "quote": "…guidance of $4.55 to $4.75…" } ],
      "notes": "actuals land upper-half of guidance historically" } ] }
```

### Contract F — 🟠 final call: `out/<TICKER>/final.json`

Written by 🟢 combine **code** (the LLM's structured output has no field for the final value — it emits drivers and deltas; code computes):

```json
{ "company_id": "HD", "finals": [
    { "metric_id": "hd_adj_eps", "value": 4.72, "unit": "USD / share", "basis": "adjusted",
      "anchor": 4.68, "anchor_kind": "range_base", "delta": 0.04,
      "delta_evidence": [ { "source": "out/HD/analysis/news.md", "published_at": "2026-08-14",
                            "quote": "…" } ],
      "fallback_tier": 0, "rationale": "one sentence" } ] }
```

**Anchor priority is fixed, not per-run judgement:** consensus → guidance midpoint → range base → seasonal naive; combine takes the highest-priority anchor available and records it in `anchor_kind`, so absence of consensus never leaves the anchor ambiguous.

`fallback_tier` records how the number was produced (see §5). The workbook writer reads **only** this file — and that works because **the orchestrator guarantees this file always exists**: if combine fails or times out, `run.py` itself writes `final.json` from the fallback chain (tiers 1–4) before invoking the writer. The no-blank guarantee lives in the orchestrator, not in hope.

### Fixtures make us parallel

We hand-write one **fixture** per contract for HD (30 min, split up) and commit them under `fixtures/HD/`. From that moment: 🟢 builds analyses against the fixture dossier without waiting for the swarm; 🔵 builds against fixture facts without waiting for 🟢; 🟢's combine and 🔴's workbook writer build against fixture timeseries/ranges without waiting for 🔵. **Nobody blocks on anybody.** When a real upstream file validates, downstream re-points from `fixtures/` to `out/`.

---

## 5. Fallback chain — why nothing is ever blank

The orchestrator resolves every metric through this chain, in order, logging the tier used:

| Tier | Source | When |
|---|---|---|
| 0 | `final.json` value (validated, in range) | normal path |
| 1 | `ranges.json` base | combine failed/timed out |
| 2 | `consensus.json` anchor | guardrails failed |
| 3 | Seasonal naive: last comparable period × trailing YoY from `timeseries.json` | extractor-only world |
| 4 | Last reported value from the corpus | absolute last resort |

Tiers 1–4 are pure deterministic code inside `run.py`, written by 🔴 early, tested with fixtures. Whatever tier fires, **the orchestrator materialises a normalised `final.json` before the workbook writer runs** — the writer never needs to know a fallback happened. A total model outage at 17:20 still produces 12 defensible numbers. This deterministic path (timeseries → ranges → anchor) is also our **minimum ship path**: it must work end-to-end before any research-enhanced combine is considered load-bearing.

---

## 6. Working rules

### Git

1. **Commit small, push immediately.** Work that exists only on a laptop doesn't exist — and our commit history is also our proof the entry was built today (the rules disqualify pre-made work; history is the evidence).
2. Work on `main`, or on a branch that merges back **within the hour**. No long-lived branches, no force-push to `main`, pull before push.
3. `main` must always pass `python scripts/validate_contracts.py --fixtures` + a stub run. If you break it, fixing it is your next commit.
4. Never commit: `entry.json`, `.env`, real forecasts before 18:00 (`submission/*.xlsx` is already gitignored), `out/` (add to gitignore).
5. Schemas & fixtures **freeze once the HD fixture passes end-to-end through workbook generation** (target ~13:45) — freezing before the contracts have survived one real pass just forces late exceptions. After the freeze, a change needs an ack from all of us in chat and a `schema_version` bump in the changed file.
6. **Never delete or rewrite someone else's directory without their explicit ack** — see §3.

### AI coding agents (everyone is using one — these rules are for them too)

The root `AGENTS.md` / `CLAUDE.md` carry these rules, so Codex and Claude Code pick them up automatically. Additionally, tell your agent — and check its diffs for — the following:

1. **Stay in your directory.** Agents must not "helpfully" refactor shared code, schemas, fixtures, `challenge/`, or another person's area. If your agent's diff touches a path you don't own, revert it and coordinate in chat.
2. **Never invent schema fields.** The contracts in §4 are closed; a needed field is a chat message, not a unilateral edit.
3. **Prompts are files**, versioned in your directory as `.md` (judges read prompts, and diffs beat archaeology). No prompts buried in string literals.
4. Run the validator before committing; paste failures to your agent — that's its feedback loop.
5. Keep runs reproducible: fixed inputs, cache external fetches, log model + timestamps. The final run's log is a deliverable.
6. Agent output still gets a 60-second human skim from its owner before merge. You own what you commit, not your agent.

### Forecast discipline (team-level agreements)

1. Anchor + delta; ≤3 deliberate deviations across the 12 metrics; each deviation needs **≥2 cited evidence items** in `delta_evidence`.
2. Blind first: the combine's first estimate is made with consensus **redacted from the prompt**; anchors are revealed in a second step for bounded reconciliation. (Anchoring can't be prompted away — it has to be structural.)
3. Every validation failure is **logged, not hidden** — the judges' rubric explicitly credits "rejected values."
4. Any pipeline addition must beat the current config on 🔵's eval harness, or it gets deleted. We'd rather present a small system that provably works.

---

## 7. Rough plan per person (develop and adapt as you see fit)

### 🔴 Egor & co — foundational research swarm + delivery glue (orchestrator, workbooks, HTML, submission)

*Read first: `docs/research/agent-architecture.md` (orchestrator-workers + evidence ledger), `qa-verification.md` (deterministic gates), `single-file-html.md` + the HTML sections of `judge-profile.md`.*

- **First — walking skeleton (~45 min):** `python pipeline/run.py --company HD --stub`: read fixtures → combine stub → workbook writer (openpyxl, load `challenge/templates/`, fill **only** the yellow forecast cells, never touch the Summary sheet structure) → `npm run check:submission` green. From that moment the end-to-end path exists all day.
- **Swarm v1:** orchestrator spawning parallel workers per topic (historical figures / guidance / segments / risks) over `offline-data` + `live-data` + web; workers return structured, cited facts — not prose essays — merged into `dossier.md` per company. Start with HD, scale to four. This is the input everyone downstream consumes — its quality caps everyone else's.
- **Validation gates + fallback chain (in `run.py`):** unit/magnitude sanity vs last reported (catches 1000× errors), recompute derived identities, range containment on 🟢's finals, consensus-distance escalation with documented-driver requirement, tiers 1–4. Log every rejection to the run log.
- **Architecture HTML** (second red person in parallel): start from the supplied `architecture/index.html` template. The diagram must name our real files/modules and annotate the **edges** with actual payloads (judges check the diagram against the code). Include: conventions table, eval results table, fallback chain, an honest "where this fails" section. **Draft showable by 15:30** (the 16:00 conversation is the highest-weight moment of the prize); locked 17:10. Self-contained, ≤2MB, no external requests, no secrets/emails.
- **Done when:** one command produces all four workbooks from the live pipeline; every submitted number traces to `final.json` → evidence; HTML matches reality.

### 🟢 David — analysis products + the 🟠 combine (final call)

*Read first: `docs/research/street-process.md` (where consensus is weak), `llm-numeric-forecasting.md` (blind→reveal→reconcile, schema starvation), `academic-ml.md` (#1: fixed blend weights), `prediction-methodology.md`. Skim `judge-profile.md`.*

- You've already built the hard data part — `challenge/live-data/` with guidance, consensus and market data per company, and the extended search helper. Two workstreams remain: the analysis products (Contract B/C) and the combine (Contract F).
- **Analyses v1, one company (HD):** produce conforming `context.md`, `facts.md`, `news.md`, `consensus.json` — from live-data + the fixture dossier. Goal is validating files, not elegance. Then automate: a small script/prompt per product so all four companies are regenerable (judges care that the system, not a human, did the work).
- **Combine v1 (the 🟠 step — your second half of the day):** per metric: (a) blind structured estimate from dossier + timeseries, consensus redacted; (b) reveal anchors (`ranges.json`, `consensus.json`); (c) bounded reconciliation — the model emits **drivers, a delta vs anchor, and evidence refs**; the schema has *no field for the final value*; your code computes it, clamps into 🔵's range, applies a fixed blend toward the anchor (fixed weights — fitted weights on one day of data are noise). Your own `context.md`/`news.md` inform the delta, bounded to a small band. Tune the blend weight and deviation bounds against 🔵's eval harness.
- **Basis verification for all 12 metrics:** confirm each metric's exact definition (the §1 trap column) from company documents; write the findings down — they go verbatim into the architecture HTML conventions table. This is the highest score-per-hour work in the day. **Hays deserves your best hour** — full-year GBP metrics, pence EPS, pre-exceptional basis; it's the company most teams will fumble.
- **Done when:** four companies × (context + facts + news + consensus) validating with every number cited; combine produces `final.json` for all 12 metrics with drivers + evidence; conventions table handed to the HTML owner.

### 🔵 Rachel — extraction, guardrails, hill-climb evals

*Read first: `docs/research/evals-hillclimbing.md`, `prediction-methodology.md` (guidance-position bias + surprise persistence), `qa-verification.md` (deterministic checks), `street-actuals-appendix.md`.*

- Note: your `research-rachel/` starter push was removed from `main` in commit `21c32e4` (recoverable via `git checkout 05bdd8c -- research-rachel/` if needed). **Compliance caution before reusing any of it:** the event rules allow declared *generic* pre-existing components only — pre-event challenge-specific code, prompts or workflows are a disqualification risk even if declared. Reuse generic utilities at most (declared in `entry.json`); rebuild anything forecasting-specific fresh today.
- **Extractor v1:** fixture dossier + 🟢's `facts.md` → `timeseries.json`; period canonicalisation, unit/basis normalisation. Then the **backtest scaffold**: for each company pick the last 6–8 reported periods from the corpus as held-out targets, restricting inputs to documents dated before each target (corpus filenames carry dates — point-in-time discipline is what makes the backtest honest).
- **Guardrails v1:** deterministic range builder per metric: seasonal-naive band, YoY trend band, guidance-anchored (actuals land in the **upper half** of guidance ranges historically — use last guidance, not first), consensus anchor when present. Emit `ranges.json`. Also compute the two baselines every config must beat: **B0** seasonal naive, **B1** consensus/guidance-mid.
- **Hill climb:** the harness's **primary score is the official formula from `JUDGING.md`** — `min(5.0, |our miss| / max(|proxy miss|, floor))` averaged across metrics, using **B1 as the Wall Street proxy** (the real benchmark is hidden) and the official floors (0.5pp for %, 0.5% of reported for money/EPS). EPS-in-cents and median APE are secondary diagnostics only — never tune on a metric that isn't the scored one. Run each config ≥3 times (variance is real); keep a results table — config, score, repeats, delta vs baseline. Tune combine's blend weight and deviation bounds with 🟢 against this table. **The results table goes in the HTML** — it's the single most judge-legible artefact we can produce.
- **Scope honestly:** start with a smoke backtest — one company × 3–4 held-out periods — and expand only if time allows. A small, leak-free backtest labelled as such beats an ambitious one with look-ahead bias; the judges hand-check claims.
- **Done when:** `ranges.json` for all 12 metrics with methods + evidence; a backtest table with ≥2 configs vs baselines on the official-formula score.

---

## 8. Timeline & integration checkpoints (updated ~12:45)

| Time | Checkpoint | Bar to clear |
|---|---|---|
| 13:00 | Lunch sync (all) | Confirm this plan + open decisions (§10); schemas + HD fixtures committed |
| 13:45 | **CP1 — skeleton + schema freeze** | Stub run end-to-end on fixtures; `check:submission` green; contracts freeze once this passes |
| 15:00 | **CP2 — first real company** | HD flows swarm → analysis → ranges → final → workbook, live |
| 15:30 | HTML draft showable | Two speakers chosen; one 5-minute rehearsal of the story |
| 15:45 | **CP3 — all four + feature freeze** | Full run on all companies; after this only fixes and tuning |
| 16:00–17:15 | Judging pass + dry runs | ≥2 full clean runs; keep building while one person is with judges |
| 17:00 | Social posts close | Optional, individual $500 prizes — see §9 |
| 17:10 | **Lock** | HTML final; commit; hash into `entry.json` |
| 17:15 | **Final run** | `python pipeline/run.py --all 2>&1 \| tee logs/final-run-$(date +%H%M).log` — this exact string goes in `entry.json` |
| 17:30–17:45 | **Upload everything** | Four workbooks + private form — don't ride the 18:00 deadline |

If a checkpoint slips by more than ~20 minutes, we cut scope at that layer (fewer swarm workers, fewer eval configs, simpler combine) — the fallback chain means the system always ships.

## 9. Submission logistics — named owners

| Deliverable | Owner |
|---|---|
| `entry.json` + private form on openstocks.com/hackathon (agent name, members + emails, models, final command, **final commit hash**) | Egor |
| Final run execution + `logs/` capture | Egor |
| Workbook uploads (manual — the agent must never submit programmatically): HD | David |
| ADI | Rachel |
| HAS | Egor |
| DE | 4th member (else Egor) |
| Architecture HTML upload (with entry form) | Egor |

**Upload readiness check by 15:00:** every uploader signs in to openstocks.com and opens their company's Forecast Model page so login problems surface three hours early, not at 17:35. Egor is the backup uploader for all four companies. Everyone verifies their own upload shows as received before 17:50. Last valid upload per company before 18:00 counts.

**Social prizes** (optional, individual, close **17:00**): $500 each for X and LinkedIn. A post missing the required tags doesn't qualify — X: `@_openstocks @primerapp_ @AITinkerers @openai`; LinkedIn: tag Primer, OpenAI, AI Tinkerers. Judged on thoughtful insight, not engagement.

**Compliance we all keep in mind:** everything competition-specific is built today (commit history is our proof). Declaring pre-existing components in `entry.json` covers **generic** things only — coding harnesses, SDKs, the starter helper, generic utilities; it does **not** make pre-event challenge-specific code, prompts or workflows legal, so anything forecasting-specific from before today (including `research-rachel/` scaffolding) gets rebuilt, not reused. No secrets or emails in the repo or HTML; forecasts are made by the system, not by hand.

## 10. Open decisions (settle at the 13:00 lunch sync)

1. Confirm 🔴 keeps the delivery glue — orchestrator, validator, workbooks, HTML, submission (see note at top).
2. Stack — proposal: Python 3.11 + openpyxl, direct API calls, no framework.
3. Agent name (goes on the leaderboard — pick once, it's in every form).
4. Models per stage + who has which API keys; how we spend the $50 Codex credit.
5. The two judge-conversation speakers.
6. Upload assignments above — confirm or swap.
7. Whether any *generic* utility from `research-rachel/` is worth recovering and declaring — everything challenge-specific gets rebuilt today regardless (disqualification risk otherwise).
