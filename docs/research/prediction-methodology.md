# Forecasting Methodology: from ingested data to a number that beats consensus

Research doc for "Agents vs Wall Street" (16 Aug 2026). Everything here is sourced; numbers are quoted
from the cited studies. Scored 50% on accuracy vs actuals **and** consensus ~6 weeks later.

---

## 0. The five findings that matter most

| # | Finding | Number | Source |
|---|---|---|---|
| 1 | Actual EPS lands at the **upper bound** of management's guidance range, not the midpoint. Vendors (incl. FactSet) compare consensus to the **midpoint** — so the bias is sitting there unexploited. | Median `ACT_DIS` = **1.00** (1.00 = upper bound, 0 = midpoint); mean 1.20 for 2002–2010; 45.7% of actuals land **above** the high end | [Ciconte, Kirk & Tucker, *Rev. Acc. Stud.* 19(2) 628–660](https://link.springer.com/article/10.1007/s11142-013-9259-2) |
| 2 | A retrieval-augmented LLM alone **loses** to the crowd; LLM **blended with** the crowd beats the crowd. | LLM system Brier .179, crowd .149, **system+crowd .146** — best in every subgroup | [Halawi et al., NeurIPS 2024](https://arxiv.org/html/2402.18563v1) |
| 3 | Consensus EPS basis is **decided per company by whichever basis the majority of contributing analysts use** — it is NOT uniformly non-GAAP. Getting this wrong is a 100%+ error. | Q2'26: GOOGL actual $9.11 vs est $2.88; AMZN $5.75 vs $1.82 — both GAAP-basis consensus. Index surprise 29.2% → **10.9% excluding just those two**. | [FactSet, 7 Aug 2026](https://insight.factset.com/sp-500-earnings-season-update-august-7-2026) |
| 4 | Analysts systematically **do not model predictable buybacks** into share count → consensus EPS is structurally too low for heavy repurchasers. | Bulge-bracket analyst, verbatim: *"to forecast shares outstanding we just take the fully diluted number from the prior quarter and push the number forward"* → *"will lead to consistently pessimistic EPS estimates for firms repurchasing shares"* | [Kaplan et al., UWAC 2022](https://www.utah-wac.org/2022/Papers/kaplan_UWAC.pdf) |
| 5 | Decomposition helps only under **high uncertainty about an extreme quantity**; on well-anchored quantities it *hurts badly*. | 42% error reduction under high uncertainty across 15 tests; but **+458% median error** on non-extreme problems | [MacGregor & Armstrong, *IJF* 10(4) 495–506](https://marketing.wharton.upenn.edu/wp-content/uploads/2022/02/140-JSA-Judgmental-Decomposition-When-Does-It-Work.pdf) |

---

## 1. Calibrating the target: what "beating consensus" actually requires

Baseline stats you must beat, from [FactSet Earnings Insight](https://www.factset.com/earningsinsight)
(7 Aug 2026 update, Q2 2026 season, 88% of S&P 500 reported):

| Metric | Q2 2026 | 5-yr avg | 10-yr avg |
|---|---|---|---|
| % companies with EPS above consensus | 86% | 78% | 76% |
| Aggregate EPS surprise | +29.2% (**+10.9% ex-GOOGL/AMZN**) | +7.0% | +7.4% |
| % companies with revenue above consensus | 76% | 70% | 68% |
| Aggregate revenue surprise | +3.2% | +1.9% | +1.6% |

Earlier in the same season ([17 Jul 2026](https://insight.factset.com/sp-500-earnings-season-update-july-17-2026)):
88% EPS beat / +16.4% surprise; 85% revenue beat / +3.8% surprise.

A cross-check from [DWS's S&P 500 EPS Tracker](https://download.dws.com/download/asset/inline/49221af1-0106-4b46-a4cd-2bcae5fec944?tenant=Dwscom)
measuring against **consensus as of fiscal quarter-end** (not the drifting mean): Q3'25 = 78% EPS beat,
aggregate surprise **+5.9%**; 55% sales beat, +2.5%. Historic average EPS beat **+3.5%** (2011–2025, ex 2020–21).

**Three operational consequences:**

1. **Consensus is a biased estimator with a known sign.** The median company beats. A forecast that is
   *unconditionally* equal to consensus loses the accuracy tiebreak to consensus, and a forecast that
   sits *below* consensus is fighting a ~78/22 prior. Default posture: at or modestly above consensus.
2. **The size of the edge you need is small.** Median EPS beat is low single-digit percent; median revenue
   beat is ~1.5–2%. You do not need a brilliant call — you need to be systematically 1–3% above consensus
   on revenue and ~3–5% above on EPS, and to *not* blow up on the tails.
3. **The consensus snapshot matters enormously.** FactSet's mean estimate drifts up to the report date;
   quarter-end consensus is staler and easier to beat. Log which snapshot the hackathon scores against and
   pin your comparison to that same vintage.

**Revenue is the harder target, EPS is the softer one.** 70% revenue beat vs 78% EPS beat, and a 1.9%
vs 7.0% surprise magnitude. Revenue is close to un-manageable; EPS is manageable via buybacks,
opex timing, tax discretes and non-GAAP definitional choices. Expect to place higher above consensus on
EPS than on revenue.

---

## 2. Driver-based decomposition

### 2.1 When decomposition beats direct extrapolation — the evidence is *narrow*

[MacGregor & Armstrong (1994)](https://marketing.wharton.upenn.edu/wp-content/uploads/2022/02/140-JSA-Judgmental-Decomposition-When-Does-It-Work.pdf)
is the cleanest result in the literature and it is a warning, not an endorsement:

- On **9 "extreme value, high uncertainty"** problems, decomposition reduced median error ratio by a factor
  of 68.3 on average (MacGregor et al. subset: global error ratio 99.3 → decomposed 3.0, a 96.3× reduction;
  Armstrong et al. subset: 18.0 → 5.7).
- In their own experiment (10 problems, 280 subjects, 1,078 estimates): on the 6 extreme problems, median
  error reduced by a factor of **19.78** (p < 0.001).
- On **non-extreme, low-uncertainty** problems: decomposition **increased** median error by **458%**
  (p < 0.05). In the earlier reanalysis, decomposed error was 50% higher than global.
- [MacGregor (2001), *Principles of Forecasting* ch.6](https://link.springer.com/chapter/10.1007/978-0-306-47630-3_6):
  summarising 3 studies / 15 tests, decomposition gave a **42% error reduction under high uncertainty**;
  and multiplicative decomposition is *"especially sensitive to correlated errors in component values."*
- Armstrong's [evidence-based summary](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/FindingsfromEvidence-BasedForecasting.pdf)
  puts well-established error reductions at: **combining forecasts 12%**, causal models 10%, judgmental
  bootstrapping 6%, damped trend 5%.

**The decision rule falls out directly.** Next-quarter revenue for a large-cap is *not* an extreme,
high-uncertainty quantity — you know last year's same quarter to the dollar and the number moves ±15%.
That is exactly the regime where MacGregor & Armstrong found decomposition *destroys* accuracy through
error compounding across multiplied components.

> **Use decomposition as a cross-check and an explanation generator, not as the primary estimator** —
> *unless* the identity closes on disclosed data (see 2.2), in which case it is not really judgmental
> decomposition at all, it is arithmetic on observed inputs.

Corollary on component count: because multiplicative decomposition compounds correlated component errors,
keep the driver tree to **2–3 multiplied terms maximum**. `DAU × ad_load × CPM × FX × mix` is five
correlated guesses; `impressions_growth × price_per_ad_growth` is two disclosed numbers.

### 2.2 The driver identities that actually close

**Ad-based (Meta, and structurally the same at Snap/Pinterest/Reddit).** Meta discloses exactly two
drivers, and the identity closes to within a rounding point:

| Quarter | Ad impressions YoY | Avg price per ad YoY | Implied (1+i)(1+p)−1 | Reported ad revenue YoY |
|---|---|---|---|---|
| Q1 2026 | +19% | +12% | **+33.3%** | **+33%** |
| Q2 2026 | +14% | +12% | **+27.7%** | **+27%** |

Sources: [Meta Q1 2026 release](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/),
[Q2 2026 release](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Second-Quarter-2026-Results/default.aspx).
Meta also gives the regional split (Q1'26 impressions: APAC +23%, Europe +17%, RoW +17%, US&C +13%;
price/ad: Europe +19%, RoW +18%, US&C +14%, APAC +5%) — [Investing.com deck summary](https://ca.investing.com/news/company-news/meta-q1-2026-slides-33-revenue-surge-driven-by-ad-momentum-93CH-4597444).
This is the *ideal* decomposition case: both drivers are disclosed, mean-reverting, and the product
reconciles to reported revenue.

**SaaS/subscription — cRPO is the strongest single leading indicator in the whole exercise.**
Current remaining performance obligation is ASC 606-mandated, auditable, and *guided* by several companies.

- Workday Q2 FY26: cRPO $7.91B, **+16.4%**; management guided Q3 subscription revenue $2.235B (+14%) and
  Q3 cRPO +15–16% ([prepared remarks](https://investor.workday.com/files/doc_financials/2026/q2/workday-fiscal-2026-second-quarter-prepared-remarks.pdf)).
- Workday Q1 FY27: cRPO $8.806B **+15.5%**, total RPO $27.294B +10.9%, subscription revenue +14.3% —
  a 200bp cRPO-over-revenue gap; and a 460bp cRPO-over-RPO gap flagging shortening contract durations
  ([Pacer AI](https://getpacerai.com/blog/what-is-current-performance-obligation/)).
- Salesforce Q1 FY27: cRPO $33.6B +14% (+13% CC); **guides next-quarter cRPO growth ~14%** alongside
  revenue $11.27–11.35B ([IR](https://investor.salesforce.com/financials/quarterly-results/)).
- Conversion rule of thumb: **cRPO converts to GAAP revenue at ~90–100% within 12 months**; cRPO leads
  revenue by **2–3 quarters** ([saasdb](https://saasdb.app/learn/financials/rpo-and-backlog/),
  [tapebrief](https://tapebrief.com/blog/reading-deferred-revenue)).
- Workday, ServiceNow and Atlassian **do not disclose ARR at all** — cRPO is the only auditable forward look.
- Caveat: for consumption models (Snowflake, Datadog) RPO is a credit commitment, not usage — pair with NRR
  and management's consumption commentary.

**Retail / restaurants.** `Revenue = comp-base revenue × (1 + comp) + new-unit contribution`, and
`comp ≈ traffic + ticket`, `ticket = price × mix × UPT`. Starbucks Q3 FY26 discloses it exactly this way:
global comps +7.9% = transactions +4.2% + ticket +3.5%; US +7.9% = +4.2% + 3.6%; NA net revenue +7% on
+8.1% comps with store count −2%; 175 net new stores to 41,304
([SBUX release](https://investor.starbucks.com/news/financial-releases/news-details/2026/Starbucks-Reports-Q3-Fiscal-Year-2026-Results/default.aspx)).
Diagnostic grid ([tapebrief](https://tapebrief.com/blog/same-store-sales-decoded)): traffic+/ticket+ = clean;
traffic+/ticket− = buying volume with promo; **traffic−/ticket+ = the dangerous one** (headline comp holds
while the base erodes, precedes guidance cuts); traffic−/ticket− = deterioration. Always look at the
**two- and four-year stack**, not the single-year comp.

**Hardware/semis.** `Units × ASP`, plus channel inventory (sell-in vs sell-through) and supply constraint.
Apple's Sep-Q 2026 guide is a live example of a *supply*-bound quarter, not a demand-bound one: revenue
guided +9–11% with management explicitly attributing the ~500bp deceleration to (a) a **2.5pt sequential FX
headwind** and (b) supply constraints on advanced nodes hitting iPhone/Mac/iPad — Cook: *"it's a demand
forecast issue"*, iPhone +22% and Mac +29% in the June quarter
([transcript](https://www.fool.com/earnings/call-transcripts/2026/08/07/apple-aapl-q3-2026-earnings-call-transcript/)).
Note that in supply-bound quarters the units driver is capped by capacity, not demand — bounded upside.

**Marketplaces/fintech:** `GMV or TPV × take rate`. **Energy:** `volume × realised price`, plus hedges.
**Consumer subscription:** `paid net adds × ARPU`, with price-increase timing and regional mix.

### 2.3 How pros structure the quarterly model

The sell-side quarterly build is: revenue by segment/geography → gross margin → opex lines →
operating income → below-the-line (interest, OI&E, FX remeasurement, equity method, minority interest) →
pre-tax → tax at guided/normalised ETR → net income → **÷ diluted weighted-average shares** → EPS.

For guiding companies, management hands you nearly the whole stack. Apple's Sep-Q 2026 guidance is the
canonical example — revenue growth range, segment colour, gross margin range, opex range, OI&E, and tax rate:

> revenue +9–11% YoY; gross margin 47–48% (incl. ~1pt tariff-refund benefit); opex $19.1–19.4B;
> OI&E ~$350M (ex mark-to-market on minority investments); **tax rate ~16.5%**
> — [Apple Q3 FY26 call](https://www.fool.com/earnings/call-transcripts/2026/08/07/apple-aapl-q3-2026-earnings-call-transcript/)

Every line except share count is guided. For such companies the forecasting problem collapses entirely
into "where in/vs the range" (§3) plus a share-count estimate (§8).

**Company-compiled consensus.** Many companies publish their own analyst consensus on the IR site
(Shell via Vara Research, GSK, Centrica, Equinor, Legal & General). It is often *better* than vendor
consensus because the company polices contributor coverage and line-item definitions
([Centrica](https://www.centrica.com/investors/company-compiled-consensus/),
[GSK](https://www.gsk.com/en-gb/investors/analyst-consensus/),
[Shell](https://www.shell.com/investors/results-and-reporting/consensus-estimates.html)).
Roughly **40% of FTSE 100/250** publish it; only ~15% include cash flow/net debt
([IR-connect](https://ir-connect.co.uk/2021/02/11/debunking-those-excuses-for-not-publishing-analyst-consensus/)).
Cheap tool: check the IR site for a "consensus" page before trusting a scraped vendor number.

---

## 3. Guidance-anchored forecasting — the single highest-value trick

### 3.1 The core result: the upper bound, not the midpoint

[Ciconte, Kirk & Tucker (2014)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2061440), 30,106
management **quarterly** EPS range forecasts, 1996–2010, First Call CIG + IBES actuals.

Define `ACT_DIS = (ACTUAL − Midpoint) / (0.5 × (High − Low))`. So **0 = midpoint, 1 = upper bound, 2 = one
half-width above the upper bound.**

**Distribution of where actuals land (Table 2):**

| Period | < Low | Low–Mid | = Mid | Mid–High | **> High** | ACT_DIS mean | ACT_DIS median |
|---|---|---|---|---|---|---|---|
| 1996–2001 (n=5,300) | 15.4% | 23.2% | 11.6% | 28.5% | 21.5% | −0.37 | 0.00 |
| **2002–2010 (n=24,806)** | 13.1% | 10.9% | 6.6% | 23.7% | **45.7%** | **+1.20** | **+1.00** |
| Full sample | 13.5% | 13.0% | 7.5% | 24.6% | 41.4% | +0.93 | +1.00 |

The regime shifted at Reg FD. In 2002–2010 the **median outcome is exactly the upper bound**, and the mean
is *above* it. **76.0% of quarters land at or above the midpoint. 45.7% land strictly above the high end.**
Year-by-year the median ACT_DIS climbs from 1.00 (2002–2008) to **2.00 (2009 and 2010)**.

**Use the LAST guidance, not the first (Table 3, 2002–2010, 3,638 firm-quarters with multiple forecasts):**

| Forecast | < Low | Low–Mid | = Mid | Mid–High | > High | ACT_DIS mean | median | Horizon (days) | Range width ($) |
|---|---|---|---|---|---|---|---|---|---|
| **First** | **31.6%** | 8.8% | 3.8% | 13.4% | 42.4% | +0.06 | 1.00 | 112.2 | 0.044 |
| **Last** | 6.5% | 12.3% | 8.2% | 32.3% | **40.8%** | **+1.295** | 1.00 | 46.6 | 0.035 |

The **first** guidance of a quarter has a fat left tail (31.6% below the low end) — it is issued ~112 days
out and gets revised. The **last** guidance (issued ~47 days out, range 20% narrower) has only a 6.5% left
tail and a mean 1.3 half-widths above the midpoint. **Always anchor on the most recent guidance.**

**Cross-sectional modifiers (Table 4, 2002–2010):**

| Cut | > High | ACT_DIS mean | ACT_DIS median |
|---|---|---|---|
| Large firms (top-third mkt cap) | **50.0%** | 1.55 | 1.09 |
| Small firms | 40.2% | 0.71 | 1.00 |
| High growth (top-third M/B) | **51.5%** | 1.92 | 1.40 |
| Low growth | 39.4% | 0.39 | 1.00 |

Large-cap and high-growth firms sandbag *harder*. Since the hackathon target is almost certainly a
well-covered large-cap, use the large/high-growth calibration, not the pooled one.

**Two critical caveats.** (a) The sample ends in 2010, and 2009–2010 are post-crisis outliers (median
ACT_DIS 2.00) that inflate the pooled mean. (b) The paper notes that in recent times managers guide
**street (non-GAAP) earnings, not GAAP** — the strategic behaviour is motivated by beating *street*
expectations. So this bias applies to the non-GAAP line.

### 3.2 The vendor convention makes the bias exploitable

Ciconte et al. quote a WSJ piece: *"Where companies have issued a range of earnings expectations,
Fac[t]Set uses the midpoint of the guidance range for comparison with the Wall Street consensus."*
And they show **analysts barely unravel the bias**: their `AF_DIS` measure (analyst consensus position
in the range, same scale) sits near **0** while `ACT_DIS` sits near **1** in the later period. Investors
partially unravel it — the market treats the *upper bound* as management's expectation — but the
published consensus does not.

That is the whole edge: **the bias is public, stable, and left in the consensus number.**

### 3.3 Corroboration from a manager survey

[Hribar et al., survey of 357 public-company CFOs/IROs, 2021](https://clsbluesky.law.columbia.edu/2022/10/17/how-corporate-managers-think-about-forward-looking-guidance/)
(published in [*JAE* 2024](https://www.sciencedirect.com/science/article/abs/pii/S0165410124000612)):

- Respondents say they *typically communicate a lower future performance number than their private
  expectation* — guidance is deliberately conservative, to leave room and to induce beatable sell-side
  forecasts.
- Managers are **~9× as likely** to say their internal expectation is **above** rather than below the
  midpoint of their own range.
- **90%** say they are at least 70% confident results will meet their guidance. Historically, the firms in
  the sample met their **initial** guidance only **31%** of the time
  ([Iowa/Tippie](https://tippie.uiowa.edu/news/2023/11/misplaced-confidence),
  [Bloomberg](https://www.bloomberg.com/news/articles/2023-05-23/company-earnings-guidance-is-wrong-about-70-of-the-time)).

That last pair is the key nuance: *initial* annual guidance is nearly useless (31% hit rate); the *latest*
quarterly guidance is highly informative and biased low. Weight accordingly.

### 3.4 Chronic lowballers are identifiable and persistent

[*Journal of Corporate Finance* (2023), "Does lowball guidance work?"](https://www.sciencedirect.com/science/article/pii/S0890838923000586),
S&P 1500, 2001–2017. Definition: beat own EPS guidance **midpoint** by **≥ $0.05 for ≥ 4 consecutive quarters**.

- **329 of 2,953 firms (11.1%)** qualify as lowball firms.
- Named examples: **Apple, Netflix, Qualcomm, LinkedIn, Target, Marriott, Procter & Gamble, General Motors.**
- Episode duration: **median 6 quarters, mean 7–8**; ~25% last only 4 quarters, ~10% last >3 years.
- **~1/3 of lowball firms restart** a new episode after ending one.
- Ending mechanics (293 of 329 eventually stopped): 74 stopped guiding, 117 missed guidance, 102 shrank to
  <$0.05 beats.
- Predictors of lowballing: sales growth, earnings growth, **earnings volatility** (marginal effect 55.9%),
  and transient institutional ownership.

**Directly implementable:** compute the firm's own 8-quarter `ACT_DIS` history. If median ≥ 1, treat the
upper bound as the central estimate. If the firm is in a >6-quarter lowball streak, apply a **regime-break
haircut** — the base rate says the streak has a meaningful chance of terminating.

### 3.5 Companies actively guide *down* to protect a beat streak

[Kross, Ro & Suk, *JAE* 2011](https://www.sciencedirect.com/science/article/abs/pii/S0165410110000297),
First Call 1996–2008: probability a firm issues a management forecast rises from **14%** (no meet-or-beat
string) to **45%** (12-quarter MBE string), and the incidence of **bad-news** forecasts rises
disproportionately. Analysts partially discount this — revisions following bad-news forecasts from
consistent-MBE firms are **dampened**.

Implication: for a long-streak firm, a *guidance cut* is weak evidence of deterioration and strong evidence
of expectations management. Do not treat guide-downs from habitual beaters at face value.

---

## 4. Company-specific surprise persistence

### 4.1 The time-series fact

[Bernard & Thomas (1990), *JAE*](https://www.sciencedirect.com/science/article/abs/pii/016541019090008R):
autocorrelations of **seasonally-differenced** quarterly earnings (i.e. `ΔE_t = E_t − E_{t−4}`),
firm-level, 1974–1986, firms with ≥10 quarterly observations:

| Lag | 1 | 2 | 3 | **4** |
|---|---|---|---|---|
| Bernard & Thomas (1990) | **+0.34** | **+0.19** | **+0.06** | **−0.24** |
| [Lewellen replication](https://web.mit.edu/lewellen/www/Documents/Earnings.pdf), firm-level | +0.34 | +0.18 | +0.05 | **−0.29** (all \|t\| > 5) |
| Lewellen, market-level (dE/B-agg) | +0.70 | +0.55 | +0.30 | +0.03 |

**The lag-4 sign flip is the single most under-used fact here.** A positive shock this quarter predicts
positive-but-decaying shocks for three quarters and then a **partial reversal in the fourth**. Naively
averaging the last four surprises therefore *cancels out* real signal. Firm earnings contain a transitory
idiosyncratic component that diversifies away at the index level (hence market-level autocorrelations are
much higher).

### 4.2 The surprise-streak fact

[MSCI Research](https://www.msci.com/research-and-insights/blog-post/should-we-be-surprised-by-earnings-surprises),
IBES + MSCI USA IMI/Large Cap, Q1 2002 – Q3 2018:

- Companies that beat (or missed) last quarter **more often** surprise in the same direction this quarter.
- The likelihood of same-direction continuation **increases with streak length**.
- The frequency of positive surprises is **higher in the US than elsewhere, and highest among US large caps.**
- Market reaction is **larger when a streak ends** — a positive surprise following a negative surprise gets
  more than **twice** the residual return of two consecutive positive surprises.

[Loh & Warachka, *Management Science* 58(7) 1305–1321 (2012)](https://ideas.repec.org/a/inm/ormnsc/v58y2012i7p1305-1321.html):
PEAD is strong and significant when a surprise **extends** a streak, and **negligible** when a streak
terminates; **streaks explain about half of PEAD** in their sample.

Practitioner-side figures (weaker sourcing, treat as directional): ~65% probability of beating again after
a +4% beat, ~60% of missing again after a −3% miss
([Pomegra](https://pomegra.io/learn/library/track-b-stock-market-core/earnings/chapter-09-revisions-and-surprise/surprise-history-as-a-signal));
78% of firms with 8+ consecutive beats beat again, 82% at 12+ consecutive beats
([BigEarnings](https://bigearnings.ai/blog/consecutive-earnings-beats-winning-streak)). Also from that
source: median 1-day move on the 2nd consecutive beat +2.8% decaying to +0.8% by the 10th, and −6.3% when
an 8+ streak breaks (vs −3.1% for an unstreaked miss) — the market prices the expected beat.

Peer clustering is real and exploitable: [ExtractAlpha](https://extractalpha.com/2023/03/08/quants-how-to-improve-earnings-forecasts-with-unique-alt-datasets/)
find that in a regression of current surprise on past **peer** surprises, peers defined by **overlapping
analyst coverage dominate industry-classification peers**. Also: firms that miss tend to announce **late,
near weekends/holidays, or on high-news-volume days**, and high cross-sectional estimate dispersion predicts
misses. Both are cheap features.

### 4.3 How many past quarters?

Two different windows for two different quantities:

| Quantity | Window | Rationale |
|---|---|---|
| **Guidance-bias / management style** (`ACT_DIS` median, lowball flag) | **8 quarters** | Lowball episodes have median duration 6 and mean 7–8 quarters ([JCF 2023](https://www.sciencedirect.com/science/article/pii/S0890838923000586)); 8 captures a full style regime without averaging across a regime break. |
| **Surprise momentum** (residual beat vs consensus) | **3 quarters, decaying weights ≈ 0.34 / 0.19 / 0.06**, and **explicitly do not add lag 4** (its coefficient is −0.24) | Bernard & Thomas autocorrelation structure. |

Never use a flat 4-quarter or 8-quarter mean of surprises: it mixes the +0.34 and −0.24 lags and washes
out the signal.

---

## 5. Seasonality and the mechanical baseline

### 5.1 The model

The standard benchmark is the **seasonal random walk with drift** (Foster 1977 Model 2):

```
E[Rev_q] = Rev_{q−4} + δ            where δ = mean of (Rev_{q−4k} − Rev_{q−4k−4}) over the training window
```

equivalently in growth space `E[g_q] = mean(g_{q−1..q−k})` where `g = YoY growth`.
[Foster, Olsen & Shevlin (1984)](https://iangow.github.io/far_book/pead.html) found the seasonal random walk
performs **as well as** more complex time-series models. Bernard & Thomas's whole thesis is that prices
*"fail to reflect the extent to which each firm's earnings series differs from a seasonal random walk"* —
i.e. the SRW is the market's implicit model, and the deviations from it are the alpha.

Refinement using the autocorrelation structure (the "Foster/Bernard-Thomas correction"):

```
ΔE_q = 0.34·ΔE_{q−1} + 0.19·ΔE_{q−2} + 0.06·ΔE_{q−3} − 0.24·ΔE_{q−4}
E[E_q] = E_{q−4} + ΔE_q
```

This is ~8 lines of TypeScript and is a genuinely better mechanical baseline than a plain SRW.

### 5.2 YoY vs QoQ — which framing

| | Revenue | EPS |
|---|---|---|
| **Recommended framing** | **YoY growth rate** (seasonal difference), with a **QoQ sequential build cross-check** | **YoY, always**; margin × revenue is more robust than direct EPS extrapolation |
| Why | YoY removes seasonality by construction. QoQ requires an explicit seasonal factor which is unstable when the seasonal pattern shifts (product cycles, calendar shifts, 53rd weeks). | EPS is a ratio with a levered numerator; QoQ EPS is dominated by margin and tax noise. Seasonally-differenced *earnings* is precisely the series Bernard & Thomas showed to be autocorrelated. |
| When QoQ wins | Companies that guide sequentially (Apple guides Sep-Q *relative to* Jun-Q: *"we get pretty close to the June overall total company growth rate"*); consumption businesses with no seasonality; and any quarter where the year-ago comp is contaminated (extra week, divestiture, one-off). | Rarely. Use QoQ only to sanity-check the implied sequential margin path. |

**Robustness ranking, revenue:** YoY growth > QoQ with seasonal factors > level extrapolation.
**Robustness ranking, EPS:** `revenue_forecast × margin_forecast − BTL, ÷ shares` > YoY EPS growth >
direct EPS level. Never forecast EPS as a raw level.

### 5.3 Analysts vs time-series: know when the mechanical model is competitive

- [Fried & Givoly (1982)](https://care-mendoza.nd.edu/assets/152185/bradshawpaper.pdf): mean prediction
  errors **16.4% (analysts) vs 19.3% (modified submartingale RW) vs 20.3% (RW)** — analysts win, but by less
  than folklore suggests.
- [Bradshaw, Drake, Myers & Myers](https://care-mendoza.nd.edu/assets/152185/bradshawpaper.pdf): analysts'
  superiority is *"economically small"* at short horizons, and **random walk forecasts are more accurate
  than analysts' at longer horizons** (~half of two-year-ahead horizons). Analyst superiority concentrates
  in firms with **small** EPS changes; it fades when analysts forecast **large** changes. Untabulated:
  plain RW beats RW-with-drift.

**Read-through:** at the 1-quarter horizon with guidance available, analysts (consensus) are hard to beat
head-on. Your edge comes from *correcting a known bias in consensus*, not from out-forecasting it from
scratch. This is the strongest argument for anchor-and-adjust over free-form estimation.

---

## 6. Statistical prior + LLM adjustment: the anchor-and-adjust pattern

### 6.1 Evidence that bounded adjustment beats free-form

**Judgmental-adjustment literature.** [Fildes, Goodwin, Lawrence & Nikolopoulos (2009), *IJF*](https://www.sciencedirect.com/science/article/abs/pii/S0169207008001362)
studied four supply-chain companies:

- **>37%** of statistical forecasts were judgmentally adjusted (Fildes & Goodwin 2007; Fildes & Petropoulos 2015);
  only ~25% of forecasts rely exclusively on statistical methods.
- In **3 of 4** companies judgmental adjustment increased accuracy on average, **but**:
  - **larger adjustments produced greater average accuracy improvement**;
  - **small adjustments often damaged accuracy**;
  - **positive (upward) adjustments were much less likely to improve accuracy than negative ones, and were
    made in the wrong direction more frequently** — a clear optimism bias.
- Recommended remedies: restrict the opportunity to intervene, and **mechanically combine judgment with the
  statistical forecast** rather than letting judgment overwrite it.

Three concrete design rules fall out:
1. **Deadband.** Reject adjustments below a minimum magnitude — they are noise. (Do not apply a ±0.3%
   tweak; either the evidence supports a real move or leave the anchor alone.)
2. **Asymmetric bounds.** Allow a *wider* downward adjustment band than upward, because upward adjustments
   are the biased ones. (This fights, but does not eliminate, the §3 upward guidance bias — the guidance
   bias belongs in the *anchor*, not in the LLM's discretionary adjustment.)
3. **Mechanical combination.** Blend, don't overwrite.

**LLM analogue — the decisive result.** [Halawi, Zhang, Chen & Steinhardt, NeurIPS 2024](https://arxiv.org/html/2402.18563v1)
built a retrieval-augmented LLM forecasting system and evaluated on post-cutoff questions:

| Setting | System Brier | Crowd Brier | **System + crowd aggregate** |
|---|---|---|---|
| All questions | .179 | .149 | **.146** |
| Crowd uncertain (0.3–0.7) | .238 | .240 | **.233** |
| ≥5 relevant articles | .175 | .142 | **.140** |
| All 3 criteria met | **.240** | .247 | **.237** |

Ablations: base GPT-4 with **no retrieval** = .206 vs full system .179 (retrieval is worth ~.027 Brier).
Bare zero-shot models were mostly **at or worse than random (.25)**; best single model .208 vs crowd .149.

> **The blend of system and crowd is the best entry in every single row.** The LLM alone loses to the
> crowd; the LLM as an *adjustment on top of* the crowd wins.

The system also **outperforms the crowd specifically when the crowd is uncertain** (.199 vs .246 on the
0.3–0.7 band in the arXiv version) and **underperforms when the crowd is confident**. Translated to our
problem: the LLM's edge concentrates in high-estimate-dispersion, low-guidance-clarity situations. When
guidance is tight and dispersion is low, shrink hard toward consensus.

Corroboration on the direction of information flow: [Schoenegger, Tuminauskaite, Park, Bastos & Tetlock,
*Science Advances* (2024)](https://doi.org/10.1126/sciadv.adp1528) — showing GPT-4 and Claude 2 the
**median human forecast** improved their Brier scores by **17–28%** (GPT-4 .17→.14; Claude 2 .22→.15),
**but simply averaging human and machine forecasts was more accurate still.** The models under-updated
toward the human anchor and over-weighted their own view.

**Conclusion for our build:** do the arithmetic blend in code. Do not ask the model to "consider consensus
and produce a final number" — it will anchor insufficiently.

### 6.2 What the anchor should be

Candidate anchors, best first for a **guiding** company:

1. `guidance_upper_bound` (or `midpoint + 1.0 × half-width`), from the **most recent** guidance — §3.1.
2. Consensus.
3. Seasonal-RW-with-BT-correction — §5.1.

For a **non-guiding** company: consensus first, SRW+BT second.

Then blend: `anchor = w_g·guidance_implied + w_c·consensus + w_m·mechanical`, with weights conditioned on
guidance recency and estimate dispersion.

---

## 7. Ensembling

### 7.1 Why the median, and why independence matters more than cleverness

- **Simple median is a remarkably strong aggregator.** Schoenegger et al.: across a large aggregation
  literature *"a central takeaway being that a simple median is an unexpectedly powerful aggregation
  mechanism: one that works across a myriad of contexts."* In their 12-LLM ensemble, **only 3 of 12 models
  beat the model median**. The median also neutralised a systematic acquiescence bias present in the
  majority of individual models.
- **The forecast combination puzzle.** Optimised combination weights generally **fail to beat equal
  weighting** ([Wang & Hyndman, 50-year review](https://arxiv.org/pdf/2205.04216);
  [Solving the Forecast Combination Puzzle](https://arxiv.org/pdf/2308.05263)). Makridakis & Winkler (1983):
  more methods in a simple average → better accuracy *and lower variance of the result*. Practitioner
  consensus: **diminishing returns after 4–5 distinct methods**. Armstrong's meta-estimate for combining:
  **~12% error reduction**.
- **Independence is the binding constraint, not N.** [Da & Huang, *Management Science* (2020),
  "Harnessing the Wisdom of Crowds"](https://dl.acm.org/doi/10.1287/mnsc.2019.3294), run *with* Estimize:
  the more public information a contributor viewed before forecasting, the **more accurate their individual
  forecast** but the **less accurate the group consensus**, because useful private information stops
  entering. Randomised experiments confirmed causality. **Estimize switched to a blind platform in
  November 2015 as a result.**
- **Crowd size does help, but through independent information.** [Jame, Johnston, Markov & Wolfe,
  *JAR* (2016)](https://onlinelibrary.wiley.com/doi/10.1111/1475-679X.12121): combining Estimize with IBES
  beats IBES alone **57% of the time at 60 days, 60% at 30 days, 64% at 1 day** — and the average number of
  Estimize forecasts in the consensus rises from **1.83 (60d) to 5.86 (1d)** over the same span.
  Estimize consensus alone beats IBES **57%** of the time, **61%** for firms with a *diverse* following
  ([Bliss et al.](http://com.estimize.public.s3.amazonaws.com/papers/Barbara%20Bliss%20-%20University%20of%20San%20Diego%20-%20The%20Value%20of%20Crowdsourcing%20-%20Estimize%20-%20July.pdf)).
  Diversity, observable ex ante, is the driver.

### 7.2 Recommended ensemble design

```
N independent, BLIND agent runs          (no run sees another run's number; no run sees consensus)
      ↓  median
method-level estimate
      ↓  median across K distinct methods (K = 3–4: mechanical, guidance-anchored, LLM-driver, LLM-direct)
raw ensemble estimate
      ↓  arithmetic shrink toward consensus (in code, not in a prompt)
final forecast
```

- **N per method: 5–7.** Gains are steep to ~5 and flat after; Estimize's crowd went from 1.8 → 5.9
  contributors for its biggest accuracy gain. Beyond ~8 you are paying tokens for correlated samples,
  because runs from the same model with the same context are far less independent than 12 different models.
- **Diversity beats count.** Force independence structurally: vary the *evidence subset* each run sees
  (guidance-only / filings-only / transcript-only / news-only), vary temperature, and if budget allows vary
  the model family. Schoenegger et al.'s ensemble worked because it spanned 12 *different* models.
- **Aggregate with the median, not the mean.** Robust to the one run that hallucinates a 10× number, which
  will happen.
- **Do not show runs the consensus.** Da & Huang is unambiguous: public-anchor exposure improves the
  individual and degrades the aggregate. Blend with consensus *afterwards*, in code (Schoenegger et al.:
  averaging human + machine beat letting the model update on the human median).
- **Weighting:** start equal-weighted. The combination puzzle says learned weights rarely help, and with a
  one-day eval harness you have nowhere near enough data to fit them. If you must weight, weight by
  *inverse historical MAPE of each method on your backtest*, and shrink those weights halfway to equal.

---

## 8. EPS-specific mechanics

```
EPS = (Revenue × GrossMargin − Opex ± BelowTheLine) × (1 − ETR) ÷ DilutedWeightedAvgShares
```

Every term below is a documented way to have a good revenue forecast and a bad EPS forecast.

### 8.1 GAAP vs non-GAAP — get this right or nothing else matters

**The rule (FactSet, authoritative):** *"the majority of analysts providing EPS estimates for a company
will establish the basis used."* FactSet explicitly names **Alphabet, Amazon.com and Meta Platforms** as
companies whose consensus is on a **GAAP** basis, because the majority of contributing analysts submit GAAP
estimates ([FactSet Consensus Estimates DataFeed](https://insight.factset.com/resources/factset-consensus-estimates-datafeed);
also FactSet's Q2 2026 commentary). Default consensus uses a trailing **100-day** validation window,
extending to at most 150 days for unreported periods.

**What happens when you assume wrong** — Q2 2026, real:

| Company | Actual (GAAP) EPS | Consensus | Cause |
|---|---|---|---|
| Alphabet | **$9.11** | $2.88 | $98B of other income, mostly net unrealised gains on equity securities |
| Amazon | **$5.75** | $1.82 | $53.4B gain, primarily its Anthropic investment |

These two names took the **index-level** earnings surprise from **10.9% to 29.2%**
([FactSet, 7 Aug 2026](https://insight.factset.com/sp-500-earnings-season-update-august-7-2026)). If your
agent had forecast a "normalised" number for either name, it would have missed by ~200%.

**How to determine the basis for a given company (checklist, in order):**
1. Read the company's **own earnings release headline**. If the press-release headline metric is
   "Non-GAAP diluted EPS" / "Adjusted EPS" and guidance is given on that basis, consensus is almost
   certainly non-GAAP. Salesforce, for example, guides **both**: Q2 FY27 diluted EPS **GAAP $1.74–1.76**
   *and* **non-GAAP $3.25–3.27** — an $1.50 gap on a ~$3 number
   ([CRM IR](https://investor.salesforce.com/financials/quarterly-results/)).
2. Check whether a **non-GAAP reconciliation table** exists. Reg G / Item 10(e) of Reg S-K *requires* a
   reconciliation to the most directly comparable GAAP measure in the earnings release — so the table is
   machine-findable and gives you both numbers plus every adjustment line.
3. Check whether the company **guides EPS at all**, and on which basis. Whatever management guides is what
   analysts model. Apple guides revenue/GM/opex/OI&E/tax — implying GAAP EPS. Salesforce guides both.
4. Sanity-check the magnitude: if consensus EPS is far below the trailing GAAP EPS for a company with large
   amortisation or SBC, consensus is likely non-GAAP; if consensus tracks GAAP including investment gains
   (GOOGL/AMZN/META), it is GAAP.
5. If ambiguous, **forecast both and report the one matching the scored consensus basis**, with the other as
   a documented sensitivity.

**How big is the gap** ([Calcbench × Suffolk University annual studies](https://www.calcbench.com/blog/post/blogger3692334331784427297/Special-Report-Non-GAAP-Adjustments-in-2025)):

| Study year | # S&P 500 reporting non-GAAP NI/EPS | % adjusting **upward** | Avg non-GAAP − GAAP NI | As % of avg GAAP NI |
|---|---|---|---|---|
| 2025 | **361 (72%)** | 87% | $751M | **23%** |
| 2024 | 351 (71%) | 89% | $870M | ~30% |
| 2023 | 260 sampled | 86% | $698M | 29% (6.3 adjustments/company) |
| 2022 | 200 sampled | 83% | $1,095M | 38% |

Biggest adjustment categories by dollar value (2021 sample): **amortisation of intangibles 50.6%**,
**stock-based comp 16.1%**, restructuring 13.7%, M&A/divestiture 11.4%, tax adjustments **−11.0%**,
impairment 8.4%. Median non-GAAP − GAAP EPS gap roughly **$0.30 (2013) → $0.60 (2020)**, with **80%** of
firms reporting non-GAAP above GAAP ([Calcbench](https://www.calcbench.com/blog/post/654260670019305472/looking-at-the-gap-in-non-gaap-eps-numbers)).

**Revenue basis.** Revenue consensus is essentially always **GAAP revenue**. But guidance is frequently
given in **constant currency** or **organic** terms, and companies hand you the bridge in dollars — e.g.
Salesforce Q2 FY27: *"10%–11% Y/Y and 10% CC, $50M Y/Y FX"*; cRPO *"~14%, ~13% CC, $200M Y/Y FX."*
Convert CC guidance to reported using the disclosed FX dollar bridge, not your own FX model.

### 8.2 Diluted share count — the most exploitable structural bias

**The mechanics.** Diluted weighted-average shares = period-weighted basic shares + incremental shares from
options/warrants/RSUs under the **treasury stock method** (incremental = awards × (price − strike) ÷ price,
with assumed proceeds = exercise price + average unrecognised comp cost), plus if-converted shares for
convertibles. Crucially, **quarterly EPS uses that quarter's weighted average**, and year-to-date diluted
shares are the **average of the quarters' weighted-average incremental shares**, not an independently
computed full-year average ([PwC Viewpoint FSP 7.5](https://viewpoint.pwc.com/dt/us/en/pwc/accounting_guides/financial_statement_/financial_statement___18_US/chapter_7_earnings_p_US/75_diluted_eps_US.html)).

Weighting is why buybacks are under-modelled: shares bought back late in a quarter reduce the weighted
average for only part of the quarter, so the *EPS* effect lags the *share-count* effect by roughly a quarter.

**The bias.** [Kaplan et al. (2022)](https://www.utah-wac.org/2022/Papers/kaplan_UWAC.pdf) decomposed EPS
forecasts into street-earnings numerator and share-count denominator (IBES does not publish share forecasts,
so they bound them). Findings:

- Analysts' share forecasts are **less accurate than simple time-series models** of shares outstanding.
- Analysts nonetheless use the denominator to **herd EPS toward consensus** — share errors share the sign of
  street-earnings errors, reducing EPS dispersion.
- Analysts **fail to incorporate predictable variation in shares outstanding, such as past repurchases**,
  and this explains much of the meet-or-beat effect.
- Verbatim from a senior bulge-bracket analyst: *"to forecast shares outstanding we just take the fully
  diluted number from the prior quarter and push the number forward to next quarter... Some companies have
  a recurring buyback, but only a minority repurchase and cancel the shares."* The authors' conclusion:
  *"This forecasting method will lead to consistently pessimistic EPS estimates for firms repurchasing shares."*

**How to exploit it.** Forecast share count properly ([Wall Street Prep approach 3](https://www.wallstreetprep.com/knowledge/forecasting-companys-earnings-per-share-shares-outstanding/)):

```
basic_shares_next = latest_cover_page_basic_shares            (10-Q cover, NOT the income statement average)
                    + expected_issuance
                    − (expected_$_repurchase / expected_avg_price)
diluted_next      = basic_shares_next + (historical diluted − basic gap)
weighted_avg      ≈ 0.5 × (shares_begin + shares_end)          for a smooth buyback programme
```

Wall Street Prep's Apple illustration of why the cover page matters: cover-page basic shares 5,332M vs
income-statement weighted-average basic 5,471M — a **2.5%** gap, i.e. 2.5% of EPS, in one year.

Guardrails:
- **Model executed repurchases, not authorisations.** An authorisation is optionality; the 10-Q Item 2(c)
  "Issuer Purchases of Equity Securities" table is the receipt. (One source claims quantitative daily
  repurchase disclosure is now required — the 2023 SEC rule requiring this was challenged in court, so treat
  the 10-Q monthly table as the reliable source and verify before relying on daily data.)
- **Don't double-count.** If you model buybacks reducing the count, don't also apply an aggressive treasury-
  stock-method dilution assumption on the same shares.
- **SBC dilution runs the other way.** High-SBC companies grow the share count 2–4%/yr absent offsetting
  buybacks; a "flat share count" assumption silently overstates EPS.

### 8.3 Effective tax rate — the biggest single-line EPS blow-up risk

**The rule.** Under **ASU 2016-09**, all excess tax benefits and deficiencies from share-based compensation
flow through **income tax expense**, and — critically — they are **discrete items in the period they occur
and are explicitly EXCLUDED from the estimated annual effective tax rate** (ASC 740-270-30-4/30-12).
[Deloitte FAQ #15](https://dart.deloitte.com/USDART/home/publications/archive/deloitte-publications/heads-up/2016/frequently-asked-questions-about-asu-2016):
should you forecast excess tax benefits in the AETR? *"No."* KPMG's assessment: the ASU
*"increases the volatility in reported earnings"*, driven by **share-price changes and the timing of option
exercises and award vesting** ([KPMG Defining Issues 16-11](https://assets.kpmg.com/content/dam/kpmg/pdf/2016/04/Defining-Issues-O-1604-11.pdf)).
Academic confirmation: errors in analysts' implied ETR forecasts **significantly increased** for firms with
material ETR effects from ASU 2016-09 ([SSRN 3062091](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3062091)).
ASU 2016-09 also changes the *denominator*: excess tax benefits are excluded from treasury-stock-method
assumed proceeds, so fewer hypothetical shares are repurchased and dilution **increases**.

**Live example.** Meta Q1 2026: reported GAAP net income $26.8B / **$10.44 EPS**, *"flattered by an $8.03B
tax benefit (underlying $18.7B / $7.31 EPS)"*
([Q1 2026 call summary](https://vectorshift.ai/research/companies/meta-platforms/earnings/2026-q1)).
A **43%** EPS gap created entirely below the operating line.

**Guardrails:**
- Use **management's guided tax rate** when given (Apple: *"our tax rate to be around 16.5%"*). It is the
  single best ETR estimate and it is free.
- For calendar-Q1 with heavy RSU vesting and a stock that has risen sharply, expect a **downward** ETR
  discrete. For a stock that has fallen, expect a shortfall (upward ETR).
- **Never** extrapolate last quarter's reported ETR. Use guided AETR + explicit discrete adjustment.
- Flag ETR moves >300bp vs guidance as requiring an explicit justification.

### 8.4 Below-the-line and one-offs

- **Other income/expense** is where mark-to-market on equity investments lives — the GOOGL/AMZN Q2'26 blow-ups
  were *entirely* OI&E. Apple guides it explicitly and explicitly **excludes** the volatile part:
  *"We expect OIE to be around $350 million, excluding any potential impact from the mark to market of
  minority investments."* If a company holds large marketable equity stakes and its consensus is GAAP-basis,
  the OI&E line is unforecastable — say so and widen the interval rather than pretending.
- **Interest income/expense**: mechanical from the balance sheet + rate path; low error.
- **FX remeasurement gains/losses**: separate from translation; small but noisy.
- **Restructuring, impairments, legal settlements**: hit GAAP EPS; usually **excluded** from non-GAAP/street
  EPS. Which side of the line you are on is set by §8.1.
- Standard non-GAAP add-backs by size (Calcbench): amortisation of intangibles ~50% of total adjustment
  dollars, SBC ~16%, restructuring ~14%, M&A ~11%.

### 8.5 A quick error-attribution frame

For a large-cap with ~50% gross margin and ~25% operating margin, a **1% revenue error** propagates to
roughly a **3–4% EPS error** (operating leverage). Compare to: 50bp gross-margin error ≈ 2% EPS;
100bp ETR error ≈ 1.3% EPS; 1% share-count error ≈ 1% EPS. So the ranking of effort is
**revenue > gross margin > share count ≈ tax > BTL** — except that BTL and tax produce the *fat tails*.

---

## 9. Fat-tail and rare-event handling

### 9.1 Guidance withdrawal / suspension

**Base rates** ([FactSet, 23 May 2025](https://insight.factset.com/few-sp-500-companies-have-withdrawn-eps-guidance-for-2025)):

- Q1 2025 season, 478 S&P 500 reporters: **259 (54%)** commented on FY EPS guidance; of those, only
  **8 (3%)** withdrew or declined to update. Six cited tariff uncertainty.
- Breakdown of the 251 that did guide: 139 maintained, **64 raised**, 37 lowered, 8 initiated, 3 gave
  multiple ranges.
- **Q1 2020 (COVID): 185 S&P 500 companies** withdrew or did not update annual EPS guidance — a ~23×
  jump over a normal season.
- [Jenner & Block survey](https://www.jenner.com/en/news-insights/client-alerts/a-survey-of-how-public-companies-are-providing-guidance-in-light-of-tariffs)
  of 100 S&P 500 releases (Apr–May 2025): **6%** either pulled guidance or moved from annual to
  quarter-by-quarter; 18% quantified a tariff impact; 20% explicitly excluded tariffs from guidance.

**Cheap detection heuristics:**
- Scan the latest **8-K Item 2.02 / 7.01** and IR press releases for: `withdraw`, `suspend`, `not
  reaffirming`, `no longer providing`, `pausing`, `updating our outlook to reflect`, and the shift from
  annual to quarterly-only guidance.
- Treat a shift from **annual → quarterly-only guidance** as a soft withdrawal signal, not a neutral event.
- Note the asymmetry: 20% of companies in the 2025 survey said guidance **excluded** tariff impacts. If the
  guidance explicitly excludes a live cost shock, do **not** apply the §3 upward guidance-beat adjustment —
  the range is not a full forecast.
- If guidance is withdrawn: fall back to consensus + mechanical SRW, widen the interval, and **suppress the
  guidance-bias adjustment entirely**.

### 9.2 M&A closing mid-quarter

Revenue is consolidated **from the acquisition date only** — a stub period. Rules of thumb:
- Stub contribution ≈ target quarterly revenue × (days from close to quarter-end / days in quarter).
- Check whether consensus includes it: vendor consensus is stale for days-old deals; the company usually
  quantifies it. Salesforce is the cleanest live example — it breaks out the Informatica contribution
  in both actuals and guidance: *"including $444 million Informatica contribution"* in Q1 FY27 revenue,
  and *"including slightly above 4pts Informatica contribution"* in Q2 FY27 revenue guidance
  ([CRM IR](https://investor.salesforce.com/financials/quarterly-results/)).
- Detection: 8-K Item 2.01 (completion of acquisition), plus any press release with "completes acquisition".
- EPS effect is usually *negative* near-term (deal amortisation, financing cost) on GAAP and *neutral-to-
  positive* on non-GAAP — another reason the §8.1 basis question is load-bearing.

### 9.3 FX

Companies hand you the number; use theirs, not yours.

- **Meta Q1 2026:** FX effect on revenue **$1,749M on $56,311M = 3.1%**; GAAP growth 33% vs constant
  currency 29% → a **4pt FX tailwind**
  ([release](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/)).
- **Apple Sep-Q 2026 guidance:** FX a **2.5pt sequential headwind** to total-company YoY growth; and for
  Services specifically a **5pt headwind** to the YoY growth rate from the March to September quarter.
- **Salesforce Q2 FY27 guidance:** *"10% CC, $50M Y/Y FX"* — the bridge in dollars.

Cheap overlay when the company doesn't disclose: `FX_impact ≈ international_revenue_share ×
weighted_avg_FX_move_over_the_quarter`. Use **quarter-average** spot rates (revenue is translated at average
rates), not period-end. Every large multinational discloses constant-currency growth; back out
international share from the geographic segment table.

### 9.4 Fiscal-calendar traps

- **4-5-4 NRF retail calendar**: quarters of 13 weeks (4+5+4) so each contains equal weekends; weekend sales
  are 40–60% of weekly revenue. **Re-bin any calendar-based external data (foot traffic, search interest,
  card panels) into fiscal quarters, not calendar quarters.**
- **53rd week every 5–6 years**, landing in Q4. Real magnitudes:
  - **Kroger FY2023**: 53rd week = **$2.7B sales**, $187M operating profit, **$0.20 EPS**
    ([release](https://ir.kroger.com/news/news-details/2024/Kroger-Reports-Fourth-Quarter-and-Full-Year-2023-Results-Announces-Guidance-for-2024/default.aspx)).
  - **Victoria's Secret Q4'23**: extra week ≈ **$80M net sales (390bp of YoY)**, $20M operating income,
    **$0.20 EPS** — *plus* a further **~2pts** of pressure from the retail calendar *shift*
    ([script](https://victoriassecret.gcs-web.com/static-files/bac71919-6c55-4546-bf94-a5e7c6e9e84d)).
  - **Cracker Barrel FY2024**: 53rd week = $62.8M revenue, $5.5M net income, **$0.25 EPS**; adjusting for it,
    FY25 revenue growth goes from +0.4% to +2.2% and net income growth from +13.3% to +30.9%
    ([release](https://investor.crackerbarrel.com/news-releases/news-release-details/cracker-barrel-reports-fourth-quarter-and-full-year-fiscal-2025)).
  - Nordstrom FY2024 Q4: **~7 percentage points** of negative YoY impact from losing the 53rd week and the
    associated weekly calendar shift ([8-K exhibit](https://www.sec.gov/Archives/edgar/data/39911/000003991125000004/q42024eprexhibit991.htm)).
- Practical check: **count the weeks in the target quarter and in the year-ago comp quarter.** If they
  differ, the YoY framing is broken and must be adjusted before any of §5 applies.

### 9.5 Detecting that you are in a tail at all

Flag a quarter as high-variance (→ widen interval, shrink harder to consensus, suppress aggressive
adjustments) if **any** of:
1. Guidance withdrawn, suspended, or narrowed to quarterly-only.
2. M&A/divestiture closed or expected to close inside the quarter.
3. Company holds large marketable equity stakes **and** consensus is GAAP-basis (OI&E unforecastable).
4. 52 vs 53 week mismatch, or a fiscal-calendar shift.
5. FX move >5% in the trade-weighted basket relevant to the company over the quarter.
6. Cross-sectional estimate dispersion in the top decile (ExtractAlpha: high dispersion predicts misses).
7. Prior-quarter surprise magnitude in the tail (|surprise| > 10%) — a regime change may be in progress.
8. A meet-or-beat streak ≥ 8 quarters (streak-break risk; the JCF study says almost all lowball episodes
   eventually end, and BigEarnings measures a −6.3% 1-day move when an 8+ streak breaks vs −3.1% otherwise).

---

## Implications for our build

### Recipe A — **Guidance-Anchored Shrunk Ensemble** (default; build this first)

**Step 0 — Resolve the target.** Determine (a) whether scored consensus EPS is GAAP or non-GAAP, using the
§8.1 five-step checklist, and (b) which consensus *vintage* is scored. Store both on the forecast record.
If the basis is ambiguous, emit both and flag. **This step is worth more than everything else combined.**

**Step 1 — Build three independent anchors.**

| Anchor | Construction | Available when |
|---|---|---|
| `A_guid` | From the **most recent** guidance. Revenue: `midpoint + 1.0 × half-width` (i.e. the **upper bound**). EPS: same, then re-derive through the margin/tax/share stack if the company guides components (Apple-style). | Company guides |
| `A_cons` | Vendor consensus, exact scored vintage | Always |
| `A_mech` | Seasonal RW with Bernard–Thomas correction: `E_q = E_{q−4} + 0.34·ΔE_{q−1} + 0.19·ΔE_{q−2} + 0.06·ΔE_{q−3} − 0.24·ΔE_{q−4}` on **seasonally-differenced** revenue and EPS | Always (needs ≥ 9 quarters) |

**Step 2 — Firm-specific guidance-bias calibration.** Over the last **8 quarters**, compute the realised
`ACT_DIS = (actual − mid)/(0.5×(high−low))` for the firm's own last-guidance-of-quarter.
Let `d = median(ACT_DIS_8q)`, clamped to **[0, 2]**. Set `A_guid = mid + d × half_width`.
If the firm has <4 usable quarters, fall back to the population prior for its bucket:

| Bucket | Prior `d` | Source |
|---|---|---|
| Large-cap | **1.09** (median) / 1.55 (mean) | Ciconte Table 4 Panel B, 2002–2010 |
| High-growth (top-third M/B) | **1.40** (median) / 1.92 (mean) | Ciconte Table 4 Panel A |
| Pooled / small / low-growth | **1.00** | Ciconte Table 2, 2002–2010 |

Use the **median**, not the mean — the means are inflated by 2009–2010.

**Step 3 — Combine into the mechanical anchor.**

```
A = w_g·A_guid + w_c·A_cons + w_m·A_mech,   weights renormalised over available anchors
default:  w_g = 0.45,  w_c = 0.40,  w_m = 0.15     (company guides, guidance < 60 days old)
no guidance:                w_c = 0.75,  w_m = 0.25
guidance withdrawn:         w_c = 0.80,  w_m = 0.20   and force d = 0
guidance > 90 days old:     halve w_g, redistribute to w_c
```

**Step 4 — N blind LLM runs.** N = 5 per method, temperature-varied, each seeing a **different evidence
subset** (guidance+transcript / 10-Q+8-K / news+macro / driver metrics). **No run sees consensus, and no run
sees another run's number** (Da & Huang 2020). Each run outputs `{revenue, eps, 3 evidence citations,
confidence}`. Take the **median** across runs.

**Step 5 — Bounded adjustment.** The LLM's job is to propose an adjustment `δ` to `A`, not a level.

```
δ_rev ∈ [−4%, +3%]        δ_eps ∈ [−8%, +6%]        (asymmetric: upward adjustments are the biased ones)
deadband: |δ| < 0.5% (rev) or < 1.5% (eps)  →  set δ = 0
each δ must cite ≥ 2 distinct pieces of dated evidence; unjustified δ = 0
in a §9.5 tail regime, halve all bounds
```

Rationale: Fildes et al. — small adjustments damage accuracy, positive adjustments are the biased ones, and
mechanical combination beats letting judgment overwrite.

**Step 6 — Surprise-persistence tilt (mechanical, not LLM).**

```
tilt = 0.34·s₁ + 0.19·s₂ + 0.06·s₃          where sₖ = surprise vs consensus k quarters ago, in %
                                             (deliberately NO lag-4 term: its coefficient is −0.24)
apply:  0.5 × tilt,  clipped to ±2% (revenue) / ±4% (EPS)
if the firm has an 8+ quarter beat streak: halve the tilt (streak-break risk)
```

**Step 7 — EPS re-derivation and guardrails.** Never emit an EPS that isn't reconciled through:

```
EPS = (Rev × GM − Opex ± BTL) × (1 − ETR) ÷ DilutedShares
```
- `ETR` = **guided rate** if given, else trailing-4Q AETR excluding discretes. Never last quarter's reported ETR.
- `DilutedShares` = cover-page basic shares (10-Q, not the income-statement average) − executed-buyback run-rate
  shares + historical basic-to-diluted gap. **For heavy repurchasers this is where the edge is** (Kaplan et al.).
- If the company holds large marketable equity stakes and consensus is GAAP-basis: mark OI&E unforecastable,
  widen the interval, and shrink `δ_eps` to zero.
- If GAAP-basis: add back nothing. If non-GAAP-basis: exclude amortisation of intangibles, SBC, restructuring
  and M&A costs per the company's own reconciliation table.

**Step 8 — Final shrink toward consensus.**

```
final = λ·estimate + (1 − λ)·consensus
λ = 0.65 baseline
λ = 0.80 when estimate dispersion is high / guidance is stale / crowd is uncertain   (Halawi: LLM edge is here)
λ = 0.45 when guidance is tight and dispersion is low                                 (crowd is confident)
λ = 0.30 in any §9.5 tail regime
```
This is the Halawi result implemented literally: the system+crowd blend beat the crowd in **every** subgroup.
Do it in code — Schoenegger et al. showed models under-update when asked to blend in-prompt.

**Step 9 — Sanity gates (hard fail → fall back to consensus).**
Reject and re-run if: revenue YoY growth outside [prior 8-quarter min − 10pts, max + 10pts]; implied gross
margin outside [trailing min − 300bp, max + 300bp]; implied share count moved >3% QoQ; EPS sign flip without
an explicit cited cause; final estimate >25% from consensus without a §9 tail flag.

---

### Recipe B — **Pure Mechanical + Guidance** (the null model; the eval harness baseline)

`0.5 × (guidance upper bound) + 0.5 × consensus`, plus the Bernard–Thomas tilt, no LLM at all.
Cost: ~zero. This is the honest floor. **If Recipe A cannot beat this in backtest, ship this.**
It captures the two strongest documented biases (guidance conservatism, surprise autocorrelation) with no
model risk, and it is the demo slide that will land: "here is the null model, here is what the agent adds."

### Recipe C — **Driver-Decomposition First** (A/B this on the right business models only)

Replace `A_mech` with an explicit driver build, and raise `w_m` to 0.30. **Only enable** when the identity
closes on disclosed data — ad companies (`impressions × price/ad`, which reconciles to <1pt for Meta),
SaaS with guided cRPO (`cRPO × 90–100% conversion`), retail (`comp base × (1+traffic+ticket) + new units`).
**Disable everywhere else**: MacGregor & Armstrong measured **+458% error** from decomposition on
non-extreme, well-anchored quantities, which is exactly next-quarter revenue for a stable large-cap.
Expect this to win on META/GOOGL/CRM/WDAY/SBUX-type names and lose on conglomerates.

### Recipe D — **Free-form LLM direct** (control arm, to prove the scaffolding matters)

Single LLM, full context, "what will revenue and EPS be?", no anchor, no bounds, no ensemble. Include it in
the harness purely as the ablation. Expect it to lose: Halawi's bare zero-shot models scored **at or worse
than random**, and the best single model (.208) trailed the crowd (.149) badly.

---

### Eval-harness design (what to hill-climb on tonight)

Backtest over the last 8–12 quarters for 20–40 large-caps. Score with:

1. `|forecast − actual| / |actual|` (the accuracy half of the hackathon score), **and**
2. **Win rate vs consensus** — the fraction of company-quarters where `|our error| < |consensus error|`.
   This is the number that decides the competition. Track it separately for revenue and EPS.
3. Report both **median** and **mean** absolute percentage error — the mean will be owned by one GAAP
   OI&E blow-up, and that is diagnostic, not noise.

**Ablate in this order (highest expected value first):**
`d` (guidance position: 0 = midpoint vs 1.0 = upper bound vs firm-calibrated) → `λ` (consensus shrink) →
adjustment bounds and deadband → N per method → Recipe C on/off by business model.

The `d = 0 vs d = 1` ablation is the money experiment. If the Ciconte result still holds in 2024–2026 data,
moving the guidance anchor from midpoint to upper bound should be visible in the win rate immediately, and
it is the headline for the design half of the score.
