# Swarm research corpus — built 2026-08-16 (during event)

> Best-practice research for building today's foundational research swarm and its
> consumers. Five files, each self-contained, produced by parallel research agents
> from primary 2025–2026 sources. Read this index first; open at most two files per
> query, and prefer grepping a heading over reading a whole file.

How to navigate (for agents): (1) pick the file whose hook below matches your
question; (2) `rg -n "^## " <file>` to list its sections; (3) read only the matching
section — every section is self-contained; (4) if nothing matches, say so rather
than stretching a near-match. Every file starts with `## Key takeaways` (≤8 bullets)
— read that alone when context is tight.

## Files

- [01-swarm-architecture.md](01-swarm-architecture.md): orchestrator/worker fan-out — when it beats a single agent, delegation contracts, effort scaling, single-writer rule, MAST failure modes, completeness gates
- [02-vectorless-rag.md](02-vectorless-rag.md): structuring a markdown corpus for index+grep retrieval — TOC/llms.txt format, file size limits, greppable headings, frontmatter, navigation prompting
- [03-grounded-extraction.md](03-grounded-extraction.md): extracting numbers with mechanically verifiable quotes — schema-constrained decoding limits, quote-first spans, fuzzy matching, retry-once policy, unit/basis/period traps
- [04-financial-research-agents.md](04-financial-research-agents.md): persona design for earnings forecasting — procedure beats persona labels, evidence-stream ranking, narrative-bias counters, redundancy collapse, coverage-matrix gating
- [05-swarm-ops.md](05-swarm-ops.md): running the swarm — asyncio fan-out patterns, GPT-5.6 prompt caching, local response cache + offline replay, retry policy, verified model pricing, LangSmith without LangChain

## Section map

01-swarm-architecture.md
- When orchestrator/worker fan-out beats a single agent — the 90.2% result and its token-capacity mechanism; ~15x cost
- The delegation contract: what every worker brief must specify — objective / format / tools / boundaries
- Effort scaling rules and topology: fixed versus dynamic fan-out — worker-count rules, bounded rounds
- Context isolation, structured receipts, and the single-writer rule — 1–2k-token receipts into one synthesizer
- Known failure modes and mitigations — MAST's 14 modes, 3 categories, mitigations per category
- Completeness gates, verification loops, and citation integrity — judge rubric as stop condition, clean-context verifier
- Operating a swarm in production — durable execution, tracing, deployment

02-vectorless-rag.md
- Why vectorless retrieval is the 2026 default for small corpora — context rot, just-in-time loading, grep-vs-vector evidence
- Index file design: the TOC that fits in context — llms.txt + PageIndex formats, hook-writing rule
- File granularity, size limits, and naming — 500-line ceiling, `## Contents` blocks, one-level-deep references
- Heading conventions that make grep the retrieval engine — front-loaded entities, synonyms, stable anchors
- Frontmatter metadata and machine-readable blocks — routing YAML, JSONL over tables
- How to prompt the consuming agent to navigate — the bounded read-index → grep → read-section loop
- Measured results and caveats — comparison table, vendor-benchmark caveats

03-grounded-extraction.md
- Schema-constrained decoding: what it guarantees and what it does not — syntax-only guarantee, field-order effects, numeric bounds now supported
- Prompting for verbatim quotes: quote-first, spans not offsets, fuzzy matching — four failure modes to test
- Retrieval-then-extract vs whole-document extraction — lost-in-the-middle, grounding benchmark numbers
- Validation loops: retry once with a structured error, not self-correction — admissible alternatives are the active ingredient
- Unit, basis, and period normalisation traps in financial text — seven traps with deterministic checks
- Evals and benchmarks for extraction fidelity — quote-verifiability rate as the core metric; attribution evals

04-financial-research-agents.md
- Role prompting for financial analysis: procedure beats persona — withdrawn-paper caveat, output contracts over labels
- Evidence streams that actually carry signal for quarterly revenue and EPS — RPO/backlog > guidance-as-biased-prior > revisions > peers > tone/macro
- Countering management narrative bias — guidance walk-down data, three structural counters
- Redundancy and diversity control across personas — measured collapse, six controls
- Claim-level quality: fact-vs-inference tagging and falsifiability — per-claim schema, confidence tiers
- Completeness gating instead of persona counting — metric × dimension matrix, mandatory vs optional cells

05-swarm-ops.md
- Async fan-out: semaphores, TaskGroups, timeouts, partial results — catch-inside-worker rule, SDK timeout gotchas
- GPT-5.6 prompt caching mechanics and prompt ordering — 1.25x write fee, invalidators, static-first ordering
- Local response caching and offline replay for reproducibility — content-addressed keys, rw/off/offline modes
- Retry policy: retry once with the error, or fail fast — transport vs schema classes, do-not-retry list
- Cost and latency budgeting for fan-out — verified gpt-5.6-sol/-terra/-luna pricing, sizing formula
- Observability: LangSmith without LangChain, and OpenTelemetry GenAI — wrap_openai confirmed; skip OTel GenAI today
- Wall-clock optimisation for a live demo — precompute / parallelise / do-not-parallelise lists
