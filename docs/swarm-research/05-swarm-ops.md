---
title: Swarm Ops — Running LLM Agent Fan-Out Cheaply, Fast, and Reproducibly
description: Operational patterns for Python LLM swarms — asyncio concurrency, prompt and response caching, retry policy, cost budgeting, tracing, and demo-day wall-clock tuning.
tags:
  - asyncio
  - concurrency
  - prompt-caching
  - reproducibility
  - retries
  - cost-budgeting
  - observability
  - langsmith
  - opentelemetry
  - openai
date: 2026-08-16
---

# Swarm Ops — Running LLM Agent Fan-Out Cheaply, Fast, and Reproducibly

## Key takeaways

- Use `asyncio.TaskGroup` (3.11+) plus a module-level `asyncio.Semaphore` and a per-call `asyncio.timeout`; never fan out unbounded tasks against a rate-limited API.
- Ship partial results: collect per-worker outcomes as `Ok`/`Err` records inside the task rather than letting one exception cancel the group, so the synthesis step runs on whatever succeeded.
- Order every prompt static-first (system, tools, schema, few-shots) and variable-last; on GPT-5.6 cached reads cost 0.1x input but cache *writes* cost 1.25x, so bad ordering now costs money rather than being merely neutral.
- Pass a stable `prompt_cache_key` per worker archetype and keep tool arrays byte-identical — one edited tool description invalidates the whole prefix.
- Add a local content-addressed disk cache keyed on SHA-256 of (model, canonicalised messages, tools, schema, temperature, seed) with a `--offline` flag that raises on a miss; this is what makes demo runs reproducible.
- Retry schema-validation failures exactly once with the validator error appended; never retry business-rule rejections, tool-empty results, or context-length errors.
- Budget fan-out as cheap workers (`gpt-5.6-luna`, $0.20/$1.20 per 1M) into one expensive synthesis call (`gpt-5.6-sol`, $5/$30); hierarchical routing reports ~98% of full-frontier accuracy at ~61% of cost.
- Trace with `wrap_openai(AsyncOpenAI())` + `@traceable` — no LangChain required — and precompute every network-bound artefact before the demo so the live path is one warm fan-out.

## Async fan-out: semaphores, TaskGroups, timeouts, partial results

The 2026 consensus pattern is structured concurrency with an explicit concurrency gate. `asyncio.TaskGroup` (Python 3.11+) replaces `asyncio.gather` because it gives every task an explicit lifetime and cancels stragglers on scope exit, eliminating orphaned tasks. But a TaskGroup alone will happily create thousands of in-flight requests, so pair it with `asyncio.Semaphore` sized to your rate limit, and wrap each call in `asyncio.timeout()` for a per-call deadline.

```python
SEM = asyncio.Semaphore(12)

async def worker(client, item) -> Result:
    try:
        async with SEM, asyncio.timeout(45):
            return Ok(await call_model(client, item))
    except Exception as e:                # swallow INSIDE the task
        return Err(item.id, repr(e))

async def fan_out(items):
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(worker(client, i)) for i in items]
    return [t.result() for t in tasks]
```

The critical detail for shipping partial results: **catch inside the worker**. TaskGroup's semantics are all-or-nothing — an escaping exception cancels siblings. Returning a result union keeps the group healthy and lets synthesis proceed on the successful subset. If you prefer `gather`, `return_exceptions=True` gives the same property with weaker cancellation guarantees.

Tune the client, not just the loop. The OpenAI Python SDK defaults to `Timeout(connect=5, read=600, write=600, pool=600)` — a 10-minute read timeout that will hang a demo. Set `AsyncOpenAI(timeout=httpx.Timeout(connect=5, read=60, write=60, pool=5), max_retries=2)`. For fan-out above ~100 concurrent calls, pass a custom `httpx.AsyncClient` with raised `max_connections`/`max_keepalive_connections`, since the default pool becomes the bottleneck before the API does.

Size the semaphore from headers, not guesswork: read `x-ratelimit-remaining-requests` and `x-ratelimit-remaining-tokens`, and honour `Retry-After` on 429.

## GPT-5.6 prompt caching mechanics and prompt ordering

Automatic prefix caching still applies, but the economics changed on the GPT-5.6 family and it is no longer free to get wrong.

**Mechanics.** Eligibility requires at least 1,024 tokens through the cache breakpoint (GPT-5.6 enforces this strictly; earlier models ranged 1,024–2,048 and matched in 128-token increments). Cacheable content includes system/developer/user/assistant messages, tool definitions *and their ordering*, structured-output schemas, and identical image/audio inputs. Requests route to cache machines by `prompt_cache_key` plus prefix hash.

**Pricing.** On GPT-5.6+, cached reads bill at 0.1x the uncached input rate and cache **writes** bill at 1.25x (a total rate, not a surcharge). Earlier families had no write fee. Track `cached_tokens` vs `cache_write_tokens` in `input_tokens_details` (Responses API) or `prompt_tokens_details` (Chat Completions); high writes with low reads means your breakpoint is in the wrong place.

**TTL.** GPT-5.6+ uses a 30-minute exact TTL via `prompt_cache_options.ttl` (only `30m` is supported), refreshed free on reuse. Earlier models used opaque 5–10 minute in-memory retention, extendable to 24 hours via `prompt_cache_retention`.

**What invalidates it.** Any change before the breakpoint: reworded instructions, reordered content, an edited tool description, a modified output schema, differing image settings. Injecting a timestamp or run ID at the top of the system prompt destroys the cache for every request. Rewriting or compacting conversation history has the same effect — append turns instead.

**Ordering rules for a swarm.** Put the persona-invariant preamble, tool definitions, schema, and few-shot examples first; put the per-company/per-ticker payload last. Give each worker archetype a stable `prompt_cache_key` (e.g. `"analyst-v3"`) so its N parallel calls share a prefix, and aim for roughly 15 requests/minute per key before partitioning. On GPT-5.6 you can mark the boundary explicitly with `prompt_cache_breakpoint: {"mode": "explicit"}`. Filter tools with `allowed_tools` rather than mutating the tool array.

## Local response caching and offline replay for reproducibility

Provider-side prompt caching saves money; it does not make a run reproducible. Even at `temperature=0` providers do not guarantee identical outputs. For a demo you need a **content-addressed local cache**.

Key on a canonicalised hash of everything that can change the output:

```python
payload = {
    "model": model,
    "messages": messages,        # already normalised
    "tools": tools,
    "response_format": schema,
    "temperature": temperature,
    "seed": seed,
}
key = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":"),
               ensure_ascii=False).encode()
).hexdigest()
```

Canonicalisation matters more than the hash: sort keys, fix separators, strip volatile fields (request IDs, timestamps, `prompt_cache_key`), and normalise whitespace in prompt templates. Two logically identical requests that differ by dict ordering will thrash the cache.

Store one JSON file per key under `.cache/llm/<key>.json` containing the request, the response, token usage, latency, and the model ID actually served. Committing (or archiving) that directory turns the whole pipeline into a replayable artefact — the record/replay "cassette" pattern from HTTP testing, adapted to model calls.

Expose three modes via a single flag:

- `--cache=rw` (default dev): read on hit, write on miss.
- `--cache=off`: bypass entirely, for measuring real cost and latency.
- `--offline` / `--cache=replay`: read-only; a miss raises rather than calling the API.

`--offline` is the demo-safety mode. It guarantees zero network dependency, zero spend, and byte-identical output on stage, and it turns "the venue Wi-Fi died" into a non-event. Run it in CI too: a replay-mode test suite catches prompt edits that silently change the cache key.

Record the model ID served alongside the response. When a provider silently rolls an alias forward, the cache file is the only evidence that yesterday's numbers came from a different model.

## Retry policy: retry once with the error, or fail fast

Two distinct failure classes need opposite handling.

**Transport failures** (429, 500, 502, timeouts, connection resets) — retry with exponential backoff and jitter, honouring `Retry-After` when present. The OpenAI SDK does this internally; cap it (`max_retries=2`) so a swarm of 50 workers cannot silently spend 10 minutes retrying. Add jitter so parallel workers do not resynchronise into a thundering herd after a shared 429.

**Schema-validation failures** — retry exactly once, and only with feedback. Send back the failed output plus the validator's error text and ask for a correction of that specific issue:

```python
try:
    return Model.model_validate_json(raw)
except ValidationError as e:
    messages += [
        {"role": "assistant", "content": raw},
        {"role": "user", "content": f"Your output failed validation:\n{e}\n"
                                    f"Return corrected JSON only."},
    ]
    return Model.model_validate_json(await call(messages))  # no second retry
```

One retry captures nearly all the recoverable cases. Beyond that, repeated content failures indicate the prompt or schema is wrong, not the model — cheaper to fail the worker and let synthesis proceed on the rest.

**Do not retry:**
- Business-rule rejections (ticker not in universe, value outside allowed range) — deterministic, will fail identically.
- Tool execution failures returning empty results — fall back, don't re-ask.
- `context_length_exceeded` and 400-class request errors — retrying the same oversized payload is guaranteed to fail.
- Anything where the retry cost exceeds the value of the field; drop it and mark the record partial.

Note the retry appends to the message tail, so it preserves the cached prefix — a validation retry is comparatively cheap on input tokens.

Instrument the retry rate as an SLO. Healthy pipelines average roughly 0.5–1.5 retries per call; sustained values above 2 point at a prompt or schema regression, or a model version change.

## Cost and latency budgeting for fan-out

Current OpenAI text tiers (verified against the live pricing and models pages, August 2026). All three GPT-5.6 models share a 1.05M-token context, 128K max output, and a 2026-02-16 knowledge cutoff.

| Model | Input /1M | Cached /1M | Output /1M | Use |
|---|---|---|---|---|
| `gpt-5.6-sol` | $5.00 | $0.50 | $30.00 | Synthesis, hard reasoning |
| `gpt-5.6-terra` | $2.00 | $0.20 | $12.00 | Balanced everyday work |
| `gpt-5.6-luna` | $0.20 | $0.02 | $1.20 | High-volume workers |
| `gpt-5.4-mini` | $0.75 | $0.075 | $4.50 | Legacy cheap tier |
| `gpt-5-mini` | $0.25 | $0.025 | $2.00 | Legacy cheap tier |

Long-context requests bill separately (Sol rises to $10/$1.00/$45). Batch API is ~50% of standard rates; Fast mode is ~2x.

**The shape that wins.** Fan out N cheap workers on `luna`, fan in to a single `sol` synthesis call. Published results for this hierarchical split report ~97.7% of full-frontier accuracy at ~61% of frontier cost. The 25x input-price gap between Luna and Sol means a 40-worker swarm on Luna costs less than two Sol calls.

**Sizing the fan-out.** Cap concurrency at `min(token_budget / per_worker_cost, rate_limit / avg_requests_per_worker)`. Compute the budget before running, not after: 40 workers x 3K input x 800 output on Luna ≈ $0.06; the same on Sol ≈ $1.56.

**Latency.** Fan-out/fan-in cuts wall-clock 36–50% versus sequential in typical workflows, but total latency is governed by the slowest worker plus synthesis. Cap `max_tokens` close to expected output size — it lowers both cost and tail latency, and reduces TPM pressure. Prompt caching independently cuts time-to-first-token by up to ~80% on warm prefixes.

## Observability: LangSmith without LangChain, and OpenTelemetry GenAI

**LangSmith, no LangChain.** The API is stable and two lines of setup. `pip install -U langsmith openai`, then:

```python
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI

client = wrap_openai(AsyncOpenAI())

@traceable(run_type="chain", name="analyst_worker")
async def analyse(ticker: str) -> Verdict: ...
```

`wrap_openai` logs every model call as a nested span with tokens, latency, and cost; `@traceable` groups a function's inputs, outputs, and child spans into one trace. Environment variables: `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, optional `LANGSMITH_PROJECT`, and `LANGSMITH_ENDPOINT` for EU/APAC regions. `run_type` accepts `chain`, `llm`, `tool`, `retriever`. Async functions work; context propagates through `TaskGroup` children via contextvars, so a swarm renders as one parent trace with N sibling spans — exactly the view you want when diagnosing which worker was slow.

Practical swarm note: tracing is a network call. Keep it enabled in dev, and gate it off (or rely on background flushing) when you are measuring true wall-clock, so the tracer's own latency doesn't pollute your numbers.

**OpenTelemetry GenAI.** Still not fully stable as of mid-2026. On 2026-06-12, semantic-conventions v1.42.0 deprecated the GenAI conventions in the main repo and moved them to `open-telemetry/semantic-conventions-genai`, which had no tagged release as of mid-July 2026; `gen-ai-spans.md` and `gen-ai-metrics.md` still carry Status: Development. `gen_ai.client` spans (one per LLM round-trip) and the core chat/embedding attributes are settled enough to build dashboards on. Agent- and tool-orchestration conventions — `gen_ai.operation.name` values like `create_agent`, `invoke_agent`, `execute_tool`, `retrieval`, `plan` — are experimental and still moving.

**Recommendation for a hackathon:** LangSmith for the demo (zero-config traces, cost attribution out of the box); OTel GenAI only if you need vendor neutrality, and pin the convention version explicitly.

## Wall-clock optimisation for a live demo

Optimise the thing the audience watches, and move everything else off the critical path.

**Precompute (before the demo starts):**
- All data fetches — filings, prices, fundamentals — into local JSON/parquet. Network I/O against third-party APIs is the least reliable part of any demo.
- Any embedding or index build.
- A full `--cache=rw` warm-up run of the exact demo inputs, so the local cache holds every response and the run is replayable at `--offline`.
- Warm the provider prefix cache by issuing one throwaway call per worker archetype; the 30-minute TTL comfortably covers a demo slot, and it removes cold-start TTFT.
- Import and client construction at process start, not on first call.

**Parallelise:**
- The worker fan-out (the whole point).
- Independent data lookups per worker, inside the same TaskGroup.
- Streaming the synthesis output so first tokens appear while generation continues — perceived latency drops even when total time doesn't.

**Do not parallelise:**
- Synthesis; it depends on the fan-in.
- Anything that would blow the RPM limit and trigger a 429 on stage. Set the semaphore conservatively for the demo run — a 429 storm looks far worse than two extra seconds.

**Guardrails.** Give every worker a hard `asyncio.timeout` and a fallback value, so a single stall degrades one card rather than the whole screen. Render results as they land instead of waiting for the full set. Keep a `--offline` replay as the rehearsed fallback and test it on the venue network. Cap `max_tokens` tightly; unbounded output is the most common source of an unexpectedly long tail.

## Sources

- OpenAI, Prompt caching guide — https://developers.openai.com/api/docs/guides/prompt-caching (retrieved 2026-08-16)
- OpenAI, API pricing — https://developers.openai.com/api/docs/pricing (retrieved 2026-08-16)
- OpenAI, Models — https://developers.openai.com/api/docs/models (retrieved 2026-08-16)
- OpenAI, Rate limits guide — https://developers.openai.com/api/docs/guides/rate-limits (retrieved 2026-08-16)
- OpenAI, Prompt Caching 201 cookbook — https://developers.openai.com/cookbook/examples/prompt_caching_201
- LangChain, LangSmith observability quickstart — https://docs.langchain.com/langsmith/observability-quickstart (retrieved 2026-08-16)
- LangSmith cookbook, tracing without LangChain — https://github.com/langchain-ai/langsmith-cookbook/blob/main/tracing-examples/traceable/tracing_without_langchain.ipynb
- OpenTelemetry, GenAI semantic conventions (new repo) — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md
- OpenTelemetry blog, Inside the LLM Call: GenAI Observability (2026) — https://opentelemetry.io/blog/2026/genai-observability/
- "GenAI semantic conventions are NOT stable yet — what shipped in 2026" — https://dev.to/azena-ai/opentelemetrys-genai-semantic-conventions-are-not-stable-yet-heres-what-actually-shipped-in-2026-3mke
- asyncio TaskGroup patterns: the complete 2026 guide — https://www.pyblog.in/programming/asyncio-taskgroup-patterns-the-complete-2026-guide/
- Structured concurrency for AI pipelines: why asyncio.gather() isn't enough (2026-04-09) — https://tianpan.co/blog/2026-04-09-structured-concurrency-ai-pipelines-parallel-tool-calls
- Modern asyncio patterns — TaskGroup, anyio, and what changed (2026) — https://blog.rajpoot.dev/posts/python/asyncio-patterns-taskgroup-anyio-2026/
- openai-python issue #1725, AsyncOpenAI concurrency and pool limits — https://github.com/openai/openai-python/issues/1725
- OpenAI Python API library reference — https://developers.openai.com/api/reference/python
- LLM structured outputs: schema validation for real pipelines (2026) — https://collinwilkins.com/articles/structured-output
- LLM structured outputs: JSON schema enforcement and tool-calling reliability (2026-05-06) — https://eastondev.com/blog/en/posts/ai/20260506-llm-structured-output/
- AI21, Reproducing variance: caching in agentic LLM pipelines — https://www.ai21.com/blog/caching-in-agentic-llm-pipelines/
- LLM response caching: cache keys, TTLs, invalidation (2026) — https://www.buildmvpfast.com/blog/llm-response-caching-cache-keys-invalidation-strategies-2026
- Zylos Research, AI agent cost optimization: token budgets and model routing (2026-04-12) — https://zylos.ai/research/2026-04-12-ai-agent-cost-optimization-token-budget-model-routing/
- Zylos Research, Parallel concurrency in production AI agents: DAG scheduling, fan-out/fan-in (2026-04-26) — https://zylos.ai/research/2026-04-26-parallel-concurrency-agent-execution/
- Multi-agent orchestration: 5 patterns that work in 2026 — https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work
- Prompt caching economics: cache-first agent design (2026) — https://www.digitalapplied.com/blog/prompt-caching-economics-cache-first-agent-architecture-2026
