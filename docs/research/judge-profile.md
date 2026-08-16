# Judge Profile & Architecture-Prize Playbook

Compiled overnight 15–16 Aug 2026. **Event is TODAY, Sun 16 Aug 2026 — doors 10:00, 33 Johns Mews, London WC1N 2QL.**

Legend: **[C]** confirmed from a primary page (URL given). **[I]** my inference. **[?]** unknown.

---

## 0. STOP — round-1 intel is materially wrong. Read this section first.

`openstocks.com/hackathon` is **live, public, and contains the complete brief including the full 100-point judging rubric, the four target companies, the schedule, the accuracy formula, the prize split and the social-prize tags.** It was not found in round 1. Everything below supersedes `hackathon-intel.md` where they conflict.

Source for all of §0: https://openstocks.com/hackathon **[C]**

| Round-1 intel said | Reality **[C]** |
|---|---|
| Doors 09:00, kickoff 09:30, hack 10:00–17:00 | **Doors 10:00**, briefing 10:30–11:15, **building starts 11:15** |
| Judging begins 17:00, judged cold | **First judging pass 16:00–17:15 — every team gets 5 min with a judge pair**, and that conversation is "the most important part of the architecture judging" |
| Architecture HTML due ~17:00 | **HTML locks 17:15.** Hard deadline 18:00 for workbooks + entry |
| "Judged cold, without us present" | **False.** There is a live 5-min defence. But the HTML must *also* stand alone — Craft (4 pts) is scored on it working "in the private judging preview without extra explanation" |
| 1 company, revenue + EPS | **4 companies × 3 metrics = 12 forecasts** |
| Likely Nike/Costco/Micron | **Home Depot, Analog Devices, Hays plc, Deere & Co** |
| 50% architecture / 50% accuracy | **$4,500 Architecture / $4,500 Accuracy / $500 X / $500 LinkedIn** = 45/45/5/5 |
| Beating consensus is a hard gate, winner-take-all | **False.** Ratio = team abs error ÷ max(WS abs error, floor), capped 5.0, averaged over 12. **Lowest average wins.** 1st/2nd/3rd all pay |
| Repo run in Modal sandbox post-event | **"Organisers will not execute participant code after the event."** A rerun *may* be requested as verification |
| Judging criteria "TBA" | **Published in full. 100 points, itemised.** |

### Two facts that can disqualify us

1. **"No pre-made competition entry … Pre-built challenge-specific code, prompts, research, forecasts, workflows or *architecture explanations* mean immediate disqualification from every prize."** **[C]**
   → **We cannot pre-write the architecture HTML tonight.** We can only internalise the doctrine in this document and build the page tomorrow. Generic unmodified coding harnesses and public libraries are explicitly allowed; challenge-specific artifacts are not. Repo history and logs must show when work was made.
2. **The repo template already contains `architecture/index.html`** — a supplied template for the required architecture explanation. **[C]** Start from theirs; do not import an outside file.

### Logistics
- **Venue: 33 Johns Mews, London WC1N 2QL.** Doors 10:00. **[C]**
- Teams **1–4 people, one agent per team**. **[C]**
- **Participant repo: `github.com/kernlai/agents-vs-wall-street-starter`** — currently **404, releases on the morning**. **[C]** Docs inside will be `RULES.md`, `JUDGING.md`, `ENTRY.md`, `SUBMISSION.md`, `SCHEDULE.md`, `SOCIAL-COMPETITION.md`.
- **OpenAI is a named fourth partner.** Each team gets **$50 of Codex credit**. **[C]**
- Setup: `npm install` → `npm run setup:entry` → fill `entry.json` (gitignored) → `npm run check:submission` before upload. Optional helper `python3 starter/search.py --company HD`. **[C]**

---

## 1. THE RUBRIC — published verbatim, 100 points

Source: https://openstocks.com/hackathon §Architecture & Design **[C]**

> "This prize rewards **how the system researches, reasons, calculates and checks its work** — not whether the numbers later happen to be right."

### The system · 70 points

| Category | Pts | The question judges ask | Evidence they use |
|---|---:|---|---|
| **Forecasting approach** | **16** | How does the system reason its way to a forecast **instead of simply asking an AI model for a number**? | The workflow, prompts, code and decision trail showing how research becomes a forecast |
| **Model quality** | 12 | Can judges **follow how evidence and assumptions become each of the 12 final numbers**? | Calculations, assumptions and traces connecting source evidence to submitted figures |
| **Data approach** | 12 | What information does it use, where from, and **how does it check it is current and trustworthy**? | Sources, citations, retrieval code, research record produced during the run |
| **Validation and reliability** | 12 | Does the system **check units, unusual values, conflicting information** and other mistakes? | Checks, tests, **rejected values**, handled failures, final run log |
| **Agent harness** | 9 | Does the organisation of the agent help it complete the task reliably, and **can the team explain it**? | Repo structure, final command, orchestration, evidence it ran as described |
| **Tooling and ergonomics** | 9 | Did the team **build useful search, extraction or checking tools**? | Working tools in the repo and evidence of how they improved the run |

### The architecture write-up · 30 points

| Category | Pts | The question judges ask | Evidence |
|---|---:|---|---|
| **Clarity** | **10** | Can a technically minded outsider understand what the system does and why **after reading the page for five minutes**? | The uploaded HTML, plain-English workflow + main decisions |
| **Diagram and accuracy** | **10** | **Does the diagram match the real system**, and can someone follow the repo instructions to reproduce the run? | Diagram checked against code, final command, clear-run log |
| **Honesty and self-knowledge** | 6 | Does the team explain **what it tried, changed or abandoned**, and where the system may fail? | Specific trade-offs, **failed approaches**, limitations, known weaknesses |
| **Craft** | 4 | Is the page clear and well made enough to publish on the team's OpenStocks profile? | Readable, self-contained page that **works in the private judging preview without extra explanation** |

### How it is actually decided **[C]**
> "The scorecard is **an overlay, not a ranking formula**. The questions and point ranges help both judge pairs cover the same ground and compare notes. **Totals do not automatically choose the winners or break a tie. The four judges make a shared, overall decision** from the conversation, repository, architecture HTML and run log."

→ **Four judges, two judge pairs.** **[C]** Each team gets 5 minutes with **one** pair (from 16:00), so **two of the four judges never meet us** — they meet the HTML, the repo and the log. That is precisely why the artifact must stand alone.

### The single loudest anti-signal **[C]**
> "**Complexity earns no points by itself.** Architecture judges favour systems that **do more of the work independently and can be rerun with less hands-on help**. A simpler system can still win either prize if it works well."
>
> "**No favoured architecture.** Simple loops, fixed pipelines and multi-agent systems are judged on how well they work."

→ Do **not** build a 14-agent swarm to look impressive. Build the smallest system that visibly does the six scored things, and *prove* each one. Autonomy and rerunnability are the stated virtues.

---

## 2. The accuracy formula (corrected) — and why it changes strategy

Source: https://openstocks.com/hackathon §Forecast Accuracy **[C]**

```
metric_score = min( |team − actual| / max( |WallStreet − actual|, floor ), 5.0 )
final = mean(metric_score over all 12)      # LOWEST wins
```
- **Floor:** 0.5 percentage points for % metrics; 0.5% of the absolute reported result for money/EPS; small fixed fallback if result is zero. **[C]**
- **Cap 5.0** per metric so one blow-up can't dominate. **Missing forecast = 5.0** (never skip a number). **[C]**
- Equal weight; each company = 25% of final. **[C]**
- Tie → count of metrics where you beat the Street; still tied → split. **[C]**
- Wall Street benchmark is **frozen internally at the submission deadline and never shown to teams**. **[C]**
- Only the four event companies count. **[C]**

**Strategic consequence [I]:** this is an *average of ratios*, not a gate. Round-1's advice ("don't hug consensus, you can't win otherwise") is **wrong here**. The right play is:
- Hug consensus on the 8–10 metrics where we have no genuine edge → scores land near 1.0, bounded.
- Deviate only where we have hard evidence (a disclosed monthly datapoint, a guidance bridge, an FX translation) → those score ≪1.0.
- The cap at 5.0 makes a bold-but-wrong metric cost at most 5.0/12 ≈ 0.42 of the average, so **one high-conviction deviation is cheap insurance-adjusted**. Two or three uncorrelated ones is the optimum.
- **Never leave a cell blank.** A missing number costs the same as being 5× worse than the Street.

**Target set [C]:**

| # | Company | Period | File | Metrics |
|---|---|---|---|---|
| 01 | **Home Depot** (HD) | FY2026 Q2 | `HD-FY2026Q2.xlsx` | Net sales USDm · Adj. diluted EPS USD · Comparable sales, total company % |
| 02 | **Analog Devices** (ADI) | FY2026 Q3 | `ADI-FY2026Q3.xlsx` | Revenue USDm · Adj. diluted EPS USD · Adj. gross margin % |
| 03 | **Hays plc** (LSE:HAS) | FY2026 | `HAS-FY2026.xlsx` | Net fees GBPm · Pre-exceptional basic EPS **pence** · Pre-exceptional operating profit GBPm |
| 04 | **Deere & Co** (DE) | FY2026 Q3 | `DE-FY2026Q3.xlsx` | Worldwide net sales & revenues USDm · Diluted EPS (GAAP) USD · Production & Precision Ag operating profit USDm |

Unit traps **[C]**: `4.5` means 4.5% for percentage metrics; Hays EPS `6.2` means 6.2 **pence**; Hays is **GBP** and a **full-year** (not a quarter). A frozen corpus of filings/transcripts/slides for all four ships in the repo; public research found during the event is allowed.

**[I]** Hays is the trap and the opportunity: a UK small/mid-cap staffer, thin analyst coverage, sterling, "pre-exceptional" definitions that are easy to get wrong. It is also *exactly* the manifesto's "coverage limitation" grievance made flesh. Getting Hays' definitions demonstrably right — and saying so — is the most on-thesis thing available.

---

## 3. Who the judges are and what they believe

Four judges **[C]**, unnamed publicly **[?]**. Overwhelmingly likely the Primer/Kernel AI core plus an OpenAI or AI Tinkerers person **[I]**.

| Person | Role | What they'll grade hardest **[I]** |
|---|---|---|
| **Seb Jory** | Founder/PM, Primer. Sole director & PSC of Kernel AI Ltd. Ex-Tellworth (ran ~$1bn UK Select L/S), ex-Liberum/Panmure equity strategist & **small-cap analyst**. Managing Partner, Lynott Partners | Does it *beat consensus*, and is the reasoning an analyst's? Small-cap literacy (→ Hays) |
| **Ruggero Gargiulo** | Co-founder, Head of Research. Ex-Tellworth analyst/quant. Author of Primer's eval doctrine | Eval rigour: variance, judges, relative scoring, path-not-just-outcome |
| **Alistair Smallwood** | Head of Applied AI, ex-equity analyst (Liberum → UBS → Lynott). Writes `theagenticanalyst.substack.com` | Ablations, null baselines, harness-vs-model attribution, statistical honesty |
| **Chris Mingard** | CTO, ML PhD Oxford | Determinism, reproducibility, code quality |

Sources: https://www.primerapp.com/about/, https://find-and-update.company-information.service.gov.uk/company/15117085 **[C]**

### 3.1 The core belief: **the harness beats the model**

Their loudest, most repeated public claim. **[C]**
- BigFinanceBench: "Primer runs on GPT-5.5 — on its own it scores 44.3% on the leaderboard; inside Primer, **79.1%. The gap is the harness**: what the model reads, which tools it can use, and what it has been taught about finance." — https://primerapp.com/evals/
- Seb Jory, LinkedIn 29 Jul 2026: "This is such a great demonstration of the power of an agent harness … next generational models are **not closing this gap** in finance, which is why we are laser focused on improving our harness." **[C]**
- Seb Jory, same post: "Next step is taking the Rogo benchmarks much further forward … (hint: not just build you a serviceable model, but **can it actually beat consensus**…)" **[C]** ← *He is personally invested in exactly tomorrow's question.*
- Alistair, 21 Jul 2026: "*What ~290 runs taught me about prompts, models, and **why the harness matters more than both**.*" **[C]**

**→ The single highest-scoring thing we can show is a same-model ablation: naked model vs our harness, on the same held-out task.** It is their own headline result, reproduced by us, in seven hours. Nothing else speaks their language as fluently.

Their own writeup of the ablation gives us the **exact sentence template** to copy — https://www.primerapp.com/blog/primer-tops-bigfinancebench/ **[C]**:
> "That objection has a very clean test. At the time of testing, Primer's agent was powered by GPT-5.5, the same model that sits at the top of the frontier table above. Given the benchmark's own tools and left to work alone, GPT-5.5 scores 55.8%. Inside Primer, the same model scores 79.1%. **Same brain, same questions, same judges. The model didn't change, so everything in that 23-point gap comes from the harness.**"

And their definition of a harness, which we should mirror in our own words: "everything that stands between a raw model and a finished piece of work: **what the model gets to read, which tools it can use, and what it has been taught about how the domain actually operates**." **[C]**

Corroborating third-party framing they'll recognise — DiligenceBench's "controlled ladder" of three reference harnesses (base loop → generic sandbox → finance harness), where "the finance harness outperformed the generic sandbox and the base loop on **every** model." https://www.llmdata.com/blog/diligence-bench **[C]** That is a ready-made shape for our ablation table: **3 rungs, same model.**

### 3.2 Ruggero's eval doctrine — 7 lessons (this *is* the meta-rubric)

Source: https://www.primerapp.com/blog/lessons-from-3-years-of-evals/ (1 Jun 2026) **[C]**

1. **Absolute scoring maxes out.** Rubrics stop differentiating once an agent is competent.
2. **Use relative / side-by-side scoring.** "Put the outputs next to each other… ask it to rank them and explain the differences." Judges struggle to grade quality past "good" in isolation.
3. **Use the strongest frontier model as judge — forget about costs.**
4. **Give the judge access to raw data.** "Without data access, the judge risks committing the sin any fund manager I ever met would punish hardest: **taking things at face value**."
5. **Variance applies to contenders *and* judges.** "We run every agent configuration **at least three times, often five** … then have the judge score each output multiple times. Only then do we aggregate. *After all… even boxing matches have 3 judges.*"
6. **Evaluate the path, not just the outcome.** Time, tool count, how often it went off-rails, what it struggled with. "The path can break ties."
7. **Next: live earnings prediction.** "Agents produce forecasts before earnings are released… we assess **both numerical accuracy and reasoning quality** … An agent can be 'right' for the wrong reason. So we evaluate both: **the forecast and the path to the forecast**."

Also: baselines matter — his baseline was "a **fixed-pipeline**, not an agent… a sequence of tightly-scoped prompts… I was even producing multiple notes and having a final model consider all those points of view." Beating that baseline was the milestone. **[C]**

**→ Lesson 7 is the whole hackathon.** OpenStocks is the productisation of Ruggero's stated roadmap. **[I]** We are building the thing he said he was going to build. Say that out loud.

**→ Lesson 5 is free points.** If we report a number from one run, we fail their published standard. **Run ≥3 seeds and show the spread.** Almost nobody else will.

### 3.3 Alistair's published architecture preference — copy this structure

Source: https://theagenticanalyst.substack.com/p/ai-failed-my-hedge-fund-interview (21 Jul 2026) **[C]**

He gave frontier models a real hedge-fund interview task (~290 runs, 5 runs per condition, 4 models). Findings, in his order:

| Test | Result |
|---|---|
| Ask directly | **0/20** |
| Prompt engineering (4 variants) | 0–1/20. "Prompts change what the model reads, **but not what it concludes**" |
| Blind/renamed to rule out memory | Still 0/20 open-ended; but **20/20** when told what question to answer → "The gap is in **choosing the question**, not answering it" |
| **6 specialist subagents + a boss** | Specialists found it **12/12**. **The boss ignored them 12/12.** "It sides with whatever the most reports point at" |
| Tournament of "unusual facts" | 0/6 — "Breadth has to be **assigned, not requested**" |
| **Hybrid: specialists → champion pass → judge** | **12/13.** "The structure changed the outcome" |

The winning structure, in his words:
> "Every specialist finding gets a **champion pass**, one call that says: assume this finding is the key to the whole company, **build the strongest case for it**, then give the boring explanation too. **Only then does the boss choose, comparing finished arguments instead of one-liners, judging by what each would mean for the company's value if true. Never by how many agents agree.**"

His stated conclusions **[C]**:
- "**Never let the boss side with the majority.** The right answer usually appears in only one report, so **majority voting kills it every time**."
- "**Findings must be developed before they're compared.** As a one-liner the right answer loses to scandal-sounding wrong ones."
- "Subagents are definitely the way to go for this class of problem."
- (Aside he'll enjoy: "The Anthropic models were much better at this than the GPT models" at the champion step.)

He reused the same structure as a **courtroom** (prosecution → defence → blind judge, run twice on rival labs' models, with 20 clean controls shuffled in) in https://theagenticanalyst.substack.com/p/finance-ai-benchmarks-are-misleading. **[C]**

**→ Design mandate [I]: our committee must be `assigned-breadth specialists → champion/steelman pass → impact-weighted adjudicator`, and we must state in the HTML that we do NOT aggregate by vote or by averaging.** Averaging N model forecasts is the obvious thing every other team will do, and the Head of Applied AI has published 290 runs of evidence that it is the *wrong* thing. Saying "we explicitly rejected majority voting, here's why" is the highest-signal sentence available to us.
**Caveat [I]:** the numeric task differs from his forensic one — for a *point estimate*, some aggregation is unavoidable. The defensible line is: **breadth assigned per driver; each driver's estimate developed into a full evidenced bridge; the adjudicator picks/weights by evidence strength, not by count** — and a median is a stated fallback, not the mechanism.

### 3.4 Alistair's statistical red lines — the "coin-flipping monkey" post

Source: https://theagenticanalyst.substack.com/p/my-chatgpt-trading-agent-is-up-68 (24 Jul 2026) **[C]**

He tore down "my ChatGPT trading agent is up 68%" by simulating 10,000 random monkeys and 100,000 leaderboards. Extract the rules he grades by:

- **A null model is mandatory.** "Judge it against the full range of outcomes that the same process could have produced."
- **A naive-but-plausible baseline beats most sophistication.** His 3-month momentum monkey (+21.5% median) beat 6 of 8 AI models.
- **"The best of N draws" is a different statistical object.** Report the median, not the winner.
- **Win rates computed on closed trades only are an artifact.** Beware metrics that quietly exclude the losses.
- **Point-in-time discipline is non-negotiable.** He re-ran with a point-in-time universe to check it didn't flatter him; he attacks FrontierFinance because "the research agent can use 2026 web results to answer questions dated years earlier… **hindsight supplied by the evaluation setup itself**."
- **Publish limitations.** He ends with "4 honest limitations" and a **pre-registered prediction**.
- **Repeat runs and error bars, or it's not a result.** "A single score is one draw from a distribution… **the honest unit is a range, not a rank**."
- **He audits his own audit**, blind, with controls, on two rival labs' models. "You do not have to take a competitor's word for it."

**→ These are the four judges' allergies. Any unqualified performance claim on our page will be read as the thing he spent two posts demolishing.** Conversely: a null baseline + 3 seeds + a limitations section is *cheap* and lands directly on "Honesty and self-knowledge" (6 pts) and "Validation and reliability" (12 pts).

Also from his eval-critique post **[C]**: they hand-checked and found errors in **12% of BigFinanceBench's public questions** and **~73/220 FrontierFinance keys**. These people *check the answer key*. **Do not overstate anything they can verify against the repo.** "Diagram and accuracy" (10 pts) is explicitly graded by **checking the diagram against the code**.

### 3.5 What Primer's own harness does (mine these for design vocabulary) **[C]**

From https://primerapp.com/evals/ and /product/:
- **Read the full filing, not isolated snippets.** Their stated FinRetrieval edge: "Primer reads the full filing, not isolated snippets… **Company, period, unit, and source context stay intact**." → *Chunked-embedding RAG over 10-Qs will read as naive.* Note their own starter helper's disclaimer echoes this: "Its results are **research leads**, so **check every figure in the cited source**." **[C]**
- **Never invent a figure.** "Every adjustment needs evidence and a clean bridge… **Invented figures or unsupported one-offs fail outright**."
- **Don't drive Excel cell-by-cell.** "Instead of forcing the agent to work cell by cell in Excel, Primer uses state-of-the-art modelling infrastructure, then converts the finished model to Excel." → **Model in code; write the .xlsx last.** This exactly matches the hackathon's `submission/` step.
- Multi-agent is their own architecture: "We use a **multi-agent architecture designed for financial reasoning** … It's transparent: **every insight is cited and explainable**." (Primer LinkedIn, reshared by Jory) **[C]**
- Their earnings-preview backtest: +34% alpha, 2,727 calls, 203 days, 53.6% hit rate, 1.42 Sharpe. **[C]**

---

## 4. OpenStocks — vocabulary, aesthetics, and the judging preview

### 4.1 Mirror their words **[C]** — https://openstocks.com/manifesto

Exact phrases to reuse: **"AI Consensus"**, **"1 rule: no human analysts"**, **"the live benchmark for AI agents"**, **"Beat Wall Street"**, **"equal compute goes into every covered company, whether it's a Magnificent 7 or a small cap"**, **"'always-on' agents can continuously cover a company… without emotional attachment"**, **"no hidden agenda"**, **"No hiding."**

Their four-part critique of Wall Street = the rubric behind the rubric:

| Their grievance | Their promised AI fix | How our architecture should visibly embody it |
|---|---|---|
| **Bias / agency problem** | "no hidden agenda… the live benchmark encourages truth" | Every number traces to a cited source; no hand-tuning; declared human input |
| **Coverage limitation** | "equal compute… Magnificent 7 or a small cap" | **Identical pipeline, identical compute across all four companies. No per-ticker special-casing.** Hays gets what Home Depot gets |
| **Forecast staleness** | "always-on agents… continuously cover" | Rerunnable on one command; show a re-forecast at T-90/T-60/T-0 |
| **Accuracy (?)** | "To be proved" | Backtest on prior reported quarters vs the Street's error for the same quarters |

**→ "Uniform compute across all four companies, no special-casing" is the single cheapest way to look on-thesis while most teams hardcode their best ticker.** **[I]**

### 4.2 Their design system — extracted from their shipped CSS **[C]**

`https://openstocks.com/_next/static/chunks/0qplnb8yheuhf.css`:

```css
--font: "DM Sans", system-ui, sans-serif;
--mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
--bg:#f4f7fb;  --panel:#fff;  --panel-soft:#f8fafc;  --panel-zebra:#f4f7fa;
--ink:#243044; --text:#1f2937; --text-2:#344054;
--muted:#667085; --muted-2:#98a2b3; --muted-3:#475467;
--blue:#2362dc;                      /* accent */
--green:#0f8f5f; --positive-text:#067647; --green-soft:#ecfdf3; --green-soft-line:#abefc6;
--red:#d8483e;   --negative-text:#b42318;
--gold:#8a6a12;  --orange:#d97706;
--line:#dbe2ec;  --line-soft:#e8edf3;
--warning-bg:#fffaeb; --warning-border:#fedf89; --warning-text:#93370d;
--radius-sm:6px; --radius-md:8px; --radius-lg:10px; --radius-xl:12px; --radius-pill:999px;
--ls-caps:.05em; --ls-wide:.08em;  --max:1280px;
```

Primer's own palette (https://www.primerapp.com/_next/static/chunks/0k7qz_0ry1afv.css) **[C]**: `--hp5-paper:#f0efe9` (warm cream), `--hp5-ink:#15171a`, `--hp5-green:#1cae54`, `--hp5-mint:#7ffaae`, `--hp5-line:#15171a1a`, `--hp5-radius:14px`, fonts **Geist / Geist Mono / Newsreader (serif)**.

**→ Both companies are LIGHT-MODE, institutional, restrained.** **[I]** Every other team will ship a dark neon-on-black "AI architecture" page. Shipping a clean light page in DM Sans + JetBrains Mono on `#f4f7fb` with a `#2362dc` accent will look like it came out of their own codebase. This is the aesthetics prize, cheaply.

Their table idiom, verbatim from their CSS **[C]**: uppercase mono column headers at **9–10px, weight 750–800, letter-spacing .05–.08em, colour `--muted-2`**, on `--panel-soft`, 1px `--line-soft` borders, 13px body. Their eyebrow labels: mono, uppercase, 10px, weight 800, colour `--blue`.

**Their chart convention — steal it exactly** (`.agent-series-*`) **[C]**:
```css
.agent-series-agent .recharts-line-curve { stroke:#2362dcb8; stroke-width:2.6px; }   /* your agent  */
.agent-series-ws    .recharts-line-curve { stroke:var(--muted-2); stroke-width:1.6px;
                                           stroke-dasharray:3 3; }                   /* Wall Street */
```
**Solid blue = our agent. Grey dashed = Wall Street.** Error colouring: positive `#067647`, negative `#d92d20`, pending grey. A forecast-vs-consensus-vs-actual chart drawn this way is literally their product's visual language.

Also present in their product CSS **[C]**: `.agent-scorecard`, `.agent-forecast-cell`, `.agent-history-comparison`, `.agent-error-positive/negative/pending`, `.race-scoreboard`, `.boxscore`, `--dash-row-h:62px`. And from Primer's product page, the earnings-preview card idiom **Metric | Est. | Cons. | Δ** with margin deltas in **bp**. **[C]**

### 4.3 ⚠️ How the judges will physically view our HTML — the highest-leverage detail

From the same CSS, the admin judging UI **[C]**:

```css
.admin-hackathon-review      { width: min(1500px,100%); height: min(900px, 100vh - 48px); }
.admin-hackathon-review > header { min-height: 84px; }
.admin-hackathon-review-body { display:grid; grid-template-columns: minmax(0,1fr) 330px; }
@media (narrow)              { grid-template-rows: minmax(420px,55vh); grid-template-columns:1fr;
                               overflow-y:auto; }
.admin-hackathon-preview-shell iframe { width:100%; height:100%; background:var(--panel); }
```

Decoded **[C on the CSS, I on the arithmetic]**:
- Our file is rendered **in an `<iframe>` inside a modal**, beside a **330px metadata sidebar**.
- Usable iframe ≈ **1140px wide × ~800px tall** on a big screen; on a laptop it collapses to a **single column as short as 420px**.
- There is a **`.admin-hackathon-review-button.shortlisted`** state styled in warning-amber → **a shortlisting step exists** inside judging.

**→ Hard design constraints:**
1. **Everything decisive must fit in the first ~420px of height at ~1100px width.** Treat 1100×420 as the fold. This is the non-obvious edge nobody else has.
2. Target width **900–1200px**; must not break at 700px. Set `max-width` and centre; do **not** design for 1440+.
3. **No `100vh` layout tricks, no `position:fixed`** — the iframe viewport is not the screen.
4. Must render **offline with zero network** (self-contained, inline CSS/JS, no CDN, no Google Fonts). **Set a system-font stack fallback** — DM Sans/JetBrains Mono will **not** load in the sandbox unless base64-embedded, and embedding is not worth the bytes. Use `ui-monospace, SFMono-Regular, Menlo, monospace` and a clean system sans; keep *their* sizing/weight/letter-spacing conventions, which is what actually reads as native.
5. It is `background: var(--panel)` behind the iframe = **white**. Paint our own background explicitly.
6. It will also be published on our OpenStocks profile (Craft criterion) → no emails, no secrets. **[C]** "Do not commit `entry.json` or put emails in the architecture HTML."

---

## 5. Social prizes — RESOLVED

Source: https://openstocks.com/hackathon §Social **[C]**

- **Two prizes, $500 each, awarded to an INDIVIDUAL, not the team.** "$500 for the best X post and another $500 for the best LinkedIn post. Enter either platform or both." **Closes 17:00** (earlier than everything else).
- **Required X tags: `@_openstocks`, `@primerapp_`, `@AITinkerers`, `@openai`.** **[C]**
- **Required LinkedIn tags: Primer, OpenAI, AI Tinkerers** ("OpenStocks does not need a separate LinkedIn tag"). **[C]**
- **"A post missing a tag will not qualify."** **[C]**

**Qualification steps [C]:** (1) share the official OpenStocks launch post on **both** X and LinkedIn; (2) publish the post you want judged — quote/repost with commentary, or a separate post; (3) include every required tag; (4) enter its link on the page **before 17:00**.

**Judged on [C]:** "Thoughtful insight — teach people something genuinely useful about the build, what you learned, or where the industry is going"; "Specific and authentic — use your real experience and choices, rather than generic event promotion"; "Clear and relevant. **Engagement is only a tie-breaker.**"

**The launch-post URLs do not exist yet.** **[C]** The page says: "Opens on Sunday — Social entries open once both launch posts are live. **The direct X and LinkedIn links will appear here.**" I verified openstocks.com currently exposes **no** social links in its markup and no `twitter:site` meta tag. **→ Get the links from https://openstocks.com/hackathon#social on the day.**

**⚠️ Disambiguation confirmed [C]:** the real X handle is **`@_openstocks` (leading underscore)**. `@openstocks_hq` is the unrelated BNB-chain DeFi company (openstocks.xyz). Round-1's caution was correct and is now resolved. Primer is **`@primerapp_` (trailing underscore)**.

**Playbook [I]:** this is the best $/effort on the board and it is *individual* — up to 4 team members can each enter both platforms. The judging criteria reward a genuine technical lesson, so **the natural post is a screenshot of our ablation table + one paragraph on what the harness changed.** Assign at 11:15; draft the insight by 14:00; publish and enter by 16:30. Do not leave it to 16:55.

---

## 6. Field, format, and competition level

From the AI Tinkerers side (research pass 2) **[C]**:
- **82 attending** signalled on https://london.aitinkerers.org/, teams ≤4 → **~20–25 teams [I]**.
- Attendee pool advertised as engineers from Google, Amazon, Meta, **Goldman Sachs and Bloomberg**, Kaggle Experts, repeat hackathon winners. **[C]**
- London's platform rubric historically: Running Code / Innovation / Real-world Impact / Theme Alignment, 25% each on a 1–5 scale. **Irrelevant tomorrow** — OpenStocks published their own 100-point rubric, which overrides it. **[C]**
- Prior London winners (Sep 2025 Pixel Panel; Dec 2025 NPC / Recall / FlatScout) were **consumer-legible, demo-first products, not infrastructure or eval plays**, and showcase entries were video-led with stack-specific descriptions. **[C]**
- Portal results pages historically never get published; winners are announced on LinkedIn only. **[C]**
- **Submission completion at London is poor** (Sep 2025: 120 builders, 35+ teams, only 4 entries in the public showcase) → **a complete, well-documented entry is disproportionately rewarded.** **[I]**

**[I] Read on the field:** most teams will ship "call GPT-5.6 four times, average the numbers, dark-mode landing page." The rubric's 70 points for *system* evidence — traces, rejected values, run logs, custom tools — is aimed squarely at separating from exactly that. The published rubric is public, but **most teams will not read it carefully and almost none will have read Primer's eval blog or Alistair's Substack.** That asymmetry is our whole edge.

---

## Implications for our build

### A. Priority order for the architecture prize (by points × winnability)

| Rank | What to build/show | Rubric line hit | Why it wins |
|---|---|---|---|
| **1** | **The ablation ladder.** Same model, 3 rungs: (a) naked one-shot "give me the number", (b) + our tools/retrieval, (c) full harness. Scored on **held-out prior quarters** of the same 4 companies. One table, 3 rows | Forecasting approach 16 · Agent harness 9 | Their own headline result, reproduced. Jory has said "the gap is the harness" in public repeatedly. Nothing else is this on-message |
| **2** | **Evidence→number traceability for all 12 figures.** Every submitted number expands to its bridge: source doc, page/section, extracted value, transformation, assumption | Model quality 12 · Data approach 12 | Literally the wording: "Can judges follow how evidence and assumptions become each of the 12 final numbers?" This is the second-biggest block and the most mechanically achievable |
| **3** | **A validation layer that visibly REJECTS things.** Unit checks (pence vs £, USDm vs USDbn, % as 4.5), period checks, cross-source conflict detection, sanity bounds vs history. **Show a table of what it caught and rejected** | Validation & reliability 12 | Rubric names "**rejected values**" as evidence. A rejection log is rare, cheap, and unfakeable |
| **4** | **≥3 seeds per company + spread.** Report median and range, never a single draw | Validation 12 · Honesty 6 | Ruggero: "at least three times, often five." Alistair: "the honest unit is a range, not a rank" |
| **5** | **Named custom tools.** A filing fetcher that returns **full sections not snippets**, a table extractor, a units normaliser, a consensus-delta checker. Show before/after impact of each | Tooling & ergonomics 9 | "Did the team build useful search, extraction or checking tools… and evidence of how they improved the run" |
| **6** | **Uniform compute across all 4 companies + one command.** No per-ticker branches. `final command` runs all four | Agent harness 9 · manifesto "coverage" | On-thesis and directly rewarded: "do more of the work independently and can be rerun with less hands-on help" |
| **7** | **A null baseline.** "Last reported value carried forward" and/or "consensus itself" as the monkey. Show our error vs it | Honesty 6 · Forecasting 16 | Alistair's monkey post is a 3,000-word argument that a result without a null model is not a result |
| **8** | **Honest failure section.** What we tried, what we abandoned, where it breaks. Name the Hays pence/pre-exceptional trap and how we handled it | Honesty & self-knowledge 6 | Explicitly scored; almost nobody does it; costs 20 minutes |
| **9** | **A stated-conventions table for all 12 metrics.** For each: the exact definition we forecast to, and the alternative construction we rejected | Model quality 12 · Data approach 12 · Honesty 6 | Primer's closing argument in their BigFinanceBench post is precisely this: *"Ask two good analysts and you'll get two defensible numbers… choosing between the ways, then saying which you chose and why, is the actual skill. **We'd rather lose points to a stated convention than win them from a guessed one.**"* **[C]** Our 12 metrics are a minefield of exactly this — *Adjusted* diluted EPS (HD, ADI), *comparable sales, total company* (HD), *adjusted* gross margin (ADI), *pre-exceptional* basic EPS in pence and *pre-exceptional* operating profit (HAS), *GAAP* diluted EPS vs adjusted (DE), and the *Production & Precision Ag* segment boundary (DE). A one-page convention table is ~30 minutes and hits three scored categories at once |

**Committee design [I]:** assigned-breadth specialists (one per driver, not one per "opinion") → **champion/steelman pass per finding** → impact-weighted adjudicator. State explicitly on the page: *"We do not aggregate by majority vote or by averaging model outputs"* and cite the reason. If we do fall back to a median, declare it as a fallback and say why.

**Anti-patterns to avoid, from their own words [C]:**
- ❌ Chunked embedding RAG over filings (they brag about reading *full* filings)
- ❌ Driving Excel cell-by-cell (model in code; write .xlsx last)
- ❌ Averaging / majority-voting model outputs (Alistair's 12/12 failure mode)
- ❌ Any invented or unsourced figure ("fail outright")
- ❌ Agent count as a flex ("complexity earns no points by itself")
- ❌ Single-run numbers with no variance
- ❌ Hindsight leakage — enforce point-in-time in the *tools*, not just the prompt

### B. The architecture HTML — concrete outline

**Constraints:** single self-contained file, inline everything, no network, ~1100×420 fold, ≤1500px wide, locks **17:15**, must match the code (checked), no emails/secrets, start from the repo's `architecture/index.html`. Build it **from 15:00**, not 17:00 — and note the 16:00–17:15 judge conversation means a **draft should exist by 15:45** so we can show it in the 5-minute slot.

**Design language — resonate with their system, don't clone the marketing site** (cloning reads as sycophantic and costs aesthetics points) **[I]**:

- **Type, system fonts only (nothing loads offline).** Body/UI `-apple-system, "Segoe UI", Helvetica, Arial`. **Headings in Georgia at 500–600, tracking `-0.01em`, `text-wrap:balance`.** Numbers/labels `ui-monospace, SFMono-Regular, Menlo`. Georgia *is* Primer's own declared serif fallback (`Newsreader → Georgia`), so serif headings land inside their visual world at zero bytes — and a serif heading is the cheapest way to exit the AI-generated-page distribution.
- **Colour.** Page `#f4f7fb`, panels `#fff`, ink `#243044`, accent `#2362dc`, positive `#067647`, negative `#b42318`. Flat fills only — **the blue→purple gradient is the single most reliable AI-slop fingerprint**, so flat `#2362dc` is fine but a gradient is fatal.
- **⚠️ Contrast — I computed their palette; two of their own tokens fail** (ratios vs `#f4f7fb`):

  | Token | Ratio | Verdict |
  |---|---:|---|
  | `--muted-2 #98a2b3` | **2.40:1** | **FAILS.** They use this for 9px uppercase mono table headers. Copied literally it is illegible on a laptop or projector |
  | `--green #0f8f5f` | 3.82:1 | Large text / fills only |
  | `--muted #667085` | 4.63:1 | Marginal |
  | `--positive-text #067647` | 5.30:1 | Use this for green **text** |
  | `--blue #2362dc` | 5.07:1 | OK |
  | `--muted-3 #475467` | 7.15:1 | **Use this for table headers instead** |
  | `--line #dbe2ec` | 1.21:1 | Invisible on a washed-out projector |

  → Keep their *style* (uppercase mono, weight 750–800, tracking `.08em`) but set table headers at **10–11px in `#475467`, not 9px in `#98a2b3`**. Nothing below 12.5px for methodology prose. For any border that carries meaning, darken the hairline to ~14–18% ink rather than `#dbe2ec`.
- **Structure.** Sections separated by hairline top rules, not cards. Container ~1160px. Measure 44–56ch. **Numbered `01/02/03` ordinal lists, not three icon cards** — both Primer's evals page and the OpenStocks hackathon page use exactly this device. Numbers always mono + `font-variant-numeric: tabular-nums` + right-aligned; analysts are hyper-sensitive to numeral alignment.
- **Length: ~2,000–3,000 words, 6–8 screens.** Attention data: ~35% of desktop readers never scroll at all, and attention peaks around 550px then again ~1200px — which agrees with the 420px iframe fold. Headline claim, ablation and diagram must all sit above ~1200px.
- **No** dark mode (Primer's site has no `prefers-color-scheme` rule at all — one committed light theme beats two mediocre ones), no glow, no emoji, no `rounded-2xl + shadow-md` on everything, no centred pill eyebrow above the h1, no Sparkles/Zap icons, no `opacity:0 → translateY(20px)` section reveals, no pure `#000`/`#fff`.

**⚠️ Offline/JS constraints [C on the mechanism, I on their setup]:** assume `fetch()` and `<script type="module">` are unavailable (CORS blocks both under `file://`, and the preview is sandboxed). **Keep all JS inline and classic-script.** Inline SVG, `<canvas>` and `data:` URIs are safe. The page must be fully legible with JS disabled entirely.

| § | Section | Height budget | Content |
|---|---|---|---|
| — | **Above the fold (≤420px)** | — | Agent name + one-sentence description. **The ablation number as the hero**: "Same model. Naked: X. In our harness: Y." Then a 4-up stat strip: *12/12 forecasts traced · N sources cited · M values rejected by validation · 3 seeds per company*. One line: what the system is, in plain English |
| 1 | **The pipeline diagram** | ~500px | **Inline SVG**, horizontal, left→right: Corpus + public research → assigned-breadth specialists (one per driver) → champion pass → adjudicator → validation gate → workbook writer. Annotate each edge with what actually flows. **Label each node with the real file/function name from the repo** — "Diagram and accuracy" is scored by checking it against the code |
| 2 | **Worked example: one number, end to end** | ~450px | Pick one metric (Hays net fees, ideally). Source doc → extracted line → transformation → assumption → final figure. This single section carries Model quality (12) |
| 3 | **Ablation table** | ~300px | 3 rungs × same model, on held-out prior quarters. Columns: config · mean ratio vs Street · median · spread (3 seeds) · n. Plus the null baseline row |
| 4 | **Validation & rejections** | ~300px | What the checker enforces (units, periods, sign, bounds, cross-source conflicts) and a real table of **caught/rejected** values from the run |
| 5 | **The 12 forecasts** | ~350px | Their own idiom: **Metric \| Est. \| Cons.\* \| Δ** grouped by company, mono numerals, green/red deltas, margins in bp. (\*mark clearly if we don't have the Street's number — the benchmark is frozen and not supplied to teams) |
| 6 | **Data approach & point-in-time** | ~250px | Sources, how currency/recency is checked, how we prevent hindsight leakage in the *tools* |
| 7 | **What we tried and abandoned / known weaknesses** | ~250px | Honest, specific, named. Include the traps (Hays pence, pre-exceptional, ADI adj. gross margin, DE segment op profit) |
| 8 | **Reproduce it** | ~150px | Final command, final commit hash, expected runtime, where the log lives |

**Interactivity — the evidence says build much less than instinct suggests [C on the studies, I on the application]:**

The HCI literature is damning for a cold read. Mosca/Ottley/Chang (CHI 2021): across 5 interaction techniques × 3 designs, **no technique improved task performance, hover significantly *decreased* accuracy for high-spatial-ability users, and 57% of participants never interacted at all.** Kaur et al. (CSCW 2024): interactive interpretability tools produced **lower** mental-model accuracy and **lower** usability than static equivalents, at higher cognitive effort. Dragicevic's rule: *a reader must be able to freeze the page at any point and have it make sense.*

- ✅ **Build (in this order):**
  1. **Scroll-triggered bar growth + number count-up** on the ablation chart — `transform: scaleX()` + IntersectionObserver, ~20 lines. This is Primer's *own* only interaction. Pure polish, zero comprehension cost.
  2. **A static, fully-labelled trace of one real run** — timings, tool calls, tokens, the retry that failed. Not interactive. Highest-value single artifact; directly answers Ruggero's "evaluate the path".
  3. **`<details>` "show the working" disclosures** under each claim — native, zero JS, works offline, mirrors Primer's own "Read the full analysis →".
  4. Sticky section nav / progress rail with anchors — helps a skimmer, invisible to a reader.
- ❌ **Cut:** hover-only tooltips (measurably *harmful* to experts, dead on a projector); parameter sliders (the 57% statistic kills them); **tabbed content** (hides half the argument from a skimmer — so drop the per-company tab idea, stack all four); animated diagrams; charting libraries; dark-mode toggle; anything needing >30 lines of JS.

Craft is 4 points; Clarity is 10 and Diagram-accuracy is 10. **Static and legible beats clever**, and two of the four judges will only ever see this file.

**⚠️ Diagram rule — the highest-leverage single instruction here [C]:** Bertrand Meyer, *"Beware of boxes bearing arrows."* The canonical failure of architecture diagrams (and the standard critique of ByteByteGo-style visuals) is **labelled boxes with unlabelled arrows — experts read the edges.** For each edge, annotate what flows: payload, format, whether it is model-generated or deterministic, and what happens on failure. Include a legend and a title. And do not use a box-and-arrow diagram to convey a *sequence* — if order matters, give it a temporal axis.

**Two sections most teams omit, both cheap and heavily rewarded [I]:**
- **Non-goals.** "A doc without non-goals has agreed to everything by omission." Say what we deliberately did not build (e.g. no live market data, no per-company tuning, no fine-tuning).
- **Alternatives, steelmanned.** Give each rejected design its genuine advantages *first*, then why we rejected it. One-line strawmen read instantly as approval theatre. This is also where "we rejected majority voting" belongs, and it feeds Honesty (6 pts) directly.

**The test to apply to every sentence on the page [I]:** *could a reasonable expert disagree with this?* If not, it is decoration — cut it. Adjectives where numbers belong ("robust", "scalable", "significant") are the tell these judges react to hardest.

### C. Schedule (real times)

| Time | Action |
|---|---|
| 10:00 | Doors. **Whole team present** |
| 10:30–11:15 | Briefing — **capture any rubric deltas verbatim**; ask: is the Street benchmark snapshot taken at 18:00 today? |
| 11:15 | Build starts. Assign: (1) pipeline, (2) tools+validation, (3) ablation/backtest harness, (4) **architecture HTML + social** |
| ~13:00 | End-to-end forecast for one company at any quality |
| 14:00 | Social insight drafted |
| 15:00 | All 12 numbers exist; **HTML drafting starts**; ablation running |
| 15:45 | HTML draft complete enough to show a judge |
| **16:00–17:15** | **5-minute judge-pair conversation** — the most heavily weighted single moment. Lead with the ablation |
| **17:00** | **Social entry closes** (post published + link submitted) |
| **17:15** | **Architecture HTML LOCKS.** Final run begins (45 min) |
| 17:30 | Uploads open — manual, per company |
| **18:00** | Hard deadline: 4 workbooks uploaded + `entry.json` recorded |

### D. Three sentences to put on the page

1. *"Same model, three harnesses: naked one-shot scores X, our full harness scores Y on held-out quarters — the gap is the harness, not the model."*
2. *"We deliberately do not aggregate by majority vote: the right answer usually appears in one place, and voting kills it. Findings are developed into full evidenced bridges before anything compares them."*
3. *"Every one of the 12 numbers traces to a cited line in a source document; N candidate values were rejected by the validation layer before submission; here is what we abandoned and where this system will fail."*

### E. Open questions for the 10:30 briefing **[?]**
1. Is the Wall Street benchmark snapshotted at 18:00 today, or at each company's report date?
2. Do the four judges see the repo, or only the HTML + log + conversation?
3. Does the 5-minute pair conversation have a fixed question list (the rubric's "The question judges ask" column suggests yes)?
4. Confirm the `architecture/index.html` template's expected structure — does it prescribe sections?
5. Any constraint on the HTML file size?
