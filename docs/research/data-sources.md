# Data Sources — Agents vs Wall Street (16 Aug 2026)

Research compiled 15 Aug 2026. Goal: forecast a US-listed company's **next quarterly revenue + EPS** and beat sell-side consensus.

**Legend:** `[LIVE]` = actually hit tonight, response shown is real. `[DOCS]` = read from docs, not executed. `[BROKEN]` = tested and failed.

⚠️ **Two corrections to the brief up front:** the event is **Sunday 16 August 2026** (16 Aug is a Sunday), and **there is no OpenAI involvement** — it's presented by Primer · OpenStocks · AI Tinkerers. See §8.

### The 60-second version

Every endpoint in this box was verified working tonight, needs **no API key**, and is enough to build a competitive forecast on its own.

```
CIK map     https://www.sec.gov/files/company_tickers.json
Filings     https://data.sec.gov/submissions/CIK0001045810.json         → 8-K where items ∋ "2.02"
Exhibits    https://www.sec.gov/Archives/edgar/data/1045810/{accn}/index.json
GUIDANCE    https://www.sec.gov/Archives/edgar/data/1045810/000104581026000051/q1fy27pr.htm
History     https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{Tag}.json
Segments    {BASE}/FilingSummary.xml → R*.htm
CONSENSUS   yahoo-finance2@4 → quoteSummary(sym,{modules:["earningsTrend"]})
            https://stockanalysis.com/stocks/nvda/forecast/__data.json
Calendar    https://stockanalysis.com/stocks/earnings-calendar/__data.json
Transcripts https://huggingface.co/datasets/defeatbeta/yahoo-finance-data (DuckDB httpfs)
Macro       https://fred.stlouisfed.org/graph/fredgraph.csv?id=RSXFS
```
All SEC calls need `User-Agent: <App>/<ver> (<email>)` or they 403. StockAnalysis and Nasdaq need a browser UA (Nasdaq also needs `Referer: https://www.nasdaq.com/`).

### Contents

| § | Topic | Bottom line |
|---|---|---|
| [1](#1-sec-edgar--the-backbone) | SEC EDGAR | Free, keyless, complete. Backbone. Four gotchas that will silently corrupt your data |
| [2](#2-earnings-call-transcripts) | Transcripts | defeatbeta parquet (bulk) + Motley Fool (latest). Both free |
| [3](#3-consensus-estimates--the-number-to-beat) | Consensus | `yahoo-finance2@4` primary, StockAnalysis cross-check. Nasdaq is stale — don't benchmark on it |
| [4](#4-structured-fundamentals-apis-historical-quarterly-financials) | Fundamentals APIs | stockanalysis `__data.json`. Tiingo/Polygon/Intrinio are traps |
| [5](#5-management-guidance) | Guidance | 8-K EX-99.1. **No free structured dataset exists — this is the edge** |
| [6](#6-alternative-data--free-and-wireable-in-one-day) | Alt data | FRED + Wikipedia + TSA + Greenhouse. Google Trends is dead |
| [7](#7-earnings-calendar--who-reports-when) | Calendar | stockanalysis + Nasdaq, cross-checked against 8-K cadence |
| [8](#8-openstocks-and-the-event-itself) | OpenStocks & rules | No public API yet. **Prize rules should shape your architecture** |
| [9](#9-worked-reference-play-nvda-q2-fy2027) | Worked play | NVDA: guidance-implied $94.9B vs consensus $91.9B, fully derived |
| [→](#implications-for-our-build) | **Implications** | Priority order + primary/fallback per data type |

---

## 1. SEC EDGAR — the backbone

Everything below is free, no API key, no signup. Only requirement: a descriptive `User-Agent`.

### 1.0 Auth / etiquette / rate limits

| Item | Value | Status |
|---|---|---|
| Auth | None. No key, no token. | `[LIVE]` |
| Required header | `User-Agent: <AppName>/<ver> (<contact email>)` | `[LIVE]` |
| Missing/blank UA | **HTTP 403** | `[LIVE]` |
| Default `curl/8.x` UA | **HTTP 403** — curl's own UA is blocked | `[LIVE]` |
| Stated limit | **"our current maximum access rate is 10 requests per second"** — verbatim from the SEC Webmaster FAQ | `[LIVE]` |
| Observed | 15 concurrent `companyconcept` requests → 15× HTTP 200 in 1.27s, no 429 | `[LIVE]` |
| Compression | `Accept-Encoding: gzip` supported and worth it: AAPL companyfacts is **3.79 MB raw / 272 KB gzipped** (14×) | `[LIVE]` |
| Over-limit behaviour | 403 + temporary IP block. Not a 429. Do not hammer. | `[DOCS]` |
| Missing-UA error string | "Undeclared Automated Tool" | `[LIVE]` |
| Freshness | "The JSON structures are updated throughout the day, in real time, as submissions are disseminated." Bulk ZIPs republished nightly ~03:00 ET. | `[LIVE]` |

SEC's own sample header block, quoted from `https://www.sec.gov/about/webmaster-frequently-asked-questions` `[LIVE]`:
```
User-Agent: Sample Company Name AdminContact@<sample company domain>.com
Accept-Encoding: gzip, deflate
Host: www.sec.gov
```

```ts
const SEC_HEADERS = {
  "User-Agent": "WallStreetHackathon/1.0 (tools@brside.com)",
  "Accept-Encoding": "gzip, deflate",
};
```

Ship a token-bucket limiter at **8 req/s** with a global mutex. `undici`/`fetch` decompresses gzip automatically; native `https` does not.

### 1.1 Ticker → CIK

Two files, both on `www.sec.gov` (not `data.sec.gov`), both refreshed nightly.

```
https://www.sec.gov/files/company_tickers.json           # 796 KB, 10,398 entries [LIVE]
https://www.sec.gov/files/company_tickers_exchange.json  # 181 KB, adds exchange  [LIVE]
```

`company_tickers.json` — object keyed by arbitrary index string:
```json
{"0":{"cik_str":1045810,"ticker":"NVDA","title":"NVIDIA CORP"},
 "1":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."}}
```

`company_tickers_exchange.json` — columnar, more efficient:
```json
{"fields":["cik","name","ticker","exchange"],
 "data":[[1045810,"NVIDIA CORP","NVDA","Nasdaq"],[320193,"Apple Inc.","AAPL","Nasdaq"]]}
```

**Gotcha:** `cik_str` is an integer. Every `data.sec.gov` path needs it **zero-padded to 10 digits** with the `CIK` prefix: `320193` → `CIK0000320193`. Download once at startup into SQLite (`tickers(ticker PK, cik TEXT, name, exchange)`); it is 10k rows and never needs re-fetching during the day.

Also available: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=apple&type=10-Q&output=atom` for fuzzy name search `[DOCS]`, but the JSON file + local fuzzy match is faster.

### 1.2 Submissions API — filing history

```
https://data.sec.gov/submissions/CIK0000320193.json     # 164 KB [LIVE]
```

Top-level keys `[LIVE]`:
`cik, entityType, sic, sicDescription, ownerOrg, name, tickers, exchanges, ein, lei, description, website, investorWebsite, category, fiscalYearEnd, stateOfIncorporation, addresses, phone, flags, formerNames, filings`

- `fiscalYearEnd` — **critical**. `"0926"` for AAPL (late Sept), `"0131"` for NVDA (late Jan), `"0630"` for MSFT. Tells you immediately whether fiscal ≠ calendar quarters.
- `sic` / `sicDescription` — e.g. AAPL `3571 / Electronic Computers`. Use for peer-set selection.
- `investorWebsite` — direct link to the IR site for transcripts/decks.

`filings.recent` is **columnar** — 16 parallel arrays, up to **1,000 most recent filings**:
```
accessionNumber, filingDate, reportDate, acceptanceDateTime, act, form, fileNumber,
filmNumber, items, core_type, size, isXBRL, isInlineXBRL, isXBRLNumeric,
primaryDocument, primaryDocDescription
```

Zip index `i` across all arrays to reconstruct a filing record. Older filings live in `filings.files[]` → e.g. `{"name":"CIK0000320193-submissions-001.json","filingCount":1240,"filingFrom":"1994-01-26","filingTo":"2015-06-02"}` fetched from `https://data.sec.gov/submissions/CIK0000320193-submissions-001.json` `[LIVE]`.

**The single most useful filter — find the earnings press release 8-K:**
`form == "8-K" && items.includes("2.02")` (Item 2.02 = Results of Operations and Financial Condition).

Real output for NVDA `[LIVE]`:
```
2026-05-20  0001045810-26-000051  nvda-20260520.htm  items: 2.02,9.01
2026-02-25  0001045810-26-000019  nvda-20260225.htm  items: 2.02,9.01
2025-11-19  0001045810-25-000228  nvda-20251119.htm  items: 2.02,9.01
2025-08-27  0001045810-25-000207  nvda-20250827.htm  items: 2.02,9.01
```
The cadence (Feb 25 / May 20 / Aug 27 / Nov 19) is itself a **free earnings-date predictor** — see §7.

Other 8-K items worth flagging: `1.01` material agreement, `2.05` restructuring, `4.02` non-reliance (restatement — big red flag), `5.02` officer departure, `7.01` Reg FD, `8.01` other, `9.01` exhibits.

### 1.3 companyfacts — every XBRL fact for a company

```
https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json   # 3.79 MB raw / 272 KB gz [LIVE]
```

Shape:
```
{ cik, entityName, facts: { "dei": {...2 concepts}, "us-gaap": {...503 concepts for AAPL} } }
facts["us-gaap"][TAG] = { label, description, units: { "USD": [ fact, ... ] } }
```

A single fact `[LIVE]`, AAPL fiscal Q3 2026:
```json
{"start":"2026-03-29","end":"2026-06-27","val":109417000000,
 "accn":"0000320193-26-000020","fy":2026,"fp":"Q3","form":"10-Q",
 "filed":"2026-07-31","frame":"CY2026Q2"}
```

Unit keys seen: `USD`, `USD/shares`, `shares`, `pure`.

#### Gotcha A — the same concept mixes quarterly and year-to-date durations

For AAPL's revenue tag, the array contains **both** the 3-month and the cumulative 6/9/12-month facts, undifferentiated `[LIVE]`:
```
2025-09-28 → 2026-06-27   364,357,000,000   (9-month YTD)   frame=None
2026-03-29 → 2026-06-27   109,417,000,000   (3-month Q3)    frame=CY2026Q2
```
**Filter by `end - start` in days.** Quarterly = 80–100 days. Annual = 350–375. Never trust `fp` alone.

Secondary trick: **quarterly duration facts carry a `frame` key of the form `CY####Q#`; YTD facts have `frame: null`.** Filtering on `frame != null && /Q\d$/` is a clean, cheap de-dup. It also de-dups the same period restated in a later filing.

#### Gotcha B — Q4 is never reported as a discrete quarter

The 10-K reports the full year only. Demonstrated live on MSFT (FY ends 30 Jun) `[LIVE]`:
```
2025-07-01..2025-09-30  dur= 91   77.673B  fy2026Q1  10-Q
2025-10-01..2025-12-31  dur= 91   81.273B  fy2026Q2  10-Q
2026-01-01..2026-03-31  dur= 89   82.886B  fy2026Q3  10-Q
2025-07-01..2026-06-30  dur=364  331.839B  fy2026FY  10-K
```
Fiscal Q4 revenue = `331.839 − (77.673 + 81.273 + 82.886)` = **90.007B**. Your ingestion layer must synthesise Q4. Same applies to EPS, but EPS does **not** sum exactly (share-count drift) — derive Q4 EPS as `Q4 NetIncome / Q4 WeightedAverageDilutedShares`, not by subtraction of EPS values.

#### Gotcha C — the revenue tag is not the same across companies

Tested fallback chain, in order `[LIVE]`:
1. `RevenueFromContractWithCustomerExcludingAssessedTax`
2. `Revenues`
3. `RevenueFromContractWithCustomerIncludingAssessedTax`
4. `SalesRevenueNet` (pre-ASC606, ~2018 and earlier)

Results running that chain over 11 tickers `[LIVE]`:

| Ticker | Tag that hit | Latest quarter | Value |
|---|---|---|---|
| AAPL | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-06-27 | $109.417B |
| NVDA | **Revenues** | 2026-04-26 | $81.615B |
| MSFT | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-03-31 | $82.886B |
| AMZN | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-06-30 | $200.606B |
| GOOGL | **Revenues** | 2026-06-30 | $119.796B |
| META | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-06-30 | $60.801B |
| TSLA | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-06-30 | $28.236B |
| COST | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-05-10 | $70.527B |
| LULU | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-05-03 | $2.4716B |
| DAL | RevenueFromContractWithCustomerExcludingAssessedTax | 2026-06-30 | $19.757B |
| **JPM** | **none of the four** → needs `RevenuesNetOfInterestExpense` ($57.347B, 2026-06-30) | | |

**Financials (banks/insurers) need a separate chain:** `RevenuesNetOfInterestExpense`, `InterestAndDividendIncomeOperating` + `NoninterestIncome`, `InterestIncomeExpenseNet`. Also note NVDA *used* to tag `RevenueFromContractWithCustomerExcludingAssessedTax` (2018–2020 data still sits there) and switched to `Revenues` — so **filter the chain by recency, not just presence**. My test only accepted a tag if it had a quarterly fact with `end >= 2025-06-01`; that's the correct guard.

#### The EPS + supporting tag set

| Metric | Primary tag | Unit |
|---|---|---|
| Diluted EPS (GAAP) | `EarningsPerShareDiluted` | `USD/shares` |
| Basic EPS | `EarningsPerShareBasic` | `USD/shares` |
| Net income | `NetIncomeLoss` | `USD` |
| Diluted share count | `WeightedAverageNumberOfDilutedSharesOutstanding` | `shares` |
| Gross profit | `GrossProfit` | `USD` |
| Cost of revenue | `CostOfRevenue` / `CostOfGoodsAndServicesSold` | `USD` |
| Operating income | `OperatingIncomeLoss` | `USD` |
| R&D | `ResearchAndDevelopmentExpense` | `USD` |
| SG&A | `SellingGeneralAndAdministrativeExpense` | `USD` |
| Tax rate inputs | `IncomeTaxExpenseBenefit`, `IncomeLossFromContinuingOperationsBeforeIncomeTaxes...` | `USD` |
| Deferred revenue (leading indicator) | `ContractWithCustomerLiabilityCurrent`, `DeferredRevenueCurrent` | `USD` |
| RPO / backlog (**strong leading indicator**) | `RevenueRemainingPerformanceObligation` | `USD` |
| Inventory (channel signal) | `InventoryNet` | `USD` |
| Buybacks (EPS driver) | `PaymentsForRepurchaseOfCommonStock` | `USD` |

**GAAP vs non-GAAP:** XBRL gives you **GAAP only**. Consensus EPS is almost always **non-GAAP/adjusted**. You must bridge: non-GAAP EPS ≈ GAAP EPS + SBC/share + amortisation of intangibles/share + one-offs/share. Get the actual reconciliation from the 8-K exhibit 99.1 (§5) — every press release contains a GAAP↔non-GAAP reconciliation table. **This is the single biggest silent scoring failure mode in this hackathon: forecasting a GAAP number and comparing it to a non-GAAP consensus.**

### 1.4 companyconcept — one tag, one company (use this, not companyfacts)

```
https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/EarningsPerShareDiluted.json
# 3.97 KB, 338 facts [LIVE]
```
Returns `{cik, taxonomy, tag, label, description, entityName, units:{...}}` — same fact objects as companyfacts.

Real tail `[LIVE]`:
```
2024-09-29..2025-09-27  7.46  fy2025 FY  10-K  frame=CY2025
2025-09-28..2025-12-27  2.84  fy2026 Q1  10-Q  frame=CY2025Q4
2025-09-28..2026-03-28  4.85  fy2026 Q2  10-Q  frame=None      <- YTD, discard
2025-12-28..2026-03-28  2.01  fy2026 Q2  10-Q  frame=CY2026Q1
2025-09-28..2026-06-27  6.88  fy2026 Q3  10-Q  frame=None      <- YTD, discard
2026-03-29..2026-06-27  2.02  fy2026 Q3  10-Q  frame=CY2026Q2
```

**Prefer companyconcept over companyfacts.** 4 KB vs 3.8 MB. Twenty tag fetches ≈ 80 KB and 3 seconds at 8 req/s, versus one 3.8 MB blob you then have to search. Only pull companyfacts when you need tag *discovery* (e.g. "what revenue-ish tags does this filer use?"), then cache it.

Returns **404** if the company never used that tag — treat 404 as "not applicable", not an error, and fall through the chain.

### 1.5 Frames — one tag, one period, all companies

```
https://data.sec.gov/api/xbrl/frames/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax/USD/CY2026Q2.json
# 61 KB, pts=2098 filers [LIVE]
```
```json
{"taxonomy":"us-gaap","tag":"...","ccp":"CY2026Q2","uom":"USD","label":"...","pts":2098,
 "data":[{"accn":"0001628280-26-050134","cik":1800,"entityName":"ABBOTT LABORATORIES",
          "loc":"US-IL","start":"2026-04-01","end":"2026-06-30","val":12593000000}]}
```

Period formats, all verified `[LIVE]`:

| Format | Meaning | Example tested |
|---|---|---|
| `CY2025` | annual duration | `.../Revenues/USD/CY2025.json` → 200, 67 KB |
| `CY2026Q2` | quarterly duration | 200, 2,098 filers |
| `CY2026Q2I` | **instantaneous** (balance-sheet items) | `.../Assets/USD/CY2026Q2I.json` → 200, 140 KB |
| `dei` taxonomy works too | | `.../dei/EntityCommonStockSharesOutstanding/shares/CY2026Q2I.json` → 200 |

**Killer use case:** build a same-sector peer panel in one request. Grab CY2026Q2 revenue for all 2,098 filers, join to SIC from submissions, and you have every peer's just-reported quarter — a read on sector demand before your target reports. Also lets you compute sector-level YoY growth as a prior.

**Gotcha:** frames only include filers whose period boundaries align to the calendar frame within a few days. AAPL (quarter ending 27 Jun) appears in CY2026Q2 `[LIVE]`; NVDA (quarter ending 26 Apr) lands in **CY2026Q1**, not Q2. And a company is only in a frame once its filing lands, so recent frames fill in over weeks. Do not treat frame membership as a company universe.

### 1.6 Full-text search

```
https://efts.sec.gov/LATEST/search-index?q=%22revenue+guidance%22&forms=8-K&dateRange=custom&startdt=2026-07-01&enddt=2026-08-14
```
Raw Elasticsearch response `[LIVE]`:
```json
{"took":58,"hits":{"total":{"value":290,"relation":"eq"},"hits":[
  {"_index":"edgar_file","_id":"0001193125-26-332802:rare-ex99_1.htm","_score":8.16,
   "_source":{"ciks":["0001515673"],"period_ending":"...","display_names":["..."],
              "root_forms":["8-K"],"file_date":"...","form":"8-K","adsh":"...",
              "file_type":"EX-99.1","file_description":"...","items":["2.02","9.01"],
              "sics":["..."],"biz_states":["..."]}}]}}
```

Params (all `[LIVE]` unless noted): `q` (supports `"exact phrase"`), `forms` (comma-sep), `ciks` (10-digit zero-padded), `startdt`/`enddt` (`YYYY-MM-DD`), `dateRange=custom`, `from` (pagination offset), `entityName`, `locationCode` `[DOCS]`.

`_id` is `{accession}:{filename}` — which is **exactly** what you need to build the archive URL (see §1.7). `file_type` tells you `EX-99.1` vs `EX-99.2` directly.

**Coverage starts 2001-01-01, verified by probe** `[LIVE]`:
```
1999 → 0 hits    2000 → 0 hits    2001 → 10,000 hits    2002 → 10,000 hits
```
(10,000 is the ES result cap; use `from` to page, but you cannot exceed 10k total — narrow with `ciks`/`forms`/dates.)

Scoped example that works `[LIVE]`: `?q=%22third+quarter+outlook%22&forms=8-K&ciks=0001045810` → 6 hits, top one `0001045810-11-000039:cfocommentary.htm`, `file_type: EX-99.2`, `file_description: "Q212 CFO COMMENTARY"`.

**High-value queries for this problem:**
- `q="is expected to be"&forms=8-K&ciks=<cik>` → guidance sentences
- `q="we now expect"&forms=8-K` → guidance revisions
- `q="reconciliation of GAAP to non-GAAP"&ciks=<cik>` → the bridge table
- `q="material weakness"` / `forms=8-K` + item 4.02 → restatement risk
- Sector-wide: `q="softening demand"&forms=10-Q&startdt=...` → thematic read-across

### 1.7 Fetching the actual documents (archive layout)

Given accession `0001045810-26-000051` and CIK `1045810`:
```
ACCN_NODASH = 000104581026000051
BASE = https://www.sec.gov/Archives/edgar/data/1045810/000104581026000051/
```

List the files — **use `index.json`, not `{accession}-index.json`** (the latter 404s) `[LIVE]`:
```
GET https://www.sec.gov/Archives/edgar/data/1045810/000104581026000051/index.json
```
Real listing for NVDA's Q1 FY27 earnings 8-K `[LIVE]`:
```
0001045810-26-000051-index.html
0001045810-26-000051.txt              <- full submission, all exhibits concatenated
0001045810-26-000051-xbrl.zip
FilingSummary.xml                     <- map of the R*.htm rendered reports
MetaLinks.json
nvda-20260520.htm                     <- the 8-K cover itself
nvda-20260520_htm.xml                 <- XBRL instance (has dimensions!)
q1fy27pr.htm            274 KB        <- EX-99.1  PRESS RELEASE (guidance lives here)
q1fy27cfocommentary.htm 165 KB        <- EX-99.2  CFO COMMENTARY (gold mine)
R1.htm
```

**NVIDIA files a separate "CFO Commentary" exhibit every quarter** — a structured, numbers-dense narrative that is far easier to parse than the transcript. Several large caps do this (NVDA, historically ORCL, others). Always check for EX-99.2.

Other useful archive endpoints `[DOCS]`/`[LIVE]`:
- `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=...&type=8-K&dateb=&owner=include&count=40&output=atom` — Atom feed alternative `[DOCS]`
- `https://www.sec.gov/Archives/edgar/full-index/2026/QTR3/form.idx` — all filings by form, per quarter `[DOCS]`
- `https://www.sec.gov/Archives/edgar/daily-index/2026/QTR3/` — daily indexes, for "did they file yet?" polling `[DOCS]`

### 1.8 Segment revenue — NOT in companyfacts

**`companyfacts`/`companyconcept` return only *consolidated, non-dimensional* facts.** Segment/geography/product breakouts carry XBRL dimensions and are stripped out. This surprises people. Two ways to get them:

**Option A (recommended, ~10 lines of code): scrape the rendered `R*.htm` financial report files.**

1. `GET {BASE}/FilingSummary.xml` → 70 `<Report>` entries for NVDA's 10-Q `[LIVE]`
2. Match `<ShortName>` against `/segment|disaggregat|geograph|revenue/i` → get `<HtmlFileName>`

Real matches for NVDA 10-Q `0001045810-26-000052` `[LIVE]`:
```
R20.htm  Segment Information
R62.htm  Segment Information - Schedule of Reportable Segments (Details)
R63.htm  Segment Information - Schedule of Reconciling Items (Details)
R64.htm  Segment Information - Schedule of Revenue by Geographic Regions (Details)
R66.htm  Segment Information - Schedule of Revenue by Market Platform (Details)
R2.htm   Condensed Consolidated Statements of Income
```

3. `GET {BASE}/R66.htm` and parse the `<table>` — it's clean, tiny (2.5 KB), server-rendered HTML.

Actual parsed output `[LIVE]`, NVDA revenue by market platform, $ in millions:
```
                                      Apr 26, 2026 | Apr 27, 2025
Revenue (total)                             81,615 |       44,062
Data Center                                 75,246 |       39,112
  Hyperscale                                37,869 |       17,599
  AI Clouds, Industrial, & Enterprise       37,377 |       21,513
Edge Computing                               6,369 |        4,950
```
And R62.htm (reportable segments) `[LIVE]`:
```
Compute & Networking   revenue 74,550 (vs 39,589)  op income 53,335 (vs 22,054)
Graphics               ...
```

Bonus: the R-file tables come with the **prior-year comparative column for free**, so you get YoY per segment in one fetch.

**The same trick gets you the entire income statement in one 7 KB fetch.** `R2.htm` for that NVDA 10-Q `[LIVE]`, with the prior-year comparative column included:
```
Condensed Consolidated Statements of Income ($M)   Apr 26 2026 | Apr 27 2025
Revenue                                                 81,615 |      44,062
Cost of revenue                                         20,458 |      17,394
Gross profit                                            61,157 |      26,668
  Research and development                               6,321 |       3,989
  Sales, general and administrative                      1,300 |       1,041
Total operating expenses                                 7,621 |       5,030
Operating income                                        53,536 |      21,638
Interest income / expense / other, net                  16,367 |         272
Income before income tax                                69,903 |      21,910
Income tax expense                                      11,582 |       3,135
Net income                                              58,321 |      18,775
Diluted EPS                                              $2.39 |       $0.76
Diluted weighted-average shares (M)                     24,391 |      24,611
```
This is **more complete and better-labelled than reassembling companyfacts tag-by-tag**, and it needs no tag-fallback logic. Downside: it's per-filing, so building a 12-quarter history means 12 fetches + 12 parses, and the row labels are company-specific strings rather than stable XBRL tags. Use companyconcept for the *time series*, R-files for *this quarter's detail and segments*.

Parsing note: `R*.htm` tables are followed by a long block of XBRL element definitions. Cut everything from the first row whose first cell is `X` or that contains `Namespace Prefix:`.

**Option B: parse the inline-XBRL instance** (`nvda-20260426_htm.xml`) and resolve `<xbrli:context>` dimension members. More robust and machine-typed, but you need an XBRL-aware parser and 2–3× the code. Not worth it in a one-day build.

**Option C: SEC DERA Financial Statement Data Sets** `[LIVE]` — quarterly ZIPs of `sub/num/pre/tag` TSVs covering every filer; `num.txt` includes a `segments` column in recent vintages.
```
https://www.sec.gov/files/dera/data/financial-statement-data-sets/2026q1.zip   → HTTP 200
https://www.sec.gov/files/dera/data/financial-statement-and-notes-data-sets/2026q1_notes.zip → HTTP 404 (path changed; find via the DERA landing page)
```
Great for bulk backtesting across thousands of filers; overkill for a single-company demo.

### 1.9 What in each form actually matters for forecasting

| Form | What to extract | Why |
|---|---|---|
| **8-K item 2.02 → EX-99.1** | Reported rev/EPS, **forward guidance ("Outlook")**, GAAP↔non-GAAP reconciliation, segment table | The guidance number is often 70%+ of the answer. Consensus anchors to it. |
| **8-K item 2.02 → EX-99.2** | CFO commentary / supplemental (not all filers) | Densest numbers-per-token source that exists |
| **10-Q** | Income statement, segment note, deferred revenue, RPO/backlog, MD&A drivers, subsequent events | Segment mix + deferred/RPO are the leading indicators |
| **10-K** | Full-year, risk factors, segment history, seasonality, customer concentration | Seasonality priors; Q4 derivation base |
| **8-K item 4.02** | Non-reliance / restatement | Disqualifies your historical series |
| **8-K item 5.02** | CFO departure | Guidance-reset risk |
| **DEF 14A** | Exec comp targets tied to revenue/EPS | Reveals management's own internal plan |

### 1.10 Worked guidance retrieval, end to end `[LIVE]`

```
1) ticker NVDA → cik 0001045810                  (company_tickers.json)
2) submissions → newest 8-K with items ∋ "2.02"  → accn 0001045810-26-000051, 2026-05-20
3) index.json                                    → q1fy27pr.htm is EX-99.1
4) GET .../000104581026000051/q1fy27pr.htm       → 15 KB gz, strip tags → 20,790 chars
5) locate "Outlook"
```
Verbatim extract from the filing:

> "NVIDIA's outlook for the second quarter of fiscal 2027 is as follows: • Revenue is expected to be $91.0 billion, plus or minus 2%. NVIDIA is not assuming any Data Center compute revenue from China in its outlook. • GAAP and non-GAAP gross margins are expected to be 74.9% and 75.0%, respectively, plus or minus 50 basis points. • GAAP and non-GAAP operating expenses are expected to be approximately $8.5 billion and $8.3 billion, respectively."

Same document also yields the reported quarter `[LIVE]`: operating expenses $7,449M, operating income $53,783M, net income $45,548M, **diluted EPS $1.87**, Data Center revenue a record $75.2B (+21% QoQ, +92% YoY).

**The GAAP trap, caught live in this very document.** The same press release states verbatim:

> "For the quarter, GAAP and non-GAAP earnings per diluted share were $2.39 and $1.87, respectively."

XBRL `EarningsPerShareDiluted` gives you **$2.39**. Consensus for NVDA is quoted on the **non-GAAP $1.87** basis. Here the gap runs the *unusual* direction — non-GAAP is 22% *lower* than GAAP, because NVDA excluded a ~$15.9B non-operating investment gain (visible as `Other income (expense), net 15,929` in R2.htm). Anyone who naively pipes `EarningsPerShareDiluted` into a consensus comparison scores a catastrophic false "beat". **Always read the GAAP↔non-GAAP sentence out of EX-99.1 and record which basis you are forecasting on.**

**That is a complete, self-contained forecast in four HTTP calls, zero API keys.** With guidance of $91.0B ±2%, gross margin 75.0% and opex $8.3B non-GAAP, you can build a bottom-up EPS estimate arithmetically and only need to model the *deviation from guidance* — which for NVDA has historically been a beat.

**Timing note:** NVDA's 8-K cadence is Feb 25 / May 20 / Aug 27 / Nov 19. Their Q2 FY2027 report is due **~26–27 Aug 2026**, i.e. ~11 days after the hackathon. That makes NVDA an excellent demo target: guidance is on the record, consensus is published, and the resolution date is close enough to be credible.

### 1.11 Real-time "has it filed yet?" feeds

```
# All 8-Ks as they land, newest first (Atom) [LIVE]
https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=10&output=atom
```
Live sample pulled tonight `[LIVE]`:
```
8-K - Precipio, Inc. (0001043961) (Filer)              2026-08-14T17:30:25-04:00
8-K - Mediaco Holding Inc. (0001784254) (Filer)        2026-08-14T17:29:43-04:00
8-K - INNSUITES HOSPITALITY TRUST (0000082473) (Filer) 2026-08-14T17:27:14-04:00
```
Per-company variant `[LIVE]` (HTTP 200, 2.1 KB): `?action=getcompany&CIK=0001045810&type=8-K&count=10&output=atom`.
Daily index directory `[LIVE]`: `https://www.sec.gov/Archives/edgar/daily-index/2026/QTR3/`.

Latency from acceptance to feed appearance is seconds-to-a-minute. If your demo needs a "we called it, then the filing dropped" moment, poll the per-company Atom feed every 30s.

### 1.12 Bulk downloads (avoid tomorrow)

| File | Size | Note |
|---|---|---|
| `https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip` | **1.41 GB** | every filer's companyfacts `[LIVE]` |
| `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` | **1.56 GB** | every filer's submissions `[LIVE]` |

Only worth it if you plan a mass backtest. For a demo, per-company REST calls are faster than the download.

### 1.13 Minimal EDGAR tool surface to build first

```ts
resolveCik(ticker)                             // company_tickers.json, cached in SQLite
getFilings(cik, {forms?, items?, limit?})      // submissions API
getConcept(cik, tag, {unit?})                  // companyconcept
getQuarterlySeries(cik, metric)                // tag fallback chain + duration filter + Q4 synthesis
getFilingFiles(cik, accn)                      // index.json
getExhibit(cik, accn, filename)                // archive fetch → text
getSegments(cik, accn)                         // FilingSummary.xml → R*.htm → table
fullTextSearch(q, {forms?, ciks?, dates?})     // efts
getFrame(tag, unit, period)                    // frames, peer panel
```


---

## 2. Earnings call transcripts

### 2.1 Summary

| Source | Free? | Full text + Q&A? | History | Key needed | Verdict |
|---|---|---|---|---|---|
| **defeatbeta parquet (HuggingFace)** | **Yes** | Yes, **speaker-segmented** | ≥2023 confirmed for NVDA | No | **Best for bulk backfill** `[LIVE]` |
| **Motley Fool scrape** | Yes | Yes, full call | **~2018 → present** | No | **Best for same-day latest** `[LIVE]` |
| **SEC 8-K EX-99.2 (CFO commentary)** | Yes | Prepared remarks only, no Q&A | full | No | **License-clean, underrated** `[LIVE]` |
| Alpha Vantage `EARNINGS_CALL_TRANSCRIPT` | 25 req/day | Yes + per-paragraph sentiment | varies | Yes (`demo` works for demo params) | Fine for one live ticker `[LIVE]` |
| earningscall.biz | demo = AAPL/MSFT only | Yes (ASR) | ~2020+ | Yes | $60–155/mo `[LIVE]` |
| Seeking Alpha | index only | **No — Premium $299/yr** | — | No (index) | Index is free, body isn't `[LIVE]` |
| **API Ninjas** | **No — premium-only** | — | 2005+ on Business tier | Yes | **Deprioritize** `[LIVE]` 400 |
| **FMP** | **No — $149/mo Ultimate** | — | — | Yes | Skip `[LIVE]` |
| **Finnhub** | **No — excluded even at $3,500/mo** | — | — | Yes | Skip `[DOCS]` |
| Quartr / Roic.ai / Intrinio | No | — | — | — | Sales-gated, skip `[DOCS]` |

### 2.2 defeatbeta — best free option `[LIVE]`

**The dataset name commonly cited is wrong.** `defeatbeta/stock-earnings-call-transcripts` does not exist. The real one is:

```
https://huggingface.co/datasets/defeatbeta/yahoo-finance-data
  data/stock_earning_call_transcripts.parquet     # 2.25 GB
```
143,082 downloads, last modified **2026-08-15** — updated today.

**The datasets-server `/rows` API does NOT work here** — returns `{"error":"Not supported: dataset viewer is disabled…"}`. Ignore that path.

**DuckDB + httpfs reads the parquet directly over HTTPS with range requests** — no download, no key `[LIVE]`:
```sql
INSTALL httpfs; LOAD httpfs;
SELECT symbol, fiscal_year, fiscal_quarter, report_date, len(transcripts)
FROM read_parquet('https://huggingface.co/datasets/defeatbeta/yahoo-finance-data/resolve/main/data/stock_earning_call_transcripts.parquet')
WHERE symbol = 'NVDA';
```
Schema — **already speaker-segmented, no parsing needed**:
```
symbol VARCHAR, fiscal_year INTEGER, fiscal_quarter INTEGER, report_date VARCHAR,
transcripts_id INTEGER,
transcripts STRUCT(paragraph_number INTEGER, speaker VARCHAR, content VARCHAR)[]
```
**12 NVDA quarters returned in 14.6 seconds** over HTTP `[LIVE]` (columnar pruning works):
```
('NVDA',2027,1,'2026-05-20',76)  ('NVDA',2026,4,'2026-02-25',45)  ('NVDA',2026,3,'2025-11-19',35)
('NVDA',2026,2,'2025-08-27',28)  ('NVDA',2026,1,'2025-05-28',29)  ('NVDA',2025,4,'2025-02-26',36)
... back to ('NVDA',2024,2,'2023-08-23',37)
```
It correctly uses **NVDA's fiscal calendar** (FY2027 Q1 = May 2026), matching SEC.

**Sibling files in the same repo, several directly useful:**
```
stock_earning_calendar.parquet      196 KB   ← report dates
stock_statement.parquet             115 MB   ← income statement history
stock_revenue_breakdown.parquet     1.2 MB   ← segment revenue
stock_tailing_eps.parquet           2.9 MB
stock_sec_filing.parquet             90 MB
company_tickers.json                1.4 MB
```
Note: DuckDB is a native dependency. In TS use `@duckdb/node-api`, or shell out to the `duckdb` CLI and read JSON — the latter is faster to wire in a hackathon.

License: derived from Yahoo Finance, non-commercial/research posture. Fine for a hackathon; don't resell.

### 2.3 Motley Fool — free, full text, plain curl `[LIVE]`

**URL pattern:** `https://www.fool.com/earnings/call-transcripts/{YYYY}/{MM}/{DD}/{slug}/`

**Slugs are not derivable — do not guess them.** They vary: `nvidia-nvda-q1-2027-earnings-transcript` (no "call") vs `hawaiian-electric-he-q2-2026-earnings-call-transcript`.

**Discovery — this is the important part:**
- **Monthly sitemap:** `https://www.fool.com/sitemap/{YYYY}/{MM}` — `2026/05` returned 972,845 bytes containing **2,132 transcript URLs**. Your backfill index.
- **News sitemap (last ~48 h):** `https://www.fool.com/news-sitemap.xml` — includes `<news:stock_tickers>` (e.g. `NASDAQ:NVDA`), giving you ticker→URL mapping free. Your live poller.
- The sitemap index at `https://www.fool.com/sitemap/` goes back to **1995/03**. ⚠️ `https://www.fool.com/sitemap.xml` is a **404 SPA error page** — use the trailing-slash `/sitemap/` form.

**Extraction proof (NVDA Q1 FY2027)** `[LIVE]`:
```
.../2026/05/20/nvidia-nvda-q1-2027-earnings-transcript/
HTTP 200, 502,843 bytes → 60,057 chars text
marker "Full Conference Call Transcript" at char 10,142 → ~49,915 chars of full call incl. Q&A
```
No JS rendering needed. Parse from the `Full Conference Call Transcript` marker; speakers appear as `Name: text`. Content *before* the marker is Fool's own editorial summary — useful metadata, but not the call.

**History:** `2019/01` confirmed (older entries use `.aspx`); `2018/01` present; `2017/01` and `2017/08` returned **zero**. Usable depth ≈ **2018 → present**. Coverage is broad — 2,132 calls in one month, including microcaps.

**Rate limits:** none encountered. Needs a browser `User-Agent`.

**Licensing:** `robots.txt` has 85 `Disallow` lines but **none cover `/earnings/` or `/call-transcripts/`**, and there are no `GPTBot`/`CCBot`/`ClaudeBot` rules (only `MauiBot`, `Bytespider` blocked). So robots permits it — **but Fool's Terms of Use prohibit redistribution/commercial reuse**, and they own the transcripts as editorial product. **Low risk for an in-room demo, high risk for anything shipped. Analyse in memory; do not republish.**

### 2.4 Seeking Alpha — index free, body paywalled `[LIVE]`

```
GET https://seekingalpha.com/api/v3/symbols/NVDA/transcripts?page[size]=3   → HTTP 200, no auth
```
Returns `id, type, title, publishOn, isLockedPro, isPaywalled, links.self` — a **free transcript index** (dates + article IDs). The article *body* needs Premium ($299/yr). Transcripts moved behind Premium years ago and remain there.

The much more valuable find on the same unauthenticated API is a **consensus estimates** endpoint — see §3.

### 2.5 Others

**Alpha Vantage works on the `demo` key** `[LIVE]`:
```
https://www.alphavantage.co/query?function=EARNINGS_CALL_TRANSCRIPT&symbol=IBM&quarter=2024Q1&apikey=demo
```
Returns speaker-segmented JSON **with a per-paragraph LLM sentiment score** — a genuinely nice free feature:
```json
{"speaker":"Arvind Krishna","title":"CEO","content":"Thank you for joining us...","sentiment":"0.6"}
```
Real keys are capped at **25 requests/day**, so it's fine for one live ticker, useless for backfill.

**earningscall.biz** `[LIVE]`: `https://v2.api.earningscall.biz/transcript?apikey=demo&exchange=NASDAQ&symbol=AAPL&year=2026&quarter=3&level=1` works — 44,767 chars. **Demo key is restricted to AAPL and MSFT** (NVDA/IBM return empty). `level=2` gives speaker segmentation but with **anonymous IDs** (`spk12`) unless you pay. Transcripts are ASR/machine-generated; docs admit errors. ~15 min after call ends. $60–155/mo.

**API Ninjas — premium-only, deprioritize** `[LIVE]` (`HTTP 400 {"error":"Missing API Key."}`). Docs state `/v1/earningstranscript GET — Premium Only`. Free tier (3,000 calls/mo) is **non-commercial, no caching/storing, 1–2 hrs downtime/day** and doesn't include this endpoint anyway. Developer $39–59/mo covers only the last 5 years; full 2005+ archive needs Business $99–149/mo.

**FMP** `[LIVE]`: transcript endpoints return `{"Error Message":"Invalid API KEY."}`; docs put transcripts in **Ultimate at $149/mo**. **Finnhub** `[DOCS]`: pricing footnote is damning — *"All-in-One plan doesn't include access to Earnings call transcripts."* Not in the **$3,500/mo** tier either.

**HuggingFace corpora for eval/benchmarking** (all stale relative to 2026 — don't use for live inference) `[LIVE]`:
`glopardo/sp500-earnings-transcripts` (626 dl), `kurry/sp500_earnings_transcripts` (452), `jlh-ibm/earnings_call` (311), `lamini/earnings-calls-qa` (195, Q&A pairs — good for eval), `mrSoul7766/ECTSum` (133), `awinml/earnings_calls_transcripts` (53), `ChanceFocus/flare-ectsum` (38). `MAEC` is **not** on HF — it's a GitHub academic release.

### 2.6 Audio — skip

Company IR webcast archives (Q4 Inc serves plain MP3s from `q4cdn.com`, curl-friendly) and earningscall.biz Ultimate ($129/mo) bundle audio. **Not worth it.** Text is free and same-day from Fool, ~15 min from earningscall.biz. Whisper costs 5–15 min GPU per call and buys nothing over existing text. The only real justification is vocal-tone/hesitation features — a research project, not an overnight build.

---

## 3. Consensus estimates — the number to beat

### 3.1 Comparison

| Source | Next-Q rev | Next-Q EPS | Analyst count | High/low | Revision history | Auth | Rate limit | Cost | TS ergonomics | Tested |
|---|---|---|---|---|---|---|---|---|---|---|
| **Yahoo via `yahoo-finance2`** | ✅ | ✅ | ✅ separate for rev & EPS | ✅ both | ✅ **best** (EPS 7/30/60/90d + up/down counts) | none (auto cookie+crumb) | undocumented, soft | **free** | ⭐⭐⭐⭐⭐ native TS, zod, `.d.ts`, CLI+MCP, **Node ≥22** | `[LIVE]` |
| Yahoo via raw curl | ✅ | ✅ | ✅ | ✅ | ✅ | cookie+crumb dance | — | free | ❌ **429-blocked** | `[BROKEN]` |
| Yahoo via `yfinance` (py) | ✅ | ✅ | ✅ | ✅ | ✅ | auto | — | free | ⭐⭐⭐ pandas, not TS | installed, net blocked |
| **StockAnalysis `__data.json`** | ✅ | ✅ (+adjEps) | ✅ | ❌ | ❌ | **none** | none seen | **free** (2 fwd quarters, then `[PRO]`) | ⭐⭐⭐ needs ~15-line devalue hydrator | `[LIVE]` |
| **Zacks** (HTML scrape) | ✅ | ✅ | ✅ | ✅ **both** | ~ ("Most Recent Consensus") | none | none seen | **free** | ⭐⭐ regex HTML, fragile | `[LIVE]` |
| **Nasdaq `api.nasdaq.com`** | ❌ | ✅ | ✅ | ✅ EPS only | ✅ up/down 4wk | none (**UA header required**) | none seen | **free** | ⭐⭐⭐⭐ plain JSON | `[LIVE]` |
| **Alpha Vantage `EARNINGS_ESTIMATES`** | ✅ | ✅ | ✅ separate | ✅ both | ✅ **best** (7/30/60/90d + up/down) | key | **25 req/day** ☠️ | free / $49.99+ | ⭐⭐⭐⭐ flat JSON, all strings | `[LIVE]` (demo = IBM only) |
| **Seeking Alpha `/api/v3/symbol_data/estimates`** | ✅ | ✅ | — | ❌ | ❌ | **none** | unknown | free, unofficial | ⭐⭐⭐⭐ clean JSON | `[LIVE]` |
| Finnhub **free** | ❌ | ❌ | ❌ | ❌ | ❌ | key | 60/min | free | — | `[LIVE]` 401 + `[DOCS]` |
| Finnhub All-In-One | ✅ | ✅ | ✅ | ✅ | ❌ | key | 300/min | **$3,500/mo** | ⭐⭐⭐⭐ | `[DOCS]` |
| FMP `/stable/analyst-estimates` | ✅ | ✅ | ~ | ~ | ❌ | key | 250/day free | free?/$22+ | ⭐⭐⭐ **v3 = 403 Legacy** | `[LIVE]` 401; tier unverified |
| TipRanks | — | — | — | — | — | Cloudflare | — | — | ❌ | `[BROKEN]` |
| MarketBeat | ❌ gated | ❌ gated | — | — | — | none | — | free | ⭐ | `[LIVE]`, weak |
| simplywall.st / Investing.com | — | — | — | — | — | 403 Cloudflare | — | — | ❌ | `[BROKEN]` |
| WSJ / Barron's | — | — | — | — | — | 401 paywall | — | paid | ❌ | `[BROKEN]` |
| Benzinga / Koyfin | ✅ | ✅ | ✅ | ✅ | ~ | sales-gated | — | enterprise | ❌ | reachability only |

### 3.2 Yahoo — the best free source, but only through the library `[LIVE]`

**Raw curl is dead.** Every request to `query1`/`query2.finance.yahoo.com` returned **HTTP 429 with the plaintext body `Too Many Requests`** — including the full crumb dance (`fc.yahoo.com` → `A3` cookie → `/v1/test/getcrumb`), a fresh consent session, and IP-pinned `--resolve`. The crumb itself came back as the literal string `Too Many Requests`.

**The block is client-fingerprint-based, not IP-based** — `yahoo-finance2` from Node succeeded on the *same machine in the same second*. Yahoo fingerprints TLS/HTTP client behaviour. **Do not hand-roll the crumb dance. Use the library.**

Note `https://fc.yahoo.com/` returns **HTTP 404 but still sets the `A3` cookie** — the 404 is expected and fine.

`yahoo-finance2` **v4.0.2**, published **2026-08-09**, ~197.5k weekly downloads, MIT, actively maintained. **Requires Node ≥ 22** (it warns and still works on 20, but don't risk it). Handles cookies + crumb + consent redirects automatically via a `tough-cookie` jar. Ships a CLI and an MCP server.

```ts
import YahooFinance from "yahoo-finance2";
const yf = new YahooFinance({ suppressNotices: ["yahooSurvey"] });
const r = await yf.quoteSummary("NVDA", {
  modules: ["earningsTrend", "earningsHistory", "calendarEvents", "financialData"],
});
const nextQ = r.earningsTrend.trend.find(t => t.period === "0q")!;
```

**Real NVDA `period: "0q"` payload (`endDate` 2026-07-31)** `[LIVE]`:
```json
"earningsEstimate": {"avg":2.0838,"low":2.03128,"high":2.2,"yearAgoEps":1.05,"numberOfAnalysts":40,"growth":0.9846}
"revenueEstimate" : {"avg":91956584330,"low":90302000000,"high":96655000000,"numberOfAnalysts":43,"yearAgoRevenue":46743000000,"growth":0.96730006}
"epsTrend"        : {"current":2.0838,"7daysAgo":2.08051,"30daysAgo":2.07846,"60daysAgo":2.07667,"90daysAgo":1.9626}
"epsRevisions"    : {"upLast7days":1,"upLast30days":5,"downLast30days":0,"downLast7Days":0,"downLast90days":null}
```

`earningsTrend.defaultMethodology` is `"nongaap"` for NVDA and `"gaap"` for AAPL — **the two tickers are quoted on different bases.** Read this field; don't assume.

Field reality check, confirmed across 4 periods × 2 tickers:

| Field | Populated? |
|---|---|
| `earningsEstimate.{avg,low,high,yearAgoEps,numberOfAnalysts,growth}` | ✅ all |
| `revenueEstimate.{avg,low,high,numberOfAnalysts,yearAgoRevenue,growth}` | ✅ all |
| `epsTrend.{current,7daysAgo,30daysAgo,60daysAgo,90daysAgo}` | ✅ all 5 |
| `epsRevisions.{upLast7days,upLast30days,downLast7Days,downLast30days}` | ✅ |
| `epsRevisions.downLast90days` | ❌ **always `null`** |
| `epsRevisions.upLast90days` | ❌ **absent entirely** |
| revenue revisions | ❌ **do not exist** — revisions are EPS-only |

**Footgun:** `downLast7Days` has a **capital D** in `Days`; every other key uses lowercase `days`. Confirmed in both the TS interface and the live payload.

Periods: `0q`, `+1q`, `0y`, `+1y` (plus `-1q`/`-1y`).

Two more modules worth taking in the same call:
- `calendarEvents.earnings` → `{earningsDate:["2026-08-26T20:00:00.000Z"], isEarningsDateEstimate:false, earningsAverage:2.0838, earningsLow, earningsHigh, revenueAverage, revenueLow, revenueHigh}`. **`isEarningsDateEstimate` is the confirmed/estimated flag §7.5 said nobody has** — NVDA `false`, AAPL `true`. Best available proxy for date confirmation.
- `earningsHistory.history[]` → `{epsActual, epsEstimate, epsDifference, surprisePercent, quarter, period}`. **Your backtest label source.**

**yfinance (Python) 1.6.0**, published 2026-08-13. `Ticker.earnings_estimate` / `.revenue_estimate` / `.eps_trend` / `.eps_revisions` all route through one helper that slices `earningsTrend.trend[:4]` and returns a DataFrame **indexed by `period`** with columns equal to the raw JSON keys above. `.analyst_price_targets` is a **dict, not a DataFrame** (`{high,low,mean,median,current}`). Depends on `curl_cffi` for TLS impersonation — which is exactly why it evades the 429.

### 3.3 StockAnalysis.com — free, no key, S&P Global-sourced `[LIVE]`

**There is no `/api/` endpoint** — `https://stockanalysis.com/api/symbol/s/nvda/...` returns `{"status":404}` on every variant. The real endpoint is the SvelteKit loader:
```
https://stockanalysis.com/stocks/nvda/forecast/__data.json          # 14.0 KB
https://stockanalysis.com/stocks/nvda/financials/__data.json?p=quarterly
```
HTTP 200, no auth, no cookie, browser UA sufficient. `root.estimatesSource === "spg"` → **S&P Global Market Intelligence**, with `trust.freshnessLag: "hours"`.

`estimates.table.quarterly` is **column-oriented parallel arrays** (16 quarters): `dates, fiscalYear, fiscalQuarter, revenue, eps, adjustedEps, analysts, dps, netIncome, grossProfit, grossMargin, operatingIncome, freeCashFlow, peForward, revenueGrowth, epsGrowth, adjustedEpsGrowth, lastDate`. **`lastDate` is the index of the last actual** — everything after it is an estimate.

NVDA `[LIVE]` (`lastDate: 4`):

| date | FY-Q | revenue | eps | adjEps | analysts |
|---|---|---|---|---|---|
| 2026-04-26 | FY2027Q1 | 81,615,000,000 | 2.39 | 1.87 | — (actual) |
| **2026-07-31** | **FY2027Q2** | **91,918,444,790** | 2.05872 | **2.08275** | **43** |
| 2026-10-31 | FY2027Q3 | 103,360,127,970 | 2.34019 | 2.35189 | 41 |
| 2027-01-31 | FY2027Q4 | `"[PRO]"` | `"[PRO]"` | `"[PRO]"` | `"[PRO]"` |

**Gating: exactly 2 forward quarters free**, then the literal string `"[PRO]"`. Two is all you need. **Type your arrays as `(number | "[PRO]" | null)[]`.**

Also free in the same payload: `priceTargets {avg:302.83, median:300, low:180, high:500, numPriceTargets:58}` and `currentRatings {consensus:"Strong Buy", count:61, strongBuy:48, buy:10, hold:2, sell:0, strongSell:1}`.

Missing: no high/low dispersion, no revision history. Pair it with Yahoo.

### 3.4 Zacks — the only free source with revenue high/low `[LIVE]`

`https://www.zacks.com/stock/quote/NVDA/detailed-estimates` → **HTTP 200, 157 KB server-rendered HTML** with a plain browser UA. No login, no JS. Both tables sit in the markup.

NVDA `[LIVE]`:
- **Sales estimates**, current qtr (7/2026): consensus **$91.71B**, **10 estimates**, high **93.07B**, low **90.30B**, year-ago 46.74B, YoY +96.20%
- **Earnings estimates**, current qtr (7/2026): consensus **$2.09**, **12 estimates**, **Most Recent Consensus 2.11**, high **2.13**, low **2.05**, YoY +99.05%

`Most Recent Consensus` vs `Zacks Consensus Estimate` gives you a free **staleness signal**. No official API — regex the HTML. Fragile but zero-auth, and the only free revenue dispersion available.

### 3.5 Alpha Vantage `EARNINGS_ESTIMATES` — best schema, unusable volume `[LIVE]`

```
https://www.alphavantage.co/query?function=EARNINGS_ESTIMATES&symbol=IBM&apikey=demo
```
41 rows for IBM mixing `horizon: "fiscal quarter"` and `"fiscal year"`, **18 fields per row, all populated**:
```json
{"date":"2026-12-31","horizon":"fiscal quarter",
 "eps_estimate_average":"4.6017","eps_estimate_high":"4.7680","eps_estimate_low":"4.4100",
 "eps_estimate_analyst_count":"19.0000",
 "eps_estimate_average_7_days_ago":"4.6017","eps_estimate_average_30_days_ago":"4.5644",
 "eps_estimate_average_60_days_ago":"4.5683","eps_estimate_average_90_days_ago":"4.5564",
 "eps_estimate_revision_up_trailing_7_days":"12.0000","eps_estimate_revision_down_trailing_7_days":null,
 "eps_estimate_revision_up_trailing_30_days":"7.0000","eps_estimate_revision_down_trailing_30_days":"8.0000",
 "revenue_estimate_average":"20476970520.00","revenue_estimate_high":"20713000000.00",
 "revenue_estimate_low":"20120884580.00","revenue_estimate_analyst_count":"16.00"}
```
**Richest schema of any source** — and it returns **~35 historical quarters back to 2017-06-30**, i.e. a ready-made **point-in-time consensus backtest panel**, which is exactly the PEAD / revision-momentum feature set. All values are strings; parse them.

**Killer limit: 25 requests/day**, confirmed verbatim on the premium page. `demo` key works for **IBM only**. Premium starts $49.99/mo.

**Use it once per ticker tonight and cache to disk.** Do not put it in an agent loop.

### 3.6 Seeking Alpha — unauthenticated consensus `[LIVE]`

```
GET https://seekingalpha.com/api/v3/symbol_data/estimates
      ?estimates_data_items=revenue_consensus_mean
      &period_type=quarterly&relative_periods=1&ticker_ids=1150
```
Live for NVDA (`ticker_id=1150`) `[LIVE]`:
```json
{"revenue_consensus_mean":{"1":[{"effectivedate":"2026-08-14T08:54:08.000-04:00",
 "dataitemvalue":"91956584330.0",
 "period":{"fiscalquarter":2,"fiscalyear":2027,"periodenddate":"2026-07-31"}}]}}
```
Swap `revenue_consensus_mean` → `eps_normalized_consensus_mean` for EPS. `relative_periods=1` is next quarter. **Note it returns `91956584330.0` — byte-identical to Yahoo's `revenueEstimate.avg`**, so it is the same underlying feed, not an independent check. Undocumented, ToS prohibits scraping. Demo-grade with a fallback.

### 3.7 The two providers that do NOT work free

**Finnhub free tier is useless for this task.** Pricing page has only Free ($0) and All-In-One ($3,500/mo). The free column has content for *EPS Surprises* ("4 quarters") and *Earnings Calendar* ("1 month, US"), and is **empty** for **EPS Estimates**, **Revenue Estimates**, and every other estimate row. Corroborated by Finnhub staff: *"If you are encountering 403 error, it means the data is not part of your access."* Their OpenAPI spec (`https://finnhub.io/static/swagger.json`, 588 KB, 116 paths) contains **no premium markers** — do not infer tiering from it. It is still useful for `openapi-typescript` codegen if you pay.

**FMP — two traps.**
1. **`/api/v3/` is dead for new accounts.** Accounts created after **2025-08-31** get **HTTP 403 `Legacy Endpoint`** on every `/api/v3/*` call. Use `/stable/` with the symbol as a **query param**:
```
❌ https://financialmodelingprep.com/api/v3/analyst-estimates/NVDA?period=quarter&apikey=…
✅ https://financialmodelingprep.com/stable/analyst-estimates?symbol=NVDA&period=quarter&page=0&limit=10&apikey=…
```
**This will silently eat your time if you copy a pre-2025 tutorial.**
2. Free tier = 250 calls/day, EOD only, 5 years, 500 MB/30-day bandwidth cap, US-only. **Whether `analyst-estimates` is free-tier accessible in 2026 could not be confirmed** — the plan matrix uses opaque markers. No evidence of an AAPL-only allowlist.

Register a key tonight and probe `/stable/analyst-estimates?symbol=NVDA&period=quarter` first thing. If it 402/403s you've lost nothing.

### 3.8 Cross-source sanity check — the number you must beat `[LIVE]`

**NVDA, quarter ending 2026-07-31, reports 2026-08-26:**

| Source | Revenue consensus | EPS consensus | n (EPS) | Basis |
|---|---|---|---|---|
| Yahoo `earningsTrend` `0q` | **$91.957B** (low 90.302 / high 96.655, n=43) | **$2.0838** (low 2.031 / high 2.20) | 40 | non-GAAP |
| StockAnalysis (S&P Global) | **$91.918B** | 2.05872 / **adjEps 2.08275** | 43 | both |
| Zacks direct | **$91.71B** (low 90.30 / high 93.07, n=10) | **$2.09** (low 2.05 / high 2.13; "most recent" 2.11) | 12 | Zacks adj |
| Nasdaq (Zacks-fed) | — | **$2.01** (low 1.97 / high 2.05) | 11 | Zacks adj |

Revenue agrees to **±0.27%** across four independent feeds — that number is solid. EPS clusters at **~$2.08**.

⚠️ **Nasdaq's 2.01 is a stale vintage of the same Zacks feed.** Zacks' own page says 2.09 with low 2.05 — so **Nasdaq's number sits below Zacks' own stated low**. Nasdaq's `asOf` field is `null`, so you cannot detect this from the payload. **Do not use Nasdaq as your primary consensus benchmark** — use it for revision counts and surprise history only.

**AAPL, quarter ending 2026-09-30** (`isEarningsDateEstimate: true`): revenue **$113.551B** (low 112.137 / high 117.220, n=28), EPS **$1.9766** (low 1.93 / high 2.07, n=28), **GAAP basis**. Yahoo and StockAnalysis agree to 6 significant figures. AAPL's `epsRevisions` are net-negative and 30-day-ago EPS was 2.00825 vs 1.97656 now — estimates drifting down.

### 3.9 Recommendation

1. **`yahoo-finance2@4` as primary** (Node ≥22). Free, TS-native, zero auth code, and the only free source carrying revenue high/low *and* EPS revision history in one request.
2. **StockAnalysis `__data.json` as the independent cross-check** — genuinely different vendor lineage (S&P Global). Disagreement between the two is real signal.
3. **Zacks scrape** when you need revenue dispersion (high/low), which nothing else gives free.
4. **Nasdaq** for revision counts and surprise history only — **never as the benchmark**.
5. **Alpha Vantage `EARNINGS_ESTIMATES` once per ticker tonight**, cached, as your point-in-time backtest panel.
6. **Whichever you pick, record the vendor and the GAAP/non-GAAP basis alongside the number.** The 2.01-vs-2.09 spread is 4% — larger than most real forecast edges.

---

## 4. Structured fundamentals APIs (historical quarterly financials)

EDGAR is the source of truth but gives you *as-reported* XBRL: no normalization, no margins, no TTM, no per-share derivations, no segment convenience, and a tag-fallback problem per company. These providers add that layer.

### 4.1 Comparison

| Provider | Free quarterly income stmt | Segments | Free history | Auth | Free limits | TS/HTTP ergonomics | Usable 9am with no signup? | Status |
|---|---|---|---|---|---|---|---|---|
| **stockanalysis.com `__data.json`** | **42 line items** | **Yes** | 20 quarters | none | none observed | REST + ~20-line devalue decoder | **Yes** | `[LIVE]` |
| **Yahoo `fundamentals-timeseries`** | ~40 `quarterly*` types | no | 5+ yrs | none | **aggressive 429s** | clean REST | Yes, with retry | `[LIVE]` |
| **api.nasdaq.com** | no full statements | no | — | none (needs UA + Referer) | none observed | clean REST | Yes | `[LIVE]` |
| SEC EDGAR companyfacts | as-reported XBRL | no (see §1.8) | full history | UA header | 10 req/s | REST | Yes — your backbone | `[LIVE]` |
| Alpha Vantage | `INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`, `EARNINGS` | no | ~5 yrs quarterly | `?apikey=` | **25 req/day** | REST | signup | `[LIVE]` via `demo` key |
| FMP | yes on free tier | no | **5 yrs, US only** | `?apikey=` | 250 calls/day, 500 MB/30d | REST | signup | `[DOCS]` |
| Finnhub `/stock/financials-reported` | as-reported SEC mirror | no | — | `?token=` | 60/min | official TS SDK | signup | `[DOCS]` |
| **Tiingo** | **paid add-on** | no | **DOW 30 only, 3 yrs** | Bearer | 50/hr, 500 sym/mo | REST | **No** | `[DOCS]` |
| **Polygon.io** | **paid — $29/mo standalone** | no | — | `?apiKey=` | free tier excludes financials | official TS SDK | **No** | `[LIVE]` 401 |
| EODHD | gated | no | **free = past year only** | `?api_token=` | **20/day** | REST | marginal | `[LIVE]` via `demo` |
| Twelve Data | fundamentals paid | no | — | `?apikey=` | 800/day (prices only) | REST | No | `[LIVE]` 403 |
| SimFin | alive; bulk CSV | no | 20 yrs | Bearer | signup, no card | REST | signup | `[LIVE]` 401 |
| Sharadar SF1 (Nasdaq Data Link) | paid | — | — | key | — | REST | No | `[LIVE]` 403 |
| Intrinio | **$150/mo minimum** | yes | — | key | nothing free | SDK | **No** | `[DOCS]` |
| Marketstack / sec-api.io | key required | — | — | key | — | REST | No | `[LIVE]` |

### 4.2 Three traps, all confirmed

1. **Tiingo fundamentals are still DJIA-only.** Docs verbatim: fundamentals are *"an add-on subscription. The DOW 30 are available for free/evaluation"* — 3 years, 30 tickers. Do not build on it.
2. **Polygon `/vX/reference/financials` is no longer free.** Financials & Ratios now sits under Stocks Advanced ($199/mo) or a $29/mo standalone. The free Stocks Basic tier (5 req/min) excludes it. Tested → 401.
3. **Alpha Vantage is still 25 requests/day.** That is ~6 tickers/day at 4 calls each — far too thin for an agent loop that retries.

Also: **FMP's `v3/` base is legacy**; `stable/` is current. Free tier is 250 calls/day, US-only, 5 years of history.

### 4.3 The best free source: stockanalysis.com internal JSON `[LIVE]`

```
https://stockanalysis.com/stocks/nvda/financials/income-statement/__data.json?p=quarterly
https://stockanalysis.com/stocks/nvda/financials/balance-sheet/__data.json?p=quarterly
https://stockanalysis.com/stocks/nvda/financials/cash-flow-statement/__data.json?p=quarterly
```
No key. Send a browser `User-Agent`. Confirmed independently: HTTP 200, 9.4 KB gzipped.

42 income-statement fields: `revenue, cor, gp, sgna, rnd, opex, opinc, interestExpense, pretax, taxexp, netinc, netinccmn, sharesBasic, sharesDiluted, epsBasic, epsdil, fcf, ebitda, ebit, grossMargin, operatingMargin, taxrate, …` — 55 on the balance sheet, 20 quarters deep, and **already tagged with `fiscalYear` / `fiscalQuarter`**, which solves NVDA-style off-calendar fiscal years for free.

Real NVDA quarterly series pulled `[LIVE]`:
```
2026-04-26  FY2027 Q1   $81.615B   EPSdil 2.39   EBITDA 54.533B
2026-01-25  FY2026 Q4   $68.127B   EPSdil 1.762
2025-10-26  FY2026 Q3   $57.006B   EPSdil 1.30
2025-07-27  FY2026 Q2   $46.743B   EPSdil 1.08
2025-04-27  FY2026 Q1   $44.062B   EPSdil 0.76
```
**Segment data included free** `[LIVE]` ($M):
```
compute_and_networking_revenue: [74550, 61651, 50908, 41331, 39589, ...]
graphics_revenue:               [ 7065,  6476,  6098,  5412,  4473, ...]
```

**Format gotcha:** it's a SvelteKit **devalue** payload, not plain JSON — a flat `nodes[].data` array where object values are *integer pointers into that same array*. Decoding is ~20 lines: walk the pointer graph recursively. A working Python decoder is at `scratchpad/devalue.py`; port it to TS first thing.

### 4.4 Yahoo — one important gotcha `[LIVE]`

`yahoo-finance2` v4.0.2 (published 2026-08-09, actively maintained, TS-native, **requires Node ≥ 22**) emits this warning itself:

> "QuoteSummary financial statements submodules like incomeStatementHistoryQuarterly have provided almost no data since Nov 2024. Use `fundamentalsTimeSeries` instead."

So skip `quoteSummary` for statements entirely. The raw endpoint that does work:
```
https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/NVDA
  ?symbol=NVDA&type=quarterlyTotalRevenue,quarterlyDilutedEPS&period1=1400000000&period2=1800000000
```
Returned `2025-04-30: 44.06B, 2025-07-31: 46.74B, 2025-10-31: 57.01B` `[LIVE]`. **But most follow-up calls returned HTTP 429**, including the crumb endpoint. Yahoo rate-limits datacenter/VPN IPs hard. Treat Yahoo as a fallback, cache to disk on first success, and never put it on the critical path of a live demo.

### 4.5 Recommendation

- **Primary: SEC EDGAR companyfacts + stockanalysis.com `__data.json`.** EDGAR for audited as-reported truth and the audit trail judges will care about; stockanalysis for normalization, margins, per-share, and segments in one call. Neither needs a key, so nothing can fail at 09:00 because a signup email didn't arrive.
- **Fallback: Yahoo `fundamentals-timeseries`** (cache aggressively, expect 429).
- **Optional third cross-check if someone registers tonight: FMP free (250/day)** — the only keyed provider whose free tier actually serves useful quarterly statements.
- **Do not plan around** Tiingo, Polygon, Intrinio, or Alpha Vantage.

---

## 5. Management guidance

**This is where the edge is.** Guidance is the single strongest predictor of next-quarter results, and — critically — **no free structured guidance dataset exists anywhere.** Extracting structured guidance from 8-K EX-99.1 and transcripts with an LLM is genuinely un-commoditized. Lean into it as the differentiator rather than treating it as plumbing.

### 5.1 Primary path: SEC 8-K EX-99.1 `[LIVE end to end]`

```
1. submissions.json  →  filter form=="8-K" && items ∋ "2.02"
2. {BASE}/index.json →  list exhibit files   (NOT {accession}-index.json — that 404s)
3. fetch the EX-99.1 press release
4. anchor on "Outlook" / "we expect", take the next ~1,500 chars
5. LLM-extract to {metric, min, max, point, period, basis: GAAP|non-GAAP}
```
Filenames are **company-specific and unpredictable** (`q1fy27pr.htm` vs Apple's `a8-kex991q3202606272026.htm`), so you must list the directory — you cannot construct the path.

**Resolving which file is EX-99.1 — the elegant trick:** EDGAR full-text search returns the exhibit type and filename directly `[LIVE]`:
```
https://efts.sec.gov/LATEST/search-index?q=%22second+quarter+of+fiscal+2027%22&forms=8-K&startdt=2026-05-01&enddt=2026-05-31
```
```json
{"_id":"0001045810-26-000051:q1fy27pr.htm",
 "_source":{"file_type":"EX-99.1","file_description":"EX-99.1","form":"8-K",
            "items":["2.02","9.01"],"file_date":"2026-05-20"}}
```
`_id` is literally `{accession}:{filename}`. Exhibits resolve back to ~2003 this way; FTS coverage starts 2001.

Regex anchors that work: `outlook for`, `is expected to be`, `we expect`, `we now expect`, `guidance`, `plus or minus`, `in the range of`.

### 5.2 ⚠️ The critical gotcha — many issuers put NO guidance in the 8-K `[LIVE]`

Apple's most recent earnings exhibit:
```
https://www.sec.gov/Archives/edgar/data/320193/000032019326000018/a8-kex991q3202606272026.htm
```
10,456 chars extracted. Occurrence counts: **`outlook` = 0, `guidance` = 0, `we expect` = 0, `expects` = 0.** The press release reports results only.

**Apple's guidance is spoken by the CFO on the call and exists nowhere in the filings** `[LIVE]`:
> "We also expect our September quarter total company revenue to be impacted by two main factors. First, we expect foreign exchange to be a sequential headwind of about 2.5 percentage points… **We expect gross margin to be between 47% and 48%**… **We expect operating expenses to be between $19.1 billion and $19.4 billion.** We expect OINE to be around $350 million… and our tax rate to be around 16.5%."

**Architectural consequence: your agent needs BOTH paths.** Try EX-99.1 → EX-99.2 first (structured, precise, license-clean); fall back to the transcript CFO block when the exhibit yields nothing. Apple is not an edge case — it's a large share of megacaps, and Apple gives **no explicit revenue number at all**, only growth-rate colour, which your model must handle.

### 5.3 Priority order

**EX-99.1 → EX-99.2 → transcript CFO block → IR deck.**

EX-99.2 is underrated: NVDA files `q1fy27cfocommentary.htm` (165 KB) every quarter — effectively written prepared remarks, filed with the SEC, **free and license-clean** (public domain). Several large caps do this.

IR decks are usually **not** SEC-filed. Best programmatic location is the Q4 Inc CDN, which is static and curl-friendly:
```
https://{ticker}.q4cdn.com/{account_id}/files/doc_financials/{YYYY}/q{N}/....pdf
```
Decks are lower-value than the press release — they typically restate the same numbers with more visual framing.

### 5.4 Transcript Q&A phrasings worth matching

Guidance clusters in the **CFO's closing prepared-remarks block**, just before the operator opens Q&A.

- *Point/range:* `revenue is expected to be $X`, `we expect revenue (of|to be) (between|in the range of)`, `plus or minus N%`, `we are guiding to`, `our outlook for the {next} quarter`, `we anticipate`
- *Revisions — high signal:* `we are raising our full-year`, **`we now expect`** (the "now" is the tell), `updated guidance`, `reaffirming`, `narrowing our range`, `withdrawing guidance`
- *Q&A hedges — softer, but where the real information leaks:* `we're not guiding to that specifically, but`, `directionally`, `embedded in our guidance is`, `what's contemplated in the guide`, `we've assumed`, `conservatism in the guide`

**Capture the assumptions attached to guidance, not just the number.** NVDA's "NVIDIA is not assuming any Data Center compute revenue from China in its outlook" is exactly the clause that determines whether the number is beatable. The CFO's *refusal pattern* in Q&A is itself signal.

### 5.5 Structured guidance vendors — paid only

| Vendor | Guidance product | Free? | Notes |
|---|---|---|---|
| **Benzinga** | ✅ purpose-built API | ❌ | Cheapest real option; ideal schema |
| **FMP** | ❌ **none** (analyst estimates only) | — | See warning below |
| **Finnhub** | ❌ none | — | No transcripts even at $3,500/mo |
| Estimize | crowdsourced *estimates*, not guidance | ❌ | Largely wound down — do not build on it |
| Wall Street Horizon (TMX) | event/date data, guidance flags | ❌ | Enterprise |
| Visible Alpha | consensus + guidance, deep detail | ❌ | Enterprise |
| LSEG/Refinitiv I/B/E/S | Company Guidance database | ❌ | Enterprise |
| Bloomberg BEst | guidance in terminal | ❌ | ~$30k/yr/seat |
| FactSet StreetAccount | guidance summaries | ❌ | Enterprise |

**Benzinga Guidance API** `[LIVE auth test / DOCS schema]` — no token → HTTP 401; `token=demo` → access denied. No free access. But the schema is exactly what a forecasting agent wants:
```
GET https://api.benzinga.com/api/v2.1/calendar/guidance?token={KEY}&parameters[tickers]=NVDA
eps_guidance_min/_max/_est        revenue_guidance_min/_max/_est
eps_guidance_prior_min/_max       revenue_guidance_prior_min/_max
eps_type (GAAP|Adjusted)          period (Q1..Q4|FY), period_year
is_primary (Y/N)                  confirmed (Y/N)
```
`confirmed=Y` = official disclosure; `N` = Benzinga's expected pre-announcement. Prior-vs-current fields give raise/lower/reaffirm for free.

⚠️ **FMP has NO management-guidance endpoint.** Common confusion worth flagging: FMP's `/stable/analyst-estimates` and `/stable/financial-estimates` are **sell-side consensus, not company-issued guidance.** Their own docs draw the distinction and their recommended guidance workflow is literally *"use NLP or keyword parsing"* on their transcript API — i.e. **they expect you to extract it yourself.**

**Free structured-guidance datasets: none found.** HuggingFace and Kaggle searches surfaced transcript corpora but **zero guidance-labelled datasets** — no min/max/period-tagged guidance corpus exists publicly. That gap is your opportunity.

---

## 6. Alternative data — free and wireable in one day

### 6.1 Tier 1 — wire these first (all confirmed working tonight, <15 min each)

#### FRED **without an API key** `[LIVE]`
The documented `api.stlouisfed.org` path 400s without a key, but the chart CSV endpoint needs nothing at all:
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}
```
All nine tested returned current data `[LIVE]`:
```
RSXFS   2026-07  660047     UMCSENT  2026-06  49.5      ECOMSA   2026-01  326740
INDPRO  2026-06  102.6395   DGORDER  2026-06  335418    PCE      2026-06  22184.1
HOUST   2026-06  1427       TOTALSA  2026-07  16.782    GASREGW  2026-08-10  4.006
```
Sector map:

| Sector | Series |
|---|---|
| Retail / consumer goods | `RSAFS`, `RSXFS`, `ECOMSA` (e-commerce), `RSEAS` |
| Autos | `TOTALSA`, `ALTSALES` |
| Semis / tech / industrial | `INDPRO`, `DGORDER`, `AMTMNO` |
| Housing / building products | `HOUST`, `PERMIT`, `MORTGAGE30US` |
| Energy | `GASREGW`, `DCOILWTICO` |
| Consumer health | `UMCSENT`, `PCE`, `PSAVERT`, `REVOLSL` |
| Labour (weekly!) | `ICSA` (initial claims), `PAYEMS` |
| Inflation pass-through | `CPIAUCSL`, `PPIACO` |

Still grab a free instant FRED key tonight as a backup for programmatic metadata/search.

#### Wikipedia pageviews — your Google Trends replacement `[LIVE]`
```
https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{Article}/daily/{YYYYMMDD}/{YYYYMMDD}
https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{Y}/{M}/{D}
```
No key. Set a descriptive `User-Agent` (policy requirement), ~100 req/s tolerated. Nvidia daily, Aug 2026 `[LIVE]`: `4803, 4269, 4849, 4387, 4081, 4096, 3863, 3517`.

Use the `user` agent segment to strip bots. **Point it at product pages, not just company pages** (`IPhone_17`, `Cybertruck`, `Grand_Theft_Auto_VI`) — product attention is a far better demand proxy than corporate-entity attention. This is strictly better than Google Trends right now: same signal class, no token dance, no blocking.

#### Greenhouse / Ashby / Lever public job boards — hiring as an expansion signal `[LIVE]`
```
https://boards-api.greenhouse.io/v1/boards/{company}/jobs     # no auth, clean JSON, updated_at per role
https://api.ashbyhq.com/posting-api/job-board/{company}
https://api.lever.co/v0/postings/{company}
```
Live counts `[LIVE]`: stripe **578**, datadog **425**, airbnb **186**, coinbase **167**.

Caveat that matters: you get a **snapshot**, not a series. In one day you cannot compute deltas. Use *absolute counts normalised by headcount* and *role mix* (e.g. count of "Account Executive" / "Sales" postings as a capacity proxy) cross-sectionally against peers, or snapshot repeatedly through the day if the target is fast-moving.

#### TSA checkpoint volumes — airlines and travel `[LIVE]`
```
https://www.tsa.gov/travel/passenger-volumes     # HTTP 200, 181 KB, 226 parseable table rows
```
Daily and current `[LIVE]`: `8/13/2026 → 2,708,863 · 8/12 → 2,350,055 · 8/11 → 2,238,634 · 8/10 → 2,690,569 · 8/9 → 2,855,622`. Plain regex over `<tr>/<td>`. Needs a browser UA. Directly relevant to DAL, UAL, AAL, LUV, ABNB, BKNG, EXPE, HLT, MAR.

#### App store `[LIVE]`
| Endpoint | Result |
|---|---|
| `https://rss.marketingtools.apple.com/api/v2/us/apps/top-free/25/apps.json` | 25 apps, timestamped "Sat, 15 Aug 2026 22:26:12 +0000", #1 "7 Brew Coffee" |
| `.../top-paid/25/apps.json` | works (#1 Shadowrocket) |
| `.../top-grossing/...` | **BROKEN** — no `feed` key in the response |
| `https://itunes.apple.com/lookup?id={id}&country=us` | Robinhood: `userRatingCount` **4,801,014**, rating 4.286, v2026.32.0, released 2026-08-11 |
| `https://itunes.apple.com/us/rss/customerreviews/id={id}/sortBy=mostRecent/page=1/json` | 50 reviews with per-review rating + date |

**The reviews RSS is the one that works in a single shot** — recent-review rating trend and volume need no second snapshot. `userRatingCount` deltas are a legitimate download proxy but require two observations, so today's absolute count only helps cross-sectionally. Google Play: `google-play-scraper` npm **v10.1.3, published 2026-05-31 — actively maintained**.

#### Others confirmed working `[LIVE]`
| Source | Endpoint | Result |
|---|---|---|
| HN Algolia | `hn.algolia.com/api/v1/search_by_date?query=X&tags=story` | 10,430 hits for "nvidia", free, no key |
| Bluesky | **`api.bsky.app`**`/xrpc/app.bsky.feed.searchPosts` | works — ⚠️ `public.api.bsky.app` **403s** |
| FINRA RegSHO | `cdn.finra.org/equity/regsho/daily/CNMSshvol{YYYYMMDD}.txt` | daily short volume, all tickers, pipe-delimited |
| BLS v2 | POST `api.bls.gov/publicAPI/v2/timeseries/data/` | **no key needed** (25 req/day unregistered) |
| Steam | `api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=` | CS2 = 809,567 live players |
| Tranco | `tranco-list.eu/api/lists/date/2026-08-10` | free domain rankings |
| SEC Form 4 / 13F | via submissions API (§1.2) | insider + institutional flows, free |

### 6.2 Tier 2 — free but needs a token you should grab tonight (2 min each)

**Cloudflare Radar** — the only real Similarweb substitute. Genuinely free, CC BY-NC 4.0, gives domain rankings and traffic trends. Needs a Cloudflare account → Custom API Token with `Account > Radar > Read`. `[DOCS]`
Also: FRED, EIA (`API_KEY_MISSING` without one `[LIVE]`), Census MARTS (`Missing Key` `[LIVE]`), Finnhub, FMP.

### 6.3 Tier 3 — dead, blocked, or paywalled. Do not burn time.

| Source | Status |
|---|---|
| **Google Trends** | 429 on the token dance `[LIVE]`. **`pytrends` archived 17 Apr 2025** — dead. `google-trends-api` npm last published **2020** — abandoned. The official Google Trends API is an **application-gated alpha since Jul 2025**, no self-serve. A workaround exists (warm `NID` cookie via `/_/TrendsUi/data/batchexecute`, then explore→widgetdata ~800 ms apart) and **`trendspyg` v1.5.0 (11 Aug 2026) is maintained** — but the limit follows your IP, ~10–15 requests before death. **Use Wikipedia pageviews instead.** |
| **Yahoo Finance** | 429 on both `query1`/`query2` from datacenter IPs; needs crumb+cookie. May work from a laptop on venue wifi — do not depend on it `[LIVE]` |
| **StockTwits** | Cloudflare challenge — blocked `[LIVE]` |
| **pullpush.io** (Pushshift mirror) | Returns `"This website does not provide free scraping resources for agents"` — dead for us `[LIVE]` |
| **Stooq** | JS proof-of-work challenge — blocked `[LIVE]` |
| **Reddit API** | Free tier 100 QPM/OAuth client post-2023; Pushshift proper is academic-only `[DOCS]` |
| **X/Twitter** | $100/mo Basic minimum `[DOCS]` |
| **Similarweb** | No free API. Credit model, sales-contact only `[DOCS]` |
| **Credit-card panel data** | Second Measure/Bloomberg, Yipit, Facteus, Consumer Edge, Earnest Analytics — **all institutional, six-figure, sales-gated. Not obtainable in a day. No free proxy exists.** `[DOCS]` |
| **Satellite** | Orbital Insight / RS Metrics / SpaceKnow paywalled `[DOCS]`. Free imagery does exist (Sentinel Hub, NASA Earthdata, Planet research tier) but **parking-lot counting is not feasible in a day**: you need cloud-free revisits over exact store footprints, a georeferenced store list, a trained detector, and a multi-year baseline to de-trend. Skip and say why if a judge asks. |
| **Indeed / LinkedIn / Glassdoor** | API discontinued / blocked / blocked. Use Greenhouse+Ashby+Lever instead `[DOCS]` |

### 6.4 Honest framing for the judges

Alt data will not move your point estimate much in one day — you have no time series, so most of these are cross-sectional snapshots. Their real value tomorrow is **narrative and confidence-interval width**: "TSA volumes are running +5% YoY, so we sit at the top of DAL's guidance range." Use them to justify *where inside the guidance band* you land, not to override the fundamentals.

---

## 7. Earnings calendar — who reports when

### 7.1 Best free source: stockanalysis.com, one request `[LIVE]`

```
https://stockanalysis.com/stocks/earnings-calendar/__data.json
```
647 KB decoded / 242 KB on the wire, **4,918 symbol-events across 75 days** (2026-06-15 → 2026-09-25), one call, no auth. Per symbol: `s` ticker, `n` name, `t` **bmo/amc**, `e` **EPS estimate**, `r` **revenue estimate**, `eg`/`rg` YoY growth %, `m` market cap.

Live sample `[LIVE]`:
```json
{"s":"NVDA","n":"NVIDIA","t":"amc","e":2.07,"r":91818878592,"eg":99.04,"rg":96.43}
{"s":"WMT","t":"bmo","e":0.74,"r":186817890432}
{"s":"CRM","t":"amc","e":3.09,"r":11311783680}
```
That `r` field means this single endpoint doubles as a **revenue consensus** source (§3). Caveat: no confirmed/estimated flag — only bmo/amc.

### 7.2 Richest per-ticker detail: `api.nasdaq.com` `[LIVE]`

No auth. Requires a browser `User-Agent` **and** `Referer: https://www.nasdaq.com/` — it 403s without them.

| Endpoint | Returns |
|---|---|
| `/api/calendar/earnings?date=2026-08-26` | 36 rows: `time` (`time-pre-market`/`time-after-hours`), `epsForecast`, `noOfEsts`, `fiscalQuarterEnding`, `lastYearRptDt`, `lastYearEPS`, `marketCap` |
| `/api/analyst/{sym}/earnings-date` | prose + `announcement` string |
| **`/api/analyst/{sym}/earnings-forecast`** | consensus / high / low EPS, # estimates, **revisions up/down last 4 weeks**, next 4 quarters |
| `/api/quote/{sym}/eps` | consensus vs actual per quarter |
| `/api/company/{sym}/earnings-surprise` | historical surprise % |

Live NVDA calendar row `[LIVE]`:
```json
{"symbol":"NVDA","time":"time-after-hours","epsForecast":"$2.01","noOfEsts":"11",
 "fiscalQuarterEnding":"Jul/2026","lastYearRptDt":"8/27/2025","lastYearEPS":"$0.99"}
```

Full `/earnings-forecast` payload, re-verified independently `[LIVE]`:
```json
{"fiscalEnd":"Jul 2026","consensusEPSForecast":2.01,"highEPSForecast":2.05,"lowEPSForecast":1.97,"noOfEstimates":11,"up":1,"down":0}
{"fiscalEnd":"Oct 2026","consensusEPSForecast":2.24,"highEPSForecast":2.34,"lowEPSForecast":2.05,"noOfEstimates":11,"up":1,"down":0}
{"fiscalEnd":"Jan 2027","consensusEPSForecast":2.48,"highEPSForecast":2.65,"lowEPSForecast":2.01,"noOfEstimates":10,"up":1,"down":0}
```
Consensus + dispersion + analyst count + revision momentum, four forward quarters, no key. Revision momentum (up/down counts over 4 weeks) is a well-documented predictor of surprise direction — cheap alpha for the model.

⚠️ **But do not use Nasdaq's consensus as your benchmark.** Cross-checking in §3.8 showed its NVDA EPS of 2.01 is a **stale vintage of the Zacks feed** — Zacks' own page currently says 2.09 with a stated *low* of 2.05, so Nasdaq's number sits below Zacks' own range. `asOf` is `null`, so staleness is undetectable from the payload. Use Nasdaq for **revision counts, surprise history, and date/session confirmation**; take the benchmark number from Yahoo or StockAnalysis.

### 7.3 Ground truth: SEC 8-K Item 2.02 `[LIVE]`

Filter submissions for `form=="8-K" && items.includes("2.02")` → NVDA's actual historical release dates:
```
2026-05-20, 2026-02-25, 2025-11-19, 2025-08-27, 2025-05-28, 2025-02-26, 2024-11-20, 2024-08-28
```
Backward-looking only, but the **only unimpeachable release-date series** — use it to label training data and sanity-check forward calendars (flag if a forward date is >10 days off the prior-year anniversary).

### 7.4 Others tested

| Source | Verdict |
|---|---|
| **FMP `/earning_calendar`** | **Paid-only.** FMP FAQ verbatim: *"some endpoints only accessible via paid subscriptions such as earning calendar"* `[DOCS]` |
| Finnhub `/calendar/earnings` | Free tier: 1 month forward, US, real-time updates. But inline EPS/revenue **estimates** are All-In-One ($3,500/mo) only `[DOCS]` |
| Earnings Whispers | Has a genuine "Only Confirmed Dates" filter — but needs an account + cookies `[LIVE]`, gated |
| Yahoo `calendarEvents` / `.earnings_dates` | 429-blocked from datacenter IPs; unreliable |
| Wall Street Horizon | Paid, enterprise. *The* real confirmed-date vendor; nothing free matches it |
| EODHD `/calendar/earnings` | 403 on demo; paid add-on |

### 7.5 Confirmed vs estimated — the honest answer

**Almost none of the dedicated calendar sources flag confirmed vs estimated.** Tested directly: Nasdaq returns identical `"expected*"` boilerplate for WMT (reporting in 5 days), NVDA, TGT and CRM. The asterisk is a footnote marker, not a status field.

**The one exception is Yahoo** — `calendarEvents.earnings.isEarningsDateEstimate` is a real boolean `[LIVE]`: `false` for NVDA (2026-08-26 confirmed), `true` for AAPL. It comes free in the same `quoteSummary` call you're already making for consensus (§3.2), so take it from there. It's the best single signal available, but Yahoo is 429-prone from datacenter IPs, so still corroborate.

The general substitute is **cross-source agreement**, validated end to end `[LIVE]`:

| Source | NVDA date | Session | EPS est |
|---|---|---|---|
| stockanalysis.com | 2026-08-26 | amc | 2.07 |
| Nasdaq calendar | 2026-08-26 | after-hours | 2.01 (11 ests) |
| Nasdaq analyst | 08/26/2026 | after market close | 2.01 (Zacks) |
| SEC 8-K prior year | 2025-08-27 | — | — |

Date and session agree 3/3; the prior-year 8-K lands within one day; Yahoo independently reports `isEarningsDateEstimate: false`. **Treat Yahoo's flag plus 2-source date+session agreement as "confirmed".**

**Note the EPS spread: 2.01 vs 2.07.** Different vendors (Zacks vs S&P Global / Refinitiv). Pick one consensus vendor and stay consistent, or your surprise calculation is noise. See §3.

---

## 8. OpenStocks and the event itself

### 8.1 Three corrections to the brief

1. **The event is Sunday 16 August 2026, not Saturday.** 16 Aug 2026 is a Sunday (verified by date arithmetic; 15 Aug is the Saturday). The page header says **9AM–8PM BST**; body text says 9am–7pm.
2. **No OpenAI involvement found anywhere.** The event is presented by **Primer · OpenStocks · AI Tinkerers** — that exact string appears on both the event page and openstocks.com. OpenAI appears only in AI Tinkerers' org-wide "Trusted By" list, not on this event. **Do not plan around OpenAI credits.**
3. **Primer is almost certainly `primer.io`** — the London payments-infrastructure company (founded 2020, ~138 employees, $173.4M raised, 154 Bishopsgate). Title tag: "Unified intelligence for payments | Primer". `primer.vc` resolves but serves an empty body. Not primer.ai (US NLP/defense).

### 8.2 What OpenStocks actually exposes — nothing, yet

`https://openstocks.com` is live (Next.js/turbopack). Tagline: **"Where AI Agents Forecast Earnings"**. It links straight to `https://london.aitinkerers.org/p/agents-vs-wall-street-10k`.

**There is NO public API, NO docs, NO SDK, NO MCP server, NO npm package** `[LIVE]`:
- `/docs`, `/developers`, `/mcp`, `/blog`, `/leaderboard`, `/agents`, `/pricing`, `/hackathon` all return **HTTP 200 but serve the identical landing page** — a Next.js catch-all, not real pages. Verified by diffing extracted text. **Do not be fooled by the 200s.**
- `/api`, `/api/v1`, `/api/docs`, `/llms.txt`, `/openapi.json`, `/robots.txt`, `/sitemap.xml`, `/.well-known/mcp` → **404**
- npm: `openstocks` 404, `@openstocks/sdk` 404, registry search "openstocks" → **0 results**
- Only two real pages exist: **`/manifesto`** and **`/prize-rules`**
- Site says **"Doors open August 16"** — the product launches *at* the hackathon. Expect credentials handed out in the room.

Operator: **Kernel AI Ltd**, UK company **15117085**, incorporated 5 Sep 2023, 128 City Road London EC1V 2NX. PSC/director **Sebastian Hugh Richard Jory**. Contacts `hello@openstocks.com`, `prizes@openstocks.com`.

### 8.3 The prize rules — read these, they should shape the architecture

From `openstocks.com/prize-rules` (v2026-08-08-v5) `[LIVE]`:

- **Scoring is percentage distance, not absolute.** "closeness is the percentage distance between a forecast's value … and the reported actual value, compared against the Wall Street consensus value OpenStocks records."
- **You must beat consensus to win anything.** "A potential winner is selected only from scored forecasts that are closer to the actual result than that Wall Street consensus value." If nobody beats the Street in a round, **no prize is awarded**.
- **One named metric per prize event** — revenue *or* EPS, labelled per event. Other metrics are scored but don't enter that round.
- **Ties break by earlier submission.** Submit early.
- **Scoring uses results as first reported** — restatements don't change awards. Model the **headline reported number**, not the restated one. (This aligns with using EX-99.1 as truth, not the later 10-Q.)
- Three submission types (I re-read the page directly to pin these down):
  - **Official** — OpenStocks' own forecasts. **Ineligible for prizes.**
  - **Community Workbook** — .xlsx upload; must complete in-product review and be published.
  - **Verified GitHub** — **the repository commit must complete OpenStocks' hosted verification**, i.e. they run your exact commit.
- Prize rounds: $100 each, max 20 events, $2,000 total — **separate from** the hackathon's $10,000 pot.

**Architectural implication:** build a **clean, runnable GitHub repo with a deterministic entrypoint and pinned dependencies**. The Community Verified path requires OpenStocks to execute your exact commit — an agent that only runs on your laptop with hand-fed data cannot be verified and is ineligible for ranked prizes. **Vendor/cache your data pulls into the repo** so a cold run is reproducible without your API keys.

### 8.4 Event mechanics

Verified by reading the event page directly `[LIVE]`. Verbatim details:

- **"Sunday, August 16th, 2026 • 9AM to 8PM (BST)"** in the header; body text says "9am to 7pm in central London".
- **"One rule: no human analysts."** The agent must be autonomous. Do not hand-tune the final number.
- **"We bring the data, API credits, and tooling so you're building within the first half hour, not fighting API keys."**
- **"Accuracy is scored later, as companies report"** — so pick a target that reports *soon*. NVDA (~26 Aug) is ideal; see §1.10.
- Motivation stated outright: "Consensus … sits behind institutional paywalls that run to tens of thousands a year. OpenStocks is rebuilding that layer with agents."
- Attendance is **application-approval gated**; venue address is "available after application approval".

- **$10,000 pot, two tracks:** *Accuracy* (scored later as companies report — beating consensus is the whole game) and *Design*, judged on the day as two awards: **best agent architecture** and **best aesthetics**.
- Design is winnable same-day regardless of forecast outcome — "You can win before your forecasts are ever proven right." **Two of three awards are decided in the room. Budget real time for the demo UI.**
- Format: intro, three build blocks, mentors from partners, live stage demos.
- **"We bring the data, API credits, and tooling so you're building within the first half hour, not fighting API keys."** So expect sponsor data — but nothing is public tonight, which is exactly why the free stack above matters as a hedge.
- **Team logistics: create your team on the Teams page in the hackathon portal and invite by email; every teammate must accept and complete their profile or the team isn't considered.** Do this tonight — it's blocking and depends on other people acting.
- Attendee pool includes engineers from Google, Amazon, Meta, Goldman Sachs, Bloomberg.

### 8.5 Pre-work tonight (~25 min)

1. **Complete team setup in the hackathon portal** — blocking, needs every teammate.
2. Grab free keys as insurance: Cloudflare Radar token, FRED, EIA, Census, Finnhub, FMP.
3. Write and test one thin TS client for **`api.nasdaq.com`** — consensus + surprise history + quarterly financials in one place.
4. Cache `company_tickers.json` and a `companyfacts` pull for your likely target tickers; **resolve the XBRL revenue-tag issue now, not at 2pm** (§1.3 Gotcha C).
5. Verify Node ≥ 22 if you intend to use `yahoo-finance2` v4.

---

## 9. Worked reference play: NVDA Q2 FY2027

Everything below was derived tonight from free sources, end to end. It is the shape of forecast the competition rewards, and it doubles as a pipeline test.

**Target:** NVDA fiscal Q2 2027, quarter ending 2026-07-31, reports **2026-08-26 AMC** (3-source agreement, §7.5; Yahoo `isEarningsDateEstimate: false`). Ten days after the hackathon — close enough to be credible, far enough that the result isn't already known.

### Step 1 — management guidance, from the 8-K

Pulled via submissions → item 2.02 → `index.json` → EX-99.1 (§1.10). Verbatim:
> "Revenue is expected to be **$91.0 billion, plus or minus 2%**. NVIDIA is not assuming any Data Center compute revenue from China in its outlook. GAAP and non-GAAP gross margins are expected to be **74.9% and 75.0%** … operating expenses … approximately **$8.5 billion and $8.3 billion**."

### Step 2 — the company's own guidance track record

I ran the §1.10 pipeline over the last six earnings 8-Ks and paired each guide with the actual it produced `[LIVE]`:

| Quarter | Guided (prior 8-K) | Actual reported | Beat vs guide |
|---|---|---|---|
| Q1 FY26 (Apr-2025) | $43.0B | $44.062B | **+2.47%** |
| Q2 FY26 (Jul-2025) | $45.0B | $46.743B | **+3.87%** |
| Q3 FY26 (Oct-2025) | $54.0B | $57.006B | **+5.57%** |
| Q4 FY26 (Jan-2026) | $65.0B | $68.127B | **+4.81%** |
| Q1 FY27 (Apr-2026) | $78.0B | $81.615B | **+4.63%** |

**mean +4.27%, median +4.63%, σ 1.05%, range +2.47% to +5.57% — five beats out of five.**

### Step 3 — where consensus actually sits

| Source | Q2 FY27 revenue consensus |
|---|---|
| Yahoo `earningsTrend` | $91.957B |
| StockAnalysis (S&P Global) | $91.918B |
| Zacks | $91.710B |

Consensus ≈ **$91.86B — only +0.94% above the guidance midpoint.**

### Step 4 — the gap

Applying the company's own historical guide-beat distribution to its current guide:

```
guide $91.0B × (1 + 4.27% mean)   = $94.89B
guide $91.0B × (1 + 4.63% median) = $95.22B
±1σ band                          = $93.93B – $95.84B
```
**That is +3.2% to +3.3% above consensus** — and the entire ±1σ band sits above every consensus print. Consensus is anchoring on guidance and applying almost no beat premium, while NVDA has beaten its own guide by 2.5–5.6% for five consecutive quarters.

### Why this matters for the build

The scoring rule is *percentage distance vs consensus* (§8.3). You do not need a better model of the semiconductor cycle. You need to systematically capture the **guidance-to-actual bias** that consensus under-weights — and that bias is computable from free SEC filings alone, per company, in about 20 HTTP requests.

**Caveats to state out loud in the demo, because judges will ask:**
- n=5 is a small sample, and it covers an unusually strong demand period. The beat rate is regime-dependent, not a law.
- The China-exclusion clause in the guidance is a live variable; if any Data Center China revenue lands, the beat is mechanically larger.
- This is a **revenue** play. EPS needs the extra step of §1.3 — consensus EPS ~$2.08 is **non-GAAP**, and NVDA's GAAP and non-GAAP EPS diverged 22% last quarter ($2.39 vs $1.87). Forecast the basis consensus is quoted on, or you will be scored against a number you never modelled.

Generalising: run steps 1–2 for any company that gives numeric guidance, and you have a per-company beat prior. For non-guiding issuers (Apple, §5.2) you fall back to the transcript CFO block, and the prior is built on qualitative guidance instead — harder, and worth flagging as a scope boundary tomorrow.

---

## Implications for our build

### Priority order for tomorrow morning

| # | Time | Build | Why first |
|---|---|---|---|
| **0** | tonight | **Team setup in the hackathon portal.** Every teammate must accept + complete their profile. | Blocking, depends on other humans, and cannot be done at 09:00 |
| **0** | tonight | Grab free keys as insurance: FRED, Cloudflare Radar, FMP, Finnhub, EIA | 2 min each; useless if attempted during a build block |
| **1** | 09:00–10:00 | **SEC EDGAR client** — `resolveCik`, `getFilings`, `getConcept`, `getFilingFiles`, `getExhibit`. Token bucket at 8 req/s, SQLite cache, UA header. | Zero-dependency backbone. Nothing else can fail it. |
| **2** | 10:00–10:30 | **Guidance extractor**: 8-K item 2.02 → EX-99.1 → "Outlook" anchor → LLM to `{metric,min,max,point,period,basis}`. Fallback to EX-99.2, then transcript. | This is the differentiator. No free structured guidance dataset exists (§5.5). |
| **3** | 10:30–11:00 | **Consensus client**: `yahoo-finance2` primary + StockAnalysis cross-check. Store vendor + GAAP/non-GAAP basis with every number. | You cannot score without the benchmark, and basis errors are silent and fatal |
| **4** | 11:00–11:30 | **Quarterly history**: companyconcept with tag-fallback chain + duration filter + Q4 synthesis; stockanalysis `__data.json` for normalized/segments | Feeds the guide-beat prior and seasonality |
| **5** | 11:30–12:00 | **Guide-vs-actual backtest** per company (§9 steps 1–2) | The actual edge. 20 requests per company. |
| **6** | afternoon | Transcripts (defeatbeta bulk, Fool for latest), alt data, demo UI | Two of three awards are judged in the room — **budget real time for the UI** |

### Recommended ingestion stack — primary + fallback

| Data type | Primary | Fallback | Never |
|---|---|---|---|
| Ticker → CIK | `company_tickers.json` (cached) | `company_tickers_exchange.json` | — |
| Filing history | EDGAR submissions API | — | — |
| Quarterly financials | **EDGAR companyconcept** (tag chain, duration filter) | stockanalysis `__data.json` | Tiingo, Polygon, Intrinio |
| This quarter's full statement | EDGAR `R2.htm` via FilingSummary | companyconcept assembly | — |
| Segment revenue | **EDGAR `R*.htm`** (FilingSummary → `/segment/i`) | stockanalysis `__data.json` | companyfacts (has none) |
| **Guidance** | **8-K EX-99.1 → EX-99.2** | Transcript CFO block | Any vendor — none free |
| **Consensus (rev + EPS)** | **`yahoo-finance2@4`** | StockAnalysis `__data.json` | **Nasdaq (stale), Finnhub free (absent), FMP (unverified)** |
| Consensus dispersion | Yahoo `low`/`high` | Zacks scrape (only free revenue high/low) | — |
| Revision momentum | Yahoo `epsTrend` + `epsRevisions` | Nasdaq `earnings-forecast` up/down | — |
| Point-in-time consensus history | Alpha Vantage `EARNINGS_ESTIMATES` (cache tonight, 25/day) | Yahoo `earningsHistory` | — |
| Earnings date | stockanalysis calendar + Nasdaq (2-source agreement) | Yahoo `isEarningsDateEstimate` | Wall Street Horizon (paid) |
| Transcripts (bulk) | defeatbeta parquet via DuckDB httpfs | Fool monthly sitemap | API Ninjas, Finnhub, FMP |
| Transcripts (latest) | Fool `news-sitemap.xml` → article | Alpha Vantage (25/day) | — |
| Macro / alt | FRED `fredgraph.csv` (no key) | Wikipedia pageviews, TSA, Greenhouse | Google Trends, credit-card, satellite |

### Non-negotiables

1. **Everything through SQLite with a cache-on-first-fetch layer.** Yahoo will 429 you, and re-running the agent mid-demo must not re-hit the network.
2. **Record the basis (GAAP vs non-GAAP) and the vendor on every consensus and every actual.** NVDA last quarter: GAAP EPS $2.39, non-GAAP $1.87 — a 22% gap. This is the most likely way to score a fake win and a real loss.
3. **Never trust `fp`/`fy` for period identity.** Key everything on `periodEndDate` and duration-in-days. NVDA "Q2 FY2027" ends July 2026.
4. **Q4 does not exist as a filed quarter.** Synthesise it (§1.3 Gotcha B) or your seasonality model has a hole every year.
5. **Build it as a clean, runnable GitHub repo with pinned deps and a deterministic entrypoint.** The Verified GitHub tier requires OpenStocks to execute your exact commit (§8.3). Vendor/cache the data so a cold run works without your keys.
6. **"No human analysts."** Don't hand-tune the final number; make the agent produce it.

### What to cache tonight if there's time

`company_tickers.json` · companyfacts + last 8 earnings 8-K EX-99.1s for 3–5 candidate tickers · one Alpha Vantage `EARNINGS_ESTIMATES` pull per candidate · the defeatbeta `stock_earning_calendar.parquet` (196 KB) · the SvelteKit devalue decoder ported to TS.

### Candidate targets reporting soon

NVDA (~26 Aug, guides numerically, five-quarter beat streak — the reference play), CRM, WMT, TGT, plus anything in the stockanalysis calendar's next 30 days. **Prefer companies that give numeric guidance in the 8-K** — the Apple pattern (§5.2) costs you an hour you don't have.

---

## Addendum (verified live, 16 Aug 00:30) — defeatbeta transcript parquet

- Coverage confirmed by full-file aggregate over HTTP (86s): **238,206 earnings calls,
  6,465 tickers, 2005-10 → 2026-08** (updated same-day). Deepest free transcript source.
- Query pattern matters: row-level metadata lookups ~15s over HTTP (projection pushdown);
  **content-column text scans take ~36min over HTTP** — fetch whole transcript rows by
  symbol/quarter and search locally, or download the 2.25GB parquet once for bulk work.
- Transcript text renders "plus or minus" as "±" — guidance-extraction regexes must
  match both forms.
