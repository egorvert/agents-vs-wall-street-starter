# How Wall Street Actually Produces Earnings Estimates — and Where It Is Exploitable

Research note for **"Agents vs Wall Street"** (AI Tinkerers / OpenStocks / OpenAI / Primer), London, 16 Aug 2026.
Compiled 15 Aug 2026. Every claim sourced inline. Where sources conflict, both numbers are given and the conflict is
labelled.

**The thesis in one paragraph.** Sell-side quarterly estimates are not primarily forecasts — they are a negotiated
equilibrium between management guidance and analyst career incentives, and the *aggregator itself* participates. Firms
guide down, analysts anchor on guidance, the aggregator quietly truncates the optimistic tail, and ~78% of the index
beats. The consensus you can freely download is a **stale, equal-weighted mean over a non-comparable set of "adjusted
EPS" definitions, selectively filtered, snapshotted at an unstated time**. There are four exploitable seams: (1) the
beat is partly mechanical and its size is predictable per company and per sector; (2) the consensus is stale — recency
+ analyst-quality reweighting of the *same public estimates* predicts the surprise direction ~70% of the time on EPS
and ~78% on revenue, per LSEG's own published product data; (3) management guidance ranges are pessimistically skewed
and actuals land near the **upper bound** while analysts anchor near the **midpoint**; (4) revenue is far more
forecastable than EPS — consensus revenue error is ~1.9% vs ~7% for EPS.

**Two things that will kill us if we ignore them**, both flagged in bold below: the walk-down is currently **inverted**
(analysts raised estimates in 4 of the last 5 quarters), and any LLM backtest on pre-training-cutoff quarters is
contaminated by **memorisation**, not skill.

---

## 1. The sell-side analyst workflow

### 1.1 What the model actually is

A sell-side quarterly model is a **driver-based, segment-level revenue build stitched to a margin walk**, maintained in
one Excel workbook per covered name and rolled forward every quarter.

| Segment type | Driver identity | Example |
|---|---|---|
| Hardware/product | Units × ASP | iPhone units × ASP |
| Subscription | (Beginning subs + net adds) × ARPU | Netflix, Spotify |
| Marketplace | GMV × take rate | App Store, Uber |
| Advertising | Impressions × CPM, or DAU × ad load × CPM | Meta, Google Search |
| Usage/cloud | Consumption units × price, or RPO burn-down | AWS, Azure |
| Lending | Average earning assets × NIM + fees − provisions | Banks |
| Same-store retail | Store count × sales/store, decomposed into comps (traffic × ticket) | Costco, Home Depot |

Below revenue it is a **margin walk**: prior-year gross margin, then a bridge of named deltas — mix, price/cost, FX,
input costs, freight, tariffs, utilisation, one-offs — landing on this quarter's GM. Opex is usually % of revenue with a
headcount/SBC overlay. Then D&A, net interest, tax rate, minorities, and **diluted share count** — the last is a
genuine and frequently mismodelled EPS driver: heavy repurchasers move diluted shares 0.5–2% a quarter, worth several
cents.

Mechanics references: Wall Street Prep (https://www.wallstreetprep.com/knowledge/sample-equity-research-report/),
CFI (https://corporatefinanceinstitute.com/resources/valuation/equity-research-report/),
Peak Frameworks on the day-to-day (https://www.peakframeworks.com/post/what-do-you-actually-do-in-equity-research).
Anthropic's published `earnings-reviewer` agent spec is a compact and accurate description of the post-print loop —
pull the print, load the **full** transcript (explicitly *not* summaries), update the model, run model QC, draft the
note, output a variance table of actual vs consensus vs prior estimate:
https://github.com/anthropics/financial-services/blob/main/plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md

### 1.2 Which inputs get the most weight, in practice

1. **Management guidance — dominant.** Where a company guides a quarter, consensus converges on the guide within days.
   Zacks makes this mechanical: it **drops any pre-guidance estimate falling outside the guidance range** (see §2.1).
   Analysts anchor on the **midpoint** while actuals land near the **upper bound** (§3.4) — a directly exploitable
   asymmetry.
2. **The prior quarter's print + call.** Guidance *bundled with* the earnings announcement draws faster and larger
   revisions than standalone guidance (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3840039).
3. **Company-disclosed KPIs** — comps, net adds, RPO/backlog, book-to-bill, load factors, ARPU, DAU. These are the
   actual model inputs; revenue is derived from them.
4. **Channel checks and expert networks** — supplier/distributor/customer calls via the analyst's rolodex or a paid
   network (GLG, Third Bridge, AlphaSights, Guidepoint). This is the class of information we cannot replicate (§6.1).
   Background: https://www.integrity-research.com/are-channel-checks-legit/
5. **Macro/sector series** — oil strip, FX, rates, freight, housing starts. FactSet's Q2 2026 Energy note is the clean
   example: sector revenue +42.5% y/y driven by average oil of $92.55 in Q2 2026 vs $63.68 in Q2 2025 (+45%). The
   analyst is plugging a strip price.

### 1.3 The revision calendar — when estimates actually move

- **Revisions cluster immediately after the print.** ~26–53% of analysts revise within two trading days of the earnings
  announcement (year-dependent); 58–76% of firms have at least one "responsive" analyst
  (https://www.sciencedirect.com/science/article/abs/pii/S0165410108000220). About a quarter of *recommendation*
  revisions also fall in the 3 days after the print (Yezegel, JAE 2015,
  https://www.sciencedirect.com/science/article/abs/pii/S0165410115000026).
- **Then near-silence.** Revisions are *least* informative in the week after the announcement and grow more informative
  as the next print approaches (Ivkovic & Jegadeesh, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=359320).
- **Better analysts revise later.** Analysts with more firm-specific experience, better prior accuracy, and larger
  brokers revise *later in the quarter*, and their late revisions remain more accurate even after controlling for the
  timing advantage (Kim, Lobo & Song 2011, JBF 35(8):2158-2168,
  https://ideas.repec.org/a/eee/jbfina/v35y2011i8p2158-2168.html). **The last estimates before a print carry
  disproportionate signal.**
- **Company quiet periods** run roughly from quarter-end to the release; IR stops talking to preserve Reg FD compliance
  (https://westwicke.com/2022/02/6-commonly-asked-questions-about-quiet-periods/). FINRA Rule 2241 research blackouts
  are a separate, offering-linked concept — not earnings-linked.
- **Pre-announcement season** is the last ~3 weeks of the quarter. LSEG counted 80 S&P 500 pre-announcements for
  Q3 2026 as of 14 Aug 2026: **48 positive / 6 in-line / 26 negative, N/P ratio 0.5** — versus 96 with N/P **1.4** for
  Q3 2025 (LSEG S&P 500 Earnings Scorecard 14 Aug 2026, Exhibit 9,
  https://lipperalpha.refinitiv.com/wp-content/uploads/2026/08/TRPR_82201_20260814.pdf).

### 1.4 The walk-down, quantified

FactSet tracks the change in the S&P 500 bottom-up EPS estimate through a quarter. Current (mid-2026) rolling averages:

| Window | 5-yr avg | 10-yr avg | 15-yr avg | 20-yr avg |
|---|---|---|---|---|
| First month of a quarter | −1.0% | −1.3% | −1.7% | −1.9% |
| First two months | −1.6% | −2.2% | −2.6% | −3.2% |
| **Full quarter** | **−2.0%** | **−2.7%** | **−3.3%** | **−4.2%** |

Sources: full-quarter — FactSet Earnings Insight 2 Jul 2026,
https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_070226.pdf ;
two-month — https://insight.factset.com/analysts-making-largest-increases-in-quarterly-eps-estimates-for-sp-500-companies-since-2021 ;
first-month — https://insight.factset.com/analysts-increasing-in-quarterly-eps-estimates-for-sp-500-for-2nd-straight-quarter

**Per-month decomposition (20-yr): month 1 −1.9pp, month 2 −1.3pp, month 3 −1.0pp. The walk-down is front-loaded** —
which is exactly why the *last* estimates before a print carry the information (§3.6).

*Conflict noted*: 2025-vintage FactSet articles show a different first-month profile (5-yr −1.8%, 10-yr −1.6%,
15-yr −1.6%: https://insight.factset.com/analysts-making-larger-cuts-than-average-to-eps-estimates-for-sp-500-companies-for-q2)
and a full-quarter 5-yr average of −3.0%. These are rolling windows at different as-of dates; 2020–21 quarters rolling
out of the 5-year window moves the numbers materially. Treat the index walk-down as **−2% to −4% per quarter, trending
smaller**.

DWS, using FactSet data 2011–2025, puts the two halves of the trade side by side — the cleanest single picture:
**average EPS cut during the calendar quarter = −3.3%; average EPS beat during reporting = +3.5%** (excluding 2020–21).
The walk-down and the beat almost exactly cancel. DWS "S&P 500 EPS Tracker", Americas CIO View, p.8,
https://download.dws.com/download/asset/inline/49221af1-0106-4b46-a4cd-2bcae5fec944?tenant=Dwscom

### 1.5 ⚠️ THE WALK-DOWN IS CURRENTLY INVERTED — read before hard-coding anything

**Analysts have RAISED the quarterly S&P 500 bottom-up EPS estimate in 4 of the last 5 quarters, including the last 2
consecutively.**

- Q2 2026 estimates rose **+3.4%** (to $81.54 from $78.84) from 31 Mar to 30 Jun, against a −2.0% 5-yr average.
  https://insight.factset.com/sp-500-earnings-season-preview-q2-2026
- July 2026 saw **+0.3%** for Q3 2026.
- Only **33% of Q3 2026 guiders issued negative EPS guidance (25 of 75)** vs a 5-yr average of **58%** and 10-yr
  average of **60%** (FactSet Earnings Insight 7 Aug 2026, p.15).

This is not a one-cycle anomaly. Hovakimian & Saenyasiri show the walk-down in median forecast errors was already
"practically nonexistent" for FY2004–2006 after the 2003 Global Settlement (§3.8). **The classic 1983–2006 walk-down
effect sizes are historical upper bounds, not current expectations. A model that hard-codes a downward-drift prior will
be miscalibrated right now.**

---

## 2. Consensus mechanics

### 2.1 The six aggregators, and what each actually does

| Vendor | Contributors | Universe | Headline stat | Published staleness rule | Basis rule |
|---|---|---|---|---|---|
| **LSEG / Refinitiv I/B/E/S** | **900+ brokers** | 22,000+ cos | **Mean** (median/hi/lo/SD/count also published) | "recent estimates" only — undefined. StarMine SmartEstimate uses **4 months** | Same-accounting-basis. **In practice ~half of stale estimates are retained** (see §2.2) |
| **FactSet Estimates** | **800+** | 19,000 active | Mean | **trailing 100 days**, variable window extendable to **150 days** since Dec 2014 | "Consensus class 0" excludes brokers on a different methodology; **90% of estimates collected directly from research reports** |
| **Zacks** | 185+ brokers / 2,600 analysts | ~5,000 (US/CA only) | Simple average | Proprietary "**refreshment window**" — length unpublished, empirically aggressive (§2.5) | **Two consensuses**: *BNRI* (before non-recurring items; adjusts non-conforming estimates) and *Street* (majority-rules; **excludes** minority-definition analysts). Public zacks.com shows **Street** |
| **S&P Global MI (Capital IQ)** | not published | global | Mean | not published | not published |
| **Bloomberg (BEst)** | not published | global | Mean | 1 month, for *recommendations* only | proprietary "comparable fields" restated to align with BEst and guidance |
| **Visible Alpha** (S&P Global since May 2024) | 200–260 (conflicting) | 7,000–7,300 in consensus; **min 3 analysts** to publish | Mean | not published | **Bottom-up from full broker Excel models, every line item normalised** |

Sources: LSEG I/B/E/S factsheet https://thesource.lseg.com/TheSource/getfile/download/8948effd-9a99-400f-adfd-2554fbff4d7c
and https://www.lseg.com/en/data-analytics/financial-data/company-data/ibes-estimates ;
FactSet https://developer.factset.com/api-catalog/factset-estimates-api and
https://insight.factset.com/resources/factset-consensus-estimates-datafeed ;
Zacks https://zacksdata.com/consensus/faq/ and https://findynamics.com/manuals/zacks_consensus_faq.pdf ;
S&P https://www.spglobal.com/market-intelligence/en/solutions/products/estimates ;
Visible Alpha https://press.spglobal.com/2025-03-25-S-P-Global-Market-Intelligence-Launches-Visible-Alpha-on-S-P-Capital-IQ-Pro-Platform

**Zacks' guidance rule is uniquely material to us**: when a company issues guidance, Zacks **drops any pre-guidance
estimate falling outside the guidance range** and keeps only estimates made or affirmed after. This *mechanically*
shrinks the Zacks consensus toward the guide — so a Zacks-scored beat is closer to "beat the guidance" than "beat the
Street". Zacks also reports that **Street and BNRI differ by ≥2 cents in 5–10% of companies**, concentrated in
high-tech where analysts disagree about stock comp.

**FactSet has a second actuals trap.** FactSet carries both a **Company Actual** (from the press release) and a
**Broker Actual** (the *median of post-event consensus*, updatable for up to **100 days after** the report date), with
`FE_ACTUAL_FLAG` = 1/2/3. **The Broker Actual is the default in the European zone even where a company actual exists.**
So "the actual" from FactSet can be a moving, median-of-analysts number rather than a reported figure.
https://insight.factset.com/resources/at-a-glance-factset-estimates-point-in-time-consensus

### 2.2 ⚠️ The consensus is selectively truncated — and the truncation helps companies beat

**Kaplan, Martin & Xie, "Truncating Optimism", Journal of Accounting Research 59(5):1827–1884 (2021).**
https://doi.org/10.1111/1475-679X.12397 | https://ideas.repec.org/a/bla/joares/v59y2021i5p1827-1884.html |
plain-English: https://clsbluesky.law.columbia.edu/2021/12/21/how-optimistic-earnings-forecasts-are-kept-in-check/

- I/B/E/S **removes 6% of one-quarter-ahead forecasts** before computing consensus. Among the **23% of firm-quarters
  with at least one removal, the removal rate is 16%**.
- I/B/E/S's published methodology is described by the authors as **"materially misleading"**: it claims to remove stale
  estimates but **retains roughly half of them**, and enforces majority-basis selectively.
- Removals are **subjective and company-influenced**: optimistic forecasts are dropped more often than pessimistic ones,
  and **the odds of removing an optimistic estimate rise roughly 10× when the removal would let the firm
  meet-or-beat**. The effect strengthens with insider-sale and compensation-delta incentives.

**Consequence for us: the benchmark is endogenous to the company's desire to beat it.** A model that forecasts true EPS
well can still lose on surprise-sign because the bar was shaved. Modelling the truncation is itself a potential edge —
and I/B/E/S ships an **Excluded file** containing the dropped estimates, which is the raw material for auditing it (if
we get WRDS access; we probably won't in 24h).

### 2.3 Vendors disagree about the *actual*, not just the estimate

**Larocque, Watkins & Weisbrod, "Consensus? An Examination of Differences in Earnings Information Across Forecast Data
Providers", Journal of Accounting Research.** https://doi.org/10.1111/1475-679x.70072 |
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4640370 | **open replication code:
https://github.com/eweisbrod/consensus**

- Compares **all five** providers (Bloomberg, Capital IQ, FactSet, I/B/E/S, Zacks) across **94,030 firm-quarters,
  2002–2020**.
- Finds "substantial differences across FDPs in **both forecasted and actual street earnings values**, and thus the
  earnings surprise, for the same firm-quarter."
- Provider differences have **economically meaningful effects on price responsiveness and liquidity** around earnings.
- When providers **disagree about whether a firm beat or missed**, investors side with higher-quality providers but do
  not fully impound the quality difference during the announcement window.
- **I/B/E/S ranks highest on average** in their provider-quality measure.

Supporting literature: Bradshaw & Sloan (2002, JAR 40(1):41–66) "GAAP versus The Street" — the origin;
Abarbanell & Lehavy https://papers.ssrn.com/sol3/papers.cfm?abstract_id=228918 — I/B/E/S vs Zacks vs First Call vs
Compustat, showing published street-vs-GAAP inferences are driven by a handful of extreme negative-tail observations
and a 1990 regime shift; Brown & Larocque (TAR 2013, 88(3):853–880) — I/B/E/S's reported actual ≠ what analysts were
actually forecasting.

**And the same vendor disagrees with itself over time.** Call, Hewitt, Watkins & Yohn (RAST 2021, 26(1):1–36,
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2788140): the same I/B/E/S detail file pulled in 2009 vs 2015
differs substantially — the newer vintage is more accurate and less biased, **identifies substantially different firms
as meeting-or-just-beating**, and changes measured effects of analyst experience and brokerage size by **>30%**. The
differences are ongoing. **Snapshot and version every consensus number we pull; date-stamp it in SQLite.**

**The I/B/E/S adjusted-data rounding trap** (WRDS,
https://wrds-www.wharton.upenn.edu/documents/5/A_Note_on_IBES_Unadjusted_Data_pdf.pdf): split-adjusted values are
rounded to **2 decimals in Summary, 4 in Detail**, and Summary cannot be un-adjusted — so rounding **manufactures
spurious zero forecast errors**, i.e. the exact "just met consensus" bin everyone studies. 1975–2009 saw 528 stocks
with >16:1 cumulative splits, 215 with >32:1, 66 with >64:1. I/B/E/S's effective split date also differs from the true
split date, so estimates and actuals can land on different share bases (canonical case: Microsoft's April 1990 split).

### 2.4 A live, verified example of how big the vendor gap gets

**Same 500 companies, same quarter (Q2 2026), same week:**

| Metric | FactSet (7 Aug 2026) | LSEG I/B/E/S (14 Aug 2026) |
|---|---|---|
| % beating EPS | 86% | 84.8% |
| **Aggregate EPS surprise** | **+29.2%** | **+8.4%** |
| **Comm. Services EPS surprise** | **+102.3%** | **−1.9%** |
| % beating revenue | 76% | 76.0% |
| Aggregate revenue surprise | +3.2% | +3.7% |

Entirely Alphabet and Amazon. FactSet used **GAAP** actuals — Alphabet $9.11 vs $2.88 est (including a **$98bn**
other-income gain from unrealised gains on equity securities) and Amazon $5.75 vs $1.82 (including a **$53.4bn** gain
primarily from its Anthropic investment). Ex those two names FactSet's aggregate surprise falls from 29.2% to **10.9%**.
LSEG stripped the gains and shows Communication Services at −1.9%.
Sources: FactSet Earnings Insight 7 Aug 2026 pp.6–8
https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_080726.pdf ;
LSEG Exhibits 2 & 6 https://lipperalpha.refinitiv.com/wp-content/uploads/2026/08/TRPR_82201_20260814.pdf

**And at single-stock level.** NVDA fiscal Q1-FY2027, reported 20 May 2026. **Every source agrees actual EPS = $1.87.**

| Source | Consensus | Reported surprise |
|---|---|---|
| Nasdaq (**Zacks**) | **$1.70** | **+10.0%** |
| MarketBeat | **$1.76** | **+$0.11 (+6.25%)** |

Same company, same quarter, same actual — **6 cents and 3.75 percentage points apart.** MarketBeat's *forward* numbers
match Zacks exactly, so its historical consensus came from a different snapshot than its forward consensus.

**The five mechanisms, ranked by noise injected:**
1. **Basis/definition (largest).** Majority-rules (LSEG/FactSet/S&P/Bloomberg/Zacks-Street) *excludes* minority
   definitions; Zacks-BNRI *adjusts and keeps* them. ≥2¢ divergence in 5–10% of companies, concentrated in tech, driven
   by stock-comp treatment.
2. **Which estimates are live.** 100 days (FactSet) vs ~4 months (SmartEstimate) vs Zacks' tighter window vs I/B/E/S's
   de facto retention of half its stale estimates. This alone explains 48-vs-17 estimates on NVDA (§2.5).
3. **Snapshot timing.** Consensus moves until the print. FactSet PIT freezes at local midnight; free sources rarely say.
4. **The actual itself.** FactSet may serve a mutable Broker Actual; Bloomberg maintains proprietary comparable fields.
5. **Selective removal** (§2.2).

**"Did the agent beat the Street?" is undefined until you name the vendor, the EPS definition, and the snapshot
timestamp. Vendor choice alone is worth 3–4 percentage points of surprise.**

### 2.5 How many estimates are actually in a consensus — measured, not quoted

Pulled on 15 Aug 2026, FY1, S&P Global MI (via StockAnalysis) vs Zacks (via Nasdaq):

| Ticker | S&P: EPS *N* | S&P: Rev *N* | S&P: analysts w/ rating | **Zacks: EPS *N*** | S&P EPS | Zacks EPS |
|---|---|---|---|---|---|---|
| NVDA | 48 | 53 | 61 | **17** | 8.963 | 8.79 |
| AAPL | 38 | 33 | 46 | **6** | 8.800 | 8.76 |
| MSFT | 35 | 48 | 56 | **21** | 19.704 | 19.58 |
| JPM | 10 | 11 | 24 | **7** | 24.212 | 24.28 |
| CROX | 15 | 13 | 15 | **5** | 13.950 | 13.95 |
| HURN | 5 | 5 | 5 | **3** | 9.198 | 9.18 |
| UFPT | 4 | 3 | 4 | **2** | 10.570 | 10.54 |
| PLAB | 3 | 3 | 3 | — | 1.86 | no data |

- **"Number of estimates" ≠ analyst coverage.** NVDA: 61 analysts publish ratings, 48 have a live FY1 EPS number at
  S&P, only **17** survive Zacks' refreshment window. AAPL is extreme: **46 rating analysts → 6 fresh Zacks estimates**.
- **Zacks' N runs ~35–60% of S&P's** at every cap size — its window is materially tighter than FactSet's 100/150 days.
- **Revenue N is not systematically below EPS N** — for MSFT (48 vs 35) and NVDA (53 vs 48) it is *higher*. The common
  assumption that revenue coverage is thinner is wrong at S&P.
- **The <5-estimate cliff arrives fast.** By small/mid-cap you are at 2–5 estimates. Visible Alpha's own floor for
  publishing a consensus at all is **≥3 analysts**.
- **Dispersion is driven by vendor exclusion policy at least as much as by genuine disagreement.** NVDA's Zacks range
  (7.90–11.99, ~47% of mean) is far wider than S&P's (8.20–9.58, ~15%) on one-third the estimates.

### 2.6 Free, machine-readable consensus — tested live, 15 Aug 2026

| Source | URL pattern | Licensed from | Machine-readable? | EPS | Rev | Verdict |
|---|---|---|---|---|---|---|
| **Nasdaq (undocumented API)** | `api.nasdaq.com/api/analyst/{TICKER}/earnings-forecast`<br>`api.nasdaq.com/api/company/{TICKER}/earnings-surprise` | **Zacks** | **Pure JSON, no key, no auth** | ✅ | ❌ | **Best free source** |
| **StockAnalysis.com** | `stockanalysis.com/stocks/{ticker}/forecast/` | **S&P Global MI** (TipRanks for individual analysts) | **Yes — full JSON embedded in server-rendered HTML** | ✅ | ✅ | **Best for revenue + counts** |
| **Alpha Vantage** | `alphavantage.co/query?function=EARNINGS_ESTIMATES&symbol=X` | undisclosed | JSON API (free key) | ✅ | ✅ | **Richest schema** |
| Finviz | `finviz.com/quote.ashx?t=NVDA` | undisclosed | server-rendered | partial | ❌ | thin |
| MarketBeat | `marketbeat.com/stocks/NASDAQ/{T}/earnings/` | own blend | server-rendered | ✅ | ✅ | scrapable |
| **Yahoo Finance** | `finance.yahoo.com/quote/{T}/analysis/` | **S&P Global MI** (no longer Refinitiv) | **404/503 to bots; API 429** | — | — | blocked |
| TipRanks | `tipranks.com/stocks/{t}/forecast` | own | **403** | — | — | blocked |
| WSJ | `wsj.com/market-data/quotes/{T}/research-ratings` | FactSet | **401** | — | — | paywalled |

**⚠️ The horizons differ, and this determines the build plan. Verified by direct fetch, 15 Aug 2026:**

| Source | Quarterly EPS | Quarterly revenue | Annual EPS | Annual revenue | Staleness/momentum fields |
|---|---|---|---|---|---|
| Nasdaq (Zacks) | ✅ | ❌ | ✅ | ❌ | ✅ 4-week up/down revision counts |
| StockAnalysis (S&P) | ❌ | ❌ | ✅ FY1 only | ✅ FY1 only | ❌ (but gives price targets + rating split) |
| **Alpha Vantage** | ✅ | ✅ | ✅ | ✅ | ✅ 7/30/60/90-day-ago averages + 7/30d revision counts |

**Alpha Vantage `EARNINGS_ESTIMATES` is therefore the only free source carrying quarterly REVENUE consensus, and it is
also the only one with built-in staleness fields.** Verified schema (IBM via the `demo` key — other tickers need a free
key): 41 rows per ticker across `"horizon": "fiscal quarter"` and `"fiscal year"`, each carrying
`eps_estimate_average/high/low/analyst_count`, `eps_estimate_average_{7,30,60,90}_days_ago`,
`eps_estimate_revision_{up,down}_trailing_{7,30}_days`, and `revenue_estimate_average/high/low/analyst_count`.
The `*_days_ago` fields hand us a ready-made staleness and revision-momentum feature with zero extra work.

**Nasdaq** returns `quarterlyForecast` and `yearlyForecast`, each row carrying
`fiscalEnd, consensusEPSForecast, highEPSForecast, lowEPSForecast, noOfEstimates, up, down` (up/down = revisions over
the trailing 4 weeks — **free revision momentum**). Verified live for a candidate name:
```
COST quarterlyForecast row: {fiscalEnd:"Aug 2026", consensusEPSForecast:6.51,
                             highEPSForecast:6.71, lowEPSForecast:6.28,
                             noOfEstimates:11, up:2, down:1}
```
`/api/company/{T}/earnings-surprise` returns the last 4 quarters of
`fiscalQtrEnd, dateReported, eps, consensusForecast, percentageSurprise` — our firm-specific beat prior, free.
**No revenue estimates at any horizon.**

**StockAnalysis.com** embeds the whole payload as a JS object literal in server-rendered HTML — no JS execution needed,
but note the keys are **unquoted** (`no:`, `avg:`), so this is a regex/JSON5 parse, not `JSON.parse`. Verified:
```
NVDA: eps:{"2027-01-31":{no:48, avg:8.96264, low:8.2, high:9.58457}}
      revenue:{"2027-01-31":{no:53, avg:393881298140, low:358367000000, high:415524773220}}
COST: eps:{"2026-08-31":{no:32, avg:20.57893, low:20.32, high:21.15128}, "2027-08-31":"[PRO]"}
      revenue:{"2026-08-31":{no:34, avg:301566284800, low:297183000000, high:304110000000}}
      priceTargets:{source:"spg", avg:1077.31, median:1100, low:740, high:1315, numPriceTargets:35}
      currentRatings:{source:"spg", consensus:"Buy", score:5, count:39, strongBuy:19, buy:4, ...}
```
Note the COST figures are **fiscal-YEAR** (FY ending 2026-08-31), not quarterly. In-page attribution: *"Price targets,
consensus ratings and financial forecasts are provided by S&P Global Market Intelligence. Individual analyst data is
provided by TipRanks."* **FY2 onwards is the literal string `"[PRO]"`.**

Others: FMP, Finnhub, Polygon all reject keyless requests. FMP free tier = **250 calls/day, 500MB/30d**;
`GET /stable/analyst-estimates?symbol=AAPL&period=annual` returns revenue, EPS, EBITDA, net income
(https://site.financialmodelingprep.com/developer/docs/stable/financial-estimates). Note FMP migrated from
`/api/v3/{symbol}` path-params to `/stable/?symbol=` query-params — old tutorials 404.
Yahoo's own provider page confirms the switch: *"Global company profile, EPS and revenue estimates & actuals, analyst
recommendations and price target data provided by **S&P Global Market Intelligence**"*
(https://help.yahoo.com/kb/finance-for-web/exchanges-data-providers-yahoo-finance-sln2310.html). **Yahoo is no longer an
I/B/E/S proxy.**

### 2.7 Visible Alpha — the thing we cannot have, but should imitate

Founded 2015 by a bank consortium; acquired by **S&P Global May 2024**; launched inside Capital IQ Pro Mar 2025.
It ingests **full working sell-side spreadsheet models**, not headline numbers, and normalises every line item —
"builds consensus estimates from the bottom up, normalizing the data inputs, rather than just extracting and
aggregating headline conclusions" (https://hedgenordic.com/2023/06/demystifying-consensus-estimates/).

- **1M+ consensus line items**, averaging **156–161 per company**, up to ~1,000 for some; KPI, segment, geographic,
  income statement, balance sheet, cash flow, across 170+ industries, with click-through to the source Excel formulas
  and named-broker attribution per line item.
- Coverage 7,000–7,300 companies in consensus (17,000+ in broker coverage), history from 2015, **minimum 3 covering
  analysts** to publish.
- Contributor count **conflicts across S&P's own properties**: 200+ (press release), 250+ (visiblealpha.com), 260+
  (S&P Marketplace). Cite one page or say "200–260".
- **Public availability: zero.** No free tier, no public API, nothing scrapable.

**Why it matters to us:** sell-side notes quote VA consensus, so the number an analyst is "beating" may be a VA
line-item consensus that will never match Yahoo or Nasdaq. And conceptually, VA is exactly what our agent should build
internally: a **line-item consensus, not a headline one**.

---

## 3. Documented systematic biases

### 3.1 The base rate: most companies beat

FactSet, Earnings Insight 7 Aug 2026 p.7–9, historical averages over all 500 companies:

| Metric | 1-yr avg | 5-yr avg | 10-yr avg |
|---|---|---|---|
| % of S&P 500 beating EPS | 80% | **78%** | **76%** |
| Aggregate EPS surprise | +9.2% | **+7.0%** | **+7.4%** |
| % of S&P 500 beating revenue | 78% | **70%** | **68%** |
| Aggregate revenue surprise | +1.9% | **+1.9%** | **+1.6%** |

FactSet also reports (Earnings Insight 10 Apr 2026 p.3,
https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_041026A.pdf):

> "the actual earnings growth rate has exceeded the estimated earnings growth rate at the end of the quarter in
> **37 of the past 40 quarters** for the S&P 500. The only exceptions were Q1 2020, Q3 2022, and Q4 2022."

The uplift from quarter-end to end of season: **+5.8pp (10-yr), +7.0pp (5-yr), +6.1pp (last 4 quarters)**. Over 10
years actual earnings exceeded estimated by **7.1%**; over 5 years **7.3%**; last 4 quarters **7.2%**.

DWS's independent computation — measured vs consensus **as of fiscal quarter-end**, with a $0.01 materiality
threshold — gives a *lower* per-company beat: **average EPS beat +3.5% (2011–2025 ex 2020–21)**. For 3Q25: 78% beat /
18% miss / aggregate +5.9% (+4.6% ex-Financials); sales 55% beat / 20% miss / aggregate +2.5%.

*Conflict noted, and it matters*: FactSet's ~+7% is **share-weighted aggregate** (Σactual/Σestimate), so mega-cap
outliers dominate — Q2 2026's +29.2% vs LSEG's +8.4% proves how badly. DWS's +3.5% is the historical average of that
same aggregate. The **median company** beat is far smaller than either — see §4.2.

### 3.2 Sector base rates — computed by us from LSEG I/B/E/S, 24Q2–26Q2 (9 quarters)

Computed from LSEG S&P 500 Earnings Scorecard Exhibits 26 & 27, 14 Aug 2026. **This is a directly usable prior.**

| Sector | Mean EPS surprise % | % beating EPS | Mean revenue surprise % | % beating revenue |
|---|---|---|---|---|
| Health Care | +9.1% | 88.5% | +1.96% | 83.7% |
| Consumer Discretionary | +8.6% | 72.1% | +1.50% | 67.4% |
| Financials | +8.3% | 82.0% | +3.29% | 63.1% |
| Communication Services | +7.9% | 74.9% | +1.12% | 71.2% |
| Energy | +7.8% | 76.3% | +3.70% | 69.6% |
| Technology | +6.4% | **89.1%** | +2.19% | **87.3%** |
| Industrials | +6.1% | 80.8% | +1.50% | 65.3% |
| Materials | +5.3% | 67.1% | +0.91% | 56.9% |
| Utilities | +4.3% | 65.4% | +1.18% | 59.5% |
| Consumer Staples | +3.7% | 76.0% | +0.41% | 65.1% |
| Real Estate | +1.6% | 67.2% | +1.26% | 68.8% |
| **S&P 500** | **+7.1%** | **78.9%** | **+1.91%** | **70.2%** |

Read carefully: **Technology has the highest *frequency* of beats (89% EPS, 87% revenue) but only middling
*magnitude*.** Real Estate, Utilities and Consumer Staples have the smallest surprises in both dimensions — their
consensus is nearly right and there is little room to differentiate. Financials and Energy have the largest *revenue*
surprises (+3.3%, +3.7%) because their top lines are rate- and commodity-driven and analysts stop updating.

### 3.3 The walk-down / expectations-management literature, with magnitudes

**Richardson, Teoh & Wysocki (2004), CAR 21(4):885–924** — the canonical walk-down paper.
https://onlinelibrary.wiley.com/doi/abs/10.1506/KHNW-PJYL-ADUB-0RP6 |
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=508943
53,653 firm-quarters, 1984–2001; `FESC = (actual − median forecast)/price`.
- Median consensus starts ~**1.0–1.6% of share price too high** at ~11 months out and ends *below* actual.
- **Crossover from optimistic to pessimistic occurs at Month −2 (1992–94) and Month −3 (1995–2001). No crossover at all
  pre-1992.**
- **Terminal bias: "The median forecast error in Month 0 is only one cent."** The walk-down lands the bar exactly one
  cent below actual — and the modern median surprise is still +1 cent (§4.2). The target is engineered.
- Drift rate after controls: `Horizon` coefficient **+0.00054 (t=19.1)**/month ≈ 5.4bp of price/month ≈ 0.65% over 12
  months.
- Incentive channel: firms with net insider selling post-announcement beat by **5.34% more** in EPS terms with **48%
  higher log-odds of meeting-or-beating**; a firm issuing an extra 10% of market cap next quarter beats by **~2.8%
  more**.

**Matsumoto (2002), TAR 77(3):483–514** (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=298868) — the two-lever
framework: managers avoid negative surprises via (a) upward earnings management and (b) downward guidance. Both are
operative. Predictors: high transient institutional ownership, reliance on implicit stakeholder claims, high
value-relevance of earnings. Cross-country replication (Kwon, Yin & Han, JIAAT 2006,
https://www.sciencedirect.com/science/article/abs/pii/S027842540500027X): **the US has the highest guidance rate in the
world (MGUI 37.9% vs Turkey 10.6%)** — the walk-down prior is strongest exactly where we operate.

**Bartov, Givoly & Hayn (2002), JAE 33(2):173–204**
(https://leeds-faculty.colorado.edu/rocks/bartov_givoly_hayn_2002.pdf), 64,872 firm-quarters 1983–1997:
- Favourable-surprise frequency rose **~50% (1983–93) → ~70% (1994–97)**; *exactly meeting* went 9% → 15%.
- **The premium: meeting-or-beating earns +2.3% abnormal quarterly return independent of surprise magnitude**
  (coefficient 0.023; 0.035 in 1994–97). This is why the practice persists.
- **Direct evidence of expectations management**: 39.50% of firm-quarters had a negative *surprise* but 48.65% had a
  negative *forecast error vs the earliest forecast* — a **9.15pp gap closed purely by walking estimates down**, widening
  to **13.66pp** in 1994–97. And **42.4% of quarters with a negative early-forecast error still printed a positive
  surprise vs only 11.0% the other way — nearly 4:1.**

**Call, Hribar, Skinner & Volant (2024), JAE 78(2)** — survey of corporate managers: they say they *predominantly issue
guidance that is conservative relative to their internal expectations*.
https://ideas.repec.org/a/eee/jaecon/v78y2024i2s0165410124000612.html

### 3.4 Guidance ranges: actuals sit near the **upper bound**, analysts anchor near the **midpoint**

The sharpest single exploitable finding in the literature.

- **Ciconte, Kolev & Tucker, "Does the Midpoint of Range Earnings Forecasts Represent Managers' Expectations?"**
  http://bear.warrington.ufl.edu/tucker/2013-2_management_range_forecasts.pdf |
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2061440
  They scale where actual earnings land in the guided range: +1 = upper bound, 0 = midpoint, −1 = lower bound.
  **Full sample 1996–2010: mean 0.93, median 1.00. 2002–2010: mean 1.20, median 1.00. 1996–2001: mean −0.37, median
  0.00.** In their words: the upper bound, not the midpoint, is the better proxy for management's expectation in the
  modern era — and *"analysts barely unravel the pessimistic bias that managers embed in range forecasts."*
- **Worse: analysts over-weight the lower bound.** Regressing revisions on upper- and lower-bound news shows analysts
  place significantly more weight on the lower bound, consistent with ambiguity aversion
  (https://www.sciencedirect.com/science/article/abs/pii/S0361368215000100).
- **Lowballing is a persistent firm-level trait.** Firms beating their own EPS guidance by ≥$0.05 for four consecutive
  quarters account for **9.4% of all guided firm-quarters**; median episode runs **6 quarters** (mean 7–8); a quarter of
  firms sustain exactly 4 quarters, ~10% for more than 3 years; of 293 firms that stopped, **94 restarted a later
  episode**. https://www.sciencedirect.com/science/article/pii/S0890838923000586
- Counterweight: managers are badly calibrated about their own guidance — >75% of 357 surveyed CFO/IR professionals
  believed earnings would land inside their guided range; it happens far less often
  (https://www.bloomberg.com/news/articles/2023-05-23/company-earnings-guidance-is-wrong-about-70-of-the-time).

**Build implication: where the company has guided a range for the quarter we forecast, our point estimate should sit
between the midpoint and the upper bound — closer to the upper bound for firms with a recent lowball track record —
while consensus sits at or slightly above the midpoint.**

### 3.5 Anchoring, asymmetric misreaction, and a tradeable anchoring factor

- **Abarbanell & Bernard (1992), JF 47(3):1181–1207**
  (https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1992.tb04010.x) — analysts **underreact to recent
  earnings**, consistent with the seasonal-random-walk story behind PEAD. **But**: "the underreactions in analysts'
  forecasts are at most only about half as large as necessary to explain the magnitude of the drift." Analyst
  underreaction is *a* source of drift, not the whole story.
- **Easterwood & Nutt (1999), JF 54(5):1777–1797**
  (https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00166) — the codable asymmetry: **analysts underreact to
  negative information but overreact to positive information.** After bad news the consensus is not cut enough; after
  good news it is raised too much.
- **Cen, Hilary & Wei (2013), JFQA 48(1):47–76**
  (https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/role-of-anchoring-bias-in-the-equity-market-evidence-from-analysts-earnings-forecasts-and-stock-returns/CC8469F1F8410C71234A882BDAB0DCC7 |
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=967309) — **the single most directly implementable factor in this
  document.**
  - Measure: `CAF = (firm forecast EPS − industry-median forecast EPS) / |industry-median forecast EPS|`.
  - Analysts are **pessimistic for high-CAF firms and optimistic for low-CAF firms** — they under-adjust away from the
    industry norm. **Earnings surprises are more positive for high-CAF firms.**
  - Long high-CAF / short low-CAF earns **0.76%/month = 9.12%/year** alpha, US 1983–2005, robust to standard factors,
    accruals, price momentum, earnings momentum, and nominal price per share.
  - Time-series anchoring (on the most recently announced EPS) also exists but generates only **one third** the profit.
  - **A stock split mechanically resets forecast EPS downward → split firms get more positive revisions, larger forecast
    errors and more negative surprises.** A split is a tradeable bias event.
  - Anchor stability: median nominal forecast EPS has sat between **$1.50 and $2.00 since 1978**.
- **Cautionary counterweight**: Linnainmaa, Torous & Yae (2016, JFE 122(1):42–64,
  https://ideas.repec.org/a/eee/jfinec/v122y2016i1p42-64.html) attribute **~60% of the autocorrelation in analyst
  forecast errors** to *rational* robust forecasting under model uncertainty, not bias. Do not treat all forecast-error
  persistence as irrationality.
- **Analysts hide their views in bundling rather than in the number.** Sean Wang et al., "Are Analyst Forecast Errors
  Really Kinky?" (https://scholar.smu.edu/business_accounting_research/142/): analysts with positive information who
  don't want to raise the bar signal it by revising the **price target and/or recommendation without fully revising
  EPS**. Their BF_Score (bundling intensity) is "an economically meaningful predictor of analyst-based earnings
  surprises"; high-BF_Score firms are more likely to barely meet or beat. **Adjusting surprises for BF_Score reduces the
  famous kink at zero by 66%** — two-thirds of the "earnings management" kink is actually predictable analyst bias.
  **Actionable: an EPS estimate that has not moved while price targets/ratings drifted up is a beat signal, and both
  ingredients are free (StockAnalysis gives price targets; Nasdaq gives EPS revision up/down counts).**

### 3.6 Staleness and the recency edge — the highest-conviction, cheapest edge available

- **O'Brien (1988), JAE 10(1):53–83** (https://www.sciencedirect.com/science/article/abs/pii/0165410188900237) — the
  foundational result: **the single most current forecast weakly dominates both the mean and the median consensus in
  accuracy.** Forecast *dates* matter more than analyst identity.
- **Butler, Kraft & Markov, "On the Weighting of Individual Analyst Forecasts in the Consensus"**
  (https://scholar.smu.edu/business_accounting_research/71/) — restricting to forecasts issued in the **60 days
  immediately preceding the announcement** and weighting on **forecast age, broker size and analyst experience** gives
  **3% to 15% lower MSE** than the naive equal-weight consensus, rising as the estimate count goes from 4 to 20.
  *This is the cleanest published number on what de-staling buys you.*
- **Brown (2001), FAJ 57(6):44–49** (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=202130) — a **two-factor model
  (forecast age + past accuracy)** performs as well as a six-factor model adding firm-specific experience, general
  experience, #companies, #industries and broker size, in-sample and out-of-sample, for annual and quarterly forecasts,
  1986–1998. **Two factors are enough.**
- **Sinha, Brown & Das (1997), CAR 14(1):1–42** — earlier studies failed to find persistent analyst skill *because they
  did not control for recency*. Once controlled, differential accuracy exists, strongest at minimum horizons of **5 and
  60 trading days**, and is **asymmetric**: "superior" analysts stay superior out of sample, "inferior" analysts do not
  stay inferior. **Reward the good ones; do not penalise the bad ones.**
- **LSEG StarMine SmartEstimate — the production proof.** Same I/B/E/S estimates, but exclude outliers, exclude
  estimates older than ~4 months and stale pre-revision figures, then weight by the analyst's Single-stock Estimate
  Score and by recency. The gap to the plain mean is the **Predicted Surprise % (PS%)**.
  https://lipperalpha.refinitiv.com/2021/03/20-years-of-starmine-smartestimates-20-years-of-outperformance/ |
  https://www.lseg.com/content/dam/data-analytics/en_us/documents/brochures/lseg-starmine-quantitative-analytics-brochure.pdf
  - **|PS%| > 2% predicts the sign of the actual surprise correctly ~70% of the time**, "across regions, market caps,
    sectors and financial measures". Larger |PS%| ⇒ higher hit rate.
  - **Revenue Predicted Surprise is more accurate than EPS: ~78% directional hit rate.**
  - Analyst accuracy persists: the most accurate analysts on a name are "roughly four times as likely to remain among
    the most accurate than to drop to the least accurate category."
  - Corroborating mean revisions in the same direction raise the hit rate further. LSEG's own overlay reached **75%**
    over 36 quarters in the US.
  - Verified across two independent periods (1998–2008, 2008–2017) with "essentially unchanged" performance.
  - Macro analogue: SmartEconomics predicts the direction of macro surprises **~61%** of the time — so ~70% on EPS is
    genuinely high.

**This is the most important number in this document. A recency-and-quality reweighting of the same public estimates —
with no new information at all — gets the surprise direction right ~70% on EPS and ~78% on revenue. That is a free,
replicable edge, and it tells us exactly what plain consensus is bad at: it is stale, and it is equal-weighted.**

### 3.7 Herding vs anti-herding — the literature genuinely conflicts, and both sides are useful

**Herding camp:**
- **Hong, Kubik & Solomon (2000), RAND J. Econ. 31(1):121–144**
  (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=142895) — inexperienced analysts are more likely to be
  **terminated for bold forecasts** even controlling for accuracy; consistently, they deviate less from consensus.
- **Hong & Kubik (2003), JF 58(1):313–351** (http://www.columbia.edu/~hh2679/analysts-Jf.pdf) — job separations reward
  optimism relative to accuracy, especially at brokerages with underwriting business.
- **Clement & Tse (2005), JF 60(1):307–341** — boldness rises with prior accuracy, brokerage size and general
  experience; falls with number of industries covered. **Bold forecasts are more accurate than herding forecasts**, and
  herding revisions are more strongly associated with subsequent forecast errors.

**Anti-herding camp:**
- **Bernhardt, Campello & Kutsoati (2006), JFE 80(3):657–675**
  (https://www.sciencedirect.com/science/article/abs/pii/S0304405X06000213) — test robust to correlated information,
  common shocks, and systematic optimism. **Result: no herding — analysts anti-herd.**
  - P(forecast overshoots actual *away from* consensus) = **0.59**
  - Forecasts **below** consensus fall short of actual **63%** of the time; forecasts **above** consensus exceed actual
    **56%** of the time
  - Stable to within <5pp across analyst order and <7pp across years and coverage levels
  - **Backed-out magnitude: the overshoot equals ~20% of the (forecast − consensus) difference.**
  - Replicated for Germany (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1019276), stronger under higher analyst
    competition.

**Reconciliation, and what to do about it.** These measure different decisions: Clement–Tse/HKS measure *whether* an
analyst deviates (an entry decision driven by career risk); BCK measure *by how much*, conditional on deviating (a
magnitude decision driven by strategic differentiation). Both can hold. For our build:
- **Shrink individual estimates ~20% back toward consensus** to recover an analyst's true belief. Naively taking the
  max/min of the published range over-extrapolates.
- **Consensus dispersion overstates true disagreement** — deflate it before using it as an uncertainty input.
- **Discount herding forecasts** (near-consensus, low-innovation); bold forecasts from high-past-accuracy, large-broker,
  low-coverage-breadth analysts carry the most private information.
- Anti-herding means the walk-down in §1.4 is a **guidance** effect, not a **herding** effect. Do not double-count.

### 3.8 Career incentives and regulation — how much bias actually remains in 2026

**Hovakimian & Saenyasiri (2010), FAJ 66(4):96–107**
(https://psc.ky.gov/pscecf/2012-00221/rateintervention@ag.ky.gov/10252012d/Hovakimian_and_Saenyasiri_-_Conflicts_of_Interest_and_Analysts_Behavior_-_FAJ_2010.pdf |
https://www.ssrn.com/abstract=1133102), 434,268 analyst-month observations, `Bias = (mean forecast − realized)/price × 100`:

| Period | N | Mean bias (% of price) |
|---|---|---|
| Before Reg FD (pre-Oct 2000) | 231,096 | **1.72** |
| Reg FD → Global Settlement | 77,305 | **1.97** |
| After Global Settlement | 125,867 | **0.41** |

- **Reg FD alone did essentially nothing** — bias *rose* 1.72 → 1.97 (insignificant). The common claim that Reg FD
  killed analyst optimism is **not supported**.
- **The 2003 Global Settlement did the work**: mean bias more than **four times smaller** (0.41 vs 1.97), significant at
  1%.
- **Median bias by fiscal year**: 1998 0.8, 2001 1.2, 2002 0.4, **2003 0.0, 2004 −0.1, 2005 0.0, 2006 0.0**. Median bias
  essentially disappears from 2003.
- **The walk-down flattened too**: for FY2004–2006 the walk-down in median forecast errors is described as
  **"practically nonexistent."**

**Barber, Lehavy, McNichols & Trueman (2006), JAE 41(1–2):87–117**
(https://www.anderson.ucla.edu/documents/areas/fac/accounting/Trueman_BuysHoldsSells.pdf) — recommendation distribution
Q1 1996: 60/36/4 buy/hold/sell → Q2 2000 peak: **74/24/2** → June 2003: **42/41/17**. The 10 sanctioned banks were
**not** the worst offenders (66.4% vs 64.7% buy pre-regulation — 1.7pp apart) but overcorrected hardest afterwards
(32.3% vs 45.7%). For reference, FactSet's 7 Aug 2026 count is **59.2% Buy / 36.0% Hold / 4.8% Sell** on 12,939 S&P 500
ratings — back to 1996 levels.

**Kadan, Madureira, Wang & Zach (2009), RFS**
(https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=1780&context=lkcsb_research) — post-regulation odds of a
pessimistic recommendation **+270%**, optimistic **−59%**; but informativeness fell, with average absolute 3-day
abnormal price reaction dropping **~7.1% → ~5.3% (a ~25% decline)**. Affiliated analysts were 22% more likely to issue
optimistic recs pre-regulation; insignificant after.

**All-star status stopped mattering post-Reg FD** (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1809200):
All-Star and more-experienced analysts no longer maintain superior accuracy, **large-brokerage analysts perform worse
than others**, and the importance of **prior forecast accuracy increases**. Pre-Reg FD advantages were access-based, not
skill-based. **For a 2026 model: weight past accuracy, not prestige.**

**Underwriter affiliation lives in the unfalsifiable numbers, not in quarterly EPS.** Lin & McNichols (1998, JAE
25(1):101–127, https://people.bath.ac.uk/mnsrf/teaching%202010/teaching%202009-2010/IB/Literature/L6-analysts/Lin-McNichols.pdf),
2,400 SEOs 1989–1994: affiliated analysts' **FY1 EPS forecasts are NOT more optimistic** (7.04% of price vs 7.09%
unaffiliated); the bias sits in **long-term growth forecasts** (21.29% vs 20.73%) and recommendations (1.74 vs 2.10 on
1–5, p<0.0001). **For a quarterly-EPS agent, affiliation is a second-order feature.**

**Coverage self-selection is a first-order measurement problem, though.** McNichols & O'Brien (1997, JAR 35 Supp:167–199,
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2813) — analysts **initiate coverage selectively on firms they
like** and **delay downgrades**. Key insight: **the observed distribution of forecast errors looks over-optimistic even
if every individual forecast is ex-ante unbiased**, because high forecasts are both more likely to be observed and more
likely to be over-optimistic. **Any backtest that ignores entry/exit into the consensus panel will overstate optimism
bias.**

### 3.9 Streaks beat magnitude — the surprise-persistence result, with the fine print

**The classic result concerns *realized earnings*, not analyst surprises.** Bernard & Thomas (1990, JAE 13(4):305–340,
https://www.sciencedirect.com/science/article/abs/pii/016541019090008R): autocorrelations of seasonally differenced
quarterly earnings at lags 1–4 are **+0.34, +0.19, +0.06, −0.24** (replicated by Lewellen at +0.34/+0.18/+0.05/−0.29,
all |t|>5, https://web.mit.edu/lewellen/www/Documents/Earnings.pdf). The matching price pattern at the next four
announcements is **+1.32%, +0.70%, +0.04%, −0.66%**, and **~25–30% of total PEAD is concentrated in the three-day
windows around the next three earnings announcements** — about 5% of trading days. Ball & Bartov (1996, JAE): the
market uses the correct signs but **underestimates the magnitude of serial correlation by ~50%**. Cross-sectionally,
the first-order SUE AR coefficient is **0.43 for profit firms vs 0.30 for loss firms**; highest for non-Q4 profit firms
(**0.47**), lowest for Q4 loss firms (**0.19**)
(Narayanamoorthy, JAR 2006, http://depot.som.yale.edu/icf/papers/fileuploads/2548/original/03-07.pdf).

**⚠️ But analyst-based surprises are much *less* autocorrelated, because analysts already price the persistence in.**
Loh & Warachka, "Streaks in Earnings Surprises and the Cross-Section of Stock Returns", Management Science
(https://digitalcommons.chapman.edu/cgi/viewcontent.cgi?article=1116&context=business_articles):
- "Analyst-based earnings surprises are **not highly autocorrelated**." **Only 22.28%** of their sample shows
  autocorrelated analyst-based surprises by a runs test at the 10% level.
- **But streaks still predict returns.** Long positive streaks (≥2 consecutive same-sign surprises) / short negative
  streaks, **ignoring magnitude entirely**, earns a **4-factor alpha of 0.603%/month**; adding a most-recent-magnitude
  quintile conditioner takes it to **0.882%/month**. Streak *terminations* earn insignificant returns.
- **A streak factor explains 54% of PEAD's four-factor alpha.**
- Their interpretation is gambler's fallacy, not genuine persistence — the effect survives in both the autocorrelated
  and independent subsamples.

Practitioner corroboration (MSCI, Feb 2019,
https://www.msci.com/research-and-insights/blog-post/should-we-be-surprised-by-earnings-surprises): companies that beat
(missed) last quarter more often beat (miss) this quarter, and **the probability of continuing rises with streak
length**; positive-surprise frequency is higher in the US than globally and higher still in US large caps. The market
response is **larger when a streak ends** — a positive surprise following a negative one generates **more than 2×** the
residual return of two consecutive beats.

**Actionable: encode streak sign and length as a first-class feature, not just last quarter's SUE magnitude. But do not
assume strong analyst-surprise autocorrelation — mostly it isn't there.**

---

## 4. What the typical consensus error actually looks like

### 4.1 In cents, not percent — and it does not scale with company size

Cheong & Thomas, "Why do EPS forecast error and dispersion not vary with scale?"
(https://raw.rutgers.edu/docs/seminars/Cheong_Thomas_2010.pdf), I/B/E/S, decile-sorted by share price:

- **Median absolute quarterly EPS forecast error: 2–3 cents. Mean: 5–6 cents.**
- Interquartile range of the signed error: **4–5 cents, in every price decile.**
- **Median dispersion (SD across analysts): 2 cents, in every price decile.** Mean 3 cents (5 cents in the top decile).
- Sector variation: errors and dispersion are **lower in health care and technology**, **higher in transport and
  utilities**.

Forecast error is roughly **constant in cents** whether EPS is $0.30 or $5.00. Consequences:

- On a **$5.00 EPS** name, a 3-cent error is 0.6%. On a **$0.40 EPS** name, 3 cents is 7.5%.
- If the hackathon scores **percentage error, low-EPS-base names are a variance trap.** Nike's last five quarters of
  actual-vs-consensus EPS surprise: **+66.7%, +16.7%, +43.2%, +81.5%, +80.0%** — because its quarterly EPS base is
  $0.12–$0.53 (https://www.investing.com/equities/nike-earnings). A 5-cent absolute error there is a 40% percentage
  error.
- If it scores **absolute cents** or **cents scaled by price**, high-EPS names are the safer place to be aggressive.
- Corollary: the ~$0.05 "nickel" is a real behavioural unit. Analysts and managers both round to nickels
  (Herrmann & Thomas 2005; Bamber et al. 2010; Shue & Townsend 2021 show market participants process EPS in **nominal
  absolute terms, not proportionally**). Our output should be a clean 2-decimal number, and we should expect actuals to
  cluster on nickels.

### 4.2 The shape of the surprise distribution

Bissessur & Veenman, "Analyst information precision and small earnings surprises", Review of Accounting Studies
(https://link.springer.com/article/10.1007/s11142-016-9370-2), US firms 1993–2013:

- **Median firm-quarter surprise = +1 cent. Q1 = −1 cent, Q3 = +4 cents.**
- **26.3%** of firm-quarters land on a **0 or +1 cent** surprise.
- Dispersion is V-shaped and asymmetric: mean dispersion in the −1/−2 cent bins (2.754) is **~50% higher** than in the
  +1/+2 cent bins (1.868). The 0 and +1 bins have the lowest dispersion of all.
- **Moving from high to low forecast dispersion raises the conditional probability of a 0-or-+1-cent surprise from
  14.0% to 34.6%.**

**Actionable: low dispersion is itself a predictor of a tiny positive surprise. When dispersion is 1–2 cents, the modal
outcome is consensus + 1 cent and we should not be bold. Wide dispersion is our licence to take a real position.**

### 4.3 Revenue vs EPS — revenue is the softer target

- Index aggregate revenue surprise: **5-yr +1.9%, 10-yr +1.6%** vs EPS's +7.0%/+7.4% (FactSet 7 Aug 2026).
- Our 9-quarter LSEG computation: S&P 500 mean revenue surprise **+1.91%** vs mean EPS surprise **+7.1%**.
- StarMine's directional hit rate is **higher for revenue (78%) than EPS (~70%)**.
- StarMine's own SmartForecast paper notes revenue, being the top line, "tends to be [more] stable and persistent over
  time, making the RW [random-walk] model a hard benchmark to beat"
  (https://www.lseg.com/content/dam/data-analytics/en_us/documents/white-papers/lseg-starmine-smart-forecast-model-whitepaper.pdf).
- Revenue also has **fewer definitional traps** — no SBC, no restructuring, no MTM gains.

**Build implication: expect to beat consensus more reliably on revenue than on EPS, with a *smaller* systematic positive
adjustment on revenue (+0.5% to +2%) than on EPS (+2% to +5%).**

### 4.4 The Q2 2026 regime we are forecasting into

- 86% beat EPS (highest since Q2 2021's 87%), 76% beat revenue; blended earnings growth **50.4%** (32.0% ex
  Alphabet/Amazon); blended revenue growth **15.0%** — highest since Q4 2021.
- Estimates were revised **UP 3.4%** during the quarter vs a −2.0% 5-yr average.
- Only 33% of Q3 2026 guiders issued negative guidance vs a 58% 5-yr average.
- **The market is not paying for beats**: positive-surprise names averaged **+0.4%** over the −2/+2 day window vs a 5-yr
  average of **+1.0%**; negative-surprise names **−2.3%** vs a 5-yr average of **−3.0%**.
- Forward 12-month P/E 20.0 (5-yr 19.9, 10-yr 19.0); bottom-up target price implies +18.1%.
(All: FactSet Earnings Insight 7 Aug 2026.)

---

## 5. Whisper numbers, crowds, and the buy-side bar

The published consensus is not the bar the stock trades against.

- **Bagnoli, Beneish & Watts (1999), "Whisper forecasts of quarterly earnings per share", JAE 28(1):27–50**
  (https://www.sciencedirect.com/science/article/abs/pii/S016541019900018X). 943 whispers / 3,546 First Call forecasts,
  127 firms (91% high-tech), Jan 1995 – May 1997. Whispers were **more accurate** than First Call and a **better proxy
  for market expectations**. First Call *underestimated* earnings; whispers *overestimated* them. Trading the
  whisper-vs-First-Call gap, opened 5/3/2 days before the print and closed the day before, earned market-adjusted
  returns of **1.7% / 1.3% / 1.0%**. Timing explained only part of the gap.
- **⚠️ Conflicting later evidence.** Brown & Fernando (2011), JBR 64(5):476–482
  (https://ideas.repec.org/a/eee/jbrese/v64y2011i5p476-482.html): on a **broader sample, analyst forecasts are MORE
  accurate than whispers**; whispers carry incremental value-relevant information but it is fully impounded in price;
  whispers are more common for firms with *lower* forecast accuracy. **Treat "the whisper" as a positioning/sentiment
  signal, not a better point forecast.**
- **Crowdsourced consensus does add accuracy.** Jame, Johnston, Markov & Wolfe (2016, JAR 54(4):1077–1110,
  https://onlinelibrary.wiley.com/doi/10.1111/1475-679X.12121 ; working paper
  https://acfr.aut.ac.nz/__data/assets/pdf_file/0004/29722/536465-R-Johnston-Crowds-3-19-2015-final-with-cover.pdf) —
  51,012 Estimize forecasts from 3,255 contributors, 1,874 firms, 2012–13:
  - A consensus pooling **I/B/E/S + Estimize is more accurate than I/B/E/S alone 60% of the time at 30 days and 64% on
    the day before the announcement.**
  - **~50% of Estimize forecasts are issued in the two days before the print, versus <2% of I/B/E/S forecasts.**
  - Individual Estimize forecasts are less accurate at long horizons, **equally accurate at short horizons, and less
    biased and bolder (further from consensus)** — direct evidence that sell-side analysts shrink toward consensus.
  - Estimize's own research (Drogen & Jha 2013, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2337709) claims the
    Estimize consensus beats the comparable Street consensus **58–65%** of the time, **65% with ≥20 contributors**.

**The through-line across whispers, Estimize, SmartEstimate and Butler–Kraft–Markov is identical: recency is the
dominant axis, and the late-filed, pooled, or accuracy-weighted forecast beats the stale equal-weighted mean.**

---

## 6. Where an AI agent has genuine edge — and where it does not

### 6.1 What analysts have that we cannot get

| Their input | Why we can't replicate it |
|---|---|
| Management access — IR calls, non-deal roadshows, conference 1:1s | Reg FD limits content, but tone and emphasis still leak. Not obtainable. |
| Expert networks (GLG, Third Bridge, AlphaSights, Guidepoint) | Paid, gated, $1k+/hour. |
| Primary channel checks — distributors, franchisees, store managers | Needs a rolodex and days of calls. |
| Licensed alt-data — Consumer Edge / Yipit / Second Measure card panels, Sensor Tower, RS Metrics satellite | Six-figure subscriptions. |
| **Visible Alpha line-item consensus** (segment revenue, units, margin) | No free tier. We cannot see what consensus is for a *segment* — and that is what the analyst is actually beating. |
| The vendor's live intraday consensus and the I/B/E/S Excluded file | Licensed. |

**Honest conclusion: for a company whose quarter turns on a channel-check-only variable — iPhone sell-through, a drug's
script trend, one semiconductor customer's pull-in — we will lose to the covering analyst. Do not pick that company.**

### 6.2 ⚠️ What we CANNOT claim: the "LLMs beat analysts" result has been withdrawn

**Kim, Muhn & Nikolaev, "Financial Statement Analysis with Large Language Models" (Chicago Booth) is WITHDRAWN by its
own authors.** arXiv 2407.17866 was withdrawn at v3 (20 Feb 2025) and remains withdrawn. The withdrawal comment,
verbatim:

> "A co-author identified inconsistencies in the data and analyses while attempting to replicate past analyses from the
> working paper. Accordingly, we have temporarily withdrawn the working paper from circulation while we review the
> research findings."

Nikolaev's Chicago Booth page (https://faculty.chicagobooth.edu/valeri-nikolaev/ongoing-research-projects) confirms he
independently verified the inconsistencies and adds that the companion paper **"Bloated Disclosures: Can ChatGPT Help
Investors Process Information?" was also withdrawn** after replication failed. **Do not cite the widely-quoted "GPT-4
60.35% vs analysts 52.71%" number on stage. It will be a bad look if a judge knows.**

**The direct contradiction.** Li, Shen, Tu & Zhou, "The Promise and Peril of Generative AI: Evidence from GPT as
Sell-Side Analysts" (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4480947 |
https://arxiv.org/pdf/2412.01069) — 7,114 earnings press releases, 1,000 randomly selected firms, window centred on
GPT-4 Turbo's 30 Apr 2023 cutoff:
- **GPT is significantly LESS accurate than analysts.** Mean |FE_GPT| − |FE_analyst| = **+0.033 pre-cutoff, +0.038
  post-cutoff**. GPT beats analysts in >25% of firm-quarters.
- **Directional accuracy 49.3%** (inferred from GPT's numeric EPS) or **47.7%** (prompted directly) — a coin flip —
  **vs 71.1% for analysts in their sample.**
- They state explicitly that they could not replicate Kim et al.
- **The one useful mechanism they do find**: GPT's forecast error falls monotonically with `MetricOverlap` — how much
  its emphasised metrics agree with the analyst-emphasised metrics. Mean |FE| **0.117 at zero overlap → 0.061 at
  maximum, ~48% lower.** *Actionable: make the agent explicitly identify and reason about the metrics the sell-side
  actually models for this company, rather than whatever the press release foregrounds.*

*Conflict noted*: the two papers report analyst directional accuracy of **52.7%** vs **71.1%**. Different tasks —
I/B/E/S EPS-change direction on a 1968–2021 panel vs GAAP EPS growth direction on a 2022–24 sample of large covered
firms. Do not benchmark against either without replicating the task definition.

### 6.3 ⚠️ Look-ahead bias will make our eval harness lie to us

This is the single biggest methodological risk to hill-climbing on historical quarters overnight.

- **Levy (Chicago Booth), "Caution Ahead: Numerical Reasoning and Look-ahead Bias in AI Models"**
  (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5082861): LLMs have **extremely poor numerical reasoning**, and
  commercial LLMs suffer significant look-ahead bias that "may explain a large portion of their predictability."
  **Perturbing the financial statements drops LLM predictive accuracy to chance** — memorisation, not analysis.
- **Lopez-Lira, Tang & Zhu, "The Memorization Problem"** (https://arxiv.org/html/2504.14765v2): counterfactual
  forecasting ability is formally **non-identified** once the model has seen realised values. LLMs reproduce exact
  pre-cutoff values; **instructions to respect historical boundaries fail; masking fails** (models reconstruct entities
  and dates from minimal context); no recall post-cutoff. Small post-cutoff robustness checks have **too little power**
  to distinguish skill from memorisation. Memorisation extends to embeddings.
- **Gao, Jiang & Yan, "A Test of Lookahead Bias in LLM Forecasts"** (http://arxiv.org/abs/2512.23847) — proposes
  **Lookahead Propensity (LAP)**: from a *date-only recall query*, the total first-token probability the model assigns
  to directional labels. LAP is materially positive throughout the in-sample period and **collapses to ~0 immediately
  after the training cutoff**. A positive `LAP × forecast` interaction in an accuracy regression diagnoses
  contamination. **Cheap, portable, and we should run it on our own backtest.**

**Practical rule for our eval harness: any quarter that closed before the model's training cutoff is contaminated. Our
honest evaluation set is post-cutoff quarters only. If we must use older quarters for development, report them
separately and never as evidence of edge.**

### 6.4 And report F1, not accuracy

**FinCall-Surprise** (ACL 2026, https://aclanthology.org/2026.acl-long.610.pdf , data
https://github.com/Tizzzzy/FinCall-Surprise) — 2,688 earnings calls 2019–2021, multi-modal (transcript + audio +
slides), 26 LLMs benchmarked. The headline finding is the **"high performance illusion": 15 of 26 models exceed 70%
accuracy but most fall below 55% on precision/recall/F1**, because the data is heavily imbalanced toward positive
surprises and the models simply learn the base rate. Two finance-fine-tuned models scored **12% and 10%** due to
instruction-following degradation. Audio and visual modalities added only marginal gains.

**With a 78% positive base rate, "accuracy" on surprise direction is nearly meaningless. Always report F1, and always
report against a "always predict beat" baseline.**

### 6.5 What we genuinely can do better

1. **Kill the staleness.** The best-evidenced, cheapest edge (§3.6). Collect estimate dates and revision counts (free
   from Nasdaq's `up`/`down` and Alpha Vantage's `*_days_ago` fields), apply a hard staleness cutoff, weight by
   recency, and rebuild a SmartEstimate-like number. Published hit rates: ~70% EPS / ~78% revenue.
2. **Breadth of the text corpus.** A human analyst reads one company's transcript. We can read every transcript in the
   supply chain, every 8-K, every competitor's guidance, every 10-Q footnote, in minutes. Evidence that transcript text
   carries orthogonal signal: "Which Voices Move Markets?" (https://arxiv.org/html/2604.13260v1) — FinBERT over 6.5M
   sentences from 16,428 S&P 500 transcripts (Apr 2015–Dec 2025) finds **analyst-question sentiment carries 49% of the
   optimal section weight / 59.6% of SHAP importance**; section-weighted sentiment IC **0.119** vs 0.081 for a simple
   mean, analyst-only IC **0.141**, FF5 alpha **2.03%/month (t=6.49)**, rising out-of-sample to **2.77%/month** — and it
   **survives controlling for SUE** (SUE coefficient falls only 0.01425 → 0.01342). The signal is largely orthogonal to
   the earnings surprise.
   Also: Liang & Carrasco Kind (https://ideas.repec.org/p/arx/papers/2505.18419.html) — LLM-measured managerial
   **non-responses during Q&A** predict higher analyst forecast error, dispersion and PEAD. **"What did management dodge?"
   is a free, computable feature.**
   And Matera (2025) (https://arxiv.org/html/2511.15214) uses LLM-generated counterfactual transcripts to show
   **analysts over-react to sentiment/optimism and under-react to narratives of risk and uncertainty** — a clean causal
   confirmation of Easterwood & Nutt's asymmetry (§3.5).
3. **XBRL granularity at machine speed.** Verified working 15 Aug 2026, keyless, 10 req/s, declared User-Agent required:
   - `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` — every tagged fact, every period
   - `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/<Tag>.json` — one concept's full history
   - `https://data.sec.gov/api/xbrl/frames/us-gaap/<Tag>/USD/CY2026Q1I.json` — one concept across **all** filers for a
     period (instant peer comps)
   - `https://data.sec.gov/submissions/CIK##########.json` — filing index incl. 8-K exhibit URLs
   - `https://efts.sec.gov/LATEST/search-index?q=...&forms=8-K` — EDGAR full-text search (returns 200)

   This gives exact prior-year comparatives, seasonality, segment tables, share-count trajectories and tax rates — the
   deterministic scaffolding — with zero transcription error.
4. **No career incentives.** No banking relationship, no corporate access to protect, no reason to shrink toward the
   crowd, no penalty for being bold and wrong. The literature says analysts under-shoot their own private information
   precisely because of these constraints (§3.7). **We should be deliberately bolder than consensus where our evidence
   is strong, because the consensus is contractually timid.**
5. **Perfect memory of the beat pattern.** Compute, per company, an 8–12 quarter distribution of (actual − consensus),
   (actual − guidance midpoint), and position-within-guidance-range. Humans do this by feel; we can do it as a prior.
   **Highest ROI feature in the whole build.**
6. **Deterministic arithmetic.** Rebuild the seasonal/segment bridge, share count and tax rate in TypeScript, not in the
   LLM's head. Levy's result (§6.3) says LLM numerical reasoning is genuinely poor — keep the model on judgement and
   extraction, and put every number through code.

---

## 7. The forecasting recipe implied by all of the above

```ts
// Everything is expressed as a delta to a named, timestamped consensus.
estimate = consensus_recency_weighted            // §3.6 — SmartEstimate clone, drop >90d, exp(-age/τ)
         + guidance_position_adj                 // §3.4 — lo + 0.65*(hi-lo) .. hi, not the midpoint
         + firm_beat_prior                       // §3.5/§6.5 — median (actual - consensus), last 8Q
         + sector_prior                          // §3.2 table, shrunk toward zero
         + streak_adj                            // §3.9 — sign & length of consecutive same-sign surprises
         + anchoring_adj                         // §3.5 — CAF vs industry-median forecast EPS
         + revision_momentum_adj                 // Nasdaq up/down counts; bundling divergence (§3.5)
         + driver_model_delta                    // our own bottom-up KPI build vs the implied consensus build
```

with an explicit **decision rule for whether to differ from consensus at all**: only take a non-consensus position when
`|estimate − consensus|` exceeds the noise floor (~2–3 cents, §4.1) **and** the implied Predicted Surprise % exceeds 2%
(§3.6). Otherwise print consensus + 1 cent and take the 78% base rate.

---

## Appendix: source inventory

| Source | What it gives | URL |
|---|---|---|
| FactSet Earnings Insight (weekly PDF), 7 Aug 2026 | Beat rates, surprise magnitudes, 1/5/10-yr averages, guidance splits, price reaction, sector detail | https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_080726.pdf (latest always redirects from https://www.factset.com/earningsinsight) |
| FactSet Earnings Insight, 10 Apr 2026 | "37 of past 40 quarters"; +5.8/+7.0/+6.1pp season uplift | https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_041026A.pdf |
| LSEG S&P 500 Earnings Scorecard, 14 Aug 2026 | I/B/E/S beat rates + surprise factors by sector, 9 quarters; pre-announcement N/P ratio | https://lipperalpha.refinitiv.com/wp-content/uploads/2026/08/TRPR_82201_20260814.pdf |
| DWS S&P 500 EPS Tracker | −3.3% avg quarterly cut vs +3.5% avg beat, 2011–2025 | https://download.dws.com/download/asset/inline/49221af1-0106-4b46-a4cd-2bcae5fec944?tenant=Dwscom |
| StarMine SmartEstimate performance | ~70% EPS / ~78% revenue directional hit rate at PS% > 2% | https://lipperalpha.refinitiv.com/2021/03/20-years-of-starmine-smartestimates-20-years-of-outperformance/ |
| **Kaplan, Martin & Xie, "Truncating Optimism" (JAR 2021)** | I/B/E/S drops 6% of forecasts; ~10× more likely when it enables a beat | https://doi.org/10.1111/1475-679X.12397 |
| **Larocque, Watkins & Weisbrod (JAR)** | 5 vendors, 94,030 firm-quarters, substantial actual & forecast differences; open replication code | https://doi.org/10.1111/1475-679x.70072 · https://github.com/eweisbrod/consensus |
| Call, Hewitt, Watkins & Yohn (RAST 2021) | Same I/B/E/S file, different vintages, different meet-or-beat classifications | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2788140 |
| Richardson, Teoh & Wysocki (CAR 2004) | Walk-down magnitudes; "median forecast error in Month 0 is only one cent" | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=508943 |
| Bartov, Givoly & Hayn (JAE 2002) | +2.3% MBE premium; 9.15→13.66pp expectations-management gap | https://leeds-faculty.colorado.edu/rocks/bartov_givoly_hayn_2002.pdf |
| Ciconte, Kolev & Tucker | Actuals land at the upper bound of guidance ranges (median ACT_DIS = 1.00) | http://bear.warrington.ufl.edu/tucker/2013-2_management_range_forecasts.pdf |
| Cen, Hilary & Wei (JFQA 2013) | CAF anchoring factor, 0.76%/month alpha | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=967309 |
| Loh & Warachka (Mgmt Sci) | Streaks explain 54% of PEAD alpha; only 22.28% of analyst surprises autocorrelated | https://digitalcommons.chapman.edu/cgi/viewcontent.cgi?article=1116&context=business_articles |
| Butler, Kraft & Markov | Age+accuracy weighting → 3–15% MSE reduction | https://scholar.smu.edu/business_accounting_research/71/ |
| Brown (FAJ 2001) | Two factors (age + past accuracy) ≈ six factors | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=202130 |
| Hovakimian & Saenyasiri (FAJ 2010) | Reg FD did nothing; Global Settlement cut bias 1.97 → 0.41 | https://www.ssrn.com/abstract=1133102 |
| Cheong & Thomas | Median abs quarterly EPS error 2–3¢, dispersion 2¢, invariant to scale | https://raw.rutgers.edu/docs/seminars/Cheong_Thomas_2010.pdf |
| Bissessur & Veenman (RAST 2016) | Median surprise +1¢; dispersion asymmetry around zero | https://link.springer.com/article/10.1007/s11142-016-9370-2 |
| Jame, Johnston, Markov & Wolfe (JAR 2016) | Estimize pooling beats I/B/E/S 60–64% of the time | https://onlinelibrary.wiley.com/doi/10.1111/1475-679X.12121 |
| Bagnoli, Beneish & Watts (JAE 1999) | Whispers vs First Call | https://www.sciencedirect.com/science/article/abs/pii/S016541019900018X |
| Brown & Fernando (JBR 2011) | Contradicts the above on a broader sample | https://ideas.repec.org/a/eee/jbrese/v64y2011i5p476-482.html |
| **Li, Shen, Tu & Zhou** | GPT-4 47.7–49.3% directional vs 71.1% analysts; MetricOverlap mechanism | https://arxiv.org/pdf/2412.01069 |
| **Levy, "Caution Ahead"** | LLM look-ahead bias; perturbation drops accuracy to chance | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5082861 |
| **Gao, Jiang & Yan, LAP test** | Portable look-ahead-bias diagnostic for our own harness | http://arxiv.org/abs/2512.23847 |
| FinCall-Surprise (ACL 2026) | "High performance illusion" — report F1, not accuracy | https://aclanthology.org/2026.acl-long.610.pdf |
| "Which Voices Move Markets?" | Analyst-question sentiment carries signal orthogonal to SUE; 2.03%/mo FF5 alpha | https://arxiv.org/html/2604.13260v1 |
| SEC XBRL APIs | Free, keyless, 10 req/s, verified working 15 Aug 2026 | https://data.sec.gov/api/xbrl/companyfacts/ · /companyconcept/ · /frames/ · https://data.sec.gov/submissions/ |
| Nasdaq consensus API (Zacks) | Free JSON: EPS consensus, hi/lo, count, 4-week revision up/down | `https://api.nasdaq.com/api/analyst/{TICKER}/earnings-forecast` |
| StockAnalysis.com (S&P Global MI) | Free server-rendered JSON: EPS **and revenue** consensus, counts, price targets, ratings | `https://stockanalysis.com/stocks/{ticker}/forecast/` |

---

## Implications for our build

1. **Architect as `consensus + delta`, never as a bare level.** Scoring is 50% accuracy against actuals *and* against
   consensus, so the delta is literally the scored object. Store consensus, our delta, and each delta component
   **separately** in SQLite with a timestamp, so the eval harness can attribute error to specific priors and so the
   demo can show a decomposed waterfall. This is simultaneously the best architecture and the best demo.

2. **Bake in the beat, but the *right size* of beat, and know it is currently inverted.** Consensus does NOT already
   price the average beat — that is the entire point of the walk-down. For a guidance-giving S&P 500 company in a
   normal regime the honest prior is **EPS ≈ consensus × (1 + 2% to 5%)** and **revenue ≈ consensus × (1 + 0.5% to 2%)**,
   sector-adjusted from §3.2. **Do not use FactSet's headline +7.0% aggregate** — it is share-weighted and
   mega-cap-distorted (Q2 2026's +29.2% vs LSEG's +8.4%). The **median** company beats by about **+1 cent**; DWS's
   per-company average beat is **+3.5%**. Shrink toward zero for Real Estate / Utilities / Consumer Staples. **And
   because analysts raised estimates in 4 of the last 5 quarters (§1.5), make the beat prior a *fitted parameter over
   the last 4–8 quarters*, not a constant.**

3. **Recency-weighting is the highest-conviction, lowest-effort edge. Build it first.** Drop estimates older than ~90
   days, weight by `exp(-age/τ)` and by broker trailing accuracy where observable, and publish our own Predicted
   Surprise %. Only take a non-consensus position when |PS%| > 2%. LSEG's own published hit rate at that threshold is
   ~70% EPS / ~78% revenue, and Butler–Kraft–Markov put the MSE gain from age+accuracy weighting at **3–15%**. Brown
   (2001) says **two factors (age + past accuracy) are enough** — do not over-engineer.

4. **Use the upper bound of guidance, not the midpoint.** Ciconte/Kolev/Tucker: median actual sits at the **upper
   bound** (ACT_DIS median 1.00, mean 1.20 post-2002), and analysts under-adjust because they over-weight the lower
   bound. If the company guided `[lo, hi]`, our prior should be `lo + 0.65×(hi−lo)` to `hi`. Add a lowball flag:
   ≥$0.05 beat vs own guidance for 4+ consecutive quarters ⇒ push to the upper bound. **Note the Zacks wrinkle**: Zacks
   drops pre-guidance estimates outside the range, so a Zacks-scored beat is closer to "beat the guide" — if we are
   scored on Zacks, this adjustment gets *bigger*, not smaller.

5. **Bet the revenue line harder than the EPS line.** Revenue consensus error is ~1.9% vs ~7% for EPS; StarMine's
   directional hit rate is higher on revenue (78% vs 70%); revenue has no SBC/restructuring/MTM definitional traps.
   Build revenue bottom-up from KPI drivers (XBRL + transcripts) and derive EPS through an explicit margin walk and
   share count, rather than forecasting EPS directly.

6. **Pin down the EPS *definition* and the *snapshot* before anything else — this is the highest-variance risk.**
   Get in writing on the day: **which vendor's consensus, which EPS definition, and as of what timestamp.** The Q2 2026
   Alphabet/Amazon case (FactSet +29.2% vs LSEG +8.4%) and the NVDA case (Zacks $1.70 vs MarketBeat $1.76 on an actual
   of $1.87) show vendor choice alone is worth 3–4pp of surprise. Then derive the basis empirically in code: for the
   last 8 quarters, diff the vendor's reported "actual EPS" against GAAP diluted EPS from XBRL and learn the company's
   standing adjustment. **A model that nails operating performance and reports GAAP when the vendor scores adjusted
   will lose to a much dumber model that got the basis right.** And remember the benchmark is partly endogenous:
   I/B/E/S drops optimistic estimates ~10× more often when the drop enables a beat (§2.2).

7. **Data plan, concretely — three free sources, three different vendors, and their disagreement is itself signal.**
   All verified working by direct fetch on 15 Aug 2026:
   - **Alpha Vantage `EARNINGS_ESTIMATES`** (free key) — **the only free source with QUARTERLY REVENUE consensus**, and
     it ships `eps_estimate_average_{7,30,60,90}_days_ago` plus 7/30-day revision counts, i.e. our staleness and
     momentum features for free. **Build the primary pipeline on this.**
   - **`api.nasdaq.com/api/analyst/{T}/earnings-forecast`** (Zacks, keyless JSON) — quarterly EPS consensus, high/low,
     **estimate count**, and 4-week revision up/down. Plus `/api/company/{T}/earnings-surprise` for 4 quarters of
     actual-vs-consensus history → the firm-specific beat prior, free. **No revenue at any horizon.**
   - **`stockanalysis.com/stocks/{t}/forecast/`** (S&P Global MI, keyless, server-rendered) — **annual** EPS and revenue
     with counts and high/low (FY1 only; FY2+ is `"[PRO]"`), plus **price targets and the full rating split** — the two
     ingredients for the bundling-divergence signal (§3.5). Parse as a JS object literal, not JSON: the keys are
     unquoted.
   - **SEC XBRL APIs** for every deterministic fundamental (§6.5).
   Yahoo (404/503), TipRanks (403) and WSJ (401) are blocked to bots — do not build on them.
   **Cross-vendor disagreement is a first-class feature: log Zacks-vs-S&P-vs-AlphaVantage spread per name. Wide
   disagreement means the "consensus" we are scored against is itself uncertain, and we should not be bold.**

8. **Pick the company deliberately — it is half the game.** In priority order:
   - **Reports inside the scoring window.** ~6 weeks from 16 Aug 2026 means late-Aug-to-late-Sept off-cycle reporters
     with Aug/Sept fiscal quarter-ends. Verified dates: **Oracle ~14 Sep**, **Micron 23 Sep**, **Costco 24 Sep**,
     **Nike 24 Sep**, **Accenture late Sep**; also Adobe, FedEx, Lennar, Darden, Paychex, AutoZone, General Mills,
     CarMax, Cintas. (https://investingcalendar.com/sector/technology/earnings ,
     https://www.wallstreethorizon.com/micron-earnings-calendar ,
     https://investor.costco.com/events-and-presentations/events/event-details/2026/Q4-2026-Earnings-Call/default.aspx)
   - **High EPS base.** Errors are ~constant in cents, so a ~$6.50-EPS Costco is enormously more forgiving on
     percentage error than a ~$0.44-EPS Nike (whose last five prints surprised by +66.7%, +16.7%, +43.2%, +81.5%,
     +80.0% — a coin flip on any %-based metric).
   - **Publicly observable drivers.** Costco publishes **monthly comparable sales**, so by the time it reports fiscal Q4
     most of the revenue is already public — a legitimate, replicable edge over a model that only reads the last 10-Q.
     Similar: airlines (TSA throughput, monthly traffic), autos (monthly deliveries), homebuilders (orders + Census
     starts), energy (EIA weekly + strip).
   - **Adequate coverage.** Below ~5 estimates the consensus is itself noise (§2.5) and "beating" it is luck.
   - **Avoid** anything turning on unobservable channel data (§6.1) or a single one-off item.

9. **Two cheap signals almost nobody codes.**
   (a) **Bundling divergence** — EPS estimate flat while price targets/ratings drift up is a documented beat signal;
   adjusting for it removes 66% of the kink at zero (§3.5). Both inputs are free from StockAnalysis + Nasdaq.
   (b) **Dispersion as a regime switch** — dispersion of 1–2 cents means the modal outcome is consensus +1 cent and we
   should not be bold (P(0/+1c surprise) rises 14% → 35% as dispersion falls); wide dispersion is the licence to take a
   real position (§4.2).
   Bonus (c): **CAF anchoring** — `(firm forecast EPS − industry-median forecast EPS)/|industry-median|`. High CAF ⇒
   analysts too pessimistic ⇒ more positive surprises. Historically worth 9.12%/year. Computable from the free sources
   above plus a peer list.

10. **Build the eval harness with three baselines and an honesty rule.** Backtest the last 8–12 quarters for ~30
    candidate companies, scoring: (i) `consensus` verbatim, (ii) `consensus × (1 + sector prior)` from §3.2,
    (iii) `consensus + firm-specific median historical surprise`. **If the LLM agent cannot beat baseline (iii), ship
    baseline (iii).** It will beat consensus on roughly 75–80% of names and takes an hour — build it in hour one so we
    always have a working submission. Honesty rules: **report F1 and not just accuracy** (78% base rate makes accuracy
    meaningless, §6.4); **treat any pre-training-cutoff quarter as contaminated** and report post-cutoff results
    separately (§6.3); **version and timestamp every consensus pull**, because even I/B/E/S disagrees with its own
    earlier vintages by enough to flip meet-or-beat classifications (§2.3).

11. **Do not cite the withdrawn "LLMs beat analysts" paper.** Kim/Muhn/Nikolaev is withdrawn by its own authors, and
    the best available replication (Li et al.) finds GPT-4 Turbo at **47.7–49.3% directional vs 71.1% for analysts**.
    Our pitch should be "we systematically exploit four *documented, cited* biases in how consensus is constructed,"
    not "the LLM is smarter than analysts." The first claim is defensible under questioning; the second is not.

12. **The demo visual that is also substantively true:** the **walk-down chart** — consensus for the quarter drifting
    down over time (or, this cycle, drifting *up*), the actual printing above it — with our estimate above consensus
    and the delta decomposed into named, sourced components (recency correction, guidance position, firm beat prior,
    sector prior, streak, anchoring, driver-model delta). One picture explains the whole thesis, and every number in it
    is defensible from this document.
