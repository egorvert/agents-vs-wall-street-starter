# Eval Dataset Notes — `data/seed/eval_events.csv`

Built overnight 15→16 Aug 2026 for the "Agents vs Wall Street" backtest.
Companion to [`evals-hillclimbing.md`](./evals-hillclimbing.md) (protocol) and
[`data-sources.md`](./data-sources.md) (endpoints).

**What shipped: 87 US large/mid-cap earnings events, all announced between 2026-06-10 and 2026-08-13**
— i.e. every row is Tier A under the evals doc (§1.4): announcement strictly after 2026-05-31, therefore
post-cutoff for every model we can call, including Opus 5. No canary test required for scoring validity.

| | |
|---|---|
| Rows | **87** (39 `dev` / 48 `holdout`) |
| Date range | 2026-06-10 → 2026-08-13 |
| Sectors | 11 GICS sectors, 2–14 rows each |
| EPS beat rate | **89.7%** (78 beat / 8 miss / 1 in-line) |
| Revenue beat rate | **81.6%** (71 beat / 16 miss) |
| Median revenue surprise | +1.59% (p10 −1.59%, p90 +5.50%) |
| Median EPS surprise | +6.52% (p10 0.00%, p90 +19.35%) |
| Median absolute EPS surprise | **12.0¢** (p90 57¢) |
| Rows carrying a confidence flag | **11** (see §5) |

Every row carries `consensus` and `actual` **on the same vendor basis** (Zacks street/adjusted), which is
the property that makes the surprise meaningful. Revenue is in **USD millions**; EPS in dollars.

---

## 1. Methodology

Five steps, all reproducible from the recipes in §7.

**1. Universe.** `https://stockanalysis.com/stocks/earnings-calendar/__data.json` — one unauthenticated
request, 647 KB decoded, **4,918 symbol-events across 2026-06-15 → 2026-09-25**. Filtered to
`report_date ∈ [2026-06-15, 2026-08-14]` and `market cap ≥ $10bn` → 808 candidate events. Names reporting
1–14 June (ADBE, ORCL) fall outside the calendar window and were added by ticker.

**2. Candidate list.** 249 tickers hand-picked for GICS-sector spread across mega, large and mid cap,
deliberately including both habitual numeric guiders (ADBE, ORCL, MU, JBL, ANET, AMAT, LRCX, META, AMZN,
NFLX, TER, CVS) and non-guiders / qualitative guiders (AAPL, GOOGL, most banks, most staples, the utilities,
the REITs). 243 parsed successfully.

**3. Consensus + actuals.** For each ticker,
`https://www.zacks.com/stock/research/{TICKER}/earnings-calendar` returns ~187 KB of
server-rendered HTML carrying a `document.obj_data` JS object with **two** parallel historical tables:

- `earnings_announcements_earnings_table` → `[report date, fiscal period, EPS estimate, EPS reported, Δ, surprise %, session]`
- `earnings_announcements_sales_table` → same shape, **revenue in USD millions**

This is the single highest-value find of the build: consensus *and* actual, for *both* targets, from one
vendor on one basis, in one request, with no key. It is the primary source for every row.
The row whose report date falls in `[2026-06-01, 2026-08-14]` was selected. → **238 events with complete
consensus + actual on both targets.**

**4. Two-source cross-check** (this is where rows get killed, not where they get built):

| Field | Primary | Independent cross-check | Result |
|---|---|---|---|
| Consensus EPS | Zacks | StockAnalysis calendar `e` (**S&P Global Market Intelligence**) | 83/87 checkable; median gap **1¢**, p90 8¢, max 14¢ |
| Consensus revenue | Zacks | StockAnalysis calendar `r` (S&P Global) | median gap **0.32%**, p90 1.52% |
| Actual revenue | Zacks | `stockanalysis.com/stocks/{t}/financials/__data.json?p=quarterly` | **71/87 match to 0.00%**, 77/87 within 2%; the other 10 differ by revenue *definition* (§5.3) |
| Actual EPS | Zacks | press coverage on a verified subsample (§2) | exact on all 7 checked |

**5. Exclusion filter**, applied before sampling. A row is dropped if **any** of:

- vendor EPS consensus gap > 5¢ *and* > 3% → basis ambiguity
- vendor revenue consensus gap > 2.5%
- `|revenue surprise| > 10%` → almost always a definitional mismatch, not forecastable signal
- `|EPS surprise| > 40%` → GAAP/non-GAAP "actual" failure, unless resolved by hand
- consensus EPS < $0.25 or negative → near-zero denominator plus exclusion ambiguity
- sign flip between consensus and actual EPS
- actual exactly equal to estimate (HCA: Zacks carried `20,230` in both columns — not a reported figure)

238 → **146 clean rows**. The shipped 87 are drawn from that pool.

**6. Sampling — and the bias I had to correct.** My first pass hand-picked the largest clean name in each
sector. That produced a **97.2% EPS beat rate**, versus 90.4% in the clean pool and 89.1% in the full
238-event universe. Hand-picking mega-caps in a blowout quarter systematically selects beats. That dataset
would have made "always predict a beat" look like skill.

The shipped set is instead drawn **without reference to the outcome**: within each sector, candidates are
ordered by `sha256("20260816:" + ticker)` and the first *n* taken. Beat rates now match the pool they came
from (89.7% vs 90.4%), and dev/holdout agree with each other to within 0.1pp. **Never reselect this
dataset by eye.**

**7. Split.** Stratified by sector, `sha256("20260816:split:" + ticker)` ordering, first 42% of each
sector → `dev`. ADBE / ORCL / MU / JBL are force-assigned to `dev` because they are the most recent prints
of names we may be scored on, and we want them visible during iteration. Result: **dev 39, holdout 48**.

This deliberately follows the evals doc (§4.3: `DEV = 40`, everything else held out) rather than a literal
40/20 — a 48-row holdout is worth more than a 58-row dev set. Beat rates by split:

| Split | n | EPS beat | Revenue beat |
|---|---|---|---|
| dev | 39 | 89.7% | 84.6% |
| holdout | 48 | 89.6% | 79.2% |

---

## 2. Rows verified against primary sources by hand

Seven rows were checked against the 8-K / press release **and** an independent wire consensus. All seven
confirmed the Zacks pair. This is the evidence that the machine pipeline is trustworthy.

| Ticker | Zacks cons → actual | Independent confirmation |
|---|---|---|
| ADBE | 5.83 → 5.96 EPS; 6,456.6 → 6,618 rev | AP/Zacks 5.83 & $6.46bn; FactSet 5.82 & $6.45bn; PR: $6.62bn rev, $5.96 non-GAAP |
| ORCL | 1.96 → 2.11; 19,080.5 → 19,184 | investingLive 1.97 & $19.09bn; Reuters/LSEG $19.10bn; PR: $19,184m, non-GAAP $2.111 |
| MU | 21.39 → 25.11; 36,715 → 41,456 | CNBC/LSEG 20.78 & $35.84bn; FactSet 20.86; 8-K ex-99.1: $41,456m, non-GAAP $25.11 |
| JBL | 3.12 → 3.16; 8,631.1 → 8,751 | MarketBeat 3.10 & $8.61bn; Investing.com 3.08 & $8.55bn; 8-K: $8,751m, core $3.16 |
| ANET | 0.89 → 1.02; 2,833 → 3,036 | Reuters/LSEG 0.88 & $2.82bn; PR: $3.036bn, non-GAAP $1.02 |
| UNH | 4.94 → 6.38; 110,121 → 112,032 | CNBC/LSEG 4.90 & $110.85bn; FactSet 4.91 & $111bn; PR: $112.0bn, adj $6.38 |
| CVS | 1.87 → 2.58; 100,178 → 106,096 | CNBC/LSEG 1.85 & $100.11bn; PR: $106,096m, adj $2.58 |

Pattern worth internalising: **actuals agree to the cent across every source; consensus differs by
1–4% between vendors.** The uncertainty in this dataset lives entirely in the consensus column.

---

## 3. Per-source reliability observations

| Source | Verdict | Notes |
|---|---|---|
| **zacks.com `/stock/research/{T}/earnings-calendar`** | **Best free source for this task, by a distance** | Consensus + actual, EPS + revenue, ~10 years of history, no key, no cookie, no JS. Requires a **browser User-Agent** — Node's `fetch` gets a 6 KB bot wall, `curl -H 'User-Agent: Mozilla/…'` gets the full page. 243/249 tickers parsed; the 6 failures (EA, IPG, K, MMC, DFS, BK) return the page without `obj_data`. Zacks street EPS is on the **consensus basis (non-GAAP where the company reports one)**, matching the estimate column. **Use `/earnings-calendar`, not `/earnings-announcements`** — the latter 301s and its `Location` header is **`http://`, not `https://`**, so a redirect-following client silently downgrades to plaintext. Verified 16 Aug: direct path = 200, 0 redirects, byte-identical. |
| **stockanalysis.com `earnings-calendar/__data.json`** | Excellent, one request | 4,918 events / 75 days with EPS **and revenue** consensus. Consensus is S&P Global Market Intelligence — a genuinely different feed from Zacks, which is what makes it a real cross-check. SvelteKit `devalue` encoding; ~20-line decoder in §7. Estimates for past events appear to be retained at their at-announcement vintage. |
| **stockanalysis.com `/stocks/{t}/financials/__data.json?p=quarterly`** | Excellent for actual revenue + fiscal labels | 20 quarters, column-oriented parallel arrays, `datekey`/`fiscalYear`/`fiscalQuarter`/`revenue`/`epsdil`. Its `epsdil` is **GAAP** — do not use it as the actual against a non-GAAP consensus. Used only for revenue and for the fiscal-period label. |
| **api.nasdaq.com `/api/company/{sym}/earnings-surprise`** | Works, but **do not use as the benchmark** | Returns 4 quarters of consensus/actual EPS. Carries a Zacks feed but a **stale vintage** — the `consensus-destaling` agent measured a 5.0% spread on NVDA (2.01 Nasdaq vs 2.09 zacks.com direct, same night), and `asOf` is `null` so staleness is undetectable from the payload. We used zacks.com directly for exactly this reason. Fine for revision counts and session confirmation. |
| **marketbeat.com `/stocks/{EX}/{T}/earnings/`** | Good third opinion, HTML table | Consensus EPS, reported EPS, **GAAP EPS**, revenue estimate, actual revenue, plus the guidance-vs-consensus line. Needs the exchange in the path. Used as a JBL cross-check. |
| **Exa / press coverage** | The tiebreaker | CNBC / Reuters / AP / Investor's Business Daily all state "vs $X expected by LSEG/FactSet". Indispensable for resolving basis disputes — it is how the GOOGL row got fixed. Slow: ~1 search per row, so reserve it for flagged rows. |
| **wsj.com market-data** | Dead | HTTP 401. |

### 3.1 The other five tables in that `obj_data` — what's usable and what isn't

The same page carries seven tables. Beyond `..._earnings_table` and `..._sales_table` (which built this
dataset), two were worth reconciling because `consensus-destaling` is building on them. Checked 16 Aug
against the ADBE and ORCL 8-K guidance I had already verified against the press releases in §2.

**`earnings_announcements_revisions_table` — usable, and on OUR basis.** Shape
`[date, fiscal period, prior, new, analyst, brokerage]`, covering quarterly `(Q)` and annual `(FY)` periods.
The values are **non-GAAP street EPS — the same basis as our `consensus_eps` column**, so it can be joined
to this dataset with no conversion:

| Row | Value | Company's own guidance | |
|---|---|---|---|
| ADBE `8/2026 (Q)` | $6.08 | Q3 FY26 non-GAAP EPS **$6.05–6.10** | ✅ |
| ADBE `11/2026 (FY)` | $24.40 | FY26 non-GAAP EPS **$24.35–24.45** | ✅ |
| ORCL `5/2027 (FY)` | $8.05 | FY27 non-GAAP EPS **$8.05** (raised) | ✅ exact |

⚠️ **But note what that table actually shows.** Those post-print revisions land *on* the guided number, to
the cent. The fresh revisers are substantially **echoing company guidance rather than forecasting
independently**. A de-staling tilt built on them is therefore closer to a guidance-follower than to an
information edge — which is a fine thing to build, but it should be described as such, and it partly
overlaps the evals doc's `B3` (guidance-midpoint) baseline rather than adding to it.

**`earnings_announcements_guidance_table` — do not build on it.** Shape `[date, point, range]`, ~2 rows per
date for multi-period guiders. It is **not** the company's guidance: on 6/11/26 ADBE emits `$4.61
(4.51–4.71)` and `$19.14 (18.84–19.53)`, and Adobe's five guided figures that day were Q3 revenue
$6.67–6.72bn, Q3 non-GAAP EPS $6.05–6.10, FY revenue $26.5–26.6bn, FY non-GAAP EPS $24.35–24.45 and FY GAAP
EPS $17.90–18.00 — **none of them**. ORCL's `$1.32 (1.22–1.42)` likewise is not Oracle's guided Q1 FY27
non-GAAP EPS of $1.72–1.76. The magnitudes are consistent with a forward **GAAP** EPS point + analyst
high/low band, i.e. *the wrong basis for everything else in this file*. Coverage is also unusable:
**AAPL's most recent row is 2 November 2017.**

So `data-sources.md` §5's "no free structured guidance dataset exists" **stands** — this table does not
overturn it. If anyone wants guidance for `B3`, it still has to come from the 8-K / press release text.

---

## 4. Sanity checks run before writing

- ✅ 0 malformed CSV rows; 10 fields on every line; 0 duplicate tickers.
- ✅ Every `report_date` inside `[2026-06-01, 2026-08-14]` — the whole file is Tier A.
- ✅ Revenue surprises: p10 −1.59%, median +1.59%, p90 +5.50%, full range **−6.83% to +12.91%**. Small
  single digits as expected; the one double-digit row is MU and it is real (§5).
- ✅ EPS surprises: median +6.52%, p90 +19.35%, range **−12.96% to +37.97%**. Nothing above 40% survived
  the filter; both rows above 29% (CVS, UNH) were hand-verified against the press release.
- ✅ No sign flips, no zero-crossing EPS, no negative consensus EPS.
- ✅ Actual revenue agrees with an independent source (StockAnalysis quarterly financials) **exactly on
  71/87 rows** and within 2% on 77/87. The 10 exceptions are revenue-definition differences, itemised in
  §5.3 — not data errors, but they are the thing most likely to make a correct forecast score as wrong.
- ✅ Consensus cross-checked against a second vendor feed (S&P Global) on 83/87 rows: median EPS gap **1¢**
  (p90 8¢, max 14¢), median revenue gap **0.32%** (p90 1.52%). The 4 without a cross-check
  (ADBE, ORCL, MU, JBL) were each verified against the 8-K/press release instead — see §2.

**On the 89.7% EPS beat rate.** The brief expected ~70–80%. This dataset is higher, and the reason is not
a data error:

- FactSet Earnings Insight (24 Jul 2026) reports **86% of S&P 500 companies beating EPS in Q2-2026**, versus
  a 5-year average of 78% — with aggregate earnings **+39.3%** above estimates. Q2-CY2026 was an
  exceptional quarter, and it is the *only* quarter that is post-cutoff for our models.
- Our universe is large/mid-cap tilted, and beat rates rise with market cap.
- The unfiltered 238-event universe was **89.1%** and the 146-row clean pool **90.4%**; the shipped 87 sit at
  **89.7%**, i.e. squarely inside the population it was drawn from. There is no selection lift left.

**Consequence for the harness, and it is a big one.** The evals doc's `B1` baseline
(`forecast = consensus × (1 + k)`) is *stronger* on this dataset than the doc's 76–78% base rate implies.
Fit `k` on **pre-2026 data only** (doc §3.2) and treat B1's dev score as an inflated bar, not a target.
And do not use raw directional accuracy as a headline metric: "always predict a beat" scores 89.7% here.
Use paired RSS / PWR, as pre-registered.

---

## 5. Confidence flags — rows to watch

Everything below is *in* the dataset. Flags are recorded here rather than as a CSV column because the
harness's header is fixed; grep this section by ticker.

### 5.1 One row where the vendor "actual" was overridden

**GOOGL — FY2026Q2, 2026-07-22 — HIGHEST-RISK ROW.**
Zacks records actual EPS **9.11** against a 2.88 consensus (+216%). That 9.11 is Alphabet's **GAAP** diluted
EPS, which includes a **net gain of $98.0bn** on equity securities, mostly the SpaceX IPO. Zacks also states
Alphabet revenue **ex-TAC** (101,278 cons / 103,617 act) rather than the $119.8bn total the market quotes.
Both columns were replaced with the self-consistent LSEG pair reported by CNBC:
**consensus 2.89 / 116,930 → actual 2.85 / 119,796** (a small EPS *miss*, a 2.4% revenue beat), confirmed
against the 8-K exhibit for the actuals. AP notes explicitly that Alphabet "did not disclose an adjusted
earnings figure", so the $2.85 actual is a wire-service construct — precisely the Citigroup-Q4-2017
failure mode catalogued in `street-actuals-appendix.md`. **If any single row is poisoning a config's EPS
score, drop this one first.**

### 5.2 Genuine but extreme surprises (verified, keep)

| Ticker | Split | EPS surprise | Rev surprise | Why it's real |
|---|---|---|---|---|
| MU | dev | +17.4% | **+12.9%** | Memory supercycle. 8-K ex-99.1 confirms $41,456m / $25.11 exactly. Consensus varies 20.63–21.39 across vendors (~4%), so the *magnitude* of the surprise is vendor-dependent; the direction is not. Largest revenue surprise in the file. |
| CVS | holdout | +38.0% | +5.9% | Aetna margin recovery. PR + CNBC/LSEG both confirm. |
| SWK | dev | +30.8% | +0.7% | Low EPS base ($1.20); 37¢ absolute. |
| HSY | dev | +31.0% | +5.2% | Cocoa cost relief. |
| UNH | holdout | +29.1% | +1.7% | PR + CNBC/LSEG + FactSet all confirm. |
| F | dev | +27.3% | −1.8% | 9¢ absolute on a 33¢ base — small in cents, large in percent. Score in cents. |
| TER, ELV, MS, FCX, KMI, C, DOW | mixed | +15…+21% | — | All within the filter; vendor consensus gaps ≤ 8¢. |

### 5.3 Rows where the revenue *definition* is not GAAP total revenue

Consensus and actual are internally consistent in every case (that is why they passed the filter), but the
number is **not** the revenue line an agent would compute from the income statement. Divergence vs
StockAnalysis' total revenue:

| Ticker | Zacks basis appears to be | Δ vs total revenue |
|---|---|---|
| **MAR** | fee + reimbursed-cost revenue vs SA's net fee revenue | −71.5% |
| **HLT** | as MAR | −59.3% |
| **PLD** | rental + strategic capital, ex development gains | +18.2% |
| **C** | total revenues net of interest expense | −10.5% |
| **F** | Automotive segment revenue only (excludes Ford Credit) | +7.6% |
| **GE** | GE Aerospace adjusted revenue | +5.7% |
| **GLW** | core sales (non-GAAP, constant-currency) | −4.9% |
| **BAC / WFC / PNC** | revenue net of interest expense | −3.2% to −4.3% |

**Action for the harness:** pass the revenue basis as a per-event hint in the prompt for these 10 tickers,
or exclude them from revenue scoring. An agent that correctly forecasts Marriott's $2.0bn fee revenue
scores as a −72% error against a $7.1bn target. This is the largest single source of avoidable
false-negative error in the file.

### 5.4 Guidance regime — row-level metadata for eval slicing

The brief asked for "some guidance-givers and some non-guiders" and the draw delivered that, but the
property was never recorded per row. It is now. `consensus-destaling` asked for a binary
"guides EPS / doesn't"; **binary is the wrong cut**, for two reasons:

- What determines whether an analyst revision is an *echo of the guide* rather than an independent forecast
  is whether the company guides the **next quarter's** EPS — not whether it guides EPS at all. A company
  guiding only an annual EPS range still leaves the quarterly split to the analyst.
- Six rows are REITs, which guide **FFO per share**, not EPS. They belong in neither bucket.

So: four regimes. Copy-pasteable, exhaustive, mutually exclusive, all 87 rows classified.

```js
const GUIDANCE_REGIME = {
  // guides NEXT-QUARTER EPS explicitly -> revisions to the quarterly line are largely restatements of the guide
  Q_EPS:  ['ADBE','AMAT','APH','GLW','JBL','LRCX','MU','NXPI','ON','ORCL','TER','TXN','WDC',
           'NFLX','IQV','LIN','PPG','HLT','MAR','RCL'],                                        // 20
  // guides ANNUAL EPS only -> the quarterly consensus is analyst-modelled, constrained but not set by the guide
  FY_EPS: ['DIS','VZ','GM','CL','HSY','MDLZ','MO','PEP','PG','STZ','KMI','MCO','V','CI','CVS',
           'ELV','JNJ','PFE','SYK','UNH','GD','GE','ITW','LHX','LMT','ROK','SWK','TDG','ECL',
           'CBRE','DUK','NEE','PPL','SO','SRE'],                                               // 35
  // no EPS guidance at all -> quarterly consensus fully analyst-modelled
  NO_EPS: ['CMCSA','GOOGL','META','OMC','AAPL','ABNB','CMG','DPZ','F','YUM','TSN','EOG','HAL',
           'SLB','BAC','BLK','C','MS','PNC','STT','WFC','DXCM','CSX','NSC','DOW','FCX','NUE'], // 27
  // guides FFO/AFFO per share instead of EPS
  FFO:    ['CCI','EQR','PLD','PSA','WELL'],                                                    //  5
};
```

Observed behaviour by regime, **in both units** — and the reason no causal claim is made from it:

| Regime | n | dev | hold | median consensus EPS | median abs EPS err (¢) | median EPS APE | median rev APE | EPS beat | Rev beat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Q_EPS` | 20 | 9 | 11 | $2.66 | 13.0¢ | **3.90%** | 1.51% | 90% | 85% |
| `FY_EPS` | 35 | 13 | 22 | $1.88 | 14.0¢ | 7.34% | 2.54% | 94% | 74% |
| `NO_EPS` | 27 | 14 | 13 | $1.73 | **9.0¢** | 7.84% | 2.95% | 85% | 89% |
| `FFO` | 5 | 3 | 2 | $1.53 | 8.0¢ | 3.23% | 1.59% | 80% | 80% |

**The ranking inverts between the two units, so there is no finding here.** In cents, `NO_EPS` looks like
the most accurately-forecast regime (9.0¢ vs 13–14¢). In APE it looks like the *least* accurate (7.84% vs
3.90%). An earlier draft of this section read the cents column as "consensus is most accurate where there
is no EPS guidance" — **that claim is withdrawn.** A result that flips under a defensible change of unit is
not a result. Use this table to size cells and to slice runs, not to conclude anything about guidance.

Two things worth knowing about *why* it flips, because the obvious explanation is not the right one:

- It is **not** driven by regimes holding different-sized companies. Median consensus EPS is $1.53–$2.66
  across all four — nearly flat. The **within**-regime spread dwarfs the between-regime spread
  (`Q_EPS` spans $0.72–$21.39; `NO_EPS` spans $0.32–$12.67). APE is being moved by each regime's low-EPS
  tail, not by its centre.
- The deeper cause is that **in this sample, EPS error in cents is *not* scale-free.** See §6.7.

⚠️ **Two honest limits on this classification.**⚠️ **Two honest limits on this classification.**

1. **It is my domain knowledge, not scraped from the filings.** Guidance practice at large caps is stable
   and most of these are unambiguous, but the ones in growth-percentage rather than dollar-range form are
   judgement calls: **DIS, VZ, CL, MDLZ, PEP, PG, V** all guide EPS *growth %* rather than a $ range, and
   **KMI**'s figure is an annual budget set in December rather than a quarterly guide. **NUE** issues a
   directional earnings statement rather than a range. If a decision rests on any of these, read the 8-K.
   **CBRE** sits in the Real Estate sector but is a services company guiding core EPS, not a REIT — it is
   deliberately in `FY_EPS`, not `FFO`.
2. **The dev cells are too small to test within.** `Q_EPS` has 9 dev rows. Per the evals doc §4.1, n=10
   requires 9/10 wins to reject at α=0.05 — so a per-regime comparison on dev alone is noise, not evidence.
   Slice the *pooled* 87, or grow the set first (§7.5 has 64 verified rows ready, which would roughly double
   every cell).

### 5.5 One structural caveat on ORCL

Oracle's FQ4-2026 non-GAAP EPS of **$2.111** includes one-time net investment gains (Ampere sale, Bloom
Energy warrants); the press release states ex-gains EPS would have been **$2.03**. Both Zacks and the wire
consensus scored against 2.11, so the row is consistent — but a model reasoning from operations would
"correctly" land near 2.03 and be marked 8¢ wrong.

---

## 6. Known issues

**6.1 Consensus vintage is not provably point-in-time.** Zacks' historical surprise table is presented as
the estimate carried at announcement, and it agrees with contemporaneous wire reports (§2) on every row we
checked — which is strong evidence it is frozen. But there is no `asOf` field, so we cannot *prove* it.
Per the evals doc §2.2 restatement gotcha: **re-pull `zacks.com/stock/research/{T}/earnings-calendar`
for 3–4 tickers at ~10:00 and diff against `data/seed/`.** If a past-quarter estimate has moved, the field
is not frozen and the writeup must say so. Two minutes of work; do it.

**6.2 Vendor basis disagreement is the dominant residual error, and the bias has a known direction.**
Zacks consensus runs **1–4% above** LSEG on the same event (UNH 4.94 vs 4.90; CVS 1.87 vs 1.85;
ADBE 5.83 vs 5.82; MU 21.39 vs 20.78). It is one-sided, not noise, and `consensus-destaling` and I
converged on the mechanism from opposite ends:

- Zacks **drops pre-guidance estimates that fall outside the company's guided range**, which preferentially
  removes stale low-balls and pulls the mean up;
- the estimates that survive or get filed afterwards are substantially **echoing the guide** — post-print
  revisions in Zacks' own revisions table land *on* the guided number to the cent (ADBE `8/2026 (Q)` = $6.08
  vs guided $6.05–6.10; ORCL `5/2027 (FY)` = $8.05 vs guided $8.05; see §3.1).

Same phenomenon from two ends: **the Zacks consensus is a guidance-anchored number, cleansed of stale
low-balls and repopulated with guidance-followers.** Three consequences:

1. **Our benchmark is slightly harder to beat than the true street mean**, because it already absorbs the
   guide. Errors against it will look worse than against LSEG, by roughly the 1–3% gap.
2. It explains why the beat rate here is so high (§4) without invoking a data problem — a guidance-anchored
   consensus on a quarter where companies sandbagged their guides produces exactly this.
3. A converged panel leaves little dispersion for any recency/de-staling reweighting to exploit — which is
   why that module is being gated rather than trusted, and why §5.4's regime split matters.

The literature in `street-actuals-appendix.md` puts the beat↔miss flip rate at ~8% of firm-quarters
depending on basis. **Whatever the organisers score against, our consensus column will differ from it by
roughly 1–3%, in a known direction.** Get the scoring vendor confirmed at 09:00 and, if it is not Zacks,
re-derive this column — the actuals column will not need to change.

**6.3 There is no dispersion, no analyst count, no revision history.** Zacks' historical table carries only
the mean. Point-in-time revision trends for past quarters are not retrievable free (confirmed independently
by the `consensus-destaling` agent: Zacks serves the current vintage only; the historical detail file is
WRDS/paid). So **SUE-style scaling by `σ(analyst forecasts)` is not available on this dataset** — the evals
doc lists it as a diagnostic only, which is just as well.

**6.4 Excluded on purpose, and why it matters.** The filter removed 92 of 238 events. The exclusions are
*not* random — they concentrate in refiners and integrated energy (MPC +50%, PSX +44%, CVX +22%, XOM +21%
revenue "surprises", all basis artefacts), large banks with total-vs-net revenue mismatches (JPM +17%,
GS +23%), and companies with negative or near-zero consensus EPS (MRK, BA, WBD, GILD, INTC, NKE). Energy is
consequently thin (4 rows) and there is no representation of loss-making or turnaround names. **If the
competition targets a refiner, an airline or a company printing near zero, this dataset has told us nothing
about how we perform there.**

**6.5 Season concentration.** 67 of 87 rows report in July; only 5 in June and 15 in August. All are
June-quarter-end except the off-cycle fiscals (ADBE/ORCL/MU/JBL/FDX May-end, CSCO/AMAT/STX July-end).
Fine for this competition; not a general-purpose panel.

**6.6 The confounder the evals doc already flagged (§1.4).** For a June-quarter-end, April and May 2026
sit *before* Opus 5's stated May-2026 cutoff. The answer was published in July so there is no leakage of the
result, but the model does have genuine parametric knowledge of the quarter's macro context. This makes a
"with vs without retrieval" ablation confounded on this dataset. Say so; don't hide it.

**6.7 EPS error in cents is not scale-free in this sample — which touches the primary metric.**
The evals doc §3.4 makes **median absolute EPS error in cents** the primary EPS metric, on the strength of
Cheong & Thomas (2010): absolute consensus forecast error is essentially constant in cents (median 2–3¢)
across every share-price decile, so cents is the natural scale-free unit and percentage metrics are banned.

Measured on these 87 rows, that invariance does not hold:

```
Spearman rho( |consensus EPS| , |EPS error in cents| ) = +0.494   (n = 87)
```

A +0.49 rank correlation is substantial. Higher-EPS names carry materially larger cent errors here, so a
config that happens to do well on low-EPS names will score better on the primary metric than its true skill
warrants — and `PWR`/`RSS`, being **paired per event**, are immune to this, while a raw
`median_abs_eps_cents` leaderboard is not.

Three caveats before anyone over-reads it: Cheong & Thomas sorted on **share price**, not EPS level, so this
is a related but not identical test; n=87 in a single exceptional quarter; and our universe is large-cap
tilted with no near-zero-EPS names (the filter removed them), which truncates exactly the range where their
result is most load-bearing.

**Recommendation — no change to the pre-registered metric.** Keep cents primary and keep MAPE/sMAPE banned
on EPS; the near-zero-denominator pathology the doc describes is real and this dataset simply doesn't
contain the cases that would demonstrate it. But **rank configs on `mean RSS`, which is paired and
scale-immune, exactly as §4.3 already says** — and treat any absolute `median_abs_eps_cents` comparison
between two *different* event subsets (dev vs holdout, regime vs regime, sector vs sector) as confounded by
EPS level unless the subsets are matched on it. That is the practical bite: it is a cross-subset comparison
hazard, not a within-run one.

---

## 7. How to extend the dataset on the day

**146 filter-passing rows exist; 82 of them were drawn into the shipped file (plus 5 force-added), so
64 verified rows are sitting unused.** Adding them is ~10 minutes of work and is the single
highest-leverage thing to do at 10:00 — the evals doc §4.3 is explicit that more events beats more prompt
variants (60→100 events cuts the CI half-width from ±0.12 to ±0.10; 20→60 cuts it from ±0.20 to ±0.12).

### 7.1 Fetch one ticker (the whole pipeline in three requests)

```bash
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
# 1. consensus + actual, EPS + revenue  (browser UA mandatory; Node fetch gets a bot wall)
#    NOTE: /earnings-calendar, NOT /earnings-announcements -- the old path 301s to an http:// Location.
curl -s  -H "User-Agent: $UA" "https://www.zacks.com/stock/research/AAPL/earnings-calendar" > aapl.html
# 2. independent consensus cross-check (one call covers every ticker, 2026-06-15 → 2026-09-25)
curl -s  -H "User-Agent: $UA" "https://stockanalysis.com/stocks/earnings-calendar/__data.json" > cal.json
# 3. independent actual-revenue + fiscal period label
curl -s  -H "User-Agent: $UA" "https://stockanalysis.com/stocks/aapl/financials/__data.json?p=quarterly" > aapl_fin.json
```

Pace Zacks at ~3 req/s. 249 tickers took ~5 minutes with a 350 ms delay and zero blocks.

### 7.2 Extract the Zacks tables

`document.obj_data` is JS, not JSON — scan for the key, then balance brackets while respecting strings:

```js
function extractTable(html, name) {                    // name: 'earnings_announcements_earnings_table'
  let i = html.indexOf(`"${name}"`); if (i < 0) return null;
  i = html.indexOf('[', i);
  let depth = 0, inStr = false, esc = false, j = i;
  for (; j < html.length; j++) {
    const c = html[j];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') { inStr = true; continue; }
    if (c === '[') depth++; else if (c === ']' && --depth === 0) { j++; break; }
  }
  return JSON.parse(html.slice(i, j));                 // rows still contain <div> wrappers -> strip tags
}
// row shape: [ "7/30/26", "6/2026", "$1.88", "$1.91", "<div…>+0.03</div>", "<div…>+1.60%</div>", "After Close" ]
```
The sibling table is `earnings_announcements_sales_table`, **already in USD millions**.

### 7.3 Decode the StockAnalysis SvelteKit payload

```js
function hydrate(nodes, idx, seen = new Map()) {
  if (idx === -1) return undefined;
  if (seen.has(idx)) return seen.get(idx);
  const v = nodes[idx];
  if (v === null || typeof v !== 'object') return v;
  if (Array.isArray(v)) {
    if (typeof v[0] === 'string' && ['Date','Set','Map','BigInt','RegExp'].includes(v[0]) && v.length === 2) return v[1];
    const out = []; seen.set(idx, out); for (const i of v) out.push(hydrate(nodes, i, seen)); return out;
  }
  const out = {}; seen.set(idx, out);
  for (const k of Object.keys(v)) out[k] = hydrate(nodes, v[k], seen);
  return out;
}
const decode = raw => JSON.parse(raw).nodes.filter(n => n && n.type === 'data' && n.data)
                                          .map(n => hydrate(n.data, 0));
```
Calendar: weeks live under `root.earnings` (15 weeks × ~5 days × `symbols[]`), **not** under `root.days`
(which is only per-day counts — an easy hour to lose). Symbol fields: `s` ticker, `n` name, `t` bmo/amc,
`e` EPS consensus, `r` revenue consensus (units, not millions), `m` market cap.
Financials: find the node with `.sections`, then the section with `.data.datekey`; parallel arrays
`datekey / fiscalYear / fiscalQuarter / revenue / epsdil`. Type as `(number | "[PRO]" | null)[]`.

### 7.4 Re-apply the guardrails — do not skip these

1. Run the **exclusion filter** from §1 step 5 verbatim. It is what keeps refiners and GAAP/non-GAAP
   failures out.
2. Draw new rows by **hash order, never by eye** (§1 step 6). Hand-picking cost me 7pp of fake beat rate.
3. Assign split by `sha256("20260816:split:" + ticker)`, first 42% of each sector → dev. Deterministic, so
   re-running on a larger pool keeps existing assignments stable within a sector only if the sector size is
   unchanged — **if you grow a sector, re-derive the whole split and record the new `dataset_hash`**, or
   append new rows to `holdout` only. Appending to holdout is safer mid-day and is the recommended move
   after 14:00.
4. Any row with `|EPS surprise| > 25%` or `|revenue surprise| > 8%` gets one Exa search
   (`"{company} {quarter} results analysts expected"`) before it enters the file. Every such check tonight
   either confirmed the row or exposed a basis error — the hit rate justifies the minute it costs.

### 7.5 The 64 verified rows that are ready to add right now

Already fetched, already cross-checked, already through the exclusion filter — they simply were not drawn.
Add them by re-running the sector draw with a larger `n`, or append the whole list to `holdout`.

| Sector | clean | drawn | ready to add |
|---|---:|---:|---|
| Industrials | 32 | 10 | CAT, RTX, ETN, UNP, PH, HWM, MMM, JCI, EMR, WM, UPS, CMI, NOC, URI, PCAR, RSG, GWW, FAST, CARR, ODFL, IR, DOV **(22)** |
| Financials | 18 | 9 | MA, AXP, SCHW, COF, USB, AON, TFC, PYPL, AIG **(9)** |
| Health Care | 17 | 9 | AMGN, TMO, ABT, BSX, EW, BDX, IDXX, ZTS **(8)** |
| Information Technology | 17 | 10 | **MSFT**, CSCO, KLAC, ANET, STX, FTNT, MCHP **(7)** |
| Consumer Discretionary | 15 | 9 | **AMZN**, MCD, BKNG, ORLY, DHI, LVS **(6)** |
| Consumer Staples | 14 | 8 | KO, PM, KDP, SYY, KMB, CHD **(6)** |
| Materials | 9 | 6 | SHW, APD, DD **(3)** |
| Real Estate | 8 | 6 | VICI, AVB **(2)** |
| Communication Services | 7 | 6 | T **(1)** |
| Energy | 4 | 4 | — |
| Utilities | 5 | 5 | — |

Note that **MSFT and AMZN are in the ready-to-add list, not in the shipped file** — the hash draw did not
select them. That is the price of not hand-picking, and it is the right trade: adding them back by name is
exactly the move that produced the 97.2% fake beat rate. If you want them, add the *whole* sector remainder,
not the two names you recognise.

Energy is the binding constraint at **4 clean rows total** — SLB, EOG, KMI, HAL are all already in. To add
energy you must relax the revenue-surprise rule and accept the refiner basis problem (XOM, CVX, MPC, PSX,
VLO all failed on revenue definition, not on data quality); do it only with an explicit per-event basis hint.

---

## 8. File format

`data/seed/eval_events.csv`, 87 rows + header, UTF-8, no quoting needed except names containing commas.

```
ticker,name,fiscal_period,report_date,consensus_revenue_usd_m,consensus_eps,actual_revenue_usd_m,actual_eps,split,source_urls
```

- `fiscal_period` — the **company's own** fiscal label from StockAnalysis, e.g. `FY2026Q3` for Apple's
  June quarter, `FY2026Q4` for Microsoft's and Oracle's, `FY2026Q2` for Adobe's May quarter. Not a
  calendar quarter.
- `report_date` — announcement date (ISO). **Not** the as-of timestamp: the evals doc requires
  `as_of = 8-K acceptanceDateTime − 1s`, which must be pulled from
  `https://data.sec.gov/submissions/CIK##########.json` at build time. Session (bmo/amc) is available in
  the StockAnalysis calendar `t` field and in the Zacks table's last column if you need to disambiguate a
  same-day filter.
- `consensus_*` / `actual_*` — Zacks street basis (non-GAAP where the company reports one), except GOOGL
  (§5.1). Revenue USD millions, EPS USD.
- `split` — `dev` (39) or `holdout` (48). **Touch holdout exactly twice: ~14:00 and ~18:00.**
- `source_urls` — semicolon-separated. Always the Zacks page, the per-ticker StockAnalysis financials
  endpoint and the calendar endpoint; plus press/8-K URLs for the hand-verified rows in §2.
