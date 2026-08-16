---
title: Grounded, Citation-Faithful Numeric Extraction from Filings and Transcripts
description: Current (2025–2026) practices for extracting financial figures with mechanically verifiable verbatim quote citations.
tags:
  - grounded-extraction
  - structured-outputs
  - citations
  - financial-nlp
  - validation
  - evals
date: 2026-08-16
---

## Key takeaways

- Treat the schema as a syntax guarantee only: constrained decoding cannot make a quote real, so every extracted `quote` must be re-matched against the source text by your own code before the fact is accepted.
- Ask the model for the verbatim span text, not character offsets — models are measurably worse at computing indices than at copying text (TimeStampEval, Nov 2025); compute offsets yourself by searching for the returned span.
- Validate quotes with normalised fuzzy n-gram matching (collapse whitespace, unicode dashes/quotes, non-breaking spaces) rather than raw `str.find`, then reject anything below threshold; this is exactly the anchor used in the 601k-tag SEC 8-K grounded-extraction system (Jul 2026).
- Order schema fields so `quote` (and any reasoning) is emitted before the parsed `value` — required properties are generated in order, and answer-first schemas force early commitment and cost 10–30% on reasoning-heavy tasks.
- Split extraction from interpretation: stage 1 copies quote + raw literal figure; stage 2 normalises unit, GAAP basis, and period. Grading quality in a dedicated second pass is what made scores calibrated in the 8-K study.
- Carry `metric, value, unit, period, qualifier(GAAP/adjusted/guidance)` as separate required fields — a KPI/guidance system with those fields plus rule injection hit 91.2% extraction F1 and a 2.3% unit-error rate (May 2025).
- Retry at most once, and only with a *structured* error (what failed, observed value, admissible alternatives); blind re-asking adds nothing because LLMs cannot self-correct without an external signal, and later retries tend to return subtly-wrong output that passes validation.
- Retrieve-then-extract over targeted chunks beats stuffing the whole 10-K: long-context loses ~30% accuracy when the fact sits mid-window, and ungrounded chatbots score 11–64% on single-figure retrieval vs 94.2% when bound to a structured source.

## Schema-constrained decoding: what it guarantees and what it does not

OpenAI Structured Outputs (strict mode; JSON mode is legacy) now supports more than it did at launch. Numeric keywords `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf` are supported, as are string `pattern` and `format`. Unsupported: `allOf`, `not`, `if/then/else`, `dependentRequired`. Limits: nesting depth 10, 5,000 total properties, 1,000 enum values, 120k-char schema, root must be an object (no root `anyOf`). Fine-tuned models lose string and number constraints. Recursion via `$ref: "#"` and `$defs` works.

Gotchas that bite numeric extraction specifically:

- **All fields are required.** Optionality must be modelled as `["number","null"]`. A nullable `value` is essential — you want "not disclosed" to be expressible, otherwise the model invents a number to satisfy the schema.
- **Field order is generation order.** Put `quote`, then `raw_text_value`, then the parsed `value`/`unit`. Answer-first schemas commit the model before it has looked at evidence; Tam et al. found strict format constraints cost 10–30% on reasoning tasks, and the standard mitigation is reason-then-format (free generation, then a cheap formatting call, or a reasoning field placed first).
- **Refusals bypass the schema.** A `refusal` object is returned instead of your JSON; handle it as a first-class error, not a parse failure.
- **Schema compile latency** on first use per schema, with a ~24h grammar cache invalidated by any schema edit — do not build schemas per document.
- **`pattern` cannot express "this string appears in the source."** No schema feature can. Grammar constraints guarantee well-formedness, never truth; OpenAI's own docs note hallucination remains possible.

Practical rule: schema for shape (enums for `unit`, `basis`, `period_type`; `null` for absent), post-validator for everything semantic.

## Prompting for verbatim quotes: quote-first, spans not offsets, fuzzy matching

The pattern with the best current evidence is **quote-first / extract-then-abstract**: the model must emit the supporting sentence copied verbatim *before* it emits any parsed number, and the parsed number must be derivable from that sentence alone.

TimeStampEval (arXiv:2511.11594, 18 Nov 2025) found that asking models to return the actual text span is substantially more reliable than asking them to compute character offsets — offset arithmetic is a weak point, span copying is not. Locate offsets yourself by searching the returned span.

The same paper (and the SEC 8-K system below) converge on **fuzzy matching as the verification primitive**. Strict `==` fails constantly on benign variation: whitespace collapsing, `’` vs `'`, en/em dashes, non-breaking spaces, ligatures, hyphenation across line breaks in PDF text. Normalise both sides (NFKC, collapse whitespace, unify quote/dash classes, casefold), accept n-gram similarity above a threshold, and log both forms.

Documented failure modes to test for:

- **Paraphrase drift** — summarising instead of copying ("revenue grew sharply" for "revenue increased 14% to $3.2 billion").
- **Quote splicing** — joining non-adjacent fragments with "…" into a string that never appears contiguously. Require one contiguous span.
- **Truncation at the number** — quoting the clause but dropping the "on a non-GAAP basis" tail that sets the basis. Require the quote to contain the numeral it justifies.
- **Unit drift** — the parsed value rescales relative to the quote (3.2 billion → `value: 3.2, unit: millions`). Assert `quote` contains the digits of `raw_text_value`.

Anthropic's Citations API (Jan 2025) does this at the API layer: it returns character-level offsets, document indices, and source excerpts, guaranteed rather than prompted. Anthropic's benchmarks reported up to 15% better recall accuracy vs prompt-engineered citations; Endex reported source hallucination/formatting issues going from 10% to 0%. If you are on Claude, prefer the built-in mechanism to a hand-rolled quote field.

## Retrieval-then-extract vs whole-document extraction

For filings, retrieve-then-extract is the safer default, with whole-doc reserved for short documents or a final reconciliation pass.

The measured case against naive long-context: 10–25% positional retrieval variance at 128K context, and roughly 30%+ accuracy loss when the relevant content sits mid-window (RoPE decay / "lost in the middle"), persisting across 2026 benchmarks. A 2025 Unstructured study found RAG more complete *and* cheaper than a 1M-token context on financial filings. DocFinQA (Reddy et al., 2024) exists precisely because FinQA-style snippets are unrealistic — real filings run 150+ pages.

The strongest grounding evidence is Daloopa's open benchmark on single-figure retrieval from official filings (correct currency, unit, and period required): Claude Opus 4.1 bound to a structured source via MCP scored **94.2% exact match (97.2% at ±1% tolerance)**, versus ChatGPT 63.8%, Grok 4 57.4%, Perplexity Finance 33.8%, standalone Claude 30.6%, Gemini 2.5 Pro 11.2%. Its top failure modes are ambiguous question interpretation, rounding/formatting, fiscal-vs-calendar confusion, and period shifts — i.e. mostly *normalisation*, not reading.

FinGround (arXiv:2604.23588, 26 Apr 2026) is a useful architecture reference: complexity-routed hybrid retrieval (BM25 + E5-large + structure-aware chunking that preserves row/column relationships), atomic-claim verification, then grounded regeneration with table-cell citations ("Table 3, Row: Operating Income, Col: FY2024"). It reports 91.4% detection F1 on FinHalu, a 3.6% end-to-end hallucination rate on FinQA (78% reduction vs a GPT-4o baseline), and 90.2% F1 on computational claims via formula reconstruction. Critically, it measured a **68% additional hallucination reduction after controlling for retrieval quality** — verification contributes independently of better retrieval.

Practical shape: chunk with table structure preserved, retrieve a small candidate set, extract per-chunk with quotes, then dedupe/reconcile across chunks. Never chunk mid-table.

## Validation loops: retry once with a structured error, not self-correction

The literature is unambiguous that intrinsic self-correction does not work. Huang et al. ("Large Language Models Cannot Self-Correct Reasoning Yet", ICLR 2024) and the TACL critical survey ("When Can LLMs Actually Correct Their Own Mistakes?", 2024) both conclude models cannot reliably judge their own prior output without an external signal; performance often degrades when you simply ask "are you sure?". The corollary is positive: with *valid external feedback*, refinement works well.

Your external signal is free here — the quote either matches the source or it does not, and the number either parses out of the quote or it does not. That is a deterministic verifier, which is the strongest kind.

Feedback content matters more than format. In an agent repair study (arXiv:2607.14167, 15 Jul 2026), typed structured feedback lifted success by 44 and 42 percentage points over raw diagnostics for two models — but prose carrying *the same repair content* performed within 0–2 points. The active ingredient was **admissible alternatives**: telling the model what is valid at that point. Feedback without them barely helped. A retry message should state which field failed, the observed value, why it failed, and the candidate spans/values that would be acceptable.

Budget: retries help only while they deliver new information. The same study saw raw-diagnostic loops plateau after ~4 calls while informative feedback kept improving to 6–8. For a hackathon-scale extraction pipeline, **one informative retry, then reject to a null/`unverified` outcome** is the right trade. The specific danger of deeper loops is documented: the retry that "succeeds" on attempt two or three often returns output that passes validation but is subtly wrong — a silent data-poisoning path that logs as success. Emit a `verification_status` field and let downstream consumers drop unverified facts rather than pretending they were extracted.

## Unit, basis, and period normalisation traps in financial text

This is where most real errors live — the Daloopa failure taxonomy is dominated by it, not by reading comprehension. Carry these as separate, required, enum-constrained fields rather than baking them into one string:

`metric`; `value` plus `raw_text_value` (literal digits as written); `unit`/`scale` (absolute, thousands, millions, billions, percent, per-share); `currency`; `period` and `period_type` (Q / FY / YTD / TTM, plus fiscal-vs-calendar); `basis` (GAAP / non-GAAP / adjusted / pro-forma / constant-currency); `nature` (actual / guidance / prior-year comparative / consensus).

The multi-agent KPI-and-guidance system (arXiv:2505.19197, LinqAlpha + Univ. of Florida, May 2025) uses almost this shape — Metric, Value, Unit, Period, Qualifier — with range normalisation, GAAP disambiguation, and period anchoring. With domain-rule injection and QA consistency checks it reports 91.2% extraction F1, 95.3% metric precision, 2.3% unit error rate. Its three named failure modes are the traps: **guidance misclassified as actual, adjusted metrics treated as GAAP, values assigned to the wrong fiscal period.**

Specific traps to assert against:

- **Scale inheritance and mixed scales.** "(in millions, except per share data)" sits far from the cell — header text must travel with the chunk. Prose may say "$3.2 billion" where the adjacent table says 3,200; reconcile, do not average.
- **Fiscal calendars.** Apple's FY2026 Q1 ends December 2025; NVIDIA's FY ends in January. Never infer calendar quarters from fiscal labels.
- **YTD vs quarterly.** Nine-month figures in a Q3 10-Q are routinely captured as quarterly. Require the quote to contain the period phrase.
- **Guidance ranges.** Store `low`, `high`, `midpoint` separately; "at least", "approximately", "up to" are one-sided bounds, not ranges.
- **Sign, parentheses, and comparatives.** `(1,234)` is negative; basis points vs percent for margin changes; restated prior-period figures often share a sentence with the current one.

Encode each as a deterministic check (unit in quote, period phrase in quote, sign consistency, value-vs-quote digit match). Rule-based validation layered under LLM output is where production finance pipelines converge.

## Evals and benchmarks for extraction fidelity

- **FinQA** (EMNLP 2021): 8,281 expert-annotated QA pairs over S&P 500 reports with gold supporting facts and executable numeric programs. The gold supporting facts make it usable as a *citation* eval, not just an answer eval.
- **DocFinQA** (2024): the same task over full 150+ page documents — the realistic retrieval-then-extract setting. **TAT-QA** (16,552 pairs) and **FinanceBench** (150 curated) complete the trio used by FinGround.
- **FinTagging** (arXiv:2505.20650): numeric fact extraction from text *and* tables plus XBRL taxonomy alignment — the closest public analogue to "pull the figure and label it correctly", and it isolates the text-vs-table gap.
- **FinHalu** (in FinGround, Apr 2026): 1,200 expert-annotated hallucination triples, κ=0.83; a four-week pilot with 24 analysts over 1,847 queries measured 6.1% false positives, 3.8% false negatives.
- **SEC 8-K grounded event extraction** (arXiv:2607.08346, 9 Jul 2026): 119-type taxonomy, 292,984 filings (2022–2026), 601,088 quote-anchored tags, each anchored via **fuzzy n-gram validation** with a **second pass** re-grading quote quality. Precision tracks the quality score from 12% to 96%, unsupported tags falling from 8% to near zero at the top band — and the ablation shows the score is calibrated only when assigned in a dedicated second pass.
- **Attribution evals**: ALCE (2023) scores citation recall/precision via NLI entailment; AttributionBench shows fine-tuned GPT-3.5 at only ~80% macro-F1. "Cited but Not Verified" (arXiv:2605.06635, 7 May 2026) benchmarked 14 models: link validity 94–100%, topical relevance 80–96%, but **factual accuracy only 39–77%** for frontier models (24% open-source), dropping ~42% as tool-call depth grew from 2 to 150 while surface metrics held above 92%.

Minimum viable eval here: N hand-labelled facts with (value, unit, period, basis, gold quote). Report exact-value match, ±1% match, unit/period/basis accuracy separately, and **quote-verifiability rate** — the fraction of returned quotes that fuzzy-match the source. That last number is what distinguishes this system from a chatbot.

## Sources

- OpenAI, Structured model outputs guide — https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI, Introducing Structured Outputs in the API — https://openai.com/index/introducing-structured-outputs-in-the-api/
- Azure OpenAI structured outputs (Microsoft Learn) — https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs
- JSONSchemaBench (arXiv:2501.10868) — https://arxiv.org/pdf/2501.10868
- When Correct Isn't Usable: Structured Output Reliability in SLMs (arXiv:2605.02363) — https://arxiv.org/html/2605.02363v1
- Anthropic, Introducing Citations on the Anthropic API (Jan 2025) — https://www.anthropic.com/news/introducing-citations-api
- Simon Willison on the Citations API — https://simonwillison.net/2025/Jan/24/anthropics-new-citations-api/
- TimeStampEval (arXiv:2511.11594, Nov 2025) — https://arxiv.org/pdf/2511.11594
- Grounded Event Extraction from SEC 8-K Filings (arXiv:2607.08346, Jul 2026) — https://arxiv.org/abs/2607.08346
- FinGround: Detecting and Grounding Financial Hallucinations (arXiv:2604.23588, Apr 2026) — https://arxiv.org/html/2604.23588v1
- Structuring the Unstructured: Multi-Agent KPI & Guidance Extraction (arXiv:2505.19197, May 2025) — https://arxiv.org/html/2505.19197v2
- FinTagging (arXiv:2505.20650) — https://arxiv.org/pdf/2505.20650
- DocFinQA (arXiv:2401.06915) — https://arxiv.org/html/2401.06915v3
- FinQA overview — https://beancount.io/bean-labs/research-logs/2026/05/13/finqa-numerical-reasoning-financial-data
- Daloopa open benchmark on LLM accuracy in financial retrieval — https://daloopa.com/benchmark/an-open-source-benchmark-to-measure-llm-accuracy-in-financial-retrieval
- Large Language Models Cannot Self-Correct Reasoning Yet (ICLR 2024) — https://openreview.net/pdf?id=IkmD3fKBPQ
- When Can LLMs Actually Correct Their Own Mistakes? (TACL) — https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00713/125177/
- Structured Feedback Improves Repair in an LLM Agent Loop (arXiv:2607.14167, Jul 2026) — https://arxiv.org/html/2607.14167v1
- The LLM Retry Loop That Looks Like Progress and Does Nothing — https://pithycyborg.substack.com/p/the-llm-retry-loop-that-looks-like
- Cited but Not Verified (arXiv:2605.06635, May 2026) — https://arxiv.org/html/2605.06635v1
- ALCE benchmark overview — https://www.emergentmind.com/papers/2305.14627
- RAG vs long context: what the 2026 data shows — https://usewire.io/blog/long-context-vs-rag-what-the-data-shows/
- Long Context LLMs and Lost in the Middle (2026) — https://qubittool.com/blog/long-context-lost-in-the-middle
- LlamaExtract: citations and reasoning for extracted data — https://www.llamaindex.ai/blog/get-citations-and-reasoning-for-extracted-data-in-llamaextract
