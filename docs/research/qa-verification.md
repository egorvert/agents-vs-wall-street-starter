# QA / Verification Stage — Research

**Scope:** how to scrutinise and improve a quarterly revenue/EPS forecast *before* committing it, with no human in the loop.
**Date:** 15 Aug 2026. **Consumer:** `qa` stage of ingestion → research → prediction → **QA** → final number.

---

## 0. Seven findings that should drive the design

1. **Self-critique does essentially nothing for numbers.** Self-Refine's headline "+20% absolute" is carried entirely by open-ended tasks. On GSM8K math its own Table 1 reports **64.1 → 64.1 (0.0)**, **74.8 → 75.0 (+0.2)**, **92.9 → 93.1 (+0.2)** for GPT-3.5/ChatGPT/GPT-4, versus +21.6 to +49.2 on sentiment reversal and dialogue. The authors' diagnosis: *"ChatGPT feedback for 94% of instances is 'everything looks good'"*. With an **external oracle** signalling that the answer is wrong, gains jump to 5%+. ([NeurIPS 2023 PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/91edff07232fb1b55a505a9e9f6c0ff3-Paper-Conference.pdf), [arXiv HTML](https://arxiv.org/html/2303.17651v2))
   → **Never ship an LLM self-critique loop as the QA stage. The critic must be fed an external, deterministic error signal.**
2. **Intrinsic self-correction can make reasoning worse.** Huang et al., ICLR 2024: LLMs "struggle to self-correct without external feedback, and at times performance even degrades after self-correction." ([arXiv 2310.01798](https://arxiv.org/pdf/2310.01798), [OpenReview](https://openreview.net/pdf?id=IkmD3fKBPQ))
3. **Context separation is the single cheapest verification win.** Chain-of-Verification's whole point is that verification questions must be answered *in a fresh context that cannot see the draft*: "models that attend to existing hallucinations in the context from their own generations tend to repeat the hallucinations… the **factored** version answers verification questions such that they cannot condition on the original response, avoiding repetition and improving performance" — factored beats joint on all three tasks. ([arXiv 2309.11495](https://arxiv.org/abs/2309.11495), [ACL Findings 2024](https://aclanthology.org/2024.findings-acl.212/))
4. **A checklist-prompted LLM auditor will invent defects in clean data.** FinVerBench (SEC 10-K XBRL, 2026): under a guided-checklist prompt, **9 of 14 frontier LLM runs produced 95–100% false positives on *clean* financial statements**; only one run hit 0% observed FPR. Related: models "collapse from 95.6% accuracy on simple lookups to near 0% on multivariate calculations." ([arXiv 2605.29586](https://arxiv.org/pdf/2605.29586))
   → **Arithmetic adjudication belongs to code, not to the critic. The critic must be allowed — and rewarded — for saying "no material issue".**
5. **Arithmetic must be offloaded.** PAL (program-aided LM) hits **72.0%** on GSM8K vs CoT **65.6%**, +15 absolute over PaLM-540B CoT, purely by handing the calculation to a Python interpreter. ([PMLR 2023](https://proceedings.mlr.press/v202/gao23f.html), [arXiv 2211.10435](https://arxiv.org/pdf/2211.10435))
6. **Aggregation over diverse runs is the highest-return-per-line-of-code technique in this whole document.** Halawi et al.'s human-level forecasting system aggregates scratchpad forecasts with a **trimmed mean**; Schoenegger et al. (Science Advances) show a **median-aggregated 12-LLM crowd is statistically indistinguishable from 925 human tournament forecasters**. ([NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf), [Science Advances](https://www.science.org/doi/10.1126/sciadv.adp1528))
7. **Seeing the consensus helps accuracy *and* biases you. Both are true, so sequence matters.** Exposure to the median human forecast improved GPT-4/Claude 2 accuracy by **17–28%** — but a simple average of human and machine forecasts beat the "LLM told the median" condition ([Schoenegger et al.](https://arxiv.org/html/2402.19379v4)). Meanwhile LLMs anchor on numeric hints as reliably as humans do, and CoT / "ignore the anchor" / reflection **all fail to remove it** ([Lou & Sun, arXiv 2412.06593](https://arxiv.org/pdf/2412.06593); [O'Leary, IEEE Intelligent Systems 2025](https://ieeexplore.ieee.org/document/10962248/)).
   → **Blind estimate first, then reveal consensus, then reconcile as an explicit arithmetic step. Never let the anchor into the generation context.**

---

## 1. Superforecasting principles → executable QA operations

### 1.1 What the GJP actually measured

The CHAMPS KNOW debiasing module took **under one hour** and "consistently improved accuracy (Brier scores) by **6 to 11%** over the control condition", with effects persisting a year. ([Chang, Chen, Mellers & Tetlock, *Judgment and Decision Making* 2016](https://goodjudgment.com/wp-content/uploads/2018/12/jdm16511.pdf))

The full decomposition (Table 3 of that paper):

| | Probabilistic reasoning principle |
|---|---|
| **C** | Comparison classes |
| **H** | Hunt for the right information |
| **A** | Adjust and update forecasts when appropriate |
| **M** | Mathematical and statistical models |
| **P** | Post-mortem analysis |
| **S** | Select the right level of effort to devote to each question |
| | *Political reasoning principle* |
| **K** | Know the power players and their preferences |
| **N** | Norms and protocols of institutions |
| **O** | Other perspectives should inform forecasts |
| **W** | Wildcards, accidents, and black swans |

**Which principles actually correlated with accuracy** (Year-4 self-tagged explanations, n≈6,700):
- **C (comparison classes) was the strongest positive**: mean standardised Brier **0.17** vs the next-best tag at **0.26**; C, M and S all beat untagged explanations.
- **P (post-mortem) and O (other perspectives) correlated with *worse* Brier scores.** The authors' own explanation for P: "post-mortems are normally conducted after inaccurate forecasts" — i.e. a selection confound, not evidence that pre-mortems hurt. Still, treat "add a pre-mortem" as *unproven* rather than *measured*.
- Probabilistic principles (CHAMS) improved accuracy; political principles (KNW) did not. ([J&DM 2016](https://dlab.sauder.ubc.ca/sjdm/journal/16/16511/jdm16511.html), [AI Impacts summary](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/))

**Design consequence:** weight the QA agent's effort towards base rates and statistical models, not towards vibes-based devil's advocacy.

### 1.2 Mapping to LLM-executable QA operations

| Superforecasting principle | Source | Concrete QA-agent operation (ours) |
|---|---|---|
| **Outside view first, inside view second** — "first anchor with the outside view and then adjust using the inside view"; "How often do things of this sort happen in situations of this sort?" ([Ten Commandments #3](https://goodjudgment.com/philip-tetlocks-10-commandments-of-superforecasting/)) | C, strongest measured effect | **Deterministic** `baseRateProfile(ticker)`: firm's trailing 8–12Q distribution of (a) YoY revenue growth, (b) QoQ growth, (c) gross/op margin, (d) surprise vs consensus. QA rejects any forecast whose implied values fall outside the historical IQR without a named, sourced driver. |
| **Fermi-ise: break into knowable/unknowable parts; "flush ignorance into the open"** ([#2](https://fs.blog/ten-commandments-for-superforecasters/)) | GJP | **Structural requirement, not a prompt.** Prediction stage must emit a typed decomposition (segments × price/volume × FX × one-offs) that sums to the total. QA validates the identity in code. LLMs *can* decompose Fermi problems but decomposition depth doesn't correlate with accuracy — the value is in making assumptions auditable, not in more layers ([FermiEval, arXiv 2510.26995](https://arxiv.org/html/2510.26995)). |
| **Mathematical/statistical models (M)** | GJP, positive | **Deterministic** naive benchmarks the forecast must be scored against: seasonal random walk with drift, and the Foster model (autocorrelations in seasonally-differenced quarterly earnings are positive and declining at lags 1–3 and strongly negative at lag 4) ([Foster 1977; Foster, Olsen & Shevlin 1984](https://www.sciencedirect.com/science/article/pii/S2214635020303750)). If the LLM forecast is far from *both* the naive model and consensus, that is a red flag, not an edge. |
| **Actively seek disconfirming evidence / "consider the opposite"** | Mussweiler, Strack & Pfeiffer 2000: consider-the-opposite instructions significantly attenuate anchoring by activating knowledge inconsistent with the anchor ([PSPB](https://journals.sagepub.com/doi/10.1177/01461672002611010)) | **LLM, fresh context.** A "bear/bull" pass that must produce a *number*, not prose: "state the revenue/EPS you would forecast if the strongest disconfirming reading of the dossier were correct." Feed that number into aggregation (see §6.1 on dialectical bootstrapping — this is the single best-evidenced use of a second opinion from the same model). |
| **Pre-mortem / prospective hindsight** | Mitchell, Russo & Pennington 1989: imagining an event has *already* happened raises correct identification of reasons by **~30%**; operationalised by Klein, HBR 2007 ([HBR PDF](https://lmscontent.embanet.com/USC/PPD554/Week10/PPD554_W10_HBR_Klein_Performaing_a_Project_Premortem.pdf)) | **LLM, fresh context, structured output.** "It is now [report date]. Our forecast missed by >5%. Write the three most likely causes." Each cause must be typed (`data_error` / `period_mismatch` / `driver_missed` / `one_off` / `guidance_ignored`) and map to a re-runnable check. Note the GJP caveat above: pre-mortems are *not* measured to improve Brier; justify this stage by defect *discovery*, and gate it so it can only trigger a re-check, never directly move the number. |
| **Granular updating; distinguish as many degrees of doubt as the problem permits** ([#4, #6](https://www.lesswrong.com/posts/dvYeSKDRd68GcrWoe/ten-commandments-for-aspiring-superforecasters)) | Mellers: superforecasters lose accuracy from rounding to the nearest **0.05**; ordinary forecasters barely lose from rounding to 0.20 ([Superforecasting; summary](https://commoncog.com/how-the-superforecasters-do-it/)) | **Don't round.** Emit revenue to the nearest $1M and EPS to 3dp internally; round only for display. Emit an explicit probability the actual beats consensus, and require QA-stage updates to be **small and reason-attributed** — every delta ≥ 0.5% must carry a one-line cause. Forbid "confidence: high/medium/low"; require a numeric interval. |
| **Triage / select the right level of effort (S)** | GJP, positive | Route by difficulty: dispersion of consensus estimates, number of covering analysts, presence of company guidance. High-dispersion / low-coverage names get more reruns and a wider band. |
| **Keep score** | #10 | Every QA check writes a row into SQLite with `check_id`, `severity`, `fired`, `pre_value`, `post_value`. Post-mortem the eval harness on which checks actually moved the number toward truth. |

---

## 2. LLM verification patterns — what measurably helps, and what only helps prose

### 2.1 Measured results table

| Pattern | Measured result | Helps **numbers**? |
|---|---|---|
| **Self-critique / Self-Refine** (same model, same context) | +21.6 to +49.2 on sentiment reversal/dialogue; **0.0 / +0.2 / +0.2 on GSM8K**. Feedback = "everything looks good" 94% of the time. With an external correctness oracle, +5%. ([NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/file/91edff07232fb1b55a505a9e9f6c0ff3-Paper-Conference.pdf)) | **No** (without an oracle) |
| **Intrinsic self-correction** | Performance sometimes *degrades*. ([Huang et al., ICLR 2024](https://arxiv.org/pdf/2310.01798)) | **No** |
| **Self-bias amplification** | Across GPT-4, GPT-3.5, Gemini, LLaMA2, Mixtral, DeepSeek: self-refine improves fluency but **amplifies self-bias**; external feedback with accurate assessment significantly reduces it. ([Xu et al., ACL 2024](https://aclanthology.org/2024.acl-long.826.pdf)) | **No** |
| **Chain-of-Verification (CoVe), factored** | Reduces hallucination across Wikidata list QA, closed-book MultiSpanQA, longform. **Factored** (verification answered without seeing the draft) > joint on all tasks. | **Partially** — the mechanism (independent re-derivation) is exactly what we want for dossier facts |
| **Fresh-context cross-examination (LM vs LM)** | On PopQA with ChatGPT: **F1 85.4 vs 65.2** for the best baseline; 78–80% F1 across three examiner/examinee pairings, ~17–20% better than the next-best fact-checking baseline. ([Cohen et al., EMNLP 2023](https://aclanthology.org/2023.emnlp-main.778/)) | **Yes for factual claims** |
| **Trained verifier / reranker** | Cobbe et al.: sampling many solutions and reranking with a verifier gives a boost "approximately equivalent to a **30× model size increase**" on GSM8K. ([arXiv 2110.14168](https://arxiv.org/abs/2110.14168)) | **Yes** — but needs training data we don't have in one day |
| **Process reward model (step-level)** | Process supervision solves **78.2%** of a MATH subset vs outcome supervision. ([Lightman et al., ICLR 2024](https://arxiv.org/abs/2305.20050)) | **Yes**, same caveat |
| **Critic model (CriticGPT)** | Critiques preferred over ChatGPT's in **63%** of naturally-occurring bugs; human+critic teams beat unaided humans **>60%** of the time; LLM critics catch more inserted bugs than paid human reviewers, preferred >80%. ([OpenAI](https://openai.com/index/finding-gpt4s-mistakes-with-gpt-4/), [paper PDF](https://cdn.openai.com/llm-critics-help-catch-llm-bugs-paper.pdf)) | **Yes** — critic *finds defects*; it does not set the number |
| **Multi-agent debate** | Du et al. (ICML 2024): improves factuality and math over single-agent; cases where all agents start wrong and converge right; gains plateau with agent count. ([OpenReview](https://openreview.net/pdf?id=zj7YuTE4t8)) | **Yes but expensive**; cost scales with rounds × agents |
| **Self-consistency / sampling + vote** | Significant arithmetic gains over CoT across four LMs; **but** 2025–26 work reports diminishing returns and rising cost in modern models ([arXiv 2511.00751](https://arxiv.org/pdf/2511.00751)) | **Yes** — and it generalises to continuous outputs via trimmed mean (§6) |
| **Program-aided reasoning (PAL)** | GSM8K **72.0% vs 65.6%** CoT; +15 abs over PaLM-540B CoT. | **Yes — biggest single numeric win** |
| **LLM-as-judge** | GPT-4 judges reach **>80% agreement** with human experts, "the same level of agreement between humans"; up to 85% without ties. Known biases: **position**, **verbosity** (judge scores track raw length at r≈.87 vs .44 for humans), **self-enhancement**. ([Zheng et al., NeurIPS 2023](https://arxiv.org/pdf/2306.05685), [bias survey](https://llm-judge-bias.github.io/)) | **For scoring rationale quality, yes; for setting a number, no** |
| **Rubric vs free-form critique** | Structured rubrics beat holistic scoring; recursive rubric decomposition improves agreement over base judges across GPT-4o and Llama3.1-405B ([arXiv 2602.05125](https://arxiv.org/html/2602.05125v1)). **Binary** criteria give 0.72–0.76 macro-F1 agreement and moving ternary→binary adds **~20pp** agreement — partial credit adds ambiguity without discrimination ([arXiv 2606.08625](https://arxiv.org/html/2606.08625v2)) | **Yes — use binary pass/fail rubric items, never 1–5 scales** |
| **Sampling-based hallucination detection (SelfCheckGPT)** | AUC-PR **93.42** (non-factual sentence detection), beating token-probability baselines; works black-box. ([EMNLP 2023](https://aclanthology.org/2023.emnlp-main.557.pdf)) | **Yes for claim-level flags** |
| **Deciding *when* to refine (ART)** | +5 points over self-refinement baselines by asking whether refinement is warranted and ranking refined vs initial, using a smaller decider model. ([NAACL 2024](https://aclanthology.org/2024.naacl-long.327/)) | **Yes** — refine selectively, and keep the original as a candidate |

### 2.2 The synthesis

The techniques that move **numeric** estimates share one property: **an information source outside the author's own reasoning trace**. Ranked by effect-per-hour-of-build for tomorrow:

1. Deterministic recomputation in code (PAL logic, taken to its limit).
2. Aggregation across diverse independent runs (§6).
3. Fresh-context critic that never sees the author's chain of thought (CoVe-factored / LM-vs-LM).
4. Binary rubric scoring rather than free-form critique.
5. Debate — only if time remains; it is the most expensive per unit of gain.

And the technique to actively **avoid**: a same-context self-refine loop, which on numbers buys ~0.2pp and costs a round trip, while amplifying self-bias and sycophancy (**58.19%** sycophantic responses under rebuttal, of which **14.66%** flip a correct answer to incorrect — [SycEval, arXiv 2502.08177](https://arxiv.org/html/2502.08177v4)).

**Critic hygiene rules that follow from the bias literature:**
- Critic must not see the author's reasoning, only the *dossier + the numeric output + the deterministic check results*. (CoVe factored; Delphi: including experts' own initial ratings in the feedback makes them change their opinion *less* — [Meijering & Tobi, IJF 2018](https://ideas.repec.org/a/eee/intfor/v34y2018i2p216-224.html).)
- Critic must not know which model authored the forecast (self-enhancement bias).
- Randomise the order of candidate forecasts when comparing (position bias).
- Cap critique length / score against a rubric, because judges reward verbosity at r≈.87.
- Critic must have a legitimate "no material issue" output and be evaluated on false-positive rate on known-good fixtures — otherwise you get the FinVerBench failure mode (95–100% FP on clean statements).

---

## 3. Deterministic sanity checks — the definitive earnings-forecast checklist

Everything in this section is **pure TypeScript, zero LLM calls, deterministic, and unit-testable**. Severity: `BLOCK` (cannot emit), `ESCALATE` (must be justified by the critic with a cited reason, else revert to fallback), `WARN` (logged, widens the interval).

### 3.1 Internal-consistency identities (`BLOCK` — these are arithmetic, not judgement)

| # | Check | Rule |
|---|---|---|
| D1 | **Segment sum** | `Σ segmentRevenue + other/eliminations == totalRevenue` within 0.1%. If the company reports segments, the forecast must forecast segments. |
| D2 | **Geographic sum** | Same, for geographic split if the dossier uses one. Both splits must reconcile to the same total. |
| D3 | **Income-statement chain** | `revenue − COGS = grossProfit`; `grossProfit − opex = operatingIncome`; `operatingIncome + otherIncome − interest = pretax`; `pretax × (1 − taxRate) = netIncome`. Each link checked to 0.1%. |
| D4 | **EPS identity** | `EPS = (netIncome − preferredDividends) / dilutedShares`, tolerance 0.5 cents or 0.5%, whichever is larger. Recompute EPS from the forecast's own components — **never trust an LLM-emitted EPS**. |
| D5 | **Non-GAAP bridge** | If the consensus is a non-GAAP/"street" EPS (it usually is), the forecast must state GAAP→non-GAAP adjustments (SBC, amortisation of intangibles, restructuring) and they must reconcile. Mixing GAAP forecast against non-GAAP consensus is the most common silent killer. |
| D6 | **Sign and domain sanity** | Revenue > 0; 0 ≤ grossMargin ≤ 1; tax rate ∈ [−0.5, 0.6]; share count > 0; no NaN/Infinity; units consistent (all $M or all $K — check magnitude vs last reported to catch 1000× errors). |
| D7 | **Currency consistency** | Reporting currency of forecast == reporting currency of consensus == reporting currency of last 10-Q. Flag any dossier figure quoted in a different currency without an FX rate and rate date. |

### 3.2 Outside-view / base-rate plausibility (`ESCALATE`)

| # | Check | Rule |
|---|---|---|
| D8 | **Implied YoY growth percentile** | Compute implied YoY revenue growth; locate it in the firm's trailing 12-quarter distribution. Outside [P10, P90] → ESCALATE; outside [P2, P98] → BLOCK unless a named structural driver (acquisition closed, 53rd week, divestiture, product launch date) is cited with a source. |
| D9 | **Implied QoQ vs seasonality** | Compare implied QoQ growth against the same fiscal quarter's QoQ in each of the last 3–5 years. If the forecast implies a QoQ of the opposite sign to the seasonal norm in ≥4 of the last 5 years → ESCALATE. (Foster's autocorrelation structure — positive lags 1–3, strongly negative lag 4 — is the formal version of "Q4 is always the big one".) |
| D10 | **Margin band** | Implied gross margin, operating margin and net margin each compared against the **trailing-8-quarter min/max**. Outside the range → ESCALATE; more than 150bps outside → BLOCK without a cited driver. Margins are far more mean-reverting quarter to quarter than revenue; a forecast that quietly expands op margin 300bps is usually an arithmetic slip. |
| D11 | **Naive-model distance** | Compute seasonal-random-walk-with-drift and Foster-model forecasts. If our forecast is far from *both* the naive models **and** consensus (i.e. we are the outlier in both directions), ESCALATE — the a priori odds are that we made a mistake, not that we found alpha. |
| D12 | **Surprise-vs-own-history** | Compute implied surprise = (ours − consensus)/|consensus|. Compare to the firm's own trailing-8Q surprise distribution. **Key asymmetry: forecasting exactly consensus is itself a biased forecast.** FactSet: the 5-yr average is **78%** of S&P 500 companies beating EPS estimates (10-yr **76%**), **70%/68%** for revenue, with a 5-yr average earnings surprise of **+7.0%** (10-yr **+7.4%**) ([FactSet Earnings Insight](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_112125.pdf), [insight.factset.com](https://insight.factset.com/sp-500-earnings-season-update-july-24-2026)). So the *outside view prior* is `consensus × (1 + firm's own median trailing surprise)`, not `consensus`. Measure our deviation against **that**, not raw consensus. (Index-level average surprise is skewed by mega-cap beats — always compute the firm-level median from our own SQLite history rather than using 7% as a constant.) |

### 3.3 Share count, buybacks and the EPS denominator (`ESCALATE`)

| # | Check | Rule |
|---|---|---|
| D13 | **Share-count continuity** | Forecast diluted share count vs last reported diluted weighted-average. Δ outside [−4%, +2%] per quarter → ESCALATE. |
| D14 | **Buyback run-rate consistency** | If the dossier cites buyback $ authorised/executed, implied share reduction ≈ `buyback$ / avgPrice`. Forecast reduction inconsistent with run-rate by >50% → WARN. Remember weighted-average timing: a buyback completed mid-quarter reduces the weighted-average by roughly half its full effect. |
| D15 | **Dilution floor** | SBC-heavy names have gross issuance offsetting buybacks. If the last 4 quarters all show share count *rising* and the forecast shows it falling, ESCALATE. |
| D16 | **EPS-revenue coherence** | Independently recompute `EPS_implied = revenue × netMargin / shares` and compare to the emitted EPS. Divergence >1% → BLOCK. This catches the case where the model updates revenue in the reconciliation step and forgets to reflow EPS. |

### 3.4 Guidance handling (`ESCALATE`, with a caveat most people get wrong)

| # | Check | Rule |
|---|---|---|
| D17 | **Guidance containment** | If the company guided *for this specific quarter*, a forecast outside the guided range must be justified. **But do not make this a BLOCK.** Survey evidence (357 CFOs/IR professionals): reported earnings fall within the **initial** guidance range only about **31%** of the time, while ~90% of managers were ≥70% confident they would land inside it ([Call, Hribar, Skinner & Volant, JAE 2024 — MIT Sloan PDF](https://mitsloan.mit.edu/sites/default/files/inline-files/Call_Hribar_Skinner_Volant.pdf); [coverage](https://www.ttnews.com/articles/earnings-guidance-inaccuracy)). Guidance ranges are systematically over-confident. |
| D18 | **Guidance recency & scope** | Assert the guidance being used was issued for **this** fiscal quarter and has not been superseded (pre-announcement, 8-K, conference remarks). Using last year's guidance, or FY guidance as if it were quarterly, is a classic silent failure. Store `guidance_issue_date`, `guidance_period_start`, `guidance_period_end` and check containment programmatically. |
| D19 | **Guidance skew prior** | Management guidance is generally more accurate than consensus at the firm-specific level, and less accurate for small-bad-news guidance; analysts hold the edge on macro-driven names ([Hutton, Lee & Shu, HBS](https://www.hbs.edu/faculty/Shared%20Documents/events/18/HuttonLeeShu2012.pdf); [Do Managers Always Know Better?](https://www.researchgate.net/publication/255483927_Do_Managers_Always_Know_Better_The_Relative_Accuracy_of_Management_and_Analyst_Forecasts)). Practical rule: default to the **upper half** of the guided range for revenue/EPS, because expectation management makes guidance beatable; treat guidance below consensus as a stronger signal than guidance above. |

### 3.5 FX and non-operating (`WARN`/`ESCALATE`)

| # | Check | Rule |
|---|---|---|
| D20 | **FX rate freshness** | Any FX rate used must have a quote date inside the forecast quarter. Rates older than the quarter start → ESCALATE. |
| D21 | **FX magnitude sanity** | Implied FX impact on revenue vs (international revenue % × trade-weighted currency move over the quarter). If the forecast claims an FX tailwind while the relevant currency pair moved against the company, BLOCK. |
| D22 | **Constant-currency consistency** | If the dossier quotes cc growth, check `reported growth ≈ cc growth + FX impact` to within 50bps. |
| D23 | **Tax rate** | Effective tax rate outside the trailing-8Q range by >500bps → ESCALATE. Tax is where EPS forecasts quietly break. |
| D24 | **Below-the-line** | Interest expense/income should track the debt/cash balance and rate environment; other income should not be a plug. If `otherIncome` is doing >10% of the work in getting to EPS, ESCALATE. |

### 3.6 Consensus-distance alarm (`ESCALATE` / `BLOCK`)

Calibrate thresholds against the actual difficulty of the task rather than round numbers:

- Analyst median absolute EPS forecast error is **~1.9% of stock price**; a commercial LLM's is **~2.3%** (121,369 forecasts, 607 firms, 2018–2025) — i.e. the LLM underperforms analysts by ~20% ([KDI School WP 26-14](https://archives.kdischool.ac.kr/handle/11125/69515)).
- GPT-4 one-year-ahead EPS forecast errors are **larger than analysts' on average**, but GPT beats analysts in **>25% of firm-quarters**, and accuracy degrades past the knowledge cutoff ([Li, Shen, Tu & Zhou, arXiv 2412.01069](https://arxiv.org/pdf/2412.01069)).
- The counterweight: with a chain-of-thought prompt over anonymised statements, GPT-4 hit **60.35% accuracy / 60.90% F1** on the *direction* of next-year earnings vs analysts' **52.71%** (1-month), **55.95%** (3-month), **56.58%** (6-month) — and beat even top-quintile analysts at 56.75% ([Kim, Muhn & Nikolaev, arXiv 2407.17866](https://www.arxiv.org/pdf/2407.17866v2)).

**Read:** we can plausibly beat consensus on *direction*; we should be humble about beating it on *magnitude*. So:

| Metric | Deviation from base-rate-adjusted consensus | Action |
|---|---|---|
| Revenue | > 1.5% | Require ≥1 documented, sourced driver |
| Revenue | > 4% | ESCALATE: two independent drivers + rerun |
| Revenue | > 8% | BLOCK unless a discrete corporate event (M&A, divestiture, 53rd week) is cited |
| EPS | > 5% | Require documented driver |
| EPS | > 12% | ESCALATE + rerun |
| EPS | > 25% | BLOCK unless revenue deviation or a named one-off explains it arithmetically |

A "documented reason" is a structured object, not a sentence: `{claim, sourceUrl, sourceDate, fiscalPeriod, quantifiedImpact$}` — and `quantifiedImpact` across all cited drivers must explain ≥70% of the deviation, checked in code.

### 3.7 Dispersion-aware widening

Analyst forecast **dispersion** is the standard proxy for the uncertainty component of the forecasting problem ([Xiao, UCLA](https://www.anderson.ucla.edu/documents/areas/fac/accounting/working-papers/Xiao_JMP.pdf)). Scale all of the above thresholds by the consensus dispersion: for a name where the analyst standard deviation is 4% of the mean, a 4% deviation is unremarkable; for a name where it is 0.5%, it is extraordinary. Concretely: express deviation in **units of consensus SD**, and set alarms at 1.5σ / 3σ / 5σ in addition to the absolute percentages above.

---

## 4. Evidence auditing and hallucinated-number detection

### 4.1 Why this stage is not optional

- **FinanceBench:** GPT-4-Turbo with a retrieval system incorrectly answered or refused **81%** of open-book financial questions; with long context the failure rate is still 21% (Claude 2: 24%) ([Patronus AI](https://www.patronus.ai/announcements/patronus-ai-launches-financebench-the-industrys-first-benchmark-for-llm-performance-on-financial-questions), [GitHub](https://github.com/patronus-ai/financebench)).
- **FermiEval:** models make arithmetic errors in **38%** of solutions and factual errors in **36%**; nominal 99% intervals cover the truth only **65%** of the time ([arXiv 2510.26995](https://arxiv.org/html/2510.26995)).
- **FAITH / PHANTOM** show intrinsic tabular hallucination in financial filings is a distinct, measurable failure mode requiring source-faithfulness evaluation, not just answer accuracy ([FAITH, arXiv 2508.05201](https://arxiv.org/abs/2508.05201); [PHANTOM, NeurIPS 2025](https://openreview.net/pdf?id=5YQAo0S3Hm)).

So: assume roughly a third of the dossier's derived numbers are wrong until proven otherwise.

### 4.2 The audit contract

Force the research stage to emit **atomic, typed claims** rather than prose. A material claim is any claim that feeds a forecast driver:

```ts
type Claim = {
  id: string;
  text: string;                 // "Q2 FY26 Data Center revenue was $26.3B"
  value?: number; unit?: string;// 26_300_000_000, "USD"
  fiscalPeriod: FiscalPeriod;   // {fy: 2026, q: 2, periodEnd: "2026-06-28"}
  asOf: string;                 // date the fact was true / stated
  sourceUrl: string;            // must resolve
  sourceType: "10-Q"|"10-K"|"8-K"|"PR"|"transcript"|"consensus"|"news"|"derived";
  quoteSpan?: string;           // verbatim substring from the source
  derivedFrom?: string[];       // claim ids, for computed values
};
```

### 4.3 Deterministic audits (code)

| # | Check | Rule |
|---|---|---|
| E1 | **No orphan numbers** | Every number that appears in the forecast rationale must map to a `Claim.id` or a `derived` claim whose inputs are claim ids. Regex-extract numerals from the rationale and require coverage. Uncovered numeral → BLOCK. |
| E2 | **Quote-span verification** | For every non-derived claim, assert `quoteSpan` is a literal substring of the fetched source text, and that `value` appears in the span (allowing formatting variants: `26,300`, `26.3 billion`, `$26.3B`). Fails → claim marked unverified, and any driver depending on it is dropped. This is the cheapest, highest-yield hallucination catch available. |
| E3 | **Fiscal-period alignment** | Assert `Claim.fiscalPeriod` is the intended period. Company fiscal calendars ≠ calendar quarters (NVDA, AAPL, ORCL…). Maintain a fiscal-calendar table and reject any claim whose `periodEnd` doesn't match a known period end for that issuer. |
| E4 | **Staleness / mixed-period detector** | For each claim: `asOf` must be ≤ the forecast cut-off and ≥ the earliest period that could still be relevant. Specifically flag: guidance whose `periodEnd` < the quarter being forecast (last year's guidance), consensus snapshots older than 14 days, "latest quarter" claims referring to two quarters back. |
| E5 | **Recency ordering** | If two claims assert different values for the same `(metric, fiscalPeriod)`, keep the one with the authoritative `sourceType` (10-Q > 8-K/PR > transcript > news) and the later `asOf`; raise a `CONFLICT` for the critic. Never silently average them. |
| E6 | **Unit and scale audit** | Compare each claim's magnitude to the same metric one year earlier; a >20× jump is a units error (thousands vs millions), not growth. |
| E7 | **Source resolvability** | Every `sourceUrl` must have been actually fetched in this run (check the ingestion cache), not merely asserted. LLMs fabricate plausible SEC URLs. |
| E8 | **Duplicate-driver detection** | Two drivers describing the same effect (e.g. "AI demand" and "Data Center strength") both adding to revenue = double counting. Cluster drivers by the segment they touch; if the sum of driver impacts within one segment exceeds that segment's total forecast delta, ESCALATE. |

### 4.4 LLM audits (fresh context, factored)

Run **CoVe-factored** over the claim list:

1. From the dossier, generate one verification question per material claim ("What was Segment X revenue in FY26 Q2?").
2. Answer each question **in a separate context containing only the retrieved source text** — never the dossier or the draft forecast. This is precisely the factored variant that outperformed joint CoVe.
3. Compare answers to `Claim.value`; mismatch → claim invalidated.

Add **SelfCheckGPT-style sampling** for claims with no clean source: sample the claim's value N=5 times at temperature > 0 from source text; high variance ⇒ likely hallucinated (AUC-PR 93.42 for non-factual detection).

Add **LM-vs-LM cross-examination** for the 3–5 claims with the largest forecast leverage: a separate examiner model interrogates the researcher's claim for internal inconsistency (F1 85.4 vs 65.2 baseline on PopQA).

---

## 5. Anchoring management: with or without the consensus?

### 5.1 What the evidence says

**Anchoring is real in LLMs and hard to prompt away.**
- Each of three LLMs anchored on numeric hints when asked for numerical estimates about text ([O'Leary, IEEE Intelligent Systems 2025](https://dl.acm.org/doi/abs/10.1109/MIS.2025.3544939); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5315021)).
- Statistically robust shifts between high- and low-anchor conditions across GPT-4o/GPT-4/GPT-3.5-Turbo, mirroring human behaviour, with **stronger models more consistently biased by numeric hints** ([arXiv 2511.05766](https://arxiv.org/pdf/2511.05766)).
- Mitigations that **do not work**: Chain-of-Thought, "Thoughts of Principles", explicitly instructing the model to ignore the anchor, and Reflection. What did help: collecting hints from **comprehensive/multiple angles** so no single number dominates ([Lou & Sun, arXiv 2412.06593](https://arxiv.org/pdf/2412.06593)).

**But the consensus is genuine information, and hiding it forever costs accuracy.**
- GPT-4 and Claude 2 forecasting accuracy improved **17–28%** from exposure to the median human forecast. Critically, **simply averaging human and machine forecasts beat feeding the human median into the LLM** ([Schoenegger et al.](https://arxiv.org/html/2402.19379v4)) — mechanical combination > in-context assimilation.
- Humans systematically under-weight advice (advice discounting; weight-on-advice well below the optimal 0.5 for equally-informed judges — [Yaniv](https://en.wikipedia.org/wiki/Judge%E2%80%93advisor_system), [Soll & Larrick / HBS](https://www.hbs.edu/ris/Publication%20Files/06-019.pdf)). LLMs, being sycophantic, are likely to err in the **opposite** direction and over-weight it.
- Delphi evidence: **anonymous, controlled, statistical feedback made group estimates more accurate more often than not, whereas face-to-face discussion made them worse** ([RAND RM-5888](https://www.rand.org/pubs/research_memoranda/RM5888.html); [ERIC summary](https://files.eric.ed.gov/fulltext/ED064302.pdf)). Also: feeding an expert their *own* initial rating alongside the group's makes them revise **less** ([Meijering & Tobi, IJF 2018](https://ideas.repec.org/a/eee/intfor/v34y2018i2p216-224.html)) — an argument for withholding the author's own draft from the reconciler.

### 5.2 Recommended protocol: **blind → reveal → reconcile as arithmetic**

```
Stage A  BLIND ESTIMATE (consensus redacted from every context)
         N independent runs over the dossier.
         Consensus, analyst ranges, and any price target are stripped by a
         redaction filter, not merely "not mentioned".
         Output: blind_point, blind_low, blind_high, drivers[]
              ↓
Stage B  DETERMINISTIC CHECKS (§3) + EVIDENCE AUDIT (§4)
         Still blind. Fixes here are corrections, not adjustments.
              ↓
Stage C  REVEAL  →  gap = blind_point − consensus_adjusted
         where consensus_adjusted = consensus × (1 + firm median trailing surprise)
              ↓
Stage D  RECONCILE — a *structured decomposition of the gap*, not a re-forecast.
         The reconciler must allocate 100% of the gap to labelled buckets:
           - information consensus lacks (must cite a post-consensus-date source)
           - different assumption on a specific driver (must name driver + delta)
           - unexplained residual
         Rule: unexplained residual is shrunk toward zero.
         Final = consensus_adjusted + Σ(explained deltas) + λ·residual, λ ≈ 0.3–0.5
              ↓
Stage E  AGGREGATE (§6) and emit with interval
```

**Why this shape:**
- It gets the accuracy benefit of the consensus (Schoenegger: +17–28%) via **mechanical combination**, which their own data shows beats in-context assimilation.
- It gets the anti-anchoring benefit of blind generation, without relying on prompt-level "ignore the anchor" instructions that the literature shows don't work.
- The shrinkage factor λ on the unexplained residual is the formal statement of "if you can't say *why* you disagree with the market, you mostly don't."
- Stage D is deliberately arithmetic and auditable, which is where LLMs are weakest and where our code can check the allocation sums to the gap.

**A/B this if there is any eval time at all.** Run the harness both ways (blind-then-reconcile vs consensus-visible-throughout) on 20–30 historical quarters. It is the highest-signal experiment available and it directly answers a judge's most likely question.

**Also run "consider the opposite" at Stage A**, since it is the one anchoring mitigation with a positive replication record (Mussweiler et al. 2000) and it doubles as a dialectical estimate for §6.

---

## 6. Aggregation as QA

### 6.1 Why aggregation is the best-evidenced part of the whole pipeline

- **Trimmed mean is what the state-of-the-art forecasting LM system actually uses.** Halawi et al. prompt LMs for multiple reasonings/predictions and "aggregate them into a final forecast using the **trimmed mean**", reaching Brier **0.179** vs the human crowd's **0.149** overall — and **0.199 vs 0.246 (beating the crowd)** in the selective setting where the crowd is uncertain (predictions between 0.3 and 0.7) ([NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf), [arXiv](https://arxiv.org/pdf/2402.18563)).
- **Median across a heterogeneous model crowd matches a human tournament crowd.** 12 LLMs, median-aggregated, 31 binary questions, statistically indistinguishable from 925 human forecasters ([Science Advances 2024](https://www.science.org/doi/10.1126/sciadv.adp1528)).
- **Diversity of runs matters much more than the number of runs.** Herzog & Hertwig's dialectical bootstrapping: averaging a first estimate with a *merely repeated* estimate gained **0.3 percentage points**; averaging with a **dialectical** (consider-the-opposite) estimate gained **4.1pp** (d = 0.53, 72% of participants benefited); averaging with a **different person's** estimate gained **7.1pp** (d = 0.86) ([Psychological Science 2009, PDF](https://library.mpib-berlin.mpg.de/ft/sh/SH_Wisdom_2009.pdf)).
  → **Translation for us: 5 samples of the same prompt ≈ 0.3pp. 5 samples across {different prompt framings, bull/bear, different models} ≈ 4–7pp. Vary the prompt and the model, not just the seed.**
- **Disagreement between runs is itself the signal.** Douven (2026), 15 LLMs × 254 prediction-market questions: learned aggregators beat every individual model and every classical method, and symbolic regression on the learned mapping recovered **a pure model-disagreement signal** as the lowest-complexity useful formula on the Pareto frontier ([arXiv 2607.18269](https://arxiv.org/html/2607.18269v2)).
- **Caveat on extremising:** GJP's extremised elitist aggregation beat the plain aggregate by ~10%, but "the average forecast of a team of super-forecasters often requires very little or no extremizing" ([Satopää et al.](https://www2.math.upenn.edu/~pemantle/papers/forecasting.pdf), [AI Impacts](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/)). For a **point estimate of a continuous quantity**, extremising has no natural analogue — don't invent one. Apply it only to the binary "will they beat consensus?" probability, if we emit one, and only mildly.

### 6.2 Concrete recipe

```ts
// N = 7 runs, deliberately heterogeneous:
//   2 × base prompt, temperature 0.7
//   2 × Fermi-decomposition-first prompt
//   1 × "consider the opposite / bear case" prompt   (dialectical)
//   1 × "bull case" prompt                            (dialectical)
//   1 × second model family                           (dyadic — biggest measured gain)

function aggregate(runs: Forecast[]) {
  const rev = runs.map(r => r.revenue).sort((a,b)=>a-b);
  const eps = runs.map(r => r.eps).sort((a,b)=>a-b);
  return {
    revenue: trimmedMean(rev, 0.2),   // drop top/bottom 20%
    eps:     trimmedMean(eps, 0.2),
    revDispersion: iqr(rev) / median(rev),
    epsDispersion: iqr(eps) / Math.abs(median(eps)),
  };
}
```

- **Trimmed mean over plain mean**: one run with a 10× units error destroys a mean and leaves a trimmed mean untouched. With N=7, 20% trim drops the single highest and lowest.
- **Median for EPS when N is small or EPS is near zero** — percentage dispersion explodes around zero; switch to absolute-cents dispersion when |EPS| < $0.20.
- **Dispersion → three uses:**
  1. **Confidence interval:** report `trimmedMean ± k·IQR`. Calibrate `k` on the eval harness; do not guess it.
  2. **Rerun trigger:** `revDispersion > 3%` or `epsDispersion > 8%` → discard, re-run with a stricter decomposition prompt and 2 extra samples. High dispersion almost always means an ambiguity in the dossier (period mismatch, GAAP vs non-GAAP), not genuine uncertainty — so **fix the dossier, don't just average harder**.
  3. **Escalation input:** high dispersion + large consensus distance = the worst combination; force fallback to `consensus_adjusted`.
- **Bimodality check:** if the runs cluster into two groups separated by more than 3× the within-group spread, a trimmed mean produces a number no run believes. Detect it (simple gap statistic on the sorted array) and route to the critic to resolve the disagreement rather than averaging across it.

---

## Implications for our build

### The pipeline (ordered, with what is code vs LLM)

| # | Gate | Impl | Blocking? | Notes |
|---|---|---|---|---|
| **0** | **Redaction filter** — strip consensus, analyst ranges, price targets from every context reaching the prediction stage | **Code** | Hard | A `redact(dossier)` function + a unit test asserting the consensus number does not appear in any prompt string. This is what makes Gate 6 meaningful. |
| **1** | **Blind multi-run generation**, N=7 heterogeneous (2 base, 2 Fermi-first, 1 bear, 1 bull, 1 other model family) | LLM | — | Structured output only: segments, margins, share count, drivers, claim ids. Temperature 0.7. Runs are independent — no run sees another. |
| **2** | **Deterministic validator** — D1–D7 identities, then D8–D24 | **Code** | D1–D7 = BLOCK; rest = ESCALATE/WARN | Runs per-run *and* on the aggregate. Zero LLM calls. Emits a typed `CheckResult[]`. This is the "external oracle" that Self-Refine showed is required for numeric gains. |
| **3** | **Evidence audit** — E1–E8 in code, then CoVe-factored verification of material claims | **Code + LLM (fresh context)** | Unverified claim ⇒ its driver is dropped | The verifier context contains **only source text + the question**. Never the dossier, never the draft. |
| **4** | **Fresh-context critic + pre-mortem**, blinded to author identity and author reasoning; input = dossier + numbers + `CheckResult[]` | **LLM (different model if available)** | Advisory | Output is a **binary rubric**, one line per item, plus for each defect: `{checkId, claimId, proposedDelta$, confidence}`. Must be able to return `NO_MATERIAL_ISSUE`. Cap output length. |
| **5** | **Aggregate** — trimmed mean (20%), dispersion, bimodality check | **Code** | — | Produces `blind_point`, `blind_interval`. |
| **6** | **REVEAL consensus** → compute `consensus_adjusted = consensus × (1 + firmMedianTrailingSurprise)`, gap, and σ-units | **Code** | — | First time the anchor enters the system. |
| **7** | **Reconciliation** — allocate 100% of the gap to labelled buckets; shrink the unexplained residual by λ≈0.4 | **LLM proposes allocation, code enforces the arithmetic** | Allocation must sum to gap ±1% | `final = consensus_adjusted + Σ(explained) + λ·residual`. Code rejects an allocation that doesn't add up. |
| **8** | **Final re-validation** — rerun D1–D7 and D16 on the reconciled number | **Code** | BLOCK | Catches the classic "revenue moved in reconciliation, EPS didn't reflow". |
| **9** | **Emit** point + interval + the check ledger | Code | — | Persist every `CheckResult` to SQLite for the eval harness. |

### Rerun / escalation policy

```
if (anyBlockingCheckFailed)                    → repair loop, max 2 attempts:
                                                   regenerate ONLY the broken component,
                                                   keep verified claims, then re-validate.
                                                 On 3rd failure → fall back to consensus_adjusted,
                                                 flag LOW_CONFIDENCE.

if (dispersion > threshold)                    → +3 runs with stricter decomposition prompt.
                                                 If dispersion still high → widen interval 2×,
                                                 shrink λ to 0.2 (trust consensus more).

if (bimodal)                                   → critic adjudicates the two clusters
                                                 (which one violates fewer checks?);
                                                 never average across a bimodal split.

if (|gap| > escalation threshold in §3.6)      → require ≥2 documented drivers whose
                                                 quantified impacts explain ≥70% of the gap.
                                                 Unexplained → shrink to consensus_adjusted + 0.3·gap.

if (criticProposedDelta and check agrees)      → apply; else keep the original candidate
                                                 (ART: keeping the original as a live candidate
                                                  and *deciding whether* to refine is worth +5 pts).

Hard cap: 2 QA iterations. Self-correction has negative expected value past that
(Huang et al. 2024), and hackathon wall-clock is the binding constraint.
```

### Things to deliberately NOT build tomorrow
- A same-context self-refine loop (0.0–0.2pp on numbers; costs latency; amplifies self-bias).
- A trained verifier or process reward model (30× effective model size, but needs training data we won't have).
- Multi-round debate (works, but the worst cost/benefit under a 10-hour clock — add only if Gates 0–9 are green by mid-afternoon).
- 1–5 Likert rubrics for the critic (binary criteria give ~20pp better human agreement).
- Any check that adjudicates arithmetic with an LLM (FinVerBench: 95–100% false positives on clean statements).

### Demo/eval angles that this research buys us
- "Our QA stage is **blind to consensus by construction** — here's the redaction test" is a strong, verifiable claim.
- Report **both** the blind estimate and the reconciled estimate. If blind ≈ reconciled, that's evidence of genuine signal; if they diverge, the gap decomposition is itself the interesting artefact.
- The check ledger (which of 24 checks fired, on which quarter) is a far better demo than a single number.
- Ship the A/B: blind-then-reconcile vs consensus-visible, over ~25 historical quarters. That is the paper nobody at the hackathon will have run.

---

## Source index

**Superforecasting / GJP:** [CHAMPS KNOW study (J&DM 2016)](https://goodjudgment.com/wp-content/uploads/2018/12/jdm16511.pdf) · [Cambridge version](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/developing-expert-political-judgment-the-impact-of-training-and-practice-on-judgmental-accuracy-in-geopolitical-forecasting-tournaments/123EB18425391D05FA6581FDBB3F309F) · [Mellers et al. 2014, Psych Science](https://journals.sagepub.com/doi/10.1177/0956797614524255) · [Ten Commandments](https://goodjudgment.com/philip-tetlocks-10-commandments-of-superforecasting/) · [AI Impacts evidence review](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/) · [Klein, HBR premortem](https://lmscontent.embanet.com/USC/PPD554/Week10/PPD554_W10_HBR_Klein_Performaing_a_Project_Premortem.pdf) · [Satopää extremizing](https://www2.math.upenn.edu/~pemantle/papers/forecasting.pdf)

**LLM verification:** [Self-Refine (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/file/91edff07232fb1b55a505a9e9f6c0ff3-Paper-Conference.pdf) · [LLMs Cannot Self-Correct Reasoning Yet (ICLR 2024)](https://arxiv.org/pdf/2310.01798) · [Self-Bias in Self-Refinement (ACL 2024)](https://aclanthology.org/2024.acl-long.826.pdf) · [CoVe (ACL Findings 2024)](https://aclanthology.org/2024.findings-acl.212/) · [LM vs LM (EMNLP 2023)](https://aclanthology.org/2023.emnlp-main.778/) · [Training Verifiers (Cobbe et al.)](https://arxiv.org/abs/2110.14168) · [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) · [CriticGPT](https://cdn.openai.com/llm-critics-help-catch-llm-bugs-paper.pdf) · [Multiagent Debate](https://openreview.net/pdf?id=zj7YuTE4t8) · [PAL](https://proceedings.mlr.press/v202/gao23f.html) · [MT-Bench / LLM-as-judge](https://arxiv.org/pdf/2306.05685) · [Judge bias survey](https://llm-judge-bias.github.io/) · [Rubric agreement](https://arxiv.org/html/2606.08625v2) · [Recursive rubric decomposition](https://arxiv.org/html/2602.05125v1) · [SelfCheckGPT](https://aclanthology.org/2023.emnlp-main.557.pdf) · [ART: Ask, Refine, Trust](https://aclanthology.org/2024.naacl-long.327/) · [SycEval](https://arxiv.org/html/2502.08177v4) · [Self-consistency diminishing returns](https://arxiv.org/pdf/2511.00751)

**Finance / earnings:** [Kim, Muhn & Nikolaev](https://www.arxiv.org/pdf/2407.17866v2) · [Li, Shen, Tu & Zhou (GPT-4 as sell-side analyst)](https://arxiv.org/pdf/2412.01069) · [SSRN version](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4480947) · [KDI: Simulating Analyst Forecast Behavior using LLMs](https://archives.kdischool.ac.kr/handle/11125/69515) · [FactSet Earnings Insight](https://www.factset.com/earningsinsight) · [Call, Hribar, Skinner & Volant — guidance survey](https://mitsloan.mit.edu/sites/default/files/inline-files/Call_Hribar_Skinner_Volant.pdf) · [Hutton, Lee & Shu — when analysts beat management](https://www.hbs.edu/faculty/Shared%20Documents/events/18/HuttonLeeShu2012.pdf) · [PEAD / SUE / Foster review](https://www.sciencedirect.com/science/article/pii/S2214635020303750) · [FinanceBench](https://github.com/patronus-ai/financebench) · [FinVerBench](https://arxiv.org/pdf/2605.29586) · [FAITH](https://arxiv.org/abs/2508.05201) · [PHANTOM](https://openreview.net/pdf?id=5YQAo0S3Hm) · [Forecast dispersion & uncertainty](https://www.anderson.ucla.edu/documents/areas/fac/accounting/working-papers/Xiao_JMP.pdf)

**Anchoring / aggregation:** [Mussweiler, Strack & Pfeiffer 2000](https://journals.sagepub.com/doi/10.1177/01461672002611010) · [Herzog & Hertwig — dialectical bootstrapping](https://library.mpib-berlin.mpg.de/ft/sh/SH_Wisdom_2009.pdf) · [Anchoring bias in LLMs (Lou & Sun)](https://arxiv.org/pdf/2412.06593) · [O'Leary — An Anchoring Effect in LLMs](https://dl.acm.org/doi/abs/10.1109/MIS.2025.3544939) · [Anchors in the Machine](https://arxiv.org/pdf/2511.05766) · [Halawi et al.](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a5acfd0876c940d81619c1dc60e7748-Paper-Conference.pdf) · [Schoenegger et al., Science Advances](https://www.science.org/doi/10.1126/sciadv.adp1528) · [Wisdom of LLM Crowds (Douven 2026)](https://arxiv.org/html/2607.18269v2) · [ForecastBench](https://arxiv.org/pdf/2409.19839) · [LLMs closing the gap on superforecasters](https://forecastingresearch.substack.com/p/llms-are-closing-the-gap-on-human) · [RAND Delphi experiments](https://www.rand.org/pubs/research_memoranda/RM5888.html) · [Meijering & Tobi — own-rating feedback](https://ideas.repec.org/a/eee/intfor/v34y2018i2p216-224.html) · [Soll & Larrick / advice weighting](https://www.hbs.edu/ris/Publication%20Files/06-019.pdf)
