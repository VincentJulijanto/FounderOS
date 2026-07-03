"""
Vault store — file-backed implementation of the frozen vault interface.

Layout under VAULT_PATH:
    <vault_root>/
        <company_id>/
            _index.md            # optional human-readable index (regenerated)
            2026-07-01-vietnam-expansion.md
            ...

Each decision note is markdown with YAML frontmatter:
    ---
    type: decision
    decision_id: <uuid>
    date: 2026-07-01
    recommendation: conditional
    confidence: medium
    outcome:               # filled later by write_back on feedback
    summary: One-line summary the selector ranks on.
    ---
    ## Decision
    ...body...

Retrieval (read) selects the relevant notes for a query. Selection is LLM-driven
when a key is present; in mock mode (or with a tiny vault) it falls back to a
deterministic keyword-overlap heuristic. Either way it only ever loads the bodies
of the SELECTED notes — never the whole vault.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..config import settings
from ..models import (
    CompanyProfile,
    Decision,
    BoardRecommendation,
    VaultNote,
    ContextBundle,
)

# How many notes the selector is allowed to pull into context per run.
MAX_SELECTED_NOTES = 4

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_STOPWORDS = {
    "the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "we",
    "our", "should", "is", "are", "this", "that", "with", "into", "next",
}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "decision"


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Minimal YAML-frontmatter parser (flat key: value only — no deps)."""
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw.strip()
    fm_block, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body.strip()


def _dump_frontmatter(fm: dict) -> str:
    lines = ["---"]
    for key, val in fm.items():
        lines.append(f"{key}: {val if val is not None else ''}")
    lines.append("---")
    return "\n".join(lines)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


class Vault:
    """File-backed vault rooted at VAULT_PATH. One folder per company_id."""

    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or settings.vault_path)

    # ── paths ────────────────────────────────────────────────────────────
    def _company_dir(self, company_id: str) -> Path:
        return self.root / company_id

    # ── index ────────────────────────────────────────────────────────────
    def index(self, company_id: str) -> List[VaultNote]:
        """Build the lightweight index the selector ranks on (never reads bodies)."""
        company_dir = self._company_dir(company_id)
        if not company_dir.exists():
            return []
        notes: List[VaultNote] = []
        for path in sorted(company_dir.glob("*.md")):
            if path.name.startswith("_"):
                continue
            try:
                fm, _body = _parse_frontmatter(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            notes.append(VaultNote(
                path=path.name,
                frontmatter=fm,
                summary=fm.get("summary", ""),
            ))
        return notes

    # ── read (selective retrieval) ───────────────────────────────────────
    def read(self, company_id: str, query: str) -> ContextBundle:
        """Select the notes relevant to `query` and return only their bodies."""
        index = self.index(company_id)
        if not index:
            return ContextBundle(notes=[], used_paths=[])

        selected = self._select(index, query)
        notes, used = [], []
        company_dir = self._company_dir(company_id)
        for note in selected:
            try:
                _fm, body = _parse_frontmatter(
                    (company_dir / note.path).read_text(encoding="utf-8")
                )
            except OSError:
                continue
            notes.append(body)
            used.append(note.path)
        return ContextBundle(notes=notes, used_paths=used)

    def _select(self, index: List[VaultNote], query: str) -> List[VaultNote]:
        """Rank the index against the query.

        Live mode asks the LLM to pick relevant filenames; mock mode (and any
        selector failure) falls back to keyword overlap on frontmatter+summary.
        Both cap at MAX_SELECTED_NOTES so context never balloons.
        """
        if settings.is_live and len(index) > MAX_SELECTED_NOTES:
            try:
                return self._llm_select(index, query)
            except Exception:
                pass  # never let retrieval crash the pipeline — fall through
        return self._keyword_select(index, query)

    def _keyword_select(self, index: List[VaultNote], query: str) -> List[VaultNote]:
        q = _tokens(query)
        scored = []
        for note in index:
            hay = f"{note.path} {note.summary} {' '.join(str(v) for v in note.frontmatter.values())}"
            overlap = len(q & _tokens(hay))
            scored.append((overlap, note))
        # Highest overlap first; ties keep filename order (dates sort chronologically).
        scored.sort(key=lambda t: t[0], reverse=True)
        ranked = [n for score, n in scored if score > 0]
        # If nothing overlaps, fall back to the most recent notes so history still shows.
        chosen = ranked or [n for _s, n in scored]
        return chosen[:MAX_SELECTED_NOTES]

    def _llm_select(self, index: List[VaultNote], query: str) -> List[VaultNote]:
        """Ask the LLM which notes to load, given only the index (not the bodies)."""
        from ..llm.provider import QwenProvider, FAST_MODEL

        catalog = "\n".join(
            f"{i}. {n.path} — {n.summary or n.frontmatter.get('type', 'note')}"
            for i, n in enumerate(index)
        )
        system = (
            "You select which past board notes are relevant to a new decision. "
            "Return valid JSON only: {\"indices\": [int, ...]} — at most "
            f"{MAX_SELECTED_NOTES} indices, most relevant first."
        )
        user = f"New decision / query:\n{query}\n\nAvailable notes:\n{catalog}"
        raw = QwenProvider(model=FAST_MODEL).chat(system, user, max_tokens=300)
        import json
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        picked = json.loads(m.group()) if m else {"indices": []}
        idxs = [i for i in picked.get("indices", []) if 0 <= i < len(index)]
        selected = [index[i] for i in idxs][:MAX_SELECTED_NOTES]
        return selected or self._keyword_select(index, query)

    # ── write_back (append + outcome loop) ───────────────────────────────
    def write_back(
        self,
        company_id: str,
        decision: Decision,
        recommendation: BoardRecommendation,
        learnings: Optional[List[str]] = None,
    ) -> str:
        """Append a decision note and return its decision_id (used by the outcome loop)."""
        company_dir = self._company_dir(company_id)
        company_dir.mkdir(parents=True, exist_ok=True)

        decision_id = str(uuid.uuid4())
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        summary = f"{decision.question} → {recommendation.recommendation} ({recommendation.confidence})"
        fm = {
            "type": "decision",
            "decision_id": decision_id,
            "date": date,
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "outcome": "",   # filled later by record_outcome
            "summary": summary.replace("\n", " ")[:200],
        }

        learn_lines = "\n".join(f"- {l}" for l in (learnings or [])) or "- (none recorded)"
        dissent_lines = "\n".join(
            f"- **{d.agent}**: {d.position}" for d in recommendation.dissent
        ) or "- (none)"
        body = (
            f"## Decision\n{decision.question}\n\n"
            f"### Context\n{decision.context or '(none)'}\n\n"
            f"## Recommendation: {recommendation.recommendation} "
            f"(confidence: {recommendation.confidence})\n{recommendation.rationale}\n\n"
            f"### What would change this call\n{recommendation.what_would_change_this_call}\n\n"
            f"### Dissent on record\n{dissent_lines}\n\n"
            f"### Missing inputs\n"
            + ("\n".join(f"- {mi}" for mi in recommendation.missing_inputs) or "- (none)")
            + f"\n\n### Learnings\n{learn_lines}\n\n"
            f"### Outcome\n(pending — updated when the operator reports back)\n"
        )

        # Suffix with the decision_id so two same-day decisions with an identical
        # question don't collide on filename (which would overwrite the earlier
        # note and orphan its decision_id from the outcome loop).
        filename = f"{date}-{_slugify(decision.question)}-{decision_id[:8]}.md"
        (company_dir / filename).write_text(
            f"{_dump_frontmatter(fm)}\n\n{body}", encoding="utf-8"
        )
        return decision_id

    def record_outcome(self, company_id: str, decision_id: str,
                       outcome: str, notes: str = "") -> bool:
        """Write a real outcome back against the matching decision note (the loop)."""
        company_dir = self._company_dir(company_id)
        if not company_dir.exists():
            return False
        for path in company_dir.glob("*.md"):
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError:
                continue
            fm, body = _parse_frontmatter(raw)
            if fm.get("decision_id") == decision_id:
                fm["outcome"] = (outcome or "").replace("\n", " ")[:120]
                outcome_block = (
                    f"### Outcome\n**{outcome}**\n\n{notes}\n" if outcome
                    else "### Outcome\n(pending)\n"
                )
                body = re.sub(r"### Outcome\n.*$", outcome_block, body, flags=re.DOTALL)
                path.write_text(f"{_dump_frontmatter(fm)}\n\n{body}", encoding="utf-8")
                return True
        return False

    def history(self, company_id: str) -> List[dict]:
        """The company's decision history from the index (for GET /api/company/{id})."""
        return [
            {"path": n.path, **n.frontmatter}
            for n in sorted(self.index(company_id),
                            key=lambda n: n.frontmatter.get("date", ""), reverse=True)
        ]


# Module-level singleton + contract-shaped functions (what the graph/API import).
_vault = Vault()


def read(company_id: str, query: str) -> ContextBundle:
    return _vault.read(company_id, query)


def write_back(company_id: str, decision: Decision,
               recommendation: BoardRecommendation,
               learnings: Optional[List[str]] = None) -> str:
    return _vault.write_back(company_id, decision, recommendation, learnings)


def record_outcome(company_id: str, decision_id: str, outcome: str, notes: str = "") -> bool:
    return _vault.record_outcome(company_id, decision_id, outcome, notes)


def history(company_id: str) -> List[dict]:
    return _vault.history(company_id)
