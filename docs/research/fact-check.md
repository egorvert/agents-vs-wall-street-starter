# Fact-check: load-bearing claims across `docs/research/`

Adversarial verification against primary sources, run 15 Aug 2026 (evening, pre-hackathon).
Method: direct fetch of official docs (`platform.claude.com`, `developers.openai.com`), arXiv abstract/HTML
pages by ID, SEC EDGAR with a declared User-Agent, publisher/author-hosted PDFs, and the live
openstocks.com pages. Nothing below is taken from an aggregator where a primary source existed.

**Verdict key:** `CONFIRMED` · `PARTIALLY` (materially or cosmetically differs) · `WRONG` (correction given) ·
`UNVERIFIABLE` (could not check tonight — do not assert as fact on stage).

**Tally: 46 CONFIRMED · 16 PARTIALLY · 2 WRONG · 8 UNVERIFIABLE.**

---

## Executive summary — the dangerous ones

Read only this section if you read nothing else. These are the claims that are **wrong**, or **partially wrong
in a way that changes a decision or would embarrass us in front of the Primer judges.**

### WRONG

| # | Claim | Where | Correction |
|---|---|---|---|
| W1 | *"Community (.xlsx) is explicitly prize-ineligible → we must target Community Verified"* | `hackathon-intel.md` §3 tiers table + the bolded "**→ We must target Community Verified**" | **The Prize Rules contradict the manifesto.** Prize Rules v2026-08-08-v5, *Eligibility*: "you must … **submit a Community workbook or verified GitHub forecast** before the applicable forecast window closes … A Community workbook must complete the in-product review and be published." A published .xlsx **is** prize-eligible. The manifesto's "won't count towards rankings, prizes, or any official stats" is contradicted by the operative rules doc. What the Prize Rules *do* say is narrower: "Community and verified GitHub entries … **do not become the OpenStocks consensus or change headline OpenStocks-versus-Wall-Street statistics**." → Do not tell a judge that xlsx is prize-ineligible; they wrote both pages. Targeting the GitHub tier is still the right call (it's what the hackathon submission form collects), just for a different reason. [prize-rules](https://openstocks.com/prize-rules) · [manifesto](https://openstocks.com/manifesto) |
| W2 | FactSet's **+7.0% / +7.4%** described as "**median** magnitudes", and used to justify a `forecast = consensus × 1.07` base-rate prior | `academic-ml.md` L568 ("median magnitudes +7.0%/+1.9%"); flows into `evals-hillclimbing.md` §"constant positive offset" | These are **index-level aggregate** surprises (Σactual / Σestimate), not medians and not per-company. They are dominated by a handful of mega-caps. Proof from the same report: Q2 2026 aggregate surprise was **29.2%**, but **10.9% excluding just Alphabet and Amazon** — driven by an $98bn and a $53.4bn *other income* line. A +7% per-company prior is a large overshoot. Use the **beat *rate*** (78%/76%) as the prior on **sign**, and fit the magnitude `k` on our own per-company backtest — do not import 7.0%. [FactSet 7 Aug 2026](https://insight.factset.com/sp-500-earnings-season-update-august-7-2026) |

### PARTIALLY, but materially

| # | Claim | Where | What actually differs |
|---|---|---|---|
| P1 | **Li, Shen, Tu & Zhou**: "GPT is significantly LESS accurate than analysts"; directional accuracy **49.3% / 47.7% vs analysts 71.1%**; "they state explicitly that they could not replicate Kim et al." | `street-process.md` §6.2; `llm-numeric-forecasting.md` L176 | **The paper has been substantially rewritten.** Current draft is dated **22 Oct 2025** (arXiv 2412.01069), retitled around a *diagnostic framework*, not an analyst-vs-GPT horse race. The `MetricOverlap` result is now stated as "**one standard deviation higher in alignment is associated with a 16.8 percent lower forecast error**" — not "0.117 → 0.061, −48%". And the current draft cites Kim/Muhn/Nikolaev **neutrally as a design precedent** ("following a practice similar to recent studies (e.g., Kim, Muhn, and Nikolaev, 2024)"), not as a failed replication. Sample (7,114 releases, 1,000 firms, GPT-4 Turbo cutoff 30 Apr 2023) is confirmed. **Do not put 47.7%/49.3% vs 71.1% on a slide** without re-reading the current PDF's tables — a judge who pulls up the paper will see a different abstract. |
| P2 | Leakage table: **Claude Sonnet 4.6 training cutoff = Aug 2025** | `evals-hillclimbing.md` §1.1 (column headed "Training cutoff") | Official models page: Sonnet 4.6 **reliable knowledge cutoff Aug 2025**, but **training data cutoff Jan 2026**. The doc used the *reliable* date under a *training* header — the less conservative of the two. Same shape of error is latent for any model where the two dates differ. For a leakage boundary, always use **training data cutoff**. (Opus 5 is unaffected: both are May 2026.) [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) |
| P3 | *"FedEx will not report a quarter in September"* | `company-selection.md` §(b) | Fiscal-year change, 7-month transition period and Freight spin-off are **confirmed verbatim** from the 8-K. But "no September report" is **our inference, not in the filing** — and the 8-K itself refers to "**beginning the first quarter of the Transition Period**", i.e. a transition quarter exists and will get a 10-Q. Last FDX 10-Q on EDGAR is 19 Mar 2026, so the next one is unfiled and its date is unknown. **The exclude decision is still correct** (fiscal-year change + spin-off + segment recut = zero clean history), just don't state the September claim as a fact. |
| P4 | Micron guidance **$31.00 ± $1.00 EPS** | `company-selection.md` §4.3, ranking table | Confirmed — **but the doc omits that the same table gives GAAP diluted EPS of $30.73 ± $1.00.** MU has a GAAP/non-GAAP split of ~$0.27 at the guide. `data-sources.md` warns about exactly this trap for NVDA; it is unguarded for MU. Record the basis. |
| P5 | Anthropic model shortlist includes **Claude Mythos 5** (via BenchLM, 83.21 top score) | `llm-numeric-forecasting.md` §6.3 | Score confirmed, but Mythos 5 is **not generally available** — invitation-only under Project Glasswing, no self-serve sign-up. It cannot be a fallback tomorrow. Also: the Fable 5 launch page currently carries the banner "**Access to Claude Fable 5 and Claude Mythos 5 has been restored**" — Fable 5 had an availability incident. Don't make Fable 5 the single point of failure in the harness. |

Everything else below is either confirmed or differs only cosmetically.

---

## 1. Model IDs, cutoffs, pricing, API behaviour

Sources: [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview) ·
[Claude migration guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide) ·
[Claude structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) ·
[OpenAI models](https://developers.openai.com/api/docs/models) ·
[OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) ·
[Anthropic support: training data](https://support.claude.com/en/articles/8114494-how-up-to-date-is-claude-s-training-data)

| Claim | Verdict | Notes | Source |
|---|---|---|---|
| `claude-opus-5` reliable knowledge cutoff **May 2026**, training cutoff **May 2026** | **CONFIRMED** | Both columns read May 2026. Opus 5 really is the binding leakage constraint. | models overview |
| `claude-fable-5` **Jan 2026**, `claude-sonnet-5` **Jan 2026** | **CONFIRMED** | Both reliable *and* training = Jan 2026. | models overview |
| `claude-opus-4-8` / `claude-opus-4-7` **Jan 2026** | **CONFIRMED** | | models overview |
| Claude Haiku 4.5 **Jul 2025** | **CONFIRMED** | Training Jul 2025; *reliable* knowledge cutoff is Feb 2025. Doc used the right one. | models overview |
| Claude Sonnet 4.6 **Aug 2025** listed as *training* cutoff | **PARTIALLY** | See **P2**. Training data cutoff is **Jan 2026**; Aug 2025 is the reliable-knowledge date. | models overview |
| Claude pricing: Fable $10/$50, Opus 5 $5/$25, Sonnet 5 $2/$10, Haiku 4.5 $1/$5 per MTok | **CONFIRMED** | Exact. | models overview |
| Claude 1M ctx / 128k max output on Fable 5, Opus 5, Sonnet 5 | **CONFIRMED** | Also: 300k output available on the Batches API via `output-300k-2026-03-24` beta header — worth knowing, not in the docs. | models overview |
| Adaptive thinking: Fable 5 "yes (always on)", Opus 5 / Sonnet 5 "yes" | **CONFIRMED** | Fable 5/Mythos 5 cannot disable thinking; `effort` is the only dial. `effort` defaults to `high` on Opus 5/Sonnet 5 on the API. | models overview, Fable 5 launch page |
| `gpt-5.6-sol` / `-terra` / `-luna` cutoff **16 Feb 2026** | **CONFIRMED** | All three. | OpenAI models |
| `gpt-5.6-luna` **$0.20 / $1.20** per MTok | **CONFIRMED** | Also confirmed: sol $5/$30, terra $2/$12; 1.05M ctx, 128k out on all three. | OpenAI models |
| GPT-5.5 cutoff 1 Dec 2025; GPT-5.2/5.4 31 Aug 2025; Grok 4.5 1 Feb 2026; o3/o4-mini Aug 2025 | **UNVERIFIABLE** | These come from RankScope (third-party). The current OpenAI models page **does not list GPT-5.5 or GPT-5.4 at all**. If a backtest tier depends on a GPT-5.5 cutoff, verify before relying on it. | — |
| `temperature`, `top_p`, `top_k` **removed and return 400** on current Claude models | **CONFIRMED** (Opus 4.7+/Opus 5/Opus 4.8/Fable 5/Mythos 5) / **PARTIALLY** (Sonnet 5) | Verbatim: *"Setting `temperature`, `top_p`, or `top_k` to a non-default value on Claude Opus 4.7 or later models, including Claude Opus 5, returns a 400 error."* The guide's explicit model list is Opus 5, Opus 4.8, Opus 4.7, Fable 5, Mythos 5 — **Sonnet 5 is not named**. Also: *"The SDK request types still define these fields for compatibility with earlier models, so code that sets them type-checks, but the API rejects the request server-side."* → the architectural conclusion (**get diversity structurally, not from temperature**) holds regardless. | migration guide |
| Claude structured outputs do **NOT** support `minimum`/`maximum`/`multipleOf`/`minLength`/`maxLength` | **CONFIRMED** | Verbatim in the "Not supported" list. Also unsupported: recursive schemas, external `$ref`, `additionalProperties` ≠ false. Supported: `enum`, `const`, `anyOf`/`allOf` (no `allOf` + `$ref`), `default`, array `minItems` ∈ {0,1}. | structured outputs |
| OpenAI strict schemas **DO** support `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`multipleOf` | **CONFIRMED** | Unsupported for standard models: `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`/`then`/`else`. → The doc's conclusion (**range enforcement lives in our validator either way**) is right. | OpenAI structured outputs |
| `output_config.format` is current; `output_format` "deprecated" | **PARTIALLY** | Docs say it "**moved** to `output_config.format`" and the old parameter + beta header "will continue working for a **transition period**". Functionally the same advice; "deprecated" is our word, not theirs. | structured outputs |
| First-use grammar-compilation latency; compiled grammars cached **24h** from last use; changing the format **invalidates the prompt cache** | **CONFIRMED** | All three verbatim. Cache also invalidated by changing the tool set; changing only `name`/`description` does not invalidate. → "freeze the schema early" is correct advice. | structured outputs |
| BenchLM 15 Aug 2026: Mythos 5 **83.21**, Opus 5 **83.07**, Fable 5 **82.96**, GPT-5.6 Sol **82.00** | **CONFIRMED** | Doc already labels this `[secondary]`. Correct to do so. | [benchlm.ai](https://benchlm.ai/) |
| GPT-5.6 Sol scores **97** on the math composite | **UNVERIFIABLE** | The five-benchmark composition is confirmed (AIME26 · HMMT Feb 2026 · FrontierMath v2 Tiers 1–3 · FrontierMath v2 Tier 4 · USAMO 2026) but no per-category score is exposed on the leaderboard. | benchlm.ai |
| Claude Mythos 5 usable as a model option | **PARTIALLY** | Invitation-only (Project Glasswing), no self-serve. See **P5**. | models overview |

---

## 2. The 2026-dated papers

**All five 2026 arXiv IDs resolve to real papers with the titles cited.** No fabricated citations found.

| Claim | Verdict | Notes | Source |
|---|---|---|---|
| **QuantSightBench** exists — arXiv **2604.15859**, Qin & Andriushchenko, Apr 2026 | **CONFIRMED** | *"QuantSightBench: Evaluating LLM Quantitative Forecasting with Prediction Intervals."* Submitted 17 Apr 2026. | [abs/2604.15859](https://arxiv.org/abs/2604.15859) |
| Author affiliation "ELLIS Tübingen" | **PARTIALLY** | Both authors are **Max Planck Institute for Intelligent Systems**; Andriushchenko is *also* ELLIS Institute Tübingen + Tübingen AI Center. Cite MPI-IS/ELLIS Tübingen. | ibid. |
| 11 models; restricted to **knowledge cutoffs before Sept 2025**; no model reaches 90%; best is >10pts short | **CONFIRMED** | Verbatim restriction: "Models with a documented knowledge cutoff date prior to September 2025". | [html/2604.15859v1](https://arxiv.org/html/2604.15859v1) |
| Coverage table: Gemini 3.1 Pro **79.1** · Grok 4 **76.4** · GPT-5.4 **75.3** · GPT-5.1 **74.6** · Opus 4.6 **73.6** · GLM-4.7 **62.7** · DeepSeek v3.2 **61.5** · Sonnet 4.5 **68.0** | **CONFIRMED** | Eight of eleven match exactly. | ibid. |
| Coverage: Opus 4.5 **71.7**, Gemini 3 Pro **65.4**, Kimi K2 Thinking **65.8** | **PARTIALLY** | Paper reads **72.6** (Opus 4.5) and **65.0** (Gemini 3 Pro); Kimi K2 Thinking's agentic-setting value was not locatable. Values are read off a figure, so ±1pt. Immaterial to the conclusion, but **don't quote individual model numbers to the decimal on stage** — quote the ranking and the ">10 pts short of nominal" headline. | ibid. |
| "Systematic overconfidence across all evaluated models"; calibration degrades at extreme magnitudes | **CONFIRMED** | Verbatim in the abstract. → the "treat a stated 90% interval as ~70–75%" implication stands. | abs/2604.15859 |
| **FinVerBench** exists — arXiv **2605.29586**, Silu Panda, submitted 28 May 2026 | **CONFIRMED** | SEC 10-K XBRL, 43 S&P 500 companies, four injected error types. | [abs/2605.29586](https://arxiv.org/abs/2605.29586) |
| **9 of 14** frontier LLM runs produce 95–100% false positives on clean statements; **one run** achieves 0% | **CONFIRMED — verbatim** | *"nine of fourteen complete LLM runs produce 95–100% false positives on clean statements, while one run achieves 0% observed false positives."* Also: fifteen evaluations attempted, fourteen complete (a Gemini 2.5 Pro run excluded, 40/108 gateway calls failed). The 0%-FPR run is **Claude Sonnet 4** — "correctly identifies all 62 observable injected errors and produces no false alarms on the 43 clean instances." | [html/2605.29586v1](https://arxiv.org/html/2605.29586v1) |
| "models collapse from **95.6%** accuracy on simple lookups to near 0% on multivariate calculations" attributed alongside FinVerBench | **CONFIRMED, but attribute correctly** | This is **FAITH's** result ([arXiv 2508.05201](https://arxiv.org/abs/2508.05201)), quoted in FinVerBench's related-work section — not a FinVerBench measurement. `qa-verification.md` L14 says "Related:", which is defensible, but the link points at 2605.29586. Fix the link if it goes on a slide. | ibid. |
| arXiv **2607.05904** = *"More Convincing, Not More Correct: Self-Play Reward Hacking of Reference-Free LLM Judges"* | **CONFIRMED** | Chenyu Zhou. Headline: judge pass rate rises 0.72 → 0.94 on GSM8K while true accuracy stays at 0.20. Mitigation: make the judge commit to its own answer first. | [abs/2607.05904](https://arxiv.org/abs/2607.05904) |
| arXiv **2603.11337** = *"RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engineering Agents"* | **CONFIRMED** | Atinafu & Cohen. Evaluator tampering appeared in ~half of episodes; evaluator locking eliminated it at 25–31% median runtime cost. | [abs/2603.11337](https://arxiv.org/abs/2603.11337) |
| arXiv **2605.09315** = *"Do Self-Evolving Agents Forget? Capability Degradation and Preservation in Lifelong LLM Agent Adaptation"* | **CONFIRMED** | Yu, Yuan, Jin, Liu, Yu & Wang. "Capability erosion under self-evolution"; CPE lifts retained workflow performance 41.8% → 52.8%. → the doc's "a lesson set is not the sum of its lessons" reading is fair. | [abs/2605.09315](https://arxiv.org/abs/2605.09315) |

---

## 3. Kim / Muhn / Nikolaev withdrawal and the Li et al. contradiction

| Claim | Verdict | Notes | Source |
|---|---|---|---|
| arXiv **2407.17866 withdrawn at v3 on 20 Feb 2025**, still withdrawn | **CONFIRMED** | Verdict holds as of tonight. No corrected version has appeared. | [abs/2407.17866](https://arxiv.org/abs/2407.17866) |
| Withdrawal comment quoted verbatim in `academic-ml.md` and `street-process.md` | **CONFIRMED — exact match** | *"A co-author identified inconsistencies in the data and analyses while attempting to replicate past analyses from the working paper. Accordingly, we have temporarily withdrawn the working paper from circulation while we review the research findings."* | ibid. |
| Do not quote "GPT-4 60.35% vs analysts 52.71%" as established fact | **CONFIRMED as the right call** | The paper's own listing still carries the pre-withdrawal abstract ("outperforms human analysts", "higher Sharpe ratios and alphas") — which is exactly why an unlabelled citation is dangerous. Keep the ⚠️ label. | ibid. |
| Companion paper *"Bloated Disclosures"* also withdrawn; Nikolaev faculty page confirms | **UNVERIFIABLE tonight** | Not independently re-checked. Plausible and consistent, but flag it as second-hand if said aloud. | — |
| Li et al. replication: directional accuracy **47.7% / 49.3% vs analysts 71.1%**; "could not replicate Kim et al." | **PARTIALLY — see P1** | Sample facts confirmed (7,114 releases, 1,000 firms, ±4 quarters around GPT-4 Turbo's 30 Apr 2023 cutoff, GAAP EPS vs I/B/E/S GAAP forecasts). But the **current 22 Oct 2025 draft is a rewrite**: reframed as a diagnostic framework, MetricOverlap now stated as "one standard deviation higher in alignment is associated with a **16.8 percent** lower forecast error", and Kim/Muhn/Nikolaev is cited **neutrally as a design precedent**. The 47.7/49.3/71.1 triple and the "GPT beats analysts in >25% of firm-quarters" line are from the Dec-2024 v1. | [arxiv.org/pdf/2412.01069](https://arxiv.org/pdf/2412.01069) |
| The doc's "*conflict noted*: 52.7% vs 71.1% are different tasks; don't benchmark against either" | **CONFIRMED as sound methodology** | Good instinct, keep it — and now it's doubly warranted given the paper revision. | — |

---

## 4. Hackathon facts

Sources: [openstocks.com/terms](https://openstocks.com/terms) · [/privacy](https://openstocks.com/privacy) ·
[/prize-rules](https://openstocks.com/prize-rules) · [/manifesto](https://openstocks.com/manifesto)

| Claim | Verdict | Notes | Source |
|---|---|---|---|
| OpenStocks operated by **Kernel AI Ltd, UK company 15117085** | **CONFIRMED — verbatim** | Appears identically in Terms, Privacy **and** Prize Rules ("OpenStocks prize rounds are operated by Kernel AI Ltd, a UK company (number 15117085)"). | all three |
| Privacy policy names **"Kernel AI Ltd (Primer and OpenStocks)"** — i.e. same company | **CONFIRMED — verbatim** | *"Team email addresses and the private entry record are available only to specifically authorised event staff at Kernel AI Ltd (Primer and OpenStocks)."* This is the strongest single piece of intel in the doc and it holds. | /privacy |
| Privacy policy **last updated 15 Aug 2026** | **CONFIRMED** | Written for this event. | /privacy |
| Scoring: closeness = % distance to actual, compared against the recorded Wall Street consensus | **CONFIRMED — verbatim** | | /prize-rules |
| **Hard gate: must beat consensus** — "A potential winner is selected **only** from scored forecasts that are closer to the actual result than that Wall Street consensus value" | **CONFIRMED — verbatim** | | /prize-rules |
| **Closest wins; ties broken by earlier submission** | **CONFIRMED — verbatim** | *"The closest eligible scored forecast is selected, with earlier submission winning ties, subject to review, fraud checks, and final eligibility confirmation."* → "submit early once confident" is correct. | /prize-rules |
| One prize round = one company, one fiscal period, one named metric; other metrics still scored | **CONFIRMED — verbatim** | | /prize-rules |
| Rounds voidable (merger, delisting, cancelled/delayed report, data failure) | **CONFIRMED — verbatim** | Also: **scoring uses results as first reported** — a later restatement does not change an award. Not in the doc; worth knowing. | /prize-rules |
| Platform prize **$100/event, max 20 events, $2,000 total** — separate from the $10k hackathon pot | **CONFIRMED** | And: "if no eligible forecast is closer … than the Wall Street consensus, **no prize is awarded** for that round." | /prize-rules |
| 18+, one account per person, LinkedIn connected before deadline, explicit opt-in before deadline | **CONFIRMED — verbatim** | Also: "**OpenStocks operators and OpenStocks' own Official forecasts are not eligible for prizes.**" | /prize-rules |
| Submission collects **repository URL + uploaded architecture HTML file + final commit + final command** | **CONFIRMED — verbatim** | Full list: *"the agent name and description, each team member's name and email address, the declared build style, harness, models, languages, frameworks, pre-existing components and human input, plus the repository URL, uploaded architecture HTML file, final commit and final command."* → "build the architecture HTML deliberately" is well-founded. | /privacy |
| **"verified repositories run in isolated Modal sandboxes"** | **CONFIRMED — verbatim** | → design for cold-start reproducibility, no local state, no interactive auth. | /privacy |
| **Two social prizes** | **CONFIRMED — verbatim** | *"we judge the two social prizes, contact winners and keep an auditable event record."* | /privacy |
| Three tiers — Official / Community Verified (GitHub, OpenStocks runs the agent) / Community (.xlsx) | **CONFIRMED — verbatim** | Manifesto: Community Verified = "the contributor gives access to the agent, OpenStocks runs it to produce the model … it proves it wasn't human-generated." | /manifesto |
| **"Community Verified GitHub tier only prize-eligible" / ".xlsx explicitly prize-ineligible"** | **WRONG — see W1** | Prize Rules explicitly allow a published Community workbook. The two pages contradict each other. | /prize-rules vs /manifesto |
| AI Tinkerers Sept 2025 "Ultimate Agents" — £10k, Anthropic/ElevenLabs/Dedalus/Vibe Kanban, London AI Hub | **CONFIRMED** | Event page also confirms: kickoff 9:30am sharp, mandatory attendance, teams of up to 4, build ends 6pm, wrap by 8pm — matches the doc's schedule intel. | [aitinkerers](https://london.aitinkerers.org/p/ultimate-agents-hackathon-10k-total-prizes) |
| "120 builders"; "11 judges, 6 of them current/former YC founders" | **UNVERIFIABLE** | Not on the public page (which shows 217+ listed attendees). Treat as soft. | ibid. |

---

## 5. Statistics we would repeat on stage

| Claim | Verdict | Notes | Source |
|---|---|---|---|
| FactSet: **78%** (5-yr) / **76%** (10-yr) of S&P 500 beat EPS consensus | **CONFIRMED — verbatim** | | [FactSet 7 Aug 2026](https://insight.factset.com/sp-500-earnings-season-update-august-7-2026) |
| FactSet: aggregate EPS surprise **+7.0%** (5-yr) / **+7.4%** (10-yr) | **CONFIRMED as numbers** / **WRONG as "median magnitudes"** | See **W2**. They are aggregate index-level, not medians. | ibid. |
| FactSet: **70%** (5-yr) / **68%** (10-yr) beat revenue consensus | **CONFIRMED — verbatim** | | ibid. |
| Revenue surprise magnitude "+1.7%" | **PARTIALLY** | FactSet: **1.9%** (5-yr) and **1.6%** (10-yr). `academic-ml.md` uses 1.7% in one place and 1.9% in another. Pick 1.9% (5-yr) for consistency with the EPS figure. | ibid. |
| Q2 2026 live numbers (86% beat, 29.2% aggregate surprise) as of the docs | **CONFIRMED** | Note for the writeup: **excluding Alphabet and Amazon the surprise is 10.9%** — a great on-stage illustration of why aggregate ≠ typical. Also: FactSet Earnings Insight **is not published 14 or 21 Aug**; next edition **28 Aug**. | ibid. |
| **Ciconte, Kirk & Tucker**, *Rev. Acc. Stud.* **19(2) 2014: 628–660** | **CONFIRMED** | Exact journal/volume/issue/pages. | [SSRN 2061440](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2061440) |
| `ACT_DIS` defined 1 = upper bound, 0 = midpoint, −1 = lower bound | **CONFIRMED — verbatim** | | [UF working paper PDF](http://bear.warrington.ufl.edu/tucker/2013-2_management_range_forecasts.pdf) |
| **Median ACT_DIS = 1.00**; **mean 1.20** in the later period; **45.7%** of actuals above the high end | **CONFIRMED — verbatim** | Later period: "ACT_DIS has a mean of 1.20 and median of 1.00, both significantly different from 0." And "actual earnings are above the upper bound for **45.7%** of the forecasts, at it for 15.9%, and below it for 38.4%." | ibid. |
| Implied claim that actuals sit at the guidance **upper bound** | **CONFIRMED** | Full sample mean 0.93 / median 1.00, "both insignificantly different from 1 (p=0.18 and p=1.00)". | ibid. |
| Sample "30,106" and period "2002–2010" | **PARTIALLY** | Paper's overall sample is **1996–2010**; 2002–2010 is the "later period" subsample the headline numbers come from. Full-sample mean is **0.93**, not 1.20 — say "later period" whenever you say 1.20. Sample size not re-verified. | ibid. |
| **Bernard & Thomas (1990)** autocorrelations **+0.34, +0.19, +0.06, −0.24** | **CONFIRMED — verbatim, via an independent paper** | Kothari, Lewellen & Warner: *"Bernard and Thomas (1990) report autocorrelations of 0.34, 0.19, 0.06, and –0.24 for the first four lags, estimated as the average slope in firm-level time-series regressions (using firms with a minimum of ten quarterly earnings observations from 1974 to 1986)."* | [MIT PDF](https://web.mit.edu/lewellen/www/Documents/Earnings.pdf) |
| "Lewellen replication, firm-level: +0.34, +0.18, +0.05, −0.29, all \|t\| > 5" | **CONFIRMED — verbatim** (fix the attribution) | *"simple autocorrelations are positive at the first three lags and negative at the fourth: 0.34, 0.18, 0.05, and –0.29 … All four are highly significant, with t-statistics greater than five in absolute value."* But the paper is **Kothari, Lewellen & Warner, "Stock Returns, Aggregate Earnings Surprises, and Behavioral Finance"** — not a Lewellen solo replication. Cite all three authors. | ibid. |
| B&T three-day abnormal returns **+1.32%, +0.70%, +0.04%, −0.66%** at t+1…t+4 | **CONFIRMED — verbatim** | Same paper: "abnormal returns of 1.32%, 0.70%, 0.04%, and –0.66% at the four subsequent quarterly earnings announcements." | ibid. |
| **Houlihan Lokey**: Russell 3000 1-yr weighted % error **9.76% revenue vs 84.05% earnings = 8.6×** | **CONFIRMED — verbatim** | *"Averaging the past 8 years, the overall Russell 3000 1-year % error increased from 9.76% for revenue to 84.05% for earnings, representing an 8.6x worse % error."* S&P 500 equivalent: 9.33% / 73.67% = 7.9×. | [Houlihan Lokey 2024 PDF](http://cdn.hl.com/pdf/2024/accuracy-of-analyst-estimates-2024.pdf) |
| **Anthropic multi-agent +90.2%** | **CONFIRMED — verbatim** | *"a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval."* Caveat to state honestly: it is an **internal** eval on **breadth-first research**, not on forecasting. The doc already frames it that way. | [Anthropic engineering](https://www.anthropic.com/engineering/multi-agent-research-system) |
| **PoT ≈ +12%** over CoT, incl. FinQA / ConvFinQA / TATQA, TMLR 2023 | **CONFIRMED — verbatim** | *"Under both few-shot and zero-shot settings, PoT can show an average performance gain over CoT by around 12% across all the evaluated datasets."* Eight datasets: GSM, AQuA, SVAMP, TabMWP, MultiArith + the three financial-QA sets. | [arXiv 2211.12588](https://arxiv.org/abs/2211.12588) |
| **Schoenegger et al.** (*Science Advances*): 12 LLMs, median-aggregated ≈ crowd of **925** humans on **31** binary questions | **CONFIRMED** | LLM crowd Brier **0.20** (SD 0.12) vs human crowd **0.19** (SD 0.19); "fail to find statistically significant differences", **p = 0.850**; equivalence test passes within medium effect-size bounds. Baseline 0.25. | [arXiv 2402.19379](https://arxiv.org/abs/2402.19379) (journal page 403s) |
| Exposure to the median human prediction improved LLM accuracy **17–28%** | **CONFIRMED — verbatim** | | ibid. |
| Aggregation: **median 0.197, trimmed mean 0.197, geometric mean 0.194** | **UNVERIFIABLE** | The public version reports only the median-aggregated result. The three-way comparison was not locatable. **Say "median aggregation matched the human crowd", not the three decimals.** | — |
| **Herzog & Hertwig** dialectical bootstrapping: repeated estimate **0.3pp**, dialectical **4.1pp**, another person **7.1pp** | **CONFIRMED — verbatim, all three** | Reliability gain "averaging 0.3 percentage point (SD 2.3%; Mdn 0%; CI 0.0%–0.8%; **d = 0.12**)"; dialectical "**4.1** percentage points (SD 7.8%; Mdn 3.6%; CI 2.0%–6.4%) — an effect of medium size (**d = 0.53**)"; dyadic "average dyadic gain of **7.1** percentage points (SD 8.3%; Mdn 6.7%; CI 5.0%–9.4%) — an effect of large size (**d = 0.86**)". | [MPIB PDF](https://library.mpib-berlin.mpg.de/ft/sh/SH_Wisdom_2009.pdf) · Psych. Science 20(2) 231–237 |
| "**72%** of participants benefited" from dialectical bootstrapping | **CONFIRMED — verbatim** | "Nearly three fourths of participants (**36 of 50, or 72%**) benefited"; 24% got worse. Bracketing rates: 7.9% repeated / 13.6% dialectical / 17.6% dyadic. Memorable line for the judges: *"one's own second, dialectical opinion is worth half the opinion of another judge."* | ibid. |
| The doc's translation — "5 samples of the same prompt ≈ 0.3pp; vary prompt/model ≈ 4–7pp" | **CONFIRMED as a fair reading** | Note the study is **human date-estimation (n=101, 40 Wikipedia events)**, not LLM forecasting. Present it as an analogy, not a measured LLM result. | ibid. |
| Estimize "more accurate 70%/74%/65% of the time" | **UNVERIFIABLE** | Doc already labels these as vendor marketing claims and gives a range. Leave as is. | — |

---

## 6. Company facts

| Claim | Verdict | Notes | Source |
|---|---|---|---|
| **FedEx** changed FY end from May 31 to **Dec 31**, effective **June 1, 2026**; 7-month transition period reported on Form 10-K | **CONFIRMED — verbatim** | Quote in `company-selection.md` matches the 8-K word for word, including "will report operating results covering the seven-month transition period from June 1, 2026 through December 31, 2026 in a Transition Report on Form 10-K." Calendar-year reporting from FY ending 31 Dec 2027. | [8-K 21 Jul 2026, Item 2.02](https://www.sec.gov/Archives/edgar/data/1048911/000104891126000108/fdx-20260721.htm) |
| FedEx **spun off FedEx Freight** and **re-cut reportable segments** | **CONFIRMED — verbatim** | Spin-off completed **1 June 2026** (incl. FedEx Custom Critical, LTL Select). Freight no longer a reportable segment. Two new segments: **Express U.S. Domestic** and **Express International** (previously one "Federal Express" segment). | ibid. |
| "FedEx will not report a quarter in September" | **PARTIALLY — see P3** | Our inference. The 8-K itself says "**beginning the first quarter of the Transition Period**", so a transition quarter exists. Last FDX 10-Q on EDGAR: 19 Mar 2026. **Exclusion is still correct** on structural-change grounds alone. | EDGAR filing list |
| **Oracle** Q1 FY27 reports **10 Sep**, stated on the Q4 call | **CONFIRMED** | Ken Bond (Investor Relations), Q4 FY26 call, 10 June 2026: *"We expect our Q1 fiscal year 2027 earnings results will be announced on September 10. Any change in the date will be publicly announced."* (Auto-transcript garbles "2027" as "2020 7".) Also announced: Investor Day 28 Oct, Las Vegas. | [Q4 FY26 transcript](https://www.fool.com/earnings/call-transcripts/2026/06/10/oracle-orcl-q4-2026-earnings-call-transcript/) |
| Oracle Q1 FY27 guidance **$1.72–$1.76** non-GAAP EPS, revenue **+27–29%**, RPO **$638bn** | **CONFIRMED** | All three on the same call. RPO $638bn, up 363%; 12% within 12 months, 34% in months 13–36. FY27 non-GAAP EPS guide $8.05. | ibid. |
| "MarketBeat and Sharemaestro both say 8 Sep — both wrong" | **CONFIRMED as the right conclusion** | Company statement beats aggregators. The doc's lesson ("verify each date against the company's own IR page/call") is the correct process rule. | ibid. |
| **Micron** FQ4-26 guidance: revenue **$50.0bn ± $1.0bn**, non-GAAP diluted EPS **$31.00 ± $1.00** | **CONFIRMED — verbatim from the 8-K exhibit** | Business Outlook table also gives gross margin ~86%, opex ~$1.65bn non-GAAP. | [MU Q3 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/723125/000072312526000013/a2026q3ex991-pressrelease.htm) |
| Micron guidance is unambiguous on basis | **PARTIALLY — see P4** | Same table gives **GAAP** diluted EPS **$30.73 ± $1.00**. Record which basis we forecast. | ibid. |
| Micron **beat EPS 7/7, mean +18%**, per-quarter (+11.9, +9.1, +21.7, +5.9, +26.8, +32.8, +17.4) | **UNVERIFIABLE** | Needs a point-in-time consensus database. The seven listed surprises **do** average 17.9% ≈ +18%, so the doc is internally consistent. Note the doc says "8-qtr pattern" but lists 7 values — reconcile before quoting "7/7" next to "8 quarters". | — |
| JBL 7/7 EPS +7.4% / revenue 7/7 +6.0%; ADBE 7/7 mean +2.4%, σ 0.5% | **UNVERIFIABLE** | Same reason. These drive the pick ranking, so treat the *ranking* as a hypothesis to re-derive from our own data tomorrow, not as an established fact. | — |
| **NVDA GAAP $2.39 vs non-GAAP $1.87** — non-GAAP *below* GAAP | **CONFIRMED — verbatim** | Press release: *"For the quarter, GAAP and non-GAAP earnings per diluted share were $2.39 and $1.87, respectively."* The unusual direction is real and the doc's explanation checks out: income statement shows **Other income (expense), net 15,929** ($15.9bn) for the quarter ended 26 Apr 2026. GAAP diluted $2.39 vs non-GAAP $1.87 = non-GAAP **22% lower**. → the "never pipe `EarningsPerShareDiluted` into a consensus comparison" warning is fully justified and is one of the strongest points in the docs. | [NVDA Q1 FY27 8-K EX-99.1, 20 May 2026](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000051/q1fy27pr.htm) |
| NVDA Q2 FY27 outlook: revenue **$91.0bn ± 2%**, GAAP/non-GAAP GM 74.9%/75.0%, opex ~$8.5bn/$8.3bn | **CONFIRMED — verbatim** | Q1 FY27 actuals also confirmed: revenue $81,615M, opex $7,449M, operating income $53,783M, non-GAAP net income $45,548M, Data Center a record. | ibid. |
| NVDA 8-K cadence "Feb 25 / May 20 / Aug 27 / Nov 19"; Q2 FY27 due ~26–27 Aug 2026 | **PARTIALLY** | **20 May 2026 confirmed** on EDGAR. The Aug 2026 date is a forward projection and NVDA had not announced it as of tonight (most recent 8-Ks: 2 Jul, 30 Jun, 18 Jun 2026 — none an earnings release). Fine as a planning assumption; don't state it as confirmed. | EDGAR 8-K list |

---

## Things to change before tomorrow

1. **Delete or rewrite the "xlsx is prize-ineligible" line** in `hackathon-intel.md` (**W1**). Keep the
   Community-Verified recommendation; change the justification to "it's what the submission form collects
   and what runs in the Modal sandbox".
2. **Stop calling FactSet's +7.0% a median** and stop using it as a per-company multiplier (**W2**). Use the
   beat *rate* for the sign prior; fit the magnitude on our own data. The Alphabet/Amazon example (29.2% →
   10.9%) is a *better* slide than the 7% prior ever was.
3. **Re-read the current Li et al. PDF** before any slide cites 47.7/49.3/71.1 (**P1**).
4. **Switch the leakage boundary to `training data cutoff`** everywhere, and fix Sonnet 4.6 to Jan 2026
   (**P2**). Opus 5 at May 2026 remains the binding constraint, so the Tier A / Q2-CY2026 plan is unaffected.
5. **Soften the FedEx September claim** to "structural change → exclude" (**P3**) — the exclusion survives,
   the justification needs one fewer unsupported step.
6. **Add the GAAP/non-GAAP basis flag to Micron** ($30.73 GAAP vs $31.00 non-GAAP) (**P4**).
7. **Drop Mythos 5 from any fallback plan** and don't make Fable 5 a single point of failure (**P5**).
8. **Fix two citations:** the "Lewellen replication" is Kothari, Lewellen & Warner; the "95.6% → near 0%"
   collapse is FAITH (2508.05201), quoted inside FinVerBench.
