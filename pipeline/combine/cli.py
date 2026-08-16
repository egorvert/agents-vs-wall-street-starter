"""Command-line entrypoint for David's blind/reveal combine stage."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

from pipeline.analysis.model_client import (
    DEFAULT_MODEL,
    ModelClientError,
    OpenAIResponsesClient,
    json_event_logger,
)
from pipeline.combine.core import CombineConfig, CombineError, run_combine
from pipeline.quant.guardrails import GuardrailError


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--company", help="company_id from schemas/metrics.json")
    selection.add_argument("--all", action="store_true", help="reconcile all four companies")
    parser.add_argument("--repo-root", default=str(repo_root))
    parser.add_argument("--out-root", default="out")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    out = Path(args.out_root)
    if not out.is_absolute():
        out = root / out
    manifest = json.loads((root / "schemas" / "metrics.json").read_text(encoding="utf-8"))
    company_ids = list(manifest["companies"]) if args.all else [args.company]
    config = CombineConfig(model=args.model)
    client = OpenAIResponsesClient(
        model=args.model,
        reasoning_effort=config.reasoning_effort,
        cache_root=out / ".cache",
        use_cache=not args.no_cache,
        logger=json_event_logger,
    )
    try:
        run_combine(
            company_ids,
            root,
            out,
            config,
            client,
            datetime.now().astimezone(),
            json_event_logger,
        )
    except (CombineError, GuardrailError, ModelClientError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
