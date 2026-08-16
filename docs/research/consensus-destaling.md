# De-Staling the Consensus — Implementable Spec

Research note for **"Agents vs Wall Street"**, London, 16 Aug 2026. Compiled 15 Aug 2026.
Companion to `street-process.md` §3.6 (the staleness edge) and `data-sources.md` §3 (consensus sources).

**Legend:** `[TESTED]` = HTTP call executed tonight, output shown is real. `[READ]` = from docs/papers, not executed.
`[BLOCKED]` = tested and failed.

---

## 0. The three findings that change the build

1. **Full StarMine replication is out of reach, and the free per-analyst data that exists is worse than it
   looks.** No free source gives a *complete* panel of live per-analyst estimates (9 sources tested, §2). Zacks'
   earnings-calendar page does expose a rolling feed of individual analyst revisions with dates, brokerage and
   prior→new values (§2.8) — but testing it produced the most important negative result here (§2.10): the
   "Most Recent Consensus" everyone would reach for **is a single analyst**, that analyst is a broad-coverage
   generalist on 5 of 6 names, on one ticker it is Zacks' own in-house team rather than a broker at all, and the
   revisions largely **echo published guidance**. Its real value is *provenance and QC*, not signal. Consolation:
   Brown (2001) shows a two-factor model (forecast age + past accuracy) performs *as well as* a six-factor model,
   and its companion paper shows **forecast age alone predicts as well as the full six-factor model** — so the
   panel we can't get is the one the literature says we don't need.

2. **Zacks hands us a pre-computed poor-man's SmartEstimate, free, in one GET.** `[TESTED]`
   `zacks.com/stock/quote/{T}/detailed-earning-estimates` returns — in plain server-rendered HTML, no key, no
   cookies, no JS — the **Earnings ESP**, **Most Accurate Estimate**, **Most Recent Consensus**, the
   **7/30/60/90-day consensus trend**, **up/down revision counts at 7/30/60 days**, the **last 4 quarters of
   realised surprise**, and — the part `data-sources.md` did not have — **quarterly REVENUE consensus with
   analyst counts**. This is a strict upgrade over every source in `data-sources.md` §3.1.

3. **The ±2% gate fires on none of our candidate names.** `[TESTED]` Measured tonight across the seven
   dossier tickers, |ESP| ranges 0.00%–1.69%. Zero cross the StarMine threshold. The de-staling edge is
   *real but small* on large-cap US names in mid-August. **Do not size this signal as if it were the 70% hit
   rate.** See §3.5 for why direction ≠ APE.

---

## 1. StarMine SmartEstimate mechanics — every implementable parameter

Primary sources:
- LSEG StarMine Quantitative Analytics brochure — https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/lseg-starmine-quantitative-analytics-brochure.pdf `[READ]`
- "20 years of StarMine SmartEstimates" (Lipper Alpha, 5 Mar 2021) — https://lipperalpha.refinitiv.com/2021/03/20-years-of-starmine-smartestimates-20-years-of-outperformance/ `[READ]`
- "Benefiting from the SmartEstimate during times of uncertainty" (Lipper Alpha, 7 Aug 2020) — https://lipperalpha.refinitiv.com/2020/08/benefiting-from-the-smartestimate-during-times-of-uncertainty/ `[READ]` — **the single most mechanically detailed public page**
- "Forecasting Earnings Misses – StarMine Research Note" (Lipper Alpha, 3 Jul 2018) — https://lipperalpha.refinitiv.com/webcasts/2018/07/forecasting-earnings-misses-starmine-research-note/ `[READ]`
- "Learn How to Build Your Own StarMine Earnings Surprise Forecast" (Lipper Alpha, 24 Apr 2019) — https://lipperalpha.refinitiv.com/2019/04/learn-how-to-build-your-own-starmine-earnings-surprise-forecast/ `[READ]`
- StarMine SmartForecast Model whitepaper (Sanghi) — https://www.lseg.com/content/dam/data-analytics/en_us/documents/white-papers/lseg-starmine-smart-forecast-model-whitepaper.pdf `[READ]`
- LSEG product page — https://www.lseg.com/en/data-analytics/financial-data/analytics/quantitative-analytics/starmine-smartestimates `[READ]`

### 1.1 The algorithm, as far as public sources describe it

Two steps, in order: **(1) exclude, then (2) weight.**

**Step 1 — exclusions (three filters).** Verbatim from the 2020 Lipper Alpha page:

| Filter | Rule | Marker |
|---|---|---|
| **Age** | "Estimates older than **120 days** will have this marker displayed" and are excluded | `X-Age` |
| **RevisionCluster** | "when the majority of analysts revise their estimates in a short time window… any analyst who did **not** revise his or her estimate during this window will be **removed** from the SmartEstimate **until they submit a new estimate**" | `X-Cluster` |
| **Outliers / data errors** | "excludes stale estimates and suspected data errors" — rule not published | — |

The 120-day figure is the only hard number LSEG publishes and it reconciles with `street-process.md` §2.1's "~4 months".
The RevisionCluster concept traces to Haim Mozes (Fordham), named in the 2021 anniversary piece as the consultant
"who had been doing research on revision clusters".

**Step 2 — weighting.** "All remaining analysts who have passed the X-Age and X-Cluster criteria will be included…
Analysts receive a weight based on their 'Earnings Accuracy,' which is displayed through a **1 to 5-star ranking
system**. 5-star analysts represent the most accurate analysts and will receive a higher weight… the SmartEstimate
will be calculated as a **weighted average** of all analysts included."

Weight is a function of two things and two things only: **(analyst accuracy star rating, estimate age)**.
"The highest weight is placed on the most accurate analyst with a very recent estimate."

### 1.2 ⚠️ What LSEG does NOT publish — do not pretend otherwise

- **The functional form of the recency decay.** Linear? Exponential? Step? Never stated in any public document.
  Only that weight decreases with age and hits zero at 120 days.
- **The star → weight mapping.** 1–5 stars are described; the numeric weights are not.
- **The RevisionCluster window length** ("a short time window") or the "majority" threshold.
- **The outlier rule.**

Anyone claiming a specific decay function for SmartEstimate is inventing it. We will invent one too (§3), but we
label it as ours.

### 1.3 Predicted Surprise — the output

```
PS% = (SmartEstimate − I/B/E/S Mean) / |I/B/E/S Mean| × 100
```

The mean is "a simple average of all analysts **regardless of how old the estimate is**" — i.e. the stale,
equal-weighted number everyone else quotes. PS% is literally the de-staling delta.

### 1.4 Published hit rates — the complete set

| Study / vintage | Universe & period | Threshold | Hit rate |
|---|---|---|---|
| 2001, first publication | Russell 3000 | \|PS%\| > 2% | **~70%**, "consistent across large- and small-cap, growth vs value, and by sector" |
| Stauth & Bonne 2009 whitepaper | global | \|PS%\| ≥ 2% | **~70%** "across regions, market caps, sectors and financial measures" |
| Vieira, Genin & Birman 2018 | 9,000 securities (3,000 US + 500 CA + 2,000 Dev. Europe + 1,000 Dev. Asia ex-JP + 1,000 JP + 1,500 EM), **Jan 1998 – Nov 2017**, FY1 only, monthly | PS% ≤ **−2%** | **72.6%** vs **48.0%** base rate (+24.6pp) |
| — same, early sub-period | Jan 1998 – Nov 2008 | PS% ≤ −2% | **73.05%** |
| — same, late sub-period | Dec 2008 – Nov 2017 | PS% ≤ −2% | **71.97%** |
| Revenue PS% | — | \|PS%\| > 2% | **78%** |
| **EPS PS% + revenue PS% both significant, same period** | — | both > 2% | **78%** |
| SmartEconomics (macro analogue) | macro/FX/rates/commodities | significant | **~61%** |

Monotonicity: "The greater the PS%, the higher the hit rate." Corroboration: "SmartEstimates demonstrate an
improved accuracy at predicting earnings surprises when they are **accompanied by consensus revisions in the same
direction**." LSEG's US overlay of PS% + same-direction mean revisions reached **75%** over 36 quarters
(`street-process.md` §3.6).

**Analyst-accuracy persistence** (the justification for the accuracy weight): analysts most accurate in the past
are "roughly **four times** as likely to remain among the most accurate than to drop to the least accurate
category." Note the 2014 Alpha Factor piece states the symmetric claim (least-accurate also ~4× persistent),
which **contradicts** Sinha, Brown & Das (1997) — "superior" analysts persist, "inferior" ones do not
(`street-process.md` §3.6). Conflict noted; the asymmetric academic version is better identified.

Algorithm finalised **1999**; coverage ~16,000 equities globally, updated daily; PS% computed not just on EPS but
on every I/B/E/S line item (revenue, EBITDA, etc.).

### 1.5 The academic parameters we can actually implement

These matter more than the LSEG marketing numbers because they are stated as **error reductions**, which is what
our APE scoring rewards.

**Butler, Kraft & Markov (2007), "On the Weighting of Individual Analyst Forecasts in the Consensus"** —
https://scholar.smu.edu/business_accounting_research/71/ `[READ]`
> "in the case of forecasts issued in the **sixty days immediately preceding an earnings announcement**, the mean
> squared error of an informed consensus forecast whose component weights are based on **forecast age, broker
> size, and analyst experience** is significantly less than that of a naive consensus… **MSE-improvement ranges
> from three to fifteen percent**, respectively, as the number of forecasts in the consensus varies from **four to
> twenty**."

Two implementable parameters: **a 60-day inclusion window** (tighter than StarMine's 120), and **the gain scales
with analyst count** — 3% at N=4, 15% at N=20. Our names run N=4 (JBL) to N=13 (ADBE) on the current quarter,
so expect the **low end: ~3–8% MSE reduction**.

**Brown (2001), FAJ 57(6):44–49, "How Important Is Past Analyst Forecast Accuracy?"** —
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=202130 | https://doi.org/10.2469/faj.v57.n6.2492 `[READ]`
- I/B/E/S US Detail file, annual + quarterly, **1986–1998** (13 years), using **the last forecast made by each
  analyst prior to the earnings announcement**.
- Compares a **two-factor PASTACC model** (forecast age + past accuracy) against a **six-factor ANCHAR model**
  (forecast age + company-specific experience + general experience + #companies followed + #industries followed +
  brokerage size).
- **Result: PASTACC performs as well as ANCHAR**, in both estimation (adj. R²) and prediction (extreme-decile)
  tests, for both quarterly and annual data. "Past accuracy… is as important as five analyst characteristics
  combined."
- Brown explicitly names StarMine: "the StarMine SmartEstimate [is] based partly on past accuracy."

**Brown & Mohammad, "The Predictive Value of Analyst Characteristics"** —
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=271151 `[READ]` — **the load-bearing result for us:**
> "We compare the predictive ability of a consensus forecast based **solely on forecast age (Age)** with that of a
> six-factor model… **We show that Age predicts as well as Model** using both predictive ability criteria… analyst
> characteristics have **no relevance** for the purpose of obtaining better predictions of the next quarterly
> earnings number vis-à-vis a simpler model based on forecast age."

**This is why our inability to get per-analyst accuracy scores is survivable.** Recency alone is the whole game
for next-quarter EPS.

**Slavin (2007), "Aggregating Earnings per Share Forecasts"** — https://repository.upenn.edu/curej/67 `[READ]` —
quantifies the aggregation gain in cents, the cleanest magnitude anchor available:

| Weighting method | Median absolute forecast error | vs equal-weight |
|---|---|---|
| Equal weight (the published consensus) | **5.12¢** | — |
| Brown & Mohammad ordinal-rank weighting | **4.20¢** | **−18%** |
| Slavin Method 3 (linear in predicted accuracy) | 3.96¢ | −23% |
| Slavin Method 2 (squared predicted accuracy, above-average analysts only) | **3.66¢** | **−29%** |

**O'Brien (1988), JAE 10(1):53–83** — the foundational result: **the single most current forecast weakly dominates
both the mean and the median consensus** in accuracy. Forecast *dates* matter more than analyst identity.
This is the direct justification for using Zacks' "Most Recent Consensus" field (§3.2, signal S_rec).

---

## 2. What per-analyst / revision data is actually free — 9 sources tested

### 2.1 Verdict table

| Source | Endpoint | Per-analyst EPS + date? | Revision/staleness fields? | Qtrly revenue? | Status |
|---|---|---|---|---|---|
| **Zacks (direct HTML)** | `zacks.com/stock/quote/{T}/detailed-earning-estimates` | ❌ | ✅ **best available** | ✅ | **200 OK** `[TESTED]` |
| **Zacks earnings-calendar** | `zacks.com/stock/research/{T}/earnings-calendar` | ⚠️ **partial — recent revisions only** (§2.8) | ✅ dated prior→new | ✅ ~69 qtrs history | **200 OK** `[TESTED]` |
| Nasdaq (Zacks feed) | `api.nasdaq.com/api/analyst/{T}/earnings-forecast` | ❌ | ✅ up/down 4wk only | ❌ | 200 but **stale** `[TESTED]` |
| StockAnalysis | `stockanalysis.com/stocks/{t}/forecast/` | ⚠️ ratings/PT only | ❌ | ❌ (FY only free) | 200 `[TESTED]` |
| MarketBeat | `marketbeat.com/stocks/NASDAQ/{T}/earnings/` | ❌ | ❌ | ✅ | 200 `[TESTED]` |
| Yahoo (raw curl) | `query1.finance.yahoo.com/v10/finance/quoteSummary` | ❌ | ✅ (if reachable) | ✅ | **429** `[BLOCKED]` |
| Yahoo (`yahoo-finance2`) | library | ❌ | ✅ | ✅ | **not installed; Node v20.11.1 < v22 required** |
| TipRanks | `tipranks.com/stocks/{t}/forecast` + `/api/stocks/getData/` | — | — | — | **403 Cloudflare** `[TESTED]` |
| Benzinga | `api.benzinga.com/api/v2.1/calendar/earnings` | — | — | — | **401 key required** `[TESTED]` |
| Estimize | `estimize.com/{t}`, `/api/companies/{t}/estimates` | ⚠️ crowd, gated | — | — | page 200 / API **404**, data behind "Subscribe Now" `[TESTED]` |
| Zacks Data / WRDS | institutional | ✅ full detail | ✅ | ✅ | **paid** `[READ]` |

**Conclusion: no free source provides a *complete live panel* of per-analyst EPS estimates, so Version A (§3.1) —
a true SmartEstimate — remains unbuildable.** But the negative result is narrower than I first wrote: Zacks'
earnings-calendar page leaks a **rolling window of individual analyst revisions with dates** (§2.8), which is
enough for a fresh-reviser signal and a RevisionCluster detector, just not for a weighted average over all
analysts.

### 2.2 The Zacks page — full schema, tested

```
GET https://www.zacks.com/stock/quote/{TICKER}/detailed-earning-estimates
Header: User-Agent: Mozilla/5.0 (Macintosh; ...) Chrome/127.0.0.0 Safari/537.36
→ HTTP 200, ~156 KB, plain server-rendered HTML. No key, no cookie, no JS, no observed rate limit.
```

Verified 200 OK for NVDA, ADBE, ORCL, MU, JBL, AZO, COST (7/7) `[TESTED]`.
The quote page `zacks.com/stock/quote/{T}` also carries a condensed version (ESP, Most Accurate Est, Current Qtr
Est, Current Yr Est) — verified 9/9 tickers including AAPL and CRM `[TESTED]`.

Six `<section>` blocks, each a clean `<table>`. All grids are **4 columns: Current Qtr | Next Qtr | Current Year |
Next Year**, with the fiscal period in the header (e.g. `Current Qtr (7/2026)`).

| `section id` | Heading | Rows |
|---|---|---|
| `detailed_estimate` | Detailed Estimates | **Earnings Date** (e.g. `*AMC 8/26/26`), Current Quarter, EPS Last Quarter, Last EPS Surprise, ABR |
| `detailed_earnings_estimates` *(1st)* | **Sales Estimates** | Zacks Consensus Estimate, # of Estimates, High, Low, Year ago Sales, YoY Growth Est. |
| `detailed_earnings_estimates` *(2nd)* | **Earnings Estimates** | Zacks Consensus Estimate, # of Estimates, **Most Recent Consensus**, High, Low, Year ago EPS, YoY Growth Est. |
| `agreement_estimate` | Agreement — Estimate Revisions | Up Last 7/30/60 Days, Down Last 7/30/60 Days |
| `magnitude_estimate` | Magnitude — Consensus Estimate Trend | Current, **7 / 30 / 60 / 90 Days Ago** |
| `quote_upside` | Upside — Most Accurate vs Zacks Consensus | **Most Accurate Estimate**, Zacks Consensus Estimate, **Earnings ESP** |
| `surprised_reported` | Surprise — Reported Earnings History | last 4 quarters: Reported, Estimate, Difference, Surprise %, + **Average Surprise** |

Real output, NVDA, 15 Aug 2026 `[TESTED]`:

```
Sales Estimates          Cur Qtr(7/26)  Next Qtr(10/26)  Cur Yr(1/27)  Next Yr(1/28)
  Zacks Consensus            91.71B        101.88B         387.80B       547.00B
  # of Estimates                 10             10              14            12
Earnings Estimates
  Zacks Consensus              2.09           2.32            9.09         12.57
  # of Estimates                 12             11              18            14
  Most Recent Consensus        2.11           2.38            8.97         12.53
Agreement
  Up Last 7 / 30 / 60 Days      0 / 1 / 3
  Down Last 7 / 30 / 60 Days    0 / 0 / 0
Magnitude (consensus trend)
  Current / 7d / 30d / 60d / 90d ago:  2.09 / 2.09 / 2.09 / 2.07 / 1.93
Upside
  Most Accurate Estimate       2.09           2.40            8.95         12.92
  Zacks Consensus              2.09           2.32            9.09         12.57
  Earnings ESP               0.04%          3.25%          -1.56%         2.83%
Surprise (last 4 qtrs)      5.65%, 6.58%, 4.84%, 5.00%   → Average 5.52%
Earnings Date              *AMC 8/26/26
```

**This single page is the entire de-staling feature set plus the mechanical-beat prior plus the quarterly revenue
consensus.** It replaces Alpha Vantage `EARNINGS_ESTIMATES` (which `data-sources.md` §2.6 named as the only free
quarterly-revenue source) and removes its **25 requests/day** ceiling. Update `data-sources.md` §3.1 accordingly.

### 2.3 Parsing gotchas — all hit tonight

1. **`/detailed-estimates` 301-redirects to `/detailed-earning-estimates`** (singular "earning"). `[TESTED]`
2. **A browser `User-Agent` is mandatory.** Default curl UA → Zacks bot interstitial ("Pardon Our Interruption").
   Exa's fetcher hit the same wall on `zacks.com/earnings/...` pages. `[TESTED]`
3. **Label cells contain nested tooltip `<div>`s.** Strip `div.tooltiptext` and `div.tooltip-wrapper` *before*
   matching row labels, or `Earnings ESP` will not match (its `<dt>` is followed by a tooltip div, not `</dt>`).
4. **Both Sales and Earnings tables share `id="detailed_earnings_estimates"`.** Disambiguate by document order
   (Sales first) or by the section's `<h2>` text — not by id.
5. ⚠️ **ESP is computed on unrounded values; the displayed estimates are rounded to 2dp. Never recompute ESP from
   the displayed numbers.** `[TESTED]` AAPL displays Most Accurate 1.99 / Consensus 1.98 → naive recompute
   +0.51%, but the ESP field says **0.93%**. ADBE: displayed −0.33%, field **−0.28%**. COST: displayed +1.54%,
   field **+1.45%**. **Parse the ESP field verbatim.**
6. **`Most Recent Consensus` is sometimes absent** (JBL all horizons; COST current + next qtr). Handle null.
7. On the condensed quote page the ESP `<dd>` is the one immediately after the tooltip div with
   `id="key_earnings_esp_data"` — anchor on that id, not on the string "Earnings ESP" (which also appears in nav).

### 2.4 ⚠️ Nasdaq's Zacks feed is stale — measured

Same vendor (Zacks), same ticker, same quarter, same night `[TESTED]`:

| Channel | NVDA EPS, fiscal qtr ending Jul 2026 | N |
|---|---|---|
| `api.nasdaq.com/api/analyst/NVDA/earnings-forecast` | **2.01** | 11 |
| `zacks.com/.../detailed-earning-estimates` — Zacks Consensus | **2.09** | 12 |
| `zacks.com/.../detailed-earning-estimates` — Most Recent Consensus | **2.11** | — |

**A 5.0% spread between the oldest and newest number, from one vendor, on one night.** This is the staleness
thesis demonstrated inside a single data provider, and it is a good demo slide. It also confirms
`data-sources.md` §3 — **never benchmark against Nasdaq**. Use zacks.com direct.

### 2.5 Yahoo — unavailable tonight, documented for completeness

Raw curl to `query1.finance.yahoo.com/v10/finance/quoteSummary/NVDA?modules=earningsTrend` → **HTTP 429, body
`Too Many Requests`**. The crumb dance also fails: `fc.yahoo.com` returns 404 (expected, still sets `A3`), then
`/v1/test/getcrumb` returns the literal string `Too Many Requests`. `[TESTED]` — exactly reproducing
`data-sources.md` §3.2's TLS-fingerprint finding. **Do not fight this.**

`yahoo-finance2` is not installed in `web/` or `engine/`, and **Node here is v20.11.1 while v4 requires ≥22**. Per
the no-install constraint, Yahoo is out of scope tonight.

For the record, the fields we would have used `[READ]`, from `quoteSummary(sym, {modules:["earningsTrend"]})` →
`earningsTrend.trend[]`, one entry per period (`0q`, `+1q`, `0y`, `+1y`):
- `earningsEstimate: { avg, low, high, yearAgoEps, numberOfAnalysts, growth }`
- `revenueEstimate: { avg, low, high, numberOfAnalysts, yearAgoRevenue, growth }`
- `epsTrend: { current, 7daysAgo, 30daysAgo, 60daysAgo, 90daysAgo }`
- `epsRevisions: { upLast7days, upLast30days, downLast30days, downLast90days }`

**Yahoo's `epsRevisions` is asymmetric** (up at 7/30d, down at 30/90d) and frequently null. **Zacks' Agreement
table is strictly better**: symmetric up *and* down at 7/30/60 days, for all four horizons. Even with Yahoo
working, prefer Zacks for this signal.

### 2.6 What the other sources do and don't give

- **StockAnalysis** `[TESTED]` — the "Latest Forecasts" table gives **individual analyst name + firm + rating +
  action (Maintains/Reiterates) + price target + date** (e.g. `Timothy Arcuri, UBS, Buy, Maintains, $280,
  Aug 14 2026`), sourced from TipRanks. **No per-analyst EPS.** Still valuable: this is the raw material for the
  Wang et al. **BF_Score bundling signal** (`street-process.md` §3.5) — *price target moves up while EPS estimate
  doesn't* is a beat signal, and both halves are now free (PTs here, EPS trend from Zacks). Also gives dated
  analyst activity for a RevisionCluster proxy.
- **MarketBeat** `[TESTED]` — per-quarter Average/High/Low Estimate, Number of Estimates, Revenue Estimate,
  **Company Revenue Guidance**, GAAP EPS, Beat/Miss. **No per-analyst EPS estimates.** The guidance column is the
  interesting bit, not the estimates.
- **Estimize** `[TESTED]` — 126,291 contributors, claims "Estimize Consensus is consistently more accurate…than
  Wall Street consensus like Thomson Reuters I/B/E/S". Page loads but estimates are behind "Subscribe Now"; the
  old `/api/companies/{t}/estimates` endpoint 404s. Conceptually the closest thing to per-contributor dated
  estimates. **Not free.**
- **Zacks Data / WRDS** `[READ]` — https://zacksdata.com/datasets/consensus-data/ and
  https://www.zackspro.com/historical.asp confirm the detail file exists: *"Detailed Broker Estimates — Estimate
  Date, Brokerage Name, Analyst Name, Estimate Type, Annual/Quarterly/LTG, Prior Estimate, New Estimate"*,
  quarterly from 1982. Institutional/WRDS only. This is the dataset a real StarMine clone needs.

### 2.7 Zacks' own consensus rule — a material asymmetry

From the Zacks/WRDS one-sheet (https://wrds-www.wharton.upenn.edu/documents/1174/Zacks-One-Sheet.pdf) `[READ]`:
> "When a company issues guidance, Zacks will **drop all individual estimates made prior to the guidance that fall
> outside of its range**. Zacks includes all estimates made after the date of guidance. This policy removes
> outliers that are based on old information."

Zacks is **already partially de-staled**, guidance-anchored, and mechanically shrunk toward the guide
(`street-process.md` §2.1). Two consequences:

1. **The Zacks ESP is a de-staling delta measured against an already-de-staled base**, so it will be *smaller* than
   a true I/B/E/S-mean-based StarMine PS%. This partly explains why we measure |ESP| ≤ 1.69% on all seven names.
   Applying StarMine's ±2% threshold to a Zacks ESP is **not apples-to-apples** — the threshold should be lower.
2. **Beating the Zacks consensus is closer to "beating the guidance" than "beating the Street."** If the judge
   scores against a non-Zacks consensus, our benchmark and theirs differ (see `street-process.md` §2.4: NVDA's
   last print was $1.70 Zacks vs $1.76 MarketBeat — 3.75pp of surprise apart).

---

### 2.8 ✅ Zacks earnings-calendar — per-analyst dated revisions + ~55 quarters of history

Endpoint surfaced by the `eval-dataset-builder` agent and **independently re-tested here**:

```
GET https://www.zacks.com/stock/research/{TICKER}/earnings-announcements
  → HTTP 301 → http://www.zacks.com/stock/research/{TICKER}/earnings-calendar     ⚠️ redirects to HTTP, not HTTPS
GET https://www.zacks.com/stock/research/{TICKER}/earnings-calendar
  → HTTP 200, ~184 KB, browser UA required
```
Verified 200 + parseable for NVDA, ADBE, ORCL, MU, COST, AZO (6/6) `[TESTED]`.

The page embeds a single `document.obj_data` **JavaScript** (not JSON) object with **seven** tables:

| Key | Rows (NVDA) | Shape |
|---|---|---|
| `earnings_announcements_earnings_table` | **55** | `[report date, fiscal period, EPS estimate, EPS reported, Δ, surprise %, session]` |
| `earnings_announcements_sales_table` | **69** | same shape, **revenue in USD millions** |
| **`earnings_announcements_revisions_table`** | **9** | `[date, fiscal period, prior est, new est, analyst name, brokerage]` |
| `earnings_announcements_guidance_table` | 0 | `[date, point value, range]` — **semantics unverified, see below** |
| `earnings_announcements_dividends_table` | 56 | `[ex-date, amount, announced, payable]` |
| `earnings_announcements_splits_table` | 1 | `[date, ratio]` |
| `earnings_announcements_transcript_table` | 15 | `[date, call title, Aiera dashboard URL]` |

**The revisions table is the find.** Real NVDA rows `[TESTED]`:
```
["7/27/26", "1/2028 (FY)", "$12.50", "$12.53", "Hans Engel", "Erste Group"]
["7/27/26", "1/2027 (FY)", "$8.94",  "$8.97",  "Hans Engel", "Erste Group"]
["7/13/26", "1/2028 (FY)", "--",     "$13.45", "John Vinh",  "KeyBanc Capital Markets"]
```
This is **Estimate Date + Brokerage + Analyst Name + Prior Estimate + New Estimate** — precisely the Zacks detail
file I documented in §2.6 as WRDS/institutional-only. A slice of it is public.

**And it covers quarterly periods, not just annual** `[TESTED]` — NVDA carries `7/2026 (Q)`, `10/2026 (Q)`,
`1/2027 (Q)`, `4/2027 (Q)`, `7/2027 (Q)` alongside the `(FY)` rows. `7/2026 (Q)` is exactly our target quarter.

**Its limits, measured:**
- **Small and recent.** 2–12 rows per ticker, spanning ~2–6 weeks (NVDA 13–27 Jul; AZO 19 May–17 Jun). One
  revision event emits several rows (one per fiscal period), so the distinct-analyst count is smaller still —
  NVDA's 9 rows are ~3 analysts.
- **Revisers only.** We see analysts who *moved* and their new level; we never see the level of a non-revising
  analyst. So a true weighted mean over all live estimates is still impossible — hence Version A stays dead.
- COST returned only `(FY)` rows — quarterly coverage is not guaranteed per ticker.

**What it actually unlocks — provenance, not signal.** My first instinct was to build a "fresh-reviser mean" from
these rows and treat it as an independent de-staling measurement. **Testing killed that** (§2.10): the feed is
1–3 analysts per ticker, and its newest row is *identical* to the grid page's `Most Recent Consensus` in 5/5
cases — so it is not independent of `S_rec`, it **is** `S_rec`'s provenance. What that provenance buys is real
but defensive: it tells us **who** moved the number (a 5-star specialist? a generalist? Zacks' own in-house
team?) and whether the move merely restates published guidance. Both are quality gates on `S_rec`, and both
turned out to be necessary.

*(An earlier draft cited NVDA's freshest FY1 estimate of $8.97 vs a $9.09 consensus agreeing in sign with the
−1.56% Current-Year ESP as mutual corroboration. That was wrong — with 1–2 revisers the two are not independent
draws, so agreement is not evidence.)*

It also gives a direct **RevisionCluster (X-Cluster) detector** — StarMine's second exclusion filter (§1.1) — which
I had listed as unimplementable: count distinct analysts revising within a rolling 5-day window and compare to
`# of Estimates` from the detailed-estimates page.

**Parsing notes** `[TESTED]`: `obj_data` is JS, not JSON — locate the key, then brace-balance while tracking
string state and escapes, then `eval()` (or JSON5). Cell values carry `<div>`/`<span>` wrappers that must be
stripped. Node's global `fetch` gets a ~6 KB bot wall where `curl -A '<browser UA>'` gets the full page — shell
out to curl. The `eval-dataset-builder` reports 243/249 tickers parsed; EA, IPG, K, MMC, DFS and BK return the
page with no `obj_data`, so **always null-check**.

❌ **`guidance_table` — RESOLVED: it is NOT company guidance. Do not build on it.** Reconciled by
`eval-dataset-builder` against the ADBE and ORCL 8-Ks. ADBE's 11 Jun 2026 rows are `$4.61 (4.51–4.71)` and
`$19.14 (18.84–19.53)`; Adobe's five actually-guided figures that day were Q3 revenue $6.67–6.72bn, Q3 non-GAAP
EPS $6.05–6.10, FY revenue $26.5–26.6bn, FY non-GAAP EPS $24.35–24.45, FY GAAP EPS $17.90–18.00 — **none of
them**. ORCL's `$1.32 (1.22–1.42)` is not Oracle's guided Q1 FY27 non-GAAP EPS of $1.72–1.76 either. Magnitudes
are consistent with a forward **GAAP** EPS point plus an analyst high/low band, i.e. **the wrong basis** for
everything else we use. Coverage is fatal regardless: **AAPL's most recent row is 2 Nov 2017.**
→ **`data-sources.md` §5 stands: no free structured guidance dataset exists.** Guidance still has to come from
the 8-K EX-99.1 text.

✅ **The `revisions_table` IS on our basis — non-GAAP street EPS, no conversion needed.** Same reconciliation:
ADBE `8/2026 (Q)` $6.08 vs guided Q3 non-GAAP $6.05–6.10; ADBE `11/2026 (FY)` $24.40 vs guided FY26 non-GAAP
$24.35–24.45; ORCL `5/2027 (FY)` $8.05 vs guided FY27 non-GAAP $8.05 exactly. It joins directly to the
detailed-estimates grid. But read §2.10 before using it for anything — those same three rows are the evidence
that the revisions *echo guidance* rather than forecast independently.

### 2.9 ⚠️ Zacks' consensus is biased high vs the other vendors

From `eval-dataset-builder`'s 87-event cross-vendor comparison `[READ — their measurement, not mine]`:

- Zacks consensus runs **systematically 1–4% above LSEG/S&P Global** on the same event: UNH 4.94 vs 4.90,
  CVS 1.87 vs 1.85, ADBE 5.83 vs 5.82, MU 21.39 vs 20.78.
- **Actuals agree to the cent across every source.** All the cross-vendor uncertainty sits in the consensus column.
- Median Zacks-vs-S&P-Global gap: **1¢ on EPS, 0.32% on revenue.**

**This and §2.7 are one phenomenon, not two.** Zacks *drops* pre-guidance estimates falling outside the guided
range (§2.7), and the estimates that survive or arrive afterwards *echo the guide* (§2.10c). Both ends push the
same way: the Zacks consensus is a **guidance-anchored** number, cleansed of stale low-balls and repopulated with
guidance-followers. That single mechanism explains the whole 1–4% upward bias, and it also explains why |ESP| is
so small on our names (§3.4) — when the panel has converged on the guide there is little dispersion left for a
recency-and-accuracy reweighting to exploit. **The corollary is uncomfortable and worth saying: on a
just-guided, EPS-guiding company, "de-staling the consensus" and "reading the guidance" are close to the same
trade.**

**Two consequences for this module, both material:**

1. **Our forecast inherits the bias.** The §3.2 formula anchors on `C_eps` from Zacks. If the judge scores against
   an LSEG- or S&P-Global-derived consensus, we start ~1¢ high on EPS before any tilt is applied — comparable in
   size to the entire de-staling tilt we are trying to add. **Cross-check `C` against StockAnalysis (S&P Global)
   for the target names and consider anchoring on the mean of the two.**
2. **A Zacks-measured beat prior is understated.** Higher consensus, identical actual ⇒ smaller measured surprise.
   The beat prior calibrated on Zacks history (§4.2 V1) is a *conservative* estimate of the beat against a
   lower-set benchmark. Do not then also apply it to a lower consensus without rescaling.


### 2.10 ⚠️⚠️ "Most Recent Consensus" is ONE analyst — and the reviser pool is adversely selected

The most important negative finding in this document, and a correction to my own first draft. Three problems,
all measured.

**(a) MRC is not an aggregate.** Cross-checking the grid page's `Most Recent Consensus` against the newest row of
the `revisions_table` for the same fiscal period, **they are identical in 5 of 5 testable cases** `[TESTED]`:

| Ticker | Target period | Most Recent Consensus | Newest reviser's new estimate | Match | Who |
|---|---|---|---|---|---|
| NVDA | 7/2026 (Q) | 2.11 | 2.11 | ✅ | John Vinh / KeyBanc |
| ADBE | 8/2026 (Q) | 6.08 | 6.08 | ✅ | Jackson Ader / KeyBanc |
| ORCL | 8/2026 (Q) | 1.76 | 1.76 | ✅ | Jackson Ader / KeyBanc |
| MU | 8/2026 (Q) | 32.36 | 32.36 | ✅ | John Vinh / KeyBanc |
| AZO | 8/2026 (Q) | 54.63 | 54.63 | ✅ | **Zacks Research (in-house)** |

So `(MRC − C)/C` is a **single analyst's deviation from consensus**, not a fresh-panel mean. It must be shrunk
~20% toward consensus for anti-herding overshoot (BCK 2006 — `street-process.md` §3.7), and any spec that blends
MRC with a separately-computed "fresh reviser mean" is counting the same person twice. Mine did; fixed in §3.2.

**(b) The reviser pool is tiny and adversely selected.** Distinct revisers in the last ~45 days `[TESTED]`:

| Reviser | Appears in |
|---|---|
| **Hans Engel / Erste Group** | **5 of 6 tickers** (NVDA, ADBE, ORCL, MU, COST) |
| John Vinh / KeyBanc | 2 (NVDA, MU) |
| Jackson Ader / KeyBanc | 2 (ADBE, ORCL) |
| Patrick Colville / Scotiabank | 1 (ORCL) |
| **"Research Team" / Zacks Research** | 1 (AZO) — **not a broker** |

Per-ticker distinct revisers: NVDA 2, ADBE 2, ORCL 3, MU 2, COST 1, AZO 1.

Two things are wrong here. One analyst — a generalist at a small Austrian bank — supplies the freshest estimate
on five wildly different companies. Clement & Tse (2005) find accuracy **falls** with the number of industries
covered; this is the *low*-accuracy profile, the exact opposite of the 5-star analyst StarMine up-weights. And
**AZO's only reviser is Zacks' own in-house research team**, so for AZO the "de-staled" number is Zacks marking
its own homework. **Filter `Research Team / Zacks Research` by name.**

**(c) The revisions largely echo guidance.** Verified by `eval-dataset-builder` against the ADBE and ORCL 8-Ks:
ADBE `8/2026 (Q)` $6.08 vs guided Q3 non-GAAP **$6.05–6.10**; ADBE `11/2026 (FY)` $24.40 vs guided FY26 non-GAAP
**$24.35–24.45**; ORCL `5/2027 (FY)` $8.05 vs guided FY27 non-GAAP **$8.05 exactly**. These are post-print
revisions landing *on* the guided number. The good news is that this confirms the feed is on **non-GAAP street
basis** — it joins to our other data with no conversion. The bad news is that a tilt built on it is closer to a
guidance-follower than an independent information edge, and it overlaps the guidance-midpoint baseline.

**Net effect on the recommendation:** `S_fresh` is deleted as a separate signal, `S_rec` is shrunk 0.8×,
provenance-gated, cut from weight 0.30 to 0.20, and must be orthogonalised against any guidance module (§3.2).
The revisions table's real value turns out to be **provenance and QC on `S_rec`** — telling us *who* moved the
number and whether they are a broker or Zacks itself — not a signal of its own.


---

## 3. The practical algorithm — three versions

All versions output a **de-staling tilt** `PS_destale` (a signed fraction applied to consensus), *not* a finished
forecast. The mechanical-beat prior (`street-process.md` §3.1–3.2), the guidance-upper-bound tilt (§3.4) and the
CAF anchoring factor (§3.5) are separate modules; this one must not double-count them.

```
EPS_hat = C_eps × (1 + PS_destale + PS_beat + PS_guidance + ...)
```

### 3.1 Version A — "full": per-analyst estimates × recency decay

**STILL NOT BUILDABLE**, but for a narrower reason than "the data doesn't exist". Zacks' `revisions_table` (§2.8)
gives per-analyst dated estimates for the analysts who **recently revised** — never the current level of a
non-revising analyst. A SmartEstimate is a weighted average *over all live estimates*, so a feed that shows only
the movers cannot produce one. And testing showed the movers are 1-3 analysts whose newest estimate simply IS
the `Most Recent Consensus` field (§2.10) - so there is no extra signal there either.
Documented so we can say we checked, and so nobody re-litigates it at 3am.

Had we had them, the spec would be — a defensible public-information reconstruction of StarMine:

```
For each analyst i with estimate e_i issued a_i days ago, for fiscal period p:
  1. Drop if a_i > 120                                  (StarMine X-Age)
  2. Drop if a RevisionCluster occurred at t_c and analyst i has not revised since t_c
     (cluster = ≥50% of covering analysts revised within any 5-trading-day window)
  3. Drop if |e_i − median(e)| > 3 × MAD(e)             (our outlier rule; LSEG's is unpublished)
  4. w_i = A_i × R(a_i)
       R(a)  = max(0, 1 − a/120)          linear decay to zero at the X-Age boundary
       A_i   = accuracy weight ∈ [0.5, 2.0], from the analyst's trailing-8-quarter PMAFE,
               weighted as Slavin Method 2: A_i ∝ PMAFE_i² for above-median analysts, 0 otherwise
  SmartEstimate = Σ w_i e_i / Σ w_i
  PS% = (SmartEstimate − mean(e)) / |mean(e)|
```
Per Brown & Mohammad (§1.5), setting `A_i ≡ 1` (recency only) should cost almost nothing.
**Cost if data existed: ~150 LOC. Cost in reality: unbuildable.**

### 3.2 Version B — "proxy": the Zacks composite ✅ RECOMMENDED

One HTTP GET per ticker. Everything below is a field verified present tonight.

**Inputs** (per ticker, per horizon; use `Current Qtr` unless the target quarter is the next one):

| Symbol | Field |
|---|---|
| `C` | Zacks Consensus Estimate (EPS) |
| `C_rev` | Zacks Consensus Estimate (Sales) |
| `MRC` | Most Recent Consensus (EPS), nullable |
| `MA` | Most Accurate Estimate (EPS) |
| `ESP` | Earnings ESP, **parsed verbatim as a percentage** |
| `E7,E30,E60,E90` | consensus 7/30/60/90 days ago |
| `U7,U30,U60 / D7,D30,D60` | up/down revision counts |
| `N` | # of Estimates |
| `d` | trading days from today to the Earnings Date (same page) |
| `b` | Average Surprise, last 4 quarters |

**Three orthogonal components.** They must be kept separate — measured tonight, they disagree strongly
(MU has ESP = 0.00% but +41% 90-day revision momentum), so they carry independent information.

**(a) Accuracy tilt** — the direct StarMine PS% analogue. Zacks' Most Accurate Estimate is explicitly built by
"weighting individual analyst estimates by their **timeliness** and by their **historical accuracy**"
(https://www.zackspro.com/models.asp) — the same two factors as SmartEstimate, and the same two factors Brown
(2001) validated.
```
S_acc = ESP / 100
```

**(b) Recency tilt** — O'Brien (1988): the most current forecast weakly dominates the mean.

⚠️ **Corrected after testing — see §2.10. "Most Recent Consensus" is not a consensus at all; it is the single
most recent analyst's estimate** (verified 5/5). An earlier draft of this spec blended it 50/50 with a
"fresh-reviser mean" computed from the revisions table. That was **double-counting one analyst**, and it is
deleted. There is exactly one recency signal, and it must be shrunk and quality-gated:

```
# Gate first — provenance from revisions_table (§2.8), the target period's newest row:
if reviser is "Research Team / Zacks Research":   S_rec = 0     # Zacks' own in-house estimate, not a broker
if the revision's new value lies inside company guidance issued in the interim: down-weight (see below)

S_raw  = (MRC − C) / C          if MRC present else 0
S_rec  = 0.8 × S_raw                                            # anti-herding shrinkage
```

`0.8` is **not** a free parameter — it is Bernhardt, Campello & Kutsoati (2006, JFE 80(3):657–675) as already
recorded in `street-process.md` §3.7: a lone analyst deviating from consensus **overshoots by ~20% of the
(forecast − consensus) difference**, and that note's own build instruction is "shrink individual estimates ~20%
back toward consensus to recover an analyst's true belief." Taking MRC at face value is precisely the
over-extrapolation that paragraph warns against. My first draft did exactly that.

**(c) Drift tilt** — the consensus is *itself* still moving; extrapolate what it will be at the print, damped.
```
Pick the shortest window with a non-zero move (revisions cluster then go quiet — street-process §1.3):
  if C ≠ E7  : r = (C−E7)/E7,   w = 7
  elif C ≠ E30: r = (C−E30)/E30, w = 30
  elif C ≠ E60: r = (C−E60)/E60, w = 60
  else        : r = (C−E90)/E90, w = 90

S_drift = clamp( (r / w) × d × λ , −0.02, +0.02 )      with λ = 0.35
```
`λ = 0.35` is **our parameter, not a published one.** Rationale: FactSet's 20-yr per-month walk-down
decomposition is −1.9pp / −1.3pp / −1.0pp for months 1/2/3 (`street-process.md` §1.4), so the drift rate roughly
halves as the print approaches; and §1.3 says the post-print revision cluster is followed by near-silence.
Un-damped linear extrapolation of MU's +41%/90d over 30 days to its print would add **+13%** — obviously wrong.
The ±2% clamp is the real safety net. **Flag λ and the clamp as judgement calls in the demo.**

**(d) Breadth — a confidence multiplier, not a magnitude.**
```
net = (U60 − D60) / max(N, 1)
conf = 1.15  if sign(net) == sign(PS_raw) and |net| ≥ 0.25     (LSEG: corroborating revisions → 70% → 75%)
     = 0.70  if sign(net) == −sign(PS_raw) and |net| ≥ 0.25
     = 1.00  otherwise
```

**(e) RevisionCluster gate** — StarMine's X-Cluster filter (§1.1), now implementable from §2.8:
```
cluster = ∃ a rolling 5-trading-day window in revisions_table containing
          ≥ 0.5 × N distinct analysts revising the target period
if cluster and the newest revision is more recent than the cluster:
    conf ×= 1.15      # material event; the freshest estimates carry unusual weight
```
StarMine's actual response to a cluster is to *drop* non-revisers from the mean. We cannot do that (we never see
non-revisers' levels), so we approximate the same intent by up-weighting the signal instead. **Our substitution,
not LSEG's rule.** Expect this to fire rarely — none of the six tickers tested had ≥50% of analysts revising in
any 5-day window.

**Composite:**
```
PS_raw     = 0.60·S_acc + 0.20·S_rec + 0.20·S_drift
PS_destale = clamp( PS_raw × conf , −0.03, +0.03 )
if |PS_destale| < 0.003:  PS_destale = 0        # dead-band, see §3.4
```

Weights are **literature priors, not fitted** (we cannot fit — §4). `S_acc` carries the most weight because it is
the only genuine *multi-analyst* aggregate we have — Zacks' Most Accurate Estimate is built over the whole
covering panel, weighted by timeliness and accuracy. `S_rec` was cut from 0.30 to 0.20 once testing showed it is
one analyst rather than a fresh-analyst consensus (§2.10) and that those revisions substantially echo published
guidance (§2.10 (c)). `S_drift` is unchanged: noisiest, most extrapolative, but a true panel-wide measure.

⚠️ **Orthogonality requirement — gate on `Q_EPS`, not on "guides EPS".** If the build also ships a guidance module
(`street-process.md` §3.4 / the evals doc's `B3` guidance-midpoint baseline), `S_rec` **overlaps it** and the two
must not simply be summed.

The right cut is **whether the company guides *next-quarter* EPS**, not whether it guides EPS at all — a company
guiding only an annual EPS range still leaves the quarterly split to the analyst, so its quarterly revisions are
genuine modelling work rather than echo. Regime classification for all 87 eval events is in
`eval-dataset-notes.md` §5.4 as a `GUIDANCE_REGIME` object, four exhaustive buckets:

| Regime | n | Meaning | `S_rec` treatment |
|---|---:|---|---|
| `Q_EPS` | 20 | guides next-quarter EPS | **echo-contaminated → residualise or drop `S_rec`** |
| `FY_EPS` | 35 | annual EPS range only | keep — quarterly split is the analyst's own work |
| `NO_EPS` | 27 | no EPS guidance | keep — cleanest case for the tilt |
| `FFO` | 5 | REITs, FFO/share | keep |

`Q_EPS` roster: ADBE, AMAT, APH, GLW, JBL, LRCX, MU, NXPI, ON, ORCL, TER, TXN, WDC, NFLX, IQV, LIN, PPG, HLT,
MAR, RCL. **NVDA is not in the eval set** (reports 26 Aug) — which is a shame, because it is the cleanest natural
experiment available: it guides revenue, gross margin and opex but **not** EPS, so its analysts must model EPS
themselves. `NO_EPS`'s 27 rows are the broader stand-in.

Concretely: **before shipping `S_rec`, check whether it beats "just use the guidance midpoint" on `Q_EPS` names —
if it doesn't, drop it there and let the guidance module own that information.** `0.60·S_acc + 0.20·S_drift`
stands on its own. Caveat if citing the classification: it is domain knowledge, not scraped from 8-Ks, and DIS,
VZ, CL, MDLZ, PEP, PG and V guide EPS *growth %* rather than a $ range — read the 8-K if a decision rests on one.

**Revenue.** The Zacks page gives revenue consensus and analyst count but **no revenue trend, no revenue
revisions, no revenue ESP** — and neither does any other free source (Alpha Vantage has `revenue_estimate_*` but
its `*_days_ago` and revision fields are **EPS-only**). So revenue de-staling must be transferred from EPS:
```
PS_destale_rev = ρ × PS_destale          ρ = 0.27
```
`ρ = 0.27` = the ratio of typical index-level surprise magnitudes, revenue vs EPS: **+1.91% / +7.1%**
(`street-process.md` §3.2). Use the sector-specific ratio from that table where available (e.g. Technology
2.19/6.4 = 0.34; Financials 3.29/8.3 = 0.40; Consumer Staples 0.41/3.7 = 0.11).

⚠️ **This is the painful gap: StarMine's *highest* hit rate is revenue PS% at 78%, and revenue PS% is precisely
the thing free data cannot compute.** We get it only as a scaled echo of the EPS signal. Say so out loud rather
than implying a 78% signal we don't have.

**Implementation cost: two fetches per ticker** (`/detailed-earning-estimates` for the grid, `/earnings-calendar`
for the `S_rec` provenance gate + cluster detection) **+ ~120 lines of table parsing + ~50 lines of `obj_data`
brace-balancing + ~40 lines of arithmetic. Roughly 90 minutes.** The second fetch is optional but *recommended*:
without it you cannot tell whether `S_rec` came from a broker or from Zacks' own in-house team (§2.10), and on
our sample that check zeroed one ticker in six.

### 3.3 Version C — "piggyback": ESP alone

```
PS_destale = ESP/100  if |ESP| ≥ 2%  else 0
```
~30 lines. **Fires on 0 of 7 candidate names tonight** (§3.4) — i.e. it degenerates to "use the consensus".
Keep as the fallback if Version B's parser breaks under demo pressure; it needs only the condensed quote page,
which is a smaller and more stable scrape.

### 3.4 ⚠️ Measured signal magnitudes — the reality check

All seven dossier tickers, `Current Qtr`, pulled 15 Aug 2026 `[TESTED]`:

| Ticker | ESP (S_acc) | MRC gap — **1 analyst, see §2.10** | 90-day drift | 30-day drift | \|ESP\| ≥ 2%? |
|---|---|---|---|---|---|
| NVDA | +0.04% | +0.96% | **+8.29%** | 0.00% | no |
| ADBE | −0.28% | 0.00% | +5.92% | +0.50% | no |
| ORCL | 0.00% | **+2.33%** | +1.18% | 0.00% | no |
| MU | 0.00% | **+3.09%** | **+41.08%** | 0.00% | no |
| JBL | 0.00% | n/a | **+10.35%** | 0.00% | no |
| AZO | **−1.69%** | −0.82% | −0.09% | −0.47% | no |
| COST | +1.45% | n/a | 0.00% | 0.00% | no |

Five things to take from this:

1. **The StarMine ±2% gate never fires.** Version C is inert on our universe. Because the Zacks ESP is computed
   against an already-guidance-anchored consensus (§2.7), the honest threshold for *this* dataset is lower —
   the **0.3% dead-band** in §3.2 is set from the observed distribution, not from LSEG's 2%.
2. **ESP and drift are nearly orthogonal.** MU: ESP 0.00% but +41% 90-day drift. NVDA: ESP +0.04% but +8.3% drift.
   The Most Accurate estimate has caught up with the news; the *consensus* already moved too. Both are "post-
   revision-cluster quiet". A single-signal model would throw this away.
3. **30-day drift is ~zero almost everywhere.** Textbook confirmation of `street-process.md` §1.3 — revisions
   cluster right after the print (visible in the 60–90d window) then go near-silent. We are currently *in* the
   quiet zone, which is exactly when a stale consensus is most stale but also when nothing new is arriving.
4. ⚠️ **`Most Recent Consensus` is the liveliest column — and the least trustworthy. Read §2.10 before using it.**
   ORCL +2.33% and MU +3.09% are the only values in this table that clear ±2%, which is exactly why the first
   draft of this spec leaned on them. But both are **a single analyst** — Jackson Ader (KeyBanc) on ORCL, John
   Vinh (KeyBanc) on MU — not a fresh-panel mean. AZO's −0.82% is Zacks' own in-house team, not a broker at all.
   After the 0.8× anti-herding shrink these become +1.86% and +2.47%, and after the provenance gate AZO's goes to
   zero. **The apparent strength of this column was an artefact of mistaking one analyst for a consensus**, and
   its weight went *down* from 0.30 to 0.20 as a result — the opposite of what this line originally said.
5. **Coverage is thin.** N = 4–13 estimates on the current quarter. Butler-Kraft-Markov's gain at N=4 is **3%**,
   at N=20 it's 15%. We are at the bottom of that range.

### 3.5 ⚠️ Direction ≠ APE — do not quote the 70%

Every headline number in §1.4 is a **directional hit rate** (did the surprise have the right sign). Our scoring is
**APE against the actual**, and we must beat the consensus's APE. A signal can be 70% directionally right and
still lose on APE if the magnitude is wrong.

The numbers that actually forecast our gain are the **error-reduction** results (§1.5):

| Source | Metric | Value | Applicable to us? |
|---|---|---|---|
| Butler, Kraft & Markov | MSE reduction, N=4 | **3%** | ✅ JBL (N=4–5) |
| Butler, Kraft & Markov | MSE reduction, N=20 | 15% | ❌ nothing near N=20 |
| Brown & Mohammad | median abs. error | −18% (5.12¢→4.20¢) | ⚠️ full detail file |
| Slavin Method 2 | median abs. error | −29% (→3.66¢) | ⚠️ full detail file |

Realistic expectation for **Version B on N≈10 names: a 3–8% relative reduction in EPS error.** On a consensus EPS
APE of ~7%, that is **~0.2–0.6pp of APE**. Real, free, and small. It is a tiebreaker, not the thesis. The
mechanical-beat prior (+3.5% to +7% systematic) is a far larger term — de-staling should be sized *below* it.

---

## 4. Validation plan

### 4.1 ⚠️ The blocking constraint: point-in-time revision data is not retrievable

To backtest Version B on Q2-CY2026 we would need the ESP / Most Accurate / estimate-trend **as they stood before
each print**. We cannot get them:

- **Zacks serves current vintage only.** No date parameter on the page. `[TESTED]`
- **Zacks' historical detail file** (Estimate Date, Brokerage, Analyst, Prior/New Estimate, quarterly from 1982)
  exists but is **WRDS / institutional, paid**. `[READ]`
- **Wayback is unreachable from this machine** — `web.archive.org` CDX and availability APIs both fail with
  `LibreSSL/3.3.6: error:1404B419 SSL routines:ST_CONNECT:tlsv1 alert access denied`, and the WebFetch tool is
  also blocked for that host. `[BLOCKED]` Even if reachable, per-ticker Zacks quote pages are unlikely to be
  archived at the density (daily, pre-print) a backtest needs.
- **Nasdaq / Alpha Vantage / StockAnalysis / MarketBeat** all serve current vintage only.
- **The `revisions_table` (§2.8) does NOT rescue this.** It is a rolling ~2–6 week feed — NVDA's oldest row is
  13 Jul 2026 `[TESTED]`. It tells us about revisions into the *upcoming* print, not what the estimate panel
  looked like before a print two quarters ago. The `S_rec` provenance gate is therefore *available today,
  forward* but **not reconstructable historically**, exactly like ESP.

**Therefore: the de-staling tilt still cannot be validated in-sample before tomorrow. Say this plainly rather than
producing a backtest that silently uses today's ESP against a past quarter — that is look-ahead bias and it would
make the signal look far better than it is.**

**What *did* change:** the `earnings-calendar` tables (§2.8) give ~55 quarters of frozen consensus-vs-actual for
EPS and ~69 for revenue. That does not validate the *de-staling tilt*, but it fully validates the **beat prior**
and gives us a real distribution of surprise magnitudes per company — the larger term in the forecast (§3.5).
The split is worth stating precisely, because it is easy to blur: **historical outcomes are free and deep;
historical expectations-at-a-point-in-time are not available at any price we can pay tonight.**

### 4.2 What we *can* validate on `data/seed/eval_events.csv` (now built — 87 events)

**V1 — Ground truth is free and *deep*.** Two sources, use the second:
- `surprised_reported` on the detailed-estimates page — last **4 quarters**, EPS only `[TESTED]`.
- **`earnings-calendar`'s `obj_data` (§2.8) — ~55 quarters of EPS and ~69 of revenue**, each with the consensus
  *as frozen at the report date*, the actual, and the surprise `[TESTED]`. This is ~14 years of point-in-time
  consensus-vs-actual per ticker, for both metrics, in one request.

That second one is a genuine upgrade over what I first wrote: the **beat prior can be estimated on ~40+ usable
quarters instead of 4, and on revenue as well as EPS.** Measured tonight, EPS average surprise: NVDA +5.52%,
MU +21.1%, JBL +5.9%, AZO +0.0%, ADBE +2.5%, ORCL +12.9%, COST +1.0% — but ORCL's mean is distorted by a single
+38.65% quarter, so **use the median over a long window, not Zacks' 4-quarter mean.** NVDA's revenue surprises
(+3.63%, +4.14%, +4.14%) are visibly tighter and more stable than its EPS surprises, consistent with
`street-process.md` §3.2.

Two cautions on this table:
- **Zacks' actual is not always on the consensus basis.** Per `eval-dataset-builder`: Alphabet Q2-2026 is
  recorded as GAAP 9.11 (including a ~$98bn unrealised gain) against a 2.88 adjusted consensus, and its revenue
  is stated ex-TAC; Merck shows −0.26 vs +0.23 at S&P Global. **Screen `|surprise| > 40%` and hand-check** — this
  is the same GAAP/non-GAAP trap `data-sources.md` §1.10 flags as the biggest silent scoring failure.
- The consensus column carries Zacks' upward bias (§2.9), so surprises measured here are systematically
  *understated* relative to an LSEG-benchmarked scorer.

**V2 — Cross-sectional distribution check (do this tonight, ~20 min).** Scrape ESP + trend + agreement for
~100–200 names reporting in the next 3 weeks and check:
- Is the ESP distribution centred on zero, and what fraction exceed ±2% / ±0.5%? (Our 7-name sample says the ±2%
  tail is nearly empty — confirm at scale before committing the gate.)
- Correlation between `S_acc`, `S_rec` and `S_drift`. If they are as orthogonal as the 7-name sample suggests,
  the 3-component composite is justified; if `S_acc ≈ S_rec`, collapse them and reweight.
- Distribution of `d` (days to print) — the `S_drift` extrapolation is only sane for small `d`.
**This validates the *construction*, not the *predictive power*. It is the honest limit of what today allows.**

**V3 — Forward paper-trade (the only clean test; results land after the event).** Freeze tonight's
`(ticker, as_of_ts, C, MRC, MA, ESP, E7/30/60/90, U/D, N, earnings_date)` into SQLite, then score against actuals
as they print (NVDA 26 Aug, ADBE/ORCL/MU/JBL/AZO/COST late Aug–Sep). Costs one script and one cron. It will not
produce numbers by Sunday, **but standing up the snapshot table tonight is what makes any future claim
defensible** — and demoing the frozen table is a credible answer to "how do you know this works?"

**V4 — Leakage note.** The LLM-memorisation hazard in `street-process.md` applies to *reasoning over past
quarters*, not to this module: ESP is a numeric feature, and the constraint here is data availability, not
contamination. Separately, Q2-CY2026 actuals printed Jul–Aug 2026, i.e. **after** the assistant's May 2026
knowledge cutoff, so those events are clean for LLM-based components too.

### 4.3 ⚠️ The regime-vs-accuracy comparison is withdrawn — and the unit question has a real answer

**Status: the claim that "consensus is most accurate where there is no EPS guidance" is withdrawn by its author**
(`eval-dataset-notes.md` §5.4). It flips under a defensible change of unit, and a result that flips under a
change of unit is not a result. Recomputed in both units, n=87:

| Regime | n | med consensus EPS | med abs err ¢ | med APE |
|---|---:|---:|---:|---:|
| `Q_EPS` | 20 | $2.66 | 13.0¢ | **3.90%** |
| `FY_EPS` | 35 | $1.88 | 14.0¢ | 7.34% |
| `NO_EPS` | 27 | $1.73 | **9.0¢** | 7.84% |
| `FFO` | 5 | $1.53 | 8.0¢ | 3.23% |

Cents rank `NO_EPS` best; APE ranks it worst. Neither ordering is evidence about our module.

**Two corrections to what I argued, both mine:**

1. **My mechanism was wrong even though the direction was right.** I claimed the inversion came from *between*-
   regime EPS levels (`NO_EPS` ≈ $1.50 banks vs `Q_EPS` ≈ $6 software). Median consensus EPS is **$1.53–$2.66
   across all four regimes — essentially flat.** The inversion is driven by each regime's **low-EPS tail**, not
   its centre: within-regime spread (`Q_EPS` $0.72–$21.39, `NO_EPS` $0.32–$12.67) dwarfs the between-regime gap.
2. **My MU figure was wrong.** I cited MU's consensus as $31.39. That is its **8/2026 forward quarter** from
   tonight's Zacks pull; the eval event is the quarter ending 5/2026, whose consensus was **$21.39** (reported
   $25.11, +17.39%) — confirmed in Zacks' own `surprised_reported` table. **Mixing a forward estimate with a
   historical event's consensus is exactly the error this document warns others about** (§4.1); logged so it is
   not repeated.

**And my prescription was wrong, which matters more than either.** I recommended recomputing as
`median(|surprise| / consensus)`. That is mean/median **APE on EPS, which the evals doc §3.4 explicitly bans** —
undefined at zero, explosive near zero, and dominated by the least economically meaningful names. Its primary EPS
metric is **cents**, resting on Cheong & Thomas's scale-invariance result. Reporting both units and concluding
from neither is the correct handling; switching to the banned metric is not.

**The reconciliation worth keeping** (these were being conflated, by me included): **per-event APE is the
competition's scoring rule; aggregate median-APE across events is a banned statistic.** Both are true. A single
event with a known non-zero consensus has a well-defined APE — that is what we are scored on. Averaging APE over
a heterogeneous event set is a different object, and near-zero-EPS names make it meaningless. Never let the first
justify the second.

**The finding that outranks the regime question** — from `eval-dataset-notes.md` §6.7:
```
Spearman rho( |consensus EPS| , |EPS error in cents| ) = +0.494    (n = 87)
```
Cheong & Thomas found consensus error essentially **constant in cents** across price deciles; that invariance is
the whole justification for cents as the primary metric. **On our sample it does not hold.** (Caveats from its
author: they sorted on share price, not EPS level; n=87 in one exceptional quarter; the filter removed the
near-zero-EPS names where their result bites hardest.)

**Operative rule for this module:** keep cents primary and keep APE banned as an aggregate, but treat **any
absolute `median_abs_eps_cents` comparison across two different event subsets — dev vs holdout, regime vs regime,
sector vs sector — as confounded by EPS level unless the subsets are matched on it.** Paired per-event measures
(`PWR`, `RSS`) are immune. This is a cross-subset hazard, not a within-run one — and it is precisely the hazard
the `Q_EPS` test I proposed would have walked into.


### 4.4 The honest rule that follows

**Do not fit the weights in §3.2.** With no point-in-time history, any "tuning" would be fitting to 7 observations
of a signal whose label we cannot observe. Ship the literature-derived priors, cap the total tilt at ±3%, and
state in the demo that the weights are priors. A miscalibrated tilt is worse than no tilt: our scoring is APE, and
a wrong-signed 3% tilt on EPS costs more than it can win.

---

## Implications for our build

**Recommendation: ship Version B (Zacks composite), sized small, gated, unfitted. Fall back to Version C, then to
raw consensus.**

**Primary — Version B.** Two GETs per ticker, browser User-Agent on both:
`zacks.com/stock/quote/{T}/detailed-earning-estimates` (the grid) and
`zacks.com/stock/research/{T}/earnings-calendar` (per-analyst revisions + deep history).

```
S_acc      = ESP / 100                                     # Zacks Most Accurate vs consensus, parsed verbatim
S_rec      = 0.8 × (MRC − C)/C    if MRC else 0            # ONE analyst (§2.10); 0.8 = BCK anti-herding shrink
             → 0 if the newest reviser is "Research Team / Zacks Research"  (not a broker)
             → 0 if a guidance module already owns the target quarter        (orthogonality, §3.2)
r, w       = shortest of (7,30,60,90) days with C ≠ E_w
S_drift    = clamp( (r/w) × d × 0.35 , ±0.02 )             # d = trading days to the Earnings Date
PS_raw     = 0.60·S_acc + 0.20·S_rec + 0.20·S_drift
conf       = 1.15 / 0.70 / 1.00   by agreement of sign(net revisions_60d) with sign(PS_raw), |net| ≥ 0.25
             ×1.15 more if a RevisionCluster (≥50% of N revising in any 5-day window) precedes the newest revision
PS_destale = clamp( PS_raw × conf , ±0.03 );  zero it if |PS_destale| < 0.003

EPS_hat = C_eps × (1 + PS_destale + <other modules>)
REV_hat = C_rev × (1 + 0.27 × PS_destale + <other modules>)
```

**Fallback 1 — Version C.** If the 6-table parser breaks, scrape only the condensed quote page
(`zacks.com/stock/quote/{T}`, anchor on `id="key_earnings_esp_data"`) and use `PS_destale = ESP/100` gated at
±0.5% (**not** LSEG's ±2%, which never fires here — §3.4).

**Fallback 2.** `PS_destale = 0`. Use the consensus unmodified and let the mechanical-beat and guidance modules
carry the forecast. Given the measured effect sizes this is only ~0.2–0.6pp of APE worse than the full version.

**Nine things to carry into the build:**

1. **Two Zacks pages replace Alpha Vantage as the primary consensus source** — `detailed-earning-estimates` has
   quarterly revenue *and* the staleness fields *and* no 25/day cap; `earnings-calendar` adds per-analyst dated
   revisions and ~55 quarters of consensus-vs-actual for EPS and revenue. Amend `data-sources.md` §3.1 and §4.
2. **Parse the `Earnings ESP` field; never recompute it** from the 2dp displayed estimates (§2.3 #5).
3. **Benchmark against zacks.com direct, never Nasdaq** — measured 5.0% apart on NVDA tonight (§2.4).
4. ⚠️ **Correct for Zacks' upward consensus bias.** Zacks runs 1–4% above LSEG/S&P Global on the same event while
   actuals agree to the cent; median gap 1¢ EPS / 0.32% revenue (§2.9). That is the same order of magnitude as the
   entire tilt this module produces. **Cross-check `C` against StockAnalysis (S&P Global) and consider anchoring
   on the mean of the two** — otherwise a correct tilt sits on a biased base and we lose anyway.
5. **Size this module below the mechanical-beat prior.** Published error reductions are 3–15% MSE at N=4→20, and
   we sit at N=4–13. Never quote the "70% hit rate" as if it were an APE claim (§3.5).
6. **Freeze tonight's snapshot to SQLite with a timestamp.** ESP, the estimate trend and reviser provenance are
   all computable forward but not reconstructable historically (§4.1); recording now is the only path to evidence.
7. ⚠️ **Treat `Most Recent Consensus` as one analyst, not a consensus** (§2.10) — shrink it 0.8×, drop it when
   the reviser is Zacks' own in-house team, and never blend it with anything else derived from the same feed.
8. ⚠️ **Gate `S_rec` on the `Q_EPS` regime** (guides *next-quarter* EPS — 20 of the 87 eval events, §3.2), not on
   "guides EPS" generally. There the fresh revisions land *on* the guide, so the tilt re-derives what a guidance
   module already knows; check it against the guidance-midpoint baseline and drop it if it doesn't win.
   `0.60·S_acc + 0.20·S_drift` stands on its own.
9. ⚠️ **Do not reweight on the by-regime surprise table in either unit** (§4.3). Keep cents as the
   pre-registered primary EPS metric (percentage EPS metrics are banned by the evals doc), and treat any
   cross-subset comparison of raw cents error — regime vs regime, dev vs holdout, sector vs sector — as
   confounded by EPS level (ρ ≈ +0.49 on the seed set) unless the subsets are matched on it. Paired
   per-event metrics (PWR, RSS) are immune. *(This paragraph was corrected post-freeze by the orchestrator
   per the module author's own flagged errata; §4.3 is the authoritative treatment.)*

*(Resolved, previously open: the `earnings-calendar` `guidance_table` is **not** company guidance — reconciled
against the ADBE and ORCL 8-Ks, wrong basis and AAPL's newest row is from 2017. `data-sources.md` §5 stands.)*

**And the one honest caveat for the demo:** the highest-value version of this signal — StarMine's revenue
Predicted Surprise at a 78% hit rate — is exactly the one no free data source can compute. We approximate it as a
0.27× echo of the EPS tilt. If a judge asks where our edge is weakest, that is the answer.
