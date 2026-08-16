"""Thin OpenAI Responses client with strict schemas, caching, and audit events."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-5.6-sol"  # tier-up 16:25: was terra
DEFAULT_REASONING_EFFORT = "low"
EventLogger = Callable[[dict[str, Any]], None]


class ModelClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelResult:
    data: dict[str, Any]
    response_id: str
    model: str
    usage: dict[str, Any]
    cached: bool = False


class StructuredModelClient(Protocol):
    model: str
    reasoning_effort: str

    def generate_json(
        self,
        *,
        schema_name: str,
        instructions: str,
        input_text: str,
        schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ModelResult: ...


def json_event_logger(event: dict[str, Any]) -> None:
    """Write one compact, secret-free JSON event for the orchestrator to capture."""
    print(json.dumps(event, sort_keys=True, ensure_ascii=False))


def emit_event(logger: EventLogger | None, event: str, **fields: Any) -> None:
    if logger is None:
        return
    logger(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
    )


def stable_hash(value: str | bytes | dict[str, Any]) -> str:
    if isinstance(value, dict):
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    elif isinstance(value, str):
        payload = value.encode()
    else:
        payload = value
    return hashlib.sha256(payload).hexdigest()


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
        api_key: str | None = None,
        cache_root: Path | None = None,
        use_cache: bool = True,
        logger: EventLogger | None = json_event_logger,
        timeout_seconds: float = 45.0,
        max_output_tokens: int = 8_000,
    ) -> None:
        self.model = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        self.reasoning_effort = reasoning_effort
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._cache_root = Path(cache_root) if cache_root is not None else None
        self._use_cache = use_cache
        self._logger = logger
        self._max_output_tokens = max_output_tokens
        self._client = (
            OpenAI(api_key=self._api_key, timeout=timeout_seconds, max_retries=2)
            if self._api_key
            else None
        )

    def generate_json(
        self,
        *,
        schema_name: str,
        instructions: str,
        input_text: str,
        schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ModelResult:
        if self._client is None:
            raise ModelClientError("OPENAI_API_KEY is required for live model calls")

        request_meta = dict(metadata or {})
        prompt_hash = stable_hash(instructions)
        input_hash = stable_hash(input_text)
        schema_hash = stable_hash(schema)
        cache_key = stable_hash(
            {
                "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "schema_name": schema_name,
                "schema_hash": schema_hash,
                "prompt_hash": prompt_hash,
                "input_hash": input_hash,
            }
        )
        cache_path = self._cache_path(cache_key)
        if cache_path is not None and cache_path.is_file():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            emit_event(
                self._logger,
                "model_cache_hit",
                model=self.model,
                schema_name=schema_name,
                prompt_hash=prompt_hash,
                input_hash=input_hash,
                cache_key=cache_key,
                **request_meta,
            )
            return ModelResult(
                data=cached["data"],
                response_id=cached.get("response_id", "cached"),
                model=cached.get("model", self.model),
                usage=cached.get("usage", {}),
                cached=True,
            )

        safe_schema_name = "".join(character if character.isalnum() else "_" for character in schema_name)
        payload = {
            "model": self.model,
            "store": False,
            "reasoning": {"effort": self.reasoning_effort},
            "input": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": safe_schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
            "max_output_tokens": self._max_output_tokens,
        }
        started = time.monotonic()
        emit_event(
            self._logger,
            "model_request_started",
            model=self.model,
            reasoning_effort=self.reasoning_effort,
            schema_name=schema_name,
            prompt_hash=prompt_hash,
            input_hash=input_hash,
            schema_hash=schema_hash,
            **request_meta,
        )
        try:
            response = self._client.responses.create(**payload)
        except OpenAIError as exc:
            emit_event(
                self._logger,
                "model_request_failed",
                model=self.model,
                schema_name=schema_name,
                error=type(exc).__name__,
                **request_meta,
            )
            raise ModelClientError(f"OpenAI request failed: {exc}") from exc
        elapsed_ms = round((time.monotonic() - started) * 1000)
        result = self._parse_response(response.model_dump(mode="json"))
        emit_event(
            self._logger,
            "model_request_completed",
            model=result.model,
            response_id=result.response_id,
            schema_name=schema_name,
            prompt_hash=prompt_hash,
            input_hash=input_hash,
            duration_ms=elapsed_ms,
            usage=result.usage,
            **request_meta,
        )
        if cache_path is not None:
            self._write_cache(cache_path, result)
        return result

    def _cache_path(self, cache_key: str) -> Path | None:
        if not self._use_cache or self._cache_root is None:
            return None
        return self._cache_root / "model" / f"{cache_key}.json"

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> ModelResult:
        if response.get("status") != "completed":
            raise ModelClientError(
                f"OpenAI response did not complete: {response.get('status')!r}"
            )
        texts: list[str] = []
        refusals: list[str] = []
        for output in response.get("output", []):
            if not isinstance(output, dict):
                continue
            for content in output.get("content", []):
                if not isinstance(content, dict):
                    continue
                if content.get("type") == "refusal":
                    refusals.append(str(content.get("refusal", "model refusal")))
                elif content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    texts.append(content["text"])
        if refusals:
            raise ModelClientError(f"OpenAI model refused the request: {'; '.join(refusals)}")
        if not texts:
            raise ModelClientError("OpenAI response contained no output_text")
        try:
            parsed = json.loads("".join(texts))
        except json.JSONDecodeError as exc:
            raise ModelClientError(f"OpenAI structured output was not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ModelClientError("OpenAI structured output must decode to an object")
        return ModelResult(
            data=parsed,
            response_id=str(response.get("id", "")),
            model=str(response.get("model", "")),
            usage=response.get("usage") if isinstance(response.get("usage"), dict) else {},
        )

    @staticmethod
    def _write_cache(path: Path, result: ModelResult) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "data": result.data,
            "response_id": result.response_id,
            "model": result.model,
            "usage": result.usage,
        }
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            temporary = Path(handle.name)
        os.replace(temporary, path)
