# Getting reliable numeric estimates out of LLMs

Research note for "Agents vs Wall Street" (hackathon 16 Aug 2026). Scope: the **elicitation layer** — how we turn a research dossier into a revenue number and an EPS number that beat/track consensus. Written 15 Aug 2026.

Confidence tags used below: **[primary]** = read from paper abstract/tables directly; **[derived]** = summarized from a PDF by a extraction model, numbers plausible but verify before quoting publicly; **[secondary]** = blog/leaderboard aggregator.

---

## 1. Numeric failure modes, with measured effect sizes

### 1.1 Anchoring on numbers present in context — the single biggest risk for us

Anchoring is measured with the **A-Index** = |median(high-anchor answers) − median(low-anchor answers)| / |anchor_high − anchor_low|. Human range ≈ 0.4–0.6. An A-Index of 0.3 means the model moves 30 cents on the dollar toward an arbitrary number placed in its context.

Measured A-Index on semantic-priming numeric estimation (Huang et al., arXiv:2505.15392) **[primary]**:

| Model | A-Index |
|---|---|
| Llama-3.2-1B | 0.618 |
| Mistral-7B | 0.606 |
| Phi-3.5-mini | 0.590 |
| GPT-4o-mini | 0.475 |
| Llama-3.1-8B | 0.394 |
| GPT-4o | 0.340 |
| Qwen3-235B | 0.321 |
| DeepSeek-R1 | 0.278 |

Reasoning models anchor least (22–25% total ratio vs 40–61% for standard models) but **none is immune**. https://arxiv.org/html/2505.15392v2

Mitigations that were tested and mostly failed:
- Question-aware prompts: ≤2% reduction.
- "Ignore the anchor" / Chain-of-Thought / Reflection / Thoughts-of-Principles: insufficient (also confirmed independently by Lou & Sun, arXiv:2412.06593 — https://arxiv.org/abs/2412.06593).
- Best prompt-level mitigations reached only **~10% reduction**; adversarial finetuning ~10%.
- **Estimate-first prompting (produce your own number before seeing the anchor) increased bias magnitude in some models** when done inside one context — i.e. a "pretend you haven't seen it" instruction is not a control. **[secondary]** https://zylos.ai/research/2026-06-29-anchoring-contamination-chained-llm-pipelines/

**Implication: blinding must be structural (a separate API call whose context literally does not contain the consensus number), not instructional.**

Finance-specific replication: Nguyen (2024), *Human bias in AI models? Anchoring effects and mitigation strategies in LLMs*, RCTs on GPT-4 / Claude 2 / Gemini Pro / GPT-3.5 forecasting tasks — anchoring present in all four; CoT and "ignore previous" gave limited and inconsistent mitigation. https://doi.org/10.1016/j.jbef.2024.100971

A 2026 controlled stress test of numeric anchoring on counting tasks (ErrorBench, arXiv:2607.01240) **[primary]**: moving from a *blind* prompt to an *anchored* prompt lifted the count-based F1 by **+0.21 averaged over six models** while the underlying span-level quality moved only **+0.04** — i.e. the anchor moved the number, not the knowledge. Anchoring response was *larger* in highly instruction-compliant GPT/Claude systems. Their explicit recommendation: "avoid prepopulated error counts". Direct analogue for us: avoid prepopulated consensus. https://arxiv.org/pdf/2607.01240

Chained pipelines amplify this: a stage-2 model reading a stage-1 numeric verdict conditions on it as ground truth; "Contextual Drag" (arXiv:2602.04288) shows noisy rationales in context degrade performance **even when the model is explicitly told to critique them**. **[secondary]**

### 1.2 Round-number bias / digit preference

- LLM score distributions peak on multiples of 10 (60/70/80/90) and 5 (75/85/95). In allocation tasks **89–100% of percentages were multiples of 5** across models. **[secondary, from search synthesis of arXiv:2405.01724 and arXiv:2604.23837]**
- *Benford's Curse* (arXiv:2506.01734): LLMs systematically overgenerate small leading digits even against uniform targets; the bias is driven by FFN layers whose aggregated preference mirrors the Benford-skewed digit distribution of pretraining corpora. https://arxiv.org/html/2506.01734
- LLMs as random number generators converge on human-favourite "random" numbers (37, 47, 73). https://arxiv.org/pdf/2502.19965

**Implication:** an EPS estimate of exactly $2.50 or a revenue of exactly $10,000M is weak evidence of a real estimate. Log it as a diagnostic (last-digit histogram over the eval set) — if our P50s cluster on round values, the model is guessing, and we should fall back to consensus.

### 1.3 Sycophancy toward a provided consensus

SycEval (arXiv:2502.08177) **[primary]**: sycophantic behaviour in **58.19%** of cases across medical and mathematical queries; **regressive** sycophancy (correct → incorrect after user pushback) in **14.66%**; persistence of the flipped answer **78.5%** [95% CI 77.2–79.8]. Gemini highest (62.47%), ChatGPT lowest (56.71%). https://arxiv.org/html/2502.08177v4

Simple opinion statements ("I believe the answer is X") induced agreement with incorrect beliefs at **63.7% average across seven model families, range 46.6–95.1%**. **[secondary]**

**Implication:** presenting "Wall Street consensus is $X" is functionally identical to a user asserting a belief. Expect the model to land within a few percent of consensus and to produce post-hoc justification. That is fine if we *want* a consensus-tracking forecast — it is fatal if we want an independent one for surprise detection.

### 1.4 Insensitivity to magnitude / scale

- QuantSightBench (arXiv:2604.15859) **[primary]**: "Calibration degrades sharply at extreme magnitudes, revealing systematic overconfidence across all evaluated models"; scale sensitivity is named as a key failure mode. https://arxiv.org/pdf/2604.15859
- Numbers are fragmented by tokenizers into subword units that lose magnitude ("100400" → "100"+"400"); hidden states encode digits in base-10 circular representations rather than magnitude (arXiv:2410.11781). LLM numeric errors are **far in value space but close in digit space** — models produce "633"/"823" where the answer is "833", not near-misses like "831". https://arxiv.org/pdf/2410.11781, https://arxiv.org/pdf/2602.07812
- Representational geometry warps at digit-count boundaries; more errors on problems crossing 9,999 → 10,000 style boundaries (arXiv:2603.28258).
- NUMCoT (arXiv:2406.02864) **[primary]**: LLMs "consistently struggle to memorize conversion ratios between different units"; the majority of errors concentrate on failing to identify the *magnitude* of individual numbers. Notably, they also found **introducing CoT in certain numeral/unit sub-tasks significantly deteriorates performance**. https://arxiv.org/pdf/2406.02864

**Implication:** never let a unit or scale be implicit. Every number in and out carries an explicit unit string. A $1,234M vs $1.234B vs $1,234,000K confusion is a 1000× error that our eval will score as catastrophic and that no amount of good research prevents.

### 1.5 Arithmetic errors in token space

- PAL (Gao et al., arXiv:2211.10435): delegating computation to a Python interpreter beats CoT by **+8 pts absolute on GSM8K** and **+40 pts absolute on GSM-Hard** (the variant with large/awkward numbers — exactly our regime). https://arxiv.org/pdf/2211.10435
- Program-of-Thoughts on **financial** QA: **~+12% average over CoT on FinQA, ConvFinQA, TATQA**. **[secondary]**
- *The Deterministic Horizon* (arXiv:2606.00376) **[primary]**: across 12 models and 8 task domains, tool-integrated reasoning reached **86–94% accuracy vs 24–42% for neural chain-of-thought** on deterministic state-tracking; they identify a "Deterministic Horizon" d* ∈ [19, 31] steps beyond which tool delegation is necessary; fine-tuning on optimal-length traces recovers <5%, i.e. an architectural ceiling. Cross-model correlation r = 0.81–0.91. https://arxiv.org/pdf/2606.00376

**Implication: zero in-head arithmetic. Every multiply/divide goes through a TS function. This is the cheapest, largest-effect intervention available to us.**

### 1.6 Position / recency effects in long contexts

- *Lost in the Middle* (Liu et al., TACL 2023, arXiv:2307.03172): U-shaped performance — best when the relevant evidence is at the **start or end** of the context, materially worse in the middle. https://ui.adsabs.harvard.edu/abs/2023arXiv230703172L/abstract
- Chroma *Context Rot* (2025) **[secondary]**: 18 frontier models (incl. GPT-4.1, Claude 4, Gemini 2.5, Qwen3); **every** model degrades as input length grows, with accuracy drops of **30–50%** well before the nominal context limit, and degradation worsens as needle–question similarity falls (the realistic case). https://www.trychroma.com/research/context-rot
- Halawi et al. measured this indirectly: their system's Brier score is a **tuned hyperparameter of `k` article summaries**, not "more is better" — they sweep `k` and the summary ordering criterion (relevance vs recency) on a validation set. https://arxiv.org/html/2402.18563v1

**Implication:** an "everything we found" dossier will be worse than a curated 8–15 item dossier. Order matters and should be a tuned knob, not a default.

### 1.7 Overconfidence in stated intervals

This is the best-quantified failure mode and it directly determines whether our P10/P90 are usable.

**FermiEval** (Epstein et al., arXiv:2510.26995, Stanford) **[primary]** — 500 train / 500 test Science-Olympiad Fermi questions (ground truth = base-10 exponent), models: GPT-4o-mini, Claude-3.5-Haiku, Grok-3-mini (small cost-tier frontier models — caveat):
- **Nominal 99% intervals cover the true answer only ~65% of the time on average.** Coverage *plateaus* below nominal as the requested confidence rises.
- Conformal-prediction adjustment restores accurate 99% observed coverage and cuts the **Winkler interval score by 54%**.
- Direct **log-probability elicitation** (first-token top-K logprobs over an integer-only answer format, normalized into a discrete distribution) improved GPT-4o-mini coverage from **0.63→0.85 at 90%**, **0.59→0.89 at 95%**, **0.64→0.90 at 99%**.
- *Perception-tunnel theory*: the model behaves as if sampling from a truncated slice of its own inferred distribution, neglecting the tails — which predicts exactly the observed plateau.
https://arxiv.org/pdf/2510.26995

**QuantSightBench** (Qin & Andriushchenko, ELLIS Tübingen, arXiv:2604.15859, Apr 2026) **[primary]** — numeric forecasting with 90% prediction intervals, restricted to models with knowledge cutoffs before Sept 2025 to avoid leakage. Empirical coverage of nominal **90%** intervals, agentic (retrieval-enabled) setting:

| Model | Coverage of nominal 90% PI |
|---|---|
| Gemini 3.1 Pro | 79.1% |
| Grok 4 | 76.4% |
| GPT-5.4 | 75.3% |
| GPT-5.1 | 74.6% |
| Claude Opus 4.6 | 73.6% |
| Claude Opus 4.5 | 71.7% |
| Claude Sonnet 4.5 | 68.0% |
| Kimi K2 Thinking | 65.8% |
| Gemini 3 Pro | 65.4% |
| GLM-4.7 | 62.7% |
| DeepSeek v3.2 | 61.5% |

**No model reaches the 90% target; the best is >10 pts short.** They do find a positive trend between relative interval width and mean relative error (models do widen intervals when less accurate — some signal), and confirm calibration collapses at extreme magnitudes. https://arxiv.org/pdf/2604.15859

Corroborating: *Overconfidence is Key* (TrustNLP 2024) finds high calibration error and overconfidence for verbalized mean/σ and 95% CIs across LLMs and VLMs. https://aclanthology.org/2024.trustnlp-1.13/

**Implication:** treat any model-stated 90% interval as roughly a **70–75% interval**. Multiply widths by a factor learned on our backtest (a one-line conformal correction), or we will report intervals that miss ~30% of the time.

---

## 2. Elicitation format: point vs interval vs distribution

### 2.1 Ask for quantiles, not a point estimate

Evidence stack:
- QuantSightBench argues (and demonstrates) that prediction intervals are the right interface for numeric forecasting: they force **scale awareness, internal consistency across confidence levels, and calibration over a continuum**, and are strictly more informative than a point. Frontier models *spontaneously* emit ranges when asked for continuous quantities. **[primary]**
- *Eliciting Numerical Predictive Distributions of LLMs Without Autoregression* (arXiv:2603.02913) **[derived]** identifies a concrete pathology in autoregressive numeric sampling: generating a number digit-by-digit creates path dependency — once the model emits "1", the remaining values are constrained to 1X.XX even if its true belief mass sits higher. Direct quantile elicitation (explicitly asking for the 10th / 50th / 90th percentile as separate fields) improved calibration and CRPS vs both naive sampling and vague verbalized bounds ("lower bound / best guess / upper bound"). Practical recommendations from the paper: ask for **numeric percentiles explicitly by name**, avoid narrative bound language, and validate coverage empirically. https://arxiv.org/pdf/2603.02913
- FermiEval's log-probability method is the strongest calibration fix they found short of conformal, but it needs top-K logprobs over a constrained integer format — practical for a bucketed/discretized target, awkward for continuous revenue. Worth noting as a stretch goal, not a hackathon default.

**Verdict: elicit P10 / P50 / P90 for each target (revenue, EPS). Use P50 as the point estimate. Do NOT ask for "your estimate and a confidence %".**

### 2.2 Reasoning first, number last

- No paper cleanly isolates order for numeric estimation, but the mechanism is well established: CoT lets the model condition its answer on its own intermediate tokens; answer-first forecloses that. Halawi et al.'s optimal scratchpad ends with the probability after a structured reasoning sequence, including a final step where "the model is asked to check if it is over- or under-confident and to consider historical base rates, prompting it to calibrate and amend the prediction accordingly." **[primary]** https://arxiv.org/html/2402.18563v1
- Counter-signal: NUMCoT found CoT **hurts** on pure numeral/unit conversion sub-tasks. So: reasoning for the *judgment*, tools for the *conversion*.
- Caveat worth knowing: models often determine the answer internally before the visible CoT ends — truncating CoT mid-stream frequently does not change the prediction for large models. So CoT is a real but not unbounded lever.

**Verdict: always reasoning-then-number. In a JSON schema, the reasoning fields must be declared BEFORE the numeric fields** — strict structured decoding emits keys in schema order, so schema order = generation order = whether the model gets to think first.

### 2.3 Structured output (JSON schema): net effect on numeric quality

*Let Me Speak Freely?* (Tam et al., arXiv:2408.02442) reported significant reasoning degradation under format restriction, with stricter constraints worse. GPT-4o-mini GSM8K in their runs: NL **94.57** → JSON-Schema **91.71** → FRI **87.17** → JSON-mode **86.95**. https://arxiv.org/html/2408.02442v1

But the .txt rebuttal + Dylan Castillo's independent replication **[secondary, well-documented]** show most of that gap was prompt quality, not constrained decoding:

| Task (GPT-4o-mini) | NL | FRI | JSON-Mode | JSON-Schema |
|---|---|---|---|---|
| GSM8K — Tam et al. | 94.57 | 87.17 | 86.95 | 91.71 |
| GSM8K — replication, 0-shot | 94.31 | 92.12 | 93.33 | **93.48** |
| Shuffled Obj. — Tam et al. | 82.85 | 81.46 | 76.43 | 81.77 |
| Shuffled Obj. — replication, 0-shot | **95.12** | 79.67 | 81.71 | 89.84 |

For LLaMA3-8B, structured was **as good or better** than unstructured on all three reasoning tasks. https://dylancastillo.co/posts/say-what-you-mean-sometimes.html

**Verdict:** structured output is safe for us **provided** (a) a free-text reasoning field precedes the numeric fields in the schema, and (b) the prompt is written as carefully as an unstructured one. The residual risk is real but small (a few points), and the parsing reliability is worth far more than a few points at hackathon speed. The "NL-to-format" two-call pattern (reason freely, then a cheap second call converts to JSON) is the fallback if we see numeric degradation — but it costs a round trip and adds a transcription-error surface.

### 2.4 Force units and scale, in both directions

No dedicated ablation found, but NUMCoT's magnitude/unit failures + QuantSightBench's scale-sensitivity finding + the tokenizer/magnitude literature all point the same way. Concretely:
- Every schema numeric field name carries its unit: `revenue_p50_usd_millions`, `eps_diluted_p50_usd_per_share`.
- The prompt states the scale once, explicitly, with a worked example: *"Report revenue in USD millions. Example: $12.34 billion → 12340."*
- Add a `units_restated` echo field the model must fill ("USD millions") — cheap self-check, and a parse guard.
- Deterministic post-hoc sanity gate in TS: reject any revenue P50 more than 3× or less than 0.33× the trailing-four-quarter average unless the model set an explicit `regime_change` flag. Catches the 1000× class of error for free.

### 2.5 Reference results for LLM probabilistic forecasting quality

- **Halawi et al. 2024** (NeurIPS) **[primary]**: retrieval-augmented GPT-4 system, test set of 914 binary questions opened after the model cutoff. System **Brier .179** vs crowd **.149** (accuracy 71.5% vs 77.0%). Zero-shot baselines were near-chance (random = .250; best baseline GPT-4-1106 = .208). Selective settings where it *beat* the crowd: crowd-uncertain questions (crowd pred in 0.3–0.7) **.238 vs .240**; all-criteria subset **.240 vs .247**. Weighted average of system + crowd beat both in *every* setting (**.146** unconditionally). https://arxiv.org/html/2402.18563v1
- **ForecastBench** (Forecasting Research Institute) **[primary]**: as of Jul 2026, several systems are statistically indistinguishable from superforecasters; the top system (Cassi) ranks **above** the superforecaster median on market questions for the first time. Jan 2026 standings had superforecasters leading SOTA LLMs by 0.017 Brier ≈ one year of LLM progress. https://forecastingresearch.substack.com/p/ai-models-have-likely-reached-parity , https://www.forecastbench.org/tournament/
- **Metaculus AI Benchmark** **[secondary]**: Spring 2026 Cup, `metac-claude-4-5-sonnet-high-32k+asknews` ranked **33rd of 1130 humans** (top ~3%); Metaculus's own position as of May 2026 is that Pros still beat individual bots head-to-head. https://www.metaculus.com/aib/2026/spring/
- **Wisdom of the Silicon Crowd** (Science Advances) **[primary]**: ensemble of 12 LLMs ≈ statistically indistinguishable from a crowd of 925 humans (Brier ≈ 0.20). Aggregation methods were near-identical: **median 0.197, trimmed mean 0.197, geometric mean 0.194**. Exposing LLMs to the median human prediction improved their accuracy by **17–28%**. https://www.science.org/doi/10.1126/sciadv.adp1528
- **LLMTime** (Gruver et al., NeurIPS 2023): LLMs zero-shot extrapolate numeric time series at or above purpose-built models, because digit-string next-token prediction naturally represents multimodal distributions. Important caveat for us: **RLHF-aligned models break the scaling trend — GPT-4 was worse than GPT-3** at raw numeric extrapolation. Reinforces "don't ask a chat model to be a time-series model; ask it to reason about drivers and let code do the extrapolation." https://arxiv.org/pdf/2310.07820

### 2.6 Domain evidence: LLMs vs sell-side analysts on earnings

Two results that point in opposite directions and both matter for our framing:
- **Kim, Muhn & Nikolaev (arXiv:2407.17866)** **[primary]**: anonymized financial statements only, predicting *direction* of next-year earnings change. Analysts (1-month consensus) 52.71% accuracy; GPT-4 with a simple prompt 52.33%; **GPT-4 with CoT 60.35%** — ~7pp above analysts, significant at 1%. Even top-quintile "high-ability" analysts (56.75%) are beaten. GPT's edge is largest exactly where analysts are biased or disagree. https://arxiv.org/html/2407.17866v2
- **Li, Shen, Tu & Zhou (arXiv:2412.01069)** **[primary]**: GPT-4 forecasting one-year-ahead GAAP EPS from earnings press releases, scaled |forecast error| vs I/B/E/S consensus, 7,114 releases. **GPT underperforms analysts on average**, but the 25th percentile of the error difference is −0.001 → **GPT beats analysts in >25% of firm-quarters**. Accuracy improves with "MetricOverlap" (whether GPT focused on the metrics analysts focus on): mean error falls from 0.117 at zero overlap to 0.061 at highest overlap (**−48%**). Modest degradation after the knowledge cutoff. https://arxiv.org/pdf/2412.01069

**Reading for our build:** an LLM is *not* going to beat consensus on the level of EPS. Our edge, if any, is (a) *direction of surprise* and (b) *knowing when to defer*. Both Halawi and Li point at the same shape: score selectively, and blend with the consensus prior rather than replacing it.

---

## 3. Sampling strategy

### 3.1 N and T

- Halawi et al.'s production configuration: **6 forecasts total** — 3 from the base model with the top-3 scratchpad prompts, 3 from a fine-tuned model at **T = 0.5** — aggregated by **trimmed mean**, chosen over mean, median, geometric mean and universal self-consistency on the validation set. **[primary]**
- Silicon Crowd: median / trimmed mean / geometric mean all within 0.003 Brier of one another. Aggregator choice is a second-order knob; **having an ensemble at all is the first-order one**. **[primary]**
- Self-consistency's original gains were large (+9–23% for large models; up to +27.6pp on GSM8K) but that was 2022-era models. *Self-Consistency Is Losing Its Edge* (arXiv:2511.00751) reports diminishing returns and linearly scaling cost on modern LLMs; the summary I extracted puts **optimal N at ~5–10 with a plateau at N≈10–15**, and reasoning models gaining **<1%** from added samples. **[derived — treat the exact figures as indicative, the qualitative claim is solidly supported by the abstract]** https://arxiv.org/pdf/2511.00751
- Temperature: Renze & Guven (EMNLP Findings 2024) found **no statistically significant effect of T between 0.0 and 1.0** on problem-solving accuracy across nine LLMs and five prompting techniques. https://aclanthology.org/2024.findings-emnlp.432/ For *ensembling*, though, T > 0 is what generates the diversity you are averaging over — T=0 with N samples is N copies. Optimizing-temperature-for-multi-sample work (Du et al., ICML 2025) confirms T selection materially changes multi-sample aggregate performance and proposes an entropy-based auto-tuner. https://proceedings.mlr.press/v267/du25f.html

**Verdict for a one-day build: N = 5–8, T = 0.6–0.8, aggregate with a trimmed mean (drop min and max).** Do not spend the day tuning N; spend it on the dossier.

### 3.2 Diversity beats raw N

The bigger lever than "more samples of the same prompt" is **prompt/model diversity**:
- Halawi: 3 *different* scratchpad prompts, plus two different models (they explicitly note Claude-2.1 is better on some questions and used both when generating candidates).
- Cassi (ForecastBench #2): multi-stage pipeline generating sub-questions and search queries, then forecasting with an **ensemble of models (o3 + GPT-5)**, with another model analyzing the reasoning. **[primary, via FRI writeup]**
- xAI's ForecastBench submission was deliberately minimal: give the model tools, **generate eight forecasts, average them**. That simple recipe placed #2 on the leaderboard. **[primary]** https://forecastingresearch.substack.com/p/llms-are-closing-the-gap-on-human

**Verdict: N=6 as 3 prompt variants × 2 models beats N=6 as one prompt × 6 samples.**

### 3.3 Reasoning models vs sampling ensembles, per dollar

- Reasoning/extended-thinking models anchor less (A-Index 0.278 for DeepSeek-R1 vs 0.475 for GPT-4o-mini) and benefit far less from self-consistency (<1% per arXiv:2511.00751 **[derived]**) — the internal sampling is already happening.
- QuantSightBench's coverage table shows the *interval calibration* ranking is not the same as the general capability ranking (Grok 4 at 76.4% above GPT-5.4 at 75.3% above Opus 4.6 at 73.6%). Capability leaderboards will not tell you who is best calibrated.
- Practical read for a hackathon budget: **one strong reasoning model at medium effort × 5 samples across 3 prompt variants** dominates *either* extreme (single deterministic call, or 30 samples of a cheap model). Reserve the big model for the final estimation call; use a cheap model for dossier construction, relevance filtering and summarization (this is exactly Halawi's split: GPT-3.5 for filtering/summarizing, GPT-4 for reasoning — saving 70% cost on the filtering step alone).

---

## 4. Decomposition prompting and the arithmetic policy

### 4.1 Fermi decomposition vs direct estimate — weaker than you'd hope

*LLM for Complex Reasoning Task: An Exploratory Study in Fermi Problems* (arXiv:2504.02671) **[secondary summary]**:
- GPT-4 best, with an **average error factor of ~10×**.
- CoT beat standard prompting across all models.
- **The level of decomposition did not strongly correlate with accuracy.** "Plain Fermi" prompting performed about as well as elaborate schemes for the top models.
- The binding constraints were **factual knowledge gaps and calculation errors**, not decomposition strategy.
https://arxiv.org/pdf/2504.02671

**Important nuance for us:** that finding is about *generic* Fermi questions where the model must invent the decomposition and supply the facts. In our task the decomposition is **domain-given** (segments → units × ASP → revenue; revenue → gross margin → opex → operating income → tax → net income → ÷ diluted shares → EPS) and the facts come from filings, not from the model's memory. So decomposition still earns its keep *for us* — not because it improves reasoning, but because:
1. it converts one unauditable number into ~10 auditable ones, each independently checkable against the dossier;
2. it lets us compute the answer in TS instead of in tokens;
3. it gives us per-driver uncertainty we can Monte-Carlo into a proper P10/P50/P90 rather than a verbalized one;
4. it is the demo story — a judge can see *why* the number is what it is.

Counter-risk from the analyst literature: Unpacking analyst forecast bias (2025, N=97 professional analysts) found **disaggregated forecasting amplifies optimistic bias when initial optimism is present** (confirmation bias). https://businessperspectives.org/journals/investment-management-and-financial-innovations/issue-474/... — so decomposition + a bullish framing is *worse* than aggregate. Keep the estimation prompt tonally neutral and don't feed it a "strong buy" style narrative.

### 4.2 Arithmetic: always compute in code. How to enforce it.

Effect sizes (see §1.5): PAL +40pp on GSM-Hard, PoT ~+12% on financial QA, tool-integrated 86–94% vs CoT 24–42% on state tracking.

Enforcement mechanics that actually work, in order of strength:

1. **Schema starvation (strongest, zero-trust).** The output schema contains **no** field for the derived quantity. The model emits only *drivers* — segment revenues, gross margin %, opex, tax rate, diluted share count. `total_revenue` and `eps` do not exist as writable fields. Our TS code computes them. The model physically cannot report a mis-multiplied EPS because there is nowhere to put it.
2. **Tool-only arithmetic.** Expose a `calc(expression)` tool and instruct that any product/quotient must come from it. Weaker than (1) because compliance is instructional, but useful for intermediate reasoning. Note: OpenAI structured outputs support `minimum`/`maximum`/`multipleOf`; **the Claude API does not** — so numeric range enforcement must live in our validator either way.
3. **Post-hoc recompute-and-diff.** Whatever the model reports, recompute from its own drivers and assert |reported − recomputed| / recomputed < 0.5%. Log every violation; violations are a strong quality signal for the eval writeup (and a great demo slide).
4. **Reject-and-retry** on any residual violation, with the diff shown back to the model.

Do (1) + (3) for the hackathon; they're an hour of work combined.

---

## 5. Context design

### 5.1 How much context before it hurts

- Chroma: **all 18 models degrade with length; 30–50% accuracy drops before nominal limits**, worse when the needle is only semantically related to the question (our case exactly — a 10-K risk factor is never lexically similar to "Q3 revenue"). **[secondary]**
- Liu et al.: U-shaped position curve. **[primary]**
- Halawi: the number of article summaries `k` and their ordering were *swept* as hyperparameters; the system's best selective bucket was "**≥5 relevant articles**" (Brier .175 vs .179 overall) — i.e. there is a floor below which retrieval is useless, and the win came from *relevance filtering*, not volume. They filter with a cheap model on title + first 250 words, and summarize each article against the question before it ever reaches the reasoning model. **[primary]**
- Li et al. (2412.01069): GPT's error fell 48% when the metrics it attended to overlapped with the metrics analysts attend to. **Curation of *which* numbers are in front of the model is worth ~half the error.** **[primary]**

**Verdict: hard-cap the estimation-prompt dossier at ~10–15 curated items / ~8–12k tokens. Summarize every source against the specific question before it enters the estimation context.** The 1M-token windows are a trap here.

### 5.2 Ordering

Given the U-shape, put the two highest-probative blocks at the **top and bottom** of the dossier and bury boilerplate in the middle. For quarterly earnings the natural assignment is:

- **Top:** the structured financial history table (last 8 quarters: revenue, GM%, opex, EPS, share count, YoY/QoQ growth) + company guidance for the quarter being forecast.
- **Middle:** transcript excerpts, industry datapoints, macro, peer prints, channel checks.
- **Bottom (last thing before the question):** the single most decision-relevant recent item — the guidance range, or the latest datapoint that post-dates guidance.

Make ordering a config flag (`recency_last` vs `relevance_last`) and A/B it if there's time; Halawi treated exactly this as a tunable and it moved their score.

### 5.3 Separate the dossier from the estimation prompt

Two distinct calls, two distinct artifacts:
- **Call A (dossier):** agentic, tool-heavy, cheap model, produces a *frozen, versioned, deterministic* `EvidenceDossier` JSON stored in SQLite. It never emits a forecast.
- **Call B (estimation):** no tools except `calc`, strong model, sees only the dossier + task spec. Reproducible: same dossier row + same seed config → comparable outputs.

This is not just hygiene — it is what makes the eval harness meaningful (you can hold the dossier fixed and A/B the estimation prompt, which is the only way to attribute a score change in a one-day build).

### 5.4 Blinding: withhold consensus until after an independent estimate

Evidence supporting structural blinding:
- Anchoring A-Index 0.28–0.62 (§1.1) — a consensus number in context will drag the estimate by roughly a third of any displacement.
- ErrorBench: blind → anchored moves the reported number +0.21 F1 while true quality moves +0.04. **[primary]**
- Sycophancy: 58% overall, 14.7% correct→incorrect flips under mere disagreement. **[primary]**
- Prompt-level anti-anchoring instructions ("ignore the anchor", CoT, reflection) achieve ≤10% reduction; **in-context estimate-first can backfire.** So the control must be that the consensus token is *never in the context*.

Evidence that the consensus is nevertheless genuinely informative and should be used *afterwards*:
- Silicon Crowd: exposing LLMs to the human median **improved accuracy 17–28%**. **[primary]**
- Halawi: the weighted average of system + crowd beat both in **every** setting (.146 vs .179 system, .149 crowd). **[primary]**
- Cassi's ForecastBench "crowd adjustment" — compare the final forecast to the market price and, if they diverge significantly, let an LLM review and adjust — improved Brier by **~0.01** over the same ensemble without it. **[primary, via FRI]**
- Analysts' consensus is itself a top-3 feature in ML earnings models (van Binsbergen, Han & Lopez-Lira, NBER w27843: analyst forecasts have the highest normalized feature importance ≈0.20, ahead of past earnings ≈0.15 and price ≈0.10). https://www.nber.org/system/files/working_papers/w27843/w27843.pdf

**Verdict: a three-stage protocol — blind estimate → reveal consensus → bounded reconciliation — with the blind estimate persisted separately so we can score both and report the anchoring displacement as a headline metric.** (That displacement number is also, frankly, the most demo-able artifact in this whole project: "our agent moves X% toward consensus when shown it; here is the same agent blinded.")

---

## 6. Model choice as of 15 Aug 2026

### 6.1 Anthropic (verified from platform.claude.com/docs — Models overview)

| Model | API ID | Ctx | Max out | Price in/out per MTok | Adaptive thinking | Reliable knowledge cutoff | Training cutoff |
|---|---|---|---|---|---|---|---|
| Claude Fable 5 | `claude-fable-5` | 1M | 128k | $10 / $50 | Yes (always on) | **Jan 2026** | Jan 2026 |
| Claude Opus 5 | `claude-opus-5` | 1M | 128k | $5 / $25 | Yes | **May 2026** | May 2026 |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | 128k | $2 / $10 | Yes | **Jan 2026** | Jan 2026 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200k | 64k | $1 / $5 | No (extended thinking) | **Feb 2025** | Jul 2025 |
| Claude Mythos 5 | `claude-mythos-5` | 1M | 128k | $10 / $50 | Yes | Jan 2026 | Jan 2026 (invite-only, Project Glasswing) |

Legacy but still available and relevant for leakage-free backtests: Opus 4.8 / 4.7 (Jan 2026), Opus 4.6 (**May 2025**), Sonnet 4.6 (**Aug 2025**), Sonnet 4.5 (**Jan 2025**), Opus 4.5 (**May 2025**).
- `effort` parameter defaults to `high` on Opus 5 / Sonnet 5 on the API — set it explicitly if we want cheaper/faster estimation calls.
- Fable 5 uses the Opus-4.7-generation tokenizer: **the same text produces ~30% more tokens** than pre-4.7 models. Budget accordingly.
- Batch API supports up to 300k output tokens with the `output-300k-2026-03-24` beta header — useful for a bulk backtest sweep.
https://platform.claude.com/docs/en/about-claude/models/overview

**Structured numeric output ergonomics (Claude):** `output_config.format = { type: "json_schema", schema: {...} }` (older `output_format` deprecated). Supports `object/array/string/integer/number/boolean/null`, `enum`, `const`, `required`, `additionalProperties: false`, `anyOf`/`allOf`. **Does NOT support `minimum`, `maximum`, `multipleOf`, `minLength`/`maxLength`, recursive schemas, or external `$ref`.** First use of a schema pays a grammar-compilation latency; cached 24h. Changing the format invalidates the prompt cache — so freeze the schema early or you lose caching across the backtest sweep. https://platform.claude.com/docs/en/build-with-claude/structured-outputs

### 6.2 OpenAI (verified from developers.openai.com/api/docs/models)

| Model | Ctx | Max out | Price in/out per MTok | Knowledge cutoff | Reasoning |
|---|---|---|---|---|---|
| `gpt-5.6-sol` | 1.05M | 128k | $5 / $30 | **Feb 16, 2026** | Yes (multiple levels) |
| `gpt-5.6-terra` | 1.05M | 128k | $2 / $12 | **Feb 16, 2026** | Yes |
| `gpt-5.6-luna` | 1.05M | 128k | $0.20 / $1.20 | **Feb 16, 2026** | Yes |

Earlier in-family: `gpt-5.5` (Dec 2025 cutoff), `gpt-5.4` (snapshot `gpt-5.4-2026-03-05`) — both support structured outputs. The o-series is no longer the frontier reasoning line; GPT-5.x carries reasoning-effort levels natively.

**Structured numeric output ergonomics (OpenAI):** `text.format` with `type: "json_schema"`, `strict: true`. Supports `number`, `integer`, and — unlike Claude — **`minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`**, plus numeric `enum`. Not supported: `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`/`then`/`else`. Their own CoT example puts a `steps[]` array of `{explanation, output}` **before** `final_answer` — consistent with §2.2. https://developers.openai.com/api/docs/guides/structured-outputs

### 6.3 Which is strongest for quantitative estimation

Honest answer: **nobody publishes the benchmark we actually need.** Nearest evidence:
- QuantSightBench (interval calibration on numeric forecasting, the closest analogue): Gemini 3.1 Pro > Grok 4 > GPT-5.4 > GPT-5.1 > Opus 4.6 > Opus 4.5 > Sonnet 4.5. **[primary]** Their cutoff-before-Sept-2025 restriction means GPT-5.6 / Opus 5 / Fable 5 are unmeasured.
- ForecastBench (binary judgmental forecasting): frontier systems now at superforecaster parity; the winners are *pipelines* (Cassi, xAI+tools), not raw models. **[primary]**
- BenchLM aggregator, 15 Aug 2026 snapshot **[secondary — third-party, treat as directional]**: Claude Mythos 5 83.21, Claude Opus 5 83.07, Claude Fable 5 82.96, GPT-5.6 Sol 82.00 overall; GPT-5.6 Sol scores 97 on the math composite (AIME26 / HMMT Feb 2026 / FrontierMath v2 / USAMO 2026). https://benchlm.ai/

**Practical picks for tomorrow:**
- **Estimation call (primary):** `claude-opus-5` — freshest cutoff (May 2026), $5/$25, adaptive thinking, and the effort dial. Anthropic credits may be the constraint; if OpenAI credits are the funded path, `gpt-5.6-sol` at high reasoning effort.
- **Estimation call (diversity partner for the ensemble):** the other vendor. Cross-vendor diversity is the highest-value form of ensemble diversity (§3.2).
- **Dossier / retrieval / summarization / relevance filtering:** `gpt-5.6-luna` ($0.20/$1.20) or `claude-haiku-4-5` ($1/$5). This is 80% of our token volume; do not run it on a frontier model.

### 6.4 Leakage — read this before choosing eval quarters

This is a real scoring hazard, and the judges may probe it.

- `gpt-5.6-*`: cutoff **16 Feb 2026** → knows actuals for everything reported up to ~mid-Feb 2026, i.e. through most of the Q4 CY2025 season.
- `claude-opus-5`: cutoff **May 2026** → knows Q1 CY2026 actuals (reported Apr–May 2026). **Worst leakage profile of the lot for backtesting.**
- `claude-fable-5` / `claude-sonnet-5` / `claude-opus-4-8` / `claude-opus-4-7`: **Jan 2026** → clean for anything reported Mar 2026 onward.
- `claude-sonnet-4-6`: **Aug 2025**; `claude-opus-4-6` / `claude-opus-4-5`: **May 2025**; `claude-haiku-4-5`: **Feb 2025** → progressively cleaner, progressively weaker.

**Clean backtest windows:**
- Q1 CY2026 prints (reported ~Apr–May 2026): clean for every model with a Jan-2026-or-earlier cutoff. **Not** clean for Opus 5.
- Q2 CY2026 prints (reported ~Jul–Aug 2026): clean for **every** model listed, including Opus 5 and GPT-5.6. **This is the safest backtest set and it is large — use it.**
- The live target (a company reporting after 16 Aug 2026) is clean for everything.

Li et al. found GPT's relative accuracy degrades modestly post-cutoff (mean error diff 0.033 pre vs 0.038 post) — so expect our backtest numbers to flatter us slightly relative to the live run, and say so in the writeup.

---

## Implications for our build

### The protocol to implement tomorrow

**Stage 0 — Dossier (cheap model, agentic, cached to SQLite).**
Output a frozen `EvidenceDossier` row: `{company, ticker, fiscal_quarter, as_of_date, financial_history[8 quarters], guidance{}, evidence_items[≤15]{source_url, date, one_paragraph_summary_written_against_the_question, probative_rank}}`. Every evidence item is summarized *against the specific forecasting question* by the cheap model before it is stored (Halawi's filter+summarize step; ~70% cost saving and it is what makes the estimation context small). **The dossier must not contain the consensus.** Store consensus in a *separate table*, keyed by the same row, so a coding mistake can't leak it into the prompt. Hard cap: 12k tokens.

**Stage A — BLIND estimate (strong model, N samples).**
Separate API call. Context = system prompt + dossier only. Consensus absent from the context. Output schema, in this exact field order:

```
1. scale_check          : string   // must echo "revenue in USD millions; EPS in USD per diluted share, 2dp"
2. reasoning            : string   // free text, the model's analysis. FIRST so it generates before any number.
3. key_drivers[]        : { name, unit, p10, p50, p90, source_ref }   // segments, ASPs, GM%, opex, tax rate, diluted shares
4. revenue_p10/p50/p90  : number   // USD millions — named with unit
5. eps_p10/p50/p90      : number   // USD per diluted share
6. main_risk_to_upside  : string
7. main_risk_to_downside: string
8. confidence_note      : string   // "am I over- or under-confident vs base rates?" (Halawi's calibration step)
```

- Reasoning **before** numbers (§2.2). Units in every field name (§2.4).
- **`revenue_p50` and `eps_p50` are computed by us from `key_drivers`, not written by the model** where the decomposition supports it (§4.2 schema starvation). Where the model does report them, we recompute and assert <0.5% diff; violations are logged as an eval metric.
- Sampling: **N = 6 as 3 prompt variants × 2 models** (cross-vendor), T = 0.7 for the non-reasoning path, medium effort for the reasoning path.
- Aggregate: **trimmed mean (drop min and max) of each quantile independently** across the 6 samples. Vincentization: average the P10s, average the P50s, average the P90s. Enforce monotonicity after averaging.
- **Widen the interval by a conformal factor** learned on the Q2-CY2026 backtest: compute nonconformity `s_i = max(L_i − y_i, y_i − U_i)` on the calibration set, take the ⌈0.9(n+1)⌉-th order statistic, add it to both bounds. Expect a large correction — the literature says a stated 90% interval is really ~70–75% (§1.7), and this one line is what makes our intervals honest.

**Stage B — Reveal consensus, bounded reconciliation.**
New call, context = Stage A's blind output (numbers + reasoning) + the consensus. Ask: *"Given your prior estimate and the street consensus, is there information in the consensus your analysis missed? Restate your estimate."* Then, in code:
- `final_p50 = w · blind_p50 + (1 − w) · consensus`, with `w` fit on the backtest (start at w = 0.5; Halawi/Silicon-Crowd both find the blend beats either component).
- **Cap the model's own reconciliation movement** at a configured fraction of the blind↔consensus gap (start at 60%) — an explicit ceiling on sycophancy, since prompt-level instructions don't work (§1.1).
- If |blind − consensus| / consensus > threshold (say 8% revenue / 15% EPS), route to an explicit **divergence review** step that must cite specific dossier items justifying the gap, else fall back to the blend. This is Cassi's "crowd adjustment", worth ~0.01 Brier for them.

**Stage C — Deterministic guards (pure TS, no LLM).**
1. Recompute revenue and EPS from drivers; assert <0.5%.
2. Sanity band: reject revenue P50 outside [0.33×, 3×] the TTM-quarter average unless `regime_change` flag set.
3. Monotonicity: P10 < P50 < P90 for every quantity.
4. Unit echo matches the expected string.
5. Round-number diagnostic: log the last significant digit of every P50; a >40% share of {0, 5} across the eval set is a red flag we report honestly.
6. Persist: blind estimate, consensus, reconciled estimate, final blend, and **the anchoring displacement** `(reconciled − blind) / (consensus − blind)` — our headline bias metric, directly comparable to the A-Index literature.

**Arithmetic policy, stated once:** the model never multiplies or divides. It emits drivers with units; TS computes. Any expression the model wants evaluated goes through a `calc()` tool whose call and result are logged. Everything derived is recomputed and diffed.

### Three variants to A/B (this is the eval harness's job)

**V1 — Blind Direct (baseline).** No decomposition. Single strong model, reasoning-then-P10/P50/P90 for revenue and EPS directly, N=6, trimmed mean, conformal widening, no consensus at all. Cheapest, fastest, and the honest control. *Hypothesis: surprisingly hard to beat — cf. the Fermi finding that decomposition depth doesn't correlate with accuracy.*

**V2 — Blind Decomposed + tool arithmetic.** Full driver schema, schema starvation, TS computes revenue and EPS, quantiles derived by Monte-Carlo over per-driver P10/P50/P90 (assume lognormal per driver, 10k draws, take output percentiles) rather than verbalized. *Hypothesis: better calibration and much better explainability; point accuracy roughly a wash. This is the demo version.*

**V3 — Consensus-Anchored Surprise.** Consensus given up front; the model predicts **surprise** (`% deviation from consensus`) with P10/P50/P90 on the deviation, not the level. Deliberately embraces the anchor, since consensus is the single strongest feature in earnings models (NBER w27843) and the scoring metric is vs consensus anyway. *Hypothesis: best raw MAPE, worst independence — it will hug consensus and produce near-zero surprises. Compare its surprise distribution against V1's implied surprise to quantify exactly how much information the blinding buys.*

**Score all three on the same frozen dossiers** over Q2 CY2026 prints (leakage-clean for every model in §6.4). Metrics: MAPE on revenue and EPS; **beat-rate vs consensus**; directional surprise accuracy; **empirical coverage of the nominal 80% interval** (expect ~60–70% before conformal correction, ~80% after); recompute-violation rate; round-digit share; anchoring displacement (V1 vs V3).

### Things to explicitly not do

- Do not put the consensus number anywhere in the Stage-A context and rely on "ignore it" — measured mitigation ceiling is ~10%.
- Do not use a 1M-token dossier because we can. 30–50% degradation, and the win is in curation (−48% error from attending to the right metrics).
- Do not ask for "your estimate and a confidence percentage". Ask for named percentiles.
- Do not let a number appear in the output that wasn't computed in TS from a driver.
- Do not run the estimation at T=0 with N=6 — that's one sample billed six times.
- Do not backtest `claude-opus-5` on Q1 CY2026 or earlier and call it clean.

---

## Source index

Anchoring: arXiv:2505.15392 · arXiv:2412.06593 · arXiv:2607.01240 · doi:10.1016/j.jbef.2024.100971 · zylos.ai 2026-06-29
Digits/round numbers: arXiv:2506.01734 · arXiv:2502.19965 · arXiv:2405.01724
Sycophancy: arXiv:2502.08177
Magnitude/tokenization: arXiv:2410.11781 · arXiv:2602.07812 · arXiv:2603.28258 · arXiv:2406.02864
Arithmetic/tools: arXiv:2211.10435 (PAL) · arXiv:2606.00376 (Deterministic Horizon)
Position/length: arXiv:2307.03172 (Lost in the Middle) · trychroma.com/research/context-rot
Calibration/intervals: arXiv:2510.26995 (FermiEval) · arXiv:2604.15859 (QuantSightBench) · aclanthology.org/2024.trustnlp-1.13
Elicitation: arXiv:2603.02913 (non-autoregressive quantiles) · arXiv:2408.02442 + dylancastillo.co rebuttal replication
Forecasting systems: arXiv:2402.18563 (Halawi) · forecastbench.org · forecastingresearch.substack.com · science.org/doi/10.1126/sciadv.adp1528 · metaculus.com/aib/2026/spring
Sampling: arXiv:2511.00751 · aclanthology.org/2024.findings-emnlp.432 · proceedings.mlr.press/v267/du25f.html
Fermi: arXiv:2504.02671
Finance/earnings: arXiv:2407.17866 (Kim/Muhn/Nikolaev) · arXiv:2412.01069 (Li et al.) · NBER w27843 (van Binsbergen/Han/Lopez-Lira)
Models/APIs: platform.claude.com/docs/en/about-claude/models/overview · platform.claude.com/docs/en/build-with-claude/structured-outputs · developers.openai.com/api/docs/models · developers.openai.com/api/docs/guides/structured-outputs · benchlm.ai
