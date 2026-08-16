---
title: Swarm Architecture for Research Agents
description: Current (2025-2026) best practices for orchestrator/worker LLM research swarms that gather cited evidence from a document corpus and the web.
tags:
  - swarm
  - orchestrator-worker
  - multi-agent
  - delegation-contract
  - context-isolation
  - failure-modes
  - evaluation
  - citations
date: 2026-08-16
---

# Swarm Architecture for Research Agents

## Key takeaways

- Use orchestrator/worker fan-out only for breadth-first research where subtasks are independent; Anthropic measured +90.2% over a single agent on their internal research eval, at ~15x the tokens of a chat (Anthropic, 2025-06-13).
- Give every worker an explicit four-part brief — objective, output format, tools/sources to use, and task boundaries — because vague briefs cause duplicated searches and coverage gaps (Anthropic, 2025-06-13).
- Embed effort-scaling rules in the orchestrator prompt (simple lookup = 1 worker / 3-10 tool calls; comparison = 2-4 workers / 10-15 calls each; complex = 10+ workers) instead of letting the model guess (Anthropic, 2025-06-13).
- Keep writes single-threaded — parallelize reading, synthesize with one writer — since conflicting implicit decisions from parallel writers are the dominant failure source (Cognition, 2025-06-12; LangChain, 2025-06-16).
- Have workers return a condensed structured receipt (~1,000-2,000 tokens), not raw tool output, so search context stays isolated in the worker (Anthropic, 2025-09-29).
- Add a verifier with a *clean* context — Cognition's review agent finds ~2 bugs per Devin-written PR, ~58% severe, and works better without shared context (Cognition, 2026-04-22).
- Budget for failure: 7 open-source MAS frameworks showed 41%-86.7% failure rates across system design, inter-agent misalignment, and task verification (Cemri et al., NeurIPS 2025).
- Gate completion on a coverage/verification check (LLM-as-judge over accuracy, citation accuracy, completeness, source quality, tool efficiency) rather than on spawning more agents (Anthropic, 2025-06-13).

## When orchestrator/worker fan-out beats a single agent

Anthropic's Research feature uses an orchestrator-worker topology: a LeadResearcher plans, saves the plan to memory, spawns subagents that search in parallel with their own context windows, then synthesizes. Their internal eval put a Claude Opus 4 lead with Claude Sonnet 4 subagents **90.2% ahead of single-agent Opus 4** on breadth-first research (Anthropic, 2025-06-13).

The stated mechanism matters for design decisions: on BrowseComp, three factors explained 95% of performance variance, and **token usage alone explained 80%**, with tool-call count and model choice as the other two. Fan-out helps mainly because it buys parallel context capacity, not because agents "collaborate."

The cost is real. Agents use ~4x the tokens of chat; multi-agent systems ~15x. Anthropic's own guidance: fan-out is justified only when task value is high, work is heavily parallelizable, evidence exceeds one context window, and many complex tools are involved.

Fan-out is a poor fit when subtasks share dependencies or need identical context; Anthropic names most coding tasks as a bad fit. Cognition argued this more strongly for write-heavy work: parallel agents make conflicting implicit decisions about style and edge cases, and the final agent inherits the mess (Cognition, 2025-06-12).

The reconciliation, from LangChain (2025-06-16): **read actions parallelize; write actions do not.** Anthropic's system parallelizes retrieval but deliberately synthesizes the report in a single unified call. For an evidence-gathering swarm over a corpus plus the web, this is the load-bearing rule — fan out the reading, keep one writer.

By 2026 Cognition's position had softened but not reversed: they now ship multi-agent systems where "multiple agents contribute intelligence to a task while writes stay single-threaded," and note most production subagents remain read-only, "more resembling tool calls than true multi-agent collaboration" (Cognition, 2026-04-22).

## The delegation contract: what every worker brief must specify

Anthropic's second prompting principle — "teach the orchestrator how to delegate" — is the most directly actionable finding for a fan-out research system. Each subagent needs four things (Anthropic, 2025-06-13):

1. **Objective** — the specific question this worker answers.
2. **Output format** — the exact shape of the receipt it returns.
3. **Tools and sources guidance** — which retrieval surfaces to use, and which to avoid.
4. **Clear task boundaries** — what is explicitly *not* this worker's job.

The failure they observed without this is concrete and worth quoting as a test case: instructions as short as "research the semiconductor shortage" led one subagent to explore the 2021 automotive chip crisis while two others duplicated each other on 2025 supply chains, "without an effective division of labor." Vague briefs produce **duplicated work, coverage gaps, and misinterpreted tasks** — exactly the three things a fan-out system exists to avoid.

Tool guidance is not decoration. Anthropic notes "an agent searching the web for context that only exists in Slack is doomed from the start," and that with MCP servers agents meet unfamiliar tools of wildly varying description quality. Their heuristics: examine available tools first, match tool to intent, prefer specialized over generic. Their tool-testing agent, which rewrote a flawed tool description after dozens of trials, produced a **40% decrease in task completion time** for later agents.

Two supporting behaviors: **start wide, then narrow** (agents default to long, specific queries returning few results — prompt them to open broad, evaluate, then drill in), and **guide the thinking process** (the lead uses extended thinking to decide worker count and roles; workers use interleaved thinking after tool results to spot gaps).

Cognition's counterweight: pass enough of the originating trace and shared priors (todo list, plan file) that a worker cannot misread its slice (Cognition, 2025-06-12).

## Effort scaling rules and topology: fixed versus dynamic fan-out

Agents are bad at judging how much effort a task deserves. Anthropic's early system spawned **50 subagents for simple queries** and searched endlessly for nonexistent sources. Their fix was not a smarter planner but explicit scaling rules written into the orchestrator prompt (Anthropic, 2025-06-13):

| Query type | Workers | Tool calls each |
| --- | --- | --- |
| Simple fact-finding | 1 | 3-10 |
| Direct comparison | 2-4 | 10-15 |
| Complex research | 10+ | clearly divided responsibilities |

These "prevent overinvestment in simple queries, which was a common failure mode in our early versions."

On topology, their production shape is **dynamic but bounded**: the lead spins up 3-5 subagents in parallel rather than serially, each subagent issues 3+ tool calls in parallel, and the lead may spawn another round after reviewing results. Those two levels of parallelism **cut research time by up to 90%** on complex queries. So the recommendation is neither a rigid fixed DAG nor unbounded recursive spawning — it is a fixed-shape round (bounded width) that the orchestrator may repeat if a completeness check fails.

Execution is **synchronous** in Anthropic's production system: the lead waits for each set of subagents. They call this a bottleneck but keep it because async execution "introduces challenges in result coordination, state consistency, and error propagation." For a hackathon-scale swarm, synchronous rounds are the right default.

OpenAI frames the same choice as the **manager pattern** (a central LLM delegating to specialists via tool calls and synthesizing results) versus the **decentralized pattern** (peer agents handing off control, no central synthesizer). For cited-evidence research use the manager pattern — one agent must hold the synthesis and the citation obligation (OpenAI, *A Practical Guide to Building Agents*).

## Context isolation, structured receipts, and the single-writer rule

Anthropic frames context as a finite **attention budget**: every token depletes it, because transformer attention scales with n² pairwise relationships and models have fewer specialized parameters for context-wide dependencies. This is the mechanical reason fan-out helps — "each subagent context window can be allocated to a more narrow sub-task" (Anthropic, 2025-09-29).

The concrete interface rule: a subagent returns a **condensed, distilled summary of its work, often 1,000-2,000 tokens**, not its raw trace. This achieves "clear separation of concerns — the detailed search context remains isolated within sub-agents, while the lead agent focuses on synthesizing and analyzing the results." For an evidence swarm, make that receipt a strict schema (claim, evidence span, source URL/doc id, date, confidence) so the orchestrator never has to re-read raw pages.

Anthropic pairs isolation with two other context techniques: **compaction** (summarize a near-full context and reinitiate a fresh window, preserving decisions and open problems while discarding redundant tool output; tool-result clearing is the cheap first step) and **structured note-taking** (persist plans and notes to external memory, pull them back later). Their lead agent saves its plan to memory precisely because a 200k context will truncate and the plan must survive.

Cognition's clean-context finding cuts the other way and is worth internalizing: their code-review agent works **better with no shared context** with the writer, because a fresh short context is genuinely smarter (context rot) and because reasoning backward from artifacts surfaces things the author overlooked (Cognition, 2026-04-22). So: **share context for decomposition, withhold it for verification.**

The single-writer rule follows from Cognition's Principle 2, "actions carry implicit decisions, and conflicting decisions carry bad results." Parallel readers are safe; parallel writers to a shared artifact are not. Route all worker receipts into one synthesizer that owns the final document.

## Known failure modes and mitigations

Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (arXiv:2503.13657, NeurIPS 2025 Datasets & Benchmarks) is the strongest empirical grounding available. They annotated **1,642 execution traces across 7 popular MAS frameworks** (GPT-4 series, Claude series, plus Qwen2.5 and CodeLlama in analysis) over coding, math, and general agent tasks, and measured **41% to 86.7% failure rates** on those SOTA open-source frameworks.

The MAST taxonomy has **14 failure modes in 3 categories**, built via grounded theory from 150+ traces (each averaging 15,000+ lines) with six expert annotators, validated at inter-annotator agreement κ = 0.88; their o1-based LLM annotator reached κ = 0.77, and κ = 0.79 on two unseen frameworks.

The three categories, with the mitigation each implies for a research swarm:

1. **System/specification design issues** — ambiguous roles, unclear task definitions, missing constraints, violated task specs. *Mitigation:* the four-part delegation contract above, plus explicit boundaries naming what a worker must not do.
2. **Inter-agent misalignment** — communication breakdown, withheld or ignored information, derailment, state desync, duplicated work. *Mitigation:* single-writer synthesis, disjoint worker briefs, shared plan file, structured receipts instead of free-form chatter.
3. **Task verification / termination** — premature termination, absent or incomplete verification, incorrect verification. *Mitigation:* an explicit completeness gate and a separate verifier agent (next section).

Practitioner reports name overlapping modes. Anthropic's early failures: spawning 50 subagents for a simple query, endless searching for nonexistent sources, agents "distracting each other with excessive updates," and continuing after they already had sufficient results (Anthropic, 2025-06-13). Cognition's: subagents misreading their slice, and parallel workers producing stylistically incompatible outputs (Cognition, 2025-06-12).

Note the split — MAST attributes only about a fifth of failures to verification gaps and the larger share to specification and coordination, so **fixing briefs and topology usually beats adding a checker**.

## Completeness gates, verification loops, and citation integrity

The decision every research orchestrator faces is *"do I have enough, or do I spawn another round?"* Two mechanisms answer it.

**A grading gate.** Anthropic scores research output with a single LLM-as-judge prompt across five criteria — **factual accuracy, citation accuracy, completeness, source quality, and tool efficiency** — returning a 0.0-1.0 score plus a pass/fail grade. A single judge call proved "most consistent and aligned with human judgements." Those criteria are reusable as a swarm's stop condition: on a completeness or citation failure, spawn one targeted follow-up round with a narrowed brief rather than more agents blindly.

**A separate verifier with clean context.** Cognition's Devin Review catches an average of **2 bugs per PR on Devin-written PRs, ~58% of them severe** (logic errors, missing edge cases, security vulnerabilities), looping through multiple cycles and finding new bugs each time. The counterintuitive choice: the reviewer shares *no* context with the writer. Generalizing to research: a fact-check worker should see the claims and sources, not the researcher's trace. The critical piece is the **bridge back** — the writer must use its broader context to filter which findings to act on, or the loop never terminates (Cognition, 2026-04-22).

**Citations as a separate pass.** Anthropic runs a dedicated **CitationAgent** after the research loop exits: it takes the documents plus the draft report and identifies specific locations for citations, "ensuring all claims are properly attributed to their sources." Making attribution its own stage — rather than trusting each worker to cite inline — is the pattern to copy for structured cited-fact output.

Evaluate small: Anthropic started with **~20 queries** representing real usage, enough to see the impact of changes. They grade **end state, not turn-by-turn**, since agents legitimately find alternative paths, and kept human testing in the loop to catch hallucinated answers and source-selection bias.

## Operating a swarm in production

Four operational lessons from Anthropic's production Research system (2025-06-13), all of which apply at small scale too:

**Agents are stateful and errors compound.** A long-running agent holds state across many tool calls, so a mid-run failure cannot be fixed by restarting from scratch — restarts are expensive and user-hostile. Build **durable execution** that resumes from where the agent was when the error occurred. LangChain makes the same argument and built it into LangGraph (LangChain, 2025-06-16).

**Non-determinism makes debugging hard.** Identical prompts produce different runs. Anthropic's fix was **full production tracing** of agent decision patterns and interaction structures (not conversation content, for privacy), which let them answer complaints like "the agent didn't find obvious information" — bad queries? bad sources? tool failures? Without traces you are guessing.

**Deploy without killing running agents.** Shipping a code change mid-run can break in-flight work. Anthropic uses **rainbow deployments**, gradually shifting traffic so existing runs finish on the version they started on.

**Coordination complexity grows faster than agent count.** Anthropic's remedy was iteration discipline, not architecture: they built simulations using the exact production prompts and tools, then watched agents work step by step ("think like your agents"). This exposed failure modes invisible from outputs alone. They also found Claude 4 models to be effective prompt engineers on their own failure traces — given a prompt and a failure mode, the model can diagnose and propose a fix.

One economic caveat for any design review: at ~15x chat token usage, a swarm must be pointed at tasks whose value justifies the spend (Anthropic, 2025-06-13). Cognition's 2026 framing is that cost pressure now itself drives multi-agent design — cheap models for bulk work, escalating to a frontier "smart friend" when needed — but that pattern works today only when *both* models are strong (Cognition, 2026-04-22).

## Sources

- Anthropic, "How we built our multi-agent research system," 2025-06-13 — https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic, "Effective context engineering for AI agents," 2025-09-29 — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Cognition (Walden Yan), "Don't Build Multi-Agents," 2025-06-12 — https://cognition.com/blog/dont-build-multi-agents
- Cognition (Walden Yan), "Multi-Agents: What's Actually Working," 2026-04-22 — https://cognition.com/blog/multi-agents-working
- LangChain (Harrison Chase), "How and when to build multi-agent systems," 2025-06-16 — https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems
- Cemri, Pan, Yang, Agrawal et al. (UC Berkeley), "Why Do Multi-Agent LLM Systems Fail?" arXiv:2503.13657 (v1 2025-03-17; NeurIPS 2025 Datasets & Benchmarks) — https://arxiv.org/abs/2503.13657
- MAST taxonomy code and MAST-Data dataset — https://github.com/multi-agent-systems-failure-taxonomy/MAST and https://huggingface.co/datasets/mcemri/MAST-Data
- OpenAI, "A Practical Guide to Building Agents" (manager vs decentralized patterns) — https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
