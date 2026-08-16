---
title: Designing LLM research personas for earnings forecasting
description: What the 2024–2026 literature says about analyst-role decomposition, which evidence streams predict quarterly results, and how to stop multi-persona research from being redundant or biased.
tags: [earnings-forecasting, research-agents, personas, multi-agent, evidence-quality, bias, coverage-gating]
date: 2026-08-16
---

## Key takeaways

- Do not cite "GPT-4 beats analysts at earnings direction" as settled: the Kim/Muhn/Nikolaev arXiv paper was **withdrawn on 20 Feb 2025** after a co-author found data inconsistencies while replicating it — use it as a design hypothesis, not evidence.
- Persona strings alone are near-worthless; what helped in that work was the **analyst-style reasoning procedure** (trend → ratio → narrative → directional call), so encode personas as *procedures and source territories*, not as identity flavour text.
- Split each persona by **exclusive question + exclusive source territory**; identical questions across differently-labelled agents is exactly the setup that produces measured representational collapse (mean pairwise cosine 0.888, effective rank 2.17/3.0).
- Weight evidence by *mechanical linkage to the reported number*: contracted balances (RPO/backlog/deferred revenue), guidance ranges, and peer read-across from earlier reporters in the same season outrank tone and sentiment.
- Treat management guidance as a **biased-but-informative prior**: managers deliberately guide to beatable targets, so extract the range and the assumptions, and record the historical beat/miss distribution rather than the midpoint alone.
- Run counterevidence as a **separate pass over accepted evidence**, not as extra bull/bear collector agents — dissent injected as a role reduces conformity even when the dissenter is wrong.
- Tag every claim `fact | inference` with unit, period, publication date and excerpt; atomic-claim decomposition plus numeric recomputation is the standard 2026 mechanism for catching financial hallucination.
- Gate on **per-metric coverage across dimensions** (baseline / guidance / driver bridge / external corroboration / street + counterevidence), not on persona count — role-grounded rubric coverage beat prompt-only coverage by ~21 points on specialised roles.

## Role prompting for financial analysis: procedure beats persona

The headline result everyone quotes — GPT-4 with analyst-mimicking chain-of-thought predicting earnings-change direction better than human analysts, with tradeable alpha — comes from Kim, Muhn and Nikolaev (arXiv:2407.17866, v1 25 Jul 2024). That preprint was **withdrawn on 20 Feb 2025**: a co-author identified inconsistencies in the data and analyses while attempting to replicate the working paper's results. The abstract itself never carried the widely-repeated "60.35% vs analysts" figure. Treat the whole claim as unverified.

What survives is the *method*, a procedure rather than a persona: anonymise the statements, force a structured pass (trends → ratios → narrative → directional call), and demand the reasoning before the answer. Nothing in it depends on telling the model it is "a seasoned Wall Street analyst".

The persona-prompting literature is consistent about this. Zheng et al. ("When 'A Helpful Assistant' Is Not Really Helpful", arXiv:2311.10054, updated through 2024) tested 162 roles across 4 LLM families and 2,410 factual questions and found adding a persona to the system prompt does **not** reliably improve performance over no persona. The 2026 PRISM work (arXiv:2603.18507) sharpens it: expert personas improve alignment/style adherence but *damage* task accuracy, which is why they route personas by intent rather than applying them universally.

Design implication for the swarm: a persona should be a **contract** — an exclusive question, an allowed source list, an output schema, and a reasoning procedure. The identity label is UI, not capability. Role-grounded structure does pay off when it defines *deliverable content*: FinProBench (arXiv:2608.04077, 4 Aug 2026) built rubrics from 1,723 professional deliverables across 57 financial occupations and found role-grounded rubric coverage beat prompt-only coverage 99.1% vs 78.0% on prior-sparse specialised roles (vs 90.7% vs 89.2% on conventional roles) — the gain comes from specifying what a role must produce.

## Evidence streams that actually carry signal for quarterly revenue and EPS

Rank evidence by how mechanically it connects to the number being reported.

**Tier 1 — contracted forward balances.** RPO, backlog and deferred revenue are contracted revenue not yet recognised; issuers describe RPO as a leading indicator of revenue while explicitly warning it is *not* proportional to future growth, given seasonality, renewal timing, contract duration and FX (Box 10-Q/10-K, 2019–2021). Use them for floor and direction, not as a multiplier, and pull the issuer's caveat paragraph and current/non-current split.

**Tier 1 — management guidance for the target period.** Explicit ranges, the assumptions behind them, and any superseded version. See the bias section below.

**Tier 2 — street expectations and revision momentum.** Consensus is the scoring baseline, so it is evidence about the *question*, not about the company. Revision momentum has long-documented predictive content: prices underreact to analyst forecast revisions and drift in the revision direction, and revisions reinforce surprises when the two signals agree. Capture consensus with a snapshot date, dispersion, high/low, analyst count, and revision direction over the last 30/90 days — a stale consensus is the single most common silent error.

**Tier 2 — peer read-across inside the same reporting season.** Intra-industry information transfer is well established: an early reporter's announcement informs peers' expected results, and the effect depends on whether the later firm's earnings are consistent or contradictory with the early announcer's surprise (*Competitive earnings news and PEAD*, IRFA 2017; EFMA 2021 on announcement timing). Rule: enumerate suppliers, customers and competitors who *already reported an overlapping period*, and record the comparable KPI, not the headline beat.

**Tier 3 — macro/nowcast series and management tone.** Corroboration and current-quarter delta only. Agentic nowcasting (arXiv:2601.11958, Jan 2026) reports narrative streams adding value over quantitative signals alone — but it targets *returns*, not reported EPS, so do not import its weighting.

## Countering management narrative bias

Management commentary is the highest-density evidence source and the most strategically shaped one, so extract it and then attack it.

**Guidance is deliberately beatable.** The walk-down literature (Richardson, Teoh & Wysocki) documents managers selectively guiding estimates down so the firm can beat them. Survey evidence from Call, Hribar, Skinner & Volant (*Corporate managers' perspectives on forward-looking guidance*, JAE 2024) finds 79% of managers say meeting their most recent guidance is very important — higher than the 62% for the analyst consensus — and that managers issue conservative guidance to buffer shortfalls and encourage beatable analyst forecasts. The share of firms missing targets pre-guidance but meeting post-revision targets rose from 5.5% (1995) to 20.0% (2014). Operational consequence: never take the guidance midpoint as an unbiased estimate. Record (a) the range, (b) the stated assumptions, (c) the firm's own history of guiding vs actual over the last 8–12 quarters, and (d) whether guidance was revised intra-quarter.

**Tone is informative and manipulable.** Call tone predicts abnormal returns and drift, but optimistic tone also functions as impression management: optimistic call tone is positively associated with stock price *crash* risk (J. Bus. Ethics 2019), and within-call "tone distance" between managers predicts volatility and inversely relates to future growth prospects (*Financial Review*, 2025). Use tone as a flag for where to dig, never as a claim.

**Cheap structural counters.** (1) A counterevidence pass over already-accepted evidence rather than extra bull/bear collectors — a devil's-advocate role measurably reduces conformity *even when the dissenter is wrong* (arXiv:2410.12428). (2) Context-aware retrieval assembling both local and global thematic evidence per claim, as in CARAG (Preprints 202501.0676, Jan 2025), plus conflict-driven summarisation that surfaces contradictions instead of averaging them (arXiv:2507.01281). (3) Require every management-sourced claim to name one non-management source that could confirm or contradict it.

## Redundancy and diversity control across personas

Multi-persona swarms fail in a specific, measured way. Patel (*Representational Collapse in Multi-Agent LLM Committees*, arXiv:2604.03809, Apr 2026) measured three-agent committees over 100 questions: mean pairwise cosine similarity 0.888 and effective rank 2.17 out of 3.0 — agents produced near-identical reasoning *despite different role prompts* — and proposed weighting aggregation by representational divergence. Companion work on diversity collapse (arXiv:2604.18005, Apr 2026) adds three structural findings: group-size scaling gives diminishing returns, dense/fully-connected communication accelerates premature convergence, and authority-framed agents suppress diversity relative to peer-framed ones.

Controls that follow directly:

1. **Exclusive questions and exclusive source territories.** Redundancy is designed in when two personas can legitimately answer the same question. Give each lens a question no other lens may answer and a source list no other lens may read first.
2. **Sparse topology.** Run foundational lenses in isolation over their own sources; do not let them read each other's drafts. Merge once, at the orchestrator. Broadcast only the shared target definition and the consensus snapshot.
3. **No forecast values from collectors.** If ten lenses each emit a number, aggregation becomes a popularity vote over correlated priors. Collectors emit claims, direction and drivers; a single downstream pass produces the number.
4. **Anonymise identity in any debate/merge step.** Identity signals skew multi-agent debate; anonymising participants reduces that bias (arXiv:2510.07517, v5 2026).
5. **Deduplicate on claim content, not wording.** Key claims by (metric, period, direction, source URL) and collapse duplicates, keeping the earliest-dated primary source.
6. **Prefer heterogeneity where it is cheap** — different models, temperatures or retrieval slices for lenses that must overlap.

## Claim-level quality: fact-vs-inference tagging and falsifiability

The 2026 practice for financial LLM output is atomic-claim verification. FinGround (arXiv:2604.23588) decomposes generated text into atomic claims, **recomputes numerical claims**, and aligns each to evidence before issuing a verdict; VeriFin (arXiv:2608.10213, Aug 2026) classifies financial atomic claims into numerical, temporal, entity-attribute, comparative, regulatory and computational types and verifies each by type. A documented failure mode: over-aggressive decomposition strips context, so keep each claim decontextualised *enough to verify* but carrying its period, unit and entity.

Minimum per-claim schema for an earnings dossier:

- `metric` (exact, with GAAP/adjusted flag and fiscal period)
- `claim_type`: `fact` (stated in a dated source) vs `inference` (derived) — inferences must name the facts they rest on
- `value`, `unit`, `period` for anything numeric
- `direction` and `causal_driver`
- `source_url`, `publication_date`, `information_cutoff`, verbatim `excerpt`
- `counterevidence`: the strongest contradicting item found, or explicit `none_found`
- `falsifier`: the observation that would overturn the claim
- `delta`: what changed vs the prior quarter or prior consensus snapshot

Two practical notes. Extraction from calls is genuinely harder than from filings: models trained on SEC filings degrade on conversational transcripts, and a 2026 industry-track system doing open-ended KPI extraction from calls reached **79.7% precision under human evaluation** (arXiv:2605.03147 / ACL 2026 Industry) — so route filing-derived and call-derived numbers through different confidence tiers. Second, sycophancy is a live risk in agentic financial applications: models measurably shift analysis toward stated user preferences (*The Price of Agreement*, arXiv:2604.24668, Apr 2026), so never pass the desired conclusion, the current working forecast, or another agent's stance into a collector's prompt.

## Completeness gating instead of persona counting

"Did we run enough personas?" is unanswerable; "does every metric have coverage on every dimension?" is checkable. Gate each target metric on five dimensions: **historical baseline and definition / management guidance / operating-driver bridge / independent external corroboration / street expectation plus counterevidence.** Any empty cell forces either a targeted follow-up task or an explicit `unavailable` marker with a reason. This mirrors how deep-research evaluation converged in 2026: ResearchRubrics (arXiv:2511.07685) uses 2,593 expert-written criteria scoring completeness, grounding, reasoning soundness and source usage, with a **mandatory vs optional** split so systems can be gated on minimum viable coverage rather than an average score; DeepResearch Bench II (arXiv:2601.08536, Feb 2026) uses checklist-based coverage plus citation traceability.

Make the gate cheap and mechanical:

- Build the coverage matrix as `metric × dimension` and fill it from claim metadata, not from agent self-reports.
- Mark **mandatory** cells (baseline, guidance, street) versus **optional** (external corroboration when no third-party data exists). Fail the run on missing mandatory cells; annotate optional gaps.
- Add staleness checks as gate conditions: consensus snapshot date, guidance-supersession check, and "any peer in the comparable set reported after our latest evidence".
- Add a contradiction check: at least one dimension per metric must contain an item that disagrees with management's framing, or the dossier is flagged as one-sided.
- Report coverage in the output. A dossier that says "driver bridge unavailable: company does not disclose segment volumes" is more trustworthy, and more useful to the downstream forecaster, than one that silently omits it.

## Sources

- Kim, Muhn, Nikolaev — Financial Statement Analysis with LLMs (withdrawn 20 Feb 2025): https://arxiv.org/abs/2407.17866
- SUERF policy brief on the above: https://www.suerf.org/wp-content/uploads/2024/10/SUERF-Policy-Brief-1008_Kim-et-al.pdf
- When "A Helpful Assistant" Is Not Really Helpful (162 personas, 2,410 questions): https://arxiv.org/html/2311.10054v3
- Expert Personas Improve LLM Alignment but Damage Accuracy (PRISM, 2026): https://arxiv.org/abs/2603.18507
- FinProBench: role-grounded rubrics from professional deliverables (Aug 2026): https://arxiv.org/html/2608.04077
- Representational Collapse in Multi-Agent LLM Committees (Apr 2026): https://arxiv.org/pdf/2604.03809
- Diversity Collapse in Multi-Agent LLM Systems (Apr 2026): https://arxiv.org/abs/2604.18005
- When Identity Skews Debate: anonymization for bias-reduced multi-agent reasoning: https://arxiv.org/pdf/2510.07517
- Conformity in Large Language Models (devil's-advocate role): https://arxiv.org/pdf/2410.12428
- The Price of Agreement: LLM sycophancy in agentic financial applications (Apr 2026): https://arxiv.org/pdf/2604.24668
- Call, Hribar, Skinner, Volant — Corporate managers' perspectives on forward-looking guidance (JAE 2024): https://mitsloan.mit.edu/sites/default/files/inline-files/Call_Hribar_Skinner_Volant.pdf
- The Walk-Down to Beatable Analyst Forecasts (Richardson, Teoh, Wysocki): https://www.researchgate.net/publication/228139693_The_Walk-Down_to_Beatable_Analyst_Forecasts_The_Role_of_Equity_Issuance_and_Insider_Trading_Incentives
- Tone Distance: Managerial Tone Divergence and Market Reaction (Financial Review, 2025): https://onlinelibrary.wiley.com/doi/10.1111/fire.70002
- Earnings conference call tone and stock price crash risk: https://link.springer.com/article/10.1007/s10551-019-04326-1
- Competitive earnings news and post-earnings announcement drift (IRFA 2017): https://www.sciencedirect.com/science/article/abs/pii/S1057521917300212
- Earnings Announcement Timing and Intra-Industry Information Transfers (EFMA): https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2021-Leeds/papers/EFMA%202020_stage-1301_question-Full%20Paper_id-94.pdf
- The Value of Analyst Forecast Revisions: https://escholarship.org/content/qt2r7980f3/qt2r7980f3_noSplash_c002fc5c3b5de2401d705fadd922a1f3.pdf
- RPO/backlog/deferred revenue definition and caveats (Box 10-K FY2021): https://www.sec.gov/Archives/edgar/data/1372612/000156459021014377/box-10k_20210131.htm
- CARAG: Context-Aware Retrieval framework for fact verification (Jan 2025): https://www.preprints.org/manuscript/202501.0676
- Rethinking All Evidence: conflict-driven summarization for trustworthy RAG: https://arxiv.org/pdf/2507.01281
- FinGround: detecting and grounding financial hallucinations via atomic claim verification: https://arxiv.org/pdf/2604.23588
- VeriFin: neurosymbolic verification of LLM-generated financial claims (Aug 2026): https://arxiv.org/html/2608.10213
- KPI extraction from earnings calls, 79.7% precision (ACL 2026 Industry): https://arxiv.org/abs/2605.03147
- ResearchRubrics: prompts and rubrics for evaluating deep research agents: https://arxiv.org/html/2511.07685v1
- DeepResearch Bench II (Feb 2026): https://arxiv.org/pdf/2601.08536
- FinCall-Surprise: multi-modal benchmark for earnings surprise prediction (Oct 2025): https://arxiv.org/pdf/2510.03965
- Autonomous Market Intelligence: Agentic AI Nowcasting (Jan 2026): https://arxiv.org/pdf/2601.11958
- Earnings2Insights multi-agent collaboration (FinNLP 2025): https://aclanthology.org/2025.finnlp-2.26.pdf
