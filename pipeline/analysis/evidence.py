"""Deterministic, cutoff-aware evidence catalog shared by analysis and combine."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

from starter.search import find_document_directory, load_company, parse_frontmatter


WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source: str
    published_at: str
    quote: str
    title: str
    document_type: str
    period: str

    def prompt_record(self) -> dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "published_at": self.published_at,
            "document_type": self.document_type,
            "period": self.period,
            "quote": self.quote,
        }

    def citation(self) -> dict[str, str]:
        return {
            "source": self.source,
            "published_at": self.published_at,
            "quote": self.quote,
        }


def normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("*", "")).strip()


def parse_iso_date(value: str, where: str) -> date:
    if not isinstance(value, str) or len(value) != 10:
        raise EvidenceError(f"{where}: expected YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError(f"{where}: invalid date {value!r}") from exc
    if parsed.isoformat() != value:
        raise EvidenceError(f"{where}: date must be canonical YYYY-MM-DD")
    return parsed


def resolve_repo_source(repo_root: Path, source: str) -> Path:
    if not isinstance(source, str) or not source.strip():
        raise EvidenceError("source must be a non-empty repository-relative path")
    if source.startswith(("http://", "https://")):
        raise EvidenceError("URL evidence must be saved as a dated repository note")
    relative = Path(source)
    if relative.is_absolute():
        raise EvidenceError(f"source must be repository-relative: {source!r}")
    root = Path(repo_root).resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EvidenceError(f"source escapes the repository: {source!r}") from exc
    if not resolved.is_file():
        raise EvidenceError(f"source file does not exist: {source}")
    return resolved


def validate_citation(
    repo_root: Path,
    citation: dict,
    *,
    cutoff: date,
    where: str,
) -> None:
    if not isinstance(citation, dict):
        raise EvidenceError(f"{where}: citation must be an object")
    source = citation.get("source")
    published_at = citation.get("published_at")
    quote = citation.get("quote")
    if not isinstance(quote, str) or not quote.strip():
        raise EvidenceError(f"{where}: quote must be non-empty")
    published = parse_iso_date(published_at, f"{where} published_at")
    if published > cutoff:
        raise EvidenceError(f"{where}: evidence is after cutoff {cutoff.isoformat()}")
    source_path = resolve_repo_source(repo_root, source)
    source_text = normalise_text(source_path.read_text(encoding="utf-8", errors="replace"))
    if normalise_text(quote) not in source_text:
        raise EvidenceError(f"{where}: quote is not present in {source}")


def _source_paths(repo_root: Path, company_id: str, dossier_path: Path) -> list[Path]:
    company = load_company(repo_root / "challenge" / "companies.json", company_id)
    roots = []
    for collection in ("offline-data", "live-data"):
        root = repo_root / "challenge" / collection
        roots.append(find_document_directory(root, company))
    paths = {
        path
        for root in roots
        for path in root.rglob("*.md")
        if path.name not in {"INDEX.md", "README.md"}
    }
    if dossier_path.is_file():
        paths.add(dossier_path)
    return sorted(paths)


def _evidence_id(source: str, quote: str) -> str:
    digest = hashlib.sha256(f"{source}\0{normalise_text(quote)}".encode()).hexdigest()[:12]
    return f"E{digest}"


def build_evidence_catalog(
    *,
    repo_root: Path,
    company_id: str,
    dossier_path: Path,
    cutoff: date,
    source_paths: Sequence[Path] | None = None,
    max_quote_chars: int = 1_800,
) -> tuple[EvidenceItem, ...]:
    repo_root = Path(repo_root).resolve()
    dossier_path = Path(dossier_path).resolve()
    catalog: dict[str, EvidenceItem] = {}
    paths = _source_paths(repo_root, company_id, dossier_path) if source_paths is None else source_paths
    for path in sorted({Path(path).resolve() for path in paths}):
        raw = path.read_text(encoding="utf-8", errors="replace")
        metadata, body = parse_frontmatter(raw)
        relative = path.resolve().relative_to(repo_root).as_posix()
        published_at = str(metadata.get("published_at") or "")
        if not published_at and path == dossier_path:
            published_at = cutoff.isoformat()
        if published_at:
            try:
                if parse_iso_date(published_at, relative) > cutoff:
                    continue
            except EvidenceError:
                continue
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        for block in re.split(r"\n\s*\n", body):
            quote = block.strip()
            if len(normalise_text(quote)) < 30:
                continue
            if len(quote) > max_quote_chars:
                quote = quote[:max_quote_chars].rstrip()
            evidence_id = _evidence_id(relative, quote)
            catalog[evidence_id] = EvidenceItem(
                evidence_id=evidence_id,
                source=relative,
                published_at=published_at,
                quote=quote,
                title=title,
                document_type=str(metadata.get("document_type") or "RESEARCH_DOSSIER"),
                period=str(metadata.get("period") or ""),
            )
    return tuple(sorted(catalog.values(), key=lambda item: (item.source, item.evidence_id)))


def select_evidence(
    catalog: Sequence[EvidenceItem],
    *,
    terms: Iterable[str],
    limit: int,
    require_number: bool = False,
) -> tuple[EvidenceItem, ...]:
    wanted = {term.casefold() for term in terms if term.strip()}
    scored = []
    for item in catalog:
        words = {word.casefold() for word in WORD_RE.findall(item.quote)}
        overlap = len(words & wanted)
        if require_number and not NUMBER_RE.search(item.quote):
            continue
        live_bonus = 10 if "challenge/live-data/" in item.source else 0
        dossier_bonus = 4 if item.document_type == "RESEARCH_DOSSIER" else 0
        date_score = int(item.published_at[:4]) - 2000 if item.published_at else 0
        score = overlap * 20 + live_bonus + dossier_bonus + date_score
        scored.append((score, item.published_at, item.source, item.evidence_id, item))
    scored.sort(reverse=True)
    return tuple(entry[-1] for entry in scored[:limit])


def evidence_map(items: Sequence[EvidenceItem]) -> dict[str, EvidenceItem]:
    return {item.evidence_id: item for item in items}
