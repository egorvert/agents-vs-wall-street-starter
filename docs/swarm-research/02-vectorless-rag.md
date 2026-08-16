---
title: Vectorless RAG — navigational retrieval over a markdown corpus
description: How to structure a 10–50 file markdown corpus so an LLM agent retrieves from it by reading an index, grepping, and opening one section — no embeddings, no vector DB.
tags: [vectorless-rag, agentic-search, context-engineering, corpus-design, llms-txt, pageindex, grep, progressive-disclosure]
date: 2026-08-16
---

## Key takeaways

- Build one `INDEX.md` at the corpus root: an H1, a one-blockquote scope line, then H2 groups listing every file as `[path](path): one-line hook` — this is the only file the agent loads unconditionally.
- Cap the index at roughly 1,500 tokens so it always fits in context; push all detail behind links, never inline it.
- Keep each content file 100–400 lines (one topic per file); split at 500 lines, which is Anthropic's published ceiling for a progressively-disclosed markdown file.
- Give every file with more than ~100 lines its own `## Contents` list of its H2s, so a `head -40` preview still reveals the whole file's scope.
- Write headings as literal search targets — include the exact entity names, tickers, error codes, and API names an agent would grep for, not clever titles.
- Make every `##` section self-contained: restate the subject by name instead of writing "as mentioned above," because sections get read in isolation.
- Put durable routing metadata in YAML frontmatter (`title`, `description`, `tags`, `entities`, `date`) and keep numeric/tabular facts in fenced `jsonl` blocks rather than prose.
- Prompt the consuming agent with a fixed loop — read index → grep for the term → read only the matched section → stop when sufficient — and require it to cite `file#heading`.

## Why vectorless retrieval is the 2026 default for small corpora

Anthropic named the pattern "just-in-time context loading" in *Effective context engineering for AI agents* (29 Sep 2025): rather than pre-processing all data, agents "maintain lightweight identifiers (file paths, stored queries, web links, etc.) and use these references to dynamically load data into context at runtime using tools." Claude Code is the reference implementation — `CLAUDE.md` is dropped in up front, while `glob` and `grep` retrieve files on demand, "effectively bypassing the issues of stale indexing and complex syntax trees."

The same post explains why this matters at all: context rot. Transformer attention is an `n²` budget, so recall degrades as the window fills. The goal is "the smallest possible set of high-signal tokens." A vector DB does not help with that — it returns k chunks whether or not they are relevant, and it cannot say "nothing here."

Evidence, not just doctrine. PwC's *Is Grep All You Need? How Agent Harnesses Reshape Agentic Search* (arXiv:2605.15184, 14 May 2026) compared grep against vector retrieval on a 116-question LongMemEval subset across a custom harness and three provider CLIs (Claude Code, Codex, Gemini CLI). Grep "generally yields higher accuracy than vector retrieval," but the paper's real finding is that the harness and how tool output is presented (inline vs. written to a file the agent re-reads) move scores as much as the retriever does. Fudan's LogicalRAG (arXiv:2605.27123) reaches parity with a strong agentic hybrid baseline using only an inverted index, at much lower build and serving cost, and with fewer unsupported answers — because a lexical miss is an explicit failure signal, whereas embeddings always return *something*.

For a 10–50 file corpus the calculus is decisive: the whole index fits in context, so there is nothing for an ANN search to accelerate.

## Index file design: the TOC that fits in context

Two conventions to copy, both battle-tested.

**llms.txt (Jeremy Howard; v1 Sep 2024, v2 current).** The format is deliberately rigid so parsers *and* models can read it: an optional BOM; an H1 with the project name (the only required element); a blockquote summary; free markdown paragraphs (no headings); then zero or more H2 sections containing "file lists" — markdown lists where each entry is `[name](url)` optionally followed by `:` and notes. A trailing `## Optional` section is the convention for links an agent may skip when context is tight. The spec's stated goal: "The file itself stays small enough to fit in context. The detail lives behind the links."

**PageIndex (VectifyAI, 19 Sep 2025).** Same idea, JSON-shaped. Documents become a tree of nodes with `node_id`, `title`, `summary`, and `sub_nodes`; the tree is placed in the prompt as an *in-context index* the model reasons over — "deciding where to look next, not merely what looks similar." Retrieval is a loop: read the ToC, select a section, extract, ask "is this sufficient?", else return to the ToC.

Concretely, for our corpus:

```markdown
# Agents vs Wall Street — knowledge corpus

> Market microstructure, instrument definitions, and persona briefs for the
> trading-agent swarm. Read this file first; open at most two others per query.

## Instruments
- [instruments/equities.md](instruments/equities.md): tickers, lot sizes, halt rules
- [instruments/options.md](instruments/options.md): greeks, expiry conventions, assignment

## Optional
- [appendix/glossary.md](appendix/glossary.md): term definitions, only if a term is unrecognised
```

The one-line hook after the colon does the routing work. Write it as a *disambiguator* against sibling files, not a summary of the file — "halt rules" earns its tokens; "information about equities" does not.

## File granularity, size limits, and naming

Anthropic's skill-authoring guidance is the most specific published numbers on this and transfers directly to any agent-read markdown corpus:

- **Under 500 lines** per progressively-disclosed file; "split content into separate files when approaching this limit."
- **Table of contents for files over 100 lines** — because "Claude may partially read files… might use commands like `head -100` to preview content rather than reading entire files." A `## Contents` list at the top means a partial read still reveals the full scope.
- **References one level deep.** Index → file. Never index → file → file: "Claude may partially read files when they're referenced from other referenced files," producing incomplete information.
- **Descriptive filenames.** `form_validation_rules.md`, not `doc2.md`; `reference/finance.md`, not `docs/file1.md`.
- **Organize directories by domain**, so a question about sales never loads finance context.

Practical targets for 10–50 markdown files: 100–400 lines each, one topic per file, 3–8 H2 sections per file. If a file needs two `## Contents` groups that share no vocabulary, it is two files.

Anthropic also notes the payoff: "No context penalty for large files. Reference files, data, or documentation don't consume context tokens until actually read." That inverts the usual instinct — it is safe to bundle a comprehensive `glossary.md`, as long as nothing forces the agent to read it.

Directory naming is itself a signal. Anthropic: "the presence of a file named `test_utils.py` in a `tests` folder implies a different purpose than a file with the same name located in `src/core_logic/`." Folder hierarchies, naming conventions, and timestamps are free routing metadata.

## Heading conventions that make grep the retrieval engine

Grep only finds what you literally wrote. Headings therefore have one job: contain the exact strings an agent will search for.

- **Front-load the entity.** `## AAPL — earnings calendar and blackout windows`, not `## When we can't trade`. The agent greps `AAPL`, `earnings`, `blackout`.
- **Spell out synonyms once, in the heading or the first line.** `## Position sizing (risk budget, notional cap)` catches three query vocabularies with one heading.
- **Keep the hierarchy predictable.** Fern's LLM-friendly docs guidance (Mar 2026): H2 for major topics, H3 for subtopics, consistently — "predictable patterns help retrieval systems identify which chunk contains the answer." Vercel's agent-readability spec (23 Mar 2026) sets a floor of 3+ headings per page.
- **Never number-only.** `## 4.2` is ungreppable; `## 4.2 Margin call escalation` is not.
- **Use stable anchors.** Agents cite `file.md#margin-call-escalation`; renaming a heading breaks every citation, so treat headings as an API.

**Self-containment is the hard rule.** Fern again: "Each section under a clear heading should contain a complete thought that makes sense when retrieved independently… Instead of referencing 'the authentication method mentioned earlier,' state 'OAuth 2.0 authentication' directly. Agents may retrieve each chunk without surrounding context." In a grep-first corpus this is not a nicety — the agent will genuinely see one `##` block and nothing else. Repeat the subject noun in every section, and repeat units, currencies, and as-of dates rather than inheriting them from the file header.

One deliberate exception: cross-references *by path* are good. PageIndex's headline win was following an in-document pointer ("Appendix G of this report…") to the right table — something embedding similarity cannot do. Write `See [instruments/options.md#assignment](instruments/options.md#assignment)` and the agent can act on it.

## Frontmatter metadata and machine-readable blocks

YAML frontmatter is the cheapest routing signal available: it is greppable without parsing, and it survives partial reads because it is at byte zero.

A workable schema for each corpus file:

```yaml
---
title: Options — greeks, expiry, assignment
description: One line, ~15 words, states scope and boundary. Used verbatim in INDEX.md.
tags: [options, greeks, expiry, assignment]
entities: [SPY, QQQ, AAPL]
updated: 2026-08-16
---
```

`description` should carry both *what* and *when to use it* — Anthropic's rule for skill descriptions (max 1,024 chars, third person, "include both what the Skill does and specific triggers/contexts for when to use it") applies unchanged. Keeping `description` identical to the hook in `INDEX.md` means the agent's routing decision and its confirmation-on-open agree.

Cloudflare's Markdown for Agents (Jul 2026) converges on the same minimal set — `title`, `description`, `image` — emitted as YAML frontmatter ahead of the body, with JSON-LD preserved as a fenced `json` block at the end of the document.

**Prose vs. machine-readable blocks.** Split by whether the content is *read* or *computed on*:

- Rules, rationale, judgement calls, edge cases → prose under a greppable H2.
- Repeated records with identical fields (tickers, thresholds, fixtures, schemas) → a fenced ```jsonl block, one object per line.

JSONL beats a markdown table for agent consumption: each line is independently greppable and independently parseable, so `grep '"ticker":"AAPL"' data.jsonl` returns a complete, valid record — whereas grepping a markdown table row returns a fragment with no header. Keep the block under the H2 that names its contents, and precede it with a one-line field legend so a partial read still explains the schema.

Avoid time-relative statements ("before August 2025, use the old API"). Anthropic's guidance: put superseded material in an explicit `## Old patterns` section with a dated `<details>` block, so stale content is visible but never mistaken for current.

## How to prompt the consuming agent to navigate

The retrieval policy belongs in the agent's system prompt, not in the corpus. PwC's finding — that harness and result presentation move accuracy as much as the retriever — means this prompt is a first-class part of the design.

A minimal, effective loop:

```
Corpus: ./corpus/. Never read files not reachable from corpus/INDEX.md.

1. Read corpus/INDEX.md in full. It lists every file with a one-line hook.
2. Pick at most 2 candidate files from the hooks.
3. Before opening a file, grep the corpus for the specific entity or term:
   grep -rn -i "<term>" corpus/ --include=*.md
4. Read only the matched section. If a file is >200 lines, read its
   "## Contents" block first, then read the single relevant section.
5. Stop as soon as the question is answerable. Do not read "for completeness."
6. If grep returns nothing, say so and stop — do not substitute a near match.
7. Cite every claim as file.md#heading.
```

Step 6 is the point of going vectorless: lexical retrieval can return empty, and an explicit miss is a correct answer. LogicalRAG measured exactly this — anchoring retrieval in explicit lexical constraints "substantially reduces hallucinations" and improves abstention when evidence is absent.

Step 5 matters because Anthropic's tradeoff is real: "runtime exploration is slower than retrieving pre-computed data… Without proper guidance, an agent can waste context by misusing tools, chasing dead-ends." Bound the loop — 2 files, ~3 greps — rather than trusting the agent to self-limit.

Finally, iterate on observed behaviour, not intuition. Anthropic's checklist: watch for unexpected exploration order (structure is unintuitive), missed references (links insufficiently prominent), a file read every single time (promote it into the index), and files never read at all (delete them or fix their hook).

## Measured results and caveats

| Source | Setting | Result |
| --- | --- | --- |
| PwC, arXiv:2605.15184 (14 May 2026) | 116-Q LongMemEval subset, 4 harnesses | grep generally > vector; harness and inline-vs-file result delivery shift scores as much as retriever choice |
| Fudan/Kingstar LogicalRAG, arXiv:2605.27123 (May 2026) | Agentic multi-turn QA | Inverted index + LLM-authored logical queries matches strong agentic hybrid at much lower build/serving cost; fewer unsupported answers |
| VectifyAI Mafin 2.5 on PageIndex (Feb 2026) | FinanceBench, 100% coverage | 98.7% accuracy vs. ~50% reported for conventional vector RAG |
| Fern (Mar 2026) | HTML → markdown docs | >90% token reduction (~16,000 → ~1,600 tokens/page) |

Caveats worth stating in the demo. The FinanceBench figure is a vendor benchmark for a full commercial system, not an isolated ablation of "tree index vs. embeddings" — treat it as directional. The PwC result is a preprint on a 116-question subset. And the whole approach has a genuine cost: several sequential tool calls per query instead of one ANN lookup, so latency is higher. Anthropic's own recommendation is the hybrid — cheap, always-loaded context up front (the index) plus autonomous exploration for the rest — which is precisely the design above.

## Sources

- Anthropic, *Effective context engineering for AI agents*, 29 Sep 2025 — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, *Skill authoring best practices* (500-line limit, TOC >100 lines, one-level references, progressive disclosure) — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Jeremy Howard, *The /llms.txt file, v2* (v1 published 3 Sep 2024) — https://llmstxt.org/
- Mingtian Zhang, Yu Tang & PageIndex Team, *PageIndex: Next-Generation Vectorless, Reasoning-based RAG*, 19 Sep 2025 — https://pageindex.ai/blog/pageindex-intro
- VectifyAI, *PageIndex Leads Financial QA Benchmark* (Mafin 2.5, FinanceBench 98.7%), Feb 2026 — https://pageindex.ai/blog/Mafin2.5 · repo: https://github.com/VectifyAI/Mafin2.5-FinanceBench
- Sen, Kasturi, Lumer, Gulati & Subbiah (PwC), *Is Grep All You Need? How Agent Harnesses Reshape Agentic Search*, arXiv:2605.15184, 14 May 2026 — https://arxiv.org/abs/2605.15184
- Zeng, Deng, Wan, Jiang, Zheng & Huang, *Rethinking Agentic RAG: Toward LLM-Driven Logical Retrieval Beyond Embeddings*, arXiv:2605.27123, May 2026 — https://arxiv.org/abs/2605.27123
- Fern, *Write LLM-friendly docs in March 2026*, 9 Mar 2026 — https://buildwithfern.com/post/how-to-write-llm-friendly-documentation
- Cloudflare, *Markdown for Agents*, updated 13 Jul 2026 — https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/
- Vercel, *Agent Readability: A Specification for AI-Optimized Websites*, 23 Mar 2026 — https://vercel.com/kb/guide/agent-readability-spec
- VectifyAI, *PageIndex* (open-source tree index) — https://github.com/VectifyAI/PageIndex
