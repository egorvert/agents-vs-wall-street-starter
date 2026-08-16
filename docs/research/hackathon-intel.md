# Agents vs Wall Street — Event & Organizer Intel

Compiled 15 Aug 2026 (night before). Event is Sun 16 Aug 2026, London.

Legend: **[C]** = confirmed, sourced from a primary page. **[C-portal]** = confirmed by us from the signed-in hackathon portal (not publicly verifiable). **[I]** = inferred / my reasoning. **[?]** = unknown, must ask on the day.

---

## 0. The single most important finding

**Primer and OpenStocks are the same company.** Both are operated by **Kernel AI Ltd**, UK company **15117085**.

- OpenStocks Terms: "OpenStocks is operated by Kernel AI Ltd, a UK company (number 15117085)" — https://openstocks.com/terms **[C]**
- OpenStocks Privacy Policy: "Team email addresses and the private entry record are available only to specifically authorised event staff at **Kernel AI Ltd (Primer and OpenStocks)**" — https://openstocks.com/privacy **[C]** ← explicit
- Primer job listing: "Developed by UK-based engineering team **Kernel**, Primer is an AI-powered app delivering financial reporting insights" — https://app.welcometothejungle.com/jobs/duHHNGsP **[C]**
- Companies House: KERNEL AI LTD, inc. 5 Sep 2023, 128 City Road London EC1V 2NX, SIC 62020. Sole director & 75%+ PSC: **Sebastian Hugh Richard Jory** (b. Mar 1989). — https://find-and-update.company-information.service.gov.uk/company/15117085/officers **[C]**
- Seb Jory is Primer's founder (also Managing Partner at Lynott Partners, ex-Tellworth fund manager, ex-Liberum/Panmure equity strategist). — https://www.primerapp.com/about/ **[C]**

**Why this matters:** "Presented by Primer · OpenStocks · AI Tinkerers" is really *one sponsor plus the venue community*. The judges for the architecture prize are the Primer team — professional equity analysts turned AI-harness engineers who publish evals for a living. They are not generalist hackathon judges. Design for *them*.

---

## 1. The event — confirmed facts

Source: https://london.aitinkerers.org/p/agents-vs-wall-street-10k and portal https://london.aitinkerers.org/hackathons/h_6eHoon48MVI

### Framing **[C]**
> "Agents vs Wall Street is a one-day hackathon where you build an AI agent that forecasts a real company's earnings, then send it head-to-head with Wall Street consensus. **One rule: no human analysts.**"

> "An autonomous agent that predicts a company's next results, **revenue and EPS**, from whatever data and tools you choose. You bring the approach. **We bring the data, API credits, and tooling** so you're building within the first half hour, not fighting API keys."

### Schedule (from portal, authoritative) **[C]**
```
09:00  Doors open, coffee and croissants
09:30  Kickoff talk
10:00  Hack begins
12:00  Lunch
17:00  Judging begins, dinner
19:00  Finalists present
20:00  Beer
20:30  Event ends
```
> "**IMPORTANT: Full team must be present for kickoff talk to be eligible for the prize**"

Note the discrepancy: prose says "9am to 7pm", listing says 9AM–8PM BST, portal schedule ends 20:30. **Trust the portal.** Practical build window is **10:00 → 17:00 = 7 hours**, not 10. Judging starts at 17:00 — the artifact must be *done* by then, with 19:00 finalist presentations as a separate, later stage.

### Prizes **[C]**
$10,000 pot, split two ways:
1. **Accuracy** — scored after the event, once "your companies" report. Compared to actual results *and* to Wall Street consensus.
2. **Design** — judged on the day. **Two** awards: *best agent architecture* (how the forecasting agent is engineered) and *best aesthetics* (how it looks and presents).

Portal's "Judging Criteria" and "Prizes" sections are **published but empty** as of tonight. **[C]** They will likely be filled at kickoff — treat published criteria as live intel to capture at 09:30.

Additionally, from our portal view: **50% architecture (judged on the day) / 50% accuracy (~6 weeks later)** **[C-portal]**, and **$8.5k OpenAI credits, criteria TBA** **[C-portal]**. I could not independently verify either on public pages.

### Format & logistics **[C]**
- 9am–7pm central London (exact venue given to accepted attendees only).
- "A short intro to frame the challenge, **three build blocks**, mentors from our partners on hand, then demos and the design judging live on stage."
- Teams: create team in portal → invite by email → **each teammate must accept and complete profile**. AI Tinkerers London standard is **teams of up to 4** (from the Sept 2025 event page) **[I]** — not restated for this event.
- ~82–163 attending signals on the listing. Attendee pool described as AI/ML engineers from Google, Amazon, Meta, **Goldman Sachs, and Bloomberg**; Kaggle Experts; repeat hackathon winners. **[C]** Expect genuine finance-domain competition in the room.
- Mentors: "mentors from our partners" — unnamed. **[?]** Judges: unnamed publicly. **[?]** Expect Primer/OpenStocks staff + AI Tinkerers-recruited judges (historically 6–11 judges, many YC founders).

---

## 2. Submission mechanics — reverse-engineered from the privacy policy

This is the highest-value intel in this document. OpenStocks' privacy policy enumerates **exactly what the submission form collects**, which tells us the deliverables before they're announced.

Source: https://openstocks.com/privacy (last updated **15 Aug 2026** — i.e. yesterday/today, written for this event) **[C]**

> "If your team enters the main Agents vs Wall Street competition, we collect the private entry record you upload: the **agent name and description**, each team member's name and email address, the declared **build style, harness, models, languages, frameworks, pre-existing components and human input**, plus the **repository URL**, **uploaded architecture HTML file**, **final commit** and **final command**."

And how it's used:

> "connect the declared system to its **final repository commit** and uploaded **architecture HTML**, judge eligibility and the **Architecture & Design Prize**"

### What this tells us **[C on the fields; I on the implications]**

| Field collected | Implication for our build |
|---|---|
| **uploaded architecture HTML file** | The architecture prize is judged from a **single self-contained HTML file**. This is the aesthetics deliverable too. Not a slide deck, not a README. Build this deliberately — it is 50% of the on-the-day score. |
| **final commit** + **final command** | The repo must be **re-runnable from one command at one pinned commit**. Determinism and a clean entrypoint are graded, implicitly. |
| **repository URL** | Public/accessible GitHub repo required. |
| **declared harness, models, languages, frameworks** | They want the *harness* story. Primer's entire public identity is "the harness beats the model" (see §4). Name your harness. |
| **declared pre-existing components and human input** | Honesty disclosure. "No human analysts" is enforced by self-declaration. Do **not** hand-tune the final numbers — declare human input as design/plumbing only. |
| **build style** | **[?]** Likely "vibe-coded / hand-written / agent-written". Unknown enum. |
| Prize name: **"Architecture & Design Prize"** | The two on-the-day awards are administered as one named prize bundle. |

### The separate "social competition" — free prize money **[C]**
> "If you enter the Agents vs Wall Street **social competition**, we collect your name, email address, team or agent name, the **X or LinkedIn post links** you choose to enter, **your confirmation that you shared both official launch posts**..."
> "...judge the **two social prizes**..."

There are **two additional social prizes**, entered by sharing **both** of OpenStocks' official launch posts on X and/or LinkedIn and submitting the links. This does **not** require an OpenStocks or Google account. Near-zero effort, non-trivial expected value. **Assign this to one person at ~10:00 on the day.** OpenStocks' launch posts will go live 16 Aug ("Doors open August 16"). **[I]**

### How OpenStocks runs verified agents **[C]**
> "For forecasts submitted from a verified repository, we also **fetch and run that repository itself**, which can include information embedded in its files and commit history."
> "verified repositories run in **isolated Modal sandboxes**"

**Architectural constraint:** if we want to be "Community Verified" tier (and plausibly for accuracy scoring), our repo must execute **inside a Modal sandbox** — fresh container, no local state, no interactive auth, secrets injected as env vars, and network egress that we should not assume is unrestricted. Design for cold-start reproducibility from commit → forecast JSON.

### OpenStocks' own stack (useful for integration guesses) **[C]**
Google sign-in, **Supabase** (DB + auth), **Render** (hosting), Resend (email), **PostHog EU** (analytics), Tremendous (payouts), **OpenAI** (used to match extracted workbook tables to consensus metrics), Google AI models (agent-name screening), **Modal** (sandboxed repo execution).

---

## 3. OpenStocks — what they are and what will impress them

Sources: https://openstocks.com/manifesto, https://openstocks.com/, https://openstocks.com/prize-rules

### The product **[C]**
"OpenStocks is the platform where AI agents forecast companies' earnings." Launching **16 Aug 2026** — this hackathon *is* the launch event. Site currently is a pre-launch splash: manifesto, "Notify me at launch", "Apply to the hackathon". `/how-it-works` and `/leaderboard` exist as routes but currently render the splash — the app is behind sign-in and goes live tomorrow. **[C]**

### The four objectives (verbatim structure) **[C]**
1. **Host a financial model for every company** — live model for every listed company globally, forecasts continuously updated. "1 rule: no human analysts."
2. **Be the live benchmark for AI agents** — public benchmark for earnings prediction; agents submit, get scored vs actuals.
3. **Create the world's 1st "AI Consensus"** — aggregate agent forecasts into a consensus per company.
4. **Beat Wall Street** — "make AI Consensus canonical, not Wall Street's."

### Contribution tiers **[C]**
| Tier | Mechanism | Counts for rankings/prizes? |
|---|---|---|
| **Official** | Vetted entities, "mostly AI labs and companies working on AI agents". Forms the official AI Consensus. | Yes (and defines consensus) |
| **Community Verified** | **GitHub method — contributor gives access to the agent, OpenStocks runs it to produce the model.** Verifies the LLM + harness and "proves it wasn't human-generated." | Yes |
| **Community** | Excel `.xlsx` upload. No proof of AI authorship. | **No** — "won't count towards rankings, prizes, or any official stats" |

**→ We must target Community Verified (GitHub/runnable-repo).** An .xlsx-only submission is explicitly prize-ineligible on their platform. **[C]**

### Their four-part critique of Wall Street — the worldview to mirror **[C]**
1. **Bias / agency problem** — banks forecast companies that are also their clients. *AI: "no hidden agenda... the live benchmark encourages truth."*
2. **Coverage limitation** — big caps get more/better analysts. *AI: "equal compute goes into every covered company, whether it's a Magnificent 7 or a small cap."*
3. **Forecast staleness** — humans don't continuously update, are "reluctant to change their view." *AI: "'always-on' agents can continuously cover a company... without emotional attachment."*
4. **Forecast accuracy (?)** — "To be proved."

**This is the rubric behind the rubric.** An architecture that visibly embodies *independence, uniform compute, continuous re-forecasting, and auditability* will read as "on-thesis" to these judges. A one-shot prompt that emits two numbers will not.

### Prize Rules — the exact scoring formula they already use **[C]**
Source: https://openstocks.com/prize-rules (Version 2026-08-08-v5)

> "closeness is the **percentage distance between a forecast's value for the round's metric and the reported actual value**, compared against the **Wall Street consensus value OpenStocks records for the round**, and the miss OpenStocks computes this way is the score of record. A potential winner is selected **only from scored forecasts that are closer to the actual result than that Wall Street consensus value**. The **closest** eligible scored forecast is selected, with **earlier submission winning ties**."

Decoded:
- Metric: **absolute percentage error** vs the actual. `|forecast − actual| / |actual|`. **[I]** on exact denominator; "percentage distance" is not fully specified.
- **Hard gate: you must beat consensus APE, or you cannot win at all.** Not a relative-rank score — a threshold, then a min.
- **Winner-take-all per round.** No partial credit for second place.
- **Ties broken by earlier submission time.** Submit early once you're confident.
- Scoring uses **results as first reported**; later restatements don't change awards.
- Rounds can be **voided** (merger, delisting, cancelled/indefinitely delayed report, data failure) → no prize.
- One prize round = **one company, one fiscal period, one named metric**. Other metrics still get scored and published but don't enter the round.

Other Prize Rules facts: 18+, one account per person, LinkedIn identity must be connected **before the deadline**, must explicitly opt the forecast into the competition by accepting the rules before the same deadline ("submitting a forecast does not enter it automatically"). Platform prize is **$100 per Prize event, max 20 events, $2,000 total** — this is the *OpenStocks platform launch program*, **separate from and much smaller than** the $10k hackathon pot. Don't confuse them. **[C]**

### GitHub org **[C]**
`github.com/openstocks` exists (created 2023-01-07) but has **0 public repos, 0 followers**. No public SDK/docs to pre-read. Tooling will be handed out on the day.

### ⚠️ Disambiguation — three different "OpenStocks" **[C]**
1. **openstocks.com** — ours. Kernel AI Ltd / Primer. AI earnings consensus.
2. **openstocks.xyz** — unrelated DeFi platform on BNB Smart Chain, tokenized pre-IPO SPVs (SpaceX/OpenAI/Anthropic). **This one owns `linkedin.com/company/openstocks` and `x.com/@openstocks_hq`.** ~4 employees, India-based.
3. Various "finstocks/divistocks" noise.

**Do not cite or follow the .xyz entity's socials.** The real OpenStocks' launch posts (needed for the social prize) will come from Kernel AI/Primer/Seb Jory channels — confirm the correct handles at the event before posting. **[I]**

---

## 4. Primer — the judges' day job

Sources: https://primerapp.com/, /about/, /evals/, /product/, /blog/

### What it is **[C]**
"The AI analyst for equity investors." Browser-based, SOC 2, used by (per third-party coverage) Allianz GI, Jefferies, BlackRock, Fidelity, Panmure, Bridgepoint. Covers ~2,000 companies US/UK/EU. Founded 2023, London (St James / Westminster).

### Team **[C]**
- **Seb Jory** — Founder, Portfolio Manager. Ex-Tellworth (ran $1bn UK Select L/S), ex-Liberum/Panmure equity strategist & small-cap analyst, ex-RBS leveraged credit. Managing Partner, Lynott Partners. Sole director/PSC of Kernel AI Ltd.
- **Ruggero Gargiulo** — Co-founder, Head of Research. Ex-Tellworth investment analyst / quant.
- **Alistair Smallwood** — Head of Applied AI, former equity analyst.
- **Chris Mingard** — CTO, ML PhD Oxford.
- (Historic listings also name Jason Warren, co-founder/CTO — Maths & CS Oxford, ex-Morgan Stanley trading systems, ex-$2bn systematic macro fund; and Liam Rogan, Head of Growth.)

### Their public thesis — **"the harness beats the model"** **[C]**
This is the single loudest signal about what wins the architecture prize.

- BigFinanceBench (Rogo): **Primer 79.1%** vs best frontier model GPT-5.5 at 55.8%. Their words: *"Primer runs on GPT-5.5 — on its own it scores 44.3% on the leaderboard; inside Primer, 79.1%. **The gap is the harness**: what the model reads, which tools it can use, and what it has been taught about finance."*
- FinRetrieval (Daloopa): **500/500, 100%** retrieval accuracy vs ~90% frontier+MCP. Their explanation: *"Primer reads the **full filing, not isolated snippets**... Company, period, unit, and source context stay intact."*
- Financial modelling (Wall Street Prep): Primer 81% vs Claude-in-Excel 48%, ChatGPT 43%. Their explanation: *"Instead of forcing the agent to work **cell by cell in Excel**, Primer uses state of the art modelling infrastructure, then converts the finished model to Excel."*
- Underlying cash flow: 81.6%, judged *"on justification, not just numbers"* — *"Every adjustment needs evidence and a clean bridge... **Invented figures or unsupported one-offs fail outright**."*
- **Earnings previews backtest: +34% alpha vs SPX over 2,727 calls / 203 trading days, 53.6% hit rate, 1.42 Sharpe.**
- Blog posts are largely eval-methodology critiques: *"Finance AI benchmarks are misleading — I read all 220 questions in FrontierFinance. Nearly three quarters of the answer keys have errors."* They found errors in 12% of BigFinanceBench's public questions and published them.
- Seb Jory, LinkedIn, 29 Jul 2026: *"Next step is taking the Rogo benchmarks much further forward... (hint: not just build you a serviceable model, but **can it actually beat consensus**...)"* ← They are personally invested in exactly this question.

### What Primer's own UI looks like (aesthetics reference) **[C]**
Their product page mocks an **earnings preview card** with precisely our output shape:

```
Earnings preview — MSFT Q1 FY25
Metric        Est.    Cons.    Δ
Revenue      105.1    103.3   +1.7%
EPS           2.82     2.74   +2.9%
Op. margin    48.3     45.1   +120bp
```
Plus "Revenue trajectory" chart, "Beat / miss vs consensus", key themes, Q&A focus, call sentiment vs prior.

**→ If our architecture HTML renders an Est. / Cons. / Δ table in this idiom, it will look native to the judges.** Bonus: op. margin as a third row, and bp for margin deltas.

### Why they're sponsoring **[I]**
Recruiting + distribution for the OpenStocks launch + sourcing "Official tier" contributors. Note the job ads served on the hackathon portal itself: *"AI Engineer: Build Frontier Agents Reinventing Financial Modelling — Own the agent loop from eval to RL in London."* **[C]** A strong architecture story is also a job interview.

---

## 5. AI Tinkerers London — how these are actually run

Sources: https://london.aitinkerers.org/, /p/ultimate-agents-hackathon-10k-total-prizes, /hackathons/h__-9q8SnqEEg, aitinkerers.org/hackathons, organizer LinkedIn posts

### Chapter facts **[C]**
- Part of a 251-city / 122,000+ member network. London ran **18 events in the last 12 months**; "2025 = 10 hackathons hosted in London, NYC and [Paris]".
- Screened, demo-first, no-pitch. "Your projects make it past localhost."
- Organizer figure: **Louis Knight-Webb** (also founder/CEO of Vibe Kanban) has run/hosted London events and writes the recaps; also Shanice Walker on ops. **[C]** He posted "last night was my final time hosting" in Apr 2025 but was still writing recaps through Dec 2025 — current org lineup unclear. **[?]**

### Standard judging machinery (from the Dec 2025 portal) **[C]**
```
09:00  Team registration closes
17:55  Submit your project
18:00  Round 1 Judging — judges submit ratings
19:00  Final Judging completes
```
Two-round structure: **all teams rated in Round 1, subset presents in the final.** Our event mirrors this — 17:00 judging begins, 19:00 *finalists* present. **You are judged before you present.** The submitted artifact (architecture HTML + repo) has to stand alone without you in the room. This is the most commonly missed detail.

### Prior results & what wins **[C]**
- **Sept 2025 "Ultimate Agents" (£10k, Anthropic/ElevenLabs/Dedalus/Vibe Kanban, 120 builders, London AI Hub):** 🥇 Pixel Panel, 🥈 Match Me, 🥉 Laissez. Plus **partner prizes** ("Dedalus: Wali Labs, Synapsis, Weave, Games"; "ElevenLabs: Spam Fighter"; "Vibe Kanban: Teambolica, Weave"). **11 judges, 6 of them current/former YC founders.**
- **Dec 2025 "knowledge & retrieval" (partners incl. OpenAI, Redis, Prolific, EF, ElevenLabs, Vibe Kanban):** 🥇 AI copilot for gamers, 🥈 Recall — webpages → searchable knowledge graph (GitHub linked in submission), 🥉 visual search over London property listings.

Patterns worth acting on **[I]**:
- Winners are **crisp, demoable, single-sentence-describable** products, not sprawling platforms.
- **Partner prizes are awarded separately and generously** — multiple teams win them. The OpenAI credits are almost certainly this shape. Explicitly targeting the partner prize is cheap upside.
- Submissions that **link a GitHub repo** show up in the winner showcase. Repos matter.
- Showcase pages are public afterwards — good for the "declared" fields honesty.

---

## 6. Accuracy scoring — what we actually know

### Confirmed **[C]**
- Metrics: **revenue and EPS**.
- Comparison is to **both** actual results and Wall Street consensus.
- Scored **after** the event, "as companies report", announced "as the results come in".
- OpenStocks' documented house formula (§3): percentage distance from actual, gated on beating the recorded Wall Street consensus, closest wins, ties → earlier submission.
- 50/50 architecture/accuracy weighting. **[C-portal]**

### Open questions to resolve at kickoff **[?]**
1. **One company or several?** Event copy says "**your companies** report" (plural) and "a real company's earnings" (singular). Prize Rules define a round as one company + one period + one metric. Likely: a **fixed target list assigned on the day**, possibly with a choice. **Ask first thing.**
2. **Revenue and EPS both scored, or one named "prize metric"?** Their platform rules score every required metric but only one enters a prize round. The hackathon may differ.
3. **Whose consensus?** "the Wall Street consensus value **OpenStocks records for the round**" — snapshotted by them, at an unspecified time. If it's snapshotted on 16 Aug and actuals land in late Sept, consensus drift over 6 weeks is a real, exploitable factor. **Ask when the consensus snapshot is taken.**
4. **Denominator / scale.** Percentage error on EPS is brutal for low-EPS companies; a $0.02 miss on $0.30 EPS is 6.7%. Company choice may dominate skill.
5. **Aggregation across metrics/companies** — mean APE? Any weighting? Unknown.
6. **Submission lock time.** Prize Rules emphasise "before the applicable forecast window closes" and ties broken by earlier submission.

### Likely target universe **[I — flag as unconfirmed]**
"~6 weeks after 16 Aug" ≈ **late September 2026**. That points squarely at the **companies with fiscal quarters ending 31 Aug**, which report mid-to-late September — the classic "early reporters" cohort:

| Company | Fiscal period | Report date (2026) | Status |
|---|---|---|---|
| **Nike (NKE)** | Q1 FY27 | **24 Sep 2026, after close** | reported confirmed |
| **Costco (COST)** | Q4 FY26 | **24 Sep 2026, after market** | reported confirmed |
| **Micron (MU)** | Q4 FY26 | **23 Sep 2026** (one source says 29 Sep) | unconfirmed |
| **FedEx (FDX)** | Q1 FY27 | ~mid-late Sep | unconfirmed |
| **Accenture (ACN)** | Q4 FY26 | ~late Sep | unconfirmed |
| Also plausible | Carnival, Lennar, General Mills, Darden, CarMax, Paychex, Cintas, AutoZone, Jabil, Conagra | Sep | unconfirmed |

Sources: marketbeat/investing/tipranks/wallstreethorizon aggregators; none authoritative. **Confirm all dates on the day.** Note Micron's date is contested across sources, which matters because a delayed report = **voided round** under Prize Rules.

**Characteristics that should drive company choice if we get one** **[I]**:
- **High EPS magnitude** (Costco ~$5-6/qtr, Accenture ~$3/qtr) → percentage errors are forgiving. Avoid low-EPS names.
- **Predictable, disclosure-rich revenue** — Costco publishes **monthly sales**, which is close to a cheat code for revenue. Nike and FedEx have heavy segment/FX disclosure.
- **Avoid Micron** — memory pricing makes revenue/EPS wildly volatile and analyst dispersion enormous; high variance cuts both ways but consensus is also more likely to be badly wrong, so it's a lottery not a skill play. Also the least date-certain.
- **Consensus dispersion is the real edge:** beating consensus is a *threshold*, so pick a name where consensus is stale or where a public high-frequency dataset (monthly sales, FX, freight volumes, channel checks) is available and analysts update slowly. That's literally OpenStocks' "forecast staleness" thesis.

---

## 7. OpenAI credits ($8.5k, criteria TBA)

Nothing event-specific is public. **[C]** — portal Prizes section is empty. Pattern evidence:

- OpenAI was a partner at AI Tinkerers London Dec 2025. **[C]**
- OpenAI Build Week 2026 (July, $100k pool) judged on: *"technical implementation, design and user experience, potential impact, and the quality of the idea. Strong submissions demonstrate **thoughtful use of GPT-5.6 and Codex** while clearly communicating the problem, solution, and approach."* Prizes "may include cash awards, OpenAI credits, DevDay passes, spotlight opportunities." — https://openai.com/build-week/ **[C]**
- AI Tinkerers partner prizes are historically "best use of [technology]" and awarded to multiple teams. **[C]**
- **Primer itself runs on GPT-5.5/5.6** and Primer publicly blogged "How GPT-5.6 earned its place in Primer". OpenStocks uses OpenAI internally for workbook→consensus field matching. **[C]** The whole stack is OpenAI-native.

**Inference [I]:** the credits prize will be "best use of OpenAI" judged loosely on creative/thorough API use. Cheap ways to qualify: latest GPT-5.x as the reasoning core, **structured outputs / strict JSON schema** for the forecast object (also genuinely correct engineering here), **Agents SDK** for orchestration, parallel tool calls, and — a differentiator — using the **Evals API** to score our own agent's back-test on prior quarters. Given Primer's eval obsession, "we built an eval harness with OpenAI Evals and back-tested on the last 8 quarters" hits the architecture prize *and* the credits prize with one artifact.

---

## 8. Quick-reference contact/URL table

| Thing | URL |
|---|---|
| Event page | https://london.aitinkerers.org/p/agents-vs-wall-street-10k |
| Hackathon portal (schedule, criteria TBA) | https://london.aitinkerers.org/hackathons/h_6eHoon48MVI |
| OpenStocks manifesto | https://openstocks.com/manifesto |
| OpenStocks Prize Rules (scoring formula) | https://openstocks.com/prize-rules |
| OpenStocks Privacy (submission fields!) | https://openstocks.com/privacy |
| OpenStocks Terms | https://openstocks.com/terms |
| Primer evals (judge mindset) | https://primerapp.com/evals/ |
| Primer product (UI idiom) | https://primerapp.com/product/ |
| Primer team | https://www.primerapp.com/about/ |
| Kernel AI Ltd (Companies House) | https://find-and-update.company-information.service.gov.uk/company/15117085 |
| Prior AIT London hackathon showcase | https://london.aitinkerers.org/hackathons/h_c5jaaKp6A5U/showcase |
| Contact | hello@openstocks.com · prizes@openstocks.com |

---

## Implications for our build

### A. Treat the architecture HTML as a first-class deliverable, not documentation
The privacy policy names an **"uploaded architecture HTML file"** as a collected artifact used to "judge eligibility and the Architecture & Design Prize." Both on-the-day awards — architecture *and* aesthetics — most likely collapse onto this one file plus the demo. **Budget 90 minutes for it and assign an owner at 10:00, not 16:30.** It must be self-contained (single HTML, inline CSS/JS, no CDN), render the agent's DAG, and show a live forecast. Because Round 1 judging happens *before* finalists present, **it must be persuasive with nobody standing next to it.**

### B. Build the architecture story around OpenStocks' four grievances
Their manifesto is the rubric. Make each of the four visibly true of our agent, and say so in those words:
1. **Independence / no agenda** → deterministic, auditable pipeline; every number traces to a filing. Show the citation graph.
2. **Uniform compute across companies** → *don't* hand-special-case one ticker. Show the same agent running over N companies with identical compute. This is the single easiest way to look on-thesis while everyone else hardcodes one stock.
3. **No staleness** → make it re-runnable and show a **forecast-over-time chart** (re-run on data as of T-90/T-60/T-30 days and plot how the forecast moved). Cheap to build, extremely on-message, and nobody else will do it.
4. **Accuracy, proved** → back-test on the last 4–8 reported quarters and show APE vs the consensus APE for the same quarters. This is the killer slide for these specific judges.

### C. Mirror the "harness beats the model" thesis explicitly
Primer's whole public identity is that a 44%→79% jump came from the harness. Our pitch should be structurally identical: *"same model, naked vs in our harness, here's the delta."* Run one ablation on the day — bare model one-shot forecast vs full pipeline, on held-out prior quarters — and put both numbers on the architecture HTML. That single comparison speaks their language more fluently than any diagram.

Corollaries from their evals, worth copying:
- **Read full filings, not snippets** (their stated FinRetrieval edge). Chunked RAG over 10-Qs will read as naive to them.
- **Never invent a figure**; every adjustment carries evidence and a bridge ("invented figures or unsupported one-offs fail outright").
- **Don't drive Excel cell-by-cell**; model in code, export at the end if needed.

### D. Engineer for the Modal sandbox from the first commit
Community Verified tier — the only prize-eligible tier — means **OpenStocks fetches and runs our repo in an isolated Modal sandbox**. That imposes: pinned deps, one documented `final command`, no interactive auth, secrets via env vars only, no reliance on local files or warm caches, bounded runtime, graceful degradation if a data source is unreachable. Output a **strict JSON schema** forecast object (structured outputs) — that also serves the OpenAI credits angle. Decide the entrypoint at 10:00; retrofitting reproducibility at 16:30 is how teams lose this.

### E. Scoring-driven strategy: beating consensus is a *gate*, not a gradient
- You get **zero** unless your APE < consensus APE. Second-closest wins nothing. So **don't hug consensus** — a forecast that's deliberately near consensus mathematically cannot win. Take a defensible, evidenced deviation.
- But note the tension with the 50% architecture score, which is guaranteed and judged tomorrow. **The expected-value play is: maximise architecture (certain, in-room, 50%) and take one high-conviction, well-evidenced deviation on accuracy (lottery, 50%).**
- **Ties break on earlier submission** — submit as soon as we're confident, don't sit on it.
- **Prefer high-EPS, high-disclosure names** (Costco's monthly sales; Nike/FedEx segment + FX detail) over volatile low-EPS ones (Micron). Percentage error punishes small denominators.
- **Ask at kickoff:** how many companies, which metric is scored, and **when the consensus snapshot is taken** — a snapshot taken tomorrow with actuals in late September means 6 weeks of consensus drift we can reason about.
- Watch for **void risk**: a delayed or cancelled report kills the round. Prefer date-certain reporters.

### F. Free money, low effort
- **Two social prizes** for sharing both OpenStocks launch posts (X and/or LinkedIn) and submitting the links. No account needed. Assign to one person at 10:00 once the launch posts are live; verify the *correct* OpenStocks accounts first (see the .xyz disambiguation).
- **OpenAI credits partner prize** — historically awarded to several teams. Structured outputs + Agents SDK + an Evals-API back-test costs us little and is genuinely the right design.
- **Full team must be at the 09:30 kickoff to be prize-eligible.** Non-negotiable. Be there at 09:00.

### G. Practical time budget
Real build window is **10:00–17:00 (7h)**, with judging starting at 17:00 and finalists presenting at 19:00. Suggested split: data/tooling spike by 11:00 → working end-to-end forecast (any quality) by 13:00 → back-test + ablation by 15:30 → architecture HTML + submission record by 16:45 → submit early (tie-break). Capture the kickoff talk's judging criteria and company list verbatim at 09:30 and re-plan against it immediately — the portal's criteria section is empty tonight, so the kickoff is where the real rubric lands.
