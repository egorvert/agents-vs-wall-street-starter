"""LLM plumbing: LangSmith-wrapped OpenAI client, structured outputs, local
content-addressed cache, retry-once-with-error policy.

Cache modes (env RESEARCH_CACHE): rw (default) = record/replay; off = never
cache; offline = replay only, raise on miss. Keys hash model + messages +
schema + prompt file hashes, so a prompt edit invalidates cleanly.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI

from . import config

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = wrap_openai(AsyncOpenAI())
    return _client


def _cache_mode() -> str:
    return os.environ.get("RESEARCH_CACHE", "rw")


def _cache_key(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def _cache_path(key: str):
    return config.CACHE_DIR / f"{key}.json"


class SchemaRetryError(RuntimeError):
    pass


@traceable(run_type="chain", name="call_structured")
async def call_structured(
    *,
    model: str,
    system: str,
    user: str,
    schema_name: str,
    schema: dict,
    prompt_version: str,
    metadata: dict[str, Any],
    validate=None,
) -> dict:
    """One structured-output call with local caching and one validator retry.

    `validate(parsed) -> list[str]` returns problem strings; non-empty triggers
    exactly one retry with the problems and admissible context appended. A second
    failure raises — deeper loops mainly produce plausible-but-wrong output.
    """
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    key = _cache_key({
        "model": model, "messages": messages, "schema": schema,
        "prompt_version": prompt_version, "cutoff": config.CUTOFF_DATE,
    })
    mode = _cache_mode()
    path = _cache_path(key)
    if mode in ("rw", "offline") and path.exists():
        return json.loads(path.read_text())["parsed"]
    if mode == "offline":
        raise RuntimeError(f"offline cache miss for {metadata.get('worker')}/{metadata.get('company_id')}")

    async def _once(msgs):
        resp = await client().chat.completions.create(
            model=model,
            messages=msgs,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": schema},
            },
            langsmith_extra={"metadata": metadata},
        )
        return json.loads(resp.choices[0].message.content)

    started = time.time()
    parsed = await _once(messages)
    problems = validate(parsed) if validate else []
    if problems:
        retry_note = (
            "Your previous answer had verification problems. Fix ONLY these, keeping "
            "everything that was correct. Problems (with admissible alternatives where "
            "known):\n- " + "\n- ".join(problems[:20])
        )
        messages = messages + [
            {"role": "assistant", "content": json.dumps(parsed)},
            {"role": "user", "content": retry_note},
        ]
        parsed = await _once(messages)
        problems = validate(parsed) if validate else []
        if problems:
            # ship what survives; caller drops failing items and logs them
            parsed["_unresolved"] = problems

    if mode == "rw":
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "parsed": parsed, "model": model, "wall_s": round(time.time() - started, 2),
            "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }))
        tmp.rename(path)  # atomic
    return parsed
